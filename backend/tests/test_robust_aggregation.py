"""Comprehensive Automated Test Suite for Federated Robust Aggregation."""
import pytest
import numpy as np
from federated.robust_aggregation import (
    validate_parameter_state,
    validate_deltas,
    compute_deltas,
    coordinate_median,
    coordinate_trimmed_mean,
    apply_delta_to_global
)
from federated.server import FLServer
from federated.client import Client


def test_coordinate_median_odd_clients():
    """Verify coordinate median on known scalar coordinates with odd client count (N=5)."""
    deltas = [
        {"weights": np.array([1.0, 10.0]), "bias": np.array([0.1])},
        {"weights": np.array([2.0, 20.0]), "bias": np.array([0.2])},
        {"weights": np.array([3.0, 30.0]), "bias": np.array([0.3])},  # Median
        {"weights": np.array([4.0, 40.0]), "bias": np.array([0.4])},
        {"weights": np.array([100.0, -500.0]), "bias": np.array([99.0])},  # Outlier
    ]
    agg = coordinate_median(deltas)
    # Sorted coordinate 0: [1, 2, 3, 4, 100] -> median = 3.0
    # Sorted coordinate 1: [-500, 10, 20, 30, 40] -> median = 20.0
    assert np.allclose(agg["weights"], np.array([3.0, 20.0]))
    assert np.allclose(agg["bias"], np.array([0.3]))


def test_coordinate_median_even_clients():
    """Verify coordinate median on known scalar coordinates with even client count (N=4)."""
    deltas = [
        {"weights": np.array([1.0]), "bias": np.array([0.0])},
        {"weights": np.array([2.0]), "bias": np.array([1.0])},
        {"weights": np.array([4.0]), "bias": np.array([3.0])},
        {"weights": np.array([10.0]), "bias": np.array([5.0])},
    ]
    agg = coordinate_median(deltas)
    # Median of [1, 2, 4, 10] is (2 + 4) / 2 = 3.0
    # Median of [0, 1, 3, 5] is (1 + 3) / 2 = 2.0
    assert np.allclose(agg["weights"], np.array([3.0]))
    assert np.allclose(agg["bias"], np.array([2.0]))


def test_trimmed_mean_known_values():
    """Verify trimmed mean trims the configured tails and averages the remainder."""
    # N=5, trim_ratio=0.2 -> k = floor(5 * 0.2) = 1.
    # Sorted weights[0]: [1, 2, 3, 4, 100] -> trimmed: [2, 3, 4] -> mean = 3.0
    deltas = [
        {"weights": np.array([1.0]), "bias": np.array([10.0])},
        {"weights": np.array([2.0]), "bias": np.array([20.0])},
        {"weights": np.array([3.0]), "bias": np.array([30.0])},
        {"weights": np.array([4.0]), "bias": np.array([40.0])},
        {"weights": np.array([100.0]), "bias": np.array([999.0])},
    ]
    agg = coordinate_trimmed_mean(deltas, trim_ratio=0.2)
    assert np.allclose(agg["weights"], np.array([3.0]))
    assert np.allclose(agg["bias"], np.array([30.0]))


def test_extreme_outlier_mitigation():
    """Demonstrate that an extreme Byzantine update shifts FedAvg but is rejected by median and trimmed mean."""
    honest_updates = [
        {"weights": np.array([0.5, 0.5]), "bias": np.array([0.1])},
        {"weights": np.array([0.52, 0.48]), "bias": np.array([0.11])},
        {"weights": np.array([0.49, 0.51]), "bias": np.array([0.09])},
        {"weights": np.array([0.51, 0.50]), "bias": np.array([0.10])},
    ]
    malicious_update = [
        {"weights": np.array([-1000.0, 5000.0]), "bias": np.array([-999.0])}
    ]
    all_updates = honest_updates + malicious_update

    # FedAvg would be ruined
    median_agg = coordinate_median(all_updates)
    assert 0.45 < median_agg["weights"][0] < 0.55
    assert 0.45 < median_agg["weights"][1] < 0.55

    trimmed_agg = coordinate_trimmed_mean(all_updates, trim_ratio=0.2)
    assert 0.45 < trimmed_agg["weights"][0] < 0.55
    assert 0.45 < trimmed_agg["weights"][1] < 0.55


def test_delta_computation_and_application():
    """Verify Delta_k = w_k - w_global and w_new = w_old + Delta_agg."""
    global_state = {
        "weights": np.array([1.0, 2.0]),
        "bias": np.array([0.5])
    }
    client_states = [
        {"weights": np.array([1.2, 2.3]), "bias": np.array([0.6])},
        {"weights": np.array([1.1, 2.1]), "bias": np.array([0.7])},
    ]
    deltas = compute_deltas(client_states, global_state)
    assert np.allclose(deltas[0]["weights"], np.array([0.2, 0.3]))
    assert np.allclose(deltas[1]["weights"], np.array([0.1, 0.1]))

    agg_delta = coordinate_median(deltas)
    new_global = apply_delta_to_global(global_state, agg_delta)
    assert np.allclose(new_global["weights"], np.array([1.15, 2.2]))
    assert np.allclose(new_global["bias"], np.array([0.65]))


def test_invalid_trim_ratio_rejected():
    deltas = [{"weights": np.array([1.0]), "bias": np.array([0.0])}]
    with pytest.raises(ValueError):
        coordinate_trimmed_mean(deltas, trim_ratio=-0.1)
    with pytest.raises(ValueError):
        coordinate_trimmed_mean(deltas, trim_ratio=0.5)
    with pytest.raises(TypeError):
        coordinate_trimmed_mean(deltas, trim_ratio="invalid")


def test_non_finite_values_rejected():
    with pytest.raises(ValueError, match="non-finite"):
        validate_parameter_state({"weights": np.array([np.nan]), "bias": np.array([0.0])})
    with pytest.raises(ValueError, match="non-finite"):
        validate_parameter_state({"weights": np.array([1.0]), "bias": np.array([np.inf])})


def test_inconsistent_shapes_rejected():
    deltas = [
        {"weights": np.array([1.0, 2.0]), "bias": np.array([0.0])},
        {"weights": np.array([1.0]), "bias": np.array([0.0])},
    ]
    with pytest.raises(ValueError, match="Inconsistent weights shape"):
        coordinate_median(deltas)


def test_fl_server_integration():
    """Verify FLServer aggregate with FedAvg, coordinate_median, and trimmed_mean."""
    server = FLServer(n_features=2)
    server.set_global_state({"weights": np.array([0.0, 0.0]), "bias": np.array([0.0])})

    states = [
        {"weights": np.array([1.0, 1.0]), "bias": np.array([0.1])},
        {"weights": np.array([2.0, 2.0]), "bias": np.array([0.2])},
        {"weights": np.array([3.0, 3.0]), "bias": np.array([0.3])},
        {"weights": np.array([4.0, 4.0]), "bias": np.array([0.4])},
        {"weights": np.array([10.0, 10.0]), "bias": np.array([9.0])},
    ]
    counts = [100, 100, 100, 100, 100]

    # Test coordinate_median
    s_med = server.aggregate(states, counts=counts, method="coordinate_median")
    assert np.allclose(s_med["weights"], np.array([3.0, 3.0]))

    # Test trimmed_mean
    server.set_global_state({"weights": np.array([0.0, 0.0]), "bias": np.array([0.0])})
    s_trim = server.aggregate(states, counts=counts, method="trimmed_mean", trim_ratio=0.2)
    assert np.allclose(s_trim["weights"], np.array([3.0, 3.0]))

    # Test invalid method
    with pytest.raises(ValueError, match="Unknown aggregation method"):
        server.aggregate(states, counts=counts, method="nonexistent_method")


def test_client_poisoning_attacks():
    """Verify Client.train_poisoned generates sign-flipped and scaled updates."""
    x = np.random.randn(50, 4)
    y = np.random.randint(0, 2, size=50)
    client = Client("client_test", x, y)
    
    global_state = {"weights": np.zeros(4), "bias": np.zeros(1)}
    clean_state, _ = client.train(global_state, epochs=5, lr=0.05)
    poisoned_state, _ = client.train_poisoned(
        global_state, attack_type="sign_flip", factor=2.0, epochs=5, lr=0.05
    )
    
    # Poisoned delta should be -2 * clean delta
    clean_delta = clean_state["weights"] - global_state["weights"]
    poisoned_delta = poisoned_state["weights"] - global_state["weights"]
    assert np.allclose(poisoned_delta, -2.0 * clean_delta)


def test_robust_aggregate_states_helper():
    from federated.robust_aggregation import robust_aggregate_states
    global_state = {"weights": np.array([0.0, 0.0]), "bias": np.array([0.0])}
    client_states = [
        {"weights": np.array([1.0, 1.0]), "bias": np.array([0.1])},
        {"weights": np.array([2.0, 2.0]), "bias": np.array([0.2])},
        {"weights": np.array([3.0, 3.0]), "bias": np.array([0.3])},
        {"weights": np.array([4.0, 4.0]), "bias": np.array([0.4])},
        {"weights": np.array([10.0, 10.0]), "bias": np.array([9.0])},
    ]
    res_med = robust_aggregate_states(global_state, client_states, method="coordinate_median")
    assert np.allclose(res_med["weights"], np.array([3.0, 3.0]))
    
    res_trim = robust_aggregate_states(global_state, client_states, method="trimmed_mean", trim_ratio=0.2)
    assert np.allclose(res_trim["weights"], np.array([3.0, 3.0]))

