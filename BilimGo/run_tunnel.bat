@echo off
title BilimGo Cloudflare Tunnel (bilimgo.smart-tools.uk)
echo ======================================================
echo   BilimGo Cloudflare Tunnel ishga tushmoqda...
echo   Domen: https://bilimgo.smart-tools.uk -> http://localhost:8000
echo ======================================================
cloudflared tunnel --config "%~dp0cloudflared_bilimgo.yml" run
pause
