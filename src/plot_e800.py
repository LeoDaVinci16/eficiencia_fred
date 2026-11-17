"""Plot the E800 SCADA exports (modes, levels, temperatures).

Reads raw/csv/dataExport_{modes,nivells,temp}_e800.csv and writes one PNG per
file to figures/e800/. Sensors with alarm limits (`<tag>_mini` / `<tag>_maxi`)
get their own panel with the limits drawn as dashed lines; limits that are
always 0 (not configured) are skipped.
"""
from pathlib import Path
import math

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_DIR / "raw" / "csv"
OUTPUT_DIR = PROJECT_DIR / "figures" / "e800"

INK = "#1f2328"
MUTED = "#6e7781"
GRID = "#d8dee4"
SERIES = "#2a6fdb"
LIMIT = "#c4432b"


def load(name):
	df = pd.read_csv(INPUT_DIR / f"dataExport_{name}_e800.csv", encoding="utf-8-sig")
	df["t_stamp"] = pd.to_datetime(df["t_stamp"])
	return df.set_index("t_stamp").sort_index()


def style(ax):
	ax.grid(True, color=GRID, linewidth=0.6)
	for side in ("top", "right"):
		ax.spines[side].set_visible(False)
	for side in ("left", "bottom"):
		ax.spines[side].set_color(MUTED)
	ax.tick_params(colors=MUTED, labelsize=8)
	ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))


def sensor_tags(df):
	"""Tags that are measurements, i.e. not a _mini/_maxi limit column."""
	return sorted(c for c in df.columns if not c.endswith(("_mini", "_maxi")))


def plot_sensors(df, title, unit, out_name, ncols=2):
	tags = sensor_tags(df)
	nrows = math.ceil(len(tags) / ncols)
	fig, axes = plt.subplots(nrows, ncols, figsize=(14, 2.6 * nrows), sharex=True, squeeze=False)

	for ax, tag in zip(axes.flat, tags):
		ax.plot(df.index, df[tag], color=SERIES, linewidth=0.8)
		for suffix in ("mini", "maxi"):
			limit = df.get(f"{tag}_{suffix}")
			if limit is not None and (limit != 0).any():
				ax.plot(df.index, limit, color=LIMIT, linewidth=1, linestyle="--")
				ax.annotate(suffix, (1, limit.iloc[-1]), xycoords=("axes fraction", "data"),
							xytext=(3, 0), textcoords="offset points",
							va="center", fontsize=7, color=MUTED)
		ax.set_title(tag, loc="left", fontsize=10, color=INK)
		ax.set_ylabel(unit, fontsize=8, color=MUTED)
		style(ax)

	for ax in axes.flat[len(tags):]:
		ax.set_visible(False)

	fig.suptitle(title, x=0.01, ha="left", color=INK)
	fig.tight_layout()
	save(fig, out_name)


def plot_modes(df):
	cols = list(df.columns)
	fig, axes = plt.subplots(len(cols), 1, figsize=(14, 2 * len(cols)), sharex=True, squeeze=False)
	for ax, col in zip(axes.flat, cols):
		ax.step(df.index, df[col].astype(float), where="post", color=SERIES, linewidth=0.9)
		ax.set_title(col, loc="left", fontsize=10, color=INK)
		if df[col].dtype == bool:
			ax.set_yticks([0, 1], ["False", "True"])
		else:
			ax.yaxis.get_major_locator().set_params(integer=True)
		style(ax)
	fig.suptitle("E800 - modes and phases", x=0.01, ha="left", color=INK)
	fig.tight_layout()
	save(fig, "e800_modes.png")


def save(fig, name):
	OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
	out = OUTPUT_DIR / name
	fig.savefig(out, dpi=150)
	plt.close(fig)
	print(f"-> {out}")


def main():
	plot_modes(load("modes"))
	plot_sensors(load("nivells"), "E800 - levels (LT)", "level", "e800_nivells.png")
	plot_sensors(load("temp"), "E800 - temperatures (TT)", "°C", "e800_temp.png")


if __name__ == "__main__":
	main()
