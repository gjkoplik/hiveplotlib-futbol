# hiveplotlib-futbol

Exploring [hiveplotlib](https://hiveplotlib.readthedocs.io) with football (soccer) passing data.

The bet, in one line: passing networks are almost always drawn on the pitch (nodes at average
player position), which is a hairball and not comparable across teams. A hive plot fixes the
layout by structure instead. We bin the pitch into **zones** (thirds x channels) and read ball
**progression, recycling, the midfield-skip, and lateral movement** off the geometry, on a layout
that is identical for every team and match.

Exploratory/satellite repo, not part of hiveplotlib core. See [`PLAN.md`](PLAN.md) for the full
plan and status, and [`DATASETS.md`](DATASETS.md) for data sourcing and the schema.

## Quick start

```bash
make install-ds       # uv sync incl. the datashader backend (the figures need it)
make figs             # render the flagship + the formation lineups to figures/
make passes           # just the flagship (every pass as a lateral arc, two teams)
make lineups          # just the per-starter lineups, laid out in the team's formation
make format           # ruff
```

Data is fetched from [StatsBomb open data](https://github.com/statsbomb/open-data) at runtime and
never committed (attribution: "Data provided by StatsBomb"; see `DATASETS.md` for license notes).
