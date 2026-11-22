# Scientific Scope & Limitations: Quantum FL-IoT Research Prototype

To maintain strict scientific and academic honesty, the following scope boundaries, assumptions, and engineering limitations must be recognized:

---

## 1. Quantum Key Distribution (E91) Limitations

1. **Simulation Environment**:
   - The E91 quantum key distribution implementation is an educational and research simulation executed via software circuits in Qiskit Aer and numerical statevector calculations.
   - It **does not run on physical quantum optical hardware** (such as entangled photon sources, spontaneous parametric down-conversion crystals, or avalanche photodiode detectors).

2. **Key Post-Processing Protocol**:
   - In production QKD systems, raw sifted bitstrings require:
     - Authenticated classical communication for basis reconciliation.
     - Information reconciliation (error correction using LDPC or Cascade codes).
     - Finite-key security bounds and composable security analysis.
     - Privacy amplification using universal hash functions.
   - In this research prototype, SHA-256 serves as a deterministic privacy-amplification and key derivation placeholder (`derive_session_key`).

3. **Bell Test Security Claims**:
   - A CHSH Bell inequality violation ($S > 2.0$) experimentally demonstrates quantum non-locality and entanglement.
   - **A CHSH violation alone does not prove the complete absence of an eavesdropper**. Standard QKD security relies on strict QBER parameter estimation under finite-key bounds.

---

## 2. Federated Learning & Byzantine Defense Limitations

1. **Robust Aggregation is a Mitigation, Not a Universal Shield**:
   - Coordinate-wise median and trimmed mean mitigate sign-flip and large-magnitude outlier attacks.
   - They **do not protect against stealthy, targeted backdoor attacks** where an attacker crafts gradients that remain near the honest update distribution while activating a malicious trigger.

2. **Byzantine Breakdown Ratios**:
   - Coordinate-wise median is resilient when the malicious fraction $f < N/2$. If $\ge 50\%$ of participating nodes collude, the median will track the malicious update.
   - Trimmed mean with parameter $\beta$ is resilient only when $f \le \lfloor N \cdot \beta \rfloor$. For $N=5, \beta=0.2$, having 2 malicious nodes overwhelms the defense, causing performance collapse.

3. **Non-IID Heterogeneity Trade-Off**:
   - In non-IID settings with extreme label skew, honest clients naturally compute divergent gradient vectors.
   - Robust aggregators may mistake legitimate specialized client updates for malicious outliers, leading to slight accuracy degradation compared to clean FedAvg.

---

## 3. Cryptographic & IoT Transport Scope

1. **Cryptographic Protection Scope**:
   - AES-256-GCM and HMAC-SHA256 authenticate the communication link and ensure in-transit confidentiality.
   - **They do not ensure that the client's internal training data or generated updates are honest**.

2. **MQTT Broker Deployment**:
   - The repository provides standard MQTT transport adapters using `paho-mqtt`.
   - Core automated tests and algorithmic benchmarks run in-process to allow standalone execution without an external broker daemon.
   - Deploying in production requires an external Mosquitto or HiveMQ broker configured with TLS certificates and client authentication.
