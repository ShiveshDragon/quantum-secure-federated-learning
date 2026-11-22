import csv, os
from quantum.e91 import run_chsh, simulate_correlation
from quantum.noise import build_depolarizing_noise


def main():
    rows=[]
    for p in [0.0, 0.001, 0.005, 0.01, 0.02, 0.05]:
        noise = None if p == 0 else build_depolarizing_noise(p)
        chsh = run_chsh(shots=8000, seed=20, noise_model=noise)["CHSH"]
        same = simulate_correlation(0, 0, shots=8000, seed=20, noise_model=noise)["correlation"]
        qber = (1 + same) / 2
        rows.append({"depolarizing_probability": p, "chsh": chsh, "equal_basis_qber_estimate": qber})
        print(rows[-1])
    path=os.path.join(os.path.dirname(os.path.dirname(__file__)),"results","noise_experiment.csv")
    with open(path,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)


if __name__ == "__main__": main()
