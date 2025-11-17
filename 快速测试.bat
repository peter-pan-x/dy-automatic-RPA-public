@echo off
chcp 65001 >nul
title 快速测试 - 元素检测
color 0B

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                          🧪 快速测试 - 元素检测                              ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

:: 设置环境变量
set ANDROID_HOME=C:\adb
set ANDROID_SDK_ROOT=C:\adb

:: 快速检查
echo 🔍 快速环境检查...
echo.

:: 检查设备
adb devices | findstr "device" | findstr /v "List" >nul
if %errorlevel% neq 0 (
    echo ❌ 未检测到设备
    echo.
    adb devices
    echo.
    echo 请确保：
    echo   1. 设备已连接
    echo   2. USB调试已开启
    echo   3. 已授权此电脑
    echo.
    pause
    exit /b 1
)
echo ✅ 设备已连接

:: 检查Appium
curl -s http://127.0.0.1:4723/status >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Appium未运行
    echo.
    echo 请先运行: 一键启动环境.bat
    echo 或手动启动: appium
    echo.
    pause
    exit /b 1
)
echo ✅ Appium已运行
echo.

:: 显示提示
echo ════════════════════════════════════════════════════════════════════════════════
echo 📱 重要提示
echo ════════════════════════════════════════════════════════════════════════════════
echo.
echo ⚠️  测试前请确认：
echo    1. 手机屏幕已解锁
echo    2. 抖音应用已打开
echo    3. 当前在【视频播放页面】（重要！）
echo    4. 不要在评论页面、首页或其他页面
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo.

set /p READY="准备好了吗？(y/n): "
if /i not "%READY%"=="y" (
    echo.
    echo 请准备好后重新运行此脚本
    pause
    exit /b 0
)

:: 运行测试
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo 🚀 启动元素检测测试工具
echo ════════════════════════════════════════════════════════════════════════════════
echo.

python test_element_detection.py

echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo ✅ 测试完成
echo ════════════════════════════════════════════════════════════════════════════════
echo.
echo 📊 测试结果已保存到：
echo    - config/element_detection_stats.json (统计数据)
echo    - logs/ (日志文件)
echo.
pause

