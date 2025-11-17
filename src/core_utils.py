"""
原子工具库 - 包含基础操作和反检测措施
提供健壮的元素查找、人性化的滑动、安全的输入等功能
"""

import time
import random
import math
from typing import Optional, Tuple, List, Dict, Any
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy as By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, 
    TimeoutException,
                                       StaleElementReferenceException,
    ElementNotInteractableException,
    WebDriverException
)
import config.settings as settings

# 导入新模块
try:
    from .logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    from config.selectors import ElementSelectors
    from .anti_detection import get_anti_detection_coordinator
    HAS_ENHANCED_MODULES = True
except ImportError:
    HAS_ENHANCED_MODULES = False
    print("[WARN] Enhanced modules not found, using basic features")

class HumanBehaviorSimulator:
    """人类行为模拟器"""

    @staticmethod
    def random_pause(min_seconds: float = 0.5, max_seconds: float = 2.0):
        """随机暂停"""
        pause_time = random.uniform(min_seconds, max_seconds)
        time.sleep(pause_time)

    @staticmethod
    def human_like_delay():
        """人性化延迟"""
        delay = random.gauss(1.5, 0.5)  # 正态分布，均值1.5秒
        delay = max(0.3, min(3.0, delay))  # 限制在0.3-3.0秒之间
        time.sleep(delay)

    @staticmethod
    def simulate_mistake() -> bool:
        """模拟操作失误"""
        if settings.ANTI_DETECTION_CONFIG.get('simulate_human_errors', False):
            return random.random() < 0.05  # 5%概率失误
        return False

    @staticmethod
    def variable_touch_position(base_x: int, base_y: int,
                              screen_width: int, screen_height: int) -> Tuple[int, int]:
        """生成变化的触摸位置"""
        if not settings.ANTI_DETECTION_CONFIG.get('variable_touch_positions', True):
            return base_x, base_y

        # 添加随机偏移
        offset_range = min(screen_width, screen_height) * 0.02  # 2%偏移范围
        x_offset = random.uniform(-offset_range, offset_range)
        y_offset = random.uniform(-offset_range, offset_range)

        new_x = int(base_x + x_offset)
        new_y = int(base_y + y_offset)

        # 确保不超出屏幕边界
        new_x = max(0, min(screen_width, new_x))
        new_y = max(0, min(screen_height, new_y))

        return new_x, new_y

class ElementFinder:
    """健壮的元素查找器"""

    def __init__(self, driver: webdriver.Remote):
        self.driver = driver
        self.wait = WebDriverWait(driver, settings.RECOVERY_CONFIG.get('element_wait_timeout', 10))
        self.behavior = HumanBehaviorSimulator()
        self._selector_cache = {}  # 选择器缓存
        self._cache_hits = 0
        self._cache_misses = 0

    def find_element_safe(self, by: By, value: str, timeout: int = 5, 
                         use_cache: bool = True) -> Optional[any]:
        """
        安全的元素查找，绝不崩溃
        支持选择器缓存优化性能
        """
        cache_key = f"{by}:{value}"
        
        # 检查缓存
        if use_cache and cache_key in self._selector_cache:
            cached_selector = self._selector_cache[cache_key]
            try:
                element = self.driver.find_element(cached_selector['by'], cached_selector['value'])
                if element and element.is_displayed():
                    self._cache_hits += 1
                    logger.debug(f"使用缓存选择器成功: {cache_key}")
                    return element
            except:
                # 缓存失效，清除
                del self._selector_cache[cache_key]
        
        self._cache_misses += 1
        
        # 尝试直接查找
        try:
            element = self.driver.find_element(by, value)
            if element and element.is_displayed():
                # 更新缓存
                if use_cache:
                    self._selector_cache[cache_key] = {'by': by, 'value': value}
                return element
        except (NoSuchElementException, StaleElementReferenceException) as e:
            logger.debug(f"直接查找失败: {by}={value}, 错误: {e}")

        # 使用显式等待
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            if element.is_displayed():
                if use_cache:
                    self._selector_cache[cache_key] = {'by': by, 'value': value}
                return element
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
            logger.debug(f"显式等待失败: {by}={value}, 错误: {e}")

        # 尝试查找部分匹配的文本
        if by == By.XPATH and value.startswith('//android.widget.TextView'):
            try:
                # 提取文本内容进行模糊匹配
                text_content = value.split('@text=')[-1].strip("'\"")
                elements = self.driver.find_elements(By.CLASS_NAME, 'android.widget.TextView')
                for elem in elements:
                    if elem.text and text_content.lower() in elem.text.lower():
                        if elem.is_displayed():
                            logger.info(f"模糊匹配成功: {text_content}")
                            return elem
            except Exception as e:
                logger.debug(f"模糊匹配失败: {e}")

        logger.warning(f"元素未找到: {by} = {value}")
        return None
    
    def find_element_by_selectors(self, selectors: List[Dict[str, Any]], 
                                  timeout: int = 5) -> Optional[any]:
        """
        使用选择器列表查找元素（按优先级）
        
        Args:
            selectors: 选择器列表（从 ElementSelectors 获取）
            timeout: 超时时间
            
        Returns:
            元素对象或None
        """
        for selector in sorted(selectors, key=lambda x: x.get('priority', 999)):
            try:
                element = self.find_element_safe(
                    selector['by'], 
                    selector['value'],
                    timeout=timeout
                )
                if element:
                    logger.info(f"✅ 使用选择器成功: {selector.get('description', 'N/A')}")
                    return element
            except Exception as e:
                logger.debug(f"选择器失败: {selector.get('description', 'N/A')}, 错误: {e}")
                continue
        
        logger.warning(f"所有选择器均失败，共尝试 {len(selectors)} 个")
        return None
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        total = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total * 100) if total > 0 else 0
        return {
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'hit_rate': hit_rate,
            'cache_size': len(self._selector_cache)
        }
    
    def clear_cache(self):
        """清空选择器缓存"""
        self._selector_cache.clear()
        logger.info("选择器缓存已清空")

    def find_elements_safe(self, by: By, value: str) -> List[any]:
        """安全的多个元素查找"""
        try:
            elements = self.driver.find_elements(by, value)
            return [elem for elem in elements if elem.is_displayed()]
        except (NoSuchElementException, StaleElementReferenceException):
            return []

    def wait_and_click(self, by: By, value: str, timeout: int = 10) -> bool:
        """等待元素可点击并点击"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )

            # 添加随机延迟
            self.behavior.human_like_delay()

            # 获取屏幕尺寸用于位置偏移
            screen_size = self.driver.get_window_size()

            # 获取元素位置
            location = element.location
            new_x, new_y = self.behavior.variable_touch_position(
                location['x'] + element.size['width'] // 2,
                location['y'] + element.size['height'] // 2,
                screen_size['width'],
                screen_size['height']
            )

            # 使用点击坐标而不是直接点击元素
            self.driver.tap([(new_x, new_y)], 100)

            # 模拟失误检查
            if self.behavior.simulate_mistake():
                print("🤷 模拟操作失误，重新点击...")
                time.sleep(random.uniform(0.5, 1.0))
                self.driver.tap([(location['x'] + element.size['width'] // 2,
                                 location['y'] + element.size['height'] // 2)], 100)

            return True
        except (TimeoutException, ElementNotInteractableException) as e:
            print(f"⚠️ 点击失败: {by} = {value}, 错误: {e}")
            return False

class SwipeController:
    """人性化滑动控制器"""

    def __init__(self, driver: webdriver.Remote):
        self.driver = driver
        self.behavior = HumanBehaviorSimulator()
        self.last_swipe_time = 0
        self.swipe_count = 0
        self.failed_swipes = 0
        
        # 获取反检测协调器
        if HAS_ENHANCED_MODULES:
            try:
                self.anti_detection = get_anti_detection_coordinator()
            except:
                self.anti_detection = None
        else:
            self.anti_detection = None

    def swipe_up_humanized(self, distance_ratio: float = 0.6) -> bool:
        """
        人性化的上滑操作（增强版）
        distance_ratio: 滑动距离占屏幕高度的比例
        """
        try:
            # 控制滑动频率
            current_time = time.time()
            time_since_last_swipe = current_time - self.last_swipe_time
            min_interval = random.uniform(0.8, 1.5)  # 随机最小间隔
            
            if time_since_last_swipe < min_interval:
                sleep_time = min_interval - time_since_last_swipe
                time.sleep(sleep_time)
                logger.debug(f"滑动间隔控制: 等待 {sleep_time:.2f}秒")

            screen_size = self.driver.get_window_size()
            width = screen_size['width']
            height = screen_size['height']

            # 使用增强的反检测模块生成轨迹
            if self.anti_detection and HAS_ENHANCED_MODULES:
                try:
                    behavior_sim = self.anti_detection.get_behavior_simulator()
                    trajectory = behavior_sim.generate_swipe_trajectory(width, height, "up")
                    
                    # 执行轨迹滑动（如果支持）
                    if len(trajectory) >= 2:
                        start_point = trajectory[0]
                        end_point = trajectory[-1]
                        duration = trajectory[-1][2]  # 最后一个点的时间戳
                        
                        self.driver.swipe(start_point[0], start_point[1],
                                        end_point[0], end_point[1], duration)
                        
                        logger.info(f"📱 高级轨迹滑动: 点数={len(trajectory)}, 时长={duration}ms")
                    else:
                        raise Exception("轨迹点不足")
                        
                except Exception as e:
                    logger.debug(f"高级滑动失败，使用标准模式: {e}")
                    # 回退到标准滑动
                    return self._standard_swipe_up(width, height, distance_ratio)
            else:
                # 使用标准滑动
                return self._standard_swipe_up(width, height, distance_ratio)

            self.last_swipe_time = time.time()
            self.swipe_count += 1
            
            # 偶尔添加小幅度回弹（模拟真实滑动）
            if random.random() < 0.12:  # 12%概率
                time.sleep(random.uniform(0.1, 0.3))
                bounce_distance = random.randint(15, 40)
                end_x, end_y = trajectory[-1][0], trajectory[-1][1] if HAS_ENHANCED_MODULES and self.anti_detection else (width // 2, int(height * 0.3))
                self.driver.swipe(end_x, end_y, end_x, end_y + bounce_distance, 200)
                logger.debug("添加回弹效果")

            return True

        except WebDriverException as e:
            self.failed_swipes += 1
            logger.error(f"WebDriver滑动异常: {e}", exc_info=False)
            return False
        except Exception as e:
            self.failed_swipes += 1
            logger.error(f"滑动失败: {e}")
            return False
    
    def _standard_swipe_up(self, width: int, height: int, distance_ratio: float) -> bool:
        """标准上滑操作（后备方案）"""
        try:
            # 计算滑动起始和结束位置
            start_x = width // 2
            start_y = int(height * (0.7 if distance_ratio > 0.5 else 0.6))
            end_y = int(height * (0.3 if distance_ratio > 0.5 else 0.2))

            # 添加随机偏移
            start_x, start_y = self.behavior.variable_touch_position(
                start_x, start_y, width, height
            )
            end_x, end_y = self.behavior.variable_touch_position(
                start_x, end_y, width, height
            )

            # 设置滑动参数
            if settings.ANTI_DETECTION_CONFIG.get('random_scroll_speed', True):
                duration = random.randint(300, 800)  # 300-800ms
            else:
                duration = 500

            # 执行滑动
            self.driver.swipe(start_x, start_y, end_x, end_y, duration)
            
            logger.info(f"📱 标准上滑: ({start_x}, {start_y}) -> ({end_x}, {end_y}), {duration}ms")
            return True
        except Exception as e:
            logger.error(f"标准滑动失败: {e}")
            return False
    
    def get_swipe_stats(self) -> Dict[str, Any]:
        """获取滑动统计信息"""
        success_rate = ((self.swipe_count - self.failed_swipes) / self.swipe_count * 100) if self.swipe_count > 0 else 0
        return {
            'total_swipes': self.swipe_count,
            'failed_swipes': self.failed_swipes,
            'success_rate': success_rate
        }

    def swipe_down_humanized(self, distance_ratio: float = 0.6) -> bool:
        """人性化的下滑操作"""
        try:
            screen_size = self.driver.get_window_size()
            width = screen_size['width']
            height = screen_size['height']

            start_x = width // 2
            start_y = int(height * 0.3)
            end_y = int(height * 0.7)

            # 添加随机偏移
            start_x, start_y = self.behavior.variable_touch_position(
                start_x, start_y, width, height
            )
            end_x, end_y = self.behavior.variable_touch_position(
                start_x, end_y, width, height
            )

            duration = random.randint(300, 800) if settings.ANTI_DETECTION_CONFIG.get('random_scroll_speed', True) else 500

            self.driver.swipe(start_x, start_y, end_x, end_y, duration)
            return True

        except Exception as e:
            print(f"❌ 下滑失败: {e}")
            return False

class InputController:
    """安全的输入控制器"""

    def __init__(self, driver: webdriver.Remote):
        self.driver = driver
        self.behavior = HumanBehaviorSimulator()
        self.finder = ElementFinder(driver)

    def send_keys_safe(self, element, text: str, clear_first: bool = True) -> bool:
        """
        安全的文本输入
        """
        try:
            if not element:
                return False

            # 确保元素可交互
            if not element.is_displayed() or not element.is_enabled():
                print("⚠️ 元素不可交互")
                return False

            # 点击元素聚焦
            element.click()
            self.behavior.human_like_delay()

            # 清空现有文本
            if clear_first:
                element.clear()
                self.behavior.random_pause(0.3, 0.8)

            # 模拟人类打字速度
            for char in text:
                element.send_keys(char)
                # 随机打字间隔
                if char in [' ', '@', '#', '.']:
                    time.sleep(random.uniform(0.2, 0.4))  # 特殊字符慢一点
                else:
                    time.sleep(random.uniform(0.05, 0.15))  # 普通字符

            # 完成后的随机延迟
            self.behavior.human_like_delay()
            print(f"⌨️ 安全输入: {text}")
            return True

        except Exception as e:
            print(f"❌ 输入失败: {e}")
            return False

    def send_keys_by_locator(self, by: By, value: str, text: str) -> bool:
        """通过定位器查找元素并输入"""
        element = self.finder.find_element_safe(by, value)
        return self.send_keys_safe(element, text)

# 全局工具实例初始化
_finder = None
_swipe_controller = None
_input_controller = None

def init_utils(driver: webdriver.Remote):
    """初始化工具实例"""
    global _finder, _swipe_controller, _input_controller
    _finder = ElementFinder(driver)
    _swipe_controller = SwipeController(driver)
    _input_controller = InputController(driver)

def find_element_safe(by: By, value: str, timeout: int = 5) -> Optional[any]:
    """安全的元素查找"""
    if _finder is None:
        raise RuntimeError("工具未初始化，请先调用 init_utils()")
    return _finder.find_element_safe(by, value, timeout)

def find_elements_safe(by: By, value: str) -> List[any]:
    """安全的多个元素查找"""
    if _finder is None:
        raise RuntimeError("工具未初始化，请先调用 init_utils()")
    return _finder.find_elements_safe(by, value)

def wait_and_click(by: By, value: str, timeout: int = 10) -> bool:
    """等待元素可点击并点击"""
    if _finder is None:
        raise RuntimeError("工具未初始化，请先调用 init_utils()")
    return _finder.wait_and_click(by, value, timeout)

def swipe_up_humanized(distance_ratio: float = 0.6) -> bool:
    """人性化上滑"""
    if _swipe_controller is None:
        raise RuntimeError("工具未初始化，请先调用 init_utils()")
    return _swipe_controller.swipe_up_humanized(distance_ratio)

def swipe_down_humanized(distance_ratio: float = 0.6) -> bool:
    """人性化下滑"""
    if _swipe_controller is None:
        raise RuntimeError("工具未初始化，请先调用 init_utils()")
    return _swipe_controller.swipe_down_humanized(distance_ratio)

def send_keys_safe(element, text: str, clear_first: bool = True) -> bool:
    """安全的文本输入"""
    if _input_controller is None:
        raise RuntimeError("工具未初始化，请先调用 init_utils()")
    return _input_controller.send_keys_safe(element, text, clear_first)

def human_like_delay():
    """人性化延迟"""
    HumanBehaviorSimulator.human_like_delay()

def random_pause(min_seconds: float = 0.5, max_seconds: float = 2.0):
    """随机暂停"""
    HumanBehaviorSimulator.random_pause(min_seconds, max_seconds)