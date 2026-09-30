@echo off
title Enviar Atualizacoes do MOVMASSA para o GitHub
cd /d "c:\Users\Gabriela\app_webgis2"
echo ========================================================
echo  ENVIANDO ATUALIZACOES PARA O GITHUB (RENDER WEB)
echo ========================================================
echo.
echo O Git agora vai se conectar ao GitHub. Se abrir uma janela
echo no seu navegador solicitando autorizacao, clique em "Authorize".
echo.
git push origin main
echo.
if %ERRORLEVEL% equ 0 (
    echo [OK] Atualizacoes enviadas com sucesso para o GitHub!
    echo O Render ja iniciou o deploy automatico da versao Web.
) else (
    echo [!] Ocorreu um problema ao enviar. Verifique o login no GitHub.
)
echo.
pause
