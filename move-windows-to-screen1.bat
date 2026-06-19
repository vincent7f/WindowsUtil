@echo off
chcp 65001 >nul
:: Move application windows that are not on screen 1 to the primary monitor
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0move-windows-to-screen1.ps1"
if errorlevel 1 pause
