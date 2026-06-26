# Data

Football passing data for hive plots. The common thread: a pass has an **origin and a
destination on a normalized pitch**, which is exactly the structure the zone hive plot needs.

Raw data is never committed. `statsbombpy` fetches from StatsBomb's public open-data repo at
runtime and caches locally.

## Source: StatsBomb open data

- Repo: https://github.com/statsbomb/open-data — free JSON, no authentication required.
- Access: `statsbombpy` (`from statsbombpy import sb`). Key calls: `sb.competitions()`,
  `sb.matches(competition_id, season_id)`, `sb.events(match_id)`. With no API credentials it reads
  the open-data repo directly.
- Pitch model: 120 (length) x 80 (width). **Both teams are normalized to attack toward x=120**, so
  increasing x is "toward goal" for everyone (verified empirically; see below).

### License (resolve before anything ships publicly)

StatsBomb open data is free **for non-commercial use with attribution** ("Data provided by
StatsBomb"), and may not be used for betting. The loader fetches at runtime and never commits the
files, which fits those terms for an exploratory/academic example. Two things to confirm before a
public writeup, same caution as the bioinformatics repo's RegulonDB note: (1) the exact current
wording of the StatsBomb Open Data User Agreement and whether the intended use (a docs example) is
clearly covered; (2) that attribution is present on every shipped figure and the notebook.

## Schema (the fields we use)

Pass events (`events[events["type"] == "Pass"]`) carry, all present on 100% of passes in the match
checked:

| Field | Meaning |
| --- | --- |
| `location` | `[x, y]` start of the pass |
| `pass_end_location` | `[x, y]` end of the pass |
| `position` | passer's position, 21 granular labels (Goalkeeper .. Center Forward) |
| `pass_outcome` | **NaN = completed**; "Incomplete" / "Out" / "Pass Offside" otherwise |
| `pass_type` | **NaN = open play**; set pieces tagged (Throw-in, Free Kick, Corner, Goal Kick, Kick Off) |
| `pass_height` | Ground / Low / High Pass (for the aerial panel idea) |
| `pass_switch` | flagged switches of play |
| `pass_recipient` | receiving player (available for player-level variants) |
| `team`, `player`, `minute` | for splitting by team, player, and time |

## Binning (in `data.py`)

- Thirds (x): `def` [0,40), `mid` [40,80), `fin` [80,120].
- Channels (y): `L` [0,26.7), `C` [26.7,53.3), `R` [53.3,80].
- Zone = `<third>_<channel>` (nine zones, the hive plot nodes).
- **Open question:** which touchline is y=0 (channel handedness). Does not affect structure, only
  the L/R label; pin before any "builds down the left" claim.

## Candidate matches / competitions (open data, subject to change)

Verified present: **2022 Men's World Cup** (competition_id 43, season_id 106); the final is
match_id 3869685 (Argentina vs France), used for grounding.

Others StatsBomb has published at various times, worth pulling for specific stories:

| Story | Look for |
| --- | --- |
| Possession / tiki-taka (legible base + comparison anchor) | Messi-era Barcelona La Liga (multiple seasons in open data) |
| Direct / counter contrast (WS3) | a route-one performance to set against a possession side |
| Tournament small-multiples (HivePlotMatrix) | a full World Cup or Euro group/knockout set |
| Women's game | Women's World Cup, FA WSL, NWSL |

Pick the flagship per figure once the encoding is settled; possession-dominant teams make the zone
plot most legible. Confirm availability with `sb.competitions()` at the time, since the published
set changes.

### Recency (checked 2026-06-25)

The freshest competitions in the open data are **UEFA Euro 2024** and **Copa America 2024** (men),
**Women's Euro 2025**, and the 2023/2024 top-five-league seasons. The most recent **men's World
Cup is 2022**.

**No live / current-tournament data.** The 2026 World Cup (in progress now) is *not* in the open
data and won't be mid-tournament: live in-tournament data is StatsBomb's commercial product; the
free open data is released selectively and after the fact. A real-time 2026 angle is not possible
with this source. If a story fresher than 2022 is wanted, **Euro 2024 / Copa America 2024** are
the move.

**Champions League is available** as the **finals** across ~20 seasons (1999/2000 through
2018/2019, plus a few 1970s). That includes the Messi-era Barcelona finals (2008/09, 2010/11,
2014/15) -- peak tiki-taka -- which are strong possession references. **No Premier League** in the
open data, so no Liverpool / no Thiago-at-Liverpool; Thiago's early Barcelona years (2009-2013)
fall inside the La Liga open data.

**Strong style references on hand:** Euro 2024 (the final was **Spain 2-1 England**; Spain were
excellent and possession-led) and the Barcelona Champions League finals for tiki-taka.
