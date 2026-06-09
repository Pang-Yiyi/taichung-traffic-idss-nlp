@echo off
title IDSS 智慧決策支援系統
cd /d "%~dp0"
echo ================================================
echo   智慧決策支援系統  (port 8502)
echo ================================================
streamlit run app_idss.py --server.port 8502 --server.headless false
pause
