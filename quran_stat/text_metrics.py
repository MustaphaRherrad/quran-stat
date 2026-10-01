"""Mesures descriptives de distributions finies, sans hypothèse de normalité."""

import math
from collections import Counter

import numpy as np


def distribution(values):
    data = np.asarray(list(values), dtype=float)
    if not data.size:
        raise ValueError("La distribution est vide.")
    mean, median, std = float(data.mean()), float(np.median(data)), float(data.std())
    q1, q3 = map(float, np.percentile(data, [25, 75]))
    mad = float(np.median(np.abs(data - median)))
    return {
        "n": int(data.size), "total": float(data.sum()), "min": float(data.min()),
        "p05": float(np.percentile(data, 5)), "q1": q1, "median": median,
        "mean": mean, "q3": q3, "p95": float(np.percentile(data, 95)),
        "p99": float(np.percentile(data, 99)), "max": float(data.max()),
        "population_variance": std ** 2, "population_std": std,
        "coefficient_variation": std / mean if mean else None,
        "iqr": q3 - q1, "mad": mad,
        "skewness": float(np.mean(((data - mean) / std) ** 3)) if std else None,
        "excess_kurtosis": float(np.mean(((data - mean) / std) ** 4) - 3) if std else None,
        "tukey_low": q1 - 1.5 * (q3 - q1), "tukey_high": q3 + 1.5 * (q3 - q1),
        "extreme_low": q1 - 3 * (q3 - q1), "extreme_high": q3 + 3 * (q3 - q1),
    }


def outlier_flags(value, stats):
    z = 0.6744897501960817 * (value - stats["median"]) / stats["mad"] if stats["mad"] else None
    return {
        "tukey": value < stats["tukey_low"] or value > stats["tukey_high"],
        "extreme": value < stats["extreme_low"] or value > stats["extreme_high"],
        "modified_z": z, "mad_outlier": abs(z) > 3.5 if z is not None else None,
    }


def concentration(frequencies):
    values = np.sort(np.asarray([n for n in frequencies if n > 0], dtype=float))
    if not values.size:
        raise ValueError("Aucune fréquence positive.")
    total, size = float(values.sum()), len(values)
    p = values / total
    entropy = float(-np.sum(p * np.log2(p)))
    maximum = math.log2(size)
    return {
        "types_observed": size, "tokens": int(total), "entropy_bits": entropy,
        "maximum_entropy_bits": maximum, "normalized_entropy": entropy / maximum if maximum else None,
        "effective_types": 2 ** entropy,
        "gini_observed_types": float(2 * np.dot(np.arange(1, size + 1), values) / (size * total) - (size + 1) / size),
        "top_5_share": float(values[-5:].sum() / total),
        "top_10_share": float(values[-10:].sum() / total),
        "top_20_share": float(values[-20:].sum() / total),
        "simpson_with_replacement": float(np.sum(p ** 2)),
    }


def mattr(tokens, window=500):
    """Moyenne exacte de la diversité types/tokens sur toutes les fenêtres."""
    if window <= 0:
        raise ValueError("La fenêtre doit être positive.")
    if len(tokens) < window:
        return None
    counts = Counter(tokens[:window])
    total = len(counts) / window
    for index in range(window, len(tokens)):
        leaving = tokens[index - window]
        counts[leaving] -= 1
        if not counts[leaving]:
            del counts[leaving]
        counts[tokens[index]] += 1
        total += len(counts) / window
    return total / (len(tokens) - window + 1)


def lexical_metrics(tokens):
    frequencies = Counter(tokens)
    n, v = len(tokens), len(frequencies)
    if not n:
        raise ValueError("Aucun mot.")
    hapax = sum(count == 1 for count in frequencies.values())
    return {
        **concentration(frequencies.values()), "ttr": v / n,
        "hapax_types": hapax, "hapax_share_types": hapax / v, "hapax_share_tokens": hapax / n,
        "dis_legomena_types": sum(count == 2 for count in frequencies.values()),
        "mattr_500": mattr(tokens, 500), "mattr_1000": mattr(tokens, 1000),
        "yule_k": 10000 * (sum(count * count for count in frequencies.values()) - n) / (n * n),
    }


def zipf_fit(frequencies):
    """Régression descriptive log10(fréquence) ~ log10(rang), tous types."""
    values = np.array(sorted(frequencies, reverse=True), dtype=float)
    x, y = np.log10(np.arange(1, len(values) + 1)), np.log10(values)
    slope, intercept = np.polyfit(x, y, 1)
    residual = y - (slope * x + intercept)
    variance = np.sum((y - y.mean()) ** 2)
    return {"slope": float(slope), "intercept": float(intercept),
            "r_squared": float(1 - np.sum(residual ** 2) / variance) if variance else None,
            "types": len(values), "fit_scope": "all observed word types; descriptive OLS, not a power-law test"}
