.PHONY: install install-pitch install-ds format clean passes lineups figs

install:
	uv sync --extra dev

install-pitch:
	uv sync --extra dev --extra pitch

install-ds:
	uv sync --extra dev --extra datashader

# --- figures (all need the datashader extra; run install-ds first) ---
passes:        ## FLAGSHIP: two-team passing matrices (2022 WC final + Euro 2024 final)
	uv run python -m futbol_hiveplots.plot_passes

lineups:       ## per-starter lineup in formation, both teams, datashader HPM
	uv run python -m futbol_hiveplots.plot_lineups

figs: passes lineups

format:
	uv run ruff format
	uv run ruff check --fix

clean:
	rm -rf figures
