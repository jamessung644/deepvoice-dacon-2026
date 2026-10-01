import csv
import hashlib
import os
import stat
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.submission_verification_core import (
    PREDICTION_COLUMNS,
    compare_predictions,
    read_predictions,
    snapshot_package,
    validate_zip,
)


def write_csv(path: Path, rows, header=None):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header or ["ID", *PREDICTION_COLUMNS])
        writer.writerows(rows)


def rows():
    return [["a", "0", "0.1", "0.2", "0.3", "0.4"], ["b", "1", "0.2", "0.3", "0.4", "0.5"]]


def test_read_predictions_validates_exact_order_and_values(tmp_path):
    path = tmp_path / "pred.csv"
    write_csv(path, rows())
    parsed = read_predictions(path, ["a", "b"])
    assert parsed[0]["ID"] == "a"


def test_empty_prediction_contracts_are_rejected(tmp_path):
    path = tmp_path / "empty.csv"
    write_csv(path, [])
    with pytest.raises(ValueError, match="expected_ids"):
        read_predictions(path, [])
    with pytest.raises(ValueError, match="columns"):
        compare_predictions([], [], [])
    with pytest.raises(ValueError, match="rows"):
        compare_predictions([], [], PREDICTION_COLUMNS)
    with pytest.raises(ValueError, match="columns"):
        compare_predictions([{"ID": "a", "X": "0"}], [{"ID": "a", "X": "0"}], ["X", "X"])


@pytest.mark.parametrize("bad_rows", [
    [["b", "0", "0.1", "0.2", "0.3", "0.4"], ["a", "1", "0.2", "0.3", "0.4", "0.5"]],
    [["a", "0", "nan", "0.2", "0.3", "0.4"], ["b", "1", "0.2", "0.3", "0.4", "0.5"]],
    [["a", "0", "0.1", "0.2", "0.3", "1.1"], ["b", "1", "0.2", "0.3", "0.4", "0.5"]],
])
def test_read_predictions_rejects_order_nan_and_range(tmp_path, bad_rows):
    path = tmp_path / "bad.csv"
    write_csv(path, bad_rows)
    with pytest.raises(ValueError):
        read_predictions(path, ["a", "b"])


def test_read_predictions_rejects_duplicate_header_and_id(tmp_path):
    path = tmp_path / "bad.csv"
    write_csv(path, rows(), ["ID", *PREDICTION_COLUMNS[:-1], "ID"])
    with pytest.raises(ValueError, match="header"):
        read_predictions(path, ["a", "b"])
    write_csv(path, [["a", *rows()[0][1:]], ["a", *rows()[1][1:]]])
    with pytest.raises(ValueError, match="order|duplicate"):
        read_predictions(path, ["a", "b"])


def test_compare_predictions_matches_by_id_and_reports_delta():
    column = PREDICTION_COLUMNS[0]
    reference = [{"ID": "a", column: "0.1"}, {"ID": "b", column: "0.2"}]
    candidate = [{"ID": "b", column: "0.2"}, {"ID": "a", column: "0.1"}]
    report = compare_predictions(reference, candidate, [column])
    assert report["status"] == "matched" and report["rows"] == 2
    candidate[1][column] = "0.11"
    with pytest.raises(ValueError):
        compare_predictions(reference, candidate, [column])


def test_compare_predictions_parses_float_independently():
    column = PREDICTION_COLUMNS[0]
    with pytest.raises(ValueError, match="float|range"):
        compare_predictions([{"ID": "a", column: "nan"}], [{"ID": "a", column: "0.1"}], [column])


def test_snapshot_package_hashes_and_pinned_mutation(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    expected = {"a.txt": hashlib.sha256(b"a").hexdigest()}
    assert snapshot_package(tmp_path, expected) == expected
    (tmp_path / "a.txt").write_text("b")
    with pytest.raises(ValueError, match="snapshot"):
        snapshot_package(tmp_path, expected)


def test_snapshot_package_rejects_symlink_and_fifo(tmp_path):
    target = tmp_path / "outside"
    target.write_text("x")
    (tmp_path / "link").symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        snapshot_package(tmp_path)
    (tmp_path / "link").unlink()
    fifo = tmp_path / "pipe"
    os.mkfifo(fifo)
    with pytest.raises(ValueError, match="special"):
        snapshot_package(tmp_path)


def make_zip(path: Path, entries):
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in entries:
            archive.writestr(name, payload)


def test_validate_zip_hashes_crc_and_optional_binding(tmp_path):
    path = tmp_path / "ok.zip"
    make_zip(path, [("a.txt", b"abc"), ("dir/b.txt", b"def")])
    expected = {name: hashlib.sha256(payload).hexdigest() for name, payload in [("a.txt", b"abc"), ("dir/b.txt", b"def")]}
    report = validate_zip(path, expected)
    assert report["status"] == "passed" and report["expanded_bytes"] == 6
    assert validate_zip(path)["expected_files_bound"] is False


@pytest.mark.parametrize("entries", [
    [("../escape", b"x")],
    [("a\\b", b"x")],
    [("a.txt", b"x"), ("a.txt", b"x")],
])
def test_validate_zip_rejects_traversal_backslash_duplicate(tmp_path, entries):
    path = tmp_path / "bad.zip"
    make_zip(path, entries)
    with pytest.raises(ValueError):
        validate_zip(path)


def test_validate_zip_rejects_symlink_entry(tmp_path):
    path = tmp_path / "link.zip"
    info = zipfile.ZipInfo("link")
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(info, b"/outside")
    with pytest.raises(ValueError, match="symlink"):
        validate_zip(path)


def test_validate_zip_rejects_hash_mutation_and_size_cap(tmp_path):
    path = tmp_path / "cap.zip"
    make_zip(path, [("a", b"1234")])
    with pytest.raises(ValueError, match="hashes"):
        validate_zip(path, {"a": "0" * 64})
    with pytest.raises(ValueError, match="expanded"):
        validate_zip(path, max_expanded_bytes=3)
