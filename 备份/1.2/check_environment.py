#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
抖音RPA环境检查工具
检查所有必需的软件、依赖和配置
"""

import sys
import subprocess
import os
from pathlib import Path

# 设置Windows控制台编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

class Colors:
    """控制台颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text, color=Colors.CYAN):
    """打印标题"""
    print(f"\n{color}{text}{Colors.RESET}")

def print_success(text):
    """打印成功信息"""
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")

def print_error(text):
    """打印错误信息"""
    print(f"{Colors.RED}[ERROR] {text}{Colors.RESET}")

def print_warning(text):
    """打印警告信息"""
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.RESET}")

def print_info(text):
    """打印信息"""
    print(f"{Colors.GRAY}    {text}{Colors.RESET}")

def run_command(command, capture_output=True):
    """运行命令并返回结果"""
    try:
        if capture_output:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0, result.stdout.strip()
        else:
            result = subprocess.run(command, shell=True, timeout=10)
            return result.returncode == 0, ""
    except subprocess.TimeoutExpired:
        return False, "命令超时"
    except Exception as e:
        return False, str(e)

def check_python():
    """检查Python安装"""
    print_header("[1/7] 检查Python安装...")
    success, output = run_command("python --version")
    if success:
        print_success(f"Python已安装: {output}")
        return True
    else:
        print_error("Python未安装或未添加到PATH")
        print_info("解决方案: 访问 https://www.python.org/downloads/ 下载并勾选 'Add Python to PATH'")
        return False

def check_pip():
    """检查pip"""
    print_header("[2/7] 检查pip...")
    success, output = run_command("pip --version")
    if success:
        print_success(f"pip已安装: {output}")
        return True
    else:
        print_error("pip未安装")
        print_info("解决方案: python -m ensurepip --upgrade")
        return False

def check_dependencies():
    """检查项目依赖"""
    print_header("[3/7] 检查项目依赖...")
    
    dependencies = [
        "Appium-Python-Client",
        "requests",
        "colorlog",
        "python-dateutil",
        "psutil"
    ]
    
    all_installed = True
    missing_deps = []
    
    for dep in dependencies:
        success, output = run_command(f"pip show {dep}")
        if success:
            # 提取版本号
            for line in output.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':')[1].strip()
                    print_success(f"{dep} {version}")
                    break
        else:
            print_error(f"{dep} 未安装")
            missing_deps.append(dep)
            all_installed = False
    
    if missing_deps:
        print_info(f"运行以下命令安装缺失的依赖:")
        print_info(f"pip install {' '.join(missing_deps)}")
    
    return all_installed

def check_adb():
    """检查ADB工具"""
    print_header("[4/7] 检查ADB工具...")
    success, output = run_command("adb version")
    if success:
        version_line = output.split('\n')[0] if output else "ADB"
        print_success(f"ADB已安装: {version_line}")
        return True
    else:
        print_error("ADB工具未安装或未添加到PATH")
        print_info("解决方案:")
        print_info("1. 下载 Android Platform Tools:")
        print_info("   https://developer.android.com/studio/releases/platform-tools")
        print_info("2. 解压到 C:\\adb")
        print_info("3. 将 C:\\adb 添加到系统PATH环境变量")
        return False

def check_devices():
    """检查设备连接"""
    print_header("[5/7] 检查设备连接...")
    success, output = run_command("adb devices")
    
    if not success:
        print_warning("跳过设备检查 (ADB未安装)")
        return False
    
    # 解析设备列表
    lines = output.split('\n')[1:]  # 跳过第一行 "List of devices attached"
    devices = [line.strip() for line in lines if line.strip() and '\tdevice' in line]
    
    if devices:
        print_success(f"检测到 {len(devices)} 个已连接的Android设备:")
        for device in devices:
            device_id = device.split('\t')[0]
            print_info(f"- {device_id}")
        return True
    else:
        print_error("未检测到已连接的Android设备")
        print_info("解决方案:")
        print_info("1. 使用USB数据线连接Android手机到电脑")
        print_info("2. 在手机上开启'开发者选项'和'USB调试'")
        print_info("3. 在手机上授权USB调试")
        print_info("4. 运行 'adb devices' 确认连接")
        return False

def check_appium_service():
    """检查Appium服务"""
    print_header("[6/7] 检查Appium服务...")
    
    try:
        import requests
        response = requests.get("http://127.0.0.1:4723/status", timeout=3)
        if response.status_code == 200:
            print_success("Appium服务正在运行 (http://127.0.0.1:4723)")
            return True
    except ImportError:
        print_warning("requests库未安装,无法检查Appium服务")
        return False
    except Exception:
        print_warning("Appium服务未运行")
        print_info("解决方案:")
        print_info("1. 安装Node.js: https://nodejs.org/")
        print_info("2. 安装Appium: npm install -g appium")
        print_info("3. 安装UIAutomator2驱动: appium driver install uiautomator2")
        print_info("4. 启动Appium服务: appium")
        print_info("   或运行项目中的 '启动Appium服务.bat' (如果存在)")
        return False

def check_project_files():
    """检查项目文件"""
    print_header("[7/7] 检查项目文件...")
    
    required_files = [
        "src/main.py",
        "src/app_driver.py",
        "src/core_utils.py",
        "src/interactions.py",
        "config/settings.py",
        "requirements.txt"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"{file_path} 存在")
        else:
            print_error(f"{file_path} 不存在")
            all_exist = False
    
    return all_exist

def main():
    """主函数"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*50}")
    print("抖音RPA环境检查工具 v2.0")
    print("自动检测必需的软件和配置")
    print(f"{'='*50}{Colors.RESET}\n")
    
    error_count = 0
    warning_count = 0
    
    # 执行所有检查
    checks = [
        ("Python", check_python, True),
        ("pip", check_pip, True),
        ("依赖", check_dependencies, True),
        ("ADB", check_adb, True),
        ("设备", check_devices, True),
        ("Appium服务", check_appium_service, False),
        ("项目文件", check_project_files, True)
    ]
    
    for name, check_func, is_critical in checks:
        try:
            result = check_func()
            if not result:
                if is_critical:
                    error_count += 1
                else:
                    warning_count += 1
        except Exception as e:
            print_error(f"{name}检查失败: {str(e)}")
            if is_critical:
                error_count += 1
            else:
                warning_count += 1
    
    # 打印总结
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*50}")
    print("检查完成")
    print(f"{'='*50}{Colors.RESET}\n")
    
    if error_count == 0 and warning_count == 0:
        print_success("所有检查通过! 可以开始使用项目。")
        print(f"\n{Colors.CYAN}下一步:{Colors.RESET}")
        print_info("1. 确保Appium服务正在运行")
        print_info("2. 运行: python src/main.py --auto-accept")
        print_info("   或双击: 快速启动.bat")
        return 0
    elif error_count == 0:
        print_warning(f"检查完成,发现 {warning_count} 个警告")
        print_info("建议修复警告后再运行项目")
        return 0
    else:
        print_error(f"检查失败,发现 {error_count} 个错误和 {warning_count} 个警告")
        print_info("请根据上述提示修复问题后重新运行检查")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}检查已取消{Colors.RESET}")
        sys.exit(1)

