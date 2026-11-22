# System Architecture: Quantum-Secured Federated Learning for IoT

## 1. High-Level Pipeline

The system integrates four distinct security and machine learning layers:

```
[IoT Sensor Clients 1-5]
          │
          ▼
 [Local Private Datasets]
          │
          ▼
[Local Logistic Model Training]
          │
          ▼
[Generate Parameter Updates: w_k]
          │
          ├─────────────────────────────────────────────────┐
          │ (Optional Adversarial Model-Poisoning)           │
          ▼                                                 ▼
[Clean Delta: Δ_k = w_k - w_g]                [Poisoned Delta: Δ_mal = -γ Δ_k]
          │                                                 │
          └───────────────────────┬─────────────────────────┘
                                  │
                                  ▼
             [E91 Entangled-Photon QKD Simulation]
              (|Ψ⁻⟩ Singlet State, CHSH S ≈ 2.828)
                                  │
                                  ▼
                    [SHA-256 Session Key K_sess]
                                  │
                                  ▼
           [AES-256-GCM Authenticated Encryption (IV + CT)]
                                  │
                                  ▼
            [HMAC-SHA256 Envelope Authentication Tag]
                                  │
                                  ▼
              [MQTT Transport Adapter (or In-Process)]
                                  │
                                  ▼
                       [Central Aggregation Server]
                                  │
                                  ├─ 1. Verify Message Signature (HMAC-SHA256)
                                  ├─ 2. Authenticated Decryption (AES-256-GCM)
                                  ├─ 3. Replay Protection (client_id, round, msg_id)
                                  ├─ 4. Structural & Numerical Validation (Finite, Shapes)
                                  │
                                  ▼
                   [Select Aggregation Strategy]
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
     [FedAvg]            [Coordinate Median]       [Trimmed Mean (β)]
(Weighted Mean)         (Delta Median across N)   (Tail Trimming across N)
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                                  ▼
             [Updated Global Model: w_g^(t+1) = w_g^(t) + Δ_agg]
                                  │
                                  ▼
                  [Global Test Set Evaluation]
                                  │
                                  ▼
                   [Web Dashboard & Results API]
```

---

## 2. Component Breakdown

### 2.1 Quantum Layer (`quantum/`)
- **`e91.py`**: Simulates the Ekert 91 protocol. Prepares singlet photon pairs $|\Psi^-\rangle = \frac{|01\rangle - |10\rangle}{\sqrt{2}}$. Measures in complementary bases ($0^\circ, 45^\circ$ for Alice, $22.5^\circ, -22.5^\circ$ for Bob). Computes correlation $E(a,b) = -\cos(2(a-b))$ and tests the CHSH Bell inequality ($S \approx 2.828 > 2.0$). Executes Qiskit Aer circuit simulation.
- **`noise.py`**: Implements depolarizing quantum noise channels.
- **`attacks.py`**: Intercept-resend eavesdropping disturbance simulation.

### 2.2 Cryptographic Layer (`crypto/`)
- **`key_manager.py`**: Converts sifted quantum key bitstrings to 32-byte cryptographic session keys using SHA-256.
- **`aes_crypto.py`**: AES-256-GCM authenticated encryption with 12-byte random nonces and authenticated associated data context (`client_id:round`).
- **`hmac_auth.py`**: HMAC-SHA256 constant-time envelope signature generation and verification.
- **`replay_detector.py`**: Tracks accepted signatures, message IDs, and round freshness to reject replayed and stale updates.

### 2.3 Federated Learning Layer (`federated/`)
- **`dataset.py`**: Synthetic IoT sensor classification benchmark with StandardScaler, supporting IID and non-IID label skew.
- **`model.py`**: Lightweight logistic regression model with sigmoid activation and binary cross-entropy gradient descent.
- **`client.py`**: Decentralized client keeping local data strictly private; supports clean and adversarial poisoned training (`train_poisoned`).
- **`server.py`**: Central server managing global state, update validation, replay detection, evaluation metrics, and multiple aggregation algorithms.
- **`robust_aggregation.py`**: Coordinate-wise median and trimmed mean operating on update deltas.

### 2.4 Server & Web Application (`server/` and `frontend/`)
- **`server/api_server.py`**: Flask REST API providing endpoints for all quantum, crypto, FL, and robust aggregation features.
- **`frontend/`**: Modern dashboard featuring 7 interactive panels with live charts, parameter sliders, and precomputed research sweeps.
