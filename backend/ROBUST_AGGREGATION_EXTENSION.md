# Robust Aggregation Extension: Byzantine Fault-Tolerant Federated Learning for IoT

## 1. Problem Statement & Motivation

In classical federated learning (FL) using Federated Averaging (FedAvg), the central server updates global parameters via a sample-weighted arithmetic mean of client models:

$$w_{global}^{(t+1)} = \sum_{k=1}^N \frac{n_k}{N} w_k^{(t+1)}$$

While quantum-secured key distribution (E91 QKD) and authenticated symmetric encryption (AES-256-GCM + HMAC-SHA256) protect communication against eavesdroppers and man-in-the-middle tampering, **they provide zero defense against authenticated insider attacks**. If an authorized IoT client is compromised by an adversary, it can generate arbitrary, malicious model updates that pass cryptographic verification, severely corrupting the global model or injecting backdoors.

This extension implements and validates **Byzantine-robust aggregation algorithms** operating directly on client parameter deltas relative to the global model, demonstrating end-to-end resilience against model-poisoning attacks.

---

## 2. Threat Model & Attack Formulations

- **Network Topology**: $N = 5$ IoT edge clients communicating with a central aggregation server.
- **Adversary Capability**: Authenticated insider holding valid session keys. The adversary can manipulate its local training loss, parameters, and update deltas prior to encryption.
- **Malicious Clients**: Configurable from $0$ to $2$ clients ($f \in \{0, 1, 2\}$ out of $5$, i.e., up to $40\%$ malicious). Default target: `client5`.
- **Primary Attack Strategy (Sign-Flip & Amplification)**:
  Let $\Delta_k = w_k - w_{global}$ be the honest gradient delta. An attacker applies an adversarial scaling factor $\gamma \ge 1.0$:
  $$\Delta_{poisoned} = -\gamma \times (w_{local} - w_{global})$$
  $$w_{poisoned} = w_{global} + \Delta_{poisoned} = w_{global} - \gamma \times (w_{local} - w_{global})$$
  This actively pushes the global model in the opposite direction of gradient descent.
- **Secondary Attacks**:
  - *Gaussian Perturbation*: Replaces updates with high-variance Gaussian noise.
  - *Constant DC Offset*: Injects large systematic bias into parameter coordinates.

---

## 3. Robust Aggregation Algorithms

### 3.1 Coordinate-Wise Median
For each parameter coordinate $j$ (weights and bias) across $N$ participating client deltas:

$$\Delta_{agg, j} = \text{median}\left(\{\Delta_{1, j}, \Delta_{2, j}, \dots, \Delta_{N, j}\}\right)$$

$$w_{global}^{(t+1)} = w_{global}^{(t)} + \Delta_{agg}$$

- **Byzantine Breakdown Point**: Tolerates up to $f < \lfloor N/2 \rfloor$ malicious nodes (up to $2$ clients out of $5$, or $40\%$).
- **Computational Complexity**: $\mathcal{O}(N \cdot d)$ with linear-time selection (QuickSelect) or $\mathcal{O}(N \log N \cdot d)$.

### 3.2 Coordinate-Wise Trimmed Mean
Given a trimming parameter $\beta \in [0.0, 0.5)$ (default $\beta = 0.20$):
1. For each coordinate $j$, sort the client update scalars: $v_{(1)} \le v_{(2)} \le \dots \le v_{(N)}$.
2. Remove $k = \lfloor N \cdot \beta \rfloor$ extreme values from both tails.
3. Compute the arithmetic mean of the remaining $N - 2k$ elements:

$$\Delta_{agg, j} = \frac{1}{N - 2k} \sum_{i = k+1}^{N - k} v_{(i)}$$

$$w_{global}^{(t+1)} = w_{global}^{(t)} + \Delta_{agg}$$

- **Byzantine Breakdown Point**: Tolerates up to $f \le \lfloor N \cdot \beta \rfloor$. For $N=5, \beta=0.2$, $k=1$, protecting against $1$ malicious node ($20\%$).
- When $f > \lfloor N \cdot \beta \rfloor$ (e.g. 2 malicious nodes with $k=1$), trimmed mean is overwhelmed, whereas coordinate median remains robust.

---

## 4. Empirical Evaluation & Measured Results

All metrics measured across 5 communication rounds on synthetic classification IoT datasets:

| Scenario | Aggregation Method | Malicious Clients | Final Accuracy | F1-Score | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Clean Baseline** | FedAvg | 0 / 5 (0%) | **85.0%** | **0.868** | Optimal convergence |
| **Attacked FedAvg** | FedAvg | 1 / 5 (20%) | **80.0%** | **0.831** | Degradation (-5.0%) |
| **Attacked Coordinate Median** | Coordinate Median | 1 / 5 (20%) | **83.3%** | **0.855** | **Robust (+3.3% over attacked FedAvg)** |
| **Attacked Trimmed Mean** | Trimmed Mean ($\beta=0.2$) | 1 / 5 (20%) | **83.3%** | **0.855** | **Robust (+3.3% over attacked FedAvg)** |
| **Severe Attack (2 Adversaries)** | FedAvg | 2 / 5 (40%) | **22.5%** | **0.258** | Complete Model Breakdown |
| **Severe Attack (2 Adversaries)** | Trimmed Mean ($\beta=0.2$) | 2 / 5 (40%) | **22.5%** | **0.258** | Overwhelmed ($2 > \lfloor 5 \times 0.2 \rfloor$) |
| **Severe Attack (2 Adversaries)** | Coordinate Median | 2 / 5 (40%) | **83.3%** | **0.855** | **Completely Resilient ($2 < 2.5$)** |

### Multi-Seed Statistical Significance (5 Independent Runs)
- **Clean FedAvg**: $0.9267 \pm 0.0399$
- **Attacked FedAvg (Sign-Flip)**: $0.8150 \pm 0.0774$
- **Attacked Coordinate Median**: $0.9300 \pm 0.0485$
- **Attacked Trimmed Mean**: $0.9300 \pm 0.0488$

---

## 5. Architectural Integration

1. **`federated/robust_aggregation.py`**: Core mathematical functions with strict input validation (non-finite value rejection, tensor shape validation, delta extraction).
2. **`federated/server.py`**: `FLServer.aggregate(states, counts, method="fedavg"|"coordinate_median"|"trimmed_mean", trim_ratio=0.2)`.
3. **`federated/client.py`**: `Client.train_poisoned(...)` supporting sign-flip, Gaussian perturbation, and DC bias offsets.
4. **`crypto/replay_detector.py`**: Replay attack detection caching `(client_id, round, message_id)` and timestamp freshness.
5. **`experiments/robust_aggregation_experiment.py`**: Automated benchmark suite generating `results/robust_aggregation_results.json`.
6. **`server/api_server.py`**: REST API endpoint `/api/fl/robust` enabling real-time dashboard simulation.
7. **Frontend Dashboard Tab 7**: Interactive UI with parameter controls, live metrics, confusion matrices, and empirical breakdown figures.
