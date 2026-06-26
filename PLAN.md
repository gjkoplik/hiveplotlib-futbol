# hiveplotlib-futbol — plan

Status: **exploratory prototype** (started 2026-06-25). Throwaway/satellite repo, not part of
hiveplotlib core. This file is the durable plan and summary; read it before picking the work
back up. Conventions mirror the sibling repos (`hiveplotlib-nn-viz`, `hiveplotlib-bioinformatics-examples`):
uv + `pyproject.toml`, `src/futbol_hiveplots/`, raw data never committed.

## The bet

Soccer passing networks are a large, mature subfield, but nearly all of them are drawn the same
way: nodes placed at each player's **average pitch position**, edges = passes. That layout is
spatially honest and visually a hairball, and crucially **two teams' plots are not comparable**
because the node positions differ from team to team and match to match.

A hive plot throws away literal position and fixes the layout by *role in the structure*, which is
exactly hiveplotlib's thesis. Soccer hands us the structure for free, in two complementary ways
we are pursuing as "yes, and", not "either/or":

- **Zones (primary).** Bin the pitch. The unit of analysis becomes *where the ball is*, not *who
  has it*. This sidesteps every messy thing about players (drift, subs, a back-three that won't
  split into three clean lines), and it makes the layout identical for every team, match, and
  league, which is the strongest possible version of the comparability argument.
- **Roles (sibling).** Nodes = players, partitioned defense / midfield / forward. This is the
  social-network reading (who bridges the team; betweenness/centrality). Different question,
  same tool. Held, not dropped.

What we expect a hive plot to show that the pitch-overlay cannot:
1. **Comparability.** Fixed layout means two teams (or one team across phases) are read side by
   side, apples to apples.
2. **Directionality.** Progression (toward goal) vs recycling (away) separate cleanly, because
   StatsBomb normalizes both teams to attack toward x=120 (verified, see below).
3. **The skip.** A ball that jumps the defensive third straight to the final third (route one)
   shows as a direct def->final edge that possession teams simply won't have.

## What's verified against real data (the assumptions the plan rests on)

Checked via `inspect_schema.py` on the 2022 World Cup final (Argentina vs France):

- Every pass carries a start `location` **and** a `pass_end_location` (100%).
- A per-event `position` tag is present (100%), 21 granular labels (Goalkeeper .. Center Forward).
- **Attack direction is normalized**: both teams' shots originate at mean x ~= 104 (min ~90), so
  "toward goal" = increasing x for *both* teams. This is the linchpin for progression/recycling.
- Pitch is the standard 120 (length) x 80 (width). `pass_outcome` is NaN for completed passes
  (so completed/incomplete is free); `pass_type` tags set pieces (so open-play filtering is free);
  `pass_height`, `pass_switch`, `pass_recipient` all present.

## Binning convention (current, in `data.py`)

- **Thirds** (length / x): `def` [0,40), `mid` [40,80), `fin` [80,120].
- **Channels** (width / y): `L` [0,26.7), `C` [26.7,53.3), `R` [53.3,80].
- **Zone** = `<third>_<channel>`, nine in all. These are the hive plot nodes.
- Default filter: open-play, completed passes. Self-loops (same zone -> same zone) dropped.
- Edge classes fall out of geometry: cross-axis one way = **progression**, the other =
  **recycle**, repeat-axis = **lateral** (within a third).

Grounding result (Argentina, WC final): 265 inter-zone open-play completed passes, **29%
progression / 16% recycle / 54% lateral**. A sane possession-football distribution.

## Design decisions (confirmed with maintainer, 2026-06-25, round 2)

After seeing the first zone figures, the maintainer redirected the v1 encoding. These are settled:

1. **One color per plot.** Multiple edge colors on one hive plot (the green/orange
   progression/recycle split) is uninterpretable where they overlap. Single hue, opacity = volume.
2. **Continuous sort, not categories.** A 3-value sort (L/C/R channel) stacks nodes at three
   points per axis and is uninteresting. Sort by a continuous per-node value: a graph metric
   (betweenness — the bridge players; or strength / eigenvector centrality) or lateral "vertical"
   position within the third.
3. **Node model = players binned into the three thirds.** Decision (2) forces this: a continuous
   per-node value needs a node that *is* an entity with a continuous value, which nine fixed zones
   can't provide. So nodes become players, partitioned into def/mid/fin (by modal position label),
   sorted continuously. Comparability survives at the *frame* level (shared three-third axes + the
   same sort function), even though the player set differs by team — exactly how the C. elegans
   male-vs-hermaphrodite panels compare. The fixed-zone model is **retained** in `data.py` as a
   finer-grained option for later, not deleted.
4. **Repeat axes on, whole game by default.** Draw all passes including within-third; the goal is
   to see the whole game, not a cross-third subset. Cross-third-only is an occasional narrowing
   (e.g. to isolate progression), not the main story.
5. **Comparability is the headline; directionality is deferred** and, when pursued, goes in
   *separate* hive plots, never as colors on one. (Maintainer stood by separate-plots; agreed to
   set directionality aside for now.)

## Node-model clarification + render standard (confirmed, 2026-06-25, round 4)

The maintainer corrected a model mismatch and set the rendering standard. Both settled:

1. **The node model is the pass-endpoint model, not player-means.** A node is one *pass
   endpoint*: every pass contributes an origin node and a destination node, each placed on its
   third's axis at its *actual lateral position* (the pitch-width `y`), with the pass as the edge.
   No aggregation, no graph features. "Every line is one pass, from where it started (which third,
   how wide) to where it ended" -- the one-sentence explanation for a soccer audience. The earlier
   player-node model (one node per player, sorted by betweenness or a *mean* lateral position) is
   **superseded** -- that "mean" was the tell that it aggregated and locked nodes to people, which
   is not what we want. (hiveplotlib places nodes by the sorting variable's *value*, verified, so
   lateral `y` gives true spacing.)
2. **Render standard: datashader for nodes and edges, library-default colormaps, unified color,
   colorbars in-figure, assembled via a generic `HivePlotMatrix`.** The matrix auto-detects a
   shared `vmax` across cells (unified color) and draws the node + edge density colorbars once at
   the bottom. Do not override the colormaps (default copper nodes / default edges; viridis was a
   mistake -- confusing to a lay audience). Render at dpi >= 150 (the earlier datashader figure was
   blurry from low dpi). `plot_passes.py` is the reference implementation; the lineup follows it.
3. **Lean into lateral placement over graph metrics.** Betweenness is only mildly interesting and
   needs explaining; lateral position is the most interpretable and needs no graph theory.

### Figure inventory (current files only; `make figs`)

| Figure | Script / target | What it shows |
| --- | --- | --- |
| `passes_wc2022.png`, `passes_euro2024.png` | `plot_passes` / `passes` | **flagship.** every pass as an arc, two teams, datashaded nodes+edges, unified color, shared colorbars, generic HPM. Reusable `passes_matrix(match_id, teams, label, stem)`. Two matches built: 2022 WC final (Argentina/France) and Euro 2024 final (Spain/England -- a much stronger possession contrast, Spain dense vs England sparse). |
| `lineup_{argentina,france}.png` | `plot_lineups` / `lineups` | per-starter **lineup** on a **fixed 5x5 formation grid** (striker / wings+attacking-mids / midfield / defenders / keeper rows; `position_to_grid`, dict-input HPM) so 4-2-3-1 / 4-3-2-1 read correctly. Within-row lanes standardized by row size (`STANDARD_COLS`) -- apples-to-apples across teams. Reusable entry point `lineup_figure(match_id, team, match_label)`. Name-only cell titles, hand-placed colorbars in the two cells left of the keeper, gray how-to-read note in the two cells right of the keeper. |

(Renamed "atlas" -> "lineups" -- "atlas" was jargon, this is just the starting lineup in
formation. The shelved channel-partition and directional-split figures, and the early zone-model
code, have been deleted along with their now-dead `data.py` helpers; only the pass-endpoint model
remains.)

Reads so far (Argentina vs France, WC final): Argentina denser and more interconnected (455 vs
346 passes); the formation atlas reads as a 4-1-2-3, Enzo the lone pivot, Messi's footprint (Right
Wing) high and right, the back four spread along the defensive row.

### Decisions (round 10)

- **Within-axis sort is now distance-from-center** (`SORT_VAR = "lat_abs"` in `data.py`, `|y-40|`):
  central play near the hub, wide play near the touchlines. Chosen over raw left-to-right because
  it makes the central-vs-wide read clean and is immune to our unresolved handedness (we never
  verified which touchline is StatsBomb y=0, so left/right could be flipped). Trade-off: loses
  flank bias on the flagship; redundant in the atlas (formation grid already shows left/right).
  `lat_y` is kept on every node, so flipping back to a flank-bias view is one token.
- **Height (within-third vertical) rejected**: the three axes already encode verticality
  (def/mid/fin), so a height sort would double-encode it; width is the complementary dimension.
- **Captions converged**: `CAPTION_CORE` in `data.py` is shared by both figures (atlas appends
  "Each panel is one starting player", flagship appends the "both teams share one layout" line).
  Reworded to tie to the hive-plot visual ("near the hub when central, near the outer tip when
  wide"). Dropped "How to read each plot" and "brighter = more passes" (ambiguous: edges run
  light->dark, nodes dark->bright).
- **Two-team titles now carry the pass count** (e.g. "Spain (458 passes)" vs "England (208)") --
  quantifies the possession gap at a glance.
- **Axis ranges are pinned to absolute pitch bounds at construction** (`axis_range_kwargs` in
  `data.py`, passed as `HivePlot(axis_kwargs=...)`), NOT inferred from data. This was a real bug:
  hiveplotlib's default infers each axis's vmin/vmax from the data on it, so a team that only
  played the first 10 m of a 40 m third would have those 10 m stretched across the whole axis --
  misleading and not comparable across teams. We pin width axes to 0..40 (center..touchline) and
  height axes to each third's slice (def 0-40, mid 40-80, fin 80-120); the constructor propagates
  these to the repeat axes automatically. Pinning identical bounds on every cell also unifies them
  by construction, so the matrix `unify_axes` is dropped.
- **Height sort: tried, then dropped as disingenuous.** Sorting within an axis by `x_pos` makes
  the cross-third passes hug the boundaries (high end of the lower third -> low end of the higher),
  but that's mostly a *geometric artifact*: most passes are short, so a pass crossing any line
  tends to straddle it closely, wherever the line is drawn. The thirds are our imposed bins, so
  that pattern shows our binning, not the team -- it can't support a "players think in thirds"
  read. Width is genuine signal by contrast (a def->mid pass can be central or wide, nothing forces
  it). So **width (`lat_abs`) is the sole sort**; the height figure and machinery were removed. If
  the "do players think in thirds" question is ever worth chasing, the honest test is a continuous
  histogram of pass x-locations (look for real breakpoints at the third lines), not a height sort.
- **Caption reworded off "hub"** (which collided two centers -- pitch middle vs figure center):
  width = "inner end is play through the middle of the pitch, outer end is play near the
  touchlines"; height = "inner end is the back of that third, outer end is the front, nearer the
  opponent's goal". Two `CAPTION_CORE` variants in `data.py`.

### Cleanup done (round 5, maintainer-authorized)

Deleted the superseded player-mean model (`plot_players.py`, `plot_players_ds.py`) and the early
zone-grounding plots (`plot_zone_base.py`, `plot_compare.py`), their figures, the now-dead
`player_nodes` / `player_edges` in `data.py`, and the `networkx` dependency (its only user). The
binning helpers (`_third`, `_channel`, `zone_*`, `position_to_*`) stay; `inspect_schema.py` stays
as the schema-validation reference. **Proposed for deletion, pending confirmation:**
`plot_direction.py` + its zone helpers, if the directional split is fully ruled out in favor of
the channel-partition matrix below.

### Decisions (round 5)

- **Lateral `vmin/vmax`: use the unified data range, not absolute 0..80.** Each third spans the
  full pitch width by definition, so the lateral range is identical everywhere and the unified
  range already is the pitch width. No anchoring needed.
- **Directional split and channel-partition matrix both deleted.** Direction was weak as a sort;
  the channel matrix turned out to be mostly short lateral passes and didn't earn its place. Both
  `plot_direction.py` and `plot_channels.py` (and the early zone-model code) have been removed,
  along with their now-dead `data.py` helpers (`zone_*`, channel constants, `expand_edges`).

**Data recency (checked 2026-06-25):** freshest open-data competitions are Euro 2024 / Copa
America 2024 (men), Women's Euro 2025; most recent men's World Cup is 2022. The 2026 World Cup is
**not** in open data and won't be mid-tournament (live data is StatsBomb's commercial product), so
no real-time 2026 angle. Euro 2024 / Copa America 2024 are the freshest men's options if a story
newer than 2022 is wanted. (See `DATASETS.md`.)

### Follow-ups (carry forward)

- **A stronger matchup / a marquee player.** Two finalists look too similar; a deliberate
  possession-vs-direct contrast (or a famous passer) would make the figures pop. Data-availability
  reality, since this drives the choice:
  - The **2010 World Cup final (Spain tiki-taka vs Netherlands) is NOT in open data** (open-data WC
    seasons: 2022, 2018, 1990, 1986, and older). For tiki-taka, use **Messi-era Barcelona La Liga**
    (multiple seasons present, the Guardiola goldmine) or **Spain at Euro 2024** (present).
  - **Liverpool / Premier League is not in open data**, so Thiago at Liverpool isn't available.
    Thiago's **early Barcelona years (2009-2013) fall inside the La Liga open data**, though, so a
    Thiago-the-passer lineup is feasible there. A marquee-player lineup is now a one-call change
    via `lineup_figure(match_id, team, label)` (would extend to filter a single player).
  - **Champions League IS available** (finals 1999/2000-2018/2019): the Barcelona finals (2009,
    2011, 2015) are peak tiki-taka. **Euro 2024 final was Spain 2-1 England** (maintainer watched
    it, Spain excellent) -- a strong possession reference.
  - A clean "direct / route-one" side is harder to source in open data; worth a scout when we pick.
- **Time dimension (point 3, noted as a follow-up per maintainer).** Most compelling hook: this
  final's late momentum swing (France dormant until ~80', then two goals in 97s). A per-phase
  matrix (e.g. 0-80' vs 80'-end, filtering passes by `minute`) of France going from quiet to
  surging is a real story already in the data. Not urgent; flagged here for when we want it.

## Workstreams

WS0 and the binning above are **done** (scaffold, schema validation, base zone plot, grounding
figures). Remaining, roughly in dependency order:

- **WS1 — Base zone hive plot, polished.** One team, one match, thirds-as-axes. Resolve the v1
  design decisions (below): overplot vs explicit width-weighting, alpha, colorblind-safe palette,
  channel handedness. Pair it with the **pitch-overlay "before"** (mplsoccer, the `pitch` extra)
  so the notebook can motivate "here's the hairball, here's the hive plot".
- **WS2 — The channels-as-axes rotation.** Same binned data, axes = `L` / `C` / `R` channels;
  progression now runs *along* each axis and the cross-axis edges are **switches of play**
  (center-to-wide, wing-to-wing). The narrative beat: build the thirds view, then rotate it.
- **WS3 — Team comparison (the comparability payoff).** A possession side vs a direct/counter
  side on the **same fixed layout**, two-panel `HivePlotMatrix`. This is the figure that makes the
  whole bet land. Candidate: a tiki-taka Barca match vs a route-one performance.
- **WS4 — Direction-as-panels HPM.** Per Gary: split toward-goal vs away-from-goal into
  side-by-side panels rather than coloring one busy plot. Generalize the move: the panel axis can
  be *any* edge split — direction, **ground vs aerial** (the aerial panel is where switches and
  route-one balls live), completed vs incomplete (where passing breaks, and in which third), and
  the sleeper, **score state** (drawing / leading / trailing): does this team stop progressing the
  moment they go a goal up? Fixed layout makes the behavioral *change* pop across panels.
  This is also where **lateral passes** get a clean home (their own panel) instead of the busy
  repeat-axis overlay from the full base figure.
- **WS5 — The 11-starter atlas HPM.** Eleven panels, one per starter, only that player's passes,
  all on the identical zone layout, ordered like a formation. Becomes a role-fingerprint atlas
  (regista dense and central, full-back pinned to one channel, striker sparse and high). Design
  risk to handle up front: per-player networks are sparse and high-variance in density, so use a
  **shared edge-width/alpha scale across all panels** or auto-scaling will lie about who carried
  the ball. The density variance is the content.
- **WS6 — Role-node sibling.** Players grouped defense / midfield / forward, edges = player-to-
  player passes; surface betweenness/centrality (hiveplotlib's `node_graph_metrics`). The social-
  network reading. Different question from the zone views; keep it clearly separate.
- **WS7 — Weight by value, not volume.** Raw pass count over-rewards boring CB-to-CB recycling.
  Weight edges by progressive distance gained, or expected-threat-added if we bring in an xT grid.
  Changes what the plots *say* (a possession side's huge low-value volume becomes visually
  distinct from genuine progression). Refinement, deferred, but recorded early because it is the
  difference between a pretty picture and an honest one.

## Time dimension — placeholder for the next iteration

Gary's inclination (endorsed): break a match into time subsets and render a `HivePlotMatrix` over
time (15-minute buckets, or by score state per WS4). **This is cheap to add later** and does not
change any of the core machinery: it is the same nodes (zones are fixed) and the same edge
binning, just filtered by `minute` before aggregation, then laid out as matrix panels. No reason
to block current planning on it; slot it as a fast follow once the static views read well. The one
thing to decide when we get there: fixed time buckets vs event-driven segments (e.g. split on
goals / red cards), which is more informative but irregular.

## Open decisions (carry into WS1 unless noted)

1. **Lead narrative.** Comparability (fixed layout beats pitch-overlay) vs directionality
   (progression/recycle/skip). *Asked Gary; still open.* Leaning comparability as the headline
   with directionality as the mechanism that makes a single panel worth reading.
2. **Node granularity.** 3 channels (current) vs 5 lanes vs a finer grid. 3 is clean for v1; finer
   may make richer plots once the encoding is settled.
3. **Lateral passes.** Their own panel (WS4), a repeat axis (busy, per the full figure), or folded
   into "recycle". Current lean: own panel.
4. **Weight encoding.** Overplot identical curves (current, canonical density look) vs explicit
   per-edge width/alpha from aggregated counts. Overplot is simplest; width is more controllable.
5. **Channel handedness.** Confirm which touchline is StatsBomb y=0 before any "builds down the
   left" claim. Structure is unaffected; only the L/R label is.
6. **GK.** In the zone framing this is a non-issue (GK passes are just defensive-third events) —
   a quiet win for zones over roles, where the GK is an awkward fourth thing.
7. **Set pieces.** Default open-play only; a set-piece view is a possible separate panel.
8. **Flagship dataset.** Possession-dominant team for legibility. Barca Messi-era La Liga (full in
   open data) or a specific WC team. Pick per figure.

## Prior art / novelty (provisional — do a real scan before any writeup)

Passing-network analysis is large and well-tooled: academic foundation (Peña & Touchette 2012,
"A network theory analysis of football strategies", arXiv:1206.6904), practitioner tooling
(`mplsoccer`, Soccermatics), and a steady stream of centrality/betweenness work. **All of it that
was located uses pitch-positioned node-link layouts.** No located use of a hive plot for soccer
passing structure. The defensible novelty is the **fixed-layout comparability** plus the
**zone-flow encoding** (progression / recycle / skip / lateral reading off geometry). Caveat, as
with nn-viz: "novel" would mean none located after an adversarial search, not provably first; run
a proper prior-art pass (a deep-research workflow) before writing any of this up.

## Graduation path

If a figure sings, it graduates into a hiveplotlib wiki example: a **gallery** notebook for a
single focused view (e.g. the base zone plot), or a **tutorial** for the full real-dataset story
(motivation, the pitch-overlay vs hive plot contrast, references with StatsBomb citation). Until
then everything lives here.
