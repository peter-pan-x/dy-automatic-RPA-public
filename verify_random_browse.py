"""
Random Browse 功能验证脚本（新版）
验证重构后的模块功能
"""

import sys
import os

def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("📦 测试模块导入...")
    print("=" * 60)
    
    try:
        print("导入 random_browse...", end=" ")
        import random_browse
        print("✅")
        
        print("检查 RandomBrowseSession 类...", end=" ")
        assert hasattr(random_browse, 'RandomBrowseSession')
        print("✅")
        
        print("检查核心方法...", end=" ")
        session = random_browse.RandomBrowseSession
        required_methods = [
            'check_environment',
            'force_start_douyin',
            'ensure_in_recommendation_tab',
            'detect_video_type',
            'skip_with_probability',
            'perform_comment_with_scroll',
            'perform_video_interactions',
            'swipe_to_next_video',
            'run'
        ]
        for method in required_methods:
            assert hasattr(session, method), f"缺少方法: {method}"
        print("✅")
        
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_session_creation():
    """测试会话对象创建"""
    print("\n" + "=" * 60)
    print("🔨 测试会话对象创建...")
    print("=" * 60)
    
    try:
        import random_browse
        
        print("创建 RandomBrowseSession 实例...", end=" ")
        session = random_browse.RandomBrowseSession(runtime_seconds=10)
        print("✅")
        
        print("检查统计数据结构...", end=" ")
        required_stats = [
            'videos_browsed', 'videos_skipped', 'normal_videos', 'live_videos',
            'like_attempts', 'like_success', 'comment_attempts', 'comment_success',
            'comment_scrolls', 'favorite_attempts', 'favorite_success', 'comments_posted'
        ]
        for stat in required_stats:
            assert stat in session.stats, f"缺少统计项: {stat}"
        print("✅")
        
        print("检查评论库加载...", end=" ")
        assert len(session.comments) > 0
        print(f"✅ (加载了 {len(session.comments)} 条评论)")
        
        print("检查运行时间设置...", end=" ")
        assert session.runtime_seconds == 10
        print("✅")
        
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_probability_logic():
    """测试概率逻辑"""
    print("\n" + "=" * 60)
    print("🎲 测试概率逻辑...")
    print("=" * 60)
    
    try:
        import random_browse
        session = random_browse.RandomBrowseSession(runtime_seconds=10)
        
        print("测试 22% 跳过概率...", end=" ")
        # 运行多次测试概率分布
        skip_count = sum(1 for _ in range(1000) if session.skip_with_probability())
        skip_rate = skip_count / 1000
        # 允许一定误差范围
        assert 0.15 < skip_rate < 0.30, f"跳过概率异常: {skip_rate:.2%}"
        print(f"✅ (实际: {skip_rate:.1%})")
        
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_new_features():
    """测试新功能特性"""
    print("\n" + "=" * 60)
    print("✨ 测试新功能特性...")
    print("=" * 60)
    
    try:
        import random_browse
        session = random_browse.RandomBrowseSession()
        
        print("检查评论区滑动方法...", end=" ")
        assert hasattr(session, 'perform_comment_with_scroll')
        print("✅")
        
        print("检查视频类型检测...", end=" ")
        assert hasattr(session, 'detect_video_type')
        print("✅")
        
        print("检查环境检查功能...", end=" ")
        assert hasattr(session, 'check_environment')
        print("✅")
        
        print("检查强制启动功能...", end=" ")
        assert hasattr(session, 'force_start_douyin')
        print("✅")
        
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("\n🔍 Random Browse 功能验证（新版）\n")
    
    results = []
    
    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("会话创建", test_session_creation()))
    results.append(("概率逻辑", test_probability_logic()))
    results.append(("新功能特性", test_new_features()))
    
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
        print("\n✨ 新功能特性:")
        print("   • 22% 概率跳过（模拟不感兴趣）")
        print("   • 66% 点赞概率（独立）")
        print("   • 66% 评论概率（独立，含评论区滑动3-6次）")
        print("   • 33% 收藏概率")
        print("   • 两阶段浏览（5-22秒 + 5-12秒）")
        print("   • 环境自动检查（Appium + ADB）")
        print("   • 视频类型分类（常规 vs 直播）")
        print("\n下一步:")
        print("1. 启动 Appium 服务: 启动Appium服务.bat")
        print("2. 连接设备并启用 USB 调试")
        print("3. 检查设备连接: adb devices")
        print("4. 运行完整测试: python random_browse.py")
    else:
        print("⚠️ 部分测试失败，请检查上述错误")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
