"""Codec regression: real FFmpeg/libsndfile I/O, no model training or weights."""
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys

import numpy as np
import pytest
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class FakeV7:
    def __init__(self, decoded, original_stems, fail_recovery=False):
        self.decoded = decoded
        self.original_stems = original_stems
        self.fail_recovery = fail_recovery
        self.calls = []
        self.saved = None
        self.librosa = SimpleNamespace(load=lambda *a, **k: (self.decoded.copy(), 16000))

    @staticmethod
    def cancellation_safe_mono(x):
        return x if x.ndim == 1 else x.mean(axis=0, dtype=np.float32)

    def separate_voice_and_music(self, path, model, device):
        self.calls.append(Path(path))
        if len(self.calls) == 1: return self.original_stems
        self.saved, rate = sf.read(path, dtype='float32', always_2d=True)
        assert rate == 16000
        if self.fail_recovery: raise RuntimeError('separation failure')
        n = len(self.saved)
        return np.zeros(n + 1, np.float32), np.ones(n + 1, np.float32)


@pytest.mark.parametrize('delta', [0, 1])
def test_normal_path_preserves_original_values_without_decode(delta):
    from stem_timeline_recovery_v1 import separate_on_raw_timeline
    x = np.arange(64000, dtype=np.float32) / 64000
    stems = (np.pad(x, (0, delta)), np.pad(x, (0, delta)))
    v7 = FakeV7(x, stems)
    v7.librosa.load = lambda *a, **k: pytest.fail('normal path must not decode again')
    got = separate_on_raw_timeline(Path('original.wav'), x, v7, None, 'cpu', nullcontext)
    assert got[0] is stems[0] and got[1] is stems[1]
    assert len(v7.calls) == 1


@pytest.mark.parametrize('delta', [-1000, -1, 2, 385, 1152])
def test_mismatch_redecodes_preserves_stereo_and_cleans_temp(delta):
    from stem_timeline_recovery_v1 import separate_on_raw_timeline
    stereo = np.stack((np.arange(64000, dtype=np.float32)/64000, np.zeros(64000, np.float32)))
    raw = FakeV7.cancellation_safe_mono(stereo)
    v7 = FakeV7(stereo, (np.zeros(len(raw)+delta), np.zeros(len(raw)+delta)))
    got = separate_on_raw_timeline(Path('original.ogg'), raw, v7, None, 'cpu', nullcontext)
    assert len(v7.calls) == 2
    np.testing.assert_array_equal(v7.saved.T, stereo)
    assert got[0].shape == (64001,)
    assert not v7.calls[1].exists()


def test_changed_second_decode_is_rejected():
    from stem_timeline_recovery_v1 import separate_on_raw_timeline
    raw = np.zeros(64000, np.float32)
    v7 = FakeV7(np.ones_like(raw), (raw[:-2], raw[:-2]))
    with pytest.raises(ValueError, match='canonical decode differs'):
        separate_on_raw_timeline(Path('a.ogg'), raw, v7, None, 'cpu', nullcontext)
    assert len(v7.calls) == 1


def test_failure_removes_temporary_audio():
    from stem_timeline_recovery_v1 import separate_on_raw_timeline
    raw = np.zeros(64000, np.float32)
    v7 = FakeV7(raw, (raw[:-2], raw[:-2]), fail_recovery=True)
    with pytest.raises(RuntimeError, match='separation failure'):
        separate_on_raw_timeline(Path('a.ogg'), raw, v7, None, 'cpu', nullcontext)
    assert not v7.calls[1].exists()


def test_canonical_mismatch_still_rejected_instead_of_padding():
    from stem_timeline_recovery_v1 import separate_on_raw_timeline
    raw = np.zeros(64000, np.float32)
    v7 = FakeV7(raw, (raw[:-2], raw[:-2]))
    v7.separate_voice_and_music = lambda *args: (raw[:-2], raw[:-2])
    with pytest.raises(ValueError, match='canonical PCM separation length mismatch'):
        separate_on_raw_timeline(Path('a.ogg'), raw, v7, None, 'cpu', nullcontext)


def test_real_ogg_decoder_disagreement_and_pcm_roundtrip(tmp_path):
    from stem_timeline_recovery_v1 import separate_on_raw_timeline
    import shutil
    if not shutil.which('ffmpeg'): pytest.skip('FFmpeg unavailable')
    raw = (.1*np.sin(np.arange(64000)/16000*2*np.pi*337)).astype(np.float32)
    path = tmp_path/'regression.ogg';sf.write(path, raw, 16000, format='OGG', subtype='VORBIS')
    decoded, _ = sf.read(path, dtype='float32')
    def ffmpeg_stems(p):
        b = subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-f','f32le','-ar','44100','-'])
        count = (len(b)//4*16000+44099)//44100
        return np.zeros(count, np.float32), np.zeros(count, np.float32)
    before = ffmpeg_stems(path)
    # The known failing fixture uses codec end padding; don't silently skip it.
    assert len(before[0])-len(decoded) > 1
    v7 = SimpleNamespace(librosa=SimpleNamespace(load=lambda *a, **k:(decoded.copy(),16000)),
                         cancellation_safe_mono=lambda a:a,
                         separate_voice_and_music=lambda p,*args:ffmpeg_stems(p))
    after = separate_on_raw_timeline(path, decoded, v7, None, 'cpu', nullcontext)
    assert len(after[0]) in (len(decoded),len(decoded)+1)
