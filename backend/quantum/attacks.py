from .e91 import generate_sifted_key


def run_intercept_resend(rounds=5000, eve_probability=1.0, seed=1234):
    return generate_sifted_key(rounds, seed=seed, eve_probability=eve_probability)
