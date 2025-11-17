@echo off
chcp 65001 >nul
title 抖音RPA - 一键启动环境
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                      抖音RPA - 一键启动环境脚本                              ║
echo ║                    启动所有必要环境（不包括主程序）                           ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

:: 设置环境变量
echo [1/4] 设置环境变量...
set ANDROID_HOME=C:\adb
set ANDROID_SDK_ROOT=C:\adb
set PATH=%PATH%;C:\adb\platform-tools
echo ✅ 环境变量已设置
echo     ANDROID_HOME=%ANDROID_HOME%
echo     ANDROID_SDK_ROOT=%ANDROID_SDK_ROOT%
echo.

:: 检查ADB是否可用
echo [2/4] 检查ADB工具...
where adb >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ADB工具未找到，请确保已安装并配置PATH
    echo    下载地址: https://developer.android.com/tools/releases/platform-tools
    pause
    exit /b 1
)
echo ✅ ADB工具已就绪
adb version | findstr "Android"
echo.

:: 检查设备连接
echo [3/4] 检查Android设备连接...
adb devices -l
echo.
echo 💡 请确认：
echo    - 设备列表中至少有一个设备
echo    - 设备状态显示为 "device"（而非 unauthorized）
echo    - 如果是 unauthorized，请在手机上授权USB调试
echo.
set /p CONTINUE="设备连接正常吗？(y/n): "
if /i not "%CONTINUE%"=="y" (
    echo.
    echo ⚠️  请按以下步骤操作：
    echo    1. 确保使用数据线（非充电线）
    echo    2. 手机开启USB调试
    echo    3. 在手机上授权USB调试（勾选"始终允许"）
    echo    4. 重新运行此脚本
    echo.
    pause
    exit /b 1
)
echo ✅ 设备连接确认完成
echo.

:: 启动Appium服务器（在新窗口中）
echo [4/4] 启动Appium Server...
echo.
echo 💡 正在新窗口中启动Appium Server...
echo    - 窗口标题: Appium Server
echo    - 请保持该窗口打开
echo    - 等待看到 "Appium REST http interface listener started..."
echo.

:: 检查Appium是否已安装
where appium >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Appium未安装！
    echo.
    echo 请安装Appium：
    echo    1. 安装Node.js: https://nodejs.org/
    echo    2. 安装Appium: npm install -g appium
    echo    3. 安装驱动: appium driver install uiautomator2
    echo.
    pause
    exit /b 1
)

:: 在新窗口启动Appium
start "Appium Server" cmd /k "echo 🚀 Appium Server 正在启动... && echo. && appium"

echo ✅ Appium Server已在新窗口启动
echo.
echo 等待5秒，让Appium完全启动...
timeout /t 5 /nobreak >nul

:: 检查Appium是否成功启动
echo.
echo 🔍 验证Appium Server状态...
curl -s http://127.0.0.1:4723/status >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Appium Server已成功启动并响应
) else (
    echo ⚠️  无法连接到Appium Server（可能还在启动中）
    echo    请查看Appium窗口，确认是否有错误
)
echo.

:: 显示完成信息
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                            🎉 环境启动完成                                   ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.
echo ✅ 已启动的服务：
echo    [√] 环境变量已设置
echo    [√] ADB工具已就绪
echo    [√] 设备连接已确认
echo    [√] Appium Server已启动（独立窗口）
echo.
echo 📋 下一步操作：
echo.
echo    【选项1】测试元素检测功能（推荐）
echo       python test_element_detection.py
echo.
echo    【选项2】运行主程序
echo       python src/main.py --auto-accept
echo.
echo    【选项3】提取UI元素（在视频页面）
echo       python get_ui_elements.py
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo.

:menu
echo 请选择操作：
echo.
echo [1] 运行元素检测测试工具 ⭐推荐
echo [2] 运行主程序
echo [3] 提取UI元素
echo [4] 检查环境状态
echo [5] 重启Appium Server
echo [0] 退出
echo.
set /p CHOICE="请输入选项 (0-5): "

if "%CHOICE%"=="1" goto test_detection
if "%CHOICE%"=="2" goto run_main
if "%CHOICE%"=="3" goto extract_ui
if "%CHOICE%"=="4" goto check_status
if "%CHOICE%"=="5" goto restart_appium
if "%CHOICE%"=="0" goto end
echo ❌ 无效选项
goto menu

:test_detection
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo 🧪 启动元素检测测试工具
echo ════════════════════════════════════════════════════════════════════════════════
echo.
echo 💡 提示：
echo    - 确保手机在抖音视频播放页面
echo    - 不要在评论页面
echo    - 测试工具会依次测试各个按钮
echo.
pause
python test_element_detection.py
echo.
echo 测试完成！
pause
goto menu

:run_main
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo 🚀 启动主程序
echo ════════════════════════════════════════════════════════════════════════════════
echo.
echo 💡 提示：
echo    - 程序会自动接受协议
echo    - 按Ctrl+C可随时停止
echo    - 所有日志保存在logs/目录
echo.
pause
python src/main.py --auto-accept
echo.
echo 程序已退出
pause
goto menu

:extract_ui
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo 🔍 提取UI元素
echo ════════════════════════════════════════════════════════════════════════════════
echo.
echo ⚠️  重要提示：
echo    1. 确保手机在抖音【视频播放页面】
echo    2. 不要在评论页面、首页等其他页面
echo    3. 提取的元素会保存到当前目录
echo.
pause
python get_ui_elements.py
echo.
echo UI元素提取完成！
echo 请查看生成的文件：
echo    - ui_dump.xml (完整UI结构)
echo    - ui_elements.json (提取的元素)
echo.
pause
goto menu

:check_status
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo 🔍 检查环境状态
echo ════════════════════════════════════════════════════════════════════════════════
echo.

echo [1/3] ADB设备连接状态：
adb devices
echo.

echo [2/3] Appium Server状态：
curl -s http://127.0.0.1:4723/status >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Appium Server 正在运行
) else (
    echo ❌ Appium Server 未响应
)
echo.

echo [3/3] Python环境：
python --version
echo.

pause
goto menu

:restart_appium
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo 🔄 重启Appium Server
echo ════════════════════════════════════════════════════════════════════════════════
echo.
echo 正在关闭旧的Appium进程...
taskkill /F /FI "WindowTitle eq Appium Server*" >nul 2>&1
timeout /t 2 /nobreak >nul
echo ✅ 旧进程已关闭
echo.
echo 正在启动新的Appium Server...
start "Appium Server" cmd /k "echo 🚀 Appium Server 正在启动... && echo. && appium"
timeout /t 5 /nobreak >nul
echo ✅ Appium Server已重启
echo.
pause
goto menu

:end
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo 👋 退出程序
echo ════════════════════════════════════════════════════════════════════════════════
echo.
echo ⚠️  提醒：
echo    - Appium Server仍在独立窗口运行
echo    - 如需关闭，请手动关闭"Appium Server"窗口
echo    - 或重新运行此脚本选择[5]重启
echo.
echo 感谢使用！
timeout /t 3 >nul
exit /b 0

