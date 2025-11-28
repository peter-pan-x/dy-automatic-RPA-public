"""测试：完整的评论区扫描逻辑 + LLM智能回复"""
import sys
import os
import time
import random
import hashlib
import logging
import atexit
import yaml

# 加载统一配置
BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.yaml')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'test_comment.log')

# 初始化日志（覆盖模式）
logger = logging.getLogger("comment_scanner")
logger.setLevel(logging.INFO)
logger.handlers.clear()

file_handler = logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')
stream_handler = logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

atexit.register(logging.shutdown)
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        _config = yaml.safe_load(f)
except:
    _config = {}

try:
    from src import app_driver
    from src.llm_reply import generate_reply
    from appium.webdriver.common.appiumby import AppiumBy as By
except Exception as e:
    logger.exception(f"导入失败: {e}")
    input("按回车退出...")
    sys.exit(1)

# 从配置读取拦截关键词
INTERCEPT_KEYWORDS = _config.get('intercept', {}).get('keywords', [
    "有没有", "求推荐", "哪里", "怎么买", "多少钱"
])

# 已回复评论的去重集合（用评论指纹）
REPLIED_COMMENTS = set()

def get_comment_fingerprint(user: str, content: str) -> str:
    """生成评论唯一指纹，用于去重"""
    raw = f"{user}:{content}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()[:16]


def scan_comments_loop(driver):
    """完整的评论扫描+自动回复流程"""
    logger.info("\n" + "="*50)
    logger.info("🚀 开始评论区扫描 + 自动回复")
    logger.info("="*50)
    
    max_scrolls = 50
    last_page_content = ""
    comments_read = 0
    replies_sent = 0
    
    try:
        for scroll_idx in range(max_scrolls):
            logger.info(f"\n📄 第 {scroll_idx + 1} 屏...")
            
            # 1. 获取当前页面特征（用于到底判断）
            current_content = get_page_content_hash(driver)
            
            # 到底检测：如果内容完全一样，说明滑不动了
            if current_content == last_page_content and scroll_idx > 0:
                logger.info("✅ 评论区已刷完（内容无变化）")
                break
            
            last_page_content = current_content
            
            # 2. 扫描并处理评论（含自动回复）
            found_count, reply_count = process_current_screen_comments(driver)
            comments_read += found_count
            replies_sent += reply_count
            
            # 3. 模拟滑动
            start_y = random.randint(1400, 1600)
            end_y = random.randint(800, 1000)
            driver.swipe(500, start_y, 500, end_y, 600)
            
            # 4. 等待加载
            time.sleep(1.5)
            
    except KeyboardInterrupt:
        logger.warning("\n⚠️ 用户中断")
    except Exception as e:
        logger.exception(f"\n❌ 扫描异常: {e}")
        
    logger.info("\n" + "="*50)
    logger.info("📊 扫描结束统计:")
    logger.info(f"   📖 读取评论: {comments_read} 条")
    logger.info(f"   💬 发送回复: {replies_sent} 条")
    logger.info(f"   🔒 去重记录: {len(REPLIED_COMMENTS)} 条")
    logger.info("="*50)

def get_page_content_hash(driver) -> str:
    """获取当前屏幕所有评论的指纹，用于判断是否翻页成功"""
    try:
        elements = driver.find_elements(By.XPATH, "//android.widget.FrameLayout")
        texts = []
        for elem in elements:
            try:
                desc = elem.get_attribute("content-desc") or ""
                if desc and "回复 按钮" in desc:
                    texts.append(desc[:30]) # 取前30个字符作为特征
            except:
                pass
        return "||".join(texts)
    except:
        return ""

def process_current_screen_comments(driver) -> tuple:
    """
    处理当前屏幕的评论，命中关键词则自动回复
    
    Returns:
        tuple: (读取评论数, 回复数)
    """
    count = 0
    reply_count = 0
    
    try:
        elements = driver.find_elements(By.XPATH, "//android.widget.FrameLayout")
        
        for elem in elements:
            try:
                desc = elem.get_attribute("content-desc") or ""
                
                # 过滤：必须是评论元素
                if "回复 按钮" not in desc:
                    continue
                
                # 提取评论内容
                # 格式: "用户名,评论内容,时间, · 地区,回复 按钮,"
                parts = desc.split(",")
                if len(parts) > 1:
                    user = parts[0]
                    content = parts[1]
                    
                    logger.info(f"   💬 [{user}]: {content}")
                    count += 1
                    
                    # 生成评论指纹，检查是否已回复
                    fingerprint = get_comment_fingerprint(user, content)
                    if fingerprint in REPLIED_COMMENTS:
                        logger.info(f"      ⏭️ 已回复过，跳过")
                        continue
                    
                    # 检查关键词
                    for keyword in INTERCEPT_KEYWORDS:
                        if keyword in content:
                            logger.info(f"      🎯 命中关键词 [{keyword}]")
                            
                            # 执行回复（传入评论内容给LLM）
                            success = do_reply(driver, elem, user, content)
                            if success:
                                REPLIED_COMMENTS.add(fingerprint)
                                reply_count += 1
                                # 回复后页面可能变化，跳出当前屏处理，下次滑动后继续
                                return count, reply_count
                            break
                            
            except Exception as e:
                continue
                
    except Exception as e:
        logger.exception(f"   处理异常: {e}")
        
    return count, reply_count


def do_reply(driver, comment_elem, target_user: str, comment_content: str) -> bool:
    """
    对评论执行回复操作
    
    Args:
        driver: Appium driver
        comment_elem: 评论元素
        target_user: 目标用户名
        comment_content: 评论内容（用于LLM生成回复）
    
    Returns:
        bool: 是否成功
    """
    try:
        # 1. 点击评论元素，触发回复
        logger.info(f"      📝 点击回复 @{target_user}...")
        comment_elem.click()
        time.sleep(1.0)
        
        # 2. 查找输入框
        input_box = None
        input_selectors = [
            (By.XPATH, "//android.widget.EditText"),
            (By.ID, "com.ss.android.ugc.aweme:id/commentEditText"),
            (By.CLASS_NAME, "android.widget.EditText"),
        ]
        
        for by, val in input_selectors:
            try:
                elems = driver.find_elements(by, val)
                if elems:
                    input_box = elems[0]
                    break
            except:
                pass
        
        if not input_box:
            logger.error(f"      ❌ 未找到输入框")
            # 点击空白处关闭
            driver.tap([(540, 800)])
            time.sleep(0.5)
            return False
        
        # 3. 调用LLM生成回复内容
        reply_text = generate_reply(comment_content)
        logger.info(f"      ✏️ 输入: {reply_text}")
        input_box.click()
        time.sleep(0.5)
        input_box.send_keys(reply_text)
        time.sleep(0.5)
        
        # 4. 点击发送按钮
        send_btn = None
        send_selectors = [
            (By.XPATH, "//android.widget.TextView[@text='发送']"),
            (By.XPATH, "//android.widget.Button[@text='发送']"),
            (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("发送")'),
        ]
        
        for by, val in send_selectors:
            try:
                elems = driver.find_elements(by, val)
                if elems:
                    send_btn = elems[0]
                    break
            except:
                pass
        
        if send_btn:
            send_btn.click()
            logger.info(f"      ✅ 回复成功!")
            time.sleep(1.0)
            return True
        else:
            logger.warning(f"      ❌ 未找到发送按钮")
            # 尝试按回车发送
            driver.press_keycode(66)  # KEYCODE_ENTER
            time.sleep(0.5)
            return True
            
    except Exception as e:
        logger.exception(f"      ❌ 回复失败: {e}")
        return False

def main():
    driver = None
    try:
        logger.info("正在连接 Appium...")
        driver = app_driver.connect()
        logger.info("✅ 连接成功")
        
        # 自动寻找并点击评论按钮
        logger.info("\n🔍 正在寻找评论按钮...")
        try:
            comment_btn = None
            selectors = [
                (By.ID, "com.ss.android.ugc.aweme:id/eiz"),  # 常见ID
                (By.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("评论")'),
                (By.XPATH, "//android.widget.LinearLayout[contains(@content-desc, '评论')]")
            ]
            
            for by, val in selectors:
                try:
                    elems = driver.find_elements(by, val)
                    if elems:
                        comment_btn = elems[0]
                        break
                except Exception as e:
                    logger.debug(f"定位评论按钮异常: {e}")
            
            if comment_btn:
                comment_btn.click()
                logger.info("📝 已自动进入评论区")
            else:
                raise RuntimeError("未找到评论按钮")
        except Exception as e:
            logger.warning(f"⚠️ 未自动定位评论按钮: {e}，请手动进入评论区")
            input("手动进入评论区后按回车继续...")
        
        scan_comments_loop(driver)
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ 用户中断程序")
    except Exception as e:
        logger.exception(f"\n❌ 主流程异常: {e}")
    finally:
        if driver:
            driver.quit()
        logger.info("程序结束")

if __name__ == "__main__":
    main()
