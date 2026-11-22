"""Robust Aggregation Experiment: Defending against model-poisoning in Quantum FL-IoT.

Evaluates FedAvg, coordinate-wise median, and trimmed mean under:
- Clean baseline (0 malicious clients)
- Sign-flip model poisoning attack (1 malicious client)
- Scaled malicious fraction (0, 1, 2 malicious clients out of 5)
- Non-IID label skew heterogeneity
- Multi-seed statistical evaluations (mean and standard deviation)
"""
import os
import sys
import json
from typing import Dict, Any, List
import numpy as np

# Ensure backend root is on sys.path
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from experiments.common import run_fl, save_json


def run_robust_aggregation_comparison(
    n_clients: int = 5,
    rounds: int = 5,
    seed: int = 42,
    attack_factor: float = 3.0,
    trim_ratio: float = 0.2
) -> Dict[str, Any]:
    """Run baseline and attack scenarios under controlled seed and parameters."""
    print(f"\n--- Running Robust Aggregation Benchmark (Seed={seed}, Factor={attack_factor}) ---")

    # 1. Clean FedAvg
    clean_fedavg_rows, _ = run_fl(
        n_clients=n_clients, rounds=rounds, secure=False, seed=seed,
        aggregation_method="fedavg", malicious_clients=[]
    )

    # 2. Attacked FedAvg (1 malicious client: client5)
    attacked_fedavg_rows, _ = run_fl(
        n_clients=n_clients, rounds=rounds, secure=False, seed=seed,
        aggregation_method="fedavg", malicious_clients=["client5"],
        attack_type="sign_flip", attack_factor=attack_factor
    )

    # 3. Attacked Coordinate Median (1 malicious client: client5)
    attacked_median_rows, _ = run_fl(
        n_clients=n_clients, rounds=rounds, secure=False, seed=seed,
        aggregation_method="coordinate_median", malicious_clients=["client5"],
        attack_type="sign_flip", attack_factor=attack_factor
    )

    # 4. Attacked Trimmed Mean (1 malicious client: client5)
    attacked_trimmed_rows, _ = run_fl(
        n_clients=n_clients, rounds=rounds, secure=False, seed=seed,
        aggregation_method="trimmed_mean", trim_ratio=trim_ratio, malicious_clients=["client5"],
        attack_type="sign_flip", attack_factor=attack_factor
    )

    # 5. Clean Robust Aggregations (Measure utility preservation on clean data)
    clean_median_rows, _ = run_fl(
        n_clients=n_clients, rounds=rounds, secure=False, seed=seed,
        aggregation_method="coordinate_median", malicious_clients=[]
    )
    clean_trimmed_rows, _ = run_fl(
        n_clients=n_clients, rounds=rounds, secure=False, seed=seed,
        aggregation_method="trimmed_mean", trim_ratio=trim_ratio, malicious_clients=[]
    )

    # Compute degradation and improvements for final round
    clean_acc = clean_fedavg_rows[-1]["accuracy"]
    att_fedavg_acc = attacked_fedavg_rows[-1]["accuracy"]
    att_median_acc = attacked_median_rows[-1]["accuracy"]
    att_trimmed_acc = attacked_trimmed_rows[-1]["accuracy"]

    degradation = clean_acc - att_fedavg_acc
    median_imp = att_median_acc - att_fedavg_acc
    trimmed_imp = att_trimmed_acc - att_fedavg_acc

    results = {
        "config": {
            "n_clients": n_clients,
            "rounds": rounds,
            "seed": seed,
            "attack_type": "sign_flip",
            "attack_factor": attack_factor,
            "trim_ratio": trim_ratio,
            "malicious_clients": ["client5"]
        },
        "scenarios": {
            "clean_fedavg": clean_fedavg_rows,
            "attacked_fedavg": attacked_fedavg_rows,
            "attacked_coordinate_median": attacked_median_rows,
            "attacked_trimmed_mean": attacked_trimmed_rows,
            "clean_coordinate_median": clean_median_rows,
            "clean_trimmed_mean": clean_trimmed_rows
        },
        "summary": {
            "clean_fedavg_accuracy": clean_acc,
            "attacked_fedavg_accuracy": att_fedavg_acc,
            "attacked_median_accuracy": att_median_acc,
            "attacked_trimmed_accuracy": att_trimmed_acc,
            "accuracy_degradation": degradation,
            "median_robustness_improvement": median_imp,
            "trimmed_robustness_improvement": trimmed_imp
        }
    }
    return results


def run_multi_seed_evaluation(seeds: List[int] = None) -> Dict[str, Any]:
    """Evaluate performance across multiple independent random seeds to report mean and std."""
    if seeds is None:
        seeds = [42, 43, 44, 45, 46]
    print(f"\n--- Running Multi-Seed Robust Aggregation Evaluation (Seeds={seeds}) ---")
    
    metrics_by_method = {
        "clean_fedavg": [],
        "attacked_fedavg": [],
        "attacked_median": [],
        "attacked_trimmed": []
    }

    for s in seeds:
        res = run_robust_aggregation_comparison(rounds=5, seed=s)
        metrics_by_method["clean_fedavg"].append(res["summary"]["clean_fedavg_accuracy"])
        metrics_by_method["attacked_fedavg"].append(res["summary"]["attacked_fedavg_accuracy"])
        metrics_by_method["attacked_median"].append(res["summary"]["attacked_median_accuracy"])
        metrics_by_method["attacked_trimmed"].append(res["summary"]["attacked_trimmed_accuracy"])

    summary = {}
    for method, vals in metrics_by_method.items():
        summary[method] = {
            "mean": float(np.mean(vals)),
            "std": float(np.std(vals)),
            "values": vals
        }
        print(f"  {method:20s}: Mean Acc = {summary[method]['mean']:.4f} +/- {summary[method]['std']:.4f}")

    return {"seeds": seeds, "metrics": summary}


def run_malicious_fraction_sweep() -> List[Dict[str, Any]]:
    """Evaluate performance degradation across malicious client fractions: 0/5, 1/5, 2/5."""
    print("\n--- Running Malicious Client Fraction Sweep ---")
    fractions = [
        {"mal_count": 0, "mal_clients": []},
        {"mal_count": 1, "mal_clients": ["client5"]},
        {"mal_count": 2, "mal_clients": ["client4", "client5"]}
    ]
    records = []
    for f in fractions:
        m_count = f["mal_count"]
        m_clients = f["mal_clients"]
        
        fedavg_rows, _ = run_fl(rounds=5, seed=42, aggregation_method="fedavg", malicious_clients=m_clients)
        median_rows, _ = run_fl(rounds=5, seed=42, aggregation_method="coordinate_median", malicious_clients=m_clients)
        trimmed_rows, _ = run_fl(rounds=5, seed=42, aggregation_method="trimmed_mean", malicious_clients=m_clients)
        
        entry = {
            "malicious_count": m_count,
            "malicious_fraction": m_count / 5.0,
            "fedavg_acc": fedavg_rows[-1]["accuracy"],
            "median_acc": median_rows[-1]["accuracy"],
            "trimmed_acc": trimmed_rows[-1]["accuracy"],
            "fedavg_f1": fedavg_rows[-1]["f1"],
            "median_f1": median_rows[-1]["f1"],
            "trimmed_f1": trimmed_rows[-1]["f1"]
        }
        records.append(entry)
        print(f"  Malicious {m_count}/5: FedAvg Acc={entry['fedavg_acc']:.4f}, Median Acc={entry['median_acc']:.4f}, Trimmed Acc={entry['trimmed_acc']:.4f}")
    return records


def run_non_iid_comparison() -> Dict[str, Any]:
    """Compare robust aggregation under IID versus non-IID label skew."""
    print("\n--- Running IID vs Non-IID Robust Aggregation Comparison ---")
    
    # IID with 1 attacker
    iid_fedavg, _ = run_fl(rounds=5, non_iid=False, aggregation_method="fedavg", malicious_clients=["client5"])
    iid_median, _ = run_fl(rounds=5, non_iid=False, aggregation_method="coordinate_median", malicious_clients=["client5"])
    
    # Non-IID with 1 attacker
    non_iid_fedavg, _ = run_fl(rounds=5, non_iid=True, aggregation_method="fedavg", malicious_clients=["client5"])
    non_iid_median, _ = run_fl(rounds=5, non_iid=True, aggregation_method="coordinate_median", malicious_clients=["client5"])
    
    res = {
        "iid": {
            "attacked_fedavg_acc": iid_fedavg[-1]["accuracy"],
            "attacked_median_acc": iid_median[-1]["accuracy"]
        },
        "non_iid": {
            "attacked_fedavg_acc": non_iid_fedavg[-1]["accuracy"],
            "attacked_median_acc": non_iid_median[-1]["accuracy"]
        }
    }
    print(f"  IID:     Attacked FedAvg={res['iid']['attacked_fedavg_acc']:.4f}, Median={res['iid']['attacked_median_acc']:.4f}")
    print(f"  Non-IID: Attacked FedAvg={res['non_iid']['attacked_fedavg_acc']:.4f}, Median={res['non_iid']['attacked_median_acc']:.4f}")
    return res


def main():
    print("===============================================================")
    print("EXPERIMENT: ROBUST AGGREGATION & MODEL-POISONING MITIGATION")
    print("===============================================================")
    
    # Primary comparison
    primary = run_robust_aggregation_comparison()
    
    # Multi-seed evaluation
    multi_seed = run_multi_seed_evaluation([42, 43, 44, 45, 46])
    
    # Malicious fraction sweep
    fraction_sweep = run_malicious_fraction_sweep()
    
    # Non-IID evaluation
    non_iid = run_non_iid_comparison()
    
    output = {
        "primary_experiment": primary,
        "multi_seed_analysis": multi_seed,
        "malicious_fraction_sweep": fraction_sweep,
        "non_iid_comparison": non_iid
    }
    
    save_path = save_json("robust_aggregation_results.json", output)
    print(f"\n[+] Robust aggregation results saved to: {save_path}")


if __name__ == "__main__":
    main()
