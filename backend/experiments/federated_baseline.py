from experiments.common import run_fl, save_json


def main():
    rows, _ = run_fl(n_clients=5, rounds=5, secure=False)
    for row in rows:
        print(f"Round {row['round']}: accuracy={row['accuracy']:.4f}, F1={row['f1']:.4f}")
    save_json("federated_baseline_results.json", {"rounds": rows})


if __name__ == "__main__":
    main()
