"""Per-player passing lineup, laid out in the team's formation.

One cell per starter, that player's passes as lateral-placed arcs (the flagship
pass-endpoint model), positioned in a generic datashader HivePlotMatrix at their
formation slot (`position_to_grid`). The bottom (keeper) row doubles as the
figure's furniture: the two cells left of the keeper hold the hand-placed
colorbars, the two cells right of the keeper hold a gray "how to read this" note.

`lineup_figure(match_id, team, match_label)` is the reusable entry point; point it
at any match / team.

Run: uv run python -m futbol_hiveplots.plot_lineups
"""

import textwrap
from pathlib import Path

import pandas as pd
from hiveplotlib import HivePlot, HivePlotMatrix, NodeCollection

from futbol_hiveplots.data import (
    CAPTION_CORE,
    LINEUP_NROW,
    SORT_VAR,
    THIRDS,
    axis_range_kwargs,
    load_passes,
    pass_endpoint_graph,
    position_to_grid,
    starting_xi,
)

SUPTITLE_FS = 40
NAME_FS = 23
AXES_LABEL_FS = 18
CBAR_LABEL_FS = 17
INTERP_FS = 16
KEEPER_ROW = LINEUP_NROW - 1

# spread players across standardized lane columns by row size, so a front three
# or back four lands identically for every team (apples-to-apples).
STANDARD_COLS = {1: [2], 2: [1, 3], 3: [0, 2, 4], 4: [0, 1, 3, 4], 5: [0, 1, 2, 3, 4]}

INTERP_TEXT = textwrap.fill(
    CAPTION_CORE + " Each panel is one starting player.", width=56
)

DEFAULT_MATCH_ID = 3869685  # 2022 WC final
DEFAULT_TEAMS = ["Argentina", "France"]
DEFAULT_LABEL = "2022 World Cup final"
FIG_DIR = Path(__file__).resolve().parents[2] / "figures"


def _cell(passes, team, player):
    nodes_df, edges = pass_endpoint_graph(passes, team, player=player)
    if len(edges) == 0:
        return None
    anchors = pd.DataFrame(
        {"node": [f"anchor_{t}" for t in THIRDS], "third": THIRDS, SORT_VAR: 0.0}
    )
    nodes_df = pd.concat([nodes_df, anchors], ignore_index=True)
    nodes = NodeCollection(data=nodes_df, unique_id_column="node")
    return HivePlot(
        nodes=nodes,
        edges=edges,
        partition_variable="third",
        sorting_variables=SORT_VAR,
        axes_order=["def", "mid", "fin"],
        repeat_axes=True,
        axis_kwargs=axis_range_kwargs(SORT_VAR),  # absolute pitch bounds, not data
    )


def lineup_figure(match_id: int, team: str, match_label: str) -> Path:
    """Build the formation lineup for one team/match and return the saved path."""
    passes = load_passes(match_id)
    xi = starting_xi(match_id, team)
    grid = xi["position"].map(position_to_grid)
    xi = xi.assign(grid_row=[g[0] for g in grid], raw_lane=[g[1] for g in grid])

    cells: dict[tuple[int, int], HivePlot] = {}
    names: dict[tuple[int, int], str] = {}
    for grid_row, group in xi.groupby("grid_row"):
        ordered = group.sort_values("raw_lane")
        cols = STANDARD_COLS.get(len(ordered), list(range(min(len(ordered), 5))))
        for col, (_, prow) in zip(cols, ordered.iterrows(), strict=False):
            hp = _cell(passes, team, prow["player"])
            if hp is None:
                continue
            cells[(grid_row, col)] = hp
            names[(grid_row, col)] = prow["label"]

    # axes are pinned to absolute bounds per cell, so they're already unified
    matrix = HivePlotMatrix(cells, backend="datashader")
    fig, axes, im_nodes, im_edges = matrix.plot(
        dpi=150,
        axes_labels_fontsize=AXES_LABEL_FS,
        show_node_colorbar=False,
        show_edge_colorbar=False,
    )

    for (r, c), name in names.items():
        axes[r, c].set_title(name, fontsize=NAME_FS, pad=10)

    _draw_colorbars(fig, axes, im_nodes, im_edges)
    _draw_interpretation(axes)

    # pull the grid up under the title, but leave a little gap below the title
    fig.subplots_adjust(top=0.95)
    fig.suptitle(f"{team} passing - {match_label}", fontsize=SUPTITLE_FS, y=0.99)
    FIG_DIR.mkdir(exist_ok=True)
    out = FIG_DIR / f"lineup_{team.lower()}.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"wrote {out}  ({len(cells)} starters)")
    return out


def _draw_colorbars(fig, axes, im_nodes, im_edges) -> None:
    """Hand-placed colorbars spanning the two cells left of the keeper."""
    ref_edges = next((v for v in im_edges.values() if v is not None), None)
    ref_nodes = next((v for v in im_nodes.values() if v is not None), None)
    host = axes[KEEPER_ROW, 0]
    host.axis("off")
    axes[KEEPER_ROW, 1].axis("off")
    if ref_edges is not None:
        cax = host.inset_axes([0.05, 0.66, 1.9, 0.13])
        cb = fig.colorbar(ref_edges, cax=cax, orientation="horizontal", extend="max")
        cb.ax.set_title("Edge density (passes)", size=CBAR_LABEL_FS)
        cb.ax.tick_params(labelsize=CBAR_LABEL_FS - 4)
    if ref_nodes is not None:
        cax = host.inset_axes([0.05, 0.18, 1.9, 0.13])
        cb = fig.colorbar(ref_nodes, cax=cax, orientation="horizontal", extend="max")
        cb.ax.set_title("Node density (pass endpoints)", size=CBAR_LABEL_FS)
        cb.ax.tick_params(labelsize=CBAR_LABEL_FS - 4)


def _draw_interpretation(axes) -> None:
    """Gray, left-aligned how-to-read note spanning the cells right of the keeper."""
    host = axes[KEEPER_ROW, 3]
    host.axis("off")
    axes[KEEPER_ROW, 4].axis("off")
    # start mid-way through the first of the two cells, so it sits clear of the keeper
    host.text(
        0.5,
        0.5,
        INTERP_TEXT,
        transform=host.transAxes,
        ha="left",
        va="center",
        color="dimgray",
        fontsize=INTERP_FS,
        linespacing=1.5,
    )


def main() -> None:
    for team in DEFAULT_TEAMS:
        lineup_figure(DEFAULT_MATCH_ID, team, DEFAULT_LABEL)


if __name__ == "__main__":
    main()
