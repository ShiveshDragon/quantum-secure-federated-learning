"""E91 protocol primitives using a singlet-state convention.

Convention used throughout this project:
    |Psi-> = (|01> - |10>) / sqrt(2)
    A(theta) = cos(2 theta) Z + sin(2 theta) X
    E(a,b) = -cos(2(a-b))

Angles are in degrees.  Equal-basis singlet outcomes are anti-correlated;
Bob therefore flips his sifted raw bit before QBER/key comparison.
"""
import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
except ImportError:  # Allows non-Qiskit tests to run in minimal environments.
    QuantumCircuit = None
    AerSimulator = None


@dataclass
class E91Result:
    alice_bits: List[int]
    bob_bits: List[int]
    alice_bases: List[float]
    bob_bases: List[float]
    kept_indices: List[int]
    qber: float
    correlations: Dict[Tuple[float, float], float]
    chsh: Optional[float]


def singlet_statevector() -> np.ndarray:
    state = np.zeros(4, dtype=complex)
    state[1] = 1 / math.sqrt(2)
    state[2] = -1 / math.sqrt(2)
    return state


def theoretical_correlation(alice_angle: float, bob_angle: float) -> float:
    a = math.radians(alice_angle)
    b = math.radians(bob_angle)
    return -math.cos(2 * (a - b))


def build_singlet_measurement_circuit(alice_angle: float, bob_angle: float,
                                      eve_probability: float = 0.0):
    if QuantumCircuit is None:
        raise RuntimeError("Install qiskit and qiskit-aer first.")

    qc = QuantumCircuit(2, 2)

    # |00> -> H(0) -> CX(0,1) -> X(0)Z(0)
    # gives (-|01> + |10>)/sqrt(2), which differs from |Psi-> only
    # by a global phase. Global phase has no effect on measurements.
    qc.h(0)
    qc.cx(0, 1)
    qc.x(0)
    qc.z(0)

    if not 0.0 <= eve_probability <= 1.0:
        raise ValueError("eve_probability must be in [0,1]")

    # The noise model attaches the random X/Z intercept-resend channel to this
    # identity instruction on Bob (qubit 1), before either party measures.
    # At p=1 the channel is 1/2 I + 1/4 X + 1/4 Z as a Pauli mixture.
    if eve_probability > 0.0:
        qc.id(1)

    # Measuring Z after Ry(-2*theta) implements
    # A(theta)=cos(2theta)Z+sin(2theta)X.
    qc.ry(-2 * math.radians(alice_angle), 0)
    qc.ry(-2 * math.radians(bob_angle), 1)
    qc.measure(0, 0)
    qc.measure(1, 1)
    return qc


def simulate_correlation(alice_angle: float, bob_angle: float, shots: int = 4096,
                         seed: int = 1234, noise_model=None,
                         eve_probability: float = 0.0) -> Dict[str, float]:
    if AerSimulator is None:
        raise RuntimeError("Install qiskit-aer first.")
    if shots <= 0:
        raise ValueError("shots must be positive")

    if not 0.0 <= eve_probability <= 1.0:
        raise ValueError("eve_probability must be in [0,1]")

    qc = build_singlet_measurement_circuit(alice_angle, bob_angle, eve_probability)
    if eve_probability > 0.0 and noise_model is None:
        from quantum.noise import build_depolarizing_noise
        noise_model = build_depolarizing_noise(0.0, eve_probability)
    sim = AerSimulator(noise_model=noise_model)
    compiled = transpile(qc, sim, seed_transpiler=seed, optimization_level=0)
    result = sim.run(compiled, shots=shots, seed_simulator=seed).result()
    counts = result.get_counts()

    p00 = counts.get("00", 0) / shots
    p01 = counts.get("01", 0) / shots
    p10 = counts.get("10", 0) / shots
    p11 = counts.get("11", 0) / shots
    return {"p00": p00, "p01": p01, "p10": p10, "p11": p11,
            "correlation": p00 + p11 - p01 - p10}


def calculate_chsh(e11: float, e12: float, e21: float, e22: float) -> float:
    return abs(e11 + e12 + e21 - e22)


def _random_measurement_bit(rng: random.Random) -> int:
    return rng.randint(0, 1)


def generate_sifted_key(rounds: int = 1000, key_angle: float = 0.0,
                        seed: int = 1234, eve_probability: float = 0.0) -> E91Result:
    """Protocol-level key simulation.

    This models ideal singlet statistics on matching key bases and an
    intercept/resend disturbance parameter. It is intentionally separate
    from the Qiskit circuit simulation used for Bell/CHSH validation.
    """
    if rounds <= 0:
        raise ValueError("rounds must be positive")
    if not 0.0 <= eve_probability <= 1.0:
        raise ValueError("eve_probability must be in [0,1]")

    rng = random.Random(seed)
    alice_bits, bob_bits, alice_bases, bob_bases, kept = [], [], [], [], []

    for i in range(rounds):
        a_basis = key_angle if rng.random() < 0.5 else 45.0
        b_basis = key_angle if rng.random() < 0.5 else 45.0
        same = math.isclose(a_basis, b_basis, abs_tol=1e-12)

        a = _random_measurement_bit(rng)
        b = 1 - a if same else _random_measurement_bit(rng)

        if eve_probability and rng.random() < eve_probability:
            # Simplified disturbance model: Eve's resent bit is random on
            # the kept basis. This is an educational attack abstraction.
            b = _random_measurement_bit(rng)

        alice_bits.append(a)
        bob_bits.append(b)
        alice_bases.append(a_basis)
        bob_bases.append(b_basis)
        if same:
            kept.append(i)

    alice_key = [alice_bits[i] for i in kept]
    bob_key = [1 - bob_bits[i] for i in kept]
    mismatches = sum(a != b for a, b in zip(alice_key, bob_key))
    qber = mismatches / len(kept) if kept else 1.0

    return E91Result(alice_key, bob_key,
                     [alice_bases[i] for i in kept],
                     [bob_bases[i] for i in kept], kept, qber, {}, None)


def run_chsh(shots: int = 4096, seed: int = 1234, noise_model=None,
             eve_probability: float = 0.0) -> Dict[str, float]:
    """Estimate CHSH from four independently simulated measurement settings.

    Eve is represented by a random X/Z-basis intercept-resend channel on Bob's
    qubit. The supplied noise_model should include this channel when a separate
    ordinary-noise model is also requested; the API builds the combined model.
    """
    if not 0.0 <= eve_probability <= 1.0:
        raise ValueError("eve_probability must be in [0,1]")
    if eve_probability > 0.0 and noise_model is None:
        from quantum.noise import build_depolarizing_noise
        noise_model = build_depolarizing_noise(0.0, eve_probability)

    # These settings produce |S|=2sqrt(2) under the chosen convention.
    a1, a2, b1, b2 = 0.0, 45.0, 22.5, -22.5
    pairs = [(a1, b1), (a1, b2), (a2, b1), (a2, b2)]
    values = [simulate_correlation(a, b, shots, seed + i, noise_model,
                                   eve_probability=eve_probability)["correlation"]
              for i, (a, b) in enumerate(pairs)]
    e11, e12, e21, e22 = values
    return {"E(a1,b1)": e11, "E(a1,b2)": e12, "E(a2,b1)": e21,
            "E(a2,b2)": e22, "CHSH": calculate_chsh(e11, e12, e21, e22),
            "ideal_CHSH": 2 * math.sqrt(2)}
