#!/usr/bin/env python3
"""Validate public result consistency and publication boundaries without models."""
import csv
from decimal import Decimal
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def verify():
    data = json.loads((ROOT / "results/official_scores.json").read_text())
    csv_rows = list(csv.DictReader((ROOT / "results/official_scores.csv").open()))
    assert len(data["submissions"]) == len(csv_rows) == 12
    by_id = {row["submission_id"]: row for row in csv_rows}
    scored = [row for row in data["submissions"] if row["status"] == "scored"]
    assert len(scored) == 11
    assert data["screenshots_published"] is False
    assert all(row["image"] is None for row in data["submissions"])
    best = max(scored, key=lambda row: Decimal(row["total"]))
    assert best["submission_id"] == data["best_observed_submission_id"] == 83804
    assert best["total"] == "0.7917453968"
    for row in data["submissions"]:
        for key, value in by_id[str(row["submission_id"])].items():
            assert value == ("" if row[key] is None else str(row[key])), (row["version"], key)
        if row["status"] != "scored":
            assert all(row[key] is None for key in ("total", "ADS", "CPS"))
            continue
        expected = Decimal("0.9") * Decimal(row["ADS"]) + Decimal("0.1") * Decimal(row["CPS"])
        assert abs(expected - Decimal(row["total"])) < Decimal("0.000000001")
        assert Decimal(row["total"]) - Decimal(best["total"]) == Decimal(row["delta_total_vs_v7"])
    first = next(row for row in scored if row["version"] == "v1")
    assert Decimal(best["total"]) - Decimal(first["total"]) == Decimal("0.1414142857")

    inventory = json.loads((ROOT / "results/model_inventory.json").read_text())
    assert inventory["weights_published"] is False
    weights = inventory["weights"]
    assert len(weights) == len({row["id"] for row in weights}) == 6
    assert sum(row["project_training"] for row in weights) == 3
    assert inventory["archive_sha256"] == "16386efd80993ecafb535db3ae53dbbc79d97a2fc01433f2fa833e7456370fb9"
    assert sum(Decimal(str(row.get("music_blend_weight", 0))) for row in weights) == 1
    for row in weights:
        assert re.fullmatch(r"[0-9a-f]{64}", row["sha256"]), row["id"]
        assert isinstance(row["bytes"], int) and row["bytes"] > 0
        assert row["archive_member"].startswith("model/")

    for markdown in ROOT.rglob("*.md"):
        for target in re.findall(r"\]\(([^)]+)\)", markdown.read_text()):
            if target.startswith(("https://", "http://", "#")):
                continue
            assert (markdown.parent / target.split("#", 1)[0]).is_file(), (markdown.name, target)
    for svg in (ROOT / "assets").glob("*.svg"):
        ET.parse(svg)

    forbidden_suffixes = {".pt", ".pth", ".th", ".safetensors", ".zip", ".wav", ".mp3", ".flac", ".sock", ".pem", ".key"}
    forbidden_roots = {"data", "baseline", "artifacts", "submission", "reports", "configs", "ops", ".work", ".superpowers"}
    private = re.compile(r"/Users/|/home/|/nas/|BEGIN (?:RSA |OPENSSH )?PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{20,}")
    count = 0
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(part in {".git", "__pycache__", ".pytest_cache", ".venv"} for part in relative.parts):
            continue
        assert not path.is_symlink(), relative
        if not path.is_file():
            continue
        assert relative.parts[0] not in forbidden_roots, relative
        assert path.suffix not in forbidden_suffixes, relative
        assert path.stat().st_size < 2_000_000, relative
        if path.suffix in {".md", ".json", ".csv", ".svg", ".yml", ".txt", ".py"} and path != Path(__file__).resolve():
            assert not private.search(path.read_text()), relative
        count += 1
    print(f"Publication PASS: {count} files; 11 scores + 1 error; 6 weight metadata entries; JSON/CSV/formula/links/SVG/boundaries")


if __name__ == "__main__":
    verify()
