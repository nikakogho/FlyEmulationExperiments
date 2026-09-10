@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" "scripts\view_delivery.py" --path results/embodied_speed_v1/A_paired
if errorlevel 1 pause
