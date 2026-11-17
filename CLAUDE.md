# CLAUDE.md

Project report and analysis for improving the efficiency of the chilled/cooling water ("fred") circuits at Euromed S.A. (Mollet del Vallès). The report is written in **Catalan**.

## Layout

- `projecte-eficiencia.qmd` — main Quarto report (Python/Jupyter chunks, `arnau-pdf` custom format, renders to `.pdf`/`.tex`). Citations in `references.bib` (IEEE CSL).
- `src/` — standalone Python scripts (pandas + matplotlib):
  - `excel2csv.py` — converts `raw/dataExport/*.xlsx` (SCADA exports) to `raw/csv/*.csv`, one file per sheet.
  - `plot_e800.py` — plots E800 SCADA exports (modes, levels, temperatures) → `figures/e800/`.
  - `plot_supersonic.py` — plots FLUXUS G608 ultrasonic flowmeter CSVs (with `#` metadata header) → `figures/supersonic/`.
  - `plot_flow_phases.py` — 3806 supersonic volume flow with E800 phases en cours (Evapora, Extract) as coloured background bands → `figures/combined/flow_3806_<phase>.png`. Imports `plot_e800` and `plot_supersonic` as modules; x-axis ticks come from `table_flow_phases.event_table()`.
  - `table_flow_phases.py` — event table (flow level 0/80/100, phase, phase name, time), one row per change of either signal → `figures/combined/flow_3806_<phase>_table.csv`.
- `raw/` — raw SCADA exports (`dataExport/`) and converted CSVs (`csv/`).
- `supersonic_Arnau/` — flowmeter CSVs, one folder per download date; filenames are `<point>_<pipe-diameter>mm_<start-date>.csv`.
- `DDIB/` — De Dietrich "Remodelació circuits de fred" study documents (P&IDs, calculations, equipment lists). Reference material; do not modify.
- `figures/` — generated plots (PNG files are git-ignored).

## Commands

```sh
python src/excel2csv.py
python src/plot_e800.py
python src/plot_supersonic.py [folders or CSVs...]
python src/plot_flow_phases.py
python src/table_flow_phases.py
quarto render projecte-eficiencia.qmd
```

Scripts resolve paths relative to the project root (`Path(__file__).resolve().parent.parent`), so they can be run from anywhere.

## Notes

- The report reads SuperSònic session data from an external SQLite DB at `C:/Users/ArnauCoronado/Documents_local/euromed/fluxus_serial/database/database.db`.
- Code style in `src/`: tabs for indentation, module docstring describing inputs/outputs, path constants at the top, `main()` entry point.
- `*.pdf`, `*.png`, `*.jpeg` are git-ignored.
