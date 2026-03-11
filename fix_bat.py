script="""@echo off
chcp 65001 > nul
cd C:\\Users\\LG\\Desktop\\Hollys_QMS

echo.
echo ========================================
echo   Hollys QMS - 깃허브 업로드
echo ========================================
echo.

git add .
git commit -m "QMS 업데이트 %date% %time%"
git push origin main

echo.
echo ✅ 깃허브 업로드 완료!
echo.
pause
"""
with open(r"c:\Users\LG\Desktop\Hollys_QMS\업로드.bat", "w", encoding="utf-8-sig", newline="\r\n") as f:
    f.write(script)
