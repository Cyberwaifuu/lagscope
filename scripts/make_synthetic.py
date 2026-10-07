"""Generate the synthetic 274-day fixture with a known lagged effect."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
START, END = "2025-12-01", "2026-08-31"
TRUE_ALPHA = -0.05
TRUE_EFFECTS = {"s_gov": (3, 0.25), "s_blog": (1, 0.45)}
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "synthetic_274.csv"


def ar1(rng: np.random.Generator, size: int, phi: float, scale: float) -> np.ndarray:
    """First-order autoregressive series starting at zero."""
    values = np.zeros(size)
    shocks = rng.normal(0.0, scale, size)
    for t in range(1, size):
        values[t] = phi * values[t - 1] + shocks[t]
    return values


def make_frame(seed: int = SEED) -> pd.DataFrame:
    """Three daily series where s_mass follows s_gov after 3 days and s_blog after 1 day."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(START, END, freq="D")
    size = len(dates)
    gov = np.clip(ar1(rng, size, 0.5, 0.25), -1, 1)
    blog = np.clip(ar1(rng, size, 0.4, 0.3), -1, 1)
    mass = np.full(size, TRUE_ALPHA) + rng.normal(0.0, 0.12, size)
    for name, series in (("s_gov", gov), ("s_blog", blog)):
        lag, beta = TRUE_EFFECTS[name]
        mass[lag:] += beta * series[:-lag]
    mass = np.clip(mass, -1, 1)
    return pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "s_gov": gov, "s_blog": blog, "s_mass": mass}).round(6)


def main(argv: list[str]) -> int:
    """Write the fixture, or with --check compare it with the committed file."""
    content = make_frame().to_csv(index=False, lineterminator="\n")
    if "--check" in argv:
        if OUTPUT.read_text(encoding="utf-8") != content:
            print(f"{OUTPUT.name} differs from the generator output; run the script without --check")
            return 1
        print(f"{OUTPUT.name} matches the generator (seed {SEED})")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
