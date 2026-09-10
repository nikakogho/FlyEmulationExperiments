@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" "scripts\view_delivery.py" --path results/odor_scene_v2
if errorlevel 1 pause
