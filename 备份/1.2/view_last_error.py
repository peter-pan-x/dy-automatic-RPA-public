#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速查看最后一次运行的错误日志
"""

import os
import sys
from datetime import datetime

# 设置Windows控制台编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def print_separator():
    print("=" * 80)

def view_error_log():
    """查看错误日志"""
    error_log_path = "logs/error.log"
    
    print_separator()
    print("抖音RPA - 错误日志查看器")
    print_separator()
    print()
    
    if not os.path.exists(error_log_path):
        print("❌ 未找到错误日志文件: logs/error.log")
        print("✅ 这可能意味着程序还没有遇到错误!")
        return
    
    # 获取文件大小
    file_size = os.path.getsize(error_log_path)
    print(f"📁 文件路径: {error_log_path}")
    print(f"📊 文件大小: {file_size:,} 字节")
    
    # 获取文件修改时间
    mod_time = datetime.fromtimestamp(os.path.getmtime(error_log_path))
    print(f"🕐 最后更新: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print_separator()
    print("最近的错误记录 (最后100行):")
    print_separator()
    
    try:
        with open(error_log_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            
            if not lines:
                print("日志文件为空")
                return
            
            # 显示最后100行
            recent_lines = lines[-100:]
            for line in recent_lines:
                print(line.rstrip())
            
            print()
            print_separator()
            print(f"✅ 共显示 {len(recent_lines)} 行 (总共 {len(lines)} 行)")
            print_separator()
            
    except Exception as e:
        print(f"❌ 读取日志文件时出错: {str(e)}")

def view_today_log():
    """查看今天的运行日志"""
    today = datetime.now().strftime('%Y%m%d')
    log_file = f"logs/douyin_rpa_{today}.log"
    
    print()
    print_separator()
    print(f"今天的运行日志: {log_file}")
    print_separator()
    print()
    
    if not os.path.exists(log_file):
        print(f"❌ 未找到今天的日志文件: {log_file}")
        print("💡 程序可能还没有运行过")
        return
    
    file_size = os.path.getsize(log_file)
    print(f"📁 文件路径: {log_file}")
    print(f"📊 文件大小: {file_size:,} 字节")
    print()
    
    print_separator()
    print("最近的日志 (最后50行):")
    print_separator()
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            
            if not lines:
                print("日志文件为空")
                return
            
            # 显示最后50行
            recent_lines = lines[-50:]
            for line in recent_lines:
                print(line.rstrip())
            
            print()
            print_separator()
            print(f"✅ 共显示 {len(recent_lines)} 行 (总共 {len(lines)} 行)")
            print_separator()
            
    except Exception as e:
        print(f"❌ 读取日志文件时出错: {str(e)}")

def main():
    """主函数"""
    # 检查logs目录
    if not os.path.exists("logs"):
        print("❌ logs目录不存在")
        print("💡 程序可能还没有运行过")
        return
    
    # 查看错误日志
    view_error_log()
    
    # 查看今天的运行日志
    view_today_log()
    
    print()
    print("💡 提示:")
    print("  - 错误日志: logs/error.log")
    print("  - 运行日志: logs/douyin_rpa_YYYYMMDD.log")
    print("  - 可以用文本编辑器打开这些文件查看完整内容")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

