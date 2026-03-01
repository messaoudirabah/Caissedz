@echo off
echo ===========================================
echo      CaisseDZ Build Script - NEXGEN MB
echo ===========================================
echo.

echo [1/4] Cleaning previous builds...
rmdir /s /q build
rmdir /s /q dist
del /q *.spec

echo.
echo [2/4] Building Executable with PyInstaller...
echo       This may take a minute. Please wait...
:: Using --windowed to hide console, --icon for app icon, and key data folders
pyinstaller --noconfirm --onedir --windowed --name "CaisseDZ" ^
    --icon "assets/logo.ico" ^
    --add-data "assets;assets" ^
    --add-data "database;database" ^
    --add-data "ui;ui" ^
    --add-data "services;services" ^
    --hidden-import "PySide6" ^
    --hidden-import "sqlite3" ^
    --hidden-import "json" ^
    --hidden-import "win32print" ^
    --hidden-import "win32ui" ^
    --hidden-import "win32con" ^
    --hidden-import "win32api" ^
    main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] PyInstaller failed! Exiting...
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/4] Copying License & Banner...
copy LICENSE.txt dist\CaisseDZ\
if exist assets\banner.jpg (
    copy assets\banner.jpg dist\CaisseDZ\assets\
) else (
    copy banner.jpg dist\CaisseDZ\assets\
)

echo.
echo [4/4] Build Complete!
echo.
echo The executable is located in: dist\CaisseDZ\CaisseDZ.exe
echo.
echo To create the installer:
echo 1. Ensure Inno Setup is installed.
echo 2. Open 'setup.iss'
echo 3. Click 'Compile'
echo.
pause
