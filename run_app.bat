@echo off
echo ===============================================
echo   CrimeVision AI - Forensic Analysis Platform
echo   Skill Wallet Capstone Project 2
echo ===============================================
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting Streamlit application...
echo.
echo Access the app at: http://localhost:8501
echo.
streamlit run app.py --server.headless false --server.port 8501
