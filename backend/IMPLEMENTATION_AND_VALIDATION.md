# Complete Implementation, Validation and Future-Work Plan

## A. Objective

Build a technically reproducible prototype for:

> Integrating quantum computing with federated learning for enhanced security and privacy in IoT networks.

The implementation is deliberately divided into layers so that a failure in one layer does not silently invalidate another.

---

# 1. Architecture

```text
                    QUANTUM LAYER
              ┌─────────────────────┐
              │ Bell/singlet state  │
              │ E91 measurements    │
              │ Sifting + QBER      │
              │ CHSH verification   │
              └──────────┬──────────┘
                         │ raw/sifted key
                         ▼
                  CRYPTOGRAPHIC LAYER
              ┌─────────────────────┐
              │ SHA-256 KDF demo    │
              │ AES-256/AES-GCM     │
              │ HMAC-SHA256        │
              └──────────┬──────────┘
                         │ secure update
                         ▼
                     IoT / FL LAYER
      ┌──────────┬──────────┬──────────┬──────────┐
      │ Client 1 │ Client 2 │ Client 3 │ Client 4 │ ... Client 5
      │ local ML │ local ML │ local ML │ local ML │
      └──────────┴──────────┴──────────┴──────────┘
                         │
                         ▼
                    MQTT ADAPTER
                         │
                         ▼
                    FL SERVER
                         │
                      FedAvg
                         │
                         ▼
                    Global model
```

---

# 2. Quantum implementation

## 2.1 State preparation

The repository uses the singlet state:

`|Psi-> = (|01> - |10>) / sqrt(2)`

The circuit starts at `|00>` and applies:

1. `H` on qubit 0
2. `CX(0,1)`
3. `X` on qubit 0
4. `Z` on qubit 0

The resulting state is `(-|01> + |10>)/sqrt(2)`, which differs from the required singlet only by a global phase of `-1`.

Global phase does not change measurement probabilities or correlations.

**Validation:** `tests/test_quantum.py::test_singlet_statevector_definition` validates the mathematical vector directly. Qiskit circuit tests then validate measurement behavior.

## 2.2 Measurement convention

Use:

`A(theta) = cos(2theta) Z + sin(2theta) X`

and the same form for Bob.

To implement this with computational-basis measurement, apply:

`Ry(-2theta)`

before measurement.

**Validation:** measured correlations are compared with:

`E(a,b) = -cos(2(a-b))`

within a statistical tolerance.

## 2.3 CHSH settings

Use:

- Alice `a1=0°`
- Alice `a2=45°`
- Bob `b1=22.5°`
- Bob `b2=-22.5°`

Then the theoretical correlations give:

- `E11 = -sqrt(2)/2`
- `E12 = -sqrt(2)/2`
- `E21 = -sqrt(2)/2`
- `E22 = +sqrt(2)/2`

and therefore:

`S = 2sqrt(2) ≈ 2.828`

**Acceptance criterion:** simulated CHSH should normally be comfortably above 2 with enough shots; the automated test uses `S > 2.5`.

## 2.4 Key basis

The prototype uses 0° and 45° as the two key-basis choices. When Alice and Bob select the same basis, the singlet produces opposite raw outcomes.

Bob flips his kept raw bit:

`Bob_key_bit = 1 - Bob_raw_bit`

Then QBER is:

`QBER = mismatches / sifted_key_length`

Ideal simulation target:

`QBER = 0`

## 2.5 Eavesdropping

The current attack experiment uses a controlled disturbance parameter rather than pretending to implement a complete physical Eve circuit. At probability 1, the kept Bob bit is randomized, causing QBER to approach 0.5.

This is useful for demonstrating the security signal, but the report should call it a **simplified intercept/resend disturbance model**.

---

# 3. Noise experiment

`quantum/noise.py` constructs a Qiskit Aer depolarizing noise model.

Noise levels tested:

```text
0.000
0.001
0.005
0.010
0.020
0.050
```

For each level measure:

- CHSH value
- equal-basis correlation
- equal-basis QBER estimate

Expected trend:

```text
more noise → weaker correlation → lower CHSH → higher error
```

The exact numerical threshold should be obtained experimentally, not invented beforehand.

---

# 4. Cryptographic implementation

## 4.1 Session key

The sifted key is converted into bytes and compressed through SHA-256 to produce a 32-byte session key for the prototype.

This is a **prototype key-derivation/privacy-amplification placeholder**, not a complete finite-key QKD privacy-amplification protocol.

## 4.2 AES-256

AES-GCM is used with:

- 256-bit key
- 12-byte random nonce
- associated data containing client/round context

The associated data binds a ciphertext to its expected client and round.

Validation:

- normal decrypt returns original payload
- wrong key fails
- wrong associated data fails

## 4.3 HMAC-SHA256

HMAC-SHA256 authenticates the serialized message envelope.

Validation:

- original message passes
- changed round/client/ciphertext envelope fails

Important design note: AES-GCM already authenticates ciphertext. HMAC is retained for the assignment's explicit requirement and for demonstrating an independent MAC layer.

---

# 5. Federated learning implementation

## 5.1 Dataset

The current prototype uses a reproducible synthetic binary-classification dataset generated with Scikit-learn.

Why:

- no proprietary data
- no external download dependency
- deterministic experiments
- easy 4/5-client simulation
- easy IID/non-IID experimentation

This should be replaced by a real IoT/edge dataset if the final project scope requires domain-specific evidence.

## 5.2 Client model

Each client trains a simple logistic regression model locally.

No raw training samples are sent to the server.

Only:

- model weights
- bias
- sample count

are sent.

## 5.3 FedAvg

For client updates `w_i` and sample counts `n_i`:

`w_global = sum(n_i * w_i) / sum(n_i)`

The same weighted operation is performed for the bias.

## 5.4 Multiple rounds

The prototype runs five FL rounds by default.

Each round:

1. server sends current global state
2. clients train locally
3. clients prepare model updates
4. secure version encrypts/authenticates updates
5. server verifies/decrypts
6. server performs FedAvg
7. global model is evaluated

---

# 6. Security-aware FL flow

For every client update:

```text
local model training
       ↓
JSON update
       ↓
AES-GCM encrypt
       ↓
HMAC-SHA256 message authentication
       ↓
MQTT transport adapter
       ↓
server HMAC verification
       ↓
AES-GCM decryption
       ↓
FedAvg
```

The actual current experiments can run without a live broker so that algorithmic testing is deterministic.

---

# 7. MQTT implementation

Topics:

```text
iot/qkd/<client_id>/key_status
iot/fl/<client_id>/update
iot/fl/global_model
```

QoS 1 is used by the adapter to request at-least-once delivery.

The core project does not require a broker for unit tests.

### Live broker validation to perform later

1. Start Mosquitto on localhost.
2. Start server subscriber.
3. Start one or more client publishers.
4. Confirm each client update reaches the server.
5. Confirm duplicate delivery does not cause unsafe double aggregation.
6. Add message IDs/idempotency before treating the MQTT path as production-like.

---

# 8. Required experiments

## Experiment 1 — Quantum correctness

Measure:

- singlet definition
- equal-basis correlation
- four CHSH correlations
- CHSH value

Expected:

- equal basis approximately -1
- CHSH approximately 2.828

## Experiment 2 — Eavesdropping

Run Eve probabilities:

`0, 0.25, 0.5, 0.75, 1.0`

Record:

- sifted bits
- QBER

Expected:

QBER increases with disturbance; full randomization approaches 50%.

## Experiment 3 — Quantum noise

Record:

- depolarizing probability
- CHSH
- equal-basis QBER estimate

Expected:

noise degrades correlations.

## Experiment 4 — Centralized baseline

Train one model using all training data.

Record:

- accuracy
- precision
- recall
- F1

## Experiment 5 — FL baseline

Use 5 clients and 5 rounds without cryptographic overhead.

Record metrics after each round.

## Experiment 6 — Secure FL

Use E91-derived prototype session key plus AES/HMAC.

Record:

- QBER
- key length
- accuracy
- precision
- recall
- F1
- encryption time
- verification/decryption time
- payload bytes

## Experiment 7 — FL vs FL+security

Compare final and per-round metrics.

The security layer should not be claimed to improve predictive accuracy by itself. The main expected difference is computational/communication overhead.

## Experiment 8 — Performance

Vary E91 rounds/key material and record:

- sifted bits
- QBER
- key-generation time
- AES encryption time
- AES decryption time

---

# 9. Validation checklist

## Quantum

- [x] mathematical singlet vector
- [x] corrected circuit preparation
- [x] fixed measurement convention
- [x] theoretical correlation formula
- [x] CHSH formula
- [x] theoretical Tsirelson-bound test
- [x] Qiskit correlation test
- [x] Qiskit CHSH test
- [ ] run Qiskit tests on the final target machine and save output

## QKD

- [x] basis selection
- [x] sifting
- [x] anti-correlation correction
- [x] QBER
- [x] Eve disturbance experiment
- [ ] complete authenticated classical channel
- [ ] error reconciliation
- [ ] finite-key analysis
- [ ] rigorous privacy amplification

## FL

- [x] 4/5 clients
- [x] local training
- [x] FedAvg
- [x] multiple rounds
- [x] IID split
- [x] simple non-IID split
- [x] evaluation metrics
- [ ] stronger IoT-specific dataset
- [ ] client dropout experiment
- [ ] model poisoning defense

## Security

- [x] AES-256
- [x] HMAC-SHA256
- [x] key derivation placeholder
- [x] associated-data binding
- [x] tampering tests
- [ ] formal threat model
- [ ] replay protection / sequence validation
- [ ] key rotation policy
- [ ] production-grade QKD reconciliation/privacy amplification

## MQTT

- [x] payload format
- [x] topic structure
- [x] client adapter
- [x] server adapter
- [ ] live broker integration test
- [ ] TLS configuration
- [ ] authentication/ACL configuration
- [ ] duplicate-message handling

## Evaluation

- [x] centralized baseline script
- [x] FL baseline script
- [x] secure FL script
- [x] security comparison
- [x] eavesdropping experiment
- [x] noise experiment
- [x] performance experiment
- [x] model comparison
- [ ] generate publication-quality plots
- [ ] add final numerical results to report
- [ ] repeat experiments with multiple random seeds and confidence intervals

---

# 10. Recommended final additions for extra marks

These are not required to make the technical prototype run, but they substantially strengthen a final project.

### A. Real IoT dataset

Replace or supplement the synthetic classification data with a suitable public IoT/cyber/edge dataset. Document:

- source
- features
- target
- preprocessing
- privacy rationale
- client partitioning strategy

### B. Non-IID comparison

Compare IID and label-skewed clients. Plot convergence per FL round.

### C. Attack beyond eavesdropping

Add one FL-specific attack such as:

- model poisoning
- sign-flip update
- malicious client

Then compare plain FedAvg with a robust aggregation method.

### D. Replay protection

Add a server-side set of accepted `(client_id, round, message_id)` values and reject duplicates/stale rounds.

### E. MQTT security

Use MQTT over TLS and broker authentication in the live demonstration.

### F. Dashboard

A simple Streamlit dashboard can display:

- CHSH
- QBER
- key length
- number of clients
- FL round
- accuracy/F1
- communication overhead
- security overhead

### G. Statistical validation

Run each experiment over at least 5 seeds and report mean ± standard deviation.

---

# 11. Final validation procedure before submission

Run this sequence on a clean environment:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q
python -m quantum.e91
python -m experiments.centralized_baseline
python -m experiments.federated_baseline
python -m experiments.secure_fl_demo
python -m experiments.eavesdropping
python -m experiments.noise_experiment
python -m experiments.security_comparison
python -m experiments.performance
python -m experiments.compare_models
```

Then inspect `results/`.

The final report should use the **actual generated numbers**, not expected/example numbers.

---

# 12. Scientific interpretation template

Use language such as:

> The E91 simulation generated the expected nonclassical correlations for the selected measurement settings. The measured CHSH parameter exceeded the classical bound of 2 and approached the theoretical quantum value of 2√2 as the number of shots increased. Under the ideal simulated channel, the sifted key exhibited negligible/zero QBER. Increasing the simulated disturbance increased QBER and degraded Bell correlations.

For FL:

> The federated system trained the model without transferring raw client training samples to the aggregation server. Secure FL introduced cryptographic processing and communication overhead while preserving the model-update aggregation workflow.

Do not claim real-world security from simulation alone.

---

# 13. Final deliverable status

The supplied repository is intended to be the **technical prototype baseline**. Remaining work is primarily validation on the target machine, result collection, plots, stronger experimental design and optional production-oriented additions.
