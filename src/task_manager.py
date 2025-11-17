"""
智能调度任务管理器 - 项目的灵魂
负责会话切换、编排、智能调度和反检测策略
"""

import time
import random
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum

from appium import webdriver
from . import interactions, tracker
from .app_driver import get_driver_manager
import config.settings as settings

class SessionState(Enum):
    """会话状态枚举"""
    STATE_FOR_YOU = "STATE_FOR_YOU"      # 无聊刷模式
    STATE_SEARCH = "STATE_SEARCH"        # 精准打击模式
    STATE_BREAK = "STATE_BREAK"          # 休息模式
    STATE_RECOVERY = "STATE_RECOVERY"    # 恢复模式
    STATE_SHUTDOWN = "STATE_SHUTDOWN"    # 关闭模式

class TaskManager:
    """智能任务管理器"""

    def __init__(self, driver: webdriver.Remote):
        self.driver = driver
        self.state = SessionState.STATE_FOR_YOU  # 启动时先"无聊刷"

        # 初始化各个模块
        self.tracker = tracker.get_tracker()
        self.driver_manager = get_driver_manager()

        # 加载配置文件
        self.keywords_list = self._load_keywords()
        self.comments_list = self._load_comments()

        # 运行状态控制
        self.running = False
        self.paused = False
        self.shutdown_requested = False

        # 会话统计
        self.current_session_videos = 0
        self.current_session_interactions = 0
        self.session_start_time = None

        # 智能调度相关
        self.last_break_time = None
        self.consecutive_errors = 0
        self.success_rate_history = []
        self.adaptive_params = {
            'like_prob_adjustment': 0.0,
            'comment_prob_adjustment': 0.0,
            'session_duration_adjustment': 1.0,
        }

        # 线程锁
        self.lock = threading.Lock()

        print("🎯 任务管理器初始化完成")

    def _load_keywords(self) -> List[str]:
        """加载搜索关键词"""
        try:
            keywords_file = "config/keywords.txt"
            with open(keywords_file, 'r', encoding='utf-8') as f:
                keywords = [line.strip() for line in f.readlines() if line.strip()]
            print(f"📝 加载了 {len(keywords)} 个搜索关键词")
            return keywords
        except Exception as e:
            print(f"⚠️ 加载关键词失败: {e}")
            return ["美食", "旅行", "科技", "音乐", "舞蹈"]

    def _load_comments(self) -> List[str]:
        """加载评论库"""
        try:
            comments_file = "config/comments.txt"
            with open(comments_file, 'r', encoding='utf-8') as f:
                comments = [line.strip() for line in f.readlines() if line.strip()]
            print(f"💬 加载了 {len(comments)} 条评论")
            return comments
        except Exception as e:
            print(f"⚠️ 加载评论失败: {e}")
            return ["真不错！", "很棒", "学习了", "点赞支持"]

    def _should_switch_state(self) -> bool:
        """判断是否应该切换状态"""
        # 检查是否在活跃时间
        if not settings.is_active_hour():
            if self.state != SessionState.STATE_BREAK:
                print("🌙 非活跃时间，切换到休息模式")
                return True

        # 检查是否需要休息
        if settings.should_take_break():
            if self.state != SessionState.STATE_BREAK:
                print("😴 需要休息，切换到休息模式")
                return True

        # 检查错误率
        if self.consecutive_errors >= 3:
            if self.state != SessionState.STATE_RECOVERY:
                print("🔧 连续错误过多，切换到恢复模式")
                return True

        return False

    def _get_next_state(self) -> SessionState:
        """获取下一个状态"""
        if self.consecutive_errors >= 3:
            return SessionState.STATE_RECOVERY

        if not settings.is_active_hour() or settings.should_take_break():
            return SessionState.STATE_BREAK

        # 正常状态切换
        if self.state == SessionState.STATE_FOR_YOU:
            return SessionState.STATE_SEARCH
        elif self.state == SessionState.STATE_SEARCH:
            return SessionState.STATE_FOR_YOU
        else:
            return SessionState.STATE_FOR_YOU

    def _adaptive_probability(self, base_prob: float, adjustment_key: str) -> float:
        """自适应概率调整"""
        adjusted_prob = base_prob + self.adaptive_params[adjustment_key]
        return max(0.0, min(1.0, adjusted_prob))

    def _update_adaptive_params(self):
        """更新自适应参数"""
        if len(self.success_rate_history) >= 5:
            recent_success_rate = sum(self.success_rate_history[-5:]) / 5

            if recent_success_rate < 0.7:  # 成功率低于70%
                # 降低交互频率
                self.adaptive_params['like_prob_adjustment'] -= 0.1
                self.adaptive_params['comment_prob_adjustment'] -= 0.05
                self.adaptive_params['session_duration_adjustment'] *= 0.9
                print("📉 检测到成功率低，降低交互频率")
            elif recent_success_rate > 0.9:  # 成功率高于90%
                # 适当增加交互频率
                self.adaptive_params['like_prob_adjustment'] += 0.05
                self.adaptive_params['comment_prob_adjustment'] += 0.02
                self.adaptive_params['session_duration_adjustment'] *= 1.05
                print("📈 成功率很高，适当增加交互频率")

    def _run_for_you_session(self):
        """运行推荐页面会话（迷魂汤模式）"""
        print("🌟 开始推荐页面会话（迷魂汤模式）")
        self.tracker.start_session("推荐页面")

        # 确保在推荐页面
        interactions.go_to_for_you_page()

        # 计算视频数量（考虑自适应调整）
        base_min = settings.SESSION_FOR_YOU_MIN_VIDEOS
        base_max = settings.SESSION_FOR_YOU_MAX_VIDEOS

        adjusted_min = int(base_min * self.adaptive_params['session_duration_adjustment'])
        adjusted_max = int(base_max * self.adaptive_params['session_duration_adjustment'])

        video_count = random.randint(adjusted_min, adjusted_max)
        self.current_session_videos = 0
        self.current_session_interactions = 0

        try:
            for i in range(video_count):
                if self.shutdown_requested:
                    break

                print(f"📺 推荐页面视频 {i+1}/{video_count}")

                # 处理弹窗
                interactions.dismiss_popups_if_present()

                # 检测是否为直播视频
                if interactions.is_live_stream():
                    print("🔴 当前为直播视频，跳过...")
                    # 退出直播界面
                    interactions.exit_live_stream()
                    # 等待一下
                    time.sleep(random.uniform(0.5, 1.0))
                    # 滑动到下一个视频
                    from . import core_utils
                    core_utils.swipe_up_humanized()
                    time.sleep(random.uniform(settings.ACTION_DELAY_MIN, settings.ACTION_DELAY_MAX))
                    continue

                # 检测是否为广告
                if interactions.is_advertisement():
                    print("📺 当前为广告视频，跳过...")
                    # 滑动到下一个视频
                    from . import core_utils
                    core_utils.swipe_up_humanized()
                    time.sleep(random.uniform(settings.ACTION_DELAY_MIN, settings.ACTION_DELAY_MAX))
                    continue

                # 检测是否有交互按钮
                if not interactions.has_interaction_buttons():
                    print("⚠️ 未检测到交互按钮，可能是特殊视频，跳过...")
                    # 滑动到下一个视频
                    from . import core_utils
                    core_utils.swipe_up_humanized()
                    time.sleep(random.uniform(settings.ACTION_DELAY_MIN, settings.ACTION_DELAY_MAX))
                    continue

                # 智能观看时间（模拟真实用户快速刷抖音，最少3秒）
                rand_val = random.random()
                if rand_val < 0.49:
                    # 49%概率：快速划过（3-5秒）- 最少3秒
                    watch_time = random.uniform(3, 5)
                    print(f"⚡ 快速浏览 ({watch_time:.1f}秒)")
                elif rand_val < 0.82:  # 0.49 + 0.33 = 0.82
                    # 33%概率：中等观看（5-10秒）
                    watch_time = random.uniform(5, 10)
                    print(f"👀 认真观看 ({watch_time:.1f}秒)")
                else:
                    # 18%概率：看完视频（10-20秒）
                    watch_time = random.uniform(10, 20)
                    print(f"🎬 看完视频 ({watch_time:.1f}秒)")
                
                time.sleep(watch_time)

                # 记录观看
                self.tracker.log_interaction('watch', True, session_type="推荐页面")
                self.current_session_videos += 1

                # 55%概率点赞
                if random.random() < self._adaptive_probability(
                    settings.FOR_YOU_LIKE_PROB, 'like_prob_adjustment'
                ):
                    if interactions.like_current_video():
                        self.tracker.log_interaction('like', True, session_type="推荐页面")
                        self.current_session_interactions += 1
                        self.consecutive_errors = 0
                    else:
                        self.consecutive_errors += 1
                        print(f"⚠️ 点赞失败 (连续失败: {self.consecutive_errors}/6)")
                        # 连续失败6次后退出
                        if self.consecutive_errors >= 6:
                            print("❌ 连续失败6次，程序退出以便检查优化")
                            self.shutdown_requested = True
                            return

                # 33%概率评论
                if random.random() < settings.FOR_YOU_COMMENT_PROB:
                    comment_text = random.choice(self.comments_list)
                    if interactions.comment_on_current_video(comment_text):
                        self.tracker.log_interaction('comment', True, comment_text, session_type="推荐页面")
                        self.current_session_interactions += 1

                # 33%概率收藏
                if random.random() < settings.FOR_YOU_FAVORITE_PROB:
                    if interactions.favorite_current_video():
                        self.tracker.log_interaction('favorite', True, session_type="推荐页面")
                        self.current_session_interactions += 1

                # 33%概率关注
                if random.random() < settings.FOR_YOU_FOLLOW_PROB:
                    if interactions.follow_current_author():
                        self.tracker.log_interaction('follow', True, session_type="推荐页面")
                        self.current_session_interactions += 1

                # 滑动到下一个视频
                from . import core_utils
                if not core_utils.swipe_up_humanized():
                    print("⚠️ 滑动失败，尝试恢复")
                    self.consecutive_errors += 1
                else:
                    self.consecutive_errors = max(0, self.consecutive_errors - 1)

                # 随机延迟
                time.sleep(random.uniform(settings.ACTION_DELAY_MIN, settings.ACTION_DELAY_MAX))

        except Exception as e:
            print(f"❌ 推荐页面会话异常: {e}")
            self.tracker.log_interaction('session_error', False, str(e), session_type="推荐页面")

        finally:
            # 完成会话
            success = self.current_session_videos > 0
            self.tracker.complete_session(
                self.current_session_videos,
                self.current_session_interactions,
                success,
                f"计划{video_count}个视频，实际完成{self.current_session_videos}个"
            )

    def _run_search_session(self):
        """运行搜索会话（精准打击模式）"""
        print("🎯 开始搜索会话（精准打击模式）")
        self.tracker.start_session("搜索")

        # 选择搜索关键词
        keyword = random.choice(self.keywords_list)
        print(f"🔍 搜索关键词: {keyword}")

        # 执行搜索
        if not interactions.perform_search_and_switch(keyword):
            print("❌ 搜索失败")
            self.tracker.log_interaction('search', False, keyword, "搜索失败", session_type="搜索")
            self.consecutive_errors += 1
            return

        self.tracker.log_interaction('search', True, keyword, session_type="搜索")
        self.consecutive_errors = 0

        # 计算视频数量
        base_min = settings.SESSION_SEARCH_MIN_VIDEOS
        base_max = settings.SESSION_SEARCH_MAX_VIDEOS

        adjusted_min = int(base_min * self.adaptive_params['session_duration_adjustment'])
        adjusted_max = int(base_max * self.adaptive_params['session_duration_adjustment'])

        video_count = random.randint(adjusted_min, adjusted_max)
        self.current_session_videos = 0
        self.current_session_interactions = 0

        try:
            for i in range(video_count):
                if self.shutdown_requested:
                    break

                print(f"📺 搜索视频 {i+1}/{video_count}")

                # 处理弹窗
                interactions.dismiss_popups_if_present()

                # 检测是否为直播视频
                if interactions.is_live_stream():
                    print("🔴 当前为直播视频，跳过...")
                    # 退出直播界面
                    interactions.exit_live_stream()
                    # 等待一下
                    time.sleep(random.uniform(0.5, 1.0))
                    # 滑动到下一个视频
                    from . import core_utils
                    core_utils.swipe_up_humanized()
                    time.sleep(random.uniform(settings.ACTION_DELAY_MIN, settings.ACTION_DELAY_MAX))
                    continue

                # 检测是否为广告
                if interactions.is_advertisement():
                    print("📺 当前为广告视频，跳过...")
                    # 滑动到下一个视频
                    from . import core_utils
                    core_utils.swipe_up_humanized()
                    time.sleep(random.uniform(settings.ACTION_DELAY_MIN, settings.ACTION_DELAY_MAX))
                    continue

                # 检测是否有交互按钮
                if not interactions.has_interaction_buttons():
                    print("⚠️ 未检测到交互按钮，可能是特殊视频，跳过...")
                    # 滑动到下一个视频
                    from . import core_utils
                    core_utils.swipe_up_humanized()
                    time.sleep(random.uniform(settings.ACTION_DELAY_MIN, settings.ACTION_DELAY_MAX))
                    continue

                # 观看时间
                watch_time = random.uniform(settings.WATCH_TIME_MIN, settings.WATCH_TIME_MAX)
                time.sleep(watch_time)

                # 记录观看
                self.tracker.log_interaction('watch', True, session_type="搜索")
                self.current_session_videos += 1

                # 高概率点赞
                if random.random() < self._adaptive_probability(
                    settings.SEARCH_LIKE_PROB, 'like_prob_adjustment'
                ):
                    if interactions.like_current_video():
                        self.tracker.log_interaction('like', True, session_type="搜索")
                        self.current_session_interactions += 1

                # 中概率评论
                if random.random() < self._adaptive_probability(
                    settings.SEARCH_COMMENT_PROB, 'comment_prob_adjustment'
                ):
                    comment_text = random.choice(self.comments_list)
                    if interactions.comment_on_current_video(comment_text):
                        self.tracker.log_interaction('comment', True, comment_text, session_type="搜索")
                        self.current_session_interactions += 1

                # 收藏操作
                if random.random() < settings.SEARCH_FAVORITE_PROB:
                    if interactions.favorite_current_video():
                        self.tracker.log_interaction('favorite', True, session_type="搜索")
                        self.current_session_interactions += 1

                # 关注操作
                if random.random() < settings.SEARCH_FOLLOW_PROB:
                    if interactions.follow_current_author():
                        self.tracker.log_interaction('follow', True, session_type="搜索")
                        self.current_session_interactions += 1

                # 滑动到下一个视频
                from . import core_utils
                if not core_utils.swipe_up_humanized():
                    print("⚠️ 滑动失败")
                    self.consecutive_errors += 1
                else:
                    self.consecutive_errors = max(0, self.consecutive_errors - 1)

                # 随机延迟
                time.sleep(random.uniform(settings.ACTION_DELAY_MIN, settings.ACTION_DELAY_MAX))

        except Exception as e:
            print(f"❌ 搜索会话异常: {e}")
            self.tracker.log_interaction('session_error', False, str(e), session_type="搜索")

        finally:
            # 完成会话
            success = self.current_session_videos > 0
            self.tracker.complete_session(
                self.current_session_videos,
                self.current_session_interactions,
                success,
                f"搜索'{keyword}'，计划{video_count}个视频，实际完成{self.current_session_videos}个"
            )

    def _run_break_session(self):
        """运行休息会话"""
        print("😴 开始休息会话")

        break_duration = settings.get_break_duration()
        self.tracker.start_session("休息")

        print(f"⏰ 休息 {break_duration} 分钟...")

        break_end_time = datetime.now() + timedelta(minutes=break_duration)

        while datetime.now() < break_end_time:
            if self.shutdown_requested:
                print("⚠️ 收到关闭信号，提前结束休息")
                break

            remaining = (break_end_time - datetime.now()).total_seconds()
            if remaining > 60:
                print(f"⏰ 剩余休息时间: {int(remaining // 60)} 分 {int(remaining % 60)} 秒")
            else:
                print(f"⏰ 剩余休息时间: {int(remaining)} 秒")

            time.sleep(30)  # 每30秒显示一次剩余时间

        self.last_break_time = datetime.now()
        self.tracker.complete_session(0, 0, True, f"休息了{break_duration}分钟")

    def _run_recovery_session(self):
        """运行恢复会话"""
        print("🔧 开始恢复会话")
        self.tracker.start_session("恢复")

        try:
            # 检查驱动连接
            if not self.driver_manager.is_connected():
                print("🔌 尝试重新连接驱动...")
                if self.driver_manager.reconnect():
                    print("✅ 驱动重连成功")
                    self.consecutive_errors = 0
                else:
                    print("❌ 驱动重连失败")
                    self.shutdown_requested = True
                    return

            # 尝试重启应用
            if self.consecutive_errors >= 5:
                print("🔄 尝试重启应用...")
                if self.driver_manager.restart_app():
                    print("✅ 应用重启成功")
                    self.consecutive_errors = 0
                else:
                    print("❌ 应用重启失败")
                    self.shutdown_requested = True
                    return

            # 重新初始化交互模块
            from . import core_utils
            interactions.init_interactions(self.driver)
            core_utils.init_utils(self.driver)

            print("✅ 恢复完成")

        except Exception as e:
            print(f"❌ 恢复会话异常: {e}")
            self.tracker.log_interaction('recovery_error', False, str(e), session_type="恢复")
            self.shutdown_requested = True

        finally:
            self.tracker.complete_session(0, 0, True, "执行恢复操作")

    def run_main_loop(self):
        """主循环 - 状态机核心"""
        print("🚀 任务管理器启动主循环")
        self.running = True

        # 初始化模块
        from . import core_utils
        interactions.init_interactions(self.driver)
        core_utils.init_utils(self.driver)

        while self.running and not self.shutdown_requested:
            try:
                # 检查是否应该切换状态
                if self._should_switch_state():
                    self.state = self._get_next_state()

                # 更新自适应参数
                self._update_adaptive_params()

                # 根据状态执行相应操作
                if self.state == SessionState.STATE_FOR_YOU:
                    self._run_for_you_session()
                    self.state = SessionState.STATE_SEARCH

                elif self.state == SessionState.STATE_SEARCH:
                    self._run_search_session()
                    self.state = SessionState.STATE_FOR_YOU

                elif self.state == SessionState.STATE_BREAK:
                    self._run_break_session()
                    # 休息后返回推荐页面
                    self.state = SessionState.STATE_FOR_YOU

                elif self.state == SessionState.STATE_RECOVERY:
                    self._run_recovery_session()
                    if not self.shutdown_requested:
                        self.state = SessionState.STATE_FOR_YOU

                # 显示统计摘要
                self.tracker.display_summary()

                # 会话间随机延迟
                if not self.shutdown_requested:
                    delay = random.uniform(2, 5)
                    print(f"⏱️ 会话间延迟 {delay:.1f} 秒...")
                    time.sleep(delay)

            except KeyboardInterrupt:
                print("\n⚠️ 收到中断信号，准备退出...")
                self.shutdown_requested = True

            except Exception as e:
                print(f"❌ 主循环异常: {e}")
                self.consecutive_errors += 1
                self.tracker.log_interaction('main_loop_error', False, str(e))

                if self.consecutive_errors >= 3:
                    print("🔧 连续错误过多，切换到恢复模式")
                    self.state = SessionState.STATE_RECOVERY

                time.sleep(10)  # 异常后等待10秒

        print("🛑 主循环结束")

    def pause(self):
        """暂停运行"""
        with self.lock:
            self.paused = True
            print("⏸️ 任务管理器已暂停")

    def resume(self):
        """恢复运行"""
        with self.lock:
            self.paused = False
            print("▶️ 任务管理器已恢复")

    def shutdown(self):
        """优雅关闭"""
        print("🛑 正在关闭任务管理器...")
        self.shutdown_requested = True
        self.running = False

        # 导出统计数据
        try:
            self.tracker.export_data()
        except Exception as e:
            print(f"⚠️ 导出数据失败: {e}")

        print("✅ 任务管理器已关闭")

    def get_status(self) -> Dict[str, Any]:
        """获取运行状态"""
        with self.lock:
            return {
                'state': self.state.value,
                'running': self.running,
                'paused': self.paused,
                'shutdown_requested': self.shutdown_requested,
                'current_session_videos': self.current_session_videos,
                'current_session_interactions': self.current_session_interactions,
                'consecutive_errors': self.consecutive_errors,
                'last_break_time': self.last_break_time.isoformat() if self.last_break_time else None,
                'adaptive_params': self.adaptive_params.copy(),
                'runtime_info': self.tracker.get_runtime_info()
            }