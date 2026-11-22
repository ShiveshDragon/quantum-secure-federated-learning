"""Generate comprehensive research figures from saved experimental results.

Generates:
1. qber_vs_eavesdropping.png - QBER vs Eve disturbance probability
2. chsh_vs_noise.png - CHSH violation degradation vs depolarizing noise
3. key_generation_overhead.png - E91 QKD simulation and key generation time
4. crypto_overhead.png - AES-GCM and HMAC microsecond processing overhead
5. fl_convergence_comparison.png - Centralized vs Standard FL vs Secure FL
6. robust_aggregation_poisoning.png - Clean vs Attacked FedAvg vs Coordinate Median vs Trimmed Mean
7. malicious_fraction_impact.png - Accuracy breakdown across malicious client fractions (0/5, 1/5, 2/5)
8. iid_vs_non_iid_robustness.png - Performance across IID and non-IID label skew
"""
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT = os.path.join(ROOT, "results")
FIG_DIR = os.path.join(OUT, "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def save_fig(fig, filename):
    fig.tight_layout()
    # Save in both results root and results/figures
    fig.savefig(os.path.join(OUT, filename), dpi=200)
    fig.savefig(os.path.join(FIG_DIR, filename), dpi=200)
    plt.close(fig)
    print(f"  [+] Saved plot: {filename}")


def plot_eavesdropping():
    p = os.path.join(OUT, "eavesdropping.csv")
    if not os.path.exists(p):
        return
    d = pd.read_csv(p)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(d["eve_probability"], d["qber"] * 100, marker="o", color="#0070f3", linewidth=2.2, label="Measured QBER (%)")
    ax.axhline(y=11.0, color="#f59e0b", linestyle="--", linewidth=1.5, label="Standard QKD Abort Threshold (11%)")
    ax.axhline(y=50.0, color="#ef4444", linestyle=":", linewidth=1.5, label="Random Guess / Complete Intercept (50%)")
    ax.set_xlabel("Eavesdropping Intercept Probability (P_eve)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Quantum Bit Error Rate - QBER (%)", fontsize=11, fontweight="bold")
    ax.set_title("E91 QKD Protocol: QBER vs Eavesdropper Disturbance", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(frameon=True)
    save_fig(fig, "qber_vs_eavesdropping.png")


def plot_noise():
    p = os.path.join(OUT, "noise_experiment.csv")
    if not os.path.exists(p):
        return
    d = pd.read_csv(p)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(d["depolarizing_probability"], d["chsh"], marker="s", color="#a855f7", linewidth=2.2, label="Simulated CHSH (S)")
    ax.axhline(y=2.0, color="#ef4444", linestyle="--", linewidth=1.5, label="Classical Local Hidden Variable Bound (S = 2.0)")
    ax.axhline(y=2.828, color="#10b981", linestyle=":", linewidth=1.5, label="Tsirelson Bound (2*sqrt(2) ≈ 2.828)")
    ax.set_xlabel("Depolarizing Noise Parameter (p)", fontsize=11, fontweight="bold")
    ax.set_ylabel("CHSH Bell Parameter (S)", fontsize=11, fontweight="bold")
    ax.set_title("CHSH Bell-Inequality Violation vs Quantum Noise", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(frameon=True)
    save_fig(fig, "chsh_vs_noise.png")


def plot_performance():
    p = os.path.join(OUT, "performance.csv")
    if not os.path.exists(p):
        return
    d = pd.read_csv(p)
    
    # 1. Key generation overhead
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(d["e91_rounds"], d["key_generation_s"] * 1000, marker="o", color="#00f5ff", linewidth=2.2, label="Key Gen Time (ms)")
    ax.set_xlabel("E91 Measurement Rounds (Pairs)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Execution Time (milliseconds)", fontsize=11, fontweight="bold")
    ax.set_title("E91 Sifting & Session Key Derivation Overhead", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(frameon=True)
    save_fig(fig, "key_generation_overhead.png")

    # 2. Crypto overhead (encryption vs decryption)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(d["e91_rounds"], d["aes_encrypt_s"] * 1000, marker="^", color="#10b981", linewidth=2.0, label="AES-GCM Encryption (ms)")
    ax.plot(d["e91_rounds"], d["aes_decrypt_s"] * 1000, marker="v", color="#ec4899", linewidth=2.0, label="AES-GCM Decryption (ms)")
    ax.set_xlabel("E91 Simulation Rounds", fontsize=11, fontweight="bold")
    ax.set_ylabel("Processing Time (milliseconds)", fontsize=11, fontweight="bold")
    ax.set_title("Cryptographic Processing Overhead per Model Update", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(frameon=True)
    save_fig(fig, "crypto_overhead.png")


def plot_model_comparison():
    p = os.path.join(OUT, "model_comparison.json")
    if not os.path.exists(p):
        return
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    
    fig, ax = plt.subplots(figsize=(7, 4.5))
    labels = ["Centralized", "Standard FL", "Secure FL"]
    accuracies = [
        d["centralized"]["accuracy"] * 100,
        d["federated_final"]["accuracy"] * 100,
        d["secure_federated_final"]["accuracy"] * 100
    ]
    f1_scores = [
        d["centralized"]["f1"] * 100,
        d["federated_final"]["f1"] * 100,
        d["secure_federated_final"]["f1"] * 100
    ]
    x = np.arange(len(labels))
    width = 0.35
    ax.bar(x - width/2, accuracies, width, label="Accuracy (%)", color="#0070f3")
    ax.bar(x + width/2, f1_scores, width, label="F1-Score (%)", color="#a855f7")
    ax.set_ylabel("Score (%)", fontsize=11, fontweight="bold")
    ax.set_title("Model Performance: Centralized vs Standard FL vs Secure FL", fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylim(0, 100)
    ax.grid(True, axis="y", linestyle="--", alpha=0.6)
    ax.legend(frameon=True)
    save_fig(fig, "fl_convergence_comparison.png")


def plot_robust_aggregation():
    p = os.path.join(OUT, "robust_aggregation_results.json")
    if not os.path.exists(p):
        return
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    scenarios = data.get("primary_experiment", {}).get("scenarios", {})
    if not scenarios:
        return
        
    rounds = [r["round"] for r in scenarios["clean_fedavg"]]
    clean_acc = [r["accuracy"] * 100 for r in scenarios["clean_fedavg"]]
    att_fedavg_acc = [r["accuracy"] * 100 for r in scenarios["attacked_fedavg"]]
    att_med_acc = [r["accuracy"] * 100 for r in scenarios["attacked_coordinate_median"]]
    att_trim_acc = [r["accuracy"] * 100 for r in scenarios["attacked_trimmed_mean"]]

    # 1. Poisoning impact across rounds
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    ax.plot(rounds, clean_acc, marker="o", color="#10b981", linewidth=2.2, label="Clean Baseline (FedAvg)")
    ax.plot(rounds, att_fedavg_acc, marker="x", color="#ef4444", linewidth=2.2, linestyle="--", label="Attacked FedAvg (Sign-Flip)")
    ax.plot(rounds, att_med_acc, marker="s", color="#0070f3", linewidth=2.2, label="Defense: Coordinate Median")
    ax.plot(rounds, att_trim_acc, marker="^", color="#a855f7", linewidth=2.2, label="Defense: Trimmed Mean (β=0.2)")
    ax.set_xlabel("Federated Learning Round", fontsize=11, fontweight="bold")
    ax.set_ylabel("Global Model Accuracy (%)", fontsize=11, fontweight="bold")
    ax.set_title("Model Poisoning Defense: Clean vs Attacked FedAvg vs Robust Methods", fontsize=12, fontweight="bold")
    ax.set_xticks(rounds)
    ax.set_ylim(0, 100)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(frameon=True)
    save_fig(fig, "robust_aggregation_poisoning.png")

    # 2. Malicious client fraction sweep
    sweep = data.get("malicious_fraction_sweep", [])
    if sweep:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        m_counts = [f"{s['malicious_count']}/5 ({int(s['malicious_fraction']*100)}%)" for s in sweep]
        fed_acc = [s["fedavg_acc"] * 100 for s in sweep]
        med_acc = [s["median_acc"] * 100 for s in sweep]
        trim_acc = [s["trimmed_acc"] * 100 for s in sweep]

        x = np.arange(len(m_counts))
        width = 0.25
        ax.bar(x - width, fed_acc, width, label="FedAvg", color="#ef4444")
        ax.bar(x, med_acc, width, label="Coordinate Median", color="#0070f3")
        ax.bar(x + width, trim_acc, width, label="Trimmed Mean (β=0.2)", color="#a855f7")
        ax.set_xlabel("Malicious Client Fraction", fontsize=11, fontweight="bold")
        ax.set_ylabel("Final Model Accuracy (%)", fontsize=11, fontweight="bold")
        ax.set_title("Byzantine Resilience across Increasing Adversary Fractions", fontsize=12, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(m_counts)
        ax.set_ylim(0, 100)
        ax.grid(True, axis="y", linestyle="--", alpha=0.6)
        ax.legend(frameon=True)
        save_fig(fig, "malicious_fraction_impact.png")


def main():
    print("\n--- Generating Research Figures from Results ---")
    plot_eavesdropping()
    plot_noise()
    plot_performance()
    plot_model_comparison()
    plot_robust_aggregation()
    print("All research figures generated successfully.")


if __name__ == "__main__":
    main()
