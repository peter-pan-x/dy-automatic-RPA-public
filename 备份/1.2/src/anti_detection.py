"""
增强的反检测模块
实现多层次的人类行为模拟和设备指纹伪装
"""

import time
import random
import math
from typing import Tuple, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class UserBehaviorProfile:
    """用户行为画像"""
    active_hours: List[int]  # 活跃时间段
    avg_session_duration: int  # 平均会话时长（分钟）
    like_rate: float  # 点赞率
    comment_rate: float  # 评论率
    watch_time_mean: float  # 观看时间均值
    watch_time_std: float  # 观看时间标准差
    swipe_speed_mean: int  # 滑动速度均值（ms）
    swipe_speed_std: int  # 滑动速度标准差


class AdvancedBehaviorSimulator:
    """高级行为模拟器"""
    
    # 预定义的用户画像
    PROFILES = {
        "casual": UserBehaviorProfile(
            active_hours=[19, 20, 21, 22, 23],
            avg_session_duration=15,
            like_rate=0.15,
            comment_rate=0.05,
            watch_time_mean=8.0,
            watch_time_std=3.0,
            swipe_speed_mean=500,
            swipe_speed_std=150
        ),
        "engaged": UserBehaviorProfile(
            active_hours=[9, 10, 11, 14, 15, 16, 19, 20, 21],
            avg_session_duration=30,
            like_rate=0.35,
            comment_rate=0.12,
            watch_time_mean=12.0,
            watch_time_std=4.0,
            swipe_speed_mean=450,
            swipe_speed_std=120
        ),
        "power_user": UserBehaviorProfile(
            active_hours=list(range(8, 24)),
            avg_session_duration=60,
            like_rate=0.50,
            comment_rate=0.20,
            watch_time_mean=15.0,
            watch_time_std=5.0,
            swipe_speed_mean=400,
            swipe_speed_std=100
        )
    }
    
    def __init__(self, profile_type: str = "engaged"):
        """
        初始化行为模拟器
        
        Args:
            profile_type: 用户画像类型 (casual, engaged, power_user)
        """
        self.profile = self.PROFILES.get(profile_type, self.PROFILES["engaged"])
        self.session_start_time = datetime.now()
        self.interaction_count = 0
        self.fatigue_level = 0.0  # 疲劳度（0-1）
        self.last_action_time = time.time()
    
    def should_be_active(self) -> bool:
        """判断当前是否应该活跃"""
        current_hour = datetime.now().hour
        
        # 基础活跃时间判断
        if current_hour not in self.profile.active_hours:
            return False
        
        # 考虑会话持续时间
        session_duration = (datetime.now() - self.session_start_time).total_seconds() / 60
        if session_duration > self.profile.avg_session_duration * 1.5:
            # 会话过长，需要休息
            return random.random() > 0.7
        
        # 考虑疲劳度
        self._update_fatigue()
        if self.fatigue_level > 0.8:
            return random.random() > 0.6
        
        return True
    
    def _update_fatigue(self):
        """更新疲劳度"""
        # 疲劳度随交互次数和时间增加
        session_duration_hours = (datetime.now() - self.session_start_time).total_seconds() / 3600
        self.fatigue_level = min(1.0, (session_duration_hours / 2.0) + (self.interaction_count / 100))
    
    def get_watch_time(self) -> float:
        """
        获取观看时间（秒）
        考虑疲劳度和时间分布
        """
        # 使用正态分布，但考虑疲劳度
        base_time = random.gauss(self.profile.watch_time_mean, self.profile.watch_time_std)
        
        # 疲劳时观看时间缩短
        fatigue_factor = 1.0 - (self.fatigue_level * 0.3)
        watch_time = base_time * fatigue_factor
        
        # 限制在合理范围内
        watch_time = max(3.0, min(30.0, watch_time))
        
        # 5%概率出现异常短观看（模拟不感兴趣快速滑过）
        if random.random() < 0.05:
            watch_time = random.uniform(0.5, 2.0)
        
        # 3%概率出现长观看（模拟特别感兴趣）
        elif random.random() < 0.03:
            watch_time = random.uniform(20.0, 40.0)
        
        return watch_time
    
    def get_action_delay(self) -> float:
        """
        获取操作间延迟（秒）
        模拟人类的反应时间和思考时间
        """
        # 基础延迟：对数正态分布
        base_delay = random.lognormvariate(0.5, 0.5)
        
        # 疲劳时反应变慢
        fatigue_factor = 1.0 + (self.fatigue_level * 0.5)
        delay = base_delay * fatigue_factor
        
        # 限制在合理范围
        delay = max(0.3, min(5.0, delay))
        
        # 10%概率出现较长停顿（模拟思考或分心）
        if random.random() < 0.1:
            delay += random.uniform(2.0, 8.0)
        
        self.last_action_time = time.time()
        return delay
    
    def should_interact(self, interaction_type: str) -> bool:
        """
        判断是否应该执行交互
        
        Args:
            interaction_type: 交互类型 (like, comment, favorite, follow)
        """
        base_prob = {
            "like": self.profile.like_rate,
            "comment": self.profile.comment_rate,
            "favorite": self.profile.comment_rate * 0.7,
            "follow": self.profile.comment_rate * 0.5
        }.get(interaction_type, 0.1)
        
        # 疲劳时交互意愿下降
        adjusted_prob = base_prob * (1.0 - self.fatigue_level * 0.5)
        
        # 连续交互后概率下降（避免过于规律）
        if self.interaction_count % 10 == 0:
            adjusted_prob *= 0.5
        
        return random.random() < adjusted_prob
    
    def generate_swipe_trajectory(self, screen_width: int, screen_height: int,
                                 direction: str = "up") -> List[Tuple[int, int, int]]:
        """
        生成人类化的滑动轨迹
        
        Args:
            screen_width: 屏幕宽度
            screen_height: 屏幕高度
            direction: 滑动方向 (up, down, left, right)
            
        Returns:
            List[Tuple[int, int, int]]: [(x, y, timestamp), ...] 轨迹点列表
        """
        trajectory = []
        
        # 起点和终点
        if direction == "up":
            start_x = screen_width // 2 + random.randint(-50, 50)
            start_y = int(screen_height * 0.7) + random.randint(-30, 30)
            end_x = start_x + random.randint(-30, 30)
            end_y = int(screen_height * 0.3) + random.randint(-30, 30)
        elif direction == "down":
            start_x = screen_width // 2 + random.randint(-50, 50)
            start_y = int(screen_height * 0.3) + random.randint(-30, 30)
            end_x = start_x + random.randint(-30, 30)
            end_y = int(screen_height * 0.7) + random.randint(-30, 30)
        else:
            start_x, start_y = screen_width // 2, screen_height // 2
            end_x, end_y = start_x, start_y
        
        # 计算总时长（ms）
        base_duration = random.gauss(self.profile.swipe_speed_mean, self.profile.swipe_speed_std)
        duration = max(200, min(1000, int(base_duration)))
        
        # 生成贝塞尔曲线轨迹点
        num_points = random.randint(15, 30)
        
        # 控制点（模拟手指滑动的轻微曲线）
        control_x = (start_x + end_x) // 2 + random.randint(-20, 20)
        control_y = (start_y + end_y) // 2 + random.randint(-20, 20)
        
        for i in range(num_points):
            t = i / (num_points - 1)
            
            # 二次贝塞尔曲线
            x = int((1 - t) ** 2 * start_x + 2 * (1 - t) * t * control_x + t ** 2 * end_x)
            y = int((1 - t) ** 2 * start_y + 2 * (1 - t) * t * control_y + t ** 2 * end_y)
            
            # 添加微小抖动（模拟手指不稳）
            x += random.randint(-3, 3)
            y += random.randint(-3, 3)
            
            timestamp = int(duration * t)
            trajectory.append((x, y, timestamp))
        
        return trajectory
    
    def simulate_typing_rhythm(self, text: str) -> List[Tuple[str, float]]:
        """
        模拟人类打字节奏
        
        Args:
            text: 要输入的文本
            
        Returns:
            List[Tuple[str, float]]: [(字符, 延迟秒数), ...]
        """
        rhythm = []
        
        for i, char in enumerate(text):
            # 基础打字速度：每个字符100-300ms
            base_delay = random.uniform(0.1, 0.3)
            
            # 特殊字符慢一些
            if char in [' ', '@', '#', '.', ',', '!', '?']:
                base_delay *= 1.5
            
            # 每个词的第一个字符稍慢（思考时间）
            if i > 0 and text[i-1] == ' ':
                base_delay *= 1.3
            
            # 偶尔停顿（模拟思考）
            if random.random() < 0.05:
                base_delay += random.uniform(0.5, 2.0)
            
            # 疲劳时打字变慢
            delay = base_delay * (1.0 + self.fatigue_level * 0.3)
            
            rhythm.append((char, delay))
        
        return rhythm
    
    def get_break_duration(self) -> int:
        """
        获取休息时长（分钟）
        基于疲劳度动态调整
        """
        base_duration = random.randint(5, 15)
        
        # 疲劳度高时需要更长休息
        if self.fatigue_level > 0.7:
            base_duration = random.randint(15, 30)
        elif self.fatigue_level > 0.5:
            base_duration = random.randint(10, 20)
        
        return base_duration
    
    def reset_session(self):
        """重置会话状态"""
        self.session_start_time = datetime.now()
        self.interaction_count = 0
        self.fatigue_level = 0.0
    
    def record_interaction(self):
        """记录一次交互"""
        self.interaction_count += 1


class DeviceFingerprint:
    """设备指纹伪装"""
    
    def __init__(self):
        self.battery_level = random.randint(20, 95)
        self.battery_status = random.choice(["charging", "discharging"])
        self.network_type = random.choice(["4G", "5G", "WiFi"])
        self.memory_usage = random.uniform(0.4, 0.8)
        self.last_update_time = datetime.now()
    
    def update_battery(self):
        """更新电池状态"""
        time_passed = (datetime.now() - self.last_update_time).total_seconds() / 60
        
        if self.battery_status == "discharging":
            # 放电：每分钟下降0.1-0.3%
            self.battery_level -= time_passed * random.uniform(0.1, 0.3)
            if self.battery_level < 20:
                # 电量低时可能会充电
                if random.random() < 0.3:
                    self.battery_status = "charging"
        else:
            # 充电：每分钟增加0.5-1%
            self.battery_level += time_passed * random.uniform(0.5, 1.0)
            if self.battery_level > 95:
                self.battery_level = 95
                if random.random() < 0.5:
                    self.battery_status = "discharging"
        
        self.battery_level = max(5, min(100, self.battery_level))
        self.last_update_time = datetime.now()
    
    def switch_network(self):
        """切换网络类型（模拟移动场景）"""
        if random.random() < 0.1:  # 10%概率切换网络
            networks = ["4G", "5G", "WiFi"]
            networks.remove(self.network_type)
            self.network_type = random.choice(networks)
    
    def get_network_delay(self) -> float:
        """
        根据网络类型获取延迟
        模拟不同网络条件下的响应时间
        """
        base_delays = {
            "WiFi": (0.05, 0.15),
            "5G": (0.1, 0.3),
            "4G": (0.2, 0.5)
        }
        
        min_delay, max_delay = base_delays.get(self.network_type, (0.1, 0.3))
        
        # 5%概率出现网络波动
        if random.random() < 0.05:
            return random.uniform(max_delay * 2, max_delay * 5)
        
        return random.uniform(min_delay, max_delay)


class AntiDetectionCoordinator:
    """反检测协调器 - 综合管理各种反检测策略"""
    
    def __init__(self, profile_type: str = "engaged"):
        self.behavior_sim = AdvancedBehaviorSimulator(profile_type)
        self.device = DeviceFingerprint()
        self.session_count = 0
        self.last_risk_check = datetime.now()
        self.risk_score = 0.0  # 风险评分（0-1）
    
    def pre_session_check(self) -> Dict[str, Any]:
        """
        会话前检查
        
        Returns:
            Dict: 检查结果和建议
        """
        result = {
            "can_proceed": True,
            "should_rest": False,
            "rest_duration": 0,
            "warnings": []
        }
        
        # 检查活跃时间
        if not self.behavior_sim.should_be_active():
            result["can_proceed"] = False
            result["should_rest"] = True
            result["rest_duration"] = self.behavior_sim.get_break_duration()
            result["warnings"].append("不在活跃时间段，建议休息")
        
        # 检查疲劳度
        if self.behavior_sim.fatigue_level > 0.8:
            result["should_rest"] = True
            result["rest_duration"] = self.behavior_sim.get_break_duration()
            result["warnings"].append(f"疲劳度过高 ({self.behavior_sim.fatigue_level:.2f})")
        
        # 检查风险评分
        self._update_risk_score()
        if self.risk_score > 0.7:
            result["can_proceed"] = False
            result["should_rest"] = True
            result["rest_duration"] = random.randint(30, 60)
            result["warnings"].append(f"风险评分过高 ({self.risk_score:.2f})")
        
        # 更新设备状态
        self.device.update_battery()
        self.device.switch_network()
        
        return result
    
    def _update_risk_score(self):
        """更新风险评分"""
        time_since_check = (datetime.now() - self.last_risk_check).total_seconds() / 60
        
        # 风险评分随时间自然下降
        self.risk_score = max(0.0, self.risk_score - time_since_check * 0.01)
        
        # 连续会话增加风险
        if self.session_count > 10:
            self.risk_score += 0.05
        
        # 疲劳度高增加风险
        if self.behavior_sim.fatigue_level > 0.7:
            self.risk_score += 0.1
        
        self.risk_score = min(1.0, self.risk_score)
        self.last_risk_check = datetime.now()
    
    def get_behavior_simulator(self) -> AdvancedBehaviorSimulator:
        """获取行为模拟器"""
        return self.behavior_sim
    
    def get_device_fingerprint(self) -> DeviceFingerprint:
        """获取设备指纹"""
        return self.device
    
    def start_session(self):
        """开始新会话"""
        self.session_count += 1
        if self.session_count % 5 == 0:
            # 每5个会话重置一次（模拟用户离开又回来）
            self.behavior_sim.reset_session()
    
    def end_session(self):
        """结束会话"""
        self.behavior_sim.record_interaction()


# 全局反检测协调器实例
_anti_detection_coordinator = None


def get_anti_detection_coordinator(profile_type: str = "engaged") -> AntiDetectionCoordinator:
    """获取反检测协调器实例"""
    global _anti_detection_coordinator
    if _anti_detection_coordinator is None:
        _anti_detection_coordinator = AntiDetectionCoordinator(profile_type)
    return _anti_detection_coordinator

