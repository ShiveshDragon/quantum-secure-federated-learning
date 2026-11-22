from experiments.common import run_fl, save_json


def main():
    plain, _ = run_fl(5, 5, secure=False, seed=42)
    secure, key = run_fl(5, 5, secure=True, seed=42)
    result = {"federated": plain, "federated_plus_security": secure, "qkd": key}
    save_json("security_comparison.json", result)
    print("Final FL accuracy:", plain[-1]["accuracy"])
    print("Final secure FL accuracy:", secure[-1]["accuracy"])
    print("Security overhead per round (s):", [r["mean_encrypt_time"] + r["mean_security_time"] for r in secure])


if __name__ == "__main__": main()
