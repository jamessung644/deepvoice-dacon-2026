"""Recover decoder length disagreement using the raw branch's exact PCM timeline.

No weight changes, guessed time shifts, rescaling of duration, or arbitrary
padding/truncation. The historical path is unchanged whenever its lengths fit.
"""
import json
from pathlib import Path
import sys
import tempfile

import numpy as np


def separate_on_raw_timeline(audio, raw, v7, separator, device, backend_context):
    raw = np.asarray(raw, dtype=np.float32)
    if raw.ndim != 1 or not len(raw) or not np.isfinite(raw).all():
        raise ValueError('invalid canonical raw waveform')
    with backend_context():
        voice, music = v7.separate_voice_and_music(audio, separator, device)
    sizes = [np.asarray(x).size for x in (voice, music)]
    if all(n in (len(raw), len(raw) + 1) for n in sizes):
        return voice, music

    # Librosa is deliberately the same decoder/rate/mono policy as frozen v7.
    # Keep both channels; the frozen separator retains its anti-phase handling.
    decoded, rate = v7.librosa.load(audio, sr=16000, mono=False, dtype=np.float32)
    decoded = np.asarray(decoded, dtype=np.float32)
    if rate != 16000 or decoded.ndim not in (1, 2) or not np.isfinite(decoded).all():
        raise ValueError('invalid canonical stereo decode')
    mono = np.asarray(v7.cancellation_safe_mono(decoded), dtype=np.float32)
    if mono.shape != raw.shape or not np.array_equal(mono, raw):
        raise ValueError('canonical decode differs from the raw branch; refusing guessed alignment')
    import soundfile as sf
    with tempfile.TemporaryDirectory(prefix='file-stem-pcm-') as temporary:
        canonical = Path(temporary) / 'canonical.wav'
        # FLOAT PCM preserves decoded samples exactly, including values above1.
        sf.write(canonical, decoded.T, 16000, format='WAV', subtype='FLOAT')
        restored, restored_rate = sf.read(canonical, dtype='float32', always_2d=True)
        expected = decoded[:, None] if decoded.ndim == 1 else decoded.T
        if restored_rate != 16000 or not np.array_equal(restored, expected):
            raise ValueError('canonical FLOAT WAV roundtrip differs')
        with backend_context():
            voice, music = v7.separate_voice_and_music(canonical, separator, device)
    recovered_sizes = [np.asarray(x).size for x in (voice, music)]
    if not all(n in (len(raw), len(raw) + 1) for n in recovered_sizes):
        raise ValueError('canonical PCM separation length mismatch: raw=%d stems=%s' % (len(raw), recovered_sizes))
    print(json.dumps({'event': 'stem_timeline_recovered', 'raw_samples': len(raw),
                      'original_stem_samples': sizes, 'canonical_stem_samples': recovered_sizes}), file=sys.stderr)
    return voice, music
