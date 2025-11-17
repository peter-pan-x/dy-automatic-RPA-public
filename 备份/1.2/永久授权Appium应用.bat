@echo off
chcp 65001 >nul
title 永久授权Appium应用
color 0B

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                       永久授权Appium辅助应用                                 ║
echo ║                    避免重复弹出安装/授权请求                                 ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

echo 📱 正在为Appium辅助应用授予所有必要权限...
echo.

echo [1/3] 授予 io.appium.settings 权限...
adb shell pm grant io.appium.settings android.permission.WRITE_SECURE_SETTINGS 2>nul
adb shell pm grant io.appium.settings android.permission.CHANGE_CONFIGURATION 2>nul
adb shell pm grant io.appium.settings android.permission.WRITE_SETTINGS 2>nul
adb shell pm grant io.appium.settings android.permission.ACCESS_FINE_LOCATION 2>nul
echo    ✓ io.appium.settings 权限授予完成

echo.
echo [2/3] 授予 io.appium.uiautomator2.server 权限...
adb shell pm grant io.appium.uiautomator2.server android.permission.WRITE_EXTERNAL_STORAGE 2>nul
adb shell pm grant io.appium.uiautomator2.server android.permission.READ_EXTERNAL_STORAGE 2>nul
echo    ✓ io.appium.uiautomator2.server 权限授予完成

echo.
echo [3/3] 授予 io.appium.uiautomator2.server.test 权限...
adb shell pm grant io.appium.uiautomator2.server.test android.permission.WRITE_EXTERNAL_STORAGE 2>nul
adb shell pm grant io.appium.uiautomator2.server.test android.permission.READ_EXTERNAL_STORAGE 2>nul
echo    ✓ io.appium.uiautomator2.server.test 权限授予完成

echo.
echo ═══════════════════════════════════════════════════════════════════════════════
echo.

echo 🔍 验证应用安装状态...
echo.
adb shell pm list packages | findstr appium
echo.

echo ✅ 权限授予完成！
echo.
echo 💡 提示：
echo    1. 如果仍然弹出安装请求，请在手机上：
echo       - 进入"设置" → "应用" → "应用管理"
echo       - 搜索 "appium"
echo       - 为每个Appium应用开启"安装未知应用"权限
echo.
echo    2. 如果是华为手机，还需要：
echo       - 进入"设置" → "安全" → "更多安全设置"
echo       - 找到"外部来源应用检查"
echo       - 将Appium相关应用添加到白名单
echo.

pause

