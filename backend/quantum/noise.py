"""Quantum noise models used by the CHSH circuit simulation."""

def build_depolarizing_noise(probability: float, eve_probability: float = 0.0):
    """Build a Qiskit Aer noise model.

    ``probability`` applies ordinary depolarizing gate noise.
    ``eve_probability`` applies an effective random X/Z-basis intercept-resend
    channel to Bob through an ``id`` instruction inserted before measurement.

    Averaging an X/Z intercept-resend attack gives the Pauli channel
        P(I) = 1 - p/2, P(X) = p/4, P(Z) = p/4.
    The two controls are independent and can be enabled together.
    """
    from qiskit_aer.noise import NoiseModel, depolarizing_error, pauli_error

    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be between 0 and 1")
    if not 0.0 <= eve_probability <= 1.0:
        raise ValueError("eve_probability must be between 0 and 1")

    noise = NoiseModel()
    if probability > 0.0:
        one = depolarizing_error(probability, 1)
        two = depolarizing_error(probability, 2)
        noise.add_all_qubit_quantum_error(one, ["x", "h", "ry"])
        noise.add_all_qubit_quantum_error(two, ["cx"])

    if eve_probability > 0.0:
        attack = pauli_error([
            ("I", 1.0 - eve_probability / 2.0),
            ("X", eve_probability / 4.0),
            ("Z", eve_probability / 4.0),
        ])
        noise.add_all_qubit_quantum_error(attack, ["id"])

    return noise
