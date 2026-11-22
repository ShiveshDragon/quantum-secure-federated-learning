"""Simulated IoT Federated Learning Client with local training and optional attack simulation."""
from dataclasses import dataclass
from typing import Dict, Tuple, Any
import numpy as np
from .model import SimpleLogisticModel


@dataclass
class Client:
    """Represents a decentralized IoT sensor node holding local private data."""
    client_id: str
    x: np.ndarray
    y: np.ndarray

    def train(
        self, 
        global_state: Dict[str, Any], 
        epochs: int = 10, 
        lr: float = 0.05
    ) -> Tuple[Dict[str, np.ndarray], int]:
        """Perform local training on private data without exposing raw records."""
        model = SimpleLogisticModel(self.x.shape[1])
        model.set_parameters(global_state)
        model.fit(self.x, self.y, epochs=epochs, lr=lr)
        return model.get_parameters(), len(self.x)

    def train_poisoned(
        self,
        global_state: Dict[str, Any],
        attack_type: str = "sign_flip",
        factor: float = 3.0,
        epochs: int = 10,
        lr: float = 0.05
    ) -> Tuple[Dict[str, np.ndarray], int]:
        """Simulate an insider adversary sending poisoned model parameters.
        
        Supported attack types:
            - 'sign_flip': Inverts and amplifies the local update delta:
              w_poison = w_global - factor * (w_local - w_global)
            - 'random_noise': Replaces the update with Gaussian perturbation
            - 'constant_offset': Adds a disruptive DC bias offset
        """
        clean_state, count = self.train(global_state, epochs=epochs, lr=lr)
        g_w = np.asarray(global_state["weights"], dtype=float)
        g_b = np.asarray(global_state["bias"], dtype=float)
        c_w = np.asarray(clean_state["weights"], dtype=float)
        c_b = np.asarray(clean_state["bias"], dtype=float)

        delta_w = c_w - g_w
        delta_b = c_b - g_b

        if attack_type == "sign_flip":
            poisoned_w = g_w - factor * delta_w
            poisoned_b = g_b - factor * delta_b
        elif attack_type == "random_noise":
            noise_w = np.random.normal(0, factor, size=delta_w.shape)
            noise_b = np.random.normal(0, factor, size=delta_b.shape)
            poisoned_w = g_w + noise_w
            poisoned_b = g_b + noise_b
        elif attack_type == "constant_offset":
            poisoned_w = c_w + factor
            poisoned_b = c_b + factor
        else:
            raise ValueError(f"Unknown attack_type '{attack_type}'")

        poisoned_state = {
            "weights": poisoned_w,
            "bias": poisoned_b
        }
        return poisoned_state, count
