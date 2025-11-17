@echo off
chcp 65001 >nul
setlocal EnableExtensions
title 环境检查工具
color 0A
echo.
echo ===============================
echo 环境检查工具
echo 自动检测必需的软件和配置
echo ===============================
echo.
echo [1/6] 检查Python安装...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python未安装或未添加到PATH
    echo 解决方案：访问 https://www.python.org/downloads/ 并勾选 Add Python to PATH
    goto error
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo [OK] Python版本: %python_version%
echo.
echo [2/6] 检查pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip未安装
    echo 解决方案：python -m ensurepip --upgrade
    goto error
)
for /f "tokens=3" %%i in ('pip --version') do set pip_version=%%i
echo [OK] pip版本: %pip_version%
echo.
echo [3/6] 检查项目依赖...
pip show Appium-Python-Client >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] 正在安装 Appium-Python-Client...
    pip install Appium-Python-Client
)
pip show requests >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] 正在安装 requests...
    pip install requests
)
echo [OK] 依赖检查完成
echo.
echo [4/6] 检查ADB工具...
adb version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] ADB工具未安装或未添加到PATH
    echo 解决方案：下载 Android Platform Tools 并将 C:\adb 加入 PATH
    goto error
)
echo [OK] ADB工具已安装
echo.
echo [5/6] 检查设备连接...
set device_found=
for /f "skip=1 tokens=2" %%i in ('adb devices') do (
    if /i "%%i"=="device" set device_found=1
)
if not defined device_found (
    echo [ERROR] 未检测到已连接的Android设备
    echo 解决方案：开启USB调试并在设备上授权
    echo 当前连接的设备：
    adb devices
    goto error
)
echo [OK] Android设备已连接
echo.
echo [6/6] 检查Appium服务...
curl -s http://127.0.0.1:4723/status >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Appium服务未运行
    echo 解决方案：在新窗口运行 appium 或双击 启动Appium服务.bat
) else (
    echo [OK] Appium服务正在运行
)
echo.
if exist "src\main.py" (
    echo [OK] 项目文件检查通过
    echo 下一步：
    echo 1. 确保Appium服务正在运行
    echo 2. 运行: python src\main.py --auto-accept
    echo 或双击: 快速启动.bat
) else (
    echo [ERROR] 未找到项目文件
    echo 请在正确的项目目录中运行此脚本
)
goto end
:error
echo.
echo 环境检查失败
echo 按提示修复后重试
:end
echo.
echo 按任意键退出...
pause >nul