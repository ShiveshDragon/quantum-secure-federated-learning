# CHSH + Eve integration fix

## Problem

The dashboard's E91 control already stored Eve's probability, and the E91 API received it. However, the CHSH button posted only `shots` and `noise`; the CHSH endpoint and `run_chsh` therefore simulated a clean entangled pair regardless of the Eve slider. The browser fallback also displayed a near-2.828 score independently of Eve.

## What changed

1. **`frontend/app.js`** — CHSH requests now include `state.e91.eveProbability`. If the Flask backend is offline, the client fallback computes the expected correlations for the same documented attack channel instead of displaying a random, Eve-independent score. The fallback remains a theoretical client-side estimate, not a Qiskit shot simulation.
2. **`server/api_server.py`** — the CHSH endpoint reads and validates `eve_probability`, builds the combined channel model, passes the setting into `run_chsh`, and includes it in the JSON response. Invalid probability values return HTTP 400.
3. **`backend/quantum/e91.py`** — an identity instruction is inserted on Bob's qubit after singlet preparation and before measurement rotations. `run_chsh` passes Eve's probability through to each of the four independently measured setting pairs.
4. **`backend/quantum/noise.py`** — the noise model can combine ordinary depolarizing gate noise with an effective random X/Z-basis intercept-resend channel.
5. **`backend/tests/test_quantum.py`** — added tests for the reduction in CHSH under a full-strength attack and probability validation. The Qiskit-dependent tests skip if Qiskit/Aer are not installed.
6. **`backend/requirements.txt` and `start.bat`** — added Flask dependencies, removed the machine-specific Python path, and fixed the batch `echo` line that previously treated `Serving` as a command.

## Attack channel and expected result

The Eve model represents an intercept-resend attack where Eve randomly chooses the X or Z basis and resends the measured state. Averaged over Eve's basis/outcome, its effective Pauli channel is

- `P(I) = 1 - p/2`
- `P(X) = p/4`
- `P(Z) = p/4`

where `p` is `eve_probability` from 0 to 1. This channel is attached to an `id` instruction on Bob's qubit, after the entangled pair is prepared and before Alice/Bob's measurement rotations. At `p=0`, the ideal CHSH expectation is `2*sqrt(2) ≈ 2.828`. At `p=1`, the model's expected score with these X-Z-plane settings is approximately `sqrt(2) ≈ 1.414`, below the classical bound of 2. Finite-shot values fluctuate around the expectation. Intermediate values decrease in expectation under this specific model; do not interpret every individual finite-shot run as guaranteed monotonic.

This is an effective channel model for the stated random-basis intercept-resend attack, not a complete adversary implementation that stores Eve's measurement record or executes the entire E91 key-distillation/security-proof process. CHSH violation is a diagnostic of correlations; it does not itself prevent an attack. QBER/key-abort logic remains a separate protocol-level check.

## Run on Windows

Open PowerShell in the inner project folder (the folder containing `start.bat`, `server`, `frontend`, and `backend`):

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\backend\requirements.txt
.\start.bat
```

If the virtual environment is in the outer folder instead, activate it using its actual path or create one in this project folder with `python -m venv .venv`. Open `http://127.0.0.1:5000`. The CHSH button uses the current Eve slider value; change the slider and click **Verify CHSH Bell Circuit** again. Check the dashboard status pill: `Live Backend` means Qiskit/Aer results; `Client Quantum Engine` means theoretical fallback.

## Validation

Run from the inner project's `backend` directory:

```powershell
python -m pytest tests -v
```

The new Qiskit tests assert that the clean case violates the classical bound and that the full-strength Eve channel lowers the score substantially. If Qiskit/Aer is unavailable, those simulation tests are skipped rather than pretending that the circuit was executed.
