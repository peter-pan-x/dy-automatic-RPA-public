"""
获取当前抖音界面的UI元素信息
用于更新元素选择器
"""

# 设置Windows控制台编码为UTF-8（必须在最开始）
import sys
import io
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

import os
from appium import webdriver
from appium.options.android import UiAutomator2Options
import xml.etree.ElementTree as ET
import json

def get_ui_tree():
    """获取UI树结构"""
    print("🔍 正在连接Appium...")
    
    # 配置
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = "Android Device"
    options.app_package = "com.ss.android.ugc.aweme"
    options.app_activity = ".main.MainActivity"
    options.automation_name = "UiAutomator2"
    options.no_reset = True
    
    # 连接
    driver = webdriver.Remote('http://127.0.0.1:4723', options=options)
    
    print("✅ 已连接到Appium")
    print("📱 当前Activity:", driver.current_activity)
    
    # 获取页面源
    print("\n🔄 正在获取页面结构...")
    page_source = driver.page_source
    
    # 保存完整XML
    with open("ui_dump.xml", "w", encoding="utf-8") as f:
        f.write(page_source)
    print("✅ 已保存完整UI结构到: ui_dump.xml")
    
    # 解析关键元素
    print("\n🔍 搜索关键元素...")
    root = ET.fromstring(page_source)
    
    elements = {
        "like_buttons": [],
        "comment_buttons": [],
        "favorite_buttons": [],
        "follow_buttons": [],
        "search_buttons": [],
        "close_buttons": []
    }
    
    # 搜索点赞相关
    keywords = {
        "like": ["赞", "like", "digg", "zan"],
        "comment": ["评论", "comment", "pinglun"],
        "favorite": ["收藏", "favorite", "star", "shoucang"],
        "follow": ["关注", "follow", "guanzhu"],
        "search": ["搜索", "search", "sousuo"],
        "close": ["关闭", "close", "guanbi", "取消", "cancel"]
    }
    
    for elem in root.iter():
        resource_id = elem.get('resource-id', '')
        text = elem.get('text', '').lower()
        content_desc = elem.get('content-desc', '').lower()
        
        # 检查点赞
        if any(kw in resource_id.lower() or kw in text or kw in content_desc for kw in keywords['like']):
            elements["like_buttons"].append({
                "resource-id": resource_id,
                "text": elem.get('text', ''),
                "content-desc": elem.get('content-desc', ''),
                "class": elem.get('class', ''),
                "clickable": elem.get('clickable', '')
            })
        
        # 检查评论
        if any(kw in resource_id.lower() or kw in text or kw in content_desc for kw in keywords['comment']):
            elements["comment_buttons"].append({
                "resource-id": resource_id,
                "text": elem.get('text', ''),
                "content-desc": elem.get('content-desc', ''),
                "class": elem.get('class', ''),
                "clickable": elem.get('clickable', '')
            })
        
        # 检查收藏
        if any(kw in resource_id.lower() or kw in text or kw in content_desc for kw in keywords['favorite']):
            elements["favorite_buttons"].append({
                "resource-id": resource_id,
                "text": elem.get('text', ''),
                "content-desc": elem.get('content-desc', ''),
                "class": elem.get('class', ''),
                "clickable": elem.get('clickable', '')
            })
        
        # 检查关注
        if any(kw in resource_id.lower() or kw in text or kw in content_desc for kw in keywords['follow']):
            elements["follow_buttons"].append({
                "resource-id": resource_id,
                "text": elem.get('text', ''),
                "content-desc": elem.get('content-desc', ''),
                "class": elem.get('class', ''),
                "clickable": elem.get('clickable', '')
            })
        
        # 检查搜索
        if any(kw in resource_id.lower() or kw in text or kw in content_desc for kw in keywords['search']):
            elements["search_buttons"].append({
                "resource-id": resource_id,
                "text": elem.get('text', ''),
                "content-desc": elem.get('content-desc', ''),
                "class": elem.get('class', ''),
                "clickable": elem.get('clickable', '')
            })
        
        # 检查关闭
        if any(kw in resource_id.lower() or kw in text or kw in content_desc for kw in keywords['close']):
            elements["close_buttons"].append({
                "resource-id": resource_id,
                "text": elem.get('text', ''),
                "content-desc": elem.get('content-desc', ''),
                "class": elem.get('class', ''),
                "clickable": elem.get('clickable', '')
            })
    
    # 保存元素信息
    with open("ui_elements.json", "w", encoding="utf-8") as f:
        json.dump(elements, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 已保存元素信息到: ui_elements.json")
    
    # 打印摘要
    print("\n📊 元素统计:")
    print(f"  点赞按钮: {len(elements['like_buttons'])} 个")
    print(f"  评论按钮: {len(elements['comment_buttons'])} 个")
    print(f"  收藏按钮: {len(elements['favorite_buttons'])} 个")
    print(f"  关注按钮: {len(elements['follow_buttons'])} 个")
    print(f"  搜索按钮: {len(elements['search_buttons'])} 个")
    print(f"  关闭按钮: {len(elements['close_buttons'])} 个")
    
    # 打印关键元素示例
    print("\n🎯 点赞按钮示例:")
    for btn in elements['like_buttons'][:3]:
        if btn['resource-id']:
            print(f"  resource-id: {btn['resource-id']}")
            print(f"  content-desc: {btn['content-desc']}")
            print()
    
    driver.quit()
    print("\n✅ 完成！")

if __name__ == "__main__":
    try:
        # 设置环境变量
        os.environ['ANDROID_HOME'] = 'C:\\adb'
        os.environ['ANDROID_SDK_ROOT'] = 'C:\\adb'
        
        get_ui_tree()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

