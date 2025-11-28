"""
Search Browse 功能验证脚本
验证搜索浏览模块功能
"""

import sys
import os

def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("📦 测试模块导入...")
    print("=" * 60)
    
    try:
        print("导入 search_browse...", end=" ")
        import search_browse
        print("✅")
        
        print("检查 SearchBrowseSession 类...", end=" ")
        assert hasattr(search_browse, 'SearchBrowseSession')
        print("✅")
        
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_keyword_loading():
    """测试关键词加载"""
    print("\n" + "=" * 60)
    print("📚 测试关键词加载...")
    print("=" * 60)
    
    try:
        import search_browse
        
        print("创建 SearchBrowseSession 实例...", end=" ")
        session = search_browse.SearchBrowseSession(runtime_seconds=10)
        print("✅")
        
        print(f"检查关键词数量...", end=" ")
        keyword_count = len(session.keywords)
        assert keyword_count > 0
        print(f"✅ (加载了 {keyword_count} 个关键词)")
        
        print("测试随机选择关键词...", end=" ")
        keyword = session.get_random_keyword()
        assert len(keyword) > 0
        print(f"✅ (示例: {keyword})")
        
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_structure():
    """测试文件结构"""
    print("\n" + "=" * 60)
    print("📁 测试文件结构...")
    print("=" * 60)
    
    files_to_check = [
        ('search_browse.py', True),
        ('random_browse.py', True),
        ('hot_words', True),  # 目录
    ]
    
    all_ok = True
    for filename, should_exist in files_to_check:
        exists = os.path.exists(filename)
        if should_exist:
            status = "✅" if exists else "❌"
            print(f"{status} {filename} {'存在' if exists else '缺失'}")
            if not exists:
                all_ok = False
    
    return all_ok

def main():
    """主测试函数"""
    print("\n🔍 Search Browse 功能验证\n")
    
    results = []
    
    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("关键词加载", test_keyword_loading()))
    results.append(("文件结构", test_file_structure()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 验证结果汇总")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有验证测试通过！")
        print("\n✨ 核心功能:")
        print("   • 关键词加载（hot_words 文件夹）")
        print("   • 搜索功能（点击 → 输入 → 提交）")
        print("   • 视频 tab 切换")
        print("   • 四宫格视频点击（左上角）")
        print("   • 随机浏览集成（复用 RandomBrowseSession）")
        print("\n下一步:")
        print("1. 启动 Appium 服务: 启动Appium服务.bat")
        print("2. 连接设备并启用 USB 调试")
        print("3. 检查设备连接: adb devices")
        print("4. 运行完整测试: python search_browse.py")
        print("\n📝 注意事项:")
        print("   - UI 选择器可能因抖音版本而异")
        print("   - 四宫格布局使用坐标点击（适应性强）")
        print("   - 搜索关键词从 hot_words 文件夹随机选择")
    else:
        print("⚠️ 部分测试失败，请检查上述错误")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
