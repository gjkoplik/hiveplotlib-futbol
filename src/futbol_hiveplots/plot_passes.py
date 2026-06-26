"""Flagship: every pass as an arc, two teams side by side, datashaded.

Two nodes per pass (origin, destination), each on its third's axis, sorted by
distance from the center of the pitch. The pass is the edge. No aggregation, no
graph metrics. Rendered through a generic ``HivePlotMatrix`` so the two teams
share one unified color scale, with the node/edge colorbars drawn once and a
gray how-to-read caption beside them. Colormaps are the library defaults.

`passes_matrix(match_id, teams, match_label, stem)` is the reusable entry point.

Run: uv run python -m futbol_hiveplots.plot_passes
"""

import textwrap
from pathlib import Path

from hiveplotlib import HivePlot, HivePlotMatrix, NodeCollection

from futbol_hiveplots.data import (
    CAPTION_CORE,
    SORT_VAR,
    axis_range_kwargs,
    load_passes,
    pass_endpoint_graph,
)

FIG_DIR = Path(__file__).resolve().parents[2] / "figures"

CAPTION = textwrap.fill(
    CAPTION_CORE + " Both teams share one fixed layout and color scale, so the two"
    " sides compare directly.",
    width=52,
)

# (match_id, [home, away], label, output stem)
MATCHES = [
    (3869685, ["Argentina", "France"], "2022 World Cup final", "passes_wc2022"),
    (3943043, ["Spain", "England"], "Euro 2024 final", "passes_euro2024"),
]


def _hive_plot(passes, team):
    """Return (hive plot, pass count) for one team."""
    nodes_df, edges = pass_endpoint_graph(passes, team)
    nodes = NodeCollection(data=nodes_df, unique_id_column="node")
    hp = HivePlot(
        nodes=nodes,
        edges=edges,
        partition_variable="third",
        sorting_variables=SORT_VAR,
        axes_order=["def", "mid", "fin"],
        repeat_axes=True,
        axis_kwargs=axis_range_kwargs(SORT_VAR),  # absolute pitch bounds, not data
    )
    return hp, len(edges)


def passes_matrix(match_id: int, teams: list[str], match_label: str, stem: str) -> Path:
    """Two-team passing matrix for one match; returns the saved path."""
    passes = load_passes(match_id)
    built = [_hive_plot(passes, t) for t in teams]
    cells = [[hp for hp, _ in built]]
    labels = [f"{t} ({n} passes)" for t, (_, n) in zip(teams, built, strict=True)]
    # axes are pinned to absolute bounds per cell, so they're already unified
    matrix = HivePlotMatrix(cells, col_labels=labels, backend="datashader")
    fig, *_ = matrix.plot(dpi=200)
    fig.suptitle(f"Passing - {match_label}", fontsize=22, y=1.04)
    # caption sits to the right of the bottom-left colorbars, ~one hive-plot wide
    fig.text(
        0.46,
        0.12,
        CAPTION,
        ha="left",
        va="center",
        color="dimgray",
        fontsize=11,
        linespacing=1.5,
    )
    FIG_DIR.mkdir(exist_ok=True)
    out = FIG_DIR / f"{stem}.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"wrote {out}")
    return out


def main() -> None:
    for match_id, teams, label, stem in MATCHES:
        passes_matrix(match_id, teams, label, stem)


if __name__ == "__main__":
    main()
