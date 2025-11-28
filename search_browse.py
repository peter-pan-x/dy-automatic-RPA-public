"""
抖音搜索浏览模块
基于关键词搜索后进行随机浏览

功能流程:
1. 加载 hot_words 文件夹中的关键词
2. 搜索随机关键词
3. 切换到视频 tab
4. 点击四宫格视频
5. 执行随机浏览
"""

import sys
import os
import time
import random
import signal
import traceback
from typing import List, Optional
from datetime import datetime
import yaml

# 添加项目根目录到路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 导入核心模块
from src import app_driver, interactions, core_utils
from src.logger import setup_logger
from appium.webdriver.common.appiumby import AppiumBy as By

# 导入 RandomBrowseSession 用于复用浏览功能
from random_browse import RandomBrowseSession

CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.yaml')

# 导入评论扫描模块（LLM智能回复）
from test_comment_text import scan_comments_loop, REPLIED_COMMENTS, INTERCEPT_KEYWORDS

# 初始化日志
logger = setup_logger("search_browse", log_dir="logs")


class SearchBrowseSession:
    """搜索浏览会话管理器 - 拦截模式（LLM智能回复）"""
    
    def __init__(self):
        """
        初始化会话（通过目标评论数量结束）
        """
        self.driver = None
        
        # 读取目标评论数量范围
        self.target_comment_min, self.target_comment_max = self._load_search_target_range()
        self.target_replies_goal = random.randint(self.target_comment_min, self.target_comment_max)
        
        # 加载关键词
        self.keywords = self._load_keywords()
        
        # 加载概率配置
        self.prob_config = self._load_probability_config()
        
        # 加载视频过滤规则
        self.video_filter = self._load_video_filter()
        
        # 统计数据
        self.stats = {
            "videos_watched": 0,
            "comments_read": 0,
            "replies_sent": 0,
            "likes_given": 0,
        }
        
        # 创建浏览会话实例（用于复用部分功能）
        self.browse_session = RandomBrowseSession()
        
        logger.info("=" * 60)
        logger.info("🔍 Search Browse Session 初始化完成 (LLM智能回复模式)")
        logger.info(f"🎯 本次目标回复: {self.target_replies_goal} 条 (范围 {self.target_comment_min}-{self.target_comment_max})")
        logger.info(f"📚 加载了 {len(self.keywords)} 个搜索关键词")
        logger.info(f"🎯 拦截关键词: {INTERCEPT_KEYWORDS}")
        logger.info("=" * 60)
    
    def _load_search_browse_config(self) -> dict:
        """加载搜索浏览模块的完整配置"""
        default = {
            'target_min': 55, 'target_max': 222,
            'like_prob': 0.8, 'comment_prob': 1.0, 'favorite_prob': 0.2,
            'min_likes': 10, 'min_comments': 3
        }
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f) or {}
            sb_cfg = cfg.get('search_browse', {})
            prob_cfg = sb_cfg.get('probability', {})
            filter_cfg = sb_cfg.get('video_filter', {})
            return {
                'target_min': sb_cfg.get('target_comment_min', default['target_min']),
                'target_max': sb_cfg.get('target_comment_max', default['target_max']),
                'like_prob': prob_cfg.get('like', 80) / 100,
                'comment_prob': prob_cfg.get('comment', 100) / 100,
                'favorite_prob': prob_cfg.get('favorite', 20) / 100,
                'min_likes': filter_cfg.get('min_likes', default['min_likes']),
                'min_comments': filter_cfg.get('min_comments', default['min_comments']),
            }
        except Exception as e:
            logger.warning(f"⚠️ 搜索浏览配置读取失败，使用默认值: {e}")
            return default

    def _load_search_target_range(self) -> tuple[int, int]:
        cfg = self._load_search_browse_config()
        min_val, max_val = cfg['target_min'], cfg['target_max']
        if min_val > max_val:
            min_val, max_val = max_val, min_val
        return min_val, max_val

    def _load_probability_config(self) -> dict:
        """加载互动概率配置"""
        cfg = self._load_search_browse_config()
        return {
            'like': cfg['like_prob'],
            'comment': cfg['comment_prob'],
            'favorite': cfg['favorite_prob'],
        }

    def _load_video_filter(self) -> dict:
        """加载有价值视频判定规则"""
        cfg = self._load_search_browse_config()
        return {
            'min_likes': cfg['min_likes'],
            'min_comments': cfg['min_comments'],
        }

    def _load_keywords(self) -> List[str]:
        """
        从 hot_words 文件夹加载所有关键词
        
        Returns:
            List[str]: 关键词列表
        """
        keywords = []
        hot_words_dir = os.path.join(os.path.dirname(__file__), 'hot_words')
        
        try:
            # 遍历所有 txt 文件
            for filename in os.listdir(hot_words_dir):
                if filename.endswith('.txt'):
                    filepath = os.path.join(hot_words_dir, filename)
                    logger.info(f"   加载文件: {filename}")
                    
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 分词（空格分隔）
                        words = content.split()
                        # 过滤空字符和无效词
                        words = [w.strip() for w in words if w.strip() and len(w.strip()) > 1]
                        keywords.extend(words)
            
            # 去重
            keywords = list(set(keywords))
            
            if not keywords:
                logger.warning("⚠️ 未加载到关键词，使用默认关键词")
                keywords = ["养生茶", "黄芪", "枸杞", "红枣", "蜂蜜"]
            
            logger.info(f"✅ 加载了 {len(keywords)} 条评论")
            return keywords
            
        except Exception as e:
            logger.error(f"❌ 加载关键词失败: {e}")
            return ["养生茶", "黄芪", "枸杞", "红枣", "蜂蜜"]
    
    def get_random_keyword(self) -> str:
        """随机选择一个关键词"""
        return random.choice(self.keywords)
    
    def perform_search(self, keyword: str) -> bool:
        """
        执行搜索操作
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            bool: 搜索是否成功
        """
        try:
            logger.info(f"\n🔍 开始搜索关键词: {keyword}")
            
            # 1. 点击搜索框（首页右上角放大镜图标）
            logger.info("   步骤1: 查找搜索入口")
            
            # 方案A: 优先使用坐标点击（右上角放大镜 - 最快最可靠）
            logger.info("      方案A: 尝试坐标点击（右上角放大镜）")
            try:
                window_size = self.driver.get_window_size()
                width = window_size['width']
                height = window_size['height']
                
                # 右上角搜索图标位置（放大镜按钮）
                x = int(width * 0.9)  # 右侧 90% 处
                y = int(height * 0.05)  # 顶部 5% 处
                
                logger.info(f"      屏幕尺寸: {width}x{height}")
                logger.info(f"      点击坐标: ({x}, {y})")
                self.driver.tap([(x, y)])
                time.sleep(2.0)
                
                # 验证是否成功（检查是否有输入框出现）
                input_check = core_utils.find_element_safe(By.XPATH, "//android.widget.EditText", timeout=1)
                if input_check:
                    logger.info("   ✅ 打开搜索页面（坐标点击）")
                    search_clicked = True
                else:
                    logger.warning("      坐标点击后未检测到输入框，尝试备用方案")
                    search_clicked = False
            except Exception as e:
                logger.warning(f"      坐标点击失败: {e}，尝试备用方案")
                search_clicked = False
            
            # 方案B: 如果坐标点击失败，尝试选择器（降低timeout加快速度）
            if not search_clicked:
                logger.info("      方案B: 尝试UI选择器")
                search_selectors = [
                    {"by": "xpath", "value": "//android.widget.ImageView[@content-desc='搜索']"},
                    {"by": "id", "value": "com.ss.android.ugc.aweme:id/a1o"},
                    {"by": "xpath", "value": "//android.widget.EditText[contains(@text, '搜索')]"},
                ]
                
                for idx, selector in enumerate(search_selectors, 1):
                    by_type = By.XPATH if selector['by'] == 'xpath' else By.ID
                    logger.info(f"      尝试选择器 [{idx}/{len(search_selectors)}]: {selector['value'][:40]}...")
                    if core_utils.wait_and_click(by_type, selector['value'], timeout=1):  # 降低到1秒
                        logger.info("   ✅ 打开搜索页面（选择器）")
                        time.sleep(2.0)
                        search_clicked = True
                        break
            
            if not search_clicked:
                logger.error("   ❌ 未找到搜索入口（坐标和选择器都失败）")
                return False
            
            # 2. 输入关键词
            logger.info("   步骤2: 查找搜索输入框")
            input_selectors = [
                {"by": "id", "value": "com.ss.android.ugc.aweme:id/et_search_kw"},
                {"by": "xpath", "value": "//android.widget.EditText"},
                {"by": "xpath", "value": "//android.widget.EditText[contains(@text, '搜索')]"},
                {"by": "xpath", "value": "//android.widget.EditText[contains(@resource-id, 'search')]"},
            ]
            
            input_element = None
            for idx, selector in enumerate(input_selectors, 1):
                by_type = By.XPATH if selector['by'] == 'xpath' else By.ID
                logger.info(f"      尝试选择器 [{idx}/{len(input_selectors)}]")
                input_element = core_utils.find_element_safe(by_type, selector['value'], timeout=3)
                if input_element:
                    logger.info("   ✅ 找到搜索输入框")
                    break
            
            if not input_element:
                logger.error("   ❌ 未找到搜索输入框")
                return False
            
            # 清空并输入
            logger.info("   步骤3: 输入关键词")
            input_element.clear()
            time.sleep(0.5)
            input_element.send_keys(keyword)
            logger.info(f"   ✅ 已输入关键词: {keyword}")
            time.sleep(1.0)
            
            # 3. 提交搜索（优先点击搜索按钮，备用回车键）
            logger.info("   步骤4: 提交搜索")
            
            # 方案A: 点击输入框右边的"搜索"按钮（更快）
            search_button_clicked = False
            search_button_selectors = [
                {"by": "xpath", "value": "//android.widget.TextView[@text='搜索']"},
                {"by": "xpath", "value": "//android.widget.Button[@text='搜索']"},
                {"by": "xpath", "value": "//android.widget.TextView[contains(@text, '搜索')]"},
            ]
            
            for idx, selector in enumerate(search_button_selectors, 1):
                by_type = By.XPATH if selector['by'] == 'xpath' else By.ID
                if core_utils.wait_and_click(by_type, selector['value'], timeout=1):
                    logger.info("   ✅ 搜索已提交（点击按钮）")
                    search_button_clicked = True
                    break
            
            # 方案B: 如果没找到按钮，使用坐标点击（输入框右侧）
            if not search_button_clicked:
                logger.info("      未找到搜索按钮，尝试坐标点击")
                try:
                    window_size = self.driver.get_window_size()
                    width = window_size['width']
                    
                    # 搜索按钮通常在输入框右侧，屏幕右边缘
                    x = int(width * 0.92)  # 右侧 92% 处
                    y = int(window_size['height'] * 0.08)  # 顶部 8% 处（搜索框位置）
                    
                    logger.info(f"      点击坐标: ({x}, {y})")
                    self.driver.tap([(x, y)])
                    logger.info("   ✅ 搜索已提交（坐标点击）")
                    search_button_clicked = True
                except Exception as e:
                    logger.warning(f"      坐标点击失败: {e}")
            
            # 方案C: 最后备用方案 - 按回车键
            if not search_button_clicked:
                logger.info("      使用回车键提交")
                self.driver.press_keycode(66)  # Enter key
                logger.info("   ✅ 搜索已提交（回车键）")
            
            time.sleep(3.0)  # 等待搜索结果加载
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            traceback.print_exc()
            return False
    
    def switch_to_video_tab(self) -> bool:
        """
        切换到视频 tab（优化速度版）
        
        Returns:
            bool: 切换是否成功
        """
        try:
            logger.info("\n📹 切换到视频 tab...")
            
            # 设置较短的隐式等待时间
            self.driver.implicitly_wait(1)
            
            tab_clicked = False
            
            # 1. 直接尝试最可靠的选择器（不遍历多个）
            try:
                element = self.driver.find_element(
                    By.ANDROID_UIAUTOMATOR, 
                    'new UiSelector().text("视频")'
                )
                if element:
                    element.click()
                    logger.info("   ✅ 已点击视频 tab")
                    tab_clicked = True
            except:
                pass
            
            # 2. 备用：XPath
            if not tab_clicked:
                try:
                    element = self.driver.find_element(By.XPATH, "//android.widget.TextView[@text='视频']")
                    if element:
                        element.click()
                        logger.info("   ✅ 已点击视频 tab (XPath)")
                        tab_clicked = True
                except:
                    pass
            
            # 3. 坐标点击（最后备用）
            if not tab_clicked:
                logger.info("   使用坐标点击...")
                window_size = self.driver.get_window_size()
                x = int(window_size['width'] * 0.58)
                y = int(window_size['height'] * 0.15)
                self.driver.tap([(x, y)])
                logger.info(f"   ✅ 坐标点击 ({x}, {y})")
                tab_clicked = True
            
            # 恢复默认等待时间
            self.driver.implicitly_wait(10)
            
            # 等待Tab加载（减少等待时间）
            time.sleep(1.5)
            
            # 验证是否真的切换成功（可选：检查是否还在商品页）
            # 这里我们简单返回点击状态，但在主流程中会检查
            if not tab_clicked:
                logger.error("❌ 未能找到或点击视频 tab")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"❌ 切换视频 tab 失败: {e}")
            return False
    
    def click_grid_video(self) -> bool:
        """
        点击搜索结果页的视频（随机选择）
        
        搜索结果页通常是滚动的视频列表（可能是2列或单列）
        
        Returns:
            bool: 点击是否成功
        """
        try:
            logger.info("\n🎬 点击搜索结果视频...")
            
            # 等待视频加载
            time.sleep(2.0)
            
            # 获取屏幕尺寸
            window_size = self.driver.get_window_size()
            width = window_size['width']
            height = window_size['height']
            
            # 搜索结果页的视频分布
            # 通常在屏幕中部有多个视频，可能是2列或单列布局
            # 我们随机选择一个位置点击
            
            # 定义可点击的区域（多个视频位置）
            video_positions = [
                (0.25, 0.35),  # 左上
                (0.75, 0.35),  # 右上
                (0.25, 0.50),  # 左中
                (0.75, 0.50),  # 右中
                (0.50, 0.40),  # 中间（单列情况）
            ]
            
            # 随机选择一个位置
            pos_x_ratio, pos_y_ratio = random.choice(video_positions)
            x = int(width * pos_x_ratio)
            y = int(height * pos_y_ratio)
            
            logger.info(f"   屏幕尺寸: {width}x{height}")
            logger.info(f"   随机选择位置: ({pos_x_ratio:.0%}, {pos_y_ratio:.0%})")
            logger.info(f"   点击坐标: ({x}, {y})")
            
            # 使用 driver.tap() 点击
            self.driver.tap([(x, y)])
            
            logger.info("✅ 已点击视频")
            time.sleep(3.0)  # 等待视频打开
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 点击视频失败: {e}")
            traceback.print_exc()
            return False
    
    def _is_in_fullscreen_mode(self) -> bool:
        """
        验证是否真正进入了全屏视频播放模式
        
        全屏模式特征：
        1. 单个视频占据屏幕90%以上
        2. 有点赞、收藏、评论按钮（位于屏幕右侧）
        3. 没有搜索Tab栏
        
        Returns:
            bool: 是否在全屏模式
        """
        try:
            # 关键检测：Tab栏是否消失 + 点赞按钮是否在右侧
            
            # 1. 检查搜索Tab栏是否存在（存在=卡片界面）
            tab_elem = core_utils.find_element_safe(
                By.ANDROID_UIAUTOMATOR, 
                'new UiSelector().text("视频")',
                timeout=1
            )
            if tab_elem:
                logger.info("   ⚠️ 检测到'视频'Tab，仍在卡片界面")
                return False
            
            # 2. 检查点赞按钮位置（全屏=右侧，卡片=底部或卡片内）
            like_elem = core_utils.find_element_safe(
                By.ANDROID_UIAUTOMATOR,
                'new UiSelector().descriptionContains("赞")',
                timeout=2
            )
            
            if like_elem:
                location = like_elem.location
                size = self.driver.get_window_size()
                # 全屏模式：点赞按钮在屏幕右侧 (x > 70% 屏幕宽度)
                if location['x'] > size['width'] * 0.7:
                    logger.info(f"   ✅ 全屏确认：点赞按钮在右侧 (x={location['x']}, 屏幕宽={size['width']})")
                    return True
                else:
                    logger.info(f"   ⚠️ 点赞按钮位置异常 (x={location['x']}), 不在右侧")
                    return False
            else:
                logger.info("   ⚠️ 未找到点赞按钮")
                return False
            
        except Exception as e:
            logger.warning(f"   全屏检测异常: {e}")
            return False
    
    def run(self) -> bool:
        """
        运行搜索浏览会话
        
        Returns:
            bool: 运行是否成功
        """
        try:
            # 1. 环境检查（复用 browse_session）
            if not self.browse_session.check_environment():
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
            
            # 3. 共享 driver 给 browse_session（必须在启动抖音前）
            self.browse_session.driver = self.driver
            
            # 4. 启动抖音
            if not self.browse_session.force_start_douyin():
                logger.error("❌ 抖音启动失败")
                return False
            
            time.sleep(2.0)
            
            # 4. 选择随机关键词
            keyword = self.get_random_keyword()
            logger.info(f"\n🎲 选择的关键词: {keyword}")
            
            # 5. 执行搜索
            if not self.perform_search(keyword):
                return False
            
            # 6. 切换到视频 tab
            if not self.switch_to_video_tab():
                logger.error("❌ 无法切换到视频 tab，停止后续操作")
                return False
            
            # 7. 点击搜索结果视频（随机）
            if not self.click_grid_video():
                logger.error("❌ 无法点击视频，停止后续操作")
                return False
            
            # 8. 验证是否成功进入全屏视频播放模式（关键！）
            logger.info("\n🔍 验证是否进入全屏视频播放模式...")
            time.sleep(2.0)  # 等待页面加载
            
            # 最多尝试3次点击进入全屏
            max_attempts = 3
            for attempt in range(max_attempts):
                if self._is_in_fullscreen_mode():
                    logger.info("✅ 确认已进入全屏视频播放模式")
                    break
                else:
                    logger.warning(f"⚠️ 第{attempt+1}次：未进入全屏模式，尝试再次点击视频卡片...")
                    if attempt < max_attempts - 1:
                        self.click_grid_video()
                        time.sleep(2.0)
            else:
                logger.error("❌ 多次尝试仍未能进入全屏模式，停止后续操作")
                return False
            
            # 8. 确认进入视频列表页面
            logger.info("\n✅ 已进入视频列表，准备开始随机浏览...")
            time.sleep(2.0)
            
            logger.info("🎬" * 20)
            
            # 调用自定义的搜索结果浏览循环（通过目标评论数量结束）
            self.run_search_result_browse_loop()
            
            logger.info("\n🧹 正在清理资源...")
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

    def run_search_result_browse_loop(self):
        """
        执行搜索结果的专用浏览循环（通过目标评论数量结束）
        
        逻辑:
        1. 检查是否为目标视频
        2. 获取点赞/评论数进行筛选 (点赞<10 且 评论<3 -> 跳过)
        3. 值得观看 -> 完整播放 -> 互动(点赞80%, 评论90%, 收藏33%)
        4. 评论互动 -> 深度浏览所有评论 -> 发表评论 -> 关闭
        5. 达到目标评论数量后结束
        """
        start_time = time.time()
        video_count = 0
        
        logger.info("\n🚀 开始搜索结果专用浏览循环")
        logger.info(f"🎯 目标回复: {self.target_replies_goal} 条")
        
        while True:
            video_count += 1
            elapsed = int(time.time() - start_time)
            logger.info(f"\n📺 视频 #{video_count} | 已回复: {self.stats['replies_sent']}/{self.target_replies_goal} | 已用时: {elapsed}秒")
            logger.info("-" * 40)
            
            try:
                # 1. 检查视频类型
                video_type = self.browse_session.detect_video_type()
                if video_type == "unknown":
                    logger.info("⏭️ 未知视频类型/非目标视频，跳过")
                    core_utils.swipe_up_humanized()
                    time.sleep(1.5)
                    continue
                
                # 2. 获取数据并筛选（规则来自配置）
                likes, comments = self._get_video_stats()
                logger.info(f"📊 视频数据: 点赞 {likes}, 评论 {comments}")
                
                min_likes = self.video_filter['min_likes']
                min_comments = self.video_filter['min_comments']
                if likes < min_likes and comments < min_comments:
                    logger.info(f"⏭️ 数据过低 (点赞<{min_likes} 且 评论<{min_comments})，不值得观看，跳过")
                    core_utils.swipe_up_humanized()
                    time.sleep(1.5)
                    continue
                
                # 3. 值得观看 - 完整播放
                logger.info("✨ 优质视频，开始完整观看...")
                self._watch_video_fully()
                self.stats["videos_watched"] += 1
                
                # 4. 互动环节
                # 点赞（概率来自配置）
                if random.random() < self.prob_config['like']:
                    logger.info(f"👍 执行点赞 ({int(self.prob_config['like']*100)}%)")
                    if interactions.like_current_video():
                        self.stats["likes_given"] += 1
                    time.sleep(1.0)
                
                # 评论拦截（概率来自配置）- 扫描评论区寻找目标用户
                if random.random() < self.prob_config['comment']:
                    logger.info(f"💬 开始评论区拦截扫描 ({int(self.prob_config['comment']*100)}%)")
                    self._process_comments_deeply()
                    
                    if self.stats["replies_sent"] >= self.target_replies_goal:
                        logger.info(f"🏁 已达到目标回复 {self.target_replies_goal} 条，结束任务")
                        break
                
                # 收藏（概率来自配置）
                if random.random() < self.prob_config['favorite']:
                    logger.info(f"⭐ 执行收藏 ({int(self.prob_config['favorite']*100)}%)")
                    interactions.favorite_current_video()
                    time.sleep(1.0)
                
                # 5. 下一个视频
                logger.info("👇 视频处理完毕，切换下一个")
                core_utils.swipe_up_humanized()
                
                # 随机等待，模拟人类操作间隔
                time.sleep(random.uniform(1.5, 3.0))
                
            except Exception as e:
                logger.error(f"❌ 浏览循环异常: {e}")
                core_utils.swipe_up_humanized()
                time.sleep(2.0)
        else:
            logger.info("🛑 时间限制触发，结束任务")

    def _get_video_stats(self) -> tuple[int, int]:
        """获取视频的点赞数和评论数
        
        核心策略：通过 content-desc 属性获取，格式通常为 "5.2万赞" 或 "1234评论"
        """
        likes = 0
        comments = 0
        
        try:
            # === 策略1: 通过 content-desc 获取点赞数 (最可靠) ===
            try:
                # 点赞按钮的 content-desc 通常包含 "XX赞" 或 "XX万赞"
                like_elem = core_utils.find_element_safe(
                    By.ANDROID_UIAUTOMATOR, 
                    'new UiSelector().descriptionContains("赞")',
                    timeout=2
                )
                if like_elem:
                    desc = like_elem.get_attribute("content-desc") or ""
                    logger.info(f"   🔍 点赞元素 content-desc: '{desc}'")
                    # 从描述中提取数字，如 "5.2万赞" -> 52000
                    likes = self._parse_count_from_desc(desc)
                else:
                    logger.info("   ⚠️ 未找到点赞元素")
            except Exception as e:
                logger.info(f"   ❌ 点赞获取异常: {e}")
            
            # === 策略2: 通过 content-desc 获取评论数 ===
            try:
                comment_elem = core_utils.find_element_safe(
                    By.ANDROID_UIAUTOMATOR,
                    'new UiSelector().descriptionContains("评论")',
                    timeout=2
                )
                if comment_elem:
                    desc = comment_elem.get_attribute("content-desc") or ""
                    logger.info(f"   🔍 评论元素 content-desc: '{desc}'")
                    comments = self._parse_count_from_desc(desc)
                else:
                    logger.info("   ⚠️ 未找到评论元素")
            except Exception as e:
                logger.info(f"   ❌ 评论获取异常: {e}")
            
            # === 如果策略1失败，尝试备用策略 ===
            if likes == 0 and comments == 0:
                logger.info("   🔄 主策略失败，尝试备用策略...")
                likes, comments = self._get_video_stats_fallback()
                
            return likes, comments
            
        except Exception as e:
            logger.warning(f"获取数据失败: {e}")
            return 0, 0
    
    def _parse_count_from_desc(self, desc: str) -> int:
        """从 content-desc 解析数量
        
        支持格式：
        - "5.2万赞,按钮" -> 52000
        - "1234评论" -> 1234
        - "10赞" -> 10
        """
        import re
        if not desc:
            return 0
        
        # 提取数字部分 (支持小数点和万/亿单位)
        match = re.search(r'([\d.]+)\s*(万|亿)?', desc)
        if match:
            num_str = match.group(1)
            unit = match.group(2)
            
            try:
                num = float(num_str)
                if unit == '万':
                    num *= 10000
                elif unit == '亿':
                    num *= 100000000
                return int(num)
            except ValueError:
                return 0
        return 0
    
    def _get_video_stats_fallback(self) -> tuple[int, int]:
        """备用获取策略：遍历所有可能的元素"""
        likes = 0
        comments = 0
        
        try:
            # 尝试查找所有包含数字的 TextView
            elements = core_utils.find_elements_safe(
                By.XPATH, 
                "//android.widget.TextView",
                timeout=1
            )
            
            for elem in elements[:20]:  # 只检查前20个
                try:
                    text = elem.text or ""
                    desc = elem.get_attribute("content-desc") or ""
                    combined = text + desc
                    
                    if '赞' in combined and likes == 0:
                        likes = self._parse_count_from_desc(combined)
                        if likes > 0:
                            logger.info(f"   ✅ 备用-找到点赞: '{combined}' -> {likes}")
                    elif '评论' in combined and comments == 0:
                        comments = self._parse_count_from_desc(combined)
                        if comments > 0:
                            logger.info(f"   ✅ 备用-找到评论: '{combined}' -> {comments}")
                except:
                    continue
                    
        except Exception as e:
            logger.info(f"   ❌ 备用策略异常: {e}")
        
        return likes, comments

    def _watch_video_fully(self):
        """模拟完整观看视频"""
        # 简单策略：随机等待 15-30 秒
        # 进阶策略：如果能获取进度条，可以更精确，但目前简单模拟即可
        duration = random.randint(15, 30)
        logger.info(f"   👀 观看中... (约 {duration} 秒)")
        
        # 分段等待，每5秒检查一次是否还在当前页面（防止意外跳出）
        for _ in range(duration // 5):
            time.sleep(5)
            # 这里可以添加检查逻辑，目前省略

    def _process_comments_deeply(self):
        """
        LLM智能回复模式：调用评论扫描模块，自动识别关键词并生成智能回复
        """
        try:
            # 1. 打开评论区
            logger.info("   📖 打开评论区...")
            comment_btn = core_utils.find_element_safe(
                By.ANDROID_UIAUTOMATOR,
                'new UiSelector().descriptionContains("评论")',
                timeout=3
            )
            if not comment_btn:
                logger.warning("   ⚠️ 未找到评论按钮")
                return
            
            comment_btn.click()
            time.sleep(2.0)
            
            # 2. 调用评论扫描模块（LLM智能回复）
            logger.info("   🤖 调用LLM智能回复模块...")
            replies_before = len(REPLIED_COMMENTS)
            scan_comments_loop(self.driver)
            replies_after = len(REPLIED_COMMENTS)
            
            # 更新统计
            new_replies = replies_after - replies_before
            self.stats['replies_sent'] += new_replies
            logger.info(f"   ✅ 本轮新增回复: {new_replies} 条")
            
            # 3. 关闭评论区
            self.driver.press_keycode(4)
            time.sleep(1.0)
            
        except Exception as e:
            logger.error(f"   评论拦截异常: {e}")
            try:
                self.driver.press_keycode(4)
            except:
                pass
    
    
    def _cleanup(self):
        """清理资源并显示统计"""
        try:
            # 显示拦截模式统计
            logger.info("\n" + "=" * 50)
            logger.info("📊 拦截模式统计")
            logger.info("=" * 50)
            logger.info(f"   📺 观看视频数: {self.stats['videos_watched']}")
            logger.info(f"   💬 阅读评论数: {self.stats['comments_read']}")
            logger.info(f"   ✉️  发送回复数: {self.stats['replies_sent']}")
            logger.info(f"   👍 点赞次数:   {self.stats['likes_given']}")
            logger.info("=" * 50)
            
            # 关闭 driver
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("✅ Driver 已关闭")
                except Exception as e:
                    logger.warning(f"⚠️ Driver 关闭异常: {e}")
                    
        except Exception as e:
            logger.error(f"❌ 清理过程异常: {e}")


_current_session = None

def _signal_handler(signum, frame):
    """信号处理器 - 确保优雅关闭"""
    logger.warning(f"\n⚠️ 收到中断信号 ({signum})，正在保存日志并退出...")
    logger.flush()  # 立即刷新日志
    
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
    signal.signal(signal.SIGINT, _signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, _signal_handler)  # 终止信号
    
    try:
        logger.info("\n" + "🔍" * 30)
        logger.info("抖音搜索浏览器 - 启动")
        logger.info("🔍" * 30)
        
        # 创建并运行会话
        _current_session = SearchBrowseSession()
        success = _current_session.run()
        
        logger.flush()  # 确保日志保存
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
