# Experiments Guide: Quantum FL-IoT Security Prototype

This document outlines the full suite of reproducible research experiments included in the project, their configurations, execution commands, and expected outputs.

---

## 1. Running the Complete Experiment Suite

To run all experiments sequentially and generate all research outputs:

```powershell
cd "c:\Users\chall\OneDrive\Desktop\quantum_project_1\quantum_project_1\backend"
python experiments/run_all.py
```

To regenerate all high-resolution research figures:

```powershell
python experiments/plot_results.py
```

---

## 2. Individual Experiment Modules

### 2.1 Centralized Baseline (`experiments/centralized_baseline.py`)
- **Objective**: Evaluates an upper-bound benchmark model trained directly on the pooled dataset (600 samples, 8 features, 40 epochs).
- **Execution**: `python experiments/centralized_baseline.py`
- **Measured Metrics**: Accuracy: 85.0%, Precision: 0.766, Recall: 1.000, F1-Score: 0.868.

### 2.2 Federated Learning Baseline (`experiments/federated_baseline.py`)
- **Objective**: Simulates 5 decentralized IoT nodes running standard FedAvg over 5 global rounds.
- **Execution**: `python experiments/federated_baseline.py`
- **Output**: Saved to `results/federated_baseline_results.json`. Final Accuracy: 85.0%, F1: 0.868.

### 2.3 Secure Federated Learning (`experiments/secure_fl_demo.py`)
- **Objective**: Runs federated learning with E91 QKD key establishment, AES-256-GCM encryption, HMAC authentication, and payload size tracking.
- **Execution**: `python experiments/secure_fl_demo.py`
- **Output**: Saved to `results/secure_fl_results.json`. Demonstrates 0% accuracy penalty (Accuracy: 85.0%) with payload size ~2,660 bytes.

### 2.4 Eavesdropping Sweep (`experiments/eavesdropping.py`)
- **Objective**: Sweeps Eve's interception probability $P_{eve} \in [0.0, 0.25, 0.50, 0.75, 1.00]$ over 20,000 photon pairs.
- **Execution**: `python experiments/eavesdropping.py`
- **Output**: Saved to `results/eavesdropping.csv`. Shows QBER rising from 0.0% to 50.3%.

### 2.5 Quantum Noise Sweep (`experiments/noise_experiment.py`)
- **Objective**: Evaluates Bell parameter degradation under depolarizing quantum noise channels with parameter $p \in [0.0, 0.001, 0.005, 0.01, 0.02, 0.05]$.
- **Execution**: `python experiments/noise_experiment.py`
- **Output**: Saved to `results/noise_experiment.csv`. CHSH violations remain valid ($S > 2.0$) across realistic noise levels.

### 2.6 Security & Timing Comparison (`experiments/security_comparison.py`)
- **Objective**: Measures the exact per-round microsecond overhead introduced by the cryptographic security pipeline.
- **Execution**: `python experiments/security_comparison.py`
- **Output**: Saved to `results/security_comparison.json`. Cryptographic overhead is < 1.0 ms per round.

### 2.7 Computational Performance Benchmarks (`experiments/performance.py`)
- **Objective**: Benchmarks execution time scaling for E91 simulation, key generation, AES-256-GCM encryption, and decryption across pair counts from 512 to 8,192.
- **Execution**: `python experiments/performance.py`
- **Output**: Saved to `results/performance.csv`.

### 2.8 Model Comparison (`experiments/compare_models.py`)
- **Objective**: Directly compares Centralized vs Standard FL vs Secure FL on identical datasets.
- **Execution**: `python experiments/compare_models.py`
- **Output**: Saved to `results/model_comparison.json`.

### 2.9 Robust Aggregation & Byzantine Defense (`experiments/robust_aggregation_experiment.py`)
- **Objective**: Evaluates FedAvg, Coordinate-Wise Median, and Trimmed Mean under sign-flip attacks, multi-seed statistical sweeps, multiple malicious client fractions (0/5, 1/5, 2/5), and non-IID label skew.
- **Execution**: `python experiments/robust_aggregation_experiment.py`
- **Output**: Saved to `results/robust_aggregation_results.json`.
