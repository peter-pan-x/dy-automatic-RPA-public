@echo off
chcp 65001 >nul
title 抖音RPA快速启动器
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                           抖音RPA快速启动器                                ║
echo ║                         一键启动，无需记住命令                              ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

:menu
echo 请选择操作：
echo.
echo [1] 检查环境（推荐首次使用）
echo [2] 自动启动并接受协议
echo [3] 只检查环境，不运行
echo [4] 启动Appium服务
echo [5] 查看运行日志
echo [6] 查看统计数据
echo [0] 退出
echo.
set /p choice=请输入选项 (0-6):

if "%choice%"=="1" goto install_and_check
if "%choice%"=="2" goto auto_start
if "%choice%"=="3" goto check_only
if "%choice%"=="4" goto start_appium
if "%choice%"=="5" goto view_logs
if "%choice%"=="6" goto view_stats
if "%choice%"=="0" goto exit
echo 无效选项，请重新选择
goto menu

:install_and_check
echo.
echo [步骤1] 安装依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败，请检查Python和pip配置
    pause
    goto menu
)
echo ✅ 依赖安装完成
echo.

echo [步骤2] 检查环境配置...
python src/main.py --check-only
pause
goto menu

:auto_start
echo.
echo 🚀 正在启动抖音RPA（自动接受协议模式）...
echo.
echo 💡 提示：
echo • 确保手机已连接并开启USB调试
echo • 确保Appium服务正在运行
echo • 按Ctrl+C可以随时停止程序
echo.
pause
python src/main.py --auto-accept
pause
goto menu

:check_only
echo.
echo 🔍 检查环境配置...
python src/main.py --check-only
pause
goto menu

:start_appium
echo.
echo 🚀 启动Appium服务...
echo.
echo 💡 提示：
echo • 这个窗口会持续显示Appium日志
echo • 不要关闭这个窗口
echo • 打开新的命令行窗口运行RPA程序
echo.
appium
pause
goto menu

:view_logs
echo.
echo 📄 查看最新的运行日志...
echo.
if exist "logs\app.log" (
    echo 显示最后50行日志：
    echo ----------------------------------------
    powershell "Get-Content 'logs\app.log' | Select-Object -Last 50"
    echo ----------------------------------------
) else (
    echo ❌ 未找到日志文件，请先运行程序生成日志
)
pause
goto menu

:view_stats
echo.
echo 📊 查看统计数据...
echo.
if exist "logs" (
    dir logs\*.db
    dir logs\*.json
    echo.
    echo 数据文件位置：logs\ 文件夹
    echo • douyin_stats.db - 主数据库
    echo • douyin_stats_export_*.json - 导出的统计数据
    echo.
    echo 您可以使用SQLite查看器打开.db文件查看详细数据
) else (
    echo ❌ 未找到数据文件夹，请先运行程序生成数据
)
pause
goto menu

:exit
echo.
echo 👋 感谢使用抖音RPA项目！
echo.
echo 📚 需要帮助？查看 '详细使用教程.md' 文件
echo.
timeout /t 3 >nul
exit