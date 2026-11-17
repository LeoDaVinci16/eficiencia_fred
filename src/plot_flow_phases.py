"""Plot the supersonic flow measurements (3806, 3801) together with an E800 phase en cours.

The phase is shown behind the flow as coloured background bands, one colour per
phase; one figure is made per phase signal in PHASES (Evapora, Extract). Only the
period where a flow measurement overlaps the E800 export is shown; flow files
with no overlap are skipped (and reported).

Output: figures/combined/flow_3806_evapora.png (Evapora),
        figures/combined/flow_3806_extract.png (Extract)
"""
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator

import plot_e800
import plot_supersonic

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "figures" / "combined"
SUPERSONIC_DIR = PROJECT_DIR / "supersonic_Arnau"

FLOW_FILES = {
	"3806 (139.7 mm)": (SUPERSONIC_DIR / "2026-11-04" / "3806_139.7mm_2026-10-30.csv", "#d9730d"),
	"3801 (88.9 mm)": (SUPERSONIC_DIR / "2026-11-10" / "3801_88.9mm_2026-11-04.csv", "#2a6fdb"),
}

# E800 phase shown as background bands on the flow panel, from dataExport_modes_e800.csv.
# One figure per entry: name -> (column, output file)
PHASES = {
	"Evapora": ("PHASES_en_cours_Evapora", "flow_3806_evapora.png"),
	"Extract": ("PHASES_en_cours_Extract", "flow_3806_extract.png"),
}
# Phase descriptions (Catalan), used in legends and tables; phase 0 = apagat
PHASE_NAMES = {
	"Extract": {
		0: "Apagat",
		1: "Inertització amb nitrogen",
		2: "Posar en buit",
		3: "Posar a pressió atmosfèrica",
		4: "Càrrega de sòlids",
		5: "Càrrega de dissolvent",
		6: "Extracció",
		7: "Filtració sota pressió",
		8: "Assecat a pressió atmosfèrica",
		9: "Assecat al buit",
		10: "Descàrrega residus",
	},
}
# Background colour per non-zero phase (assigned in ascending phase order)
PHASE_COLORS = ["#2a6fdb", "#1a7f37", "#8250df", "#bf3989", "#0e8a8a", "#b08800", "#6e7781"]
PHASE_ALPHA = 0.18
# Minimum horizontal distance between two shown time labels (inches)
LABEL_MIN_GAP_IN = 0.12


def main():
	for phase_name in PHASES:
		plot(phase_name)


def hide_crowded_labels(ax, times, x0, x1):
	"""Keep a tick mark at every time but drop labels too close to the previous shown one."""
	fig = ax.figure
	fig.canvas.draw()
	width_in = ax.get_window_extent().width / fig.dpi
	min_gap = (x1 - x0) * (LABEL_MIN_GAP_IN / width_in)
	last = None
	labels = []
	for t in times:
		if last is None or t - last >= min_gap:
			labels.append(f"{t:%d.%m %H:%M}")
			last = t
		else:
			labels.append("")
	ax.set_xticks(mdates.date2num(times), labels)


def plot(phase_name):
	phase_col, out_name = PHASES[phase_name]
	phase_label = f"E800 phase en cours - {phase_name}"

	modes = plot_e800.load("modes")
	t_start, t_end = modes.index[0], modes.index[-1]

	# Keep only the flows that overlap the E800 phase record, clipped to the overlap
	flows = {}
	for name, (path, color) in FLOW_FILES.items():
		df = plot_supersonic.load(path)[0]
		df = df[(df["time"] >= t_start) & (df["time"] <= t_end)]
		if df.empty:
			print(f"skip {name}: no overlap with the E800 export ({t_start} - {t_end})")
			continue
		flows[name] = (df, color)
	if not flows:
		raise SystemExit("No supersonic measurement overlaps the E800 export.")

	x0 = min(df["time"].iloc[0] for df, _ in flows.values())
	x1 = max(df["time"].iloc[-1] for df, _ in flows.values())
	phase = modes[phase_col].loc[x0:x1].astype(float)

	fig_h = 6
	fig, ax_f = plt.subplots(figsize=(14, fig_h))

	for name, (df, color) in flows.items():
		ax_f.plot(df["time"], df["MEASURE"], color=color, linewidth=1,
				  label=f"Volume flow {name} (supersonic)")
	ax_f.set_title(f"Volume flow and {phase_label}", loc="left", fontsize=10, color=plot_e800.INK)
	ax_f.set_ylabel("m³/h", color=plot_e800.MUTED)

	# E800 phase as background bands: one colour per phase, phase 0 (idle) left blank
	change = phase.ne(phase.shift())
	starts = phase.index[change]
	values = phase[change].astype(int)
	ends = list(starts[1:]) + [x1]
	phase_ids = sorted(p for p in values.unique() if p != 0)
	colors = {p: PHASE_COLORS[i % len(PHASE_COLORS)] for i, p in enumerate(phase_ids)}
	for start, end, p in zip(starts, ends, values):
		if p in colors:
			ax_f.axvspan(start, end, color=colors[p], alpha=PHASE_ALPHA, linewidth=0, zorder=0)

	handles = ax_f.get_legend_handles_labels()[0]
	names = PHASE_NAMES.get(phase_name, {})
	handles += [Patch(facecolor=colors[p], alpha=PHASE_ALPHA,
					  label=f"{names[p]} ({p})" if p in names else f"{phase_name} phase {p}")
				for p in phase_ids]
	# Legend below the figure (it is too wide to sit next to the panel title)
	ncol = min(len(handles), 4 if names else 5)
	legend_rows = -(-len(handles) // ncol)
	fig.legend(handles=handles, loc="lower center", ncol=ncol, frameon=False, fontsize=8)

	# Real time axis limited to the overlap; ticks at every change time from the event table
	import table_flow_phases  # local import: that module imports this one
	event_times = table_flow_phases.event_table(phase_name)["time"]
	ax_f.set_xlim(x0, x1)
	plot_e800.style(ax_f)
	ax_f.xaxis.set_major_locator(FixedLocator(mdates.date2num(event_times)))
	ax_f.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:%M"))
	ax_f.tick_params(axis="x", labelsize=6, labelrotation=60)
	for label in ax_f.get_xticklabels():
		label.set_horizontalalignment("right")
		label.set_rotation_mode("anchor")
	hide_crowded_labels(ax_f, event_times, x0, x1)

	fig.suptitle(f"Supersonic flow and E800 {phase_name} phase - {x0:%d.%m %H:%M} to {x1:%d.%m %H:%M}",
				 x=0.01, ha="left", color=plot_e800.INK)
	fig.tight_layout(rect=(0, 0.3 * legend_rows / fig_h, 1, 1))
	OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
	out = OUTPUT_DIR / out_name
	fig.savefig(out, dpi=150)
	plt.close(fig)
	print(f"-> {out}")


if __name__ == "__main__":
	main()
