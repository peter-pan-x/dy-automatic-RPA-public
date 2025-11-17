"""
Appium驱动器 - 负责初始化和管理WebDriver连接
包含异常处理、重连机制和设备状态检测
"""

import time
import subprocess
import platform
from typing import Optional
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.common.exceptions import WebDriverException, SessionNotCreatedException
import config.settings as settings

class AppiumDriver:
    """Appium驱动器管理类"""

    def __init__(self):
        self.driver = None
        self.device_connected = False
        self.appium_server_running = False
        self.retry_count = 0

    def check_device_connection(self) -> bool:
        """检查设备连接状态"""
        try:
            # 使用shell=True以便能找到PATH中的adb
            result = subprocess.run('adb devices',
                                  shell=True,
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)

            if result.returncode == 0:
                devices = result.stdout.strip().split('\n')[1:]
                return len(devices) > 0 and any('device' in line for line in devices)
            return False
        except Exception as e:
            print(f"设备连接检查失败: {e}")
            return False

    def check_appium_server(self) -> bool:
        """检查Appium Server状态"""
        try:
            import requests
            response = requests.get(f"{settings.APPIUM_SERVER_URL}/status", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def start_appium_server(self) -> bool:
        """启动Appium Server"""
        try:
            print("正在启动Appium Server...")
            if platform.system() == "Windows":
                subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/k', 'appium'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                subprocess.Popen(['appium'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 等待Appium Server启动
            for i in range(30):  # 最多等待30秒
                time.sleep(1)
                if self.check_appium_server():
                    print("Appium Server启动成功")
                    return True
                print(f"等待Appium Server启动... ({i+1}/30)")

            print("Appium Server启动超时")
            return False
        except Exception as e:
            print(f"启动Appium Server失败: {e}")
            return False

    def connect(self, max_retries: int = 3) -> Optional[webdriver.Remote]:
        """
        连接到Appium Server并初始化WebDriver
        包含完整的异常处理和恢复机制
        """
        self.retry_count = 0

        while self.retry_count < max_retries:
            try:
                print(f"尝试连接Appium (第{self.retry_count + 1}次)...")

                # 检查前置条件
                if not self.check_device_connection():
                    print("❌ 设备未连接，请检查USB连接和调试模式")
                    if self.retry_count < max_retries - 1:
                        print("等待5秒后重试...")
                        time.sleep(5)
                        self.retry_count += 1
                        continue
                    return None

                if not self.check_appium_server():
                    print("⚠️ Appium Server未运行，尝试启动...")
                    if not self.start_appium_server():
                        if self.retry_count < max_retries - 1:
                            print("等待10秒后重试...")
                            time.sleep(10)
                            self.retry_count += 1
                            continue
                        return None

                # 尝试创建WebDriver会话
                print("正在创建WebDriver会话...")
                
                # Appium 5.x使用options对象代替desired_capabilities
                options = UiAutomator2Options()
                caps = settings.DOUYIN_CAPS
                
                # 设置基本能力
                if 'platformName' in caps:
                    options.platform_name = caps['platformName']
                if 'deviceName' in caps:
                    options.device_name = caps['deviceName']
                if 'appPackage' in caps:
                    options.app_package = caps['appPackage']
                if 'appActivity' in caps:
                    options.app_activity = caps['appActivity']
                if 'automationName' in caps:
                    options.automation_name = caps['automationName']
                if 'noReset' in caps:
                    options.no_reset = caps['noReset']
                if 'fullReset' in caps:
                    options.full_reset = caps['fullReset']
                if 'unicodeKeyboard' in caps:
                    options.unicode_keyboard = caps['unicodeKeyboard']
                if 'resetKeyboard' in caps:
                    options.reset_keyboard = caps['resetKeyboard']
                if 'newCommandTimeout' in caps:
                    options.new_command_timeout = caps['newCommandTimeout']
                
                # 添加防止重复安装的关键配置
                if 'skipServerInstallation' in caps:
                    options.skip_server_installation = caps['skipServerInstallation']
                if 'skipDeviceInitialization' in caps:
                    options.skip_device_initialization = caps['skipDeviceInitialization']
                if 'autoGrantPermissions' in caps:
                    options.auto_grant_permissions = caps['autoGrantPermissions']
                if 'dontStopAppOnReset' in caps:
                    options.dont_stop_app_on_reset = caps['dontStopAppOnReset']
                if 'skipUnlock' in caps:
                    options.skip_unlock = caps['skipUnlock']
                
                # 创建WebDriver会话
                self.driver = webdriver.Remote(
                    settings.APPIUM_SERVER_URL,
                    options=options
                )

                # 验证连接
                if self._validate_connection():
                    print("✅ Appium连接成功")
                    self.device_connected = True
                    self.appium_server_running = True
                    self.retry_count = 0
                    return self.driver
                else:
                    print("❌ 连接验证失败")
                    self.quit()

            except SessionNotCreatedException as e:
                print(f"❌ 会话创建失败: {e}")
                print("可能原因：")
                print("1. 抖音应用未安装")
                print("2. 应用包名或Activity名错误")
                print("3. 设备权限问题")

            except WebDriverException as e:
                print(f"❌ WebDriver异常: {e}")
                if "connection refused" in str(e).lower():
                    print("Appium Server连接被拒绝，尝试重启...")
                    self.appium_server_running = False

            except Exception as e:
                print(f"❌ 连接异常: {e}")

            # 清理和重试
            self.quit()
            self.retry_count += 1

            if self.retry_count < max_retries:
                wait_time = min(30, 10 * self.retry_count)  # 递增等待时间
                print(f"等待{wait_time}秒后重试...")
                time.sleep(wait_time)

        print(f"❌ 连接失败，已达到最大重试次数({max_retries})")
        return None

    def _validate_connection(self) -> bool:
        """验证WebDriver连接是否有效"""
        try:
            if not self.driver:
                return False

            # 获取当前Activity
            current_activity = self.driver.current_activity
            print(f"当前Activity: {current_activity}")

            # 获取设备信息
            device_size = self.driver.get_window_size()
            print(f"设备分辨率: {device_size}")

            return True
        except Exception as e:
            print(f"连接验证失败: {e}")
            return False

    def is_connected(self) -> bool:
        """检查连接状态"""
        if not self.driver:
            return False

        try:
            # 尝试获取设备状态
            self.driver.current_activity
            return True
        except:
            return False

    def reconnect(self) -> bool:
        """重新连接"""
        print("尝试重新连接...")
        self.quit()
        return self.connect() is not None

    def restart_app(self) -> bool:
        """重启应用"""
        try:
            if not self.driver:
                return False

            print("正在重启抖音应用...")
            self.driver.terminate_app(settings.DOUYIN_CAPS['appPackage'])
            time.sleep(3)
            self.driver.activate_app(settings.DOUYIN_CAPS['appPackage'])
            time.sleep(5)

            return self._validate_connection()
        except Exception as e:
            print(f"重启应用失败: {e}")
            return False

    def quit(self):
        """安全关闭WebDriver"""
        if self.driver:
            try:
                print("正在关闭WebDriver...")
                self.driver.quit()
            except Exception as e:
                print(f"关闭WebDriver时出错: {e}")
            finally:
                self.driver = None

        self.device_connected = False
        print("WebDriver已关闭")

    def get_device_info(self) -> dict:
        """获取设备信息"""
        if not self.is_connected():
            return {}

        try:
            info = {
                'platform_version': self.driver.capabilities.get('platformVersion'),
                'device_name': self.driver.capabilities.get('deviceName'),
                'screen_size': self.driver.get_window_size(),
                'current_package': self.driver.current_package,
                'current_activity': self.driver.current_activity
            }
            return info
        except Exception as e:
            print(f"获取设备信息失败: {e}")
            return {}

# 全局驱动器实例
_driver_manager = None

def get_driver_manager() -> AppiumDriver:
    """获取驱动器管理器实例"""
    global _driver_manager
    if _driver_manager is None:
        _driver_manager = AppiumDriver()
    return _driver_manager

def connect(max_retries: int = 3) -> Optional[webdriver.Remote]:
    """连接到Appium并返回WebDriver实例"""
    manager = get_driver_manager()
    return manager.connect(max_retries)

def quit(driver=None):
    """关闭WebDriver连接"""
    global _driver_manager
    if _driver_manager:
        _driver_manager.quit()
    elif driver:
        try:
            driver.quit()
        except:
            pass

def is_healthy() -> bool:
    """检查系统健康状态"""
    manager = get_driver_manager()
    return manager.is_connected()

def health_check() -> dict:
    """执行健康检查并返回状态"""
    manager = get_driver_manager()

    status = {
        'device_connected': manager.check_device_connection(),
        'appium_server_running': manager.check_appium_server(),
        'driver_connected': manager.is_connected(),
        'device_info': manager.get_device_info() if manager.is_connected() else {}
    }

    return status