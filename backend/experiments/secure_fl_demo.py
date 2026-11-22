from experiments.common import run_fl, save_json


def main():
    rows, key_info = run_fl(n_clients=5, rounds=5, secure=True)
    for row in rows:
        print(f"Round {row['round']}: accuracy={row['accuracy']:.4f}, F1={row['f1']:.4f}, bytes={row['total_payload_bytes']}")
    save_json("secure_fl_results.json", {"key": key_info, "rounds": rows})


if __name__ == "__main__":
    main()
