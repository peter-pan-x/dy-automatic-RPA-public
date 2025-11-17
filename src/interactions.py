"""
业务插件模块 - 抖音具体交互操作
包含点赞、评论、搜索、弹窗处理等业务逻辑
"""

import time
import random
from typing import Optional, List
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy as By
from . import core_utils
import config.settings as settings

class DouyinInteractions:
    """抖音交互操作类"""

    def __init__(self, driver: webdriver.Remote):
        self.driver = driver
        # 初始化工具库
        core_utils.init_utils(driver)

    def dismiss_popups_if_present(self) -> bool:
        """
        处理各种弹窗（健壮性要求：每次循环前都调用）
        """
        handled_count = 0

        # 弹窗列表（按优先级排序）
        popup_selectors = [
            # 青少年模式弹窗
            {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/q7", "action": "close_youth_mode"},
            # 更新提示
            {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/arh", "action": "close_update"},
            # 权限请求
            {"by": By.ID, "value": "com.android.packageinstaller:id/permission_allow_button", "action": "allow_permission"},
            # 位置权限
            {"by": By.XPATH, "value": "//android.widget.TextView[@text='拒绝']", "action": "deny_location"},
            # 通知权限
            {"by": By.XPATH, "value": "//android.widget.TextView[@text='暂不开启']", "action": "deny_notification"},
            # 好友推荐弹窗
            {"by": By.XPATH, "value": "//android.widget.TextView[@text='残忍拒绝']", "action": "reject_friends"},
            # 活动弹窗关闭按钮
            {"by": By.XPATH, "value": "//android.widget.ImageView[@content-desc='关闭']", "action": "close_activity"},
            # 通用关闭按钮
            {"by": By.XPATH, "value": "//android.widget.Button[@text='我知道了']", "action": "got_it"},
            {"by": By.XPATH, "value": "//android.widget.TextView[@text='稍后']", "action": "later"},
        ]

        for popup in popup_selectors:
            try:
                element = core_utils.find_element_safe(popup["by"], popup["value"], timeout=2)
                if element:
                    if core_utils.wait_and_click(popup["by"], popup["value"]):
                        handled_count += 1
                        print(f"✅ 处理弹窗: {popup['action']}")
                        core_utils.random_pause(0.5, 1.0)
            except Exception as e:
                print(f"⚠️ 处理弹窗异常: {popup['action']}, 错误: {e}")

        if handled_count > 0:
            print(f"🧹 本次处理了 {handled_count} 个弹窗")
        return handled_count > 0

    def like_current_video(self) -> bool:
        """
        点赞当前视频
        """
        try:
            # 点赞按钮定位方式（使用更新后的选择器，优先XPath方式）
            like_selectors = [
                {"by": By.XPATH, "value": "//android.widget.ImageView[@content-desc and contains(@content-desc, '赞')]"},
                {"by": By.XPATH, "value": "//android.widget.LinearLayout[@content-desc and contains(@content-desc, '赞')]"},
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/f_u"},
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/hq+"},  # 新版本ID
                {"by": By.XPATH, "value": "//android.widget.LinearLayout[contains(@content-desc, '喜欢')]"},
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/a3o"},
            ]

            print(f"❤️ 查找点赞按钮（共{len(like_selectors)}个选择器）")
            for i, selector in enumerate(like_selectors, 1):
                by_type = "ID" if selector["by"] == By.ID else "XPATH"
                print(f"  [{i}/{len(like_selectors)}] 尝试 {by_type}: {selector['value'][:60]}...")
                element = core_utils.find_element_safe(selector["by"], selector["value"], timeout=3)
                if element:
                    # 检查是否已经点赞
                    try:
                        content_desc = element.get_attribute("content-desc") or ""
                        if "已点赞" in content_desc or "赞过了" in content_desc:
                            print("❤️ 视频已经点赞，跳过")
                            return True
                    except:
                        pass  # 忽略属性获取失败

                    # 点击点赞
                    try:
                        element.click()
                        print(f"✅ 点赞成功！（选择器 {i}）")
                        core_utils.human_like_delay()
                        return True
                    except:
                        # 尝试使用wait_and_click
                        if core_utils.wait_and_click(selector["by"], selector["value"], timeout=2):
                            print(f"✅ 点赞成功！（选择器 {i}）")
                            core_utils.human_like_delay()
                            return True

            print("⚠️ 未找到点赞按钮")
            return False

        except Exception as e:
            print(f"❌ 点赞失败: {e}")
            return False

    def comment_on_current_video(self, comment_text: str) -> bool:
        """
        评论当前视频
        优化流程：点击评论按钮 → 进入评论列表 → 点击输入框激活 → 输入内容 → 发送 → 返回
        """
        try:
            # === 第1步：点击评论按钮，进入评论列表页面 ===
            print("💬 [1/6] 查找并点击评论按钮...")
            comment_selectors = [
                {"by": By.XPATH, "value": "//android.widget.ImageView[@content-desc and contains(@content-desc, '评论')]"},
                {"by": By.XPATH, "value": "//android.widget.LinearLayout[@content-desc and contains(@content-desc, '评论')]"},
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/eiz"},
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/a3p"},
            ]

            comment_clicked = False
            for i, selector in enumerate(comment_selectors, 1):
                print(f"  尝试选择器 [{i}/{len(comment_selectors)}]")
                if core_utils.wait_and_click(selector["by"], selector["value"], timeout=3):
                    print("✅ 评论按钮已点击，进入评论列表页面")
                    comment_clicked = True
                    break

            if not comment_clicked:
                print("❌ 未找到评论按钮")
                return False

            # 等待页面加载
            print("⏳ 等待评论页面加载...")
            core_utils.random_pause(2.5, 3.5)

            # === 第2步：查找并点击输入框激活 ===
            print("💬 [2/6] 查找并点击输入框...")
            input_selectors = [
                {"by": By.XPATH, "value": "//android.widget.EditText"},
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/ebm"},
                {"by": By.XPATH, "value": "//android.widget.EditText[contains(@text, '友善')]"},
            ]

            input_element = None
            for i, selector in enumerate(input_selectors, 1):
                print(f"  尝试选择器 [{i}/{len(input_selectors)}]")
                input_element = core_utils.find_element_safe(selector["by"], selector["value"], timeout=2)
                if input_element:
                    print(f"✅ 找到评论输入框（选择器 {i}）")
                    break

            if not input_element:
                print("❌ 未找到评论输入框")
                self._close_comment_section()
                return False

            # === 第3步：点击输入框激活 ===
            print("💬 [3/6] 点击输入框激活...")
            try:
                input_element.click()
                print("✅ 输入框已激活")
            except Exception as e:
                print(f"⚠️ 点击输入框失败: {e}")

            # 等待键盘弹出
            print("⏳ 等待键盘弹出...")
            core_utils.random_pause(1.5, 2.5)

            # === 第4步：重新查找输入框并输入（解决元素过期问题）===
            print(f"💬 [4/6] 重新查找输入框并输入: {comment_text[:20]}...")
            input_success = False
            
            # 重新查找输入框（避免StaleElementReferenceException）
            for i, selector in enumerate(input_selectors, 1):
                try:
                    fresh_input = core_utils.find_element_safe(selector["by"], selector["value"], timeout=2)
                    if fresh_input:
                        fresh_input.send_keys(comment_text)
                        print(f"✅ 评论内容已输入（选择器 {i}）")
                        input_success = True
                        break
                except Exception as e:
                    print(f"  输入失败: {str(e)[:50]}")
                    continue

            if not input_success:
                print("❌ 评论输入失败")
                self._close_comment_section()
                return False

            core_utils.random_pause(0.8, 1.5)

            # === 第5步：查找并点击发送按钮 ===
            print("💬 [5/6] 查找并点击发送按钮...")
            send_selectors = [
                {"by": By.XPATH, "value": "//android.widget.TextView[@text='发送']"},
                {"by": By.XPATH, "value": "//android.widget.Button[@text='发送']"},
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/aot"},
                {"by": By.XPATH, "value": "//*[@text='发送']"},
            ]

            send_clicked = False
            for i, selector in enumerate(send_selectors, 1):
                print(f"  尝试选择器 [{i}/{len(send_selectors)}]")
                if core_utils.wait_and_click(selector["by"], selector["value"], timeout=2):
                    print(f"✅ 评论发送成功: {comment_text}")
                    send_clicked = True
                    break

            if not send_clicked:
                print("❌ 未找到发送按钮")
                self._close_comment_section()
                return False

            # 等待发送完成
            core_utils.random_pause(1.5, 2.5)

            # === 第6步：返回视频页面 ===
            print("💬 [6/6] 返回视频页面...")
            self._close_comment_section()
            core_utils.random_pause(1.0, 1.5)

            return True

        except Exception as e:
            print(f"❌ 评论过程异常: {e}")
            import traceback
            traceback.print_exc()
            self._close_comment_section()
            return False

    def _close_comment_section(self):
        """关闭评论区，返回到视频页面"""
        try:
            # 方法1：查找并点击返回按钮
            back_selectors = [
                {"by": By.XPATH, "value": "//android.widget.ImageView[@content-desc='返回']"},
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/a1i"},
                {"by": By.XPATH, "value": "//android.widget.ImageView[@content-desc='关闭']"},
            ]

            for selector in back_selectors:
                if core_utils.wait_and_click(selector["by"], selector["value"], timeout=2):
                    print("🔙 通过返回按钮关闭评论区")
                    return

            # 方法2：使用Android返回键（最可靠）
            print("🔙 使用返回键关闭评论区")
            self.driver.press_keycode(4)  # Android BACK键
            
        except Exception as e:
            print(f"⚠️ 关闭评论区失败: {e}，尝试按返回键")
            try:
                self.driver.press_keycode(4)
            except:
                pass

    def favorite_current_video(self) -> bool:
        """
        收藏当前视频
        """
        try:
            favorite_selectors = [
                {"by": By.XPATH, "value": "//android.widget.ImageView[@content-desc and contains(@content-desc, '收藏')]"},
                {"by": By.XPATH, "value": "//android.widget.LinearLayout[@content-desc and contains(@content-desc, '收藏')]"},
                {"by": By.XPATH, "value": "//android.widget.ImageView[@content-desc and contains(@content-desc, '星')]"},
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/d-5"},
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/a3q"},
            ]

            print(f"⭐ 查找收藏按钮（共{len(favorite_selectors)}个选择器）")
            for i, selector in enumerate(favorite_selectors, 1):
                by_type = "ID" if selector["by"] == By.ID else "XPATH"
                print(f"  [{i}/{len(favorite_selectors)}] 尝试 {by_type}: {selector['value'][:60]}...")
                element = core_utils.find_element_safe(selector["by"], selector["value"], timeout=3)
                if element:
                    # 检查是否已收藏
                    try:
                        content_desc = element.get_attribute("content-desc") or ""
                        if "已收藏" in content_desc:
                            print("⭐ 视频已收藏，跳过")
                            return True
                    except:
                        pass

                    # 点击收藏
                    try:
                        element.click()
                        print(f"✅ 收藏成功！（选择器 {i}）")
                        core_utils.human_like_delay()
                        return True
                    except:
                        if core_utils.wait_and_click(selector["by"], selector["value"], timeout=2):
                            print(f"✅ 收藏成功！（选择器 {i}）")
                            core_utils.human_like_delay()
                            return True

            print("⚠️ 未找到收藏按钮")
            return False

        except Exception as e:
            print(f"❌ 收藏失败: {e}")
            return False

    def follow_current_author(self) -> bool:
        """
        关注当前视频作者
        """
        try:
            follow_selectors = [
                {"by": By.XPATH, "value": "//android.widget.ImageView[@content-desc and contains(@content-desc, '关注')]"},
                {"by": By.XPATH, "value": "//android.widget.TextView[@text='关注']"},
                {"by": By.XPATH, "value": "//android.widget.Button[@content-desc='关注']"},
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/jjd"},
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/title_text"},
                {"by": By.XPATH, "value": "//android.widget.Button[@text='关注']"},
            ]

            print(f"👥 查找关注按钮（共{len(follow_selectors)}个选择器）")
            for i, selector in enumerate(follow_selectors, 1):
                by_type = "ID" if selector["by"] == By.ID else "XPATH"
                print(f"  [{i}/{len(follow_selectors)}] 尝试 {by_type}: {selector['value'][:60]}...")
                element = core_utils.find_element_safe(selector["by"], selector["value"], timeout=3)
                if element:
                    # 检查是否已关注
                    try:
                        text = element.text or ""
                        content_desc = element.get_attribute("content-desc") or ""
                        if any(keyword in text or keyword in content_desc for keyword in ["已关注", "相互关注"]):
                            print("👥 已关注作者，跳过")
                            return True
                    except:
                        pass

                    # 点击关注
                    try:
                        element.click()
                        print(f"✅ 关注成功！（选择器 {i}）")
                        core_utils.human_like_delay()
                        return True
                    except:
                        if core_utils.wait_and_click(selector["by"], selector["value"], timeout=2):
                            print(f"✅ 关注成功！（选择器 {i}）")
                            core_utils.human_like_delay()
                            return True

            print("⚠️ 未找到关注按钮")
            return False

        except Exception as e:
            print(f"❌ 关注失败: {e}")
            return False

    def perform_search_and_switch(self, keyword: str) -> bool:
        """
        执行搜索并切换到视频Tab
        """
        try:
            print(f"🔍 开始搜索: {keyword}")

            # 点击搜索框
            search_selectors = [
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/a1o"},  # 搜索框
                {"by": By.XPATH, "value": "//android.widget.ImageView[@content-desc='搜索']"},
                {"by": By.XPATH, "value": "//android.widget.TextView[@text='搜索']"},
            ]

            for selector in search_selectors:
                if core_utils.wait_and_click(selector["by"], selector["value"]):
                    print("✅ 打开搜索页面")
                    core_utils.random_pause(1.0, 2.0)
                    break
            else:
                print("⚠️ 未找到搜索入口")
                return False

            # 输入搜索关键词
            input_selectors = [
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/et_search_kw"},  # 搜索输入框
                {"by": By.XPATH, "value": "//android.widget.EditText"},
                {"by": By.XPATH, "value": "//android.widget.TextView[@text='搜你想看的']"},
            ]

            input_element = None
            for selector in input_selectors:
                input_element = core_utils.find_element_safe(selector["by"], selector["value"])
                if input_element:
                    break

            if not input_element:
                print("⚠️ 未找到搜索输入框")
                return False

            if not core_utils.send_keys_safe(input_element, keyword):
                print("❌ 搜索关键词输入失败")
                return False

            # 点击搜索
            core_utils.random_pause(0.5, 1.0)
            self.driver.press_keycode(66)  # 回车键

            print("✅ 搜索提交成功")
            core_utils.random_pause(2.0, 3.0)

            # 切换到视频Tab
            return self._switch_to_video_tab()

        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return False

    def _switch_to_video_tab(self) -> bool:
        """切换到视频Tab"""
        try:
            # 视频Tab选择器
            video_tab_selectors = [
                {"by": By.XPATH, "value": "//android.widget.TextView[@text='视频']"},
                {"by": By.XPATH, "value": "//android.widget.TextView[contains(@text, '视频')]"},
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/tab_name"},  # Tab名称
            ]

            for selector in video_tab_selectors:
                elements = core_utils.find_elements_safe(selector["by"], selector["value"])
                for element in elements:
                    if "视频" in element.text:
                        if core_utils.wait_and_click(By.XPATH, f".//android.widget.TextView[@text='{element.text}']"):
                            print("📹 切换到视频Tab")
                            core_utils.random_pause(1.0, 2.0)
                            return True

            print("⚠️ 未找到视频Tab，可能已经在视频页面")
            return True  # 假设成功，因为可能已经在视频页面

        except Exception as e:
            print(f"❌ 切换视频Tab失败: {e}")
            return False

    def go_to_home_page(self) -> bool:
        """返回首页"""
        try:
            # 首页按钮选择器
            home_selectors = [
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/a1f"},  # 首页按钮
                {"by": By.XPATH, "value": "//android.widget.ImageView[@content-desc='首页']"},
                {"by": By.XPATH, "value": "//android.widget.TextView[@text='首页']"},
            ]

            for selector in home_selectors:
                if core_utils.wait_and_click(selector["by"], selector["value"]):
                    print("🏠 返回首页")
                    core_utils.random_pause(1.0, 2.0)
                    return True

            print("⚠️ 未找到首页按钮")
            return False

        except Exception as e:
            print(f"❌ 返回首页失败: {e}")
            return False

    def go_to_for_you_page(self) -> bool:
        """切换到推荐页面"""
        try:
            # 推荐页面选择器
            for_you_selectors = [
                {"by": By.XPATH, "value": "//android.widget.TextView[@text='推荐']"},
                {"by": By.XPATH, "value": "//android.widget.TextView[contains(@text, '推荐')]"},
            ]

            for selector in for_you_selectors:
                if core_utils.wait_and_click(selector["by"], selector["value"]):
                    print("🌟 切换到推荐页面")
                    core_utils.random_pause(1.0, 2.0)
                    return True

            # 如果没找到推荐Tab，尝试返回首页（默认就是推荐）
            return self.go_to_home_page()

        except Exception as e:
            print(f"❌ 切换推荐页面失败: {e}")
            return False

    def is_live_stream(self) -> bool:
        """
        检测当前视频是否为直播
        检测方式：查找"点击进入直播间"按钮（最准确的判断方式）
        """
        try:
            # 通过"点击进入直播间"按钮检测（最准确）
            live_indicators = [
                {"by": By.XPATH, "value": "//android.widget.TextView[@text='点击进入直播间']"},
                {"by": By.XPATH, "value": "//android.widget.Button[@text='点击进入直播间']"},
                {"by": By.XPATH, "value": "//android.widget.TextView[contains(@text, '进入直播间')]"},
                {"by": By.XPATH, "value": "//android.widget.Button[contains(@text, '进入直播间')]"},
                {"by": By.XPATH, "value": "//android.widget.TextView[@content-desc='点击进入直播间']"},
            ]

            for indicator in live_indicators:
                element = core_utils.find_element_safe(indicator["by"], indicator["value"], timeout=0.5)
                if element:
                    print("🔴 检测到直播视频（发现'点击进入直播间'按钮）")
                    return True

            return False

        except Exception as e:
            print(f"⚠️ 直播检测异常: {e}")
            return False

    def exit_live_stream(self) -> bool:
        """
        退出直播界面
        尝试点击关闭按钮或执行返回操作
        """
        try:
            print("🚪 尝试退出直播界面...")

            # 尝试点击关闭按钮（右上角的×）
            close_selectors = [
                {"by": By.XPATH, "value": "//android.widget.ImageView[@content-desc='关闭']"},
                {"by": By.XPATH, "value": "//android.widget.ImageView[@content-desc='返回']"},
                {"by": By.XPATH, "value": "//android.widget.TextView[@text='×']"},
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/close"},
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/back"},
            ]

            for selector in close_selectors:
                if core_utils.wait_and_click(selector["by"], selector["value"], timeout=2):
                    print("✅ 已点击关闭按钮退出直播")
                    core_utils.random_pause(0.5, 1.0)
                    return True

            # 如果没找到关闭按钮，尝试按返回键
            self.driver.back()
            print("✅ 已通过返回键退出直播")
            core_utils.random_pause(0.5, 1.0)
            return True

        except Exception as e:
            print(f"❌ 退出直播失败: {e}")
            return False

    def is_advertisement(self) -> bool:
        """
        检测当前视频是否为广告
        检测方式：查找"广告"标识或挂车链接
        """
        try:
            ad_indicators = [
                # 标准广告标识
                {"by": By.XPATH, "value": "//android.widget.TextView[@text='广告']"},
                {"by": By.XPATH, "value": "//android.widget.TextView[contains(@text, '广告')]"},
                {"by": By.XPATH, "value": "//android.widget.TextView[@content-desc='广告']"},
                # 挂车链接标识（购物车内容）
                {"by": By.XPATH, "value": "//android.widget.TextView[contains(@text, '购物车')]"},
                {"by": By.XPATH, "value": "//android.widget.ImageView[@content-desc='购物车']"},
                {"by": By.XPATH, "value": "//android.widget.TextView[contains(@text, '商品')]"},
                {"by": By.XPATH, "value": "//android.widget.TextView[contains(@text, '立即购买')]"},
                {"by": By.XPATH, "value": "//android.widget.TextView[contains(@text, '看相似')]"},
                {"by": By.XPATH, "value": "//android.widget.TextView[contains(@text, '挂车')]"},
            ]

            for indicator in ad_indicators:
                element = core_utils.find_element_safe(indicator["by"], indicator["value"], timeout=0.5)
                if element:
                    print("📺 检测到广告视频（含挂车链接或广告标识）")
                    return True

            return False

        except Exception as e:
            print(f"⚠️ 广告检测异常: {e}")
            return False

    def has_interaction_buttons(self) -> bool:
        """
        检测当前页面是否有交互按钮（点赞/评论/收藏）
        用于判断是否为正常的视频页面
        """
        try:
            # 快速检测点赞按钮（最常见的交互按钮）
            like_selectors = [
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/f_u"},
                {"by": By.XPATH, "value": "//android.widget.LinearLayout[contains(@content-desc, '点赞')]"},
                {"by": By.XPATH, "value": "//android.widget.LinearLayout[contains(@content-desc, '喜欢')]"},
            ]

            for selector in like_selectors:
                element = core_utils.find_element_safe(selector["by"], selector["value"], timeout=1)
                if element:
                    return True

            # 如果点赞按钮找不到，尝试评论按钮
            comment_selectors = [
                {"by": By.ID, "value": "com.ss.android.ugc.aweme:id/eiz"},
                {"by": By.XPATH, "value": "//android.widget.LinearLayout[contains(@content-desc, '评论')]"},
            ]

            for selector in comment_selectors:
                element = core_utils.find_element_safe(selector["by"], selector["value"], timeout=1)
                if element:
                    return True

            return False

        except Exception as e:
            print(f"⚠️ 按钮检测异常: {e}")
            return False

# 全局交互实例
_interactions = None

def init_interactions(driver: webdriver.Remote):
    """初始化交互模块"""
    global _interactions
    _interactions = DouyinInteractions(driver)

def dismiss_popups_if_present() -> bool:
    """处理弹窗"""
    if _interactions is None:
        raise RuntimeError("交互模块未初始化，请先调用 init_interactions()")
    return _interactions.dismiss_popups_if_present()

def like_current_video() -> bool:
    """点赞当前视频"""
    if _interactions is None:
        raise RuntimeError("交互模块未初始化，请先调用 init_interactions()")
    return _interactions.like_current_video()

def comment_on_current_video(comment_text: str) -> bool:
    """评论当前视频"""
    if _interactions is None:
        raise RuntimeError("交互模块未初始化，请先调用 init_interactions()")
    return _interactions.comment_on_current_video(comment_text)

def favorite_current_video() -> bool:
    """收藏当前视频"""
    if _interactions is None:
        raise RuntimeError("交互模块未初始化，请先调用 init_interactions()")
    return _interactions.favorite_current_video()

def follow_current_author() -> bool:
    """关注当前作者"""
    if _interactions is None:
        raise RuntimeError("交互模块未初始化，请先调用 init_interactions()")
    return _interactions.follow_current_author()

def perform_search_and_switch(keyword: str) -> bool:
    """执行搜索并切换到视频Tab"""
    if _interactions is None:
        raise RuntimeError("交互模块未初始化，请先调用 init_interactions()")
    return _interactions.perform_search_and_switch(keyword)

def go_to_for_you_page() -> bool:
    """切换到推荐页面"""
    if _interactions is None:
        raise RuntimeError("交互模块未初始化，请先调用 init_interactions()")
    return _interactions.go_to_for_you_page()

def is_live_stream() -> bool:
    """检测是否为直播视频"""
    if _interactions is None:
        raise RuntimeError("交互模块未初始化，请先调用 init_interactions()")
    return _interactions.is_live_stream()

def exit_live_stream() -> bool:
    """退出直播界面"""
    if _interactions is None:
        raise RuntimeError("交互模块未初始化，请先调用 init_interactions()")
    return _interactions.exit_live_stream()

def is_advertisement() -> bool:
    """检测是否为广告"""
    if _interactions is None:
        raise RuntimeError("交互模块未初始化，请先调用 init_interactions()")
    return _interactions.is_advertisement()

def has_interaction_buttons() -> bool:
    """检测是否有交互按钮（点赞/评论/收藏）"""
    if _interactions is None:
        raise RuntimeError("交互模块未初始化，请先调用 init_interactions()")
    return _interactions.has_interaction_buttons()