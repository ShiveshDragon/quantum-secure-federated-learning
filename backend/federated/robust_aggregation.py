"""Robust aggregation algorithms for Federated Learning.

Provides coordinate-wise median and coordinate-wise trimmed mean operating
on client parameter deltas relative to the global model, defending against
malicious client model-poisoning and Byzantine update attacks.
"""
from typing import List, Dict, Any, Union
import numpy as np


def validate_parameter_state(state: Dict[str, Any], name: str = "state") -> None:
    """Validate that a model parameter dictionary is structured properly with finite values."""
    if not isinstance(state, dict):
        raise TypeError(f"{name} must be a dictionary, got {type(state).__name__}")
    if "weights" not in state or "bias" not in state:
        raise ValueError(f"{name} must contain 'weights' and 'bias' keys")
    
    weights = np.asarray(state["weights"], dtype=float)
    bias = np.asarray(state["bias"], dtype=float)
    
    if not np.all(np.isfinite(weights)):
        raise ValueError(f"{name} contains non-finite values (NaN or Inf) in 'weights'")
    if not np.all(np.isfinite(bias)):
        raise ValueError(f"{name} contains non-finite values (NaN or Inf) in 'bias'")


def validate_deltas(deltas: List[Dict[str, np.ndarray]]) -> None:
    """Validate a list of client parameter deltas for consistency, finite values, and matching shapes."""
    if not deltas:
        raise ValueError("deltas list cannot be empty")
    
    first_w_shape = None
    first_b_shape = None
    
    for i, delta in enumerate(deltas):
        validate_parameter_state(delta, f"delta[{i}]")
        w = np.asarray(delta["weights"])
        b = np.asarray(delta["bias"])
        
        if first_w_shape is None:
            first_w_shape = w.shape
            first_b_shape = b.shape
        else:
            if w.shape != first_w_shape:
                raise ValueError(
                    f"Inconsistent weights shape at index {i}: expected {first_w_shape}, got {w.shape}"
                )
            if b.shape != first_b_shape:
                raise ValueError(
                    f"Inconsistent bias shape at index {i}: expected {first_b_shape}, got {b.shape}"
                )


def compute_deltas(
    client_states: List[Dict[str, Any]], 
    global_state: Dict[str, Any]
) -> List[Dict[str, np.ndarray]]:
    """Compute client parameter updates relative to the global model: delta_k = w_k - w_global."""
    validate_parameter_state(global_state, "global_state")
    g_w = np.asarray(global_state["weights"], dtype=float)
    g_b = np.asarray(global_state["bias"], dtype=float)
    
    deltas = []
    for i, state in enumerate(client_states):
        validate_parameter_state(state, f"client_state[{i}]")
        w = np.asarray(state["weights"], dtype=float)
        b = np.asarray(state["bias"], dtype=float)
        if w.shape != g_w.shape or b.shape != g_b.shape:
            raise ValueError(
                f"Client {i} shape mismatch: w={w.shape} vs global={g_w.shape}, b={b.shape} vs global={g_b.shape}"
            )
        deltas.append({
            "weights": w - g_w,
            "bias": b - g_b
        })
    return deltas


def coordinate_median(deltas: List[Dict[str, Any]]) -> Dict[str, np.ndarray]:
    """Calculate the coordinate-wise median across client parameter deltas.
    
    For each parameter coordinate:
      aggregated_delta[j] = median({delta_k[j] for k in 1..N})
    Supports both odd and even client counts.
    """
    validate_deltas(deltas)
    
    w_stack = np.stack([np.asarray(d["weights"], dtype=float) for d in deltas], axis=0)
    b_stack = np.stack([np.asarray(d["bias"], dtype=float) for d in deltas], axis=0)
    
    median_w = np.median(w_stack, axis=0)
    median_b = np.median(b_stack, axis=0)
    
    return {
        "weights": median_w,
        "bias": median_b
    }


def coordinate_trimmed_mean(
    deltas: List[Dict[str, Any]], 
    trim_ratio: float = 0.2
) -> Dict[str, np.ndarray]:
    """Calculate the coordinate-wise trimmed mean across client parameter deltas.
    
    For each parameter coordinate:
      1. Sort client values: v_(1) <= v_(2) <= ... <= v_(N)
      2. Trim k = floor(N * trim_ratio) from both tails
      3. Compute the arithmetic mean of remaining elements:
         mean(v_(k+1) ... v_(N-k))
    
    Args:
        deltas: List of client delta dictionaries
        trim_ratio: Fraction of elements to trim from each tail (0.0 <= trim_ratio < 0.5)
    """
    if not isinstance(trim_ratio, (int, float)):
        raise TypeError(f"trim_ratio must be a float, got {type(trim_ratio).__name__}")
    if trim_ratio < 0.0 or trim_ratio >= 0.5:
        raise ValueError(f"trim_ratio must be in [0.0, 0.5), got {trim_ratio}")
    
    validate_deltas(deltas)
    n_clients = len(deltas)
    k_trim = int(np.floor(n_clients * trim_ratio))
    
    if 2 * k_trim >= n_clients:
        raise ValueError(
            f"trim_ratio {trim_ratio} trims {2 * k_trim} of {n_clients} samples, leaving no elements"
        )
    
    w_stack = np.stack([np.asarray(d["weights"], dtype=float) for d in deltas], axis=0)
    b_stack = np.stack([np.asarray(d["bias"], dtype=float) for d in deltas], axis=0)
    
    # Sort along client axis (axis=0)
    w_sorted = np.sort(w_stack, axis=0)
    b_sorted = np.sort(b_stack, axis=0)
    
    # Slice the middle elements
    if k_trim > 0:
        w_trimmed = w_sorted[k_trim : n_clients - k_trim]
        b_trimmed = b_sorted[k_trim : n_clients - k_trim]
    else:
        w_trimmed = w_sorted
        b_trimmed = b_sorted
        
    return {
        "weights": np.mean(w_trimmed, axis=0),
        "bias": np.mean(b_trimmed, axis=0)
    }


def apply_delta_to_global(
    global_state: Dict[str, Any], 
    aggregated_delta: Dict[str, np.ndarray]
) -> Dict[str, np.ndarray]:
    """Apply the aggregated delta to update the global model state: w_new = w_old + delta_agg."""
    validate_parameter_state(global_state, "global_state")
    validate_parameter_state(aggregated_delta, "aggregated_delta")
    
    g_w = np.asarray(global_state["weights"], dtype=float)
    g_b = np.asarray(global_state["bias"], dtype=float)
    d_w = np.asarray(aggregated_delta["weights"], dtype=float)
    d_b = np.asarray(aggregated_delta["bias"], dtype=float)
    
    if g_w.shape != d_w.shape or g_b.shape != d_b.shape:
        raise ValueError("Shape mismatch between global state and aggregated delta")
        
    return {
        "weights": g_w + d_w,
        "bias": g_b + d_b
    }


def robust_aggregate_states(
    global_state: Dict[str, Any], 
    client_states: List[Dict[str, Any]], 
    method: str = "coordinate_median", 
    trim_ratio: float = 0.2
) -> Dict[str, np.ndarray]:
    """Calculates each local update as local_state - global_state, robustly aggregates 
    the updates, then adds the aggregate update to the global parameters.
    """
    deltas = compute_deltas(client_states, global_state)
    if method == "coordinate_median":
        agg_delta = coordinate_median(deltas)
    elif method in ("trimmed_mean", "coordinate_trimmed_mean"):
        agg_delta = coordinate_trimmed_mean(deltas, trim_ratio=trim_ratio)
    else:
        raise ValueError(f"Unknown robust method '{method}'. Use 'coordinate_median' or 'trimmed_mean'.")
    return apply_delta_to_global(global_state, agg_delta)

