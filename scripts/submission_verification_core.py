"""Small, reusable, fail-closed verification primitives for candidate outputs."""

from __future__ import annotations

import csv
import hashlib
import math
import os
import stat
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Iterable, Mapping, Sequence


PREDICTION_COLUMNS = (
    "FILE_FAKE_PROB", "VOICE_FAKE_PROB", "MUSIC_FAKE_PROB",
    "VOICE_PRESENT_PROB", "MUSIC_PRESENT_PROB",
)


def _float(value: object, context: str) -> float:
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid float at {context}: {value!r}") from exc
    if not math.isfinite(parsed) or not 0.0 <= parsed <= 1.0:
        raise ValueError(f"probability out of range at {context}: {value!r}")
    return parsed


def read_predictions(csv_path: Path | str, expected_ids: Sequence[str]) -> list[dict[str, str]]:
    """Read one exact, ordered prediction CSV and validate all five probabilities."""
    expected = [str(value) for value in expected_ids]
    if not expected:
        raise ValueError("expected_ids cannot be empty")
    if len(expected) != len(set(expected)):
        raise ValueError("expected_ids contains duplicates")
    with Path(csv_path).open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        if fields != ["ID", *PREDICTION_COLUMNS]:
            raise ValueError(f"prediction header differs: {fields!r}")
        rows: list[dict[str, str]] = []
        for line, row in enumerate(reader, 2):
            if None in row:
                raise ValueError(f"extra CSV fields at line {line}")
            if any(value is None for value in row.values()):
                raise ValueError(f"missing CSV field at line {line}")
            rows.append({key: str(row[key]) for key in fields})
    if len(rows) != len(expected):
        raise ValueError(f"prediction row count differs: {len(rows)} != {len(expected)}")
    for index, (row, expected_id) in enumerate(zip(rows, expected), 2):
        if row["ID"] != expected_id:
            raise ValueError(f"prediction ID/order differs at row {index}: {row['ID']!r} != {expected_id!r}")
        if row["ID"] in {item["ID"] for item in rows[:index - 2]}:
            raise ValueError(f"duplicate prediction ID: {row['ID']}")
        for column in PREDICTION_COLUMNS:
            _float(row[column], f"row {index}/{column}")
    return rows


def compare_predictions(refrows: Sequence[Mapping[str, object]],
                        candrows: Sequence[Mapping[str, object]],
                        columns: Iterable[str] = PREDICTION_COLUMNS,
                        exact: bool = True) -> dict:
    """Compare rows by ID using independently parsed numeric float equality.

    ``exact=True`` means exact equality of parsed finite numeric values, not byte
    equality of the original CSV spelling.
    """
    columns = tuple(columns)
    if not columns:
        raise ValueError("comparison columns cannot be empty")
    if len(set(columns)) != len(columns) or any(column not in PREDICTION_COLUMNS for column in columns):
        raise ValueError("comparison columns must be unique prediction columns")
    def index(rows: Sequence[Mapping[str, object]], label: str) -> dict[str, Mapping[str, object]]:
        if not rows:
            raise ValueError(f"{label} rows cannot be empty")
        output = {}
        for row in rows:
            row_id = str(row.get("ID", ""))
            if not row_id or row_id in output:
                raise ValueError(f"{label} has duplicate/missing ID: {row_id!r}")
            output[row_id] = row
        return output
    reference, candidate = index(refrows, "reference"), index(candrows, "candidate")
    if set(reference) != set(candidate):
        raise ValueError("prediction ID sets differ")
    differences = []
    max_abs_delta = 0.0
    for row_id in reference:
        for column in columns:
            left = _float(reference[row_id].get(column), f"reference {row_id}/{column}")
            right = _float(candidate[row_id].get(column), f"candidate {row_id}/{column}")
            delta = abs(left - right)
            max_abs_delta = max(max_abs_delta, delta)
            if exact and left != right:
                differences.append({"ID": row_id, "column": column, "reference": left, "candidate": right})
    report = {"status": "matched" if not differences else "different", "exact": exact,
            "rows": len(reference), "columns": list(columns),
            "max_abs_delta": max_abs_delta, "differences": differences}
    if exact and differences:
        raise ValueError(f"prediction values differ: {len(differences)} cells")
    return report


def _safe_relative(name: str) -> str:
    if not name or "\\" in name or name.startswith("/") or PureWindowsPath(name).drive:
        raise ValueError(f"unsafe archive path: {name!r}")
    path = PurePosixPath(name)
    if not path.parts or path.is_absolute() or ".." in path.parts or ":" in path.parts[0]:
        raise ValueError(f"unsafe archive path: {name!r}")
    return path.as_posix()


def _sha256_stream(stream) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
        digest.update(block); size += len(block)
    return digest.hexdigest(), size


def snapshot_package(package: Path | str, pinned_hashes: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return relative regular-file SHA-256s, rejecting symlinks and special files."""
    supplied_root = Path(package)
    if supplied_root.is_symlink():
        raise ValueError(f"package contains symlink: {package}")
    root = supplied_root.resolve()
    if not root.is_dir():
        raise ValueError(f"package is not a regular directory: {package}")
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"package contains symlink: {path}")
        if path.is_dir():
            continue
        if not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
            raise ValueError(f"package contains special file: {path}")
        resolved = path.resolve()
        if root not in resolved.parents:
            raise ValueError(f"package path escapes root: {path}")
        relative = path.relative_to(root).as_posix()
        with path.open("rb") as stream:
            snapshot[relative] = _sha256_stream(stream)[0]
    if pinned_hashes is not None and dict(pinned_hashes) != snapshot:
        raise ValueError("package snapshot differs from pinned hashes")
    return snapshot


def validate_zip(zip_path: Path | str, expected_files: Mapping[str, str] | None = None,
                 max_zip_bytes: int = 10_000_000_000,
                 max_expanded_bytes: int = 32_000_000_000) -> dict:
    """Validate ZIP paths, types, CRCs, sizes and optional exact file hashes."""
    archive = Path(zip_path)
    if archive.stat().st_size > max_zip_bytes:
        raise ValueError("ZIP archive exceeds size limit")
    with zipfile.ZipFile(archive) as handle:
        infos = handle.infolist()
        seen: set[str] = set(); expanded = 0; hashes: dict[str, str] = {}
        for info in infos:
            name = _safe_relative(info.filename)
            if name in seen:
                raise ValueError(f"duplicate ZIP entry: {name}")
            seen.add(name)
            mode = (info.external_attr >> 16) & 0o170000
            if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError(f"ZIP entry is a symlink/special file: {name}")
            if info.is_dir():
                continue
            expanded += info.file_size
            if expanded > max_expanded_bytes:
                raise ValueError("ZIP expanded size exceeds limit")
            with handle.open(info, "r") as stream:
                digest, actual_size = _sha256_stream(stream)
            if actual_size != info.file_size:
                raise ValueError(f"ZIP size differs: {name}")
            hashes[name] = digest
        if handle.testzip() is not None:
            raise ValueError("ZIP CRC check failed")
    if expected_files is None:
        return {"status": "structure_verified_expected_files_unbound", "archive_bytes": archive.stat().st_size,
                "expanded_bytes": expanded, "files": hashes, "expected_files_bound": False}
    expected = {_safe_relative(key): value for key, value in expected_files.items()}
    if expected != hashes:
        raise ValueError("ZIP file set or SHA-256 hashes differ")
    return {"status": "passed", "archive_bytes": archive.stat().st_size,
            "expanded_bytes": expanded, "files": hashes, "expected_files_bound": True}
