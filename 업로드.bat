@echo off
chcp 65001 > nul
cd C:\Users\LG\Desktop\Hollys_QMS

echo.
echo ========================================
echo   Hollys QMS - 깃허브 업로드
echo ========================================
echo.

git add app.py
git commit -m "QMS 업데이트 %date% %time%"
git push

echo.
echo ✅ 깃허브 업로드 완료!
echo.
pause
