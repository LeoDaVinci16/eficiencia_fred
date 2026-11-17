"""Event tables for the combined plots: 3806 volume flow level and an E800 phase
(one table for Evapora, one for Extract).

The flow is snapped to the nearest of the levels 0 / 80 / 100 m³/h. A level that
lasts a single sample (1 min) is treated as a transition ramp and merged into
the previous level. One row is written every time the flow level or the phase
changes, over the same overlap window as plot_flow_phases.py.

Output: figures/combined/flow_3806_evapora_table.csv (Evapora),
        figures/combined/flow_3806_extract_table.csv (Extract)
        (also printed as Markdown)
"""
import pandas as pd

import plot_e800
import plot_supersonic
from plot_flow_phases import FLOW_FILES, OUTPUT_DIR, PHASE_NAMES, PHASES

FLOW_NAME = "3806 (139.7 mm)"
# One table per phase signal: name -> output file
TABLES = {
	"Evapora": "flow_3806_evapora_table.csv",
	"Extract": "flow_3806_extract_table.csv",
}
LEVELS = [0, 80, 100]
MIN_RUN = 2  # samples a flow level must last to count as a change


def flow_levels(flow):
	"""Snap to LEVELS and drop runs shorter than MIN_RUN samples."""
	snapped = flow.apply(lambda v: min(LEVELS, key=lambda lvl: abs(v - lvl)))
	run_id = snapped.ne(snapped.shift()).cumsum()
	run_len = snapped.groupby(run_id).transform("size")
	return snapped.where(run_len >= MIN_RUN).ffill().bfill().astype(int)


def main():
	for phase_name, out_name in TABLES.items():
		print(f"\n## 3806 volume flow vs {phase_name} phase\n")
		build(phase_name, out_name)


def build(phase_name, out_name):
	table = event_table(phase_name)

	OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
	out = OUTPUT_DIR / out_name
	table.to_csv(out, index=False, encoding="utf-8-sig")

	shown = table.assign(time=table["time"].dt.strftime("%d.%m %H:%M:%S"))
	print(shown.to_markdown(index=False))
	print(f"\n-> {out}")


def event_table(phase_name):
	"""Rows (flow level, phase, time) at every change of either signal."""
	phase_col = PHASES[phase_name][0]
	temp = plot_e800.load("modes")  # E800 export window
	df = plot_supersonic.load(FLOW_FILES[FLOW_NAME][0])[0]
	df = df[(df["time"] >= temp.index[0]) & (df["time"] <= temp.index[-1])]
	x0, x1 = df["time"].iloc[0], df["time"].iloc[-1]

	flow = flow_levels(df.set_index("time")["MEASURE"])
	phase = plot_e800.load("modes")[phase_col].loc[:x1].astype(int)

	# Change points of each signal inside the window (plus the window start)
	flow_changes = flow[flow.ne(flow.shift())].index
	phase_changes = phase[phase.ne(phase.shift())].loc[x0:].index
	times = sorted(set(flow_changes) | set(phase_changes) | {x0})

	rows = []
	for t in times:
		rows.append({
			"Volume flow (0-80-100)": int(flow.asof(t)),
			"phase": int(phase.asof(t)),
			"time": t,
		})
	table = pd.DataFrame(rows)
	# Drop rows where neither value actually changed (e.g. two events at the same state)
	same = table[["Volume flow (0-80-100)", "phase"]].eq(
		table[["Volume flow (0-80-100)", "phase"]].shift()).all(axis=1)
	table = table[~same].reset_index(drop=True)
	names = PHASE_NAMES.get(phase_name)
	if names:
		table.insert(2, "phase name", table["phase"].map(names))
	return table


if __name__ == "__main__":
	main()
