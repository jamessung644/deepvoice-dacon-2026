"""Catch unverified downloads, accidental overwrite and publication bypasses."""
import io
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ABC_SHA = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def record(**overrides):
    row = {"id": "fixture", "bytes": 3, "sha256": ABC_SHA,
           "release": {"url": "https://example.org/model.pth", "filename": "model.pth"}}
    row.update(overrides)
    return row


def test_verified_download_commits_exact_bytes(tmp_path):
    from tools.download_weights import download_weight
    path = download_weight(record(), tmp_path, opener=lambda request, timeout: io.BytesIO(b"abc"))
    assert path.read_bytes() == b"abc"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["model.pth"]


def test_matching_existing_file_is_reused_without_network(tmp_path):
    from tools.download_weights import download_weight
    path = tmp_path / "model.pth"
    path.write_bytes(b"abc")
    def offline(*args, **kwargs):
        raise AssertionError("Existing verified file must not be downloaded again")
    assert download_weight(record(), tmp_path, opener=offline) == path


def test_conflicting_existing_file_is_preserved(tmp_path):
    from tools.download_weights import download_weight
    path = tmp_path / "model.pth"
    path.write_bytes(b"old")
    with pytest.raises(ValueError, match="Existing"):
        download_weight(record(), tmp_path)
    assert path.read_bytes() == b"old"


@pytest.mark.parametrize("payload", [b"abd", b"abcd", b"ab"])
def test_corruption_and_wrong_size_leave_no_output(tmp_path, payload):
    from tools.download_weights import download_weight
    with pytest.raises(ValueError, match="size|SHA"):
        download_weight(record(), tmp_path, opener=lambda request, timeout: io.BytesIO(payload))
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("release", [None, {"url": "http://example.org/a", "filename": "a"},
                                     {"url": "https://example.org/a", "filename": "../a"}])
def test_unpublished_or_unsafe_download_is_rejected(tmp_path, release):
    from tools.download_weights import download_weight
    with pytest.raises(ValueError):
        download_weight(record(release=release), tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_symlink_target_is_not_followed(tmp_path):
    from tools.download_weights import download_weight
    original = tmp_path / "original"
    original.write_bytes(b"abc")
    (tmp_path / "model.pth").symlink_to(original)
    with pytest.raises(ValueError, match="symlink"):
        download_weight(record(), tmp_path)
    assert original.read_bytes() == b"abc"


def test_network_failure_removes_only_own_partial(tmp_path):
    from tools.download_weights import download_weight
    retained = tmp_path / "unrelated.part"
    retained.write_bytes(b"keep")
    def offline(*args, **kwargs):
        raise OSError("offline")
    with pytest.raises(OSError, match="offline"):
        download_weight(record(), tmp_path, opener=offline)
    assert retained.read_bytes() == b"keep"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["unrelated.part"]


def test_cli_rejects_held_weight_before_progress_or_download(tmp_path, monkeypatch, capsys):
    from tools import download_weights
    (tmp_path / "results").mkdir()
    (tmp_path / "results/model_inventory.json").write_text(json.dumps({"weights": [record(release=None)]}))
    monkeypatch.setattr(download_weights, "ROOT", tmp_path)
    output = tmp_path / "download"
    monkeypatch.setattr(sys, "argv", ["download_weights.py", "fixture", "--output-dir", str(output)])
    with pytest.raises(SystemExit) as caught:
        download_weights.main()
    assert caught.value.code == 2
    assert capsys.readouterr().out == ""
    assert not output.exists()


def test_cli_all_reuses_released_file_and_ignores_held_weight(tmp_path, monkeypatch, capsys):
    from tools import download_weights
    (tmp_path / "results").mkdir()
    (tmp_path / "results/model_inventory.json").write_text(json.dumps({"weights": [record(), record(id="held", release=None)]}))
    monkeypatch.setattr(download_weights, "ROOT", tmp_path)
    output = tmp_path / "download"
    output.mkdir()
    (output / "model.pth").write_bytes(b"abc")
    monkeypatch.setattr(sys, "argv", ["download_weights.py", "all", "--output-dir", str(output)])
    download_weights.main()
    assert "Verified:" in capsys.readouterr().out
    assert sorted(p.name for p in output.iterdir()) == ["model.pth"]
