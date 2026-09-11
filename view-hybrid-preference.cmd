@echo off
cd /d "%~dp0"
echo Recorded live neural/physics coupling with engineered navigation.
echo Learned source preference was not established. Playback creates no neural exposure.
echo Space: play/pause. Arrows: step. R: rewind. Mouse: orbit and zoom.
".venv\Scripts\python.exe" "scripts\view_delivery.py" --path "results\hybrid_preference_v1\seed315_A\paired"
if errorlevel 1 pause
