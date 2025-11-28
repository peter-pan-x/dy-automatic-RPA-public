"""
抖音RPA主程序
整合随机浏览和搜索浏览模块，模拟真实人类行为

流程：
1. 检查/启动依赖（Appium、ADB）
2. 连接设备 + 强制启动抖音
3. 阶段A：随机浏览（预热，模拟先随便刷一会）
4. 随机间隔等待（模拟人类切换意图）
5. 阶段B：搜索浏览 + 评论回复
6. 统计汇总 + 清理退出
"""

import sys
import os
import time
import random
import signal
import traceback
import yaml
from datetime import datetime

# 添加项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 导入核心模块
from src import app_driver, interactions, core_utils
from src.logger import setup_logger

# 导入浏览模块
from random_browse import RandomBrowseSession
from search_browse import SearchBrowseSession

# 配置路径
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.yaml')

# 初始化日志
logger = setup_logger("main", log_dir="logs")


class MainProgram:
    """主程序管理器"""
    
    def __init__(self):
        """初始化主程序"""
        self.driver = None
        self.start_time = None
        
        # 加载配置
        self.config = self._load_config()
        main_cfg = self.config.get('main', {})
        
        # 预热浏览时长
        warmup_min = main_cfg.get('warmup_browse_min', 60)
        warmup_max = main_cfg.get('warmup_browse_max', 180)
        self.warmup_seconds = random.randint(warmup_min, warmup_max)
        
        # 模块间隔
        gap_min = main_cfg.get('module_gap_min', 10)
        gap_max = main_cfg.get('module_gap_max', 60)
        self.module_gap = random.randint(gap_min, gap_max)
        
        # 统计
        self.stats = {
            'warmup_videos': 0,
            'search_videos': 0,
            'total_replies': 0,
            'total_likes': 0,
        }
        
        logger.info("=" * 60)
        logger.info("🚀 抖音RPA主程序 初始化完成")
        logger.info(f"⏱️  预热浏览: {self.warmup_seconds}秒 ({self.warmup_seconds//60}分钟)")
        logger.info(f"⏸️  模块间隔: {self.module_gap}秒")
        logger.info("=" * 60)
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"⚠️ 配置加载失败，使用默认值: {e}")
            return {}
    
    def run(self) -> bool:
        """
        运行主程序
        
        Returns:
            bool: 运行是否成功
        """
        self.start_time = datetime.now()
        
        try:
            # ========== 阶段0：环境检查 ==========
            logger.info("\n" + "🔧" * 20)
            logger.info("阶段0：环境检查")
            logger.info("🔧" * 20)
            
            # 创建临时session用于环境检查
            temp_session = RandomBrowseSession(runtime_seconds=self.warmup_seconds)
            if not temp_session.check_environment():
                logger.error("❌ 环境检查失败，请先启动Appium和连接设备")
                return False
            
            # ========== 阶段1：连接设备 + 启动抖音 ==========
            logger.info("\n" + "📱" * 20)
            logger.info("阶段1：连接设备 + 启动抖音")
            logger.info("📱" * 20)
            
            self.driver = app_driver.connect(max_retries=3)
            if not self.driver:
                logger.error("❌ 设备连接失败")
                return False
            
            logger.info("✅ 设备连接成功")
            
            # 初始化工具模块
            interactions.init_interactions(self.driver)
            core_utils.init_utils(self.driver)
            
            # 共享driver给temp_session
            temp_session.driver = self.driver
            
            # 强制启动抖音
            if not temp_session.force_start_douyin():
                logger.error("❌ 抖音启动失败")
                return False
            
            time.sleep(2.0)
            
            # ========== 阶段2：随机浏览（预热） ==========
            logger.info("\n" + "🎲" * 20)
            logger.info("阶段2：随机浏览（预热）")
            logger.info(f"⏱️  计划浏览: {self.warmup_seconds}秒")
            logger.info("🎲" * 20)
            
            # 确保进入视频模式
            if not temp_session.ensure_in_recommendation_tab_and_click_video():
                logger.warning("⚠️ 无法进入视频模式，尝试继续...")
            
            # 执行随机浏览
            temp_session.run_browse_loop(runtime_seconds=self.warmup_seconds)
            
            # 记录统计
            self.stats['warmup_videos'] = temp_session.stats.get('videos_browsed', 0)
            self.stats['total_likes'] += temp_session.stats.get('like_success', 0)
            
            logger.info(f"\n✅ 预热阶段完成，浏览了 {self.stats['warmup_videos']} 个视频")
            
            # ========== 阶段3：模块间隔 ==========
            logger.info("\n" + "⏸️" * 20)
            logger.info(f"阶段3：模块间隔 ({self.module_gap}秒)")
            logger.info("⏸️" * 20)
            
            logger.info(f"   😴 模拟人类切换意图，等待 {self.module_gap} 秒...")
            time.sleep(self.module_gap)
            
            # ========== 阶段4：搜索浏览 + 评论回复 ==========
            logger.info("\n" + "🔍" * 20)
            logger.info("阶段4：搜索浏览 + 评论回复")
            logger.info("🔍" * 20)
            
            # 创建搜索浏览会话（复用driver）
            search_session = SearchBrowseSession()
            search_session.driver = self.driver
            search_session.browse_session.driver = self.driver
            
            # 初始化工具模块（确保正确）
            interactions.init_interactions(self.driver)
            core_utils.init_utils(self.driver)
            
            # 选择随机关键词并执行搜索
            keyword = search_session.get_random_keyword()
            logger.info(f"🎲 选择的关键词: {keyword}")
            
            if not search_session.perform_search(keyword):
                logger.error("❌ 搜索失败")
                return False
            
            # 切换到视频tab
            if not search_session.switch_to_video_tab():
                logger.error("❌ 无法切换到视频 tab")
                return False
            
            # 点击视频进入全屏
            if not search_session.click_grid_video():
                logger.error("❌ 无法点击视频")
                return False
            
            # 验证全屏模式
            time.sleep(2.0)
            max_attempts = 3
            for attempt in range(max_attempts):
                if search_session._is_in_fullscreen_mode():
                    logger.info("✅ 确认已进入全屏视频播放模式")
                    break
                else:
                    if attempt < max_attempts - 1:
                        search_session.click_grid_video()
                        time.sleep(2.0)
            else:
                logger.error("❌ 多次尝试仍未能进入全屏模式")
                return False
            
            # 执行搜索浏览循环
            search_session.run_search_result_browse_loop()
            
            # 记录统计
            self.stats['search_videos'] = search_session.stats.get('videos_watched', 0)
            self.stats['total_replies'] = search_session.stats.get('replies_sent', 0)
            self.stats['total_likes'] += search_session.stats.get('likes_given', 0)
            
            logger.info("\n✅ 搜索浏览阶段完成")
            
            return True
            
        except KeyboardInterrupt:
            logger.info("\n⚠️ 用户中断程序")
            return False
        except Exception as e:
            logger.error(f"❌ 程序运行异常: {e}")
            traceback.print_exc()
            return False
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """清理资源并显示统计"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds() if self.start_time else 0
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 任务完成统计")
        logger.info("=" * 60)
        logger.info(f"   ⏱️  总运行时长: {int(duration)}秒 ({int(duration//60)}分钟)")
        logger.info(f"   🎲 预热视频数: {self.stats['warmup_videos']}")
        logger.info(f"   🔍 搜索视频数: {self.stats['search_videos']}")
        logger.info(f"   💬 发送回复数: {self.stats['total_replies']}")
        logger.info(f"   👍 点赞次数:   {self.stats['total_likes']}")
        logger.info("=" * 60)
        
        # 关闭driver
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Driver 已关闭")
            except Exception as e:
                logger.warning(f"⚠️ Driver 关闭异常: {e}")


# 全局变量用于信号处理
_main_program = None

def _signal_handler(signum, frame):
    """信号处理器"""
    logger.warning(f"\n⚠️ 收到中断信号 ({signum})，正在清理...")
    global _main_program
    if _main_program:
        _main_program._cleanup()
    sys.exit(1)


def main():
    """主入口"""
    global _main_program
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    
    try:
        logger.info("\n" + "🚀" * 30)
        logger.info("抖音RPA主程序 - 启动")
        logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("🚀" * 30)
        
        _main_program = MainProgram()
        success = _main_program.run()
        
        if success:
            logger.info("\n🎉 任务成功完成！")
        else:
            logger.info("\n⚠️ 任务未完全完成")
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
