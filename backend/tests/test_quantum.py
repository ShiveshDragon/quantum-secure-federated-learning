import math
import numpy as np
import pytest
from quantum.e91 import singlet_statevector, theoretical_correlation, calculate_chsh, generate_sifted_key


def test_singlet_statevector_definition():
    expected=np.array([0,1,-1,0],dtype=complex)/math.sqrt(2)
    assert np.allclose(singlet_statevector(), expected)


def test_theoretical_equal_basis_anticorrelation():
    assert theoretical_correlation(0,0) == pytest.approx(-1.0)
    assert theoretical_correlation(45,45) == pytest.approx(-1.0)


def test_theoretical_chsh_settings_reach_tsirelson_bound():
    e11=theoretical_correlation(0,22.5)
    e12=theoretical_correlation(0,-22.5)
    e21=theoretical_correlation(45,22.5)
    e22=theoretical_correlation(45,-22.5)
    assert calculate_chsh(e11,e12,e21,e22) == pytest.approx(2*math.sqrt(2))


def test_qkd_ideal_qber_is_zero():
    r=generate_sifted_key(10000,seed=7)
    assert r.qber == 0.0
    assert len(r.alice_bits) > 0


def test_eavesdropping_raises_qber():
    r=generate_sifted_key(20000,seed=8,eve_probability=1.0)
    assert 0.40 < r.qber < 0.60


def test_qiskit_singlet_and_chsh():
    qiskit=pytest.importorskip("qiskit")
    pytest.importorskip("qiskit_aer")
    from quantum.e91 import simulate_correlation, run_chsh
    assert simulate_correlation(0,0,shots=8000,seed=1)["correlation"] < -0.97
    for a,b in [(0,22.5),(0,-22.5),(45,22.5),(45,-22.5)]:
        got=simulate_correlation(a,b,shots=12000,seed=2)["correlation"]
        assert got == pytest.approx(theoretical_correlation(a,b),abs=0.04)
    assert run_chsh(shots=12000,seed=4)["CHSH"] > 2.5


def test_chsh_eavesdropping_channel_reduces_bell_violation():
    pytest.importorskip("qiskit")
    pytest.importorskip("qiskit_aer")
    from quantum.e91 import run_chsh

    clean = run_chsh(shots=12000, seed=21, eve_probability=0.0)
    attacked = run_chsh(shots=12000, seed=21, eve_probability=1.0)
    assert clean["CHSH"] > 2.5
    assert attacked["CHSH"] < 1.7
    assert attacked["CHSH"] < clean["CHSH"]


def test_chsh_eavesdropping_probability_is_validated():
    pytest.importorskip("qiskit")
    pytest.importorskip("qiskit_aer")
    from quantum.e91 import run_chsh

    with pytest.raises(ValueError):
        run_chsh(eve_probability=-0.1)
    with pytest.raises(ValueError):
        run_chsh(eve_probability=1.1)
