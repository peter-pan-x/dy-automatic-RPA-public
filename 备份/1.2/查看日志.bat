@echo off
chcp 65001 >nul
title 日志查看工具
color 0A

echo.
echo ========================================
echo   抖音RPA日志查看工具
echo ========================================
echo.

:menu
echo 请选择要查看的日志:
echo.
echo [1] 查看今天的运行日志
echo [2] 查看错误日志 (error.log)
echo [3] 查看最新的日志文件
echo [4] 打开logs目录
echo [5] 清空所有日志
echo [6] 返回
echo.
set /p choice=请输入选项 (1-6): 

if "%choice%"=="1" goto today_log
if "%choice%"=="2" goto error_log
if "%choice%"=="3" goto latest_log
if "%choice%"=="4" goto open_dir
if "%choice%"=="5" goto clear_logs
if "%choice%"=="6" goto end

echo 无效选项，请重新选择
echo.
goto menu

:today_log
echo.
echo ========================================
echo 今天的运行日志:
echo ========================================
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set today=%%a%%b%%c
set log_file=logs\douyin_rpa_%today%.log
if exist "%log_file%" (
    type "%log_file%"
) else (
    echo 未找到今天的日志文件: %log_file%
)
echo.
pause
goto menu

:error_log
echo.
echo ========================================
echo 错误日志 (最后50行):
echo ========================================
if exist "logs\error.log" (
    powershell -Command "Get-Content logs\error.log -Tail 50"
) else (
    echo 未找到错误日志文件
)
echo.
pause
goto menu

:latest_log
echo.
echo ========================================
echo 最新日志 (最后30行):
echo ========================================
for /f "delims=" %%i in ('dir /b /o-d logs\douyin_rpa_*.log 2^>nul') do (
    set latest=%%i
    goto :show_latest
)
:show_latest
if defined latest (
    echo 文件: %latest%
    echo ----------------------------------------
    powershell -Command "Get-Content logs\%latest% -Tail 30"
) else (
    echo 未找到日志文件
)
echo.
pause
goto menu

:open_dir
echo.
echo 打开logs目录...
if exist "logs\" (
    start explorer "logs\"
) else (
    echo logs目录不存在
    mkdir logs
    start explorer "logs\"
)
pause
goto menu

:clear_logs
echo.
echo ========================================
echo 警告: 即将清空所有日志文件!
echo ========================================
set /p confirm=确认清空? (yes/no): 
if /i "%confirm%"=="yes" (
    del /q logs\*.log 2>nul
    echo.
    echo ✓ 日志已清空
) else (
    echo.
    echo 取消清空操作
)
pause
goto menu

:end
echo.
echo 退出日志查看工具
timeout /t 1 >nul
exit

