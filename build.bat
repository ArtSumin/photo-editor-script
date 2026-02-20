@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

:: Определяем текущую директорию скрипта
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "VENV=%SCRIPT_DIR%\.venv"
set "DIST=%SCRIPT_DIR%\dist"
set "PRODUCTION=%SCRIPT_DIR%\production"

echo =========================================
echo   Сборка Photo Editor для Windows (.exe)
echo =========================================
echo.

:: Активируем venv, если есть
if exist "%VENV%\Scripts\activate.bat" (
    call "%VENV%\Scripts\activate.bat"
)

:: Проверяем наличие PyInstaller
where pyinstaller >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [📦] PyInstaller не найден. Устанавливаю...
    pip install pyinstaller
)

:: Создаём папку production
if not exist "%PRODUCTION%" mkdir "%PRODUCTION%"

:: ─── 1. Основной скрипт ──────────────────────────────────────────────────────

set "SRC=%SCRIPT_DIR%\photo_editor.py"
set "OUT_NAME=photo_editor"

echo 🔧 [1/2] Сборка основного скрипта (%OUT_NAME%) ...
pyinstaller --onefile --name "%OUT_NAME%" "%SRC%" --noconfirm --clean --log-level WARN

move /Y "%DIST%\%OUT_NAME%.exe" "%PRODUCTION%\%OUT_NAME%.exe" >nul
rmdir /Q /S "%SCRIPT_DIR%\build" 2>nul
rmdir /Q /S "%DIST%" 2>nul
del /Q /F "%SCRIPT_DIR%\%OUT_NAME%.spec" 2>nul

echo    [+] Готово: production\%OUT_NAME%.exe
echo.

:: ─── 2. Пресеты ──────────────────────────────────────────────────────────────

set "PRESETS_DIR=%SCRIPT_DIR%\presets"

for %%F in ("%PRESETS_DIR%\make_*.py") do (
    set "preset_file=%%F"
    set "base=%%~nF"
    
    :: Заменяем подчёркивания на дефисы для имени бинарника
    set "bin_name=!base:_=-!"
    
    echo 🔧 [2/2] Сборка пресета !bin_name! ...
    pyinstaller --onefile --name "!bin_name!" "%%F" --noconfirm --clean --log-level WARN
    
    move /Y "%DIST%\!bin_name!.exe" "%PRODUCTION%\!bin_name!.exe" >nul
    rmdir /Q /S "%SCRIPT_DIR%\build" 2>nul
    rmdir /Q /S "%DIST%" 2>nul
    del /Q /F "%SCRIPT_DIR%\!bin_name!.spec" 2>nul
    
    echo    [+] Готово: production\!bin_name!.exe
    echo.
)

echo =========================================
echo   ✅ Все бинарники собраны в: production\
echo =========================================
dir /b "%PRODUCTION%"
echo =========================================
echo.
echo Нажмите любую клавишу для выхода...
pause >nul
