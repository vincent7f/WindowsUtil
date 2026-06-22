@echo off
chcp 65001 >nul
python "%~dp0gui\app.py"
if errorlevel 1 pause
