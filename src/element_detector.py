"""
智能元素检测器模块
提供统一的元素查找、缓存、统计和动态调整功能
"""

import time
import json
import os
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy as By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 导入日志系统
try:
    from .logger import get_logger
    logger = get_logger(__name__)
except:
    import logging
    logger = logging.getLogger(__name__)


class ElementDetector:
    """智能元素检测器"""
    
    def __init__(self, driver: webdriver.Remote, config_file: str = "config/element_detection_stats.json"):
        """
        初始化元素检测器
        
        Args:
            driver: Appium driver实例
            config_file: 统计数据保存文件
        """
        self.driver = driver
        self.config_file = config_file
        
        # 统计数据
        self.stats = self._load_stats()
        
        # 缓存
        self.cache = {}
        self.cache_ttl = 30  # 缓存有效期（秒）
        
        logger.info("元素检测器已初始化")
    
    def _load_stats(self) -> Dict[str, Any]:
        """加载统计数据"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载统计数据失败: {e}")
        
        return {
            'like_button': {},
            'comment_button': {},
            'favorite_button': {},
            'follow_button': {},
            'comment_input': {},
            'send_button': {}
        }
    
    def _save_stats(self):
        """保存统计数据"""
        try:
            os.makedirs(os.path.dirname(self.config_file) if os.path.dirname(self.config_file) else ".", exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存统计数据失败: {e}")
    
    def _update_stats(self, button_type: str, selector_key: str, success: bool):
        """
        更新选择器统计数据
        
        Args:
            button_type: 按钮类型
            selector_key: 选择器标识
            success: 是否成功
        """
        if button_type not in self.stats:
            self.stats[button_type] = {}
        
        if selector_key not in self.stats[button_type]:
            self.stats[button_type][selector_key] = {
                'success_count': 0,
                'fail_count': 0,
                'last_success': None,
                'last_fail': None
            }
        
        stat = self.stats[button_type][selector_key]
        
        if success:
            stat['success_count'] += 1
            stat['last_success'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            stat['fail_count'] += 1
            stat['last_fail'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 每10次更新保存一次
        total_count = sum(s.get('success_count', 0) + s.get('fail_count', 0) 
                         for s in self.stats[button_type].values())
        if total_count % 10 == 0:
            self._save_stats()
    
    def _get_selector_key(self, by: str, value: str) -> str:
        """生成选择器唯一标识"""
        return f"{by}:{value[:50]}"
    
    def _sort_selectors_by_success_rate(self, button_type: str, selectors: List[Dict]) -> List[Dict]:
        """
        根据成功率对选择器排序
        
        Args:
            button_type: 按钮类型
            selectors: 选择器列表
            
        Returns:
            排序后的选择器列表
        """
        if button_type not in self.stats:
            return selectors
        
        def get_score(selector):
            key = self._get_selector_key(selector['by'], selector['value'])
            stat = self.stats[button_type].get(key, {})
            
            success = stat.get('success_count', 0)
            fail = stat.get('fail_count', 0)
            total = success + fail
            
            if total == 0:
                # 没有统计数据，使用原始优先级
                return (0, -selector.get('priority', 999))
            
            # 成功率
            success_rate = success / total if total > 0 else 0
            
            # 最近成功加分
            last_success = stat.get('last_success')
            recent_bonus = 0
            if last_success:
                try:
                    last_time = datetime.strptime(last_success, '%Y-%m-%d %H:%M:%S')
                    hours_ago = (datetime.now() - last_time).total_seconds() / 3600
                    if hours_ago < 24:
                        recent_bonus = 0.2
                except:
                    pass
            
            # 综合得分：成功率 + 最近成功加分 - 原始优先级权重
            score = success_rate + recent_bonus - (selector.get('priority', 999) * 0.01)
            
            return (-score, selector.get('priority', 999))  # 负号使得高分排前面
        
        sorted_selectors = sorted(selectors, key=get_score)
        return sorted_selectors
    
    def find_element_smart(self, button_type: str, selectors: List[Dict], 
                          timeout: int = 3, use_cache: bool = True) -> Optional[Any]:
        """
        智能查找元素
        
        Args:
            button_type: 按钮类型（用于统计）
            selectors: 选择器列表
            timeout: 超时时间
            use_cache: 是否使用缓存
            
        Returns:
            找到的元素，未找到返回None
        """
        # 检查缓存
        if use_cache:
            cache_key = button_type
            if cache_key in self.cache:
                cached_time, cached_selector = self.cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    try:
                        element = self._find_by_selector(cached_selector, timeout=1)
                        if element:
                            logger.debug(f"从缓存找到 {button_type}")
                            return element
                    except:
                        pass
        
        # 根据成功率排序选择器
        sorted_selectors = self._sort_selectors_by_success_rate(button_type, selectors)
        
        logger.info(f"🔍 查找 {button_type}（共{len(sorted_selectors)}个选择器）")
        
        # 尝试每个选择器
        for i, selector in enumerate(sorted_selectors, 1):
            by_type = "ID" if selector["by"] == By.ID else "XPATH"
            selector_key = self._get_selector_key(selector['by'], selector['value'])
            
            # 显示统计信息
            stat = self.stats.get(button_type, {}).get(selector_key, {})
            success_count = stat.get('success_count', 0)
            fail_count = stat.get('fail_count', 0)
            total = success_count + fail_count
            success_rate = (success_count / total * 100) if total > 0 else 0
            
            stat_info = f"(历史成功率: {success_rate:.0f}%)" if total > 0 else "(首次尝试)"
            
            logger.info(f"  [{i}/{len(sorted_selectors)}] {by_type}: {selector['value'][:60]}... {stat_info}")
            
            try:
                element = self._find_by_selector(selector, timeout)
                if element:
                    logger.info(f"✅ 找到元素！（选择器 {i}）")
                    
                    # 更新统计
                    self._update_stats(button_type, selector_key, success=True)
                    
                    # 更新缓存
                    if use_cache:
                        self.cache[button_type] = (time.time(), selector)
                    
                    return element
                else:
                    self._update_stats(button_type, selector_key, success=False)
                    
            except Exception as e:
                logger.debug(f"  选择器 {i} 失败: {e}")
                self._update_stats(button_type, selector_key, success=False)
        
        logger.warning(f"❌ 未找到 {button_type}")
        return None
    
    def _find_by_selector(self, selector: Dict, timeout: int) -> Optional[Any]:
        """
        使用单个选择器查找元素
        
        Args:
            selector: 选择器配置
            timeout: 超时时间
            
        Returns:
            找到的元素
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(
                EC.presence_of_element_located((selector['by'], selector['value']))
            )
            return element
        except (NoSuchElementException, TimeoutException):
            return None
    
    def click_element(self, element: Any, fallback_selector: Optional[Dict] = None) -> bool:
        """
        点击元素（带降级策略）
        
        Args:
            element: 要点击的元素
            fallback_selector: 失败时的备用选择器
            
        Returns:
            是否成功
        """
        try:
            element.click()
            return True
        except Exception as e:
            logger.debug(f"直接点击失败: {e}，尝试备用方法")
            
            # 尝试通过选择器点击
            if fallback_selector:
                try:
                    wait = WebDriverWait(self.driver, 2)
                    element = wait.until(
                        EC.element_to_be_clickable((fallback_selector['by'], fallback_selector['value']))
                    )
                    element.click()
                    return True
                except:
                    pass
            
            # 尝试通过坐标点击
            try:
                location = element.location
                size = element.size
                x = location['x'] + size['width'] // 2
                y = location['y'] + size['height'] // 2
                self.driver.tap([(x, y)], 100)
                return True
            except Exception as e2:
                logger.warning(f"所有点击方法都失败: {e2}")
                return False
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        summary = {}
        
        for button_type, selectors in self.stats.items():
            if not selectors:
                continue
            
            total_success = sum(s.get('success_count', 0) for s in selectors.values())
            total_fail = sum(s.get('fail_count', 0) for s in selectors.values())
            total = total_success + total_fail
            
            if total > 0:
                summary[button_type] = {
                    'total_attempts': total,
                    'success_count': total_success,
                    'success_rate': total_success / total * 100,
                    'best_selector': self._get_best_selector(button_type)
                }
        
        return summary
    
    def _get_best_selector(self, button_type: str) -> Optional[str]:
        """获取最佳选择器"""
        if button_type not in self.stats:
            return None
        
        best_key = None
        best_rate = 0
        
        for key, stat in self.stats[button_type].items():
            success = stat.get('success_count', 0)
            total = success + stat.get('fail_count', 0)
            
            if total >= 5:  # 至少5次尝试
                rate = success / total
                if rate > best_rate:
                    best_rate = rate
                    best_key = key
        
        return best_key
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("元素检测器缓存已清空")
    
    def export_stats(self, output_file: str = None):
        """导出统计数据"""
        if output_file is None:
            output_file = f"logs/element_stats_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        export_data = {
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stats': self.stats,
            'summary': self.get_stats_summary()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"统计数据已导出到: {output_file}")
        return output_file


# 全局单例
_detector_instance = None


def get_element_detector(driver: webdriver.Remote = None) -> ElementDetector:
    """
    获取元素检测器单例
    
    Args:
        driver: Appium driver实例（首次调用时必须提供）
        
    Returns:
        ElementDetector实例
    """
    global _detector_instance
    
    if _detector_instance is None:
        if driver is None:
            raise ValueError("首次调用必须提供driver参数")
        _detector_instance = ElementDetector(driver)
    
    return _detector_instance


def reset_detector():
    """重置元素检测器（用于测试）"""
    global _detector_instance
    _detector_instance = None

