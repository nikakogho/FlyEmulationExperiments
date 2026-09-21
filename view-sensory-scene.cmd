@echo off
cd /d "%~dp0"
echo Recorded mechanical sensory fixture. No connectome or learning model.
echo Space: play/pause. Arrows: step. R: rewind. Mouse: orbit and zoom.
".venv\Scripts\python.exe" "scripts\view_delivery.py" --path "results\sensory_scene_v2"
if errorlevel 1 pause
