"""
抖音RPA项目启动器（增强版 - 完整日志支持）
唯一的启动入口，包含合规性检查、环境验证和优雅启动流程
"""

import sys
import os

# 设置Windows控制台编码为UTF-8（必须在最开始）
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

import time
import signal
import argparse
import traceback
from typing import Optional
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 确保logs目录存在
os.makedirs("logs", exist_ok=True)

# 初始化日志系统（程序一启动就创建）
from src.logger import setup_logger, get_logger
logger = setup_logger("douyin_rpa", log_dir="logs")

from src import app_driver, tracker, task_manager
import config.settings as settings

class DouyinRPA:
    """抖音RPA主应用类"""

    def __init__(self):
        self.driver = None
        self.task_manager = None
        self.running = False
        self.args = None
        logger.info("="*80)
        logger.info(f"DouyinRPA实例初始化 - 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*80)

    def display_startup_banner(self):
        """显示启动横幅"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                         抖音高仿真引流RPA项目 (V4)                           ║
║                          混合动力·最终版·测试版                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ ⚠️  重要声明：                                                                  ║
║ • 本项目仅用于学习、测试和研究目的                                               ║
║ • 请遵守抖音平台的服务条款和社区准则                                             ║
║ • 自动化操作可能导致账号受到限制或封禁                                           ║
║ • 使用者需自行承担所有风险和责任                                                 ║
║ • 开发者不承担任何法律责任                                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        logger.info("显示启动横幅")

    def check_compliance_agreement(self) -> bool:
        """检查合规协议"""
        logger.info("开始合规性检查")
        print("\n📋 合规性确认")
        print("=" * 60)
        print("请仔细阅读以下声明：")
        print("1. 我理解此项目仅用于学习测试目的")
        print("2. 我将遵守抖音平台的服务条款")
        print("3. 我了解自动化操作可能带来的风险")
        print("4. 我将自行承担使用风险")
        print("5. 我不会将此项目用于商业或恶意用途")
        print("=" * 60)

        if self.args and self.args.auto_accept:
            print("✅ 自动接受协议（通过 --auto-accept 参数）")
            logger.info("用户通过--auto-accept参数自动接受协议")
            return True

        while True:
            agreement = input("\n您是否同意以上声明？(yes/no): ").strip().lower()
            if agreement in ['yes', 'y', '是', '同意']:
                print("✅ 感谢您的确认，程序继续...")
                logger.info("用户同意合规协议")
                return True
            elif agreement in ['no', 'n', '否', '不同意']:
                print("❌ 不同意协议，程序退出")
                logger.warning("用户不同意合规协议，程序退出")
                return False
            else:
                print("⚠️  请输入 yes 或 no")
                logger.debug(f"用户输入无效: {agreement}")

    def check_environment(self) -> bool:
        """检查运行环境"""
        print("\n🔍 环境检查")
        print("=" * 60)
        logger.info("="*60)
        logger.info("开始环境检查")
        logger.info("="*60)

        try:
            # 检查Python版本
            python_version = sys.version_info
            version_str = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
            logger.info(f"检查Python版本: {version_str}")
            
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
                error_msg = f"Python版本过低: {version_str}，需要Python 3.7或更高版本"
                print(f"❌ {error_msg}")
                logger.error(error_msg)
                return False
                
            print(f"✅ Python版本: {version_str}")
            logger.info(f"✅ Python版本检查通过: {version_str}")

            # 检查必要的文件
            required_files = [
                "config/settings.py",
                "config/comments.txt",
                "config/keywords.txt"
            ]
            
            logger.info("检查必要文件...")
            for file_path in required_files:
                logger.debug(f"检查文件: {file_path}")
                if not os.path.exists(file_path):
                    error_msg = f"缺少必要文件: {file_path}"
                    print(f"❌ {error_msg}")
                    logger.error(error_msg)
                    return False
                print(f"✅ 找到文件: {file_path}")
                logger.debug(f"✅ 文件存在: {file_path}")
            logger.info("✅ 必要文件检查通过")

            # 检查ADB连接
            print("📱 检查设备连接...")
            logger.info("检查ADB设备连接...")
            
            try:
                health_status = app_driver.health_check()
                logger.debug(f"设备健康检查结果: {health_status}")
            except Exception as e:
                error_msg = f"设备健康检查失败: {str(e)}"
                print(f"❌ {error_msg}")
                logger.exception(error_msg)
                return False
            
            if not health_status.get('device_connected', False):
                error_msg = "未检测到Android设备"
                print(f"❌ {error_msg}")
                print("   请确保：")
                print("   1. 设备已通过USB连接到电脑")
                print("   2. 设备已开启USB调试模式")
                print("   3. 已安装ADB驱动")
                logger.error(error_msg)
                logger.error("设备连接检查失败 - 请确保: 1.USB连接 2.USB调试已开启 3.ADB驱动已安装")
                return False
                
            print("✅ 设备连接正常")
            logger.info("✅ Android设备连接正常")

            # 检查Appium Server
            print("🔌 检查Appium Server...")
            logger.info("检查Appium Server状态...")
            
            if not health_status.get('appium_server_running', False):
                warning_msg = "Appium Server未运行"
                print(f"⚠️ {warning_msg}")
                logger.warning(warning_msg)
                print("   请手动启动Appium Server或使用命令: appium")
                logger.warning("Appium Server未运行，请执行: appium")
                
                if not self.args or not self.args.auto_start:
                    logger.error("Appium Server未运行且未设置auto_start参数，环境检查失败")
                    return False
            else:
                print("✅ Appium Server运行正常")
                logger.info("✅ Appium Server运行正常")

            # 创建必要的目录
            directories = ["logs", "data", "screenshots"]
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                logger.debug(f"创建/确认目录: {directory}")
                
            print("✅ 必要目录已创建")
            logger.info("✅ 必要目录已创建")

            print("=" * 60)
            print("✅ 环境检查通过")
            logger.info("="*60)
            logger.info("✅ 环境检查全部通过")
            logger.info("="*60)
            return True
            
        except Exception as e:
            error_msg = f"环境检查过程中发生未预期的异常"
            print(f"❌ {error_msg}: {str(e)}")
            logger.exception(f"{error_msg}: {str(e)}")
            logger.error(f"异常类型: {type(e).__name__}")
            logger.error(f"异常详情: {traceback.format_exc()}")
            return False

    def initialize_components(self) -> bool:
        """初始化组件"""
        print("\n🚀 初始化组件")
        print("=" * 60)
        logger.info("="*60)
        logger.info("开始初始化组件")
        logger.info("="*60)

        try:
            # 连接Appium
            print("🔌 连接Appium...")
            logger.info("开始连接Appium...")
            logger.debug(f"Appium配置 - Server: {getattr(settings, 'APPIUM_SERVER', 'http://127.0.0.1:4723')}")
            
            try:
                self.driver = app_driver.connect(max_retries=3)
            except Exception as e:
                logger.exception(f"Appium连接异常: {str(e)}")
                raise
                
            if not self.driver:
                error_msg = "Appium连接失败 - driver为None"
                print(f"❌ {error_msg}")
                logger.error(error_msg)
                return False
                
            print("✅ Appium连接成功")
            logger.info("✅ Appium连接成功")
            logger.debug(f"Driver信息: {type(self.driver)}")

            # 初始化统计器
            print("📊 初始化统计器...")
            logger.info("初始化统计器...")
            
            try:
                tracker.init_tracker()
            except Exception as e:
                logger.exception(f"统计器初始化异常: {str(e)}")
                raise
                
            print("✅ 统计器初始化完成")
            logger.info("✅ 统计器初始化完成")

            # 初始化任务管理器
            print("🎯 初始化任务管理器...")
            logger.info("初始化任务管理器...")
            
            try:
                self.task_manager = task_manager.TaskManager(self.driver)
            except Exception as e:
                logger.exception(f"任务管理器初始化异常: {str(e)}")
                raise
                
            print("✅ 任务管理器初始化完成")
            logger.info("✅ 任务管理器初始化完成")

            print("=" * 60)
            print("✅ 所有组件初始化完成")
            logger.info("="*60)
            logger.info("✅ 所有组件初始化完成")
            logger.info("="*60)
            return True

        except Exception as e:
            error_msg = f"组件初始化失败"
            print(f"❌ {error_msg}: {str(e)}")
            logger.exception(f"{error_msg}: {str(e)}")
            logger.error(f"异常类型: {type(e).__name__}")
            logger.error("详细堆栈跟踪:")
            logger.error(traceback.format_exc())
            return False

    def setup_signal_handlers(self):
        """设置信号处理器"""
        logger.info("设置信号处理器...")
        
        def signal_handler(signum, frame):
            logger.warning(f"收到信号 {signum}，准备优雅退出...")
            print(f"\n⚠️ 收到信号 {signum}，准备优雅退出...")
            self.shutdown()

        signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)  # 终止信号
        logger.info("✅ 信号处理器设置完成")

    def run(self):
        """运行主程序"""
        logger.info("="*80)
        logger.info("开始运行RPA主任务")
        logger.info("="*80)
        
        try:
            print("\n🎬 开始运行RPA任务...")
            print("=" * 60)
            print("💡 提示：")
            print("• 按 Ctrl+C 可以随时停止程序")
            print("• 程序会自动处理各种异常情况")
            print("• 所有数据都会保存在 logs/ 目录中")
            print("• 可以通过修改 config/runtime_config.json 实时调整参数")
            print("=" * 60)
            
            logger.info("RPA任务提示信息已显示")

            self.running = True
            logger.info("开始执行任务管理器主循环...")
            
            try:
                self.task_manager.run_main_loop()
            except Exception as e:
                logger.exception(f"任务管理器主循环异常: {str(e)}")
                raise

        except KeyboardInterrupt:
            print("\n⚠️ 用户中断程序（Ctrl+C）")
            logger.warning("用户通过Ctrl+C中断程序")
        except Exception as e:
            error_msg = f"运行过程中发生异常"
            print(f"\n❌ {error_msg}: {str(e)}")
            logger.exception(f"{error_msg}: {str(e)}")
            logger.error(f"异常类型: {type(e).__name__}")
            logger.error("详细堆栈跟踪:")
            logger.error(traceback.format_exc())
        finally:
            logger.info("进入finally块，准备关闭...")
            self.shutdown()

    def shutdown(self):
        """优雅关闭"""
        if not self.running:
            logger.debug("shutdown()被调用但running=False，跳过")
            return

        logger.info("="*80)
        logger.info("开始优雅关闭程序")
        logger.info("="*80)
        
        print("\n🛑 正在关闭程序...")
        self.running = False

        try:
            # 关闭任务管理器
            if self.task_manager:
                print("📋 保存统计数据...")
                logger.info("保存任务管理器统计数据...")
                try:
                    self.task_manager.shutdown()
                    logger.info("✅ 任务管理器已关闭")
                except Exception as e:
                    logger.exception(f"关闭任务管理器时出错: {str(e)}")

            # 关闭Appium连接
            if self.driver:
                print("🔌 断开Appium连接...")
                logger.info("断开Appium连接...")
                try:
                    app_driver.quit(self.driver)
                    logger.info("✅ Appium连接已断开")
                except Exception as e:
                    logger.exception(f"断开Appium连接时出错: {str(e)}")

            # 显示最终统计
            if self.task_manager:
                print("\n" + "="*60)
                print("📊 运行完成统计摘要")
                print("="*60)
                logger.info("生成运行统计摘要...")
                
                try:
                    status = self.task_manager.get_status()
                    runtime_info = status['runtime_info']
                    print(f"📅 运行时间: {runtime_info['total_runtime']}")
                    print(f"🔄 完成会话: {runtime_info['sessions_completed']} 个")
                    logger.info(f"运行时间: {runtime_info['total_runtime']}")
                    logger.info(f"完成会话: {runtime_info['sessions_completed']} 个")
                except Exception as e:
                    logger.warning(f"获取统计信息时出错: {str(e)}")
                
                print("✅ 程序已安全关闭")
                print("="*60)
                logger.info("✅ 程序已安全关闭")

        except Exception as e:
            error_msg = f"关闭过程中出现异常"
            print(f"⚠️ {error_msg}: {str(e)}")
            logger.exception(f"{error_msg}: {str(e)}")
        finally:
            logger.info("="*80)
            logger.info(f"程序完全退出 - 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*80)

    def parse_arguments(self):
        """解析命令行参数"""
        logger.info("解析命令行参数...")
        
        parser = argparse.ArgumentParser(
            description="抖音高仿真引流RPA项目 (V4 测试版)",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例用法:
  python src/main.py                    # 交互模式运行
  python src/main.py --auto-accept      # 自动接受协议
  python src/main.py --auto-start       # 自动启动组件
  python src/main.py --check-only       # 仅检查环境，不运行
            """
        )

        parser.add_argument(
            '--auto-accept',
            action='store_true',
            help='自动接受合规协议（无需手动确认）'
        )

        parser.add_argument(
            '--auto-start',
            action='store_true',
            help='自动启动Appium Server等组件'
        )

        parser.add_argument(
            '--check-only',
            action='store_true',
            help='仅检查环境，不运行RPA'
        )

        parser.add_argument(
            '--config',
            type=str,
            help='指定配置文件路径'
        )

        parser.add_argument(
            '--export-data',
            action='store_true',
            help='程序结束时导出统计数据'
        )

        parser.add_argument(
            '--version',
            action='version',
            version='抖音RPA V4.0 测试版'
        )

        self.args = parser.parse_args()
        logger.info(f"命令行参数: {vars(self.args)}")

def main():
    """主函数 - 程序入口点"""
    start_time = datetime.now()
    logger.info("╔"+"="*78+"╗")
    logger.info("║" + " "*25 + "程序启动" + " "*25 + "║")
    logger.info("╚"+"="*78+"╝")
    logger.info(f"启动时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"工作目录: {os.getcwd()}")
    logger.info(f"脚本路径: {os.path.abspath(__file__)}")
    
    # 创建应用实例
    app = DouyinRPA()

    try:
        # 解析命令行参数
        app.parse_arguments()

        # 显示启动横幅
        app.display_startup_banner()

        # 合规性检查
        if not app.check_compliance_agreement():
            logger.warning("用户未同意合规协议，程序退出")
            sys.exit(1)

        # 环境检查
        if not app.check_environment():
            print("\n❌ 环境检查失败，程序退出")
            print("💡 解决建议：")
            print("1. 确保Python版本 >= 3.7")
            print("2. 安装必要依赖：pip install -r requirements.txt")
            print("3. 确保Android设备已连接并开启USB调试")
            print("4. 启动Appium Server：appium")
            logger.error("环境检查失败，程序退出")
            logger.error("建议: 1.检查Python版本 2.安装依赖 3.连接设备 4.启动Appium")
            sys.exit(1)

        # 如果只是检查环境，到此结束
        if app.args and app.args.check_only:
            print("\n✅ 环境检查完成，程序退出")
            logger.info("--check-only模式，环境检查完成，程序退出")
            sys.exit(0)

        # 初始化组件
        if not app.initialize_components():
            print("\n❌ 组件初始化失败，程序退出")
            logger.error("组件初始化失败，程序退出")
            sys.exit(1)

        # 设置信号处理器
        app.setup_signal_handlers()

        # 运行主程序
        app.run()
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"程序正常结束 - 总运行时间: {duration}")

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断程序")
        logger.warning("用户通过KeyboardInterrupt中断程序")
    except Exception as e:
        error_msg = f"程序发生未捕获的异常"
        print(f"\n❌ {error_msg}: {str(e)}")
        logger.exception(f"{error_msg}: {str(e)}")
        logger.error(f"异常类型: {type(e).__name__}")
        logger.error("="*80)
        logger.error("完整堆栈跟踪:")
        logger.error("="*80)
        logger.error(traceback.format_exc())
        logger.error("="*80)
    finally:
        try:
            app.shutdown()
        except Exception as e:
            logger.exception(f"最终清理时出错: {str(e)}")
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info("="*80)
        logger.info(f"程序最终退出 - 总运行时间: {duration}")
        logger.info("="*80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # 最后的安全网
        print(f"\n!!! 致命错误 !!!")
        print(f"异常: {str(e)}")
        print(f"类型: {type(e).__name__}")
        print("\n完整堆栈跟踪:")
        print(traceback.format_exc())
        print("\n请查看 logs/error.log 获取详细错误信息")
        
        try:
            logger.critical("="*80)
            logger.critical("!!! 程序遇到致命错误 !!!")
            logger.critical("="*80)
            logger.exception(f"致命错误: {str(e)}")
            logger.critical(traceback.format_exc())
            logger.critical("="*80)
        except:
            pass  # 如果连日志都写不了，就放弃了
        
        sys.exit(1)

