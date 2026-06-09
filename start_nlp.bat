@echo off
title NLP 問答系統
cd /d "%~dp0"
echo ================================================
echo   自然語言問答系統  (port 8501)
echo ================================================
streamlit run app_nlp.py --server.port 8501 --server.headless false
pause
