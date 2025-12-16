"""
抖音随机浏览模块 - 完全重构版
基于 Appium + ADB 实现自动化随机浏览

功能特性:
- 环境检查 (Appium + ADB)
- 视频分类检测 (常规视频 vs 直播视频)
- 概率化交互 (22%跳过, 66%点赞, 66%评论, 33%收藏)
- 评论区滑动 (3-6次随机滑动)
- 两阶段浏览 (5-22秒 + 5-12秒)
- 3分钟运行时间
"""

import sys
import os
import time
import random
import signal
import subprocess
import traceback
from datetime import datetime
from typing import Optional, List

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块
from src import app_driver, interactions, core_utils
from src.logger import setup_logger
import config.settings as settings

# 初始化日志
logger = setup_logger("random_browse", log_dir="logs")


class RandomBrowseSession:
    """随机浏览会话管理器 - 新规格实现"""
    
    def __init__(self, runtime_seconds: int = 180):
        """
        初始化会话
        
        Args:
            runtime_seconds: 运行时间（秒），默认180秒（3分钟）
        """
        self.driver = None
        self.runtime_seconds = runtime_seconds
        self.start_time = None
        
        # 统计数据
        self.stats = {
            'videos_browsed': 0,      # 浏览的视频数
            'videos_skipped': 0,      # 22%跳过的视频数
            'normal_videos': 0,       # 常规视频数
            'live_videos': 0,         # 直播视频数
            'like_attempts': 0,       # 点赞尝试次数
            'like_success': 0,        # 点赞成功次数
            'comment_attempts': 0,    # 评论尝试次数
            'comment_success': 0,     # 评论成功次数
            'comment_scrolls': 0,     # 评论区滑动总次数
            'favorite_attempts': 0,   # 收藏尝试次数
            'favorite_success': 0,    # 收藏成功次数
            'comments_posted': []     # 发送的评论列表
        }
        
        # 加载评论库
        self.comments = self._load_comments()
        
        # 加载概率配置
        self.prob_config = self._load_probability_config()
        
        logger.info("=" * 60)
        logger.info("🎯 Random Browse Session 初始化完成")
        logger.info(f"⏱️  运行时长: {runtime_seconds}秒")
        logger.info(f"💬 评论库: {len(self.comments)}条")
        logger.info(f"🎲 概率配置: 跳过{int(self.prob_config['skip_video']*100)}% 点赞{int(self.prob_config['like']*100)}% 评论{int(self.prob_config['comment']*100)}% 收藏{int(self.prob_config['favorite']*100)}%")
        logger.info("=" * 60)
    
    def _load_comments(self) -> List[str]:
        """从config.yaml加载评论库"""
        import yaml
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f) or {}
            comments = cfg.get('random_browse', {}).get('comments', [])
            if comments:
                return comments
        except Exception as e:
            logger.warning(f"⚠️ 加载评论库失败: {e}")
        
        # 默认评论
        return ["666", "学到了", "真不错", "👍", "收藏了"]
    
    def _load_probability_config(self) -> dict:
        """加载互动概率配置"""
        import yaml
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f) or {}
            # 从 random_browse.probability 读取
            rb_cfg = cfg.get('random_browse', {})
            prob_cfg = rb_cfg.get('probability', {})
            return {
                'skip_video': prob_cfg.get('skip_video', 22) / 100,
                'like': prob_cfg.get('like', 66) / 100,
                'comment': prob_cfg.get('comment', 66) / 100,
                'favorite': prob_cfg.get('favorite', 33) / 100,
            }
        except Exception as e:
            logger.warning(f"⚠️ 概率配置读取失败，使用默认值: {e}")
            return {'skip_video': 0.22, 'like': 0.66, 'comment': 0.66, 'favorite': 0.33}
    
    def check_environment(self) -> bool:
        """
        检查运行环境
        
        Returns:
            bool: 环境检查是否通过
        """
        logger.info("\n" + "=" * 60)
        logger.info("🔍 开始环境检查...")
        logger.info("=" * 60)
        
        # 1. 检查 Appium 服务
        logger.info("📡 检查 Appium 服务...")
        try:
            import requests
            response = requests.get("http://127.0.0.1:4723/status", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Appium 服务运行正常")
            else:
                logger.error(f"❌ Appium 服务响应异常: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 无法连接 Appium 服务: {e}")
            logger.error("   请先运行: 启动Appium服务.bat")
            return False
        
        # 2. 检查 ADB 设备连接
        logger.info("📱 检查 ADB 设备连接...")
        try:
            result = subprocess.run(['adb', 'devices'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            if result.returncode != 0:
                logger.error("❌ ADB 命令执行失败")
                return False
            
            # 解析设备列表
            devices = [line for line in result.stdout.strip().split('\n')[1:] 
                      if '\tdevice' in line]
            
            if len(devices) == 0:
                logger.error("❌ 未检测到 Android 设备")
                logger.error("   请通过 USB 连接设备并启用 USB 调试")
                return False
            
            logger.info(f"✅ 检测到 {len(devices)} 个设备")
            for device in devices:
                logger.info(f"   📱 {device.split()[0]}")
                
        except FileNotFoundError:
            logger.error("❌ 未找到 ADB 命令")
            logger.error("   请确保 Android SDK 已安装并配置环境变量")
            return False
        except Exception as e:
            logger.error(f"❌ ADB 检查异常: {e}")
            return False
        
        logger.info("=" * 60)
        logger.info("✅ 环境检查通过")
        logger.info("=" * 60)
        return True
    
    def force_start_douyin(self) -> bool:
        """
        强制启动抖音 APP
        
        Returns:
            bool: 启动是否成功
        """
        logger.info("\n🚀 强制启动抖音 APP...")
        try:
            # 获取抖音包名
            douyin_package = "com.ss.android.ugc.aweme"
            douyin_activity = ".main.MainActivity"
            
            # 方法1: 先尝试terminate再activate（强制重启）
            try:
                logger.info(f"   尝试终止应用: {douyin_package}")
                self.driver.terminate_app(douyin_package)
                time.sleep(1.0)
            except:
                logger.info("   应用未运行，直接启动")
            
            # 启动应用
            logger.info(f"   启动应用: {douyin_package}")
            self.driver.activate_app(douyin_package)
            
            logger.info("✅ 抖音启动成功")
            time.sleep(3.0)  # 等待应用完全加载
            return True
            
        except Exception as e:
            logger.error(f"❌ 启动抖音异常: {e}")
            # 尝试备用方法：使用ADB启动
            try:
                logger.info("   尝试备用方法（ADB启动）...")
                import subprocess
                subprocess.run([
                    'adb', 'shell', 'am', 'start', '-n',
                    f'{douyin_package}/{douyin_activity}'
                ], timeout=10)
                logger.info("✅ 通过ADB启动成功")
                time.sleep(3.0)
                return True
            except Exception as e2:
                logger.error(f"❌ ADB启动也失败: {e2}")
                return False
    
    def ensure_in_recommendation_tab_and_click_video(self) -> bool:
        """
        确保在"推荐"tab下并进入常规视频模式
        
        逻辑简化：
        1. 切换到推荐tab
        2. 默认已在全屏模式，循环检测当前视频是否为常规视频（有交互按钮）
        3. 如果不是（直播/广告/无按钮），滑动到下一个
        4. 直到找到常规视频或超时
        """
        logger.info("\n🔍 确保在常规视频模式...")
        try:
            # APP打开默认在推荐tab，无需切换，直接查找常规视频
            max_attempts = 10
            logger.info(f"查找常规视频 (最多尝试{max_attempts}次)")
            
            for attempt in range(max_attempts):
                logger.info(f"\n🎯 视频检查尝试 {attempt + 1}/{max_attempts}")
                
                # 获取交互数据检测按钮
                interaction_data = self.get_video_interaction_data()
                has_like = interaction_data.get('has_like_button', False)
                has_comment = interaction_data.get('has_comment_button', False)
                
                if has_like and has_comment:
                    logger.info("✅ 确认检测到常规视频（有点赞/评论按钮）")
                    return True
                else:
                    logger.warning("⚠️ 当前不是常规视频（无交互按钮/直播/广告），切换下一个...")
                    core_utils.swipe_up_humanized()
                    time.sleep(random.uniform(1.5, 2.5))
            
            logger.error(f"❌ 经过 {max_attempts} 次尝试仍未找到常规视频")
            return False

        except Exception as e:
            logger.error(f"❌ 进入视频异常: {e}")
            return False

    def _handle_four_grid_interface(self) -> bool:
        """
        专门处理四宫格/卡片式列表的反自动化机制

        Returns:
            bool: 是否成功处理界面并进入真实视频
        """
        try:
            logger.info("🚨 检测到视频列表界面 - 启动卡片点击策略")

            # 优先尝试卡片式列表的专门点击策略
            if self._click_video_card():
                logger.info("✅ 卡片点击策略成功：成功点击视频卡片")
                return self._verify_video_entry_after_click()

            # 备用策略：传统四宫格处理
            logger.info("💥 启动传统四宫格破防策略")

            # 策略1: 强力点击第一个视频（最直接）
            if self._force_click_first_video():
                logger.info("✅ 策略1成功：强力点击第一个视频")
                return self._verify_video_entry_after_click()

            # 策略2: 尝试点击不同的网格位置
            if self._try_all_grid_positions():
                logger.info("✅ 策略2成功：尝试所有网格位置")
                return self._verify_video_entry_after_click()

            # 策略3: 长按视频进入详情（绕过限制）
            if self._long_press_video_entry():
                logger.info("✅ 策略3成功：长按进入视频详情")
                return self._verify_video_entry_after_click()

            # 策略4: 先返回上一级再重新进入
            if self._back_and_reenter():
                logger.info("✅ 策略4成功：返回重进")
                return self._verify_video_entry_after_click()

            logger.error("❌ 所有视频列表处理策略都失败")
            return False

        except Exception as e:
            logger.error(f"❌ 视频列表处理异常: {e}")
            return False

    def _click_video_card(self) -> bool:
        """
        专门点击视频卡片的策略（每排2个卡片）

        Returns:
            bool: 是否成功点击并进入视频
        """
        try:
            logger.info("📱 卡片点击策略: 专门处理视频卡片")

            if not self.driver:
                return False

            window_size = self.driver.get_window_size()
            width, height = window_size['width'], window_size['height']

            # 根据描述调整点击位置：每排2个卡片，总共4-5个
            card_positions = [
                # 第一排左边的卡片
                (width // 4, height // 3),
                # 第一排右边的卡片
                (width * 3 // 4, height // 3),
                # 第二排左边的卡片（如果有的话）
                (width // 4, height * 2 // 3),
                # 第二排右边的卡片（如果有的话）
                (width * 3 // 4, height * 2 // 3),
                # 中心位置作为备用
                (width // 2, height // 2),
            ]

            # 优先点击前几个可见的卡片
            for i, (click_x, click_y) in enumerate(card_positions):
                logger.info(f"   尝试点击卡片 {i+1}: ({click_x}, {click_y})")

                self.driver.tap([(click_x, click_y)])
                time.sleep(1.5)  # 等待页面响应

                # 检查是否进入了全屏视频
                new_state = self._detect_page_state()
                logger.debug(f"   点击后状态: {new_state}")

                if new_state == "fullscreen_video":
                    # 验证是否真的进入了视频模式
                    interaction_data = self.get_video_interaction_data()
                    has_like = interaction_data.get('has_like_button', False)
                    has_comment = interaction_data.get('has_comment_button', False)

                    if has_like and has_comment:
                        logger.info(f"✅ 卡片点击成功！成功进入视频模式（卡片 {i+1}）")
                        return True
                    else:
                        logger.warning(f"⚠️ 虽然进入全屏模式，但缺少交互按钮，继续尝试下一个卡片")

                elif new_state in ["video_list", "four_grid"]:
                    logger.info(f"   仍在卡片列表，尝试下一个卡片")
                    continue

                else:
                    logger.info(f"   页面状态变化为: {new_state}，继续尝试")
                    continue

            logger.warning("⚠️ 所有卡片位置都尝试过了，没有成功进入视频")
            return False

        except Exception as e:
            logger.debug(f"卡片点击失败: {e}")
            return False

    def _force_click_first_video(self) -> bool:
        """强力点击第一个视频"""
        try:
            logger.info("💥 策略1: 强力点击第一个视频")

            if not self.driver:
                return False

            window_size = self.driver.get_window_size()
            width, height = window_size['width'], window_size['height']

            # 第一个视频通常在左上角
            first_video_positions = [
                (width // 4, height // 4),        # 左上角
                (width // 3, height // 3),        # 稍微中心一点
                (width // 2 - 100, height // 3),  # 上部中间
            ]

            for i, (x, y) in enumerate(first_video_positions):
                logger.info(f"   尝试位置 {i+1}: ({x}, {y})")
                self.driver.tap([(x, y)])
                time.sleep(1.5)

                # 检查是否离开了四宫格
                new_state = self._detect_page_state()
                if new_state != "four_grid":
                    return True

            return False

        except Exception as e:
            logger.debug(f"强力点击失败: {e}")
            return False

    def _try_all_grid_positions(self) -> bool:
        """尝试点击所有可能的网格位置"""
        try:
            logger.info("🎯 策略2: 尝试所有网格位置")

            if not self.driver:
                return False

            window_size = self.driver.get_window_size()
            width, height = window_size['width'], window_size['height']

            # 卡片式列表的点击位置（每排2个卡片，总共4-5个）
            grid_positions = [
                # 第一排左边的卡片
                (width // 4, height // 3),
                # 第一排右边的卡片
                (width * 3 // 4, height // 3),
                # 第二排左边的卡片
                (width // 4, height * 2 // 3),
                # 第二排右边的卡片
                (width * 3 // 4, height * 2 // 3),
                # 中心位置作为备用
                (width // 2, height // 2),
                # 额外尝试位置（针对第三个露出一点的卡片）
                (width // 4, height * 4 // 5),
                (width * 3 // 4, height * 4 // 5),
            ]

            for i, (x, y) in enumerate(grid_positions):
                logger.info(f"   点击卡片位置 {i+1}: ({x}, {y})")
                self.driver.tap([(x, y)])
                time.sleep(2.0)  # 给更多时间让页面切换

                new_state = self._detect_page_state()
                if new_state == "fullscreen_video":
                    # 进一步验证是否真的进入了视频
                    interaction_data = self.get_video_interaction_data()
                    if (interaction_data.get('has_like_button', False) and
                        interaction_data.get('has_comment_button', False)):
                        return True

            return False

        except Exception as e:
            logger.debug(f"网格位置点击失败: {e}")
            return False

    def _long_press_video_entry(self) -> bool:
        """长按视频进入详情页面"""
        try:
            logger.info("👆 策略3: 长按视频进入详情")

            if not self.driver:
                return False

            window_size = self.driver.get_window_size()
            center_x, center_y = window_size['width'] // 2, window_size['height'] // 2

            # 尝试使用TouchAction进行长按
            try:
                from appium.webdriver.common.touch_action import TouchAction
                actions = TouchAction(self.driver)
                logger.info(f"   长按位置: ({center_x}, {center_y})")
                actions.press(x=center_x, y=center_y).wait(1500).release().perform()
            except ImportError:
                # 如果TouchAction不可用，使用多次点击模拟长按
                logger.warning("TouchAction不可用，使用快速点击模拟长按")
                for i in range(3):
                    self.driver.tap([(center_x, center_y)])
                    time.sleep(0.1)

            time.sleep(3.0)  # 等待长按菜单出现

            # 查找"进入详情"或类似按钮
            detail_selectors = [
                "//android.widget.TextView[@text='进入详情']",
                "//android.widget.TextView[@text='查看详情']",
                "//android.widget.TextView[contains(@text, '详情')]",
                "//android.widget.Button[contains(@text, '详情')]",
            ]

            from appium.webdriver.common.appiumby import AppiumBy as By
            for selector in detail_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        time.sleep(2.0)
                        return True
                except:
                    continue

            return False

        except Exception as e:
            logger.debug(f"长按操作失败: {e}")
            return False

    def _back_and_reenter(self) -> bool:
        """返回上一级再重新进入"""
        try:
            logger.info("🔙 策略4: 返回重进")

            if not self.driver:
                return False

            # 连续返回两次，确保离开四宫格
            logger.info("   执行返回操作")
            self.driver.press_keycode(4)  # Back键
            time.sleep(1.0)
            self.driver.press_keycode(4)
            time.sleep(2.0)

            # 重新进入推荐页面（优化版本）
            logger.info("   重新进入推荐页面")
            success = interactions.go_to_for_you_page()
            if success:
                time.sleep(1.0)  # 从2.0减少到1.0
                return True

            return False

        except Exception as e:
            logger.debug(f"返回重进失败: {e}")
            return False

    def _swipe_to_change_mode(self) -> bool:
        """滑动切换页面模式"""
        try:
            logger.info("📜 策略5: 滑动切换模式")

            if not self.driver:
                return False

            window_size = self.driver.get_window_size()
            width, height = window_size['width'], window_size['height']

            # 多种滑动模式
            swipe_patterns = [
                # 向上滑动
                (width // 2, height * 3 // 4, width // 2, height // 4, 800),
                # 向下滑动
                (width // 2, height // 4, width // 2, height * 3 // 4, 800),
                # 左滑动
                (width * 3 // 4, height // 2, width // 4, height // 2, 600),
                # 右滑动
                (width // 4, height // 2, width * 3 // 4, height // 2, 600),
            ]

            for i, (start_x, start_y, end_x, end_y, duration) in enumerate(swipe_patterns):
                logger.info(f"   滑动模式 {i+1}: ({start_x},{start_y}) -> ({end_x},{end_y})")
                self.driver.swipe(start_x, start_y, end_x, end_y, duration)
                time.sleep(2.0)

                new_state = self._detect_page_state()
                if new_state != "four_grid":
                    return True

            return False

        except Exception as e:
            logger.debug(f"滑动切换失败: {e}")
            return False

    def _verify_video_entry_after_click(self) -> bool:
        """点击后验证是否成功进入视频"""
        try:
            logger.info("🔍 验证视频进入结果...")

            # 多次验证确保稳定
            for verify_attempt in range(3):
                time.sleep(1.0)
                new_state = self._detect_page_state()
                logger.info(f"   验证 {verify_attempt + 1}/3: {new_state}")

                if new_state == "fullscreen_video":
                    # 强制验证交互按钮
                    interaction_data = self.get_video_interaction_data()
                    has_like = interaction_data.get('has_like_button', False)
                    has_comment = interaction_data.get('has_comment_button', False)

                    if has_like and has_comment:
                        logger.info("✅ 确认成功进入视频模式，检测到交互按钮")
                        return True
                    else:
                        logger.warning("⚠️ 虽然检测到全屏模式，但交互按钮不完整")

                elif new_state == "four_grid":
                    logger.warning("⚠️ 仍然在四宫格界面")

                else:
                    logger.info(f"   页面状态变化: {new_state}")

            logger.error("❌ 3次验证都未确认成功进入视频")
            return False

        except Exception as e:
            logger.debug(f"视频进入验证失败: {e}")
            return False

    def _click_random_video_from_list_with_verification(self) -> bool:
        """
        点击视频并验证是否成功进入全屏模式

        Returns:
            bool: 是否成功进入全屏视频
        """
        try:
            logger.info("👆 尝试点击视频并验证...")

            # 尝试多种点击策略
            strategies = [
                self._strategy_click_video_elements,
                self._strategy_click_by_coordinates,
                self._strategy_click_center_area
            ]

            for idx, strategy in enumerate(strategies, 1):
                logger.info(f"   使用策略 {idx}: {strategy.__name__}")

                try:
                    if strategy():
                        # 点击后等待页面切换
                        time.sleep(2.0)

                        # 验证是否成功进入全屏视频
                        new_state = self._detect_page_state()
                        logger.info(f"   点击后页面状态: {new_state}")

                        if new_state == "fullscreen_video":
                            # 强制验证交互按钮
                            interaction_data = self.get_video_interaction_data()
                            if interaction_data.get('has_like_button', False) and interaction_data.get('has_comment_button', False):
                                logger.info("✅ 策略 {idx} 成功：进入全屏模式并检测到交互按钮")
                                return True
                            else:
                                logger.warning(f"⚠️ 策略 {idx} 进入全屏但未检测到交互按钮")
                                continue
                        else:
                            logger.warning(f"⚠️ 策略 {idx} 未进入全屏模式，状态: {new_state}")
                            continue

                except Exception as e:
                    logger.warning(f"⚠️ 策略 {idx} 失败: {e}")
                    continue

            logger.error("❌ 所有策略都失败，无法进入视频")
            return False

        except Exception as e:
            logger.error(f"❌ 点击视频验证失败: {e}")
            return False

    def _strategy_click_video_elements(self) -> bool:
        """策略1：通过元素查找点击"""
        try:
            return self._click_random_video_from_list()
        except Exception as e:
            logger.debug(f"元素点击策略失败: {e}")
            return False

    def _strategy_click_by_coordinates(self) -> bool:
        """策略2：坐标点击"""
        try:
            return self._click_video_by_coordinates()
        except Exception as e:
            logger.debug(f"坐标点击策略失败: {e}")
            return False

    def _strategy_click_center_area(self) -> bool:
        """策略3：点击中心区域"""
        try:
            logger.info("🎯 使用中心区域点击策略...")

            if not self.driver:
                logger.warning("Driver为空，无法使用中心区域点击")
                return False

            window_size = self.driver.get_window_size()
            width = window_size['width']
            height = window_size['height']

            # 尝试点击多个可能的视频区域
            click_positions = [
                # 屏幕中央
                (width // 2, height // 2),
                # 上半部分
                (width // 2, height // 3),
                # 下半部分
                (width // 2, height * 2 // 3),
                # 左上区域
                (width // 3, height // 3),
                # 右上区域
                (width * 2 // 3, height // 3),
                # 左下区域
                (width // 3, height * 2 // 3),
                # 右下区域
                (width * 2 // 3, height * 2 // 3),
            ]

            for i, (click_x, click_y) in enumerate(click_positions):
                logger.info(f"   点击位置 {i+1}: ({click_x}, {click_y})")
                if self.driver:
                    self.driver.tap([(click_x, click_y)])
                time.sleep(0.5)

                # 每次点击后检查是否成功
                new_state = self._detect_page_state()
                if new_state == "fullscreen_video":
                    interaction_data = self.get_video_interaction_data()
                    if interaction_data.get('has_like_button', False):
                        logger.info(f"✅ 中心点击成功，位置 {i+1}")
                        return True

            return False

        except Exception as e:
            logger.debug(f"中心区域点击失败: {e}")
            return False

    def _swipe_to_video_list(self) -> bool:
        """
        尝试滑动到视频列表

        Returns:
            bool: 是否成功
        """
        try:
            logger.info("📜 尝试滑动到视频列表...")

            if not self.driver:
                logger.warning("Driver为空，无法滑动")
                return False

            window_size = self.driver.get_window_size()
            width = window_size['width']
            height = window_size['height']

            # 尝试不同的滑动方向
            swipe_patterns = [
                # 向下滑动
                (width // 2, height // 4, width // 2, height * 3 // 4, 1000),
                # 向上滑动
                (width // 2, height * 3 // 4, width // 2, height // 4, 1000),
                # 左右滑动
                (width // 4, height // 2, width * 3 // 4, height // 2, 800),
            ]

            for i, (start_x, start_y, end_x, end_y, duration) in enumerate(swipe_patterns):
                logger.info(f"   滑动模式 {i+1}: ({start_x},{start_y}) -> ({end_x},{end_y})")
                if self.driver:
                    self.driver.swipe(start_x, start_y, end_x, end_y, duration)
                time.sleep(1.0)

                # 检查是否到达视频列表
                new_state = self._detect_page_state()
                if new_state == "video_list":
                    logger.info(f"✅ 滑动成功，到达视频列表")
                    return True

            return False

        except Exception as e:
            logger.debug(f"滑动失败: {e}")
            return False

    def _detect_page_state(self) -> str:
        """
        智能检测当前页面状态（反四宫格欺骗机制）

        Returns:
            str: "fullscreen_video"(全屏视频), "video_list"(视频列表), "four_grid"(四宫格), "unknown"(未知)
        """
        try:
            if not self.driver:
                logger.warning("Driver为空，无法检测页面状态")
                return "unknown"

            page_source = self.driver.page_source
            from appium.webdriver.common.appiumby import AppiumBy as By

            # 第1层：基础特征检测（可能会被欺骗）
            fullscreen_indicators = [
                "点赞", "评论", "收藏", "分享",
                "com.ss.android.ugc.aweme:id/a3o",  # 点赞按钮ID
                "com.ss.android.ugc.aweme:id/eiz",  # 评论按钮ID
                "com.ss.android.ugc.aweme:id/d-5",  # 收藏按钮ID
            ]

            fullscreen_text_count = sum(1 for indicator in fullscreen_indicators if indicator in page_source)

            # 第2层：区分传统四宫格和卡片式列表
            traditional_grid_indicators = [
                "GridView", "android.widget.GridView",  # 真正的网格布局
                "四宫格", "宫格",  # 中文网格标识
                "RecyclerView.*GridView",  # 嵌套网格
            ]

            # 卡片式列表特征（每排2个卡片）
            card_list_indicators = [
                "RecyclerView",  # 列表容器
                "ListView",
                "视频列表",
                "FrameLayout.*ImageView",  # 卡片容器（FrameLayout包裹ImageView）
                "clickable.*FrameLayout",  # 可点击的FrameLayout
            ]

            traditional_grid_count = sum(1 for indicator in traditional_grid_indicators if indicator.lower() in page_source.lower())
            card_list_count = sum(1 for indicator in card_list_indicators if indicator.lower() in page_source.lower())

            # 第3层：元素功能性检测（决定性！）
            # 检测是否有真实的可点击交互按钮
            real_interactions = self._verify_real_interactions()

            # 第4层：视频播放器检测
            has_video_player = self._detect_video_player()

            # 第5层：屏幕布局分析
            layout_analysis = self._analyze_screen_layout()

            logger.info(f"🔍 页面状态分析:")
            logger.info(f"   文本特征: {fullscreen_text_count}/4 (全屏指标)")
            logger.info(f"   传统四宫格: {traditional_grid_count} (网格指标)")
            logger.info(f"   卡片式列表: {card_list_count} (列表指标)")
            logger.info(f"   真实交互: {real_interactions['count']} 个可点击元素")
            logger.info(f"   视频播放器: {has_video_player}")
            logger.info(f"   布局分析: {layout_analysis}")

            # 决策逻辑：优先识别卡片式列表，其次才是传统四宫格
            if card_list_count >= 2 and not traditional_grid_count:
                logger.info("🎯 检测结果: 卡片式视频列表")
                return "video_list"

            if traditional_grid_count >= 3:
                logger.info("🎯 检测结果: 传统四宫格界面")
                return "four_grid"

            if (real_interactions['count'] >= 2 and
                has_video_player and
                fullscreen_text_count >= 2 and
                layout_analysis.get('is_fullscreen', False)):
                logger.info("🎯 检测结果: 真实全屏视频")
                return "fullscreen_video"

            # 检测视频列表特征
            list_indicators = ["RecyclerView", "ListView", "视频列表"]
            if any(indicator in page_source for indicator in list_indicators):
                logger.info("🎯 检测结果: 视频列表")
                return "video_list"

            logger.info("🎯 检测结果: 未知状态")
            return "unknown"

        except Exception as e:
            logger.error(f"❌ 页面状态检测异常: {e}")
            return "unknown"

    def _verify_real_interactions(self) -> dict:
        """
        验证真实的交互元素（关键！区分真假界面）

        Returns:
            dict: 包含真实交互元素信息的字典
        """
        try:
            from appium.webdriver.common.appiumby import AppiumBy as By

            real_interactions = {
                'count': 0,
                'elements': [],
                'details': []
            }

            # 检查真实的可点击交互按钮
            interaction_selectors = [
                # 点赞相关
                (By.ID, "com.ss.android.ugc.aweme:id/a3o"),
                (By.XPATH, "//android.widget.ImageView[contains(@content-desc, '点赞')]"),
                (By.XPATH, "//android.widget.LinearLayout[contains(@content-desc, '点赞')]"),

                # 评论相关
                (By.ID, "com.ss.android.ugc.aweme:id/eiz"),
                (By.XPATH, "//android.widget.ImageView[contains(@content-desc, '评论')]"),
                (By.XPATH, "//android.widget.LinearLayout[contains(@content-desc, '评论')]"),

                # 收藏相关
                (By.ID, "com.ss.android.ugc.aweme:id/d-5"),
                (By.XPATH, "//android.widget.ImageView[contains(@content-desc, '收藏')]"),
                (By.XPATH, "//android.widget.LinearLayout[contains(@content-desc, '收藏')]"),

                # 分享相关
                (By.XPATH, "//android.widget.ImageView[contains(@content-desc, '分享')]"),
            ]

            for by_type, selector in interaction_selectors:
                try:
                    if not self.driver:
                        continue
                    elements = self.driver.find_elements(by_type, selector)
                    for element in elements:
                        try:
                            # 关键检查：元素是否真实可点击
                            if element.is_displayed() and element.is_enabled():
                                # 检查元素大小（四宫格中的假按钮通常很小）
                                size = element.size
                                if size['width'] > 20 and size['height'] > 20:  # 真实按钮应该有一定大小
                                    real_interactions['count'] += 1
                                    real_interactions['elements'].append(element)
                                    real_interactions['details'].append({
                                        'selector': selector,
                                        'size': f"{size['width']}x{size['height']}",
                                        'location': element.location,
                                        'text': element.text or element.get_attribute('content-desc') or ''
                                    })
                        except:
                            continue
                except:
                    continue

            return real_interactions

        except Exception as e:
            logger.debug(f"真实交互验证失败: {e}")
            return {'count': 0, 'elements': [], 'details': []}

    def _detect_video_player(self) -> bool:
        """
        检测是否有真实的视频播放器

        Returns:
            bool: 是否检测到视频播放器
        """
        try:
            from appium.webdriver.common.appiumby import AppiumBy as By

            # 视频播放器特征
            player_selectors = [
                (By.XPATH, "//android.widget.ImageView[contains(@resource-id, 'player')]"),
                (By.XPATH, "//android.view.View[contains(@resource-id, 'player')]"),
                (By.XPATH, "//android.widget.FrameLayout[contains(@resource-id, 'container')]"),
                (By.XPATH, "//android.widget.VideoView"),
                (By.XPATH, "//*[contains(@content-desc, '视频') and not(contains(@content-desc, '列表'))]"),
            ]

            for by_type, selector in player_selectors:
                try:
                    if not self.driver:
                        continue
                    elements = self.driver.find_elements(by_type, selector)
                    for element in elements:
                        try:
                            # 检查元素大小（视频播放器应该占据大部分屏幕）
                            size = element.size
                            window_size = self.driver.get_window_size()
                            screen_ratio = (size['width'] * size['height']) / (window_size['width'] * window_size['height'])

                            if screen_ratio > 0.3:  # 视频播放器应该占据至少30%的屏幕
                                return True
                        except:
                            continue
                except:
                    continue

            return False

        except Exception as e:
            logger.debug(f"视频播放器检测失败: {e}")
            return False

    def _analyze_screen_layout(self) -> dict:
        """
        分析屏幕布局特征

        Returns:
            dict: 布局分析结果
        """
        try:
            if not self.driver:
                return {
                    'is_portrait': False,
                    'has_grid_layout': False,
                    'image_count': 0,
                    'is_fullscreen': False,
                    'screen_size': 'unknown'
                }
            window_size = self.driver.get_window_size()
            page_source = self.driver.page_source.lower()

            # 计算屏幕方向
            is_portrait = window_size['height'] > window_size['width']

            # 检测网格布局特征
            grid_patterns = [
                'recyclerview.*gridview',
                'gridview.*recyclerview',
                'gridlayout',
                'grid.*layout'
            ]

            has_grid_layout = any(pattern in page_source for pattern in grid_patterns)

            # 检测多图片布局
            image_count = page_source.count('imageview')

            # 判断是否为全屏布局
            is_fullscreen = (
                is_portrait and  # 竖屏模式
                not has_grid_layout and  # 没有网格布局
                image_count >= 2 and image_count <= 6  # 合理的图片数量
            )

            return {
                'is_portrait': is_portrait,
                'has_grid_layout': has_grid_layout,
                'image_count': image_count,
                'is_fullscreen': is_fullscreen,
                'screen_size': f"{window_size['width']}x{window_size['height']}"
            }

        except Exception as e:
            logger.debug(f"屏幕布局分析失败: {e}")
            return {
                'is_portrait': False,
                'has_grid_layout': False,
                'image_count': 0,
                'is_fullscreen': False,
                'screen_size': 'unknown'
            }

    def _click_random_video_from_list(self) -> bool:
        """
        在视频列表中随机点击一个视频

        Returns:
            bool: 是否成功点击并进入视频
        """
        try:
            logger.info("👆 在视频列表中随机点击视频...")

            from appium.webdriver.common.appiumby import AppiumBy as By

            # 多种策略查找视频元素
            video_selectors = [
                # 策略1: 通过ImageView查找视频缩略图
                (By.XPATH, "//android.widget.ImageView[contains(@content-desc, '视频') or contains(@resource-id, 'cover')]"),

                # 策略2: 通过FrameLayout查找视频卡片
                (By.XPATH, "//android.widget.FrameLayout[@clickable='true']//android.widget.ImageView"),

                # 策略3: 查找RecycleView中的视频项
                (By.XPATH, "//androidx.recyclerview.widget.RecyclerView//android.widget.FrameLayout[1]//android.widget.ImageView"),

                # 策略4: 通用视频缩略图选择器
                (By.XPATH, "//android.widget.ImageView[contains(@resource-id, 'image') or contains(@resource-id, 'cover') or contains(@resource-id, 'thumb')]"),

                # 策略5: 通过ListView中的视频项
                (By.XPATH, "//android.widget.ListView//android.widget.ImageView"),
            ]

            video_elements = []

            for idx, (by_type, selector) in enumerate(video_selectors, 1):
                logger.info(f"   尝试策略 {idx}: {selector[:50]}...")
                try:
                    if not self.driver:
                        logger.warning("Driver为空，跳过此策略")
                        continue
                    elements = self.driver.find_elements(by_type, selector)
                    if elements:
                        # 过滤掉不可点击的元素
                        clickable_elements = []
                        for element in elements:
                            try:
                                # 检查是否可点击或其父容器可点击
                                if element.is_enabled() and element.is_displayed():
                                    clickable_elements.append(element)
                            except:
                                continue

                        if clickable_elements:
                            video_elements.extend(clickable_elements)
                            logger.info(f"   找到 {len(clickable_elements)} 个可点击视频元素")
                            break
                except Exception as e:
                    logger.debug(f"   策略 {idx} 失败: {e}")
                    continue

            if not video_elements:
                logger.warning("⚠️ 未找到可点击的视频元素，尝试坐标点击")
                return self._click_video_by_coordinates()

            # 随机选择一个视频点击
            selected_video = random.choice(video_elements)

            # 记录视频位置信息
            try:
                location = selected_video.location
                size = selected_video.size
                logger.info(f"   选中的视频位置: ({location['x']}, {location['y']}) 大小: {size['width']}x{size['height']}")
            except:
                pass

            # 点击视频
            logger.info("👆 点击视频进入全屏模式...")
            selected_video.click()

            # 等待页面切换
            time.sleep(2.0)

            # 验证是否成功进入全屏视频
            new_state = self._detect_page_state()
            if new_state == "fullscreen_video":
                logger.info("✅ 成功进入全屏视频模式")
                return True
            else:
                logger.warning(f"⚠️ 点击后页面状态仍为: {new_state}")
                return False

        except Exception as e:
            logger.error(f"❌ 点击视频失败: {e}")
            return False

    def _click_video_by_coordinates(self) -> bool:
        """
        通过坐标点击视频（备用方案）

        Returns:
            bool: 是否成功点击
        """
        try:
            logger.info("🎯 使用坐标点击方案...")

            if not self.driver:
                logger.warning("Driver为空，无法使用坐标点击")
                return False

            window_size = self.driver.get_window_size()
            width = window_size['width']
            height = window_size['height']

            # 在屏幕中间区域随机点击（视频通常在中间区域）
            center_x = width // 2
            center_y = height // 2

            # 在中心区域随机偏移
            offset_x = random.randint(-width//6, width//6)
            offset_y = random.randint(-height//8, height//8)

            click_x = center_x + offset_x
            click_y = center_y + offset_y

            # 确保坐标在屏幕范围内
            click_x = max(width//10, min(width * 9//10, click_x))
            click_y = max(height//10, min(height * 9//10, click_y))

            logger.info(f"   点击坐标: ({click_x}, {click_y})")

            self.driver.tap([(click_x, click_y)])
            time.sleep(2.0)

            # 验证结果
            new_state = self._detect_page_state()
            if new_state == "fullscreen_video":
                logger.info("✅ 坐标点击成功进入全屏视频")
                return True
            else:
                logger.warning(f"⚠️ 坐标点击后页面状态: {new_state}")
                return False

        except Exception as e:
            logger.error(f"❌ 坐标点击失败: {e}")
            return False
    
    def get_video_interaction_data(self) -> dict:
        """
        获取视频互动数据（点赞数、评论数等）

        Returns:
            dict: 包含互动数据的字典
        """
        try:
            from appium.webdriver.common.appiumby import AppiumBy as By

            interaction_data = {
                'like_count': 0,
                'comment_count': 0,
                'like_text': '',
                'comment_text': '',
                'has_like_button': False,
                'has_comment_button': False,
                'has_favorite_button': False,
                'is_liked': False,
                'raw_text': ''
            }

            # 方法1: 通过页面源码解析数字
            page_source = self.driver.page_source
            interaction_data['raw_text'] = page_source

            # 尝试解析点赞数 - 增强版正则表达式
            like_patterns = [
                # Appium页面源码中的实际格式（优化版）
                r'a3o[^>]*>(\d+(?:\.\d+)?[kKwW万]?)',
                r'a3o[^>]*content-desc[^>]*>(\d+(?:\.\d+)?[kKwW万]?)',
                r'a3o.*?(\d+(?:\.\d+)?[kKwW万]?)',
                # 点赞按钮相关文本
                r'点赞.*?(\d+(?:\.\d+)?[kKwW万]?)',
                r'(\d+(?:\.\d+)?[kKwW万]?)\s*赞',
                # 直接匹配模式
                r'点赞\s*[:：]?\s*(\d+(?:\.\d+)?[kKwW万]?)',
                r'赞\s*[:：]?\s*(\d+(?:\.\d+)?[kKwW万]?)',
                # 数量在文字前面
                r'(\d+(?:\.\d+)?[kKwW万]?)\s*[点赞赞]',
                # 更通用的匹配
                r'[点赞Like][:：]?\s*(\d+(?:\.\d+)?[kKwW万]?)',
                r'(\d+(?:\.\d+)?[kKwW万]?)\s*[个次条]*[点赞赞]',
                # 英文模式
                r'like.*?(\d+(?:\.\d+)?[kKwW万]?)',
                r'(\d+(?:\.\d+)?[kKwW万]?)\s*likes?',
                # 纯数字模式（作为最后备选）
                r'(\d{1,6}(?:\.\d)?[kKwW万]?)',
                r'(\d+)',
            ]

            # 尝试解析评论数 - 增强版正则表达式
            comment_patterns = [
                # Appium页面源码中的实际格式（优化版）
                r'eiz[^>]*>(\d+(?:\.\d+)?[kKwW万]?)',
                r'eiz[^>]*content-desc[^>]*>(\d+(?:\.\d+)?[kKwW万]?)',
                r'eiz.*?(\d+(?:\.\d+)?[kKwW万]?)',
                # 评论按钮相关文本
                r'评论.*?(\d+(?:\.\d+)?[kKwW万]?)',
                r'(\d+(?:\.\d+)?[kKwW万]?)\s*评论',
                # 直接匹配模式
                r'评论\s*[:：]?\s*(\d+(?:\.\d+)?[kKwW万]?)',
                # 数量在文字前面
                r'(\d+(?:\.\d+)?[kKwW万]?)\s*[评论]',
                # 更通用的匹配
                r'[评论Comment][:：]?\s*(\d+(?:\.\d+)?[kKwW万]?)',
                r'(\d+(?:\.\d+)?[kKwW万]?)\s*[个次条条]*[评论]',
                # 英文模式
                r'comment.*?(\d+(?:\.\d+)?[kKwW万]?)',
                r'(\d+(?:\.\d+)?[kKwW万]?)\s*comments?',
            ]

            # 执行正则匹配 - 点赞数
            logger.debug("🔍 开始解析点赞数...")
            import re
            found_like = False

            for i, pattern in enumerate(like_patterns, 1):
                try:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    if matches:
                        match = matches[0]  # 取第一个匹配
                        logger.debug(f"   点赞匹配模式 {i}: {pattern[:50]} -> {match}")
                        interaction_data['like_text'] = match
                        interaction_data['like_count'] = self._parse_number(match)
                        interaction_data['has_like_button'] = True
                        found_like = True
                        break
                except Exception as e:
                    logger.debug(f"   点赞模式 {i} 解析失败: {e}")
                    continue

            if not found_like:
                logger.debug("   未找到点赞数匹配")

            # 执行正则匹配 - 评论数
            logger.debug("🔍 开始解析评论数...")
            found_comment = False

            for i, pattern in enumerate(comment_patterns, 1):
                try:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    if matches:
                        match = matches[0]  # 取第一个匹配
                        logger.debug(f"   评论匹配模式 {i}: {pattern[:50]} -> {match}")
                        interaction_data['comment_text'] = match
                        interaction_data['comment_count'] = self._parse_number(match)
                        interaction_data['has_comment_button'] = True
                        found_comment = True
                        break
                except Exception as e:
                    logger.debug(f"   评论模式 {i} 解析失败: {e}")
                    continue

            if not found_comment:
                logger.debug("   未找到评论数匹配")

            # 方法2: 通过UI元素查找
            try:
                # 查找点赞按钮和对应的文本
                like_selectors = [
                    (By.XPATH, "//android.widget.TextView[contains(@text, '点赞')]"),
                    (By.XPATH, "//android.widget.TextView[contains(@text, '赞')]"),
                    (By.XPATH, "//android.widget.LinearLayout[contains(@content-desc, '点赞')]"),
                    (By.XPATH, "//android.widget.LinearLayout[contains(@content-desc, '赞')]"),
                    (By.ID, "com.ss.android.ugc.aweme:id/a3o"),
                    (By.ID, "com.ss.android.ugc.aweme:id/dkh"),
                ]

                for by_type, selector in like_selectors:
                    try:
                        elements = self.driver.find_elements(by_type, selector)
                        for element in elements:
                            try:
                                text = element.text or element.get_attribute('content-desc') or ''
                                if text and any(char.isdigit() for char in text):
                                    interaction_data['like_text'] = text
                                    interaction_data['like_count'] = self._parse_number(text)
                                    interaction_data['has_like_button'] = True

                                    # 检查是否已点赞（通常已点赞的状态有不同的文字或图标）
                                    if any(word in text for word in ['已赞', '取消赞', '已喜欢']):
                                        interaction_data['is_liked'] = True
                                    break
                            except:
                                continue
                        if interaction_data['like_count'] > 0:
                            break
                    except:
                        continue

                # 查找评论按钮和对应的文本
                comment_selectors = [
                    (By.XPATH, "//android.widget.TextView[contains(@text, '评论')]"),
                    (By.XPATH, "//android.widget.TextView[contains(@text, '评论数')]"),
                    (By.XPATH, "//android.widget.LinearLayout[contains(@content-desc, '评论')]"),
                    (By.ID, "com.ss.android.ugc.aweme:id/eiz"),
                    (By.ID, "com.ss.android.ugc.aweme:id/dki"),
                ]

                for by_type, selector in comment_selectors:
                    try:
                        elements = self.driver.find_elements(by_type, selector)
                        for element in elements:
                            try:
                                text = element.text or element.get_attribute('content-desc') or ''
                                if text and any(char.isdigit() for char in text):
                                    interaction_data['comment_text'] = text
                                    interaction_data['comment_count'] = self._parse_number(text)
                                    interaction_data['has_comment_button'] = True
                                    break
                            except:
                                continue
                        if interaction_data['comment_count'] > 0:
                            break
                    except:
                        continue

            except Exception as e:
                logger.debug(f"UI元素查找互动数据失败: {e}")

            # 记录日志
            logger.info(f"📊 视频互动数据:")
            logger.info(f"   ❤️  点赞: {interaction_data['like_text']} ({interaction_data['like_count']}) - 已点赞: {interaction_data['is_liked']}")
            logger.info(f"   💬 评论: {interaction_data['comment_text']} ({interaction_data['comment_count']})")
            logger.info(f"   🔘 按钮: 点赞={interaction_data['has_like_button']}, 评论={interaction_data['has_comment_button']}")

            return interaction_data

        except Exception as e:
            logger.error(f"❌ 获取视频互动数据异常: {e}")
            return {
                'like_count': 0, 'comment_count': 0, 'like_text': '', 'comment_text': '',
                'has_like_button': False, 'has_comment_button': False, 'has_favorite_button': False,
                'is_liked': False, 'raw_text': ''
            }

    def _parse_number(self, text: str) -> int:
        """
        解析数字文本（支持k、w等单位）

        Args:
            text: 数字文本，如 "1.2k", "3w", "500"

        Returns:
            int: 解析后的数字
        """
        try:
            if not text:
                return 0

            text = text.strip().lower()

            # 提取数字部分
            import re
            match = re.search(r'(\d+(?:\.\d+)?)([kw]?)', text)
            if not match:
                # 如果没有数字，尝试查找单个数字
                numbers = re.findall(r'\d+', text)
                if numbers:
                    return int(numbers[0])
                return 0

            number = float(match.group(1))
            unit = match.group(2)

            if unit == 'k':
                return int(number * 1000)
            elif unit == 'w':
                return int(number * 10000)
            else:
                return int(number)

        except Exception as e:
            logger.debug(f"数字解析失败 '{text}': {e}")
            return 0

    def is_video_worthy_browsing(self, interaction_data: dict) -> bool:
        """
        根据互动数据判断视频是否值得浏览和评论
        新标准：评论数量>=5为目标视频

        Args:
            interaction_data: 视频互动数据

        Returns:
            bool: 是否值得浏览
        """
        try:
            # 如果没有互动按钮，不值得浏览
            if not interaction_data.get('has_like_button', False):
                logger.info("⚠️ 无点赞按钮，跳过此视频")
                return False

            # 获取评论数
            comments = interaction_data.get('comment_count', 0)
            likes = interaction_data.get('like_count', 0)

            # 新标准：评论数>=5为目标视频
            is_worthy = comments >= 5

            logger.info(f"🎯 视频价值判断 (新标准):")
            logger.info(f"   💬 评论数: {comments} {'✅≥5 (目标视频)' if is_worthy else '❌<5 (跳过)'}")
            logger.info(f"   ❤️  点赞数: {likes}")

            return is_worthy

        except Exception as e:
            logger.error(f"❌ 视频价值判断异常: {e}")
            return True  # 默认值得浏览

    def detect_video_type(self) -> str:
        """
        检测当前视频类型

        Returns:
            str: "normal" (常规视频), "live" (直播视频), "unknown" (未知)
        """
        try:
            # 先获取互动数据
            interaction_data = self.get_video_interaction_data()

            # 方法1: 检测直播标识（最直接）
            page_source = interaction_data.get('raw_text', self.driver.page_source)

            live_indicators = [
                "点击进入直播间",
                "进入直播间",
                "直播中",
                "直播间",
                "正在直播"
            ]

            for indicator in live_indicators:
                if indicator in page_source:
                    logger.info("🔴 检测到直播视频")
                    self.stats['live_videos'] += 1
                    return "live"

            # 方法2: 检测常规视频特征（有交互按钮）
            has_like = interaction_data.get('has_like_button', False)
            has_comment = interaction_data.get('has_comment_button', False)
            has_favorite = interaction_data.get('has_favorite_button', False)

            # 更宽松的检测条件：有任何交互按钮都认为是常规视频
            if has_like or has_comment or has_favorite:
                logger.info("✅ 检测到常规视频（有交互按钮）")
                logger.info(f"   交互按钮状态: 点赞={has_like}, 评论={has_comment}, 收藏={has_favorite}")
                self.stats['normal_videos'] += 1
                return "normal"

            # 方法3: 检测页面状态（更直接的判断）
            current_state = self._detect_page_state()
            if current_state == "fullscreen_video":
                logger.info("✅ 页面状态检测为全屏视频，确认为常规视频")
                self.stats['normal_videos'] += 1
                return "normal"

            # 方法4: 检测页面源码中的交互元素文本
            interactive_keywords = ["点赞", "评论", "收藏", "分享", "like", "comment"]
            page_source = interaction_data.get('raw_text', '').lower()

            keyword_count = sum(1 for keyword in interactive_keywords if keyword in page_source)
            if keyword_count >= 2:
                logger.info(f"✅ 源码检测到{keyword_count}个交互关键词，确认为常规视频")
                self.stats['normal_videos'] += 1
                return "normal"

            logger.warning("⚠️ 未知视频类型 - 无任何交互按钮或特征")
            logger.warning(f"   交互数据: {interaction_data}")
            logger.warning(f"   页面状态: {current_state}")
            return "unknown"

        except Exception as e:
            logger.error(f"❌ 视频类型检测异常: {e}")
            return "unknown"
    
    def skip_with_probability(self) -> bool:
        """
        概率跳过（模拟不感兴趣），概率来自配置
        
        Returns:
            bool: True=跳过, False=不跳过
        """
        skip_prob = self.prob_config.get('skip_video', 0.22)
        if random.random() < skip_prob:
            logger.info(f"👋 命中跳过概率 ({int(skip_prob*100)}%) - 模拟不感兴趣")
            self.stats['videos_skipped'] += 1
            return True
        return False
    
    def read_all_comments(self) -> bool:
        """
        进入评论区，逐条阅读所有评论

        Returns:
            bool: 阅读是否成功
        """
        try:
            logger.info("=" * 60)
            logger.info("📖 开始逐条阅读评论...")

            # 1. 打开评论区
            logger.info("📝 步骤1: 打开评论面板")
            comment_button_found = False

            comment_selectors = [
                {"by": "xpath", "value": "//android.widget.ImageView[@content-desc and contains(@content-desc, '评论')]"},
                {"by": "xpath", "value": "//android.widget.LinearLayout[@content-desc and contains(@content-desc, '评论')]"},
                {"by": "id", "value": "com.ss.android.ugc.aweme:id/eiz"},
                {"by": "id", "value": "com.ss.android.ugc.aweme:id/a3p"},
            ]

            from appium.webdriver.common.appiumby import AppiumBy as By

            for selector in comment_selectors:
                by_type = By.XPATH if selector['by'] == 'xpath' else By.ID
                if core_utils.wait_and_click(by_type, selector['value'], timeout=3):
                    logger.info("✅ 评论按钮已点击")
                    comment_button_found = True
                    break

            if not comment_button_found:
                logger.warning("⚠️ 未找到评论按钮")
                return False

            # 等待评论区打开
            time.sleep(2.5)

            # 2. 逐条阅读评论
            logger.info("📖 步骤2: 逐条阅读评论...")
            comment_read_count = 0

            if not self.driver:
                logger.warning("⚠️ Driver为空，无法读取评论")
                return False

            try:
                # 查找评论列表元素
                comment_list_selectors = [
                    "//androidx.recyclerview.widget.RecyclerView",
                    "//android.widget.ListView",
                    "//android.widget.ScrollView",
                ]

                comment_items = []
                try:
                    # 尝试查找评论列表容器
                    comment_list = self.driver.find_element(By.XPATH, comment_list_selectors[0])
                    if comment_list and comment_list.is_displayed():
                        comment_items = comment_list.find_elements(By.XPATH, ".//android.widget.TextView")
                except:
                    try:
                        # 备用查找方式
                        comment_items = self.driver.find_elements(By.XPATH, "//android.widget.TextView[contains(@text, '评论')] | //android.widget.TextView[contains(@text, '回复')] | //android.widget.TextView[@text and string-length(@text) > 2]")
                    except:
                        logger.warning("⚠️ 无法找到评论元素")
                        return False

                logger.info(f"📖 找到 {len(comment_items)} 个评论相关元素")

                for i, comment_item in enumerate(comment_items):
                    try:
                        comment_text = comment_item.text
                        if comment_text and len(comment_text.strip()) > 2 and '评论' not in comment_text and '回复' not in comment_text:
                            logger.info(f"   [{i+1}] {comment_text[:50]}{'...' if len(comment_text) > 50 else ''}")
                            comment_read_count += 1
                            time.sleep(0.5)  # 模拟阅读时间
                    except:
                        continue

                logger.info(f"📖 总共阅读了 {comment_read_count} 条评论")

            except Exception as e:
                logger.warning(f"⚠️ 逐条阅读评论时出错: {e}")
                logger.info("   继续滑动查看更多评论...")

                # 如果逐条阅读失败，则滑动浏览评论区
                for scroll_round in range(3):
                    core_utils.swipe_down_humanized(distance_ratio=0.3)
                    time.sleep(1.0)
                    logger.info(f"   滑动浏览评论区 {scroll_round + 1}/3")

            # 3. 关闭评论区
            logger.info("📝 步骤3: 关闭评论区")
            self.driver.press_keycode(4)  # Back键
            time.sleep(1.0)

            logger.info("=" * 60)
            return True

        except Exception as e:
            logger.error(f"❌ 阅读评论异常: {e}")
            # 尝试关闭评论区
            try:
                self.driver.press_keycode(4)
            except:
                pass
            return False

    def perform_comment_with_scroll(self, comment_text: str) -> bool:
        """
        进入评论区 → 滑动3-6次 → 留言 → 关闭
        
        Args:
            comment_text: 评论内容
            
        Returns:
            bool: 评论是否成功
        """
        try:
            logger.info("=" * 60)
            logger.info(f"💬 开始评论操作（含滑动）: {comment_text}")
            
            # 1. 打开评论区
            logger.info("📝 步骤1: 打开评论面板")
            comment_button_found = False
            
            comment_selectors = [
                {"by": "xpath", "value": "//android.widget.ImageView[@content-desc and contains(@content-desc, '评论')]"},
                {"by": "xpath", "value": "//android.widget.LinearLayout[@content-desc and contains(@content-desc, '评论')]"},
                {"by": "id", "value": "com.ss.android.ugc.aweme:id/eiz"},
                {"by": "id", "value": "com.ss.android.ugc.aweme:id/a3p"},
            ]
            
            from appium.webdriver.common.appiumby import AppiumBy as By
            
            for selector in comment_selectors:
                by_type = By.XPATH if selector['by'] == 'xpath' else By.ID
                if core_utils.wait_and_click(by_type, selector['value'], timeout=3):
                    logger.info("✅ 评论按钮已点击")
                    comment_button_found = True
                    break
            
            if not comment_button_found:
                logger.warning("⚠️ 未找到评论按钮")
                return False
            
            # 等待评论区打开
            time.sleep(2.5)
            
            # 2. 随机滑动 2-5 次
            scroll_times = random.randint(2, 5)
            logger.info(f"📜 步骤2: 评论区滑动 {scroll_times} 次")
            
            for i in range(scroll_times):
                # 随机上滑或下滑
                if random.random() < 0.5:
                    core_utils.swipe_up_humanized(distance_ratio=0.3)
                    logger.info(f"   [{i+1}/{scroll_times}] 上滑")
                else:
                    core_utils.swipe_down_humanized(distance_ratio=0.3)
                    logger.info(f"   [{i+1}/{scroll_times}] 下滑")
                
                time.sleep(random.uniform(0.5, 1.2))
            
            self.stats['comment_scrolls'] += scroll_times
            
            # 3. 查找并点击输入框
            logger.info("📝 步骤3: 查找评论输入框")
            time.sleep(1.0)
            
            input_selectors = [
                {"by": "xpath", "value": "//android.widget.EditText"},
                {"by": "id", "value": "com.ss.android.ugc.aweme:id/ebm"},
                {"by": "xpath", "value": "//android.widget.EditText[contains(@text, '友善')]"},
            ]
            
            input_element = None
            for selector in input_selectors:
                by_type = By.XPATH if selector['by'] == 'xpath' else By.ID
                input_element = core_utils.find_element_safe(by_type, selector['value'], timeout=2)
                if input_element:
                    logger.info("✅ 找到评论输入框")
                    break
            
            if not input_element:
                logger.warning("⚠️ 未找到输入框")
                self.driver.press_keycode(4)  # 返回
                return False
            
            # 4. 点击激活输入框
            try:
                input_element.click()
                time.sleep(1.5)
            except:
                pass
            
            # 5. 输入评论
            logger.info(f"📝 步骤4: 输入评论: {comment_text}")
            time.sleep(0.5)
            
            # 重新查找输入框（避免元素过期）
            for selector in input_selectors:
                by_type = By.XPATH if selector['by'] == 'xpath' else By.ID
                fresh_input = core_utils.find_element_safe(by_type, selector['value'], timeout=2)
                if fresh_input:
                    try:
                        fresh_input.send_keys(comment_text)
                        logger.info("✅ 评论内容已输入")
                        break
                    except:
                        continue
            else:
                logger.warning("⚠️ 输入评论失败")
                self.driver.press_keycode(4)
                return False
            
            time.sleep(1.0)
            
            # 6. 点击发送按钮
            logger.info("📝 步骤5: 点击发送按钮")
            send_selectors = [
                {"by": "xpath", "value": "//android.widget.TextView[@text='发送']"},
                {"by": "xpath", "value": "//android.widget.Button[@text='发送']"},
                {"by": "id", "value": "com.ss.android.ugc.aweme:id/aot"},
            ]
            
            send_success = False
            for selector in send_selectors:
                by_type = By.XPATH if selector['by'] == 'xpath' else By.ID
                if core_utils.wait_and_click(by_type, selector['value'], timeout=2):
                    logger.info("✅ 评论发送成功")
                    send_success = True
                    break
            
            if not send_success:
                logger.warning("⚠️ 未找到发送按钮")
                self.driver.press_keycode(4)
                return False
            
            time.sleep(2.0)
            
            # 7. 关闭评论区
            logger.info("📝 步骤6: 关闭评论区")
            self.driver.press_keycode(4)  # Back键
            time.sleep(1.0)
            
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"❌ 评论操作异常: {e}")
            traceback.print_exc()
            # 尝试关闭评论区
            try:
                self.driver.press_keycode(4)
            except:
                pass
            return False
    
    def perform_target_video_interactions(self, interaction_data: dict) -> None:
        """
        目标视频的完整交互流程（新规格）

        流程:
        1. 等待视频播放（30-80%，假设视频100秒）
        2. 进入评论区，逐条阅读所有评论
        3. 留下随机预设评论
        4. 关闭评论区
        5. 33% 概率收藏
        6. 等待2-3秒后切换到下一个视频

        Args:
            interaction_data: 视频互动数据
        """
        try:
            logger.info("=" * 60)
            logger.info("🎬 开始目标视频交互流程")
            logger.info("=" * 60)

            # 显示当前视频信息
            if interaction_data:
                logger.info(f"📊 目标视频互动状态: 点赞{interaction_data['like_text']} 评论{interaction_data['comment_text']}")

            # 1. 等待视频播放（随机7-30秒，反自动化）
            # 不再使用百分比假设，而是直接使用安全的随机时间范围
            play_time = random.uniform(7, 30)
            logger.info(f"\n⏱️ 随机播放等待: {play_time:.1f}秒 (范围:7-30s)...")
            time.sleep(play_time)

            # 2. 进入评论区，逐条阅读所有评论
            logger.info(f"\n📖 开始阅读评论区...")
            self.read_all_comments()

            # 3. 留下随机预设评论
            logger.info(f"\n💬 准备留下评论...")
            comment_text = random.choice(self.comments)
            self.stats['comment_attempts'] += 1

            if self.perform_comment_with_scroll(comment_text):
                self.stats['comment_success'] += 1
                self.stats['comments_posted'].append({
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'content': comment_text
                })
                logger.info("✅ 评论成功")
                # 评论成功后，perform_comment_with_scroll 内部已经关闭了评论区
            else:
                logger.warning("⚠️ 评论失败")
                # 关键修复：评论失败时，必须手动关闭评论区
                logger.info("   尝试关闭评论区...")
                self.driver.press_keycode(4)  # Back键
                time.sleep(1.0)

            time.sleep(random.uniform(1.0, 2.0))

            # 收藏（概率来自配置）
            fav_prob = self.prob_config.get('favorite', 0.33)
            if random.random() < fav_prob:
                logger.info(f"\n🎲 命中收藏概率 ({int(fav_prob*100)}%)")
                self.stats['favorite_attempts'] += 1

                if interactions.favorite_current_video():
                    self.stats['favorite_success'] += 1
                    logger.info("✅ 收藏成功")
                else:
                    logger.warning("⚠️ 收藏失败")

                time.sleep(random.uniform(0.5, 1.0))
            else:
                logger.info("\n   跳过收藏")

            # 5. 等待2-3秒后切换到下一个视频
            wait_time = random.uniform(2, 3)
            logger.info(f"\n⏰ 等待 {wait_time:.1f}秒后切换视频...")
            time.sleep(wait_time)

            logger.info("=" * 60)
            logger.info("✅ 目标视频交互流程完成")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 目标视频交互流程异常: {e}")
            traceback.print_exc()

    def perform_video_interactions(self, interaction_data: Optional[dict] = None) -> None:
        """
        兼容旧版本的方法（已弃用，保留以防兼容性问题）
        现在直接调用 perform_target_video_interactions

        Args:
            interaction_data: 视频互动数据
        """
        if interaction_data:
            self.perform_target_video_interactions(interaction_data)
    
    def swipe_to_next_video(self):
        """滑动到下一个视频"""
        try:
            logger.info("\n👆 上滑切换到下一个视频")
            core_utils.swipe_up_humanized()
            time.sleep(random.uniform(0.8, 1.5))
        except Exception as e:
            logger.error(f"❌ 上滑失败: {e}")
    
    
    def run_browse_loop(self, runtime_seconds: Optional[int] = None):
        """
        执行浏览循环（独立方法，可被外部调用）
        
        流程（简洁版）：
        1. 检查是否常规视频（有点赞/评论按钮）→ 不是就滑动到下一个
        2. 按概率触发"不感兴趣"跳过
        3. 随机播放7-30秒
        4. 按概率点赞
        5. 按概率评论（打开→滑动2-5次→写评论→提交→关闭）
        6. 按概率收藏
        7. 滑动到下一个
        
        Args:
            runtime_seconds: 运行时间（秒），如果为None则使用self.runtime_seconds
        """
        if runtime_seconds is None:
            runtime_seconds = self.runtime_seconds
        
        logger.info("\n" + "=" * 60)
        logger.info("🎬 开始随机浏览循环")
        logger.info(f"⏱️  运行时长: {runtime_seconds}秒")
        logger.info("=" * 60)
        
        self.start_time = time.time()
        
        consecutive_failures = 0  # 连续操作失败计数
        
        while True:
            # 检查时间限制
            elapsed = time.time() - self.start_time
            remaining = int(runtime_seconds - elapsed)
            
            if elapsed >= runtime_seconds:
                logger.info(f"\n⏰ 已达到运行时间限制 ({runtime_seconds}秒)")
                break
            
            self.stats['videos_browsed'] += 1
            video_num = self.stats['videos_browsed']
            
            logger.info(f"\n{'='*50}")
            logger.info(f"📺 视频 #{video_num} | 剩余: {remaining}秒")
            logger.info("=" * 50)
            
            # 等待视频加载
            time.sleep(1.5)

            # 先检测是否为直播入口视频（直播没有常规交互按钮，需直接划过）
            if self._is_live_entrance_video():
                logger.info("🔴 检测到直播入口视频，直接划过")
                self.stats['videos_skipped'] += 1
                self.swipe_to_next_video()
                continue

            # ========== 核心判断：是否为常规视频（使用原有方法）==========
            interaction_data = self.get_video_interaction_data()
            has_like = interaction_data.get('has_like_button', False)
            has_comment = interaction_data.get('has_comment_button', False)
            
            # 只要缺少任一按钮，直接划过
            if not (has_like and has_comment):
                logger.info("⏭️ 非常规视频（无交互按钮），跳过")
                self.stats['videos_skipped'] += 1
                consecutive_failures += 1
                
                # 连续3次失败，可能界面异常，等待后重试
                if consecutive_failures >= 3:
                    logger.warning(f"⚠️ 连续{consecutive_failures}次未找到按钮，等待2秒后继续...")
                    time.sleep(2.0)
                    consecutive_failures = 0
                
                self.swipe_to_next_video()
                continue
            
            # 找到常规视频，重置失败计数
            consecutive_failures = 0
            logger.info(f"✅ 常规视频 | 点赞:{interaction_data.get('like_text', '?')} 评论:{interaction_data.get('comment_text', '?')}")
            
            # ========== 按概率触发"不感兴趣"跳过 ==========
            skip_prob = self.prob_config.get('skip_video', 0.22)
            if random.random() < skip_prob:
                logger.info(f"🎲 命中跳过概率 ({int(skip_prob*100)}%)，模拟不感兴趣")
                self.stats['videos_skipped'] += 1
                self.swipe_to_next_video()
                continue
            
            # ========== 随机播放5-15秒（每5秒检测播放状态）==========
            play_time = random.uniform(5, 15)
            logger.info(f"⏱️  播放视频 {play_time:.1f}秒...")
            
            # 分段等待，每5秒检测一次播放状态
            elapsed_play = 0
            while elapsed_play < play_time:
                wait_chunk = min(5.0, play_time - elapsed_play)
                time.sleep(wait_chunk)
                elapsed_play += wait_chunk
                
                # 检测视频是否暂停（通过查找播放按钮或暂停图标）
                if elapsed_play < play_time:  # 最后一次不检测
                    try:
                        # 检测是否有暂停状态的指示（播放按钮出现说明视频暂停了）
                        pause_indicators = [
                            'new UiSelector().descriptionContains("播放")',
                            'new UiSelector().descriptionContains("暂停")',
                        ]
                        is_paused = False
                        for selector in pause_indicators:
                            elem = core_utils.find_element_safe(
                                By.ANDROID_UIAUTOMATOR, selector, timeout=0.5
                            )
                            if elem:
                                is_paused = True
                                break
                        
                        if is_paused:
                            logger.info("   ⚠️ 检测到视频暂停，点击屏幕恢复播放")
                            # 点击屏幕中心恢复播放
                            window_size = self.driver.get_window_size()
                            center_x = window_size['width'] // 2
                            center_y = window_size['height'] // 2
                            self.driver.tap([(center_x, center_y)])
                            time.sleep(0.5)
                    except:
                        pass  # 检测失败不影响主流程
            
            # ========== 按概率点赞 ==========
            like_prob = self.prob_config.get('like', 0.66)
            if random.random() < like_prob:
                logger.info(f"👍 尝试点赞 ({int(like_prob*100)}%)")
                self.stats['like_attempts'] += 1
                if interactions.like_current_video():
                    self.stats['like_success'] += 1
                    logger.info("   ✅ 点赞成功")
                else:
                    logger.info("   ⚠️ 点赞失败")
                    consecutive_failures += 1
                time.sleep(random.uniform(0.3, 0.8))
            
            # ========== 按概率评论 ==========
            comment_prob = self.prob_config.get('comment', 0.66)
            if random.random() < comment_prob:
                logger.info(f"💬 尝试评论 ({int(comment_prob*100)}%)")
                comment_text = random.choice(self.comments)
                self.stats['comment_attempts'] += 1
                
                if self.perform_comment_with_scroll(comment_text):
                    self.stats['comment_success'] += 1
                    self.stats['comments_posted'].append({
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'content': comment_text
                    })
                    logger.info("   ✅ 评论成功")
                else:
                    logger.info("   ⚠️ 评论失败")
                    consecutive_failures += 1
                    try:
                        self.driver.press_keycode(4)
                        time.sleep(0.5)
                    except:
                        pass
                
                time.sleep(random.uniform(0.3, 0.8))
            
            # ========== 按概率收藏 ==========
            fav_prob = self.prob_config.get('favorite', 0.33)
            if random.random() < fav_prob:
                logger.info(f"⭐ 尝试收藏 ({int(fav_prob*100)}%)")
                self.stats['favorite_attempts'] += 1
                if interactions.favorite_current_video():
                    self.stats['favorite_success'] += 1
                    logger.info("   ✅ 收藏成功")
                else:
                    logger.info("   ⚠️ 收藏失败")
                    consecutive_failures += 1
                time.sleep(random.uniform(0.3, 0.8))
            
            # 连续3次操作失败，重新检查视频类型
            if consecutive_failures >= 3:
                logger.warning(f"⚠️ 连续{consecutive_failures}次操作失败，重新检查视频类型...")
                consecutive_failures = 0
                # 不滑动，在下一轮循环重新检测当前视频
                continue
            
            # ========== 滑动到下一个视频 ==========
            self.swipe_to_next_video()

    def _is_live_entrance_video(self) -> bool:
        """检测当前视频是否为直播入口/直播间视频"""
        try:
            keywords = ["进入直播间"]
            from appium.webdriver.common.appiumby import AppiumBy as By

            for kw in keywords:
                elem = core_utils.find_element_safe(
                    By.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().textContains("{kw}")',
                    timeout=0.3
                )
                if elem:
                    logger.info(f"   🔍 文本提示直播: {kw}")
                    return True

                elem = core_utils.find_element_safe(
                    By.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().descriptionContains("{kw}")',
                    timeout=0.3
                )
                if elem:
                    logger.info(f"   🔍 描述提示直播: {kw}")
                    return True

            return False

        except Exception as e:
            logger.debug(f"直播检测异常: {e}")
            return False
    
    def run(self) -> bool:
        """
        运行浏览会话（主循环）
        
        Returns:
            bool: 运行是否成功
        """
        try:
            # 1. 环境检查
            if not self.check_environment():
                return False
            
            # 2. 连接设备
            logger.info("\n📱 正在连接设备...")
            self.driver = app_driver.connect(max_retries=3)
            if not self.driver:
                logger.error("❌ 设备连接失败")
                return False
            
            logger.info("✅ 设备连接成功")
            
            # 初始化工具模块
            interactions.init_interactions(self.driver)
            core_utils.init_utils(self.driver)
            
            # 3. 强制启动抖音
            if not self.force_start_douyin():
                return False
            
            # 4. 确保在推荐页面并进入视频
            if not self.ensure_in_recommendation_tab_and_click_video():
                logger.warning("⚠️ 无法进入视频模式，继续执行...")
            
            # 5. 执行浏览循环
            self.run_browse_loop()
            
            logger.info("\n🧹 正在清理资源...")
            return True
            
        except KeyboardInterrupt:
            logger.info("\n⚠️ 用户中断程序")
            return False
        except Exception as e:
            logger.error(f"\n❌ 程序运行异常: {e}")
            traceback.print_exc()
            return False
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """清理资源并显示统计"""
        try:
            # 显示统计报告
            self._display_stats()

            # 等待10秒让用户查看统计信息
            logger.info("\n⏰ 程序将在10秒后自动关闭...")
            for i in range(10, 0, -1):
                logger.info(f"   倒计时: {i}秒")
                time.sleep(1)

            # 关闭 driver
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("✅ Driver 已关闭")
                except Exception as e:
                    logger.warning(f"⚠️ Driver 关闭异常: {e}")

        except Exception as e:
            logger.error(f"❌ 清理过程异常: {e}")
    
    def _display_stats(self):
        """显示统计报告"""
        try:
            elapsed = int(time.time() - self.start_time) if self.start_time else 0
            
            logger.info("\n" + "=" * 60)
            logger.info(f"📊 运行统计报告 (耗时: {elapsed}秒)")
            logger.info("=" * 60)
            
            # 基础统计
            target_videos = self.stats['comment_attempts']  # 目标视频数 = 尝试评论的视频数
            regular_videos = self.stats['videos_browsed'] - target_videos

            logger.info(f"📺 总浏览视频: {self.stats['videos_browsed']}")
            logger.info(f"   ├─ 目标视频(评论≥5): {target_videos}")
            logger.info(f"   ├─ 常规视频(评论<5): {regular_videos}")
            logger.info(f"   ├─ 直播视频: {self.stats['live_videos']}")
            logger.info(f"   └─ 跳过视频(22%): {self.stats['videos_skipped']}")

            # 交互统计
            logger.info("\n💫 目标视频交互统计:")

            def format_rate(success, total):
                if total == 0:
                    return "未尝试"
                rate = (success / total) * 100
                return f"{success}/{total} ({rate:.1f}%)"

            logger.info(f"   💬 评论: {format_rate(self.stats['comment_success'], self.stats['comment_attempts'])}")
            logger.info(f"   ⭐ 收藏: {format_rate(self.stats['favorite_success'], self.stats['favorite_attempts'])}")
            logger.info(f"   📖 评论区阅读: {self.stats['comment_scrolls']} 次滑动")
            
            # 评论记录
            if self.stats['comments_posted']:
                logger.info("\n📝 评论记录:")
                for comment in self.stats['comments_posted']:
                    logger.info(f"   [{comment['time']}] {comment['content']}")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ 统计报告生成失败: {e}")


_current_session = None

def _signal_handler(signum, frame):
    """信号处理器 - 确保优雅关闭"""
    logger.warning(f"\n⚠️ 收到中断信号 ({signum})，正在保存日志并退出...")
    logger.flush()
    
    global _current_session
    if _current_session:
        try:
            _current_session._cleanup()
        except Exception as e:
            logger.error(f"清理失败: {e}")
    
    logger.info("✅ 日志已保存")
    logger.flush()
    sys.exit(1)

def main():
    """主函数"""
    global _current_session
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    
    try:
        logger.info("\n" + "🚀" * 30)
        logger.info("抖音随机浏览器 - 启动")
        logger.info("🚀" * 30)
        
        # 创建并运行会话
        _current_session = RandomBrowseSession(runtime_seconds=180)
        success = _current_session.run()
        
        logger.flush()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.warning("⚠️ 用户中断程序")
        logger.flush()
        return 1
        
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        traceback.print_exc()
        logger.flush()
        return 1
    
    finally:
        logger.info("程序结束，日志已保存")
        logger.flush()


if __name__ == "__main__":
    exit(main())
