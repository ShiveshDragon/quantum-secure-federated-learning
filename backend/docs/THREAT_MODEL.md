# Threat Model & Security Analysis: Quantum FL-IoT

## 1. Adversary Model & Assumptions

This research prototype systematically addresses four distinct adversary classes across different stages of the distributed IoT architecture:

| Adversary Class | Location | Objective | Mitigating Defense Layer |
| :--- | :--- | :--- | :--- |
| **External Eavesdropper (Eve)** | Quantum Channel | Intercept or measure entangled photon pairs | **E91 Quantum Key Distribution & CHSH Inequality** |
| **Man-in-the-Middle (MitM)** | Classical / Network | Read or tamper with model updates in transit | **AES-256-GCM + HMAC-SHA256 Authenticated Encryption** |
| **Replay Attacker** | Classical Network | Re-transmit valid updates from prior rounds | **ReplayDetector (Round & Message ID Cache)** |
| **Malicious Authenticated Insider (Byzantine)** | Local IoT Node | Poison the global model via malicious updates | **Robust Aggregation (Coordinate Median & Trimmed Mean)** |

---

## 2. Threat Analysis by Layer

### 2.1 Quantum Key Distribution Threat (Eavesdropping)
- **Attack Formulation**: Eve intercepts photons transmitted between the entangled source and Alice/Bob, measures in her own basis, and resends.
- **Quantum Mechanics Defense**: Measurement collapses the singlet entangled state $|\Psi^-\rangle$. When Alice and Bob compare a subset of measurement outcomes across equal bases, QBER increases linearly with Eve's interception probability:
  $$\text{QBER} \approx 0.5 \times P_{eve}$$
- **Threshold**: If measured $\text{QBER} > 2.0\%$ (or standard $11.0\%$), key establishment is aborted immediately, preventing Eve from gaining any usable session key material.

### 2.2 Classical Network Threats (Confidentiality & Tampering)
- **Eavesdropping on Gradients**: Passive adversaries on MQTT or HTTP channels could reconstruct private training samples from raw model weights.
  - *Defense*: AES-256-GCM authenticated encryption ensures confidentiality.
- **Payload Alteration**: Active adversaries flip bits in model updates.
  - *Defense*: AES-GCM 128-bit authentication tag and HMAC-SHA256 signature reject any altered payload with overwhelming probability ($1 - 2^{-128}$).
- **Associated Data Binding**: Binds message context (`client_id:round`) into the GCM cipher. Moving ciphertext from Client 1 to Client 2 causes immediate cryptographic failure.

### 2.3 Replay Attacks
- **Threat**: An adversary captures a valid encrypted update from Round 1 and replays it in Round 5 to prevent model convergence or stall training.
- **Defense**: Server maintains a stateful cache of seen tuples `(client_id, round_number, message_id)` and verifies message freshness against the server's current round number.

### 2.4 Authenticated Insider Model Poisoning (Byzantine Attacks)
- **Why Cryptography Fails Here**: Cryptography guarantees *authenticity of origin*, not *honesty of intent*. A compromised IoT sensor node encrypts its poisoned update using a valid quantum-derived session key.
- **Attacks Evaluated**:
  1. *Sign-Flip & Amplification*: $\Delta_{poison} = -\gamma (w_{local} - w_{global})$.
  2. *Gaussian Noise Perturbation*: $\Delta_{poison} \sim \mathcal{N}(0, \sigma^2)$.
  3. *Constant DC Bias*: $\Delta_{poison} = c$.
- **Defense (Robust Aggregation)**:
  - Standard FedAvg takes an arithmetic mean, allowing a single extreme outlier to arbitrarily skew the global update.
  - Coordinate Median takes the coordinate-wise median, requiring $f \ge \lceil N/2 \rceil$ colluding nodes to manipulate the direction of descent.
  - Trimmed Mean eliminates the extreme $\beta$-fraction of values from both tails before averaging.
