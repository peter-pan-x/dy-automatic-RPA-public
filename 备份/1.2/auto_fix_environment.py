#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动修复环境问题
尝试自动安装缺失的依赖
"""

import sys
import subprocess
import os

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
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")

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
    print(f"    {text}")

def run_command(command, show_output=False):
    """运行命令并返回结果"""
    try:
        if show_output:
            result = subprocess.run(command, shell=True, check=True)
            return result.returncode == 0
        else:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            return True
    except subprocess.CalledProcessError as e:
        return False
    except Exception as e:
        print_error(f"执行命令时出错: {str(e)}")
        return False

def install_python_dependencies():
    """安装Python依赖"""
    print_header("正在安装Python依赖...")
    
    # 检查requirements.txt是否存在
    if not os.path.exists('requirements.txt'):
        print_error("未找到 requirements.txt 文件")
        return False
    
    print_info("使用清华大学镜像源加速安装...")
    command = 'pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple'
    
    print_info(f"执行: {command}")
    print_info("这可能需要几分钟时间，请耐心等待...")
    print()
    
    success = run_command(command, show_output=True)
    
    if success:
        print_success("Python依赖安装成功")
        return True
    else:
        print_error("Python依赖安装失败")
        print_info("请尝试手动执行: pip install -r requirements.txt")
        return False

def check_adb():
    """检查ADB是否安装"""
    print_header("检查ADB工具...")
    result = subprocess.run(
        "adb version",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print_success("ADB工具已安装")
        return True
    else:
        print_warning("ADB工具未安装")
        print_info("请按照以下步骤手动安装:")
        print_info("1. 访问: https://developer.android.com/studio/releases/platform-tools")
        print_info("2. 下载 Windows 版本的 Platform Tools")
        print_info("3. 解压到 C:\\adb")
        print_info("4. 将 C:\\adb\\platform-tools 添加到系统PATH环境变量")
        print_info("5. 重启命令行窗口")
        return False

def check_nodejs():
    """检查Node.js是否安装"""
    print_header("检查Node.js...")
    result = subprocess.run(
        "node --version",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        version = result.stdout.strip()
        print_success(f"Node.js已安装: {version}")
        return True
    else:
        print_warning("Node.js未安装")
        print_info("Appium需要Node.js运行")
        print_info("请访问 https://nodejs.org/ 下载并安装LTS版本")
        return False

def check_appium():
    """检查Appium是否安装"""
    print_header("检查Appium...")
    result = subprocess.run(
        "appium --version",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        version = result.stdout.strip()
        print_success(f"Appium已安装: {version}")
        return True
    else:
        print_warning("Appium未安装")
        return False

def install_appium():
    """尝试安装Appium"""
    print_header("正在安装Appium...")
    
    # 检查Node.js
    if not check_nodejs():
        print_error("无法安装Appium: Node.js未安装")
        return False
    
    print_info("安装Appium全局包...")
    if not run_command("npm install -g appium", show_output=True):
        print_error("Appium安装失败")
        print_info("请尝试手动执行: npm install -g appium")
        return False
    
    print_success("Appium安装成功")
    
    print_info("安装UIAutomator2驱动...")
    if not run_command("appium driver install uiautomator2", show_output=True):
        print_warning("UIAutomator2驱动安装失败")
        print_info("请尝试手动执行: appium driver install uiautomator2")
        return False
    
    print_success("UIAutomator2驱动安装成功")
    return True

def main():
    """主函数"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}")
    print("抖音RPA环境自动修复工具")
    print("自动安装缺失的依赖和工具")
    print(f"{'='*60}{Colors.RESET}\n")
    
    fixed_count = 0
    failed_count = 0
    manual_count = 0
    
    # 1. 安装Python依赖
    if install_python_dependencies():
        fixed_count += 1
    else:
        failed_count += 1
    
    # 2. 检查ADB
    if not check_adb():
        manual_count += 1
        print_info("ADB需要手动安装")
    
    # 3. 检查和安装Appium
    if not check_appium():
        if check_nodejs():
            print_info("尝试自动安装Appium...")
            if install_appium():
                fixed_count += 1
            else:
                failed_count += 1
        else:
            manual_count += 1
            print_info("Appium需要先安装Node.js")
    else:
        print_success("Appium已安装，无需修复")
    
    # 打印总结
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}")
    print("修复完成")
    print(f"{'='*60}{Colors.RESET}\n")
    
    print(f"{Colors.GREEN}自动修复: {fixed_count} 项{Colors.RESET}")
    print(f"{Colors.RED}修复失败: {failed_count} 项{Colors.RESET}")
    print(f"{Colors.YELLOW}需要手动处理: {manual_count} 项{Colors.RESET}")
    
    if manual_count > 0:
        print(f"\n{Colors.YELLOW}请参考 '环境问题诊断报告.md' 完成手动安装步骤{Colors.RESET}")
    
    if failed_count == 0 and manual_count == 0:
        print(f"\n{Colors.GREEN}所有问题已修复!{Colors.RESET}")
        print_info("运行 'python check_environment.py' 进行最终检查")
    else:
        print(f"\n{Colors.YELLOW}部分问题需要手动处理{Colors.RESET}")
        print_info("完成手动安装后，运行 'python check_environment.py' 进行检查")
    
    return 0 if (failed_count == 0 and manual_count == 0) else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}修复已取消{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"发生未知错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

