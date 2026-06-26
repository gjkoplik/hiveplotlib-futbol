"""Scratch: validate the StatsBomb pass schema before committing to binning.

Run: uv run python -m futbol_hiveplots.inspect_schema

Questions this answers (the assumptions the whole plan rests on):
  1. Do pass events carry a start location AND an end location?
  2. Is there a per-event position tag for the passer?
  3. Is the pitch normalized so "toward the opponent goal" is +x for BOTH teams?
     (checked empirically via where each team's shots land)
  4. Pitch dimensions actually present in the data (expect 120 x 80).
"""

import warnings

import pandas as pd
from statsbombpy import sb

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 160)

# 2022 Men's World Cup final, Argentina vs France. Falls back to the first
# available match if the id ever moves.
COMP_ID, SEASON_ID, MATCH_ID = 43, 106, 3869685


def main() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # statsbombpy nags about no-auth open data
        try:
            events = sb.events(match_id=MATCH_ID)
            match_id = MATCH_ID
        except Exception as exc:  # noqa: BLE001
            print(f"final id failed ({exc}); falling back to first WC match")
            matches = sb.matches(competition_id=COMP_ID, season_id=SEASON_ID)
            match_id = int(matches.iloc[0]["match_id"])
            events = sb.events(match_id=match_id)

    print(
        f"\n=== match {match_id}: {events.shape[0]} events, "
        f"teams = {sorted(events['team'].dropna().unique())}"
    )

    passes = events[events["type"] == "Pass"].copy()
    print(f"=== {len(passes)} pass events")
    print("\n--- pass-related columns present ---")
    print(
        [
            c
            for c in passes.columns
            if "pass" in c or c in ("location", "position", "player", "team", "minute")
        ]
    )

    cols = [
        "minute",
        "team",
        "player",
        "position",
        "location",
        "pass_end_location",
        "pass_recipient",
        "pass_outcome",
    ]
    cols = [c for c in cols if c in passes.columns]
    print("\n--- 6 sample passes ---")
    print(passes[cols].head(6).to_string())

    # location is [x, y]; pass_end_location is [x, y]. confirm + dimensions.
    locs = passes["location"].dropna()
    xs = locs.map(lambda v: v[0])
    ys = locs.map(lambda v: v[1])
    print(
        f"\n--- location ranges: x [{xs.min():.1f}, {xs.max():.1f}]  y [{ys.min():.1f}, {ys.max():.1f}]"
    )
    print(
        f"--- pass_end_location present on {passes['pass_end_location'].notna().mean():.0%} of passes"
    )
    print(
        f"--- position present on {passes['position'].notna().mean():.0%} of passes; "
        f"distinct = {sorted(passes['position'].dropna().unique())}"
    )

    # attack-direction check: for each team, where do their SHOTS originate?
    shots = events[events["type"] == "Shot"].copy()
    if len(shots):
        shots["x"] = shots["location"].map(lambda v: v[0])
        print(
            "\n--- shot origin x by team (if ~>90 for both, pitch is normalized attack-right) ---"
        )
        print(
            shots.groupby("team")["x"].agg(["count", "mean", "min", "max"]).to_string()
        )

    # and where do their passes originate, as a sanity cross-check
    passes["x"] = passes["location"].map(lambda v: v[0])
    print("\n--- pass origin x by team ---")
    print(passes.groupby("team")["x"].agg(["count", "mean"]).to_string())


if __name__ == "__main__":
    main()
