"""
检查华为手机的安全限制设置
"""

# 设置Windows控制台编码为UTF-8
import sys
import io
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

import subprocess

def run_adb_command(command):
    """运行ADB命令"""
    try:
        result = subprocess.run(
            f"adb shell {command}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip()
    except Exception as e:
        return f"错误: {e}"

def main():
    print("="*70)
    print(" "*20 + "华为手机安全限制检查")
    print("="*70)
    print()
    
    print("📱 正在检查手机设置...")
    print()
    
    # 检查1：Appium应用是否安装
    print("[1/5] 检查Appium应用安装状态")
    print("-"*70)
    apps = run_adb_command("pm list packages | grep appium")
    if apps:
        for app in apps.split('\n'):
            if app.strip():
                print(f"  ✅ {app.replace('package:', '')}")
    else:
        print("  ❌ 未找到Appium应用")
    print()
    
    # 检查2：应用权限状态
    print("[2/5] 检查Appium Settings权限")
    print("-"*70)
    perms = run_adb_command("dumpsys package io.appium.settings | grep 'granted=true'")
    if perms:
        count = perms.count('granted=true')
        print(f"  ✅ 已授予 {count} 个权限")
    else:
        print("  ⚠️  权限信息不完整")
    print()
    
    # 检查3：检查是否有华为特殊限制
    print("[3/5] 检查华为安全特性")
    print("-"*70)
    
    # 检查纯净模式
    pure_mode = run_adb_command("settings get secure pure_mode_state")
    if "1" in pure_mode:
        print("  ❌ 纯净模式：已开启（建议关闭！）")
        print("     操作：设置 → 系统和更新 → 纯净模式 → 退出")
    elif "0" in pure_mode:
        print("  ✅ 纯净模式：已关闭")
    else:
        print("  ⚠️  纯净模式：无法检测")
    
    # 检查开发者选项
    dev_options = run_adb_command("settings get global development_settings_enabled")
    if "1" in dev_options:
        print("  ✅ 开发者选项：已开启")
    else:
        print("  ❌ 开发者选项：未开启")
    print()
    
    # 检查4：USB调试状态
    print("[4/5] 检查USB调试设置")
    print("-"*70)
    adb_enabled = run_adb_command("settings get global adb_enabled")
    if "1" in adb_enabled:
        print("  ✅ USB调试：已开启")
    else:
        print("  ❌ USB调试：未开启")
    
    # 检查ADB安装监控
    install_monitor = run_adb_command("settings get global verifier_verify_adb_installs")
    if "0" in install_monitor:
        print("  ✅ ADB安装监控：已关闭")
    elif "1" in install_monitor:
        print("  ❌ ADB安装监控：已开启（建议关闭！）")
        print("     操作：开发者选项 → 监控ADB安装应用 → 关闭")
    else:
        print("  ⚠️  ADB安装监控：无法检测")
    print()
    
    # 检查5：设备信息
    print("[5/5] 设备基本信息")
    print("-"*70)
    brand = run_adb_command("getprop ro.product.brand")
    model = run_adb_command("getprop ro.product.model")
    android_ver = run_adb_command("getprop ro.build.version.release")
    
    print(f"  品牌: {brand}")
    print(f"  型号: {model}")
    print(f"  Android版本: {android_ver}")
    print()
    
    # 总结建议
    print("="*70)
    print(" "*25 + "建议操作")
    print("="*70)
    print()
    print("🔧 如果仍然有安装弹窗，请按以下顺序操作：")
    print()
    print("1. 【关键】退出纯净模式")
    print("   设置 → 系统和更新 → 纯净模式 → 退出纯净模式")
    print()
    print("2. 关闭ADB安装监控")
    print("   设置 → 开发者选项 → 监控ADB安装应用 → 选择'关闭'")
    print()
    print("3. 关闭应用安全检查")
    print("   华为应用市场 → 我的 → 设置 → 关闭'安装时病毒扫描'")
    print()
    print("4. Appium Settings安装时：")
    print("   - 关闭'增强防护'开关")
    print("   - 勾选'不再提示'")
    print("   - 点击'仍然安装'")
    print()
    print("5. 重启手机使所有设置生效")
    print()
    print("="*70)

if __name__ == "__main__":
    main()

