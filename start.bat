@echo off
cd /d "%~dp0"
title Quantum FL-IoT Research Prototype
echo ========================================================
echo Quantum-Secured Federated Learning for IoT Networks
echo Starting Flask API Server and Frontend Dashboard
echo ========================================================
set "PYTHON_EXE=python"
if exist "%~dp0..\.venv\Scripts\python.exe" set "PYTHON_EXE=%~dp0..\.venv\Scripts\python.exe"
if exist "%~dp0.venv\Scripts\python.exe" set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
start "" cmd /c "timeout /t 2 >nul & start http://127.0.0.1:5000"
"%PYTHON_EXE%" server\api_server.py
pause
