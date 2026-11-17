"""Plot FLUXUS G608 ultrasonic flowmeter exports (CSV with '#' metadata header).

Usage:
    python src/plot_supersonic.py                    # plots the default folders below
    python src/plot_supersonic.py path/to/folder ... # or any folders / CSV files

For each CSV it writes a PNG to figures/supersonic/ with the volume flow over time.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "supersonic_Arnau"
DEFAULT_DIRS = [DATA_DIR / "2026-11-04", DATA_DIR / "2026-11-10"]
OUTPUT_DIR = PROJECT_DIR / "figures" / "supersonic"

INK = "#1f2328"
MUTED = "#6e7781"
GRID = "#d8dee4"
SERIES = "#2a6fdb"


def read_meta(path: Path) -> tuple[dict[str, str], int]:
    """Return the '# key : value' metadata and the line index of the column header."""
    meta: dict[str, str] = {}
    with path.open(encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh):
            if line.startswith("#"):
                key, _, val = line[1:].partition(":")
                meta[key.strip().lstrip("\\").rstrip(":").strip()] = val.strip().lstrip(":").strip()
            elif line.startswith("CHANNEL"):
                return meta, i
    raise ValueError(f"No CHANNEL header found in {path}")


def storage_step(meta: dict[str, str]) -> pd.Timedelta:
    m = re.search(r"(\d{2}):(\d{2}):(\d{2})", meta.get("Storage Rate", ""))
    return pd.Timedelta(hours=int(m[1]), minutes=int(m[2]), seconds=int(m[3])) if m else pd.Timedelta(seconds=1)


def load(path: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    meta, header_line = read_meta(path)
    df = pd.read_csv(
        path,
        skiprows=header_line,
        na_values=["???", "---", ""],
        index_col=False,  # rows have fewer fields than the header (SCNR is empty)
    )
    for col in ("MEASURE", "SSPEED", "AMP", "SCNR"):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    start = pd.to_datetime(f"{meta['DATE']} {meta['TIME']}", format="%d.%m.%Y %H:%M:%S")
    step = storage_step(meta)
    df["time"] = start + step * pd.RangeIndex(len(df))
    return df, meta


def plot_file(path: Path) -> Path:
    df, meta = load(path)
    step_h = storage_step(meta) / pd.Timedelta(hours=1)
    volume = df["MEASURE"].fillna(0).sum() * step_h  # m3/h * h = m3

    panels = [("MEASURE", "Volume flow [m³/h]")]
    fig, ax = plt.subplots(figsize=(12, 4.5))
    axes = [ax]

    for ax, (col, label) in zip(axes, panels):
        ax.plot(df["time"], df[col], color=SERIES, linewidth=1.2)
        ax.set_ylabel(label, color=INK)
        ax.grid(True, color=GRID, linewidth=0.6)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(MUTED)
        ax.tick_params(colors=MUTED)

    flow = df["MEASURE"]
    axes[0].set_title(
        f"Point {meta.get('Meas. Point No.', '?').split(':')[-1]} · "
        f"OD {meta.get('Outer Diameter', '?')} · {meta.get('Storage Rate', '')}\n"
        f"mean {flow.mean():.2f} m³/h · median {flow.median():.2f} m³/h · "
        f"max {flow.max():.2f} m³/h · total ≈ {volume:.1f} m³",
        loc="left", color=INK, fontsize=11,
    )
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:%M"))
    axes[-1].set_xlabel("Time", color=INK)
    fig.suptitle(path.name, x=0.01, ha="left", color=MUTED, fontsize=9)
    fig.tight_layout()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / f"{path.stem}.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main(args: list[str]) -> None:
    targets = [Path(a) for a in args] or DEFAULT_DIRS
    files: list[Path] = []
    for t in targets:
        files += sorted(t.glob("*.csv")) if t.is_dir() else [t]
    if not files:
        sys.exit("No CSV files found.")
    for f in files:
        print(f"{f.name} -> {plot_file(f)}")


if __name__ == "__main__":
    main(sys.argv[1:])
