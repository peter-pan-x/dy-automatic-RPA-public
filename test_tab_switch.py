#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试动态tab切换功能"""

import sys
import os
import time

# 添加项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src import app_driver
from appium.webdriver.common.appiumby import AppiumBy as By
from search_browse import SearchBrowseSession

def test_tab_switch():
    """测试tab切换功能"""
    driver = None
    try:
        print("=" * 50)
        print("测试动态tab切换功能")
        print("=" * 50)

        # 连接设备
        print("\n1. 连接设备...")
        driver = app_driver.connect()
        if not driver:
            print("❌ 设备连接失败")
            return

        # 创建search_browse会话
        search_session = SearchBrowseSession()
        search_session.driver = driver

        # 执行搜索
        print("\n2. 执行搜索...")
        keyword = "人参茶"
        if not search_session.perform_search(keyword):
            print("❌ 搜索失败")
            return

        # 等待搜索结果加载
        time.sleep(2.0)

        # 测试tab切换
        print("\n3. 测试tab切换...")
        success = search_session.switch_to_video_tab()

        if success:
            print("\n✅ Tab切换成功！")

            # 验证是否真的切换到了视频tab
            print("\n4. 验证视频tab...")
            if search_session._verify_video_tab():
                print("✅ 确认已切换到视频tab")
            else:
                print("⚠️ 切换可能未成功（未检测到视频页面特征）")
        else:
            print("\n❌ Tab切换失败")

        # 保存当前页面的UI结构用于调试
        print("\n5. 保存页面结构...")
        try:
            page_source = driver.page_source
            with open('search_results_page.xml', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print("✅ 页面结构已保存到 search_results_page.xml")
        except Exception as e:
            print(f"⚠️ 保存页面结构失败: {e}")

    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            input("\n按回车键退出...")
            driver.quit()

if __name__ == "__main__":
    test_tab_switch()