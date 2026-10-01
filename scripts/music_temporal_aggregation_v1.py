#!/usr/bin/env python3
"""Development-only comparison of fixed temporal probability aggregations.

This script does not train, calibrate, or choose a competition submission.  It
turns already-produced window probabilities into one score per input sample and
reports ranking/threshold diagnostics.  Selection among the fixed methods must
be made on a development split that is independent of any final evaluation.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import hashlib
from pathlib import Path
from typing import Any, Iterable, Sequence


METHODS = ("mean", "max", "top2", "top3")
ALLOWED_SPLITS = ("dev", "validation", "diagnostic_dev")
ALLOWED_ROLES = ("model_selection_dev", "dev_model_selection", "diagnostic_dev")
LENGTH_BUCKETS = (
    ("0_10s", 0.0, 10.0),
    ("10_30s", 10.0, 30.0),
    ("30_45s", 30.0, 45.0),
    ("45_60s", 45.0, 60.0),
    ("60s_plus", 60.0, math.inf),
)


def aggregate_probabilities(scores: Sequence[float], method: str = "mean") -> float:
    """Return a fixed aggregation of finite probabilities in [0, 1]."""
    if method not in METHODS:
        raise ValueError(f"Unknown aggregation method: {method!r}")
    if isinstance(scores, (str, bytes)):
        raise ValueError("scores must be a non-empty sequence of probabilities")
    try:
        values = list(scores)
    except TypeError as exc:
        raise ValueError("scores must be a non-empty sequence of probabilities") from exc
    if not values:
        raise ValueError("scores must not be empty")
    if any(type(value) not in (int, float) or not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0
           for value in values):
        raise ValueError("scores must contain only finite probabilities in [0, 1]")
    probabilities = [float(value) for value in values]
    if method == "mean":
        return sum(probabilities) / len(probabilities)
    if method == "max":
        return max(probabilities)
    count = int(method[3:])
    return sum(sorted(probabilities, reverse=True)[:count]) / min(count, len(probabilities))


def _load_existing_binary_metrics():
    """Load the repository's canonical grouped-tie EER/AUC implementation."""
    source = Path(__file__).with_name("music_fake_v6_metrics.py")
    spec = importlib.util.spec_from_file_location("music_fake_v6_metrics_for_temporal", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load metric implementation: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.binary_metrics


_existing_binary_metrics = _load_existing_binary_metrics()


def binary_metrics(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Reuse canonical EER/AUC; add fixed-0.5 operating error rates."""
    pairs = [(row["label"], row["probability"]) for row in rows]
    if any(type(label) is not int or label not in (0, 1) or type(probability) not in (int, float)
           or not math.isfinite(float(probability)) or not 0.0 <= float(probability) <= 1.0
           for label, probability in pairs):
        raise ValueError("Expected known binary labels and finite probabilities")
    if not pairs:
        return {"count": 0, "real": 0, "fake": 0, "eer": None, "roc_auc": None,
                "fpr_at_0_5": None, "fnr_at_0_5": None}
    result = _existing_binary_metrics([{"label": label, "probability": probability} for label, probability in pairs])
    counts = {0: result["real"], 1: result["fake"]}
    fpr_05 = (sum(label == 0 and probability >= 0.5 for label, probability in pairs) / counts[0]
              if counts[0] else None)
    fnr_05 = (sum(label == 1 and probability < 0.5 for label, probability in pairs) / counts[1]
              if counts[1] else None)
    return {**result, "fpr_at_0_5": fpr_05, "fnr_at_0_5": fnr_05}


def length_bucket(duration_seconds: float) -> str:
    for name, lower, upper in LENGTH_BUCKETS:
        if lower <= duration_seconds < upper:
            return name
    raise ValueError("duration_seconds did not fit a length bucket")


def read_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_sample_ids: set[str] = set()
    group_splits: dict[str, str] = {}
    audio_labels: dict[str, int] = {}
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                raise ValueError(f"Blank JSONL line: {line_number}")
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"Expected object on line {line_number}")
            required = ("sample_id", "group_id", "label", "window_scores", "duration_seconds", "split", "role")
            missing = [key for key in required if key not in row]
            if missing:
                raise ValueError(f"Missing {', '.join(missing)} on line {line_number}")
            sample_id, group_id = row["sample_id"], row["group_id"]
            if not isinstance(sample_id, str) or not sample_id.strip():
                raise ValueError(f"Invalid sample_id on line {line_number}")
            if not isinstance(group_id, str) or not group_id.strip():
                raise ValueError(f"Missing or invalid group_id on line {line_number}")
            if sample_id in seen_sample_ids:
                raise ValueError(f"Duplicate sample_id: {sample_id}")
            seen_sample_ids.add(sample_id)
            if type(row["label"]) is not int or row["label"] not in (0, 1):
                raise ValueError(f"Invalid label on line {line_number}")
            if row["split"] not in ALLOWED_SPLITS:
                raise ValueError(f"Forbidden or invalid split on line {line_number}: {row['split']!r}")
            if row["role"] not in ALLOWED_ROLES:
                raise ValueError(f"Forbidden or invalid role on line {line_number}: {row['role']!r}")
            if group_id in group_splits and group_splits[group_id] != row["split"]:
                raise ValueError(f"A group_id cannot span splits: {group_id}")
            group_splits[group_id] = row["split"]
            duration = row["duration_seconds"]
            if type(duration) not in (int, float) or not math.isfinite(float(duration)) or float(duration) <= 0:
                raise ValueError(f"Invalid duration_seconds on line {line_number}")
            scores = row["window_scores"]
            if not isinstance(scores, list):
                raise ValueError(f"window_scores must be an array on line {line_number}")
            # Validate here once, independent of which method is requested later.
            aggregate_probabilities(scores, "mean")
            condition = row.get("condition")
            if condition is not None and (not isinstance(condition, str) or not condition):
                raise ValueError(f"condition must be a non-empty string when present on line {line_number}")
            audio_sha256 = row.get("source_sha256", row.get("audio_sha256"))
            if "source_sha256" in row and "audio_sha256" in row and row["source_sha256"] != row["audio_sha256"]:
                raise ValueError(f"source_sha256 and audio_sha256 differ on line {line_number}")
            if audio_sha256 is not None:
                if not isinstance(audio_sha256, str) or len(audio_sha256) != 64 or any(c not in "0123456789abcdef" for c in audio_sha256):
                    raise ValueError(f"source_sha256/audio_sha256 must be a lowercase SHA-256 hex string when present on line {line_number}")
                if audio_sha256 in audio_labels and audio_labels[audio_sha256] != row["label"]:
                    raise ValueError(f"Conflicting labels for audio_sha256: {audio_sha256}")
                audio_labels[audio_sha256] = row["label"]
            rows.append({"sample_id": sample_id, "group_id": group_id, "label": row["label"],
                         "window_scores": scores, "duration_seconds": float(duration), "condition": condition,
                         "split": row["split"], "role": row["role"], "audio_sha256": audio_sha256})
    if not rows:
        raise ValueError("Input JSONL has no rows")
    return rows


def report(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {"schema_version": "music_temporal_aggregation_v1",
                              "scope": "development-only fixed temporal aggregation comparison; not a competition improvement claim",
                              "interpretation": "Synthetic or contrived controls only validate aggregation mechanics; they cannot establish that a method improves a model.",
                              "input": {"samples": len(rows), "groups": len({row['group_id'] for row in rows}),
                                        "splits": sorted({row['split'] for row in rows}),
                                        "roles": sorted({row['role'] for row in rows})},
                              "methods": {}}
    for method in METHODS:
        scored = [{**row, "probability": aggregate_probabilities(row["window_scores"], method)} for row in rows]
        by_length = {name: binary_metrics([row for row in scored if length_bucket(row["duration_seconds"]) == name])
                     for name, _, _ in LENGTH_BUCKETS}
        conditions = sorted({row["condition"] for row in scored if row["condition"] is not None})
        by_condition = {condition: binary_metrics([row for row in scored if row["condition"] == condition])
                        for condition in conditions}
        output["methods"][method] = {"overall": binary_metrics(scored), "by_length_bucket": by_length,
                                      "by_condition": by_condition}
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="JSONL rows with window_scores")
    parser.add_argument("--output", required=True, type=Path, help="new JSON report path")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {args.output}")
    result = report(read_rows(args.input))
    result["receipt"] = {
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "metric_sha256": hashlib.sha256(Path(__file__).with_name("music_fake_v6_metrics.py").read_bytes()).hexdigest(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
