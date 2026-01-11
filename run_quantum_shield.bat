@echo off
title Quantum-Shield Scanner
color 0A

echo ========================================================
echo   QUANTUM-SHIELD: Post-Quantum Cryptography Scanner
echo ========================================================
echo.
echo [1/3] Initializing Scan Engine...
echo.

:: Run the scan using Semgrep
semgrep scan --config=quantum_rules.yaml . --json -o results.json

echo.
echo [2/3] Generating Compliance Report...
python generate_report.py

echo.
echo [3/3] Opening Report...
echo.

:: Open the HTML file in the default browser
start report.html

echo Done!
pause