import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class V6MetricsTests(unittest.TestCase):
    def load(self):
        path = ROOT / 'scripts/music_fake_v6_metrics.py'
        self.assertTrue(path.exists(), 'single-file evaluator is missing')
        spec = importlib.util.spec_from_file_location('v6_metrics', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_cross_codec_threshold_failure_is_not_hidden_by_parent_average(self):
        m = self.load()
        rows = [{'label': y, 'probability': p} for y, p in [(0, 0.0), (0, 0.8), (1, 0.6), (1, 0.9)]]
        self.assertAlmostEqual(m.binary_metrics(rows)['eer'], 0.5)
        self.assertAlmostEqual(m.binary_metrics(rows)['roc_auc'], 0.75)

    def test_rank_ties_and_reversed_predictions(self):
        m = self.load()
        self.assertEqual(m.binary_metrics([{'label': 0, 'probability': .5}, {'label': 1, 'probability': .5}])['eer'], .5)
        self.assertEqual(m.binary_metrics([{'label': 0, 'probability': 1.}, {'label': 1, 'probability': 0.}])['eer'], 1.)
        with self.assertRaises(ValueError):
            m.binary_metrics([{'label': None, 'probability': .5}])

    def test_file_route_uses_new_music_score_and_preserves_voice_evidence(self):
        m = self.load()
        result = m.file_routes(voice_present=.1, music_present=.9, voice_fake=.2,
                               df_music=.2, stem_music=.8, raw_music=.95)
        self.assertAlmostEqual(result['baseline'], .18)
        self.assertAlmostEqual(result['stem'], .72)
        self.assertAlmostEqual(result['raw'], .855)
        # With voice only, every candidate must retain the same voice evidence.
        self.assertEqual(set(m.file_routes(1, 0, .7, .1, .2, .9).values()), {.7})


if __name__ == '__main__':
    unittest.main()
