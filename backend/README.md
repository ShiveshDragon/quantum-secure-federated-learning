# Quantum-Secured Federated Learning for IoT Networks with Robust Aggregation

**Paper Reference:** *Integrating quantum computing with federated learning for enhanced security and privacy in IoT networks*  
*Results in Engineering (RINENG), Elsevier*, DOI: [10.1016/j.rineng.2025.108500](https://doi.org/10.1016/j.rineng.2025.108500)

This repository is a research prototype combining:
- **E91 Entangled-Photon Quantum Key Distribution (QKD)** simulation with Qiskit Aer circuits
- **CHSH Bell-Inequality Verification** demonstrating quantum non-locality ($S \approx 2.828 > 2.0$)
- **AES-256-GCM Authenticated Encryption** and **HMAC-SHA256 Integrity Verification**
- **Cryptographic Replay Attack Protection** (message ID, session, and round tracking)
- **Decentralized Multi-Client Federated Learning (FedAvg)**
- **Byzantine-Robust Aggregation Extension**: Coordinate-Wise Median & Trimmed Mean defending against authenticated model-poisoning adversaries
- **MQTT Transport Adapters** for edge IoT messaging
- **Interactive Web Dashboard** featuring 7 panels, real-time parameter controls, live metrics, and research figures

---

## 1. System Architecture

```
[IoT Sensor Nodes 1-5] -> [Local Model Training] -> [Optional Poisoning]
       │
       ▼
[E91 QKD Simulation (|Ψ⁻⟩, S ≈ 2.828)] -> [SHA-256 Session Key]
       │
       ▼
[AES-256-GCM Encryption + HMAC-SHA256 Signing + Replay Protection Metadata]
       │
       ▼
[Central FL Server Verification & Decryption]
       │
       ▼
[Robust Aggregation: Coordinate Median / Trimmed Mean / FedAvg]
       │
       ▼
[Global Model Update & Test Evaluation] -> [Interactive Web Dashboard]
```

---

## 2. Directory Structure

```text
quantum_fl_iot/
├── README.md                           # Main technical documentation
├── ROBUST_AGGREGATION_EXTENSION.md     # Specification of the Byzantine defense extension
├── IMPLEMENTATION_AND_VALIDATION.md   # Implementation and validation notes
├── requirements.txt                    # Project dependencies
├── start.bat                           # One-click Windows launch script
├── quantum/                            # Quantum simulation layer
│   ├── e91.py                          # E91 protocol, singlet preparation, CHSH circuits
│   ├── noise.py                        # Depolarizing noise model
│   └── attacks.py                      # Intercept-resend eavesdropping model
├── crypto/                             # Cryptographic layer
│   ├── aes_crypto.py                   # AES-256-GCM with associated data
│   ├── hmac_auth.py                    # HMAC-SHA256 constant-time verification
│   ├── key_manager.py                  # Bitstring conversion & session key derivation
│   └── replay_detector.py              # Replay, duplicate, and stale message detection
├── federated/                          # Federated learning engine
│   ├── dataset.py                      # Synthetic IoT sensor dataset & IID/non-IID split
│   ├── model.py                        # SimpleLogisticModel & classification metrics
│   ├── client.py                       # IoT Client with clean & train_poisoned() methods
│   ├── fedavg.py                       # Standard sample-weighted FedAvg
│   ├── robust_aggregation.py           # Coordinate-wise median & trimmed mean
│   └── server.py                       # FLServer supporting FedAvg & robust aggregations
├── mqtt/                               # Optional MQTT transport
│   ├── payload.py                      # Topic formatting & payload serialization
│   ├── client_mqtt.py                  # Client MQTT publisher/subscriber adapter
│   └── server_mqtt.py                  # Server MQTT aggregator adapter
├── experiments/                        # Technical reproducible experiment suite
│   ├── common.py                       # Shared orchestration pipeline
│   ├── centralized_baseline.py         # Centralized ML benchmark
│   ├── federated_baseline.py           # Standard FedAvg baseline
│   ├── secure_fl_demo.py               # Secure FL with E91 + AES + HMAC
│   ├── eavesdropping.py                # Eve intercept-resend sweep
│   ├── noise_experiment.py             # Depolarizing noise sweep
│   ├── security_comparison.py          # Microsecond security timing benchmarks
│   ├── performance.py                  # Execution time vs quantum rounds
│   ├── compare_models.py               # Comparative model analysis
│   ├── robust_aggregation_experiment.py# Model poisoning & robust aggregation sweeps
│   ├── plot_results.py                 # Generates publication-ready figures
│   └── run_all.py                      # Executes entire benchmark suite
├── tests/                              # Automated test suite (31 unit & integration tests)
├── results/                            # Saved JSON/CSV outputs and generated figures
├── server/                             # Backend API server
│   └── api_server.py                   # Flask REST server serving dashboard & API
└── frontend/                           # Interactive research web dashboard
    ├── index.html                      # Modern 7-tab dashboard interface
    ├── style.css                       # Curated styling, dark mode, glassmorphism
    └── app.js                          # Client controller & real-time simulation engine
```

---

## 3. Installation & Setup

Recommended Python version: **3.11 - 3.13**.

```powershell
# 1. Navigate to the backend directory
cd "c:\Users\chall\OneDrive\Desktop\quantum_project_1\quantum_project_1\backend"

# 2. Install dependencies
pip install -r requirements.txt
```

---

## 4. Execution Commands

### A. Start the Interactive Web Dashboard
Run the one-click script:
```powershell
# Double-click start.bat in the root folder, or run:
cd "c:\Users\chall\OneDrive\Desktop\quantum_project_1\quantum_project_1"
python server/api_server.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

### B. Run Automated Unit & Integration Tests
```powershell
cd "c:\Users\chall\OneDrive\Desktop\quantum_project_1\quantum_project_1\backend"
python -m pytest tests -v
```
*(All 31 tests pass with 100% success).*

### C. Run All Technical Experiments
```powershell
python experiments/run_all.py
```

### D. Regenerate Research Figures
```powershell
python experiments/plot_results.py
```

---

## 5. Measured Experimental Findings

### Model Poisoning Resilience (5 Clients, Sign-Flip Attack)
- **Clean FedAvg (0 Attackers)**: Accuracy = **85.0%**, F1 = 0.868
- **Attacked FedAvg (1 Attacker)**: Accuracy drops to **80.0%** (-5.0% degradation)
- **Coordinate Median (1 Attacker)**: Accuracy = **83.3%** (**+3.3% improvement** over attacked FedAvg)
- **Trimmed Mean (1 Attacker, $\beta=0.2$)**: Accuracy = **83.3%** (**+3.3% improvement** over attacked FedAvg)
- **Severe Attack (2 Attackers - 40% Malicious)**:
  - *FedAvg*: **22.5%** (Complete collapse)
  - *Trimmed Mean*: **22.5%** (Overwhelmed when $f > \lfloor N \beta \rfloor$)
  - *Coordinate Median*: **83.3%** (**Completely resilient**, holding within 1.7% of clean baseline)

### QKD Eavesdropping & Quantum Non-Locality
- **Ideal Protocol QBER**: **0.0%**
- **QBER with Full Eve Eavesdropping**: **50.3%** (Triggers mandatory key abort)
- **Ideal CHSH Score**: **2.805** (Violates classical local-hidden-variable limit of 2.0)
- **Security Overhead per Client Update**: **< 2.0 ms** for AES-256-GCM encryption and HMAC signing

---

## 6. Detailed Documentation
- [System Architecture](file:///c:/Users/chall/OneDrive/Desktop/quantum_project_1/quantum_project_1/backend/docs/ARCHITECTURE.md)
- [Threat Model & Security Analysis](file:///c:/Users/chall/OneDrive/Desktop/quantum_project_1/quantum_project_1/backend/docs/THREAT_MODEL.md)
- [Experiment Guide](file:///c:/Users/chall/OneDrive/Desktop/quantum_project_1/quantum_project_1/backend/docs/EXPERIMENTS.md)
- [Results & Empirical Analysis](file:///c:/Users/chall/OneDrive/Desktop/quantum_project_1/quantum_project_1/backend/docs/RESULTS_AND_ANALYSIS.md)
- [Scope & Scientific Limitations](file:///c:/Users/chall/OneDrive/Desktop/quantum_project_1/quantum_project_1/backend/docs/LIMITATIONS.md)
- [Robust Aggregation Technical Specification](file:///c:/Users/chall/OneDrive/Desktop/quantum_project_1/quantum_project_1/backend/ROBUST_AGGREGATION_EXTENSION.md)
