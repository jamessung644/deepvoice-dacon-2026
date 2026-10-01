"""Single-file metrics and predeclared FILE routes; never average different files."""
import math
from collections import Counter


def binary_metrics(rows):
    pairs = [(r['label'], float(r['probability'])) for r in rows]
    if not pairs or any(type(y) is not int or y not in (0, 1) or not math.isfinite(p) or not 0 <= p <= 1 for y, p in pairs):
        raise ValueError('Expected known binary labels and finite probabilities')
    counts = Counter(y for y, _ in pairs)
    result = {'count': len(pairs), 'real': counts[0], 'fake': counts[1]}
    if not counts[0] or not counts[1]:
        return dict(result, eer=None, roc_auc=None)
    groups = {}
    for y, p in pairs:
        groups.setdefault(p, [0, 0])[y] += 1
    negative_below = 0; concordant = 0.
    for p, (neg, pos) in sorted(groups.items()):
        concordant += pos * (negative_below + .5 * neg)
        negative_below += neg
    tp = fp = 0
    previous = (0., 1.)
    eer = None
    for p, (neg, pos) in sorted(groups.items(), reverse=True):
        fp += neg; tp += pos
        point = (fp / counts[0], 1 - tp / counts[1])
        ld = previous[0] - previous[1]; rd = point[0] - point[1]
        if ld <= 0 <= rd and eer is None:
            t = -ld / (rd - ld) if rd != ld else 0.
            eer = previous[0] + t * (point[0] - previous[0])
        previous = point
    return dict(result, eer=eer, roc_auc=concordant / (counts[0] * counts[1]))


def file_routes(voice_present, music_present, voice_fake, df_music, stem_music, raw_music):
    if any(not math.isfinite(v) or not 0 <= v <= 1 for v in
           (voice_present, music_present, voice_fake, df_music, stem_music, raw_music)):
        raise ValueError('Invalid component probability')
    voice = voice_present * voice_fake
    return {'baseline': max(voice, music_present * df_music),
            'stem': max(voice, music_present * stem_music),
            'raw': max(voice, music_present * raw_music),
            'stem_raw_equal': max(voice, music_present * (.5 * stem_music + .5 * raw_music))}


def single_file_metrics(predictions):
    selected = [r for r in predictions if r['source_family'] != 'SONICS']
    overall = binary_metrics(selected)
    views = {v: binary_metrics([r for r in selected if r['view_id'] == v])
             for v in sorted({r['view_id'] for r in selected})}
    real = [r for r in selected if r['label'] == 0]
    heldout = {g: binary_metrics(real + [r for r in selected if r.get('generator') == g])
               for g in ('mustango', 'elevenlabs')}
    values = [m['eer'] for m in heldout.values()]
    if any(v is None for v in values) or any(m['eer'] is None for m in views.values()):
        raise ValueError('Undefined selection slice')
    criterion = .5 * overall['eer'] + .25 * max(m['eer'] for m in views.values()) + .25 * sum(values) / len(values)
    return {'file': overall, 'views': views, 'heldout_generators': heldout, 'criterion': criterion,
            'definition': '0.5 single-file pooled EER + 0.25 worst-view EER + 0.25 heldout-generator macro EER',
            'augmentation_predictions_averaged': False, 'official_score': False}
