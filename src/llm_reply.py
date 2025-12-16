"""
大模型回复模块 - 简化版（纯预设回复模式）
从统一配置 config/config.yaml 读取预设回复列表
"""
import sys
import os
import random
import yaml

# 添加项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 加载YAML配置
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config', 'config.yaml')

def load_config():
    """加载配置文件"""
    try:
        if not os.path.exists(CONFIG_PATH):
            print(f"⚠️ 配置文件不存在: {CONFIG_PATH}")
            return {}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
            return cfg if cfg else {}
    except Exception as e:
        print(f"⚠️ 配置加载失败: {e}")
        return {}

_config = load_config()
_llm_config = _config.get('llm', {})
_promo_config = _config.get('promotion', {})

# 调试：打印配置状态
if __name__ != "__main__":
    pass  # 作为模块导入时不打印
else:
    print(f"配置路径: {CONFIG_PATH}")
    print(f"当前模式: 纯预设回复（LLM已禁用）")
    print(f"预设回复数量: {len(_llm_config.get('preset_replies', []))} 条")


def get_product_info_str():
    """格式化产品信息字符串"""
    products = _promo_config.get('products', [])
    if not products:
        return "暂无具体产品信息"
    
    info_lines = []
    for p in products:
        name = p.get('name', '未知产品')
        effect = p.get('effect', '')
        sales_point = p.get('sales_point') or p.get('sales pooint') or ''
        detail = effect
        if sales_point:
            detail = f"{effect}；卖点：{sales_point}" if effect else f"卖点：{sales_point}"
        info_lines.append(f"- {name}: {detail}")
    return "\n".join(info_lines)


def generate_reply(comment: str) -> str:
    """
    生成回复 - 纯预设模式
    直接从预设回复列表中随机选择，无需LLM调用
    """
    # 优先使用预设回复列表
    preset_list = _llm_config.get('preset_replies', [])
    if preset_list:
        return random.choice(preset_list)

    # 如果没有配置预设回复，使用基础回复
    fallback_replies = _llm_config.get('fallback_replies', ['茶研官这个牌子很不错！'])
    return random.choice(fallback_replies)


# LLM API调用函数已移除 - 改为纯预设回复模式
# 如需恢复LLM功能，请从版本历史中恢复相关代码


# 测试函数
if __name__ == "__main__":
    test_comments = [
        "最近吃太多了，怕胖怎么办",
        "熬夜皮肤好差，求推荐",
        "失眠睡不着，有没有好用的",
        "这个牌子怎么样？",
        "在哪里买？"
    ]

    print("=" * 40)
    print("预设回复测试 (纯预设模式)")
    print("=" * 40)

    for comment in test_comments:
        reply = generate_reply(comment)
        print(f"\n评论: {comment}")
        print(f"回复: {reply} ({len(reply)}字)")

    print("\n" + "=" * 40)
    print("所有测试完成 - 使用预设回复列表")
    print("响应快速，无网络延迟")
    print("=" * 40)
