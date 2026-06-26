"""Load StatsBomb open-data passes and bin them into pitch thirds.

Two facts verified against real data (see ``inspect_schema.py``):

  * every pass carries a start ``location`` and a ``pass_end_location``;
  * the pitch is normalized so both teams attack toward ``x = 120``, so
    "toward goal" is unambiguously increasing ``x``.

Pitch is 120 (length) x 80 (width). We bin the length into thirds (defensive /
middle / final), which become the hive plot axes.
"""

import warnings

import numpy as np
import pandas as pd
from statsbombpy import sb

PITCH_LENGTH = 120.0
PITCH_WIDTH = 80.0

# third of the pitch by x (length). order matters: this is the attack direction.
THIRDS = ["def", "mid", "fin"]

# within-axis sort for the pass-endpoint figures. "lat_abs" = distance from the
# center of the pitch (central play at the inner end, wide play at the outer);
# swap to "lat_y" for a raw left-to-right flank-bias view.
SORT_VAR = "lat_abs"

# shared interpretation blurb so the lineup and the two-team figure read alike.
CAPTION_CORE = (
    "Each line is one pass. The three axes are thirds of the pitch (defensive, "
    "middle, final). Along an axis, the inner end is play through the middle of "
    "the pitch and the outer end is play out near the touchlines."
)

# StatsBomb tags pass_type only for non-open-play passes (throw-ins, free kicks,
# corners, goal kicks, kick-offs). open play == pass_type is NaN.


def _third(x: float) -> str:
    if x < PITCH_LENGTH / 3:
        return "def"
    if x < 2 * PITCH_LENGTH / 3:
        return "mid"
    return "fin"


def load_passes(
    match_id: int, open_play_only: bool = True, completed_only: bool = True
) -> pd.DataFrame:
    """Return one match's open-play completed passes as a flat frame."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        events = sb.events(match_id=match_id)

    p = events[events["type"] == "Pass"].copy()
    if open_play_only:
        p = p[p["pass_type"].isna()]
    if completed_only:
        # StatsBomb convention: pass_outcome is NaN for a completed pass.
        p = p[p["pass_outcome"].isna()]

    p["x0"] = p["location"].map(lambda v: v[0])
    p["y0"] = p["location"].map(lambda v: v[1])
    p["x1"] = p["pass_end_location"].map(lambda v: v[0])
    p["y1"] = p["pass_end_location"].map(lambda v: v[1])
    p["from_third"] = p["x0"].map(_third)
    p["to_third"] = p["x1"].map(_third)
    return p.reset_index(drop=True)


def position_to_third(position: str) -> str:
    """Collapse a StatsBomb position label to def / mid / fin (forward)."""
    if "Goalkeeper" in position or "Back" in position:
        return "def"
    if "Midfield" in position:
        return "mid"
    return "fin"  # Wing, Forward, Center Forward


# fixed 5-row x 5-col formation grid:
#   row 0 striker(s) / 1 wings + attacking mids / 2 midfield / 3 defenders / 4 keeper.
# the extra top row lets shapes like 4-2-3-1 and 4-3-2-1 read correctly (a lone
# striker sits above the line behind). keeper centered on the bottom row.
LINEUP_NROW, LINEUP_NCOL = 5, 5


def position_to_grid(position: str) -> tuple[int, int]:
    """Map a StatsBomb position label to a (row, lane) slot in the 5x5 grid.

    ``row``: 0 striker, 1 wings / attacking mids, 2 midfield, 3 defenders,
    4 keeper (attack at top). ``lane``: 0 left .. 4 right (keeper at lane 2).
    The cutoffs are hand-set to StatsBomb's naming scheme, hence specific to
    this data source.
    """
    p = position
    if "Goalkeeper" in p:
        row = 4
    elif "Back" in p:  # includes Wing Back
        row = 3
    elif "Defensive Midfield" in p:
        row = 2
    elif "Attacking Midfield" in p:  # the "2" in a 4-3-2-1 sits above the mids
        row = 1
    elif "Midfield" in p:  # central / wide midfield
        row = 2
    elif "Wing" in p:  # Left/Right Wing (wing backs already caught above)
        row = 1
    else:  # Center Forward, Forward, Striker, Secondary Striker
        row = 0

    if "Left Center" in p:
        lane = 1
    elif "Right Center" in p:
        lane = 3
    elif "Left" in p:
        lane = 0
    elif "Right" in p:
        lane = 4
    else:  # Center or unspecified
        lane = 2
    return row, lane


# --- pass-endpoint model (two nodes per pass, placed by lateral position) ---
# No aggregation, no graph features. Each pass contributes an origin node and a
# destination node; each sits on its third's axis at its real lateral position,
# and the pass is the edge between them. The "explain it to a soccer person in
# one sentence" model: every line is one pass, from where it started to where it
# ended.


def pass_endpoint_graph(
    passes: pd.DataFrame, team: str, player: str | None = None
) -> tuple[pd.DataFrame, np.ndarray]:
    """Return (nodes, edges) for the pass-endpoint model.

    Whole team, or a single ``player``'s passes (for the per-player lineup).
    ``nodes``: one row per pass endpoint with ``node`` (unique id), ``third``
    (partition -> axis) and the within-axis sort options ``lat_abs`` (distance
    from the center of the pitch, 0 central .. 40 touchline; the default sort)
    and ``lat_y`` (raw left-to-right lateral position, kept for a flank-bias
    view). ``edges``: ``(origin_node, dest_node)`` per pass.
    """
    p = passes[passes["team"] == team]
    if player is not None:
        p = p[p["player"] == player]
    p = p.reset_index(drop=True)
    half = PITCH_WIDTH / 2
    origin = pd.DataFrame(
        {
            "node": [f"{i}_o" for i in p.index],
            "third": p["from_third"].to_numpy(),
            "lat_y": p["y0"].to_numpy(),
            "lat_abs": (p["y0"] - half).abs().to_numpy(),
        }
    )
    dest = pd.DataFrame(
        {
            "node": [f"{i}_d" for i in p.index],
            "third": p["to_third"].to_numpy(),
            "lat_y": p["y1"].to_numpy(),
            "lat_abs": (p["y1"] - half).abs().to_numpy(),
        }
    )
    nodes = pd.concat([origin, dest], ignore_index=True)
    edges = np.column_stack([origin["node"].to_numpy(), dest["node"].to_numpy()])
    return nodes, edges


def axis_range_kwargs(sort_var: str) -> dict[str, dict[str, float]]:
    """Per-axis ``vmin``/``vmax`` pinned to absolute pitch bounds.

    Pass to ``HivePlot(..., axis_kwargs=...)`` at construction. Without this,
    hiveplotlib infers each axis's range from the data on it, so a team that only
    played centrally would have that narrow band stretched out to the touchlines
    -- misleading, and not comparable across teams/players. Pinning to the same
    absolute bounds on every cell also unifies the cells by construction (no need
    for the matrix's ``unify_axes``). Repeat axes inherit these automatically.
    """
    if sort_var == "lat_abs":  # distance from center: 0 .. half the width
        lo, hi = 0.0, PITCH_WIDTH / 2
    elif sort_var == "lat_y":  # raw left-to-right: full width
        lo, hi = 0.0, PITCH_WIDTH
    else:
        return {}
    return {third: {"vmin": lo, "vmax": hi} for third in THIRDS}


def starting_xi(match_id: int, team: str) -> pd.DataFrame:
    """The starting eleven for a team, with clean display names.

    Columns: ``player`` (full name, the key that matches the events ``player``
    field), ``label`` (nickname if present, else full name), ``position`` (the
    starting position), ``third`` (def / mid / fin).
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        lu = sb.lineups(match_id=match_id)[team]

    rows = []
    for _, r in lu.iterrows():
        positions = r["positions"]
        if not positions or not any(
            p.get("start_reason") == "Starting XI" for p in positions
        ):
            continue
        start_pos = positions[0]["position"]
        nick = r["player_nickname"]
        rows.append(
            {
                "player": r["player_name"],
                "label": nick if isinstance(nick, str) else r["player_name"],
                "position": start_pos,
                "third": position_to_third(start_pos),
            }
        )
    return pd.DataFrame(rows)
