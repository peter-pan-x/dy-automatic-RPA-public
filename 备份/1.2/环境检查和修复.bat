@echo off
chcp 65001 >nul
title 环境检查和修复工具
color 0A

echo.
echo ========================================
echo   抖音RPA环境检查和修复工具
echo ========================================
echo.

:menu
echo 请选择操作:
echo.
echo [1] 检查环境 (推荐先运行)
echo [2] 自动修复环境问题
echo [3] 查看详细诊断报告
echo [4] 退出
echo.
set /p choice=请输入选项 (1-4): 

if "%choice%"=="1" goto check
if "%choice%"=="2" goto fix
if "%choice%"=="3" goto report
if "%choice%"=="4" goto end

echo 无效选项，请重新选择
echo.
goto menu

:check
echo.
echo 正在运行环境检查...
echo ----------------------------------------
python check_environment.py
echo.
echo ----------------------------------------
pause
goto menu

:fix
echo.
echo 正在自动修复环境问题...
echo ----------------------------------------
python auto_fix_environment.py
echo.
echo ----------------------------------------
pause
goto menu

:report
echo.
echo 正在打开诊断报告...
if exist "环境问题诊断报告.md" (
    start notepad "环境问题诊断报告.md"
) else (
    echo 未找到诊断报告文件
)
pause
goto menu

:end
echo.
echo 感谢使用！
timeout /t 2 >nul
exit

