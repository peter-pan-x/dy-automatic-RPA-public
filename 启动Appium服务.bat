@echo off
chcp 65001 >nul
title Appium服务启动器
color 0E

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                        Appium服务启动器                                    ║
echo ║                     一键启动Appium Server                                   ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

echo 🚀 正在启动Appium服务...
echo.
echo 💡 重要提示：
echo • 这个窗口会显示Appium的运行日志
echo • 请保持此窗口开启，不要关闭
echo • Appium服务启动后，请使用另一个命令行窗口运行RPA程序
echo • 服务默认运行在 http://127.0.0.1:4723
echo.
echo 📱 启动前请确保：
echo • Android设备已连接并开启USB调试
echo • 没有其他程序占用4723端口
echo.

echo ⏳ 正在启动Appium...
echo ----------------------------------------
appium
echo ----------------------------------------

echo.
echo ❌ Appium服务已停止
echo 💡 如需重新启动，请关闭此窗口后重新运行脚本
echo.
pause