import numpy as np


def fedavg(weights, sample_counts):
    if not weights or len(weights) != len(sample_counts):
        raise ValueError("weights and sample_counts must be non-empty and equal length")
    total = sum(sample_counts)
    if total <= 0 or any(c <= 0 for c in sample_counts):
        raise ValueError("sample counts must be positive")
    result = np.zeros_like(np.asarray(weights[0], dtype=float))
    for w, n in zip(weights, sample_counts):
        result += np.asarray(w, dtype=float) * (n / total)
    return result


def fedavg_state_dict(states, sample_counts):
    if not states or len(states) != len(sample_counts):
        raise ValueError("states and sample_counts must be non-empty and equal length")
    return {"weights": fedavg([s["weights"] for s in states], sample_counts),
            "bias": fedavg([s["bias"] for s in states], sample_counts)}
