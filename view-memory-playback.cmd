@echo off
cd /d "%~dp0"
echo Archived neural-output mechanical playback. No live brain or sensory feedback.
echo Space: play/pause. Arrows: step. R: rewind. Mouse: orbit and zoom.
".venv\Scripts\python.exe" "scripts\view_delivery.py" --path "results\saved_motor_body_v1\A_paired"
if errorlevel 1 pause
