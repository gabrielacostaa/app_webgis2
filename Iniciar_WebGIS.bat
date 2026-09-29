@echo off
chcp 65001 >nul
title MOVMASSA WebGIS - Angra dos Reis
cd /d "%~dp0"

echo ======================================================================
echo           SISTEMA WEBGIS MOVMASSA - ANGRA DOS REIS (RJ)
echo ======================================================================
echo.
echo Iniciando a aplicacao...
echo.

if exist "dist\WebGIS_Angra.exe" (
    echo [✓] Executando binario portatil (dist\WebGIS_Angra.exe)...
    start "" "dist\WebGIS_Angra.exe"
) else (
    echo [✓] Executando via interpretador Python...
    python desktop_launcher.py
)
