# Validation Run — Current Package

Date: 2026-10-06

## Automated tests

Command:

```bash
python -m pytest -q
```

Observed:

```text
18 passed, 1 skipped
```

The single skipped test is the Qiskit circuit/CHSH test because this build environment does not have `qiskit` or `qiskit-aer` installed.

## Static validation

```bash
python -m compileall -q .
```

Passed.

## Non-Qiskit experiment validation

The following completed successfully:

- centralized baseline
- federated baseline
- secure FL
- eavesdropping sweep
- FL vs FL+security comparison
- performance sweep

Observed examples from this runtime:

- centralized accuracy: `0.85`
- final FL accuracy: `0.85`
- final secure-FL accuracy: `0.85`
- ideal protocol-level QBER: `0.0`
- full Eve disturbance QBER: approximately `0.503`
- 5 secure FL rounds completed successfully

These are **runtime validation values**, not final scientific claims. Re-run on the submission machine and report the actual generated values.

## Not yet executable in this runtime

The following require installation of Qiskit Aer:

- Bell-state circuit measurement validation
- Qiskit correlation validation
- measured CHSH validation
- depolarizing quantum-noise experiment

Install with:

```bash
pip install -r requirements.txt
```

Then run:

```bash
python -m pytest -q
python -m experiments.noise_experiment
python -m quantum.e91
```

The final target-machine validation must show the Qiskit test no longer skipped.
