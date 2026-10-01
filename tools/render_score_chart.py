#!/usr/bin/env python3
"""Render the archived DACON score series; no model or dataset is loaded."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scores", type=Path, default=root / "results/official_scores.json"
    )
    parser.add_argument(
        "--svg", type=Path, default=root / "assets/score-progression.svg"
    )
    parser.add_argument(
        "--png", type=Path, default=root / "assets/score-progression.png"
    )
    return parser.parse_args()


def render(scores_path: Path, svg_path: Path, png_path: Path) -> None:
    data = json.loads(scores_path.read_text(encoding="utf-8"))
    rows = [row for row in data["submissions"] if row["status"] == "scored"]
    if len(rows) != 11 or len({row["submission_id"] for row in rows}) != 11:
        raise ValueError("The archived series must contain 11 distinct scored submissions")
    x = list(range(1, len(rows) + 1))
    totals = [float(row["total"]) for row in rows]
    ads = [float(row["ADS"]) for row in rows]
    if any(not 0 <= value <= 1 for value in totals + ads):
        raise ValueError("Scores must be in [0, 1]")
    best_index = next(
        i for i, row in enumerate(rows)
        if row["submission_id"] == data["best_observed_submission_id"]
    )
    if totals[best_index] != max(totals):
        raise ValueError("The highlighted submission must be the best observed total")

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 17,
            "axes.labelsize": 11,
            "svg.fonttype": "path",
            "svg.hashsalt": "deepvoice-score-progression",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    fig, ax = plt.subplots(figsize=(11.4, 5.8))
    fig.subplots_adjust(left=0.08, right=0.975, top=0.77, bottom=0.20)
    total_color, ads_color, best_color = "#19375B", "#138A86", "#C58B11"
    fig.text(
        0.08, 0.935, "DACON Submission Score Progression",
        fontsize=18, fontweight="bold", color=total_color,
    )
    fig.text(
        0.08, 0.886,
        "11 scored submissions | Total = 0.9 ADS + 0.1 CPS | Higher is better",
        color="#4A5565", fontsize=10.5,
    )
    ax.plot(x, totals, color=total_color, linewidth=2.3, zorder=3)
    ax.plot(x, ads, color=ads_color, linewidth=1.8, linestyle="--", zorder=2)
    for i, row in enumerate(rows):
        archived = row["evidence_level"] == "archived_screenshot"
        ax.scatter(
            x[i], totals[i], s=42, marker="o", edgecolors=total_color,
            facecolors=total_color if archived else "white", linewidths=1.6, zorder=4,
        )
        ax.scatter(
            x[i], ads[i], s=34, marker="s", edgecolors=ads_color,
            facecolors=ads_color if archived else "white", linewidths=1.4, zorder=4,
        )
    ax.scatter(
        x[best_index], totals[best_index], s=190, marker="o", facecolors="none",
        edgecolors=best_color, linewidths=2.3, zorder=5,
    )
    ax.annotate(
        f"Best observed: v7  #{rows[best_index]['submission_id']}\n"
        f"Total {rows[best_index]['total']}",
        xy=(x[best_index], totals[best_index]), xytext=(4.3, 0.92),
        fontsize=10, color=total_color, ha="left", va="center",
        arrowprops={"arrowstyle": "-", "color": best_color, "linewidth": 1.3},
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "#FFF8E8", "edgecolor": "#EAD4A0"},
    )
    ax.set_xlim(0.6, 11.4)
    ax.set_ylim(0, 1)
    ax.set_xticks(x, ["v9*" if row["version"] == "v9_debugged" else row["version"] for row in rows])
    ax.set_xlabel("Submission version", labelpad=11)
    ax.set_ylabel("Displayed score (0-1)", labelpad=9)
    ax.yaxis.set_major_locator(MultipleLocator(0.1))
    ax.grid(axis="y", color="#DCE2E9", linewidth=0.7, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["bottom", "left"]].set_color("#8C99A8")
    ax.tick_params(colors="#455365", length=3)
    handles = [
        Line2D([0], [0], color=total_color, marker="o", linewidth=2.3, label="Total score"),
        Line2D([0], [0], color=ads_color, marker="s", linestyle="--", linewidth=1.8, label="ADS"),
        Line2D([0], [0], color="#657080", marker="o", markerfacecolor="white", linestyle="none", label="v11: transcription only"),
    ]
    ax.legend(
        handles=handles, loc="lower left", bbox_to_anchor=(0, 1.045), ncol=3,
        frameon=False, borderaxespad=0, handlelength=2.1, columnspacing=2.2,
    )
    fig.text(
        0.08, 0.073,
        "Archived submission-table evidence. v11 has no archived screenshot. This composite score is not accuracy.",
        fontsize=9, color="#596574",
    )
    fig.text(
        0.08, 0.040,
        "* v9 is the scored debugged submission #85981; failed submission #85924 has no score and is excluded.",
        fontsize=9, color="#596574",
    )
    for path in (svg_path, png_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(svg_path, metadata={"Date": None}, facecolor="white")
    svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text().splitlines()) + "\n")
    fig.savefig(png_path, dpi=180, metadata={"Software": "DeepVoice score chart"}, facecolor="white")
    plt.close(fig)
    print(f"Rendered {len(rows)} scored submissions to {svg_path.name} and {png_path.name}")


def main() -> None:
    args = parse_args()
    render(args.scores, args.svg, args.png)


if __name__ == "__main__":
    main()
