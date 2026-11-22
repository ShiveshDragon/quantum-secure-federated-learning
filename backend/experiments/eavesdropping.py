import csv, os
from quantum.e91 import generate_sifted_key


def main():
    out = []
    for p in [0.0, 0.25, 0.5, 0.75, 1.0]:
        r = generate_sifted_key(20000, seed=123, eve_probability=p)
        out.append({"eve_probability": p, "qber": r.qber, "sifted_bits": len(r.alice_bits)})
        print(out[-1])
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results", "eavesdropping.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out[0]); w.writeheader(); w.writerows(out)


if __name__ == "__main__":
    main()
