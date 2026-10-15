@echo off
cd /d "%~dp0"
python main.py
if errorlevel 1 (
  echo.
  echo Aplikasi tidak dapat dijalankan. Pastikan Python dan dependency CustomTkinter telah terpasang.
  echo Install dependency dengan: python -m pip install -r requirements.txt
  pause
)
