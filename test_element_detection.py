"""
元素检测测试工具
可以独立测试和调试元素检测功能
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
from appium import webdriver
from appium.options.android import UiAutomator2Options
from config.selectors import ElementSelectors
from src.element_detector import get_element_detector


def test_element_detection():
    """测试元素检测功能"""
    
    print("=" * 80)
    print("🧪 元素检测测试工具")
    print("=" * 80)
    
    # 设置环境变量
    os.environ['ANDROID_HOME'] = 'C:\\adb'
    os.environ['ANDROID_SDK_ROOT'] = 'C:\\adb'
    
    print("\n🔍 正在连接Appium...")
    
    # 配置
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = "Android Device"
    options.app_package = "com.ss.android.ugc.aweme"
    options.app_activity = ".main.MainActivity"
    options.automation_name = "UiAutomator2"
    options.no_reset = True
    
    try:
        # 连接
        driver = webdriver.Remote('http://127.0.0.1:4723', options=options)
        print("✅ 已连接到Appium")
        print(f"📱 当前Activity: {driver.current_activity}")
        
        # 获取元素检测器
        detector = get_element_detector(driver)
        
        # 测试菜单
        while True:
            print("\n" + "=" * 80)
            print("请选择要测试的元素：")
            print("=" * 80)
            print("[1] 点赞按钮")
            print("[2] 评论按钮")
            print("[3] 收藏按钮")
            print("[4] 关注按钮")
            print("[5] 评论输入框")
            print("[6] 测试所有元素")
            print("[7] 查看统计信息")
            print("[8] 导出统计数据")
            print("[9] 清空缓存")
            print("[0] 退出")
            print("=" * 80)
            
            choice = input("\n请输入选项 (0-9): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                test_button(detector, 'like_button', '点赞按钮', ElementSelectors.LIKE_BUTTON)
            elif choice == '2':
                test_button(detector, 'comment_button', '评论按钮', ElementSelectors.COMMENT_BUTTON)
            elif choice == '3':
                test_button(detector, 'favorite_button', '收藏按钮', ElementSelectors.FAVORITE_BUTTON)
            elif choice == '4':
                test_button(detector, 'follow_button', '关注按钮', ElementSelectors.FOLLOW_BUTTON)
            elif choice == '5':
                test_button(detector, 'comment_input', '评论输入框', ElementSelectors.COMMENT_INPUT)
            elif choice == '6':
                test_all_elements(detector)
            elif choice == '7':
                show_stats(detector)
            elif choice == '8':
                export_stats(detector)
            elif choice == '9':
                detector.clear_cache()
                print("✅ 缓存已清空")
            else:
                print("❌ 无效选项")
        
        # 关闭连接
        driver.quit()
        print("\n✅ 测试完成，已断开连接")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def test_button(detector, button_type: str, button_name: str, selectors: list):
    """测试单个按钮"""
    print(f"\n{'=' * 80}")
    print(f"🧪 测试 {button_name}")
    print("=" * 80)
    
    element = detector.find_element_smart(button_type, selectors, timeout=3)
    
    if element:
        print(f"\n✅ 成功找到 {button_name}！")
        
        # 显示元素信息
        try:
            print(f"\n📊 元素信息:")
            print(f"  类名: {element.tag_name}")
            
            try:
                text = element.text
                if text:
                    print(f"  文本: {text}")
            except:
                pass
            
            try:
                content_desc = element.get_attribute("content-desc")
                if content_desc:
                    print(f"  描述: {content_desc}")
            except:
                pass
            
            try:
                location = element.location
                size = element.size
                print(f"  位置: ({location['x']}, {location['y']})")
                print(f"  大小: {size['width']}x{size['height']}")
            except:
                pass
        except Exception as e:
            print(f"  获取元素信息失败: {e}")
        
        # 询问是否点击
        if input("\n是否点击该元素？(y/n): ").lower() == 'y':
            if detector.click_element(element):
                print("✅ 点击成功")
            else:
                print("❌ 点击失败")
    else:
        print(f"\n❌ 未找到 {button_name}")


def test_all_elements(detector):
    """测试所有元素"""
    print(f"\n{'=' * 80}")
    print("🧪 测试所有元素")
    print("=" * 80)
    
    elements = [
        ('like_button', '点赞按钮', ElementSelectors.LIKE_BUTTON),
        ('comment_button', '评论按钮', ElementSelectors.COMMENT_BUTTON),
        ('favorite_button', '收藏按钮', ElementSelectors.FAVORITE_BUTTON),
        ('follow_button', '关注按钮', ElementSelectors.FOLLOW_BUTTON),
    ]
    
    results = {}
    
    for button_type, button_name, selectors in elements:
        print(f"\n测试 {button_name}...")
        element = detector.find_element_smart(button_type, selectors, timeout=2, use_cache=False)
        results[button_name] = element is not None
    
    # 显示结果
    print(f"\n{'=' * 80}")
    print("📊 测试结果汇总")
    print("=" * 80)
    
    for button_name, found in results.items():
        status = "✅ 成功" if found else "❌ 失败"
        print(f"{button_name}: {status}")
    
    success_count = sum(1 for found in results.values() if found)
    total_count = len(results)
    success_rate = success_count / total_count * 100
    
    print(f"\n总计: {success_count}/{total_count} ({success_rate:.1f}%)")


def show_stats(detector):
    """显示统计信息"""
    print(f"\n{'=' * 80}")
    print("📊 元素检测统计信息")
    print("=" * 80)
    
    summary = detector.get_stats_summary()
    
    if not summary:
        print("\n暂无统计数据")
        return
    
    for button_type, stats in summary.items():
        print(f"\n【{button_type}】")
        print(f"  总尝试次数: {stats['total_attempts']}")
        print(f"  成功次数: {stats['success_count']}")
        print(f"  成功率: {stats['success_rate']:.1f}%")
        
        if stats.get('best_selector'):
            print(f"  最佳选择器: {stats['best_selector'][:60]}...")


def export_stats(detector):
    """导出统计数据"""
    print(f"\n{'=' * 80}")
    print("💾 导出统计数据")
    print("=" * 80)
    
    try:
        output_file = detector.export_stats()
        print(f"\n✅ 统计数据已导出到: {output_file}")
    except Exception as e:
        print(f"\n❌ 导出失败: {e}")


if __name__ == "__main__":
    try:
        test_element_detection()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

