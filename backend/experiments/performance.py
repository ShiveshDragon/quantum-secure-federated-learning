import csv, os, time
from quantum.e91 import generate_sifted_key, run_chsh
from crypto.key_manager import derive_session_key
from crypto.aes_crypto import encrypt_json, decrypt_json


def main():
    rows=[]
    for bits in [512, 1024, 2048, 4096, 8192]:
        t=time.perf_counter(); e91=generate_sifted_key(bits, seed=77); key_t=time.perf_counter()-t
        key=derive_session_key(e91.alice_bits)
        payload={"client_id":"client1","round":1,"weights":[0.1]*64,"bias":[0.2],"sample_count":100}
        t=time.perf_counter(); enc=encrypt_json(key,payload); enc_t=time.perf_counter()-t
        t=time.perf_counter(); decrypt_json(key,enc); dec_t=time.perf_counter()-t
        rows.append({"e91_rounds":bits,"sifted_bits":len(e91.alice_bits),"qber":e91.qber,"key_generation_s":key_t,"aes_encrypt_s":enc_t,"aes_decrypt_s":dec_t})
        print(rows[-1])
    path=os.path.join(os.path.dirname(os.path.dirname(__file__)),"results","performance.csv")
    with open(path,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)


if __name__ == "__main__": main()
