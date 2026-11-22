# Pending Work

## Already implemented

- [x] Corrected singlet-state preparation
- [x] E91 measurement convention
- [x] Theoretical correlation
- [x] CHSH calculation
- [x] QKD basis selection/sifting
- [x] QBER
- [x] Simplified Eve disturbance model
- [x] Depolarizing-noise model
- [x] SHA-256 prototype session-key derivation
- [x] AES-256/AES-GCM
- [x] HMAC-SHA256
- [x] Associated-data binding
- [x] 4/5-client FL
- [x] FedAvg
- [x] Multiple FL rounds
- [x] IID + simple non-IID partitioning
- [x] MQTT payload/topic/transport adapters
- [x] Centralized baseline
- [x] FL baseline
- [x] Secure FL
- [x] Eavesdropping experiment
- [x] Noise experiment
- [x] Security comparison
- [x] Performance experiment
- [x] Automated unit/integration tests
- [x] Detailed implementation/validation documentation

## Must do before final submission

1. Install all dependencies on the actual target machine.
2. Run `python -m pytest -q`.
3. Confirm all Qiskit circuit tests pass, especially CHSH.
4. Run every experiment in `experiments/`.
5. Preserve the generated CSV/JSON results.
6. Generate plots from the measured results.
7. Repeat key experiments over multiple random seeds.
8. Put actual values into the final report.

## Strongly recommended

- Add a public IoT-specific dataset.
- Add a more rigorous non-IID client split.
- Add replay protection.
- Add a model-poisoning attack/defense experiment.
- Run MQTT through a real local broker.
- Demonstrate MQTT TLS/authentication.
- Add a simple results dashboard.

## Research-grade future work

- authenticated classical channel for QKD
- information reconciliation
- finite-key security analysis
- rigorous privacy amplification
- device-independent/security-assumption discussion
- realistic quantum channel/noise model
- client dropout and unreliable-network experiments
- robust aggregation against malicious FL clients
- formal threat model

## Important limitations

The current repository is a simulation/prototype. It must not be presented as a production QKD implementation or as proof that an eavesdropper cannot exist. SHA-256 key derivation is a prototype placeholder for the much more involved reconciliation/privacy-amplification stage of real QKD.
