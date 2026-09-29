@echo off
chcp 65001 >nul
title MOVMASSA WebGIS - Angra dos Reis (Modo Rapido)
cd /d "%~dp0"

echo ======================================================================
echo           SISTEMA WEBGIS MOVMASSA - ANGRA DOS REIS (RJ)
echo ======================================================================
echo [✓] Iniciando servidor em modo instantaneo...
echo [✓] O seu navegador padrao sera aberto em instantes.
echo.

python desktop_launcher.py
pause
