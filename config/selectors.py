"""
元素选择器配置中心
支持多版本抖音应用的元素定位
"""

from typing import Dict, List, Any
from appium.webdriver.common.appiumby import AppiumBy as By


class SelectorVersion:
    """选择器版本管理"""
    V28_PLUS = ">=28.0"  # 抖音28.0及以上版本
    V27_PLUS = ">=27.0"  # 抖音27.0及以上版本
    LEGACY = "<27.0"     # 旧版本
    ALL = "*"            # 通用选择器


class ElementSelectors:
    """元素选择器配置类
    
    选择器优先级说明：
    - UIAutomator (ANDROID_UIAUTOMATOR): 最快，原生Android定位
    - ID: 较快，但可能随版本变化
    - XPATH: 最慢，但最灵活
    """
    
    # 点赞按钮选择器（优先级从高到低）
    LIKE_BUTTON = [
        {
            "by": By.ANDROID_UIAUTOMATOR,
            "value": 'new UiSelector().descriptionContains("赞")',
            "version": SelectorVersion.ALL,
            "priority": 0,
            "description": "UIAutomator定位点赞（最快）"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.ImageView[@content-desc and contains(@content-desc, '赞')]",
            "version": SelectorVersion.ALL,
            "priority": 1,
            "description": "通过ImageView的content-desc匹配点赞（最可靠）"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.LinearLayout[@content-desc and contains(@content-desc, '赞')]",
            "version": SelectorVersion.ALL,
            "priority": 2,
            "description": "通过LinearLayout的content-desc匹配点赞"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/f_u",
            "version": SelectorVersion.ALL,
            "priority": 3,
            "description": "抖音旧版本点赞按钮ID"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/hq+",
            "version": SelectorVersion.ALL,
            "priority": 4,
            "description": "抖音新版本点赞按钮ID（2024年11月提取）"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.LinearLayout[contains(@content-desc, '喜欢')]",
            "version": SelectorVersion.ALL,
            "priority": 5,
            "description": "通过喜欢匹配点赞按钮"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/a3o",
            "version": SelectorVersion.V28_PLUS,
            "priority": 6,
            "description": "抖音28.0+版本主点赞按钮"
        }
    ]
    
    # 评论按钮选择器
    COMMENT_BUTTON = [
        {
            "by": By.ANDROID_UIAUTOMATOR,
            "value": 'new UiSelector().descriptionContains("评论")',
            "version": SelectorVersion.ALL,
            "priority": 0,
            "description": "UIAutomator定位评论（最快）"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.ImageView[@content-desc and contains(@content-desc, '评论')]",
            "version": SelectorVersion.ALL,
            "priority": 1,
            "description": "通过ImageView的content-desc匹配评论（最可靠）"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.LinearLayout[@content-desc and contains(@content-desc, '评论')]",
            "version": SelectorVersion.ALL,
            "priority": 2,
            "description": "通过LinearLayout的content-desc匹配评论"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/eiz",
            "version": SelectorVersion.ALL,
            "priority": 3,
            "description": "抖音旧版本评论按钮"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/a3p",
            "version": SelectorVersion.V28_PLUS,
            "priority": 4,
            "description": "抖音28.0+版本主评论按钮"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/comment_btn",
            "version": SelectorVersion.V27_PLUS,
            "priority": 5,
            "description": "抖音27.0+版本评论按钮"
        }
    ]
    
    # 评论输入框选择器
    COMMENT_INPUT = [
        {
            "by": By.ANDROID_UIAUTOMATOR,
            "value": 'new UiSelector().className("android.widget.EditText")',
            "version": SelectorVersion.ALL,
            "priority": 0,
            "description": "UIAutomator定位输入框（最快）"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.EditText[contains(@text, '友善') or contains(@text, '精彩') or contains(@text, '评论')]",
            "version": SelectorVersion.ALL,
            "priority": 1,
            "description": "通过EditText的文本匹配评论输入框（最可靠）"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/ebm",
            "version": SelectorVersion.ALL,
            "priority": 2,
            "description": "抖音新版本评论输入框（2024年11月提取）"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/aov",
            "version": SelectorVersion.V28_PLUS,
            "priority": 3,
            "description": "抖音28.0+版本评论输入框"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/comment_input",
            "version": SelectorVersion.V27_PLUS,
            "priority": 4,
            "description": "抖音27.0+版本评论输入框"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.EditText",
            "version": SelectorVersion.ALL,
            "priority": 5,
            "description": "通用输入框"
        }
    ]
    
    # 评论发送按钮
    COMMENT_SEND_BUTTON = [
        {
            "by": By.ANDROID_UIAUTOMATOR,
            "value": 'new UiSelector().text("发送")',
            "version": SelectorVersion.ALL,
            "priority": 0,
            "description": "UIAutomator定位发送按钮（最快）"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/aot",
            "version": SelectorVersion.V28_PLUS,
            "priority": 1,
            "description": "抖音28.0+版本发送按钮"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.TextView[@text='发送']",
            "version": SelectorVersion.ALL,
            "priority": 2,
            "description": "发送文本按钮"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.Button[@text='发送']",
            "version": SelectorVersion.ALL,
            "priority": 3,
            "description": "发送按钮"
        }
    ]
    
    # 收藏按钮选择器
    FAVORITE_BUTTON = [
        {
            "by": By.ANDROID_UIAUTOMATOR,
            "value": 'new UiSelector().descriptionContains("收藏")',
            "version": SelectorVersion.ALL,
            "priority": 0,
            "description": "UIAutomator定位收藏（最快）"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.ImageView[@content-desc and contains(@content-desc, '收藏')]",
            "version": SelectorVersion.ALL,
            "priority": 1,
            "description": "通过ImageView的content-desc匹配收藏（最可靠）"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.LinearLayout[@content-desc and contains(@content-desc, '收藏')]",
            "version": SelectorVersion.ALL,
            "priority": 2,
            "description": "通过LinearLayout的content-desc匹配收藏"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.ImageView[@content-desc and contains(@content-desc, '星')]",
            "version": SelectorVersion.ALL,
            "priority": 3,
            "description": "通过星星图标匹配收藏"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/d-5",
            "version": SelectorVersion.ALL,
            "priority": 4,
            "description": "抖音旧版本收藏按钮"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/a3q",
            "version": SelectorVersion.V28_PLUS,
            "priority": 5,
            "description": "抖音28.0+版本收藏按钮"
        }
    ]
    
    # 关注按钮选择器
    FOLLOW_BUTTON = [
        {
            "by": By.ANDROID_UIAUTOMATOR,
            "value": 'new UiSelector().descriptionContains("关注")',
            "version": SelectorVersion.ALL,
            "priority": 0,
            "description": "UIAutomator定位关注（最快）"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.ImageView[@content-desc and contains(@content-desc, '关注')]",
            "version": SelectorVersion.ALL,
            "priority": 1,
            "description": "通过ImageView的content-desc匹配关注（最可靠）"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.TextView[@text='关注']",
            "version": SelectorVersion.ALL,
            "priority": 2,
            "description": "关注文本按钮"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.Button[@content-desc='关注']",
            "version": SelectorVersion.ALL,
            "priority": 3,
            "description": "通过Button的content-desc匹配关注"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/jjd",
            "version": SelectorVersion.ALL,
            "priority": 4,
            "description": "抖音旧版本关注按钮"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/title_text",
            "version": SelectorVersion.V28_PLUS,
            "priority": 5,
            "description": "抖音28.0+版本关注按钮"
        }
    ]
    
    # 搜索框选择器
    SEARCH_ENTRY = [
        {
            "by": By.ANDROID_UIAUTOMATOR,
            "value": 'new UiSelector().description("搜索")',
            "version": SelectorVersion.ALL,
            "priority": 0,
            "description": "UIAutomator定位搜索（最快）"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.Button[@content-desc='搜索']",
            "version": SelectorVersion.ALL,
            "priority": 1,
            "description": "抖音当前版本搜索按钮（实测有效）"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/1f1",
            "version": SelectorVersion.ALL,
            "priority": 2,
            "description": "抖音当前版本搜索ID"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/a1o",
            "version": SelectorVersion.V28_PLUS,
            "priority": 3,
            "description": "抖音28.0+版本搜索入口"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.ImageView[@content-desc='搜索']",
            "version": SelectorVersion.ALL,
            "priority": 4,
            "description": "搜索图标"
        }
    ]
    
    # 搜索输入框
    SEARCH_INPUT = [
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/et_search_kw",
            "version": SelectorVersion.V28_PLUS,
            "priority": 1,
            "description": "抖音28.0+版本搜索输入框"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.EditText",
            "version": SelectorVersion.ALL,
            "priority": 2,
            "description": "通用输入框"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.TextView[@text='搜你想看的']",
            "version": SelectorVersion.ALL,
            "priority": 3,
            "description": "搜索占位符"
        }
    ]
    
    # 首页按钮
    HOME_BUTTON = [
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/a1f",
            "version": SelectorVersion.V28_PLUS,
            "priority": 1,
            "description": "抖音28.0+版本首页按钮"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.ImageView[@content-desc='首页']",
            "version": SelectorVersion.ALL,
            "priority": 2,
            "description": "首页图标"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.TextView[@text='首页']",
            "version": SelectorVersion.ALL,
            "priority": 3,
            "description": "首页文本"
        }
    ]
    
    # 推荐Tab
    FOR_YOU_TAB = [
        {
            "by": By.XPATH,
            "value": "//android.widget.TextView[@text='推荐']",
            "version": SelectorVersion.ALL,
            "priority": 1,
            "description": "推荐Tab"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.TextView[contains(@text, '推荐')]",
            "version": SelectorVersion.ALL,
            "priority": 2,
            "description": "模糊匹配推荐"
        }
    ]
    
    # 视频Tab
    VIDEO_TAB = [
        {
            "by": By.XPATH,
            "value": "//android.widget.TextView[@text='视频']",
            "version": SelectorVersion.ALL,
            "priority": 1,
            "description": "视频Tab"
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.TextView[contains(@text, '视频')]",
            "version": SelectorVersion.ALL,
            "priority": 2,
            "description": "模糊匹配视频"
        },
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/tab_name",
            "version": SelectorVersion.ALL,
            "priority": 3,
            "description": "Tab名称"
        }
    ]
    
    # 弹窗选择器（按优先级排序）
    POPUP_SELECTORS = [
        # 青少年模式
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/q7",
            "action": "close_youth_mode",
            "priority": 1
        },
        # 更新提示
        {
            "by": By.ID,
            "value": "com.ss.android.ugc.aweme:id/arh",
            "action": "close_update",
            "priority": 2
        },
        # 权限请求
        {
            "by": By.ID,
            "value": "com.android.packageinstaller:id/permission_allow_button",
            "action": "allow_permission",
            "priority": 3
        },
        # 位置权限拒绝
        {
            "by": By.XPATH,
            "value": "//android.widget.TextView[@text='拒绝']",
            "action": "deny_location",
            "priority": 4
        },
        # 通知权限
        {
            "by": By.XPATH,
            "value": "//android.widget.TextView[@text='暂不开启']",
            "action": "deny_notification",
            "priority": 5
        },
        # 好友推荐
        {
            "by": By.XPATH,
            "value": "//android.widget.TextView[@text='残忍拒绝']",
            "action": "reject_friends",
            "priority": 6
        },
        # 活动弹窗关闭
        {
            "by": By.XPATH,
            "value": "//android.widget.ImageView[@content-desc='关闭']",
            "action": "close_activity",
            "priority": 7
        },
        # 通用关闭按钮
        {
            "by": By.XPATH,
            "value": "//android.widget.Button[@text='我知道了']",
            "action": "got_it",
            "priority": 8
        },
        {
            "by": By.XPATH,
            "value": "//android.widget.TextView[@text='稍后']",
            "action": "later",
            "priority": 9
        }
    ]
    
    @classmethod
    def get_selectors(cls, selector_name: str) -> List[Dict[str, Any]]:
        """
        获取指定的选择器列表
        
        Args:
            selector_name: 选择器名称（如 'LIKE_BUTTON'）
            
        Returns:
            List[Dict]: 选择器列表
        """
        return getattr(cls, selector_name, [])
    
    @classmethod
    def add_custom_selector(cls, selector_name: str, selector_config: Dict[str, Any]):
        """
        添加自定义选择器
        
        Args:
            selector_name: 选择器名称
            selector_config: 选择器配置
        """
        if not hasattr(cls, selector_name):
            setattr(cls, selector_name, [])
        
        selectors = getattr(cls, selector_name)
        selectors.append(selector_config)
        selectors.sort(key=lambda x: x.get('priority', 999))


# 导出常用选择器
LIKE_BUTTON = ElementSelectors.LIKE_BUTTON
COMMENT_BUTTON = ElementSelectors.COMMENT_BUTTON
COMMENT_INPUT = ElementSelectors.COMMENT_INPUT
SEARCH_ENTRY = ElementSelectors.SEARCH_ENTRY
SEARCH_INPUT = ElementSelectors.SEARCH_INPUT
POPUP_SELECTORS = ElementSelectors.POPUP_SELECTORS

