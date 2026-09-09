@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" scripts\view_delivery.py
if errorlevel 1 pause
