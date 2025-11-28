@echo off
setlocal enabledelayedexpansion

:: ================================================================
:: One-Click Random Browse
:: ================================================================

echo.
echo ========================================
echo    Douyin RPA - Random Browse
echo ========================================
echo.

:: 1. Check Appium Service (Port 4723)
echo [1/3] Checking Appium Service...
netstat -ano | find "4723" | find "LISTENING" >nul
if "%ERRORLEVEL%"=="0" (
    echo [OK] Appium is running (Port 4723)
) else (
    echo [INFO] Appium is NOT running, starting it now...
    start "Appium Server" "start_appium.bat"
    
    echo   Waiting for Appium to start...
    :: Loop check port, max wait 30s
    set /a retries=0
    :check_port
    timeout /t 2 /nobreak >nul
    netstat -ano | find "4723" | find "LISTENING" >nul
    if "%ERRORLEVEL%"=="0" (
        echo   [OK] Appium started successfully!
        goto :adb_check
    )
    set /a retries+=1
    if !retries! lss 15 (
        echo   Waiting... (!retries!/15)
        goto :check_port
    )
    
    echo.
    echo [ERROR] Appium start timeout!
    echo Please try running "start_appium.bat" manually.
    echo.
    pause
    exit /b 1
)

:adb_check
:: 2. Check ADB Device
echo.
echo [2/3] Checking ADB Device...
adb devices | find "device" | find /v "List of" >nul
if %errorlevel%==0 (
    echo [OK] ADB Device connected
) else (
    echo [ERROR] No ADB device found
    echo   Please ensure:
    echo   1. Phone connected via USB
    echo   2. USB Debugging enabled
    echo   3. Computer authorized
    echo.
    pause
    exit /b 1
)

:: 3. Run Random Browse Program
echo.
echo [3/3] Starting Random Browse Program...
echo ========================================
echo.

python random_browse.py

:: 4. End
echo.
echo ========================================
echo Program Finished
echo ========================================
pause
