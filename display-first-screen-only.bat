@echo off
chcp 65001 >nul
:: Set display mode to primary monitor only (first screen)
"%SystemRoot%\System32\DisplaySwitch.exe" /internal
