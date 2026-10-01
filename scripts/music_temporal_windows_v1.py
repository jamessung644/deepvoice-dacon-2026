"""Pure-Python temporal window policies for the E0 music coverage experiment.

This module deliberately contains no audio decoding, model invocation, NumPy, or
PyTorch dependency.  It only fixes the window geometry so an experiment harness
can hold the model, weights, and probability aggregation constant.
"""
from __future__ import annotations

from typing import Literal


Policy = Literal["legacy8", "complete"]
LEGACY_MAXIMUM_WINDOWS = 8


def _valid_positive_int(value: object) -> bool:
    """Return true only for built-in positive integers (excluding booleans)."""
    return type(value) is int and value > 0


def _validate_frames_and_clip(frames: int, clip_samples: int) -> None:
    if not _valid_positive_int(frames):
        raise ValueError("frames must be a positive integer")
    # legacy8 uses clip_samples // 2 as range()'s step.  Reject one explicitly
    # rather than leaking range()'s unrelated zero-step exception.
    if type(clip_samples) is not int or clip_samples < 2:
        raise ValueError("clip_samples must be an integer of at least 2")


def window_starts(
    frames: int,
    clip_samples: int = 64_600,
    policy: Policy = "legacy8",
) -> list[int]:
    """Return valid clip starts for one file under a named E0 policy.

    ``legacy8`` reproduces v5's ``music_evaluation_window_starts`` geometry for
    its default 64,600-sample clip and eight-window limit.  ``complete`` keeps
    every legacy start and fills only its unread gaps, so the union of padded
    model inputs includes every real input sample without changing already-full
    legacy cases.
    """
    _validate_frames_and_clip(frames, clip_samples)
    if policy not in ("legacy8", "complete"):
        raise ValueError("policy must be 'legacy8' or 'complete'")

    if frames <= clip_samples:
        return [0]

    maximum_start = frames - clip_samples
    if policy == "legacy8":
        # Keep this arithmetic aligned with submission/improved_v5_file/script.py.
        natural = list(range(0, maximum_start + 1, clip_samples // 2))
        if natural[-1] != maximum_start:
            natural.append(maximum_start)
        if len(natural) <= LEGACY_MAXIMUM_WINDOWS:
            return natural
        return sorted({
            round(index * maximum_start / (LEGACY_MAXIMUM_WINDOWS - 1))
            for index in range(LEGACY_MAXIMUM_WINDOWS)
        })

    legacy_starts = window_starts(frames, clip_samples, "legacy8")
    legacy_summary = coverage_summary(frames, legacy_starts, clip_samples)
    additions: list[int] = []
    for gap_start, gap_end in legacy_summary["uncovered_intervals"]:
        # Each added window begins exactly where legacy coverage stops.  This
        # retains all legacy observations and only supplies the missing region.
        additions.extend(range(gap_start, gap_end, clip_samples))
    return sorted(legacy_starts + additions)


def coverage_summary(
    frames: int,
    starts: list[int],
    clip_samples: int = 64_600,
) -> dict[str, int | float | list[tuple[int, int]]]:
    """Describe the real-file samples covered by padded clips at ``starts``.

    Starts must be a sorted, duplicate-free list within the range a clip can
    legally begin.  When the file is shorter than one clip, its sole start of
    zero represents the padded input; otherwise legal starts always produce a
    full clip and the reported intervals are clamped to the real file length.
    """
    _validate_frames_and_clip(frames, clip_samples)
    if type(starts) is not list:
        raise ValueError("starts must be a list of integers")
    if not starts:
        raise ValueError("starts must not be empty")
    if any(type(start) is not int for start in starts):
        raise ValueError("starts must be a list of integers")
    if starts != sorted(starts) or len(starts) != len(set(starts)):
        raise ValueError("starts must be sorted and duplicate-free")

    maximum_start = max(0, frames - clip_samples)
    if starts[0] < 0 or starts[-1] > maximum_start:
        raise ValueError("start is outside the valid clip range")

    intervals: list[tuple[int, int]] = []
    for start in starts:
        end = min(frames, start + clip_samples)
        if not intervals or start > intervals[-1][1]:
            intervals.append((start, end))
        else:
            intervals[-1] = (intervals[-1][0], max(intervals[-1][1], end))

    covered_samples = sum(end - start for start, end in intervals)
    gaps: list[tuple[int, int]] = []
    cursor = 0
    for start, end in intervals:
        if start > cursor:
            gaps.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < frames:
        gaps.append((cursor, frames))
    largest_gap = max((end - start for start, end in gaps), default=0)

    return {
        "frames": frames,
        "clip_samples": clip_samples,
        "windows": len(starts),
        "covered_samples": covered_samples,
        "coverage_fraction": covered_samples / frames,
        "uncovered_samples": frames - covered_samples,
        "largest_uncovered_gap_samples": largest_gap,
        "covered_intervals": intervals,
        "uncovered_intervals": gaps,
    }
