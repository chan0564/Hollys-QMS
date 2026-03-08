@echo off
chcp 65001 > nul
cd /d C:\Users\%USERNAME%\Desktop\Hollys_QMS

echo.
echo ========================================
echo   Hollys QMS 시작 중...
echo   브라우저가 자동으로 열립니다
echo ========================================
echo.

python -m streamlit run app.py --server.headless false

pause
