import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/music_temporal_aggregation_v1.py"


def module():
    spec = importlib.util.spec_from_file_location("temporal_aggregation", SCRIPT)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class TemporalAggregationTests(unittest.TestCase):
    def test_fixed_aggregations_and_strict_probability_validation(self):
        tool = module()
        scores = [0.1, 0.8, 0.6, 0.3]
        self.assertAlmostEqual(tool.aggregate_probabilities(scores, "mean"), 0.45)
        self.assertAlmostEqual(tool.aggregate_probabilities(scores, "max"), 0.8)
        self.assertAlmostEqual(tool.aggregate_probabilities(scores, "top2"), 0.7)
        self.assertAlmostEqual(tool.aggregate_probabilities(scores, "top3"), (0.8 + 0.6 + 0.3) / 3)
        self.assertAlmostEqual(tool.aggregate_probabilities([0.2], "top3"), 0.2)
        for invalid in ([], [float("nan")], [-0.01], [1.01], [True], "0.5"):
            with self.assertRaises(ValueError):
                tool.aggregate_probabilities(invalid)
        with self.assertRaises(ValueError):
            tool.aggregate_probabilities([0.5], "noisy_or")

    def test_metrics_ties_threshold_and_missing_class_are_explicit(self):
        tool = module()
        metrics = tool.binary_metrics([
            {"label": 0, "probability": 0.5}, {"label": 1, "probability": 0.5},
            {"label": 0, "probability": 0.2}, {"label": 1, "probability": 0.8},
        ])
        self.assertAlmostEqual(metrics["roc_auc"], 0.875)
        self.assertAlmostEqual(metrics["fpr_at_0_5"], 0.5)
        self.assertEqual(tool.binary_metrics([{"label": 0, "probability": 0.2}])["eer"], None)
        self.assertEqual(tool.binary_metrics([{"label": 0, "probability": 0.2}])["fpr_at_0_5"], 0.0)

    def test_cli_outputs_all_methods_and_slices(self):
        rows = [
            {"sample_id": "a", "group_id": "g-real", "label": 0, "window_scores": [0.1, 0.2], "duration_seconds": 8, "condition": "clean", "split": "dev", "role": "model_selection_dev"},
            {"sample_id": "b", "group_id": "g-fake", "label": 1, "window_scores": [0.7, 0.9], "duration_seconds": 35, "condition": "clean", "split": "dev", "role": "model_selection_dev"},
            {"sample_id": "c", "group_id": "g-fake", "label": 1, "window_scores": [0.8], "duration_seconds": 61, "condition": "codec", "split": "dev", "role": "model_selection_dev"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            input_path, output_path = directory / "input.jsonl", directory / "report.json"
            input_path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            subprocess.run([sys.executable, str(SCRIPT), "--input", str(input_path), "--output", str(output_path)], check=True)
            report = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(set(report["methods"]), {"mean", "max", "top2", "top3"})
        self.assertEqual(report["input"], {"samples": 3, "groups": 2, "splits": ["dev"],
                                             "roles": ["model_selection_dev"]})
        self.assertEqual(set(report["receipt"]), {"input_sha256", "tool_sha256", "metric_sha256"})
        self.assertEqual(report["methods"]["mean"]["by_length_bucket"]["10_30s"]["eer"], None)
        self.assertEqual(report["methods"]["max"]["by_condition"]["codec"]["roc_auc"], None)

    def test_duplicate_sample_and_missing_group_rejected_but_group_label_mixture_allowed(self):
        tool = module()
        base = {"sample_id": "one", "group_id": "g", "label": 0, "window_scores": [0.1], "duration_seconds": 4, "split": "dev", "role": "model_selection_dev"}
        cases = [
            [base, {**base, "window_scores": [0.2]}],
            [{**base, "group_id": ""}],
        ]
        with tempfile.TemporaryDirectory() as directory:
            for number, rows in enumerate(cases):
                path = Path(directory) / f"bad-{number}.jsonl"
                path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
                with self.assertRaises(ValueError):
                    tool.read_rows(path)
            mixed_group = Path(directory) / "mixed-group.jsonl"
            mixed_group.write_text("".join(json.dumps(row) + "\n" for row in
                                          [base, {**base, "sample_id": "two", "label": 1}]), encoding="utf-8")
            self.assertEqual(len(tool.read_rows(mixed_group)), 2)
            whitespace = Path(directory) / "whitespace.jsonl"
            whitespace.write_text(json.dumps({**base, "sample_id": "  "}) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                tool.read_rows(whitespace)

    def test_group_cross_split_and_same_audio_hash_label_conflict_rejected(self):
        tool = module()
        base = {"sample_id": "one", "group_id": "g", "label": 0, "window_scores": [0.1], "duration_seconds": 4,
                "split": "dev", "role": "model_selection_dev"}
        cases = [
            [base, {**base, "sample_id": "two", "split": "validation"}],
            [base, {**base, "sample_id": "two", "label": 1, "source_sha256": "a" * 64},
             {**base, "sample_id": "three", "label": 0, "source_sha256": "a" * 64}],
        ]
        with tempfile.TemporaryDirectory() as directory:
            for number, rows in enumerate(cases):
                path = Path(directory) / f"conflict-{number}.jsonl"
                path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
                with self.assertRaises(ValueError):
                    tool.read_rows(path)
            aliases = Path(directory) / "hash-aliases.jsonl"
            aliases.write_text(json.dumps({**base, "source_sha256": "b" * 64, "audio_sha256": "c" * 64}) + "\n",
                               encoding="utf-8")
            with self.assertRaises(ValueError):
                tool.read_rows(aliases)

    def test_test_terminal_and_missing_split_or_role_are_rejected(self):
        tool = module()
        base = {"sample_id": "one", "group_id": "g", "label": 0, "window_scores": [0.1], "duration_seconds": 4,
                "split": "dev", "role": "model_selection_dev"}
        with tempfile.TemporaryDirectory() as directory:
            for number, row in enumerate(({**base, "split": "test"}, {**base, "role": "official"},
                                          {key: value for key, value in base.items() if key != "split"},
                                          {key: value for key, value in base.items() if key != "role"})):
                path = Path(directory) / f"forbidden-{number}.jsonl"
                path.write_text(json.dumps(row) + "\n", encoding="utf-8")
                with self.assertRaises(ValueError):
                    tool.read_rows(path)

    def test_one_class_slice_preserves_its_defined_fixed_threshold_rate(self):
        tool = module()
        real_only = tool.binary_metrics([{"label": 0, "probability": 0.7}, {"label": 0, "probability": 0.2}])
        fake_only = tool.binary_metrics([{"label": 1, "probability": 0.2}, {"label": 1, "probability": 0.9}])
        self.assertIsNone(real_only["eer"])
        self.assertIsNone(real_only["roc_auc"])
        self.assertEqual(real_only["fpr_at_0_5"], 0.5)
        self.assertIsNone(real_only["fnr_at_0_5"])
        self.assertEqual(fake_only["fnr_at_0_5"], 0.5)
        self.assertIsNone(fake_only["fpr_at_0_5"])


if __name__ == "__main__":
    unittest.main()
