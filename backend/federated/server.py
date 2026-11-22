"""Federated Learning Server with FedAvg and Robust Aggregation support."""
from typing import List, Dict, Any, Optional
import numpy as np
from .fedavg import fedavg_state_dict
from .model import SimpleLogisticModel, classification_metrics
from .robust_aggregation import (
    validate_parameter_state,
    compute_deltas,
    coordinate_median,
    coordinate_trimmed_mean,
    apply_delta_to_global
)
from crypto.replay_detector import ReplayDetector


class FLServer:
    """Central server orchestrating federated learning, aggregation, and model evaluation."""

    def __init__(self, n_features: int):
        self.model = SimpleLogisticModel(n_features)
        self.round = 0
        self.replay_detector = ReplayDetector()
        self.aggregation_history: List[Dict[str, Any]] = []

    def get_global_state(self) -> Dict[str, np.ndarray]:
        """Return the current global model weights and bias."""
        return self.model.get_parameters()

    def set_global_state(self, state: Dict[str, Any]) -> None:
        """Set the global model parameters."""
        validate_parameter_state(state, "new_global_state")
        self.model.set_parameters(state)

    def validate_client_update(
        self,
        state: Dict[str, Any],
        client_id: Optional[str] = None,
        round_number: Optional[int] = None,
        message_id: Optional[str] = None,
        timestamp: Optional[float] = None
    ) -> None:
        """Validate structure, numerical finiteness, and freshness (replay protection) of a client update."""
        validate_parameter_state(state, f"Client {client_id or 'unknown'} update")
        
        # Check parameter shapes match current model
        current = self.get_global_state()
        w = np.asarray(state["weights"])
        b = np.asarray(state["bias"])
        if w.shape != current["weights"].shape:
            raise ValueError(
                f"Client weights shape mismatch: expected {current['weights'].shape}, got {w.shape}"
            )
        if b.shape != current["bias"].shape:
            raise ValueError(
                f"Client bias shape mismatch: expected {current['bias'].shape}, got {b.shape}"
            )

        # Check replay protection if metadata is provided
        if client_id is not None and round_number is not None:
            valid, reason = self.replay_detector.check_and_record(
                client_id=client_id,
                round_number=round_number,
                message_id=message_id,
                timestamp=timestamp,
                current_server_round=self.round + 1
            )
            if not valid:
                raise ValueError(f"Replay rejected: {reason}")

    def aggregate(
        self,
        states: List[Dict[str, Any]],
        counts: Optional[List[int]] = None,
        method: str = "fedavg",
        trim_ratio: float = 0.2
    ) -> Dict[str, np.ndarray]:
        """Aggregate participating client parameter states using the selected method.
        
        Supported methods:
            - 'fedavg': Standard sample-weighted parameter averaging (default).
            - 'coordinate_median': Coordinate-wise median applied to client deltas (Delta_k = w_k - w_global).
            - 'trimmed_mean': Coordinate-wise trimmed mean applied to client deltas.
              Note: Robust methods do not use sample counts as FedAvg weights to avoid malicious weight inflation.
        """
        if not states:
            raise ValueError("No client states provided for aggregation")
        
        # Validate all client updates
        for i, s in enumerate(states):
            self.validate_client_update(s, client_id=f"client_{i+1}")

        global_state = self.get_global_state()

        if method == "fedavg":
            if counts is None or len(counts) != len(states):
                raise ValueError("sample counts are required for FedAvg aggregation")
            new_state = fedavg_state_dict(states, counts)
        elif method == "coordinate_median":
            # Compute deltas relative to global state: delta_k = w_k - w_global
            deltas = compute_deltas(states, global_state)
            agg_delta = coordinate_median(deltas)
            new_state = apply_delta_to_global(global_state, agg_delta)
        elif method in ("trimmed_mean", "coordinate_trimmed_mean"):
            deltas = compute_deltas(states, global_state)
            agg_delta = coordinate_trimmed_mean(deltas, trim_ratio=trim_ratio)
            new_state = apply_delta_to_global(global_state, agg_delta)
        else:
            raise ValueError(
                f"Unknown aggregation method '{method}'. Supported: 'fedavg', 'coordinate_median', 'trimmed_mean'"
            )

        self.model.set_parameters(new_state)
        self.round += 1
        
        self.aggregation_history.append({
            "round": self.round,
            "method": method,
            "n_clients": len(states),
            "trim_ratio": trim_ratio if "trimmed" in method else None
        })
        return self.get_global_state()

    def evaluate(self, x: np.ndarray, y: np.ndarray) -> float:
        """Compute test set accuracy."""
        return float(np.mean(self.model.predict(x) == y))

    def evaluate_metrics(self, x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Compute full classification metrics (accuracy, precision, recall, F1, TP, TN, FP, FN)."""
        return classification_metrics(y, self.model.predict(x))
