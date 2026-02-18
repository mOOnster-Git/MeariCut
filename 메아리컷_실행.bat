@echo off
chcp 65001 >nul

echo ============================================
echo   메아리컷을 준비 중입니다...
echo   잠시만 기다려 주세요.
echo ============================================
echo.

REM 현재 스크립트가 있는 폴더로 이동
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM venv 내부의 python.exe 존재 여부 확인
if not exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
    echo [오류] 가상환경을 찾을 수 없습니다.
    echo 1. 이 폴더 안에서 가상환경을 생성한 뒤
    echo 2. pip install -r requirements.txt 를 실행하시고
    echo    다시 이 파일을 실행해 주세요.
    echo.
    pause
    exit /b 1
)

REM pythonw.exe를 사용하여 까만 창 없이 백그라운드로 프로그램 실행
start "" "%SCRIPT_DIR%venv\Scripts\pythonw.exe" "%SCRIPT_DIR%main.py"

REM 실행 명령을 내렸으니, 까만 bat 창은 스스로 종료합니다.
exit
