"""Statistiques sur les fréquences strictement positives, comme dans Colab."""

import numpy as np


def describe(frequencies):
    values = np.array([v for v in frequencies.values() if v > 0], dtype=float)
    if not len(values):
        return {"nonzero_variations": 0}
    mean, std = float(values.mean()), float(values.std())
    q1, q3 = map(float, np.percentile(values, [25, 75]))
    upper = q3 + 1.5 * (q3 - q1)
    return {
        "nonzero_variations": len(values), "mean": mean,
        "median": float(np.median(values)), "min": int(values.min()), "max": int(values.max()),
        "q1": q1, "q3": q3, "iqr": q3 - q1, "population_std": std,
        "skewness": float(np.mean(((values - mean) / std) ** 3)) if std else None,
        "outliers_2_std": {k: v for k, v in frequencies.items() if v > 0 and abs(v - mean) > 2 * std},
        "outliers_upper_iqr": {k: v for k, v in frequencies.items() if v > upper},
    }


def plot_distribution(frequencies, output_dir):
    import os
    os.environ.setdefault("MPLCONFIGDIR", str(output_dir / ".mplconfig"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    values = [value for value in frequencies.values() if value > 0]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].hist(values, bins=30)
    axes[0].set(xlabel="Fréquence", ylabel="Nombre de variations", title="Distribution des fréquences")
    axes[1].boxplot(values)
    axes[1].set(ylabel="Fréquence", title="Dispersion des fréquences", xticks=[])
    fig.tight_layout()
    fig.savefig(output_dir / "frequency_distribution.png", dpi=160)
    plt.close(fig)
