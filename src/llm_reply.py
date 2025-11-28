"""
大模型回复模块
从统一配置 config/config.yaml 读取
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
    print(f"📁 配置路径: {CONFIG_PATH}")
    print(f"📄 完整配置: {_config}")
    
    use_openai = _llm_config.get('use_openai', False)
    print(f"🤖 当前模型: {'OpenAI' if use_openai else '通义千问 (Dashscope)'}")
    
    if use_openai:
        key = _llm_config.get('openai', {}).get('api_key')
        print(f"🔑 OpenAI Key: {'已配置' if key else '未配置'}")
    else:
        key = _llm_config.get('dashscope', {}).get('api_key')
        print(f"🔑 Dashscope Key: {'已配置' if key else '未配置'}")


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
    调用大模型生成回复
    """
    # 如果启用预设回复，直接返回预设内容
    if _llm_config.get('use_preset'):
        preset_list = _llm_config.get('preset_replies', [])
        if preset_list:
            return random.choice(preset_list)
        # 如果未配置预设，则继续走大模型流程
    # 从配置读取通用参数
    max_length = _llm_config.get('max_reply_length', 15)
    system_prompt = _llm_config.get('system_prompt', '')
    user_template = _llm_config.get('user_prompt_template', '回复：{comment}')
    fallback_replies = _llm_config.get('fallback_replies', ['不错哦'])
    
    # 准备推广信息
    brand = _promo_config.get('brand', '')
    product_info = get_product_info_str()
    
    # 构建用户提示词
    try:
        user_prompt = user_template.format(
            comment=comment,
            brand=brand,
            product_info=product_info
        )
    except KeyError:
        user_prompt = user_template.format(comment=comment)
    
    # 判断使用哪个模型
    use_openai = _llm_config.get('use_openai', False)
    
    if use_openai:
        return _call_openai(system_prompt, user_prompt, max_length, fallback_replies)
    else:
        return _call_dashscope(system_prompt, user_prompt, max_length, fallback_replies)


def _call_dashscope(system_prompt, user_prompt, max_length, fallback_replies):
    """调用通义千问"""
    ds_config = _llm_config.get('dashscope', {})
    api_key = ds_config.get('api_key', '')
    model = ds_config.get('model', 'qwen-plus')
    
    if not api_key:
        print("      ⚠️ [Dashscope] 未配置API Key")
        return random.choice(fallback_replies)
        
    try:
        import dashscope
        from dashscope import Generation
        
        dashscope.api_key = api_key
        
        response = Generation.call(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            result_format='message',
            max_tokens=50,
            temperature=0.8,
        )
        
        if response.status_code == 200:
            reply = response.output.choices[0].message.content.strip()
            return _process_reply(reply, max_length)
        else:
            print(f"      ⚠️ [Dashscope] API调用失败: {response.code} - {response.message}")
            return random.choice(fallback_replies)
            
    except ImportError:
        print("      ⚠️ 请安装: pip install dashscope")
        return random.choice(fallback_replies)
    except Exception as e:
        print(f"      ⚠️ [Dashscope] 异常: {e}")
        return random.choice(fallback_replies)


def _call_openai(system_prompt, user_prompt, max_length, fallback_replies):
    """调用OpenAI"""
    oa_config = _llm_config.get('openai', {})
    api_key = oa_config.get('api_key', '')
    base_url = oa_config.get('base_url', 'https://api.openai.com/v1')
    model = oa_config.get('model', 'gpt-3.5-turbo')
    
    if not api_key:
        print("      ⚠️ [OpenAI] 未配置API Key")
        return random.choice(fallback_replies)
        
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=50,
            temperature=0.8,
        )
        
        reply = response.choices[0].message.content.strip()
        return _process_reply(reply, max_length)
            
    except ImportError:
        print("      ⚠️ 请安装: pip install openai")
        return random.choice(fallback_replies)
    except Exception as e:
        print(f"      ⚠️ [OpenAI] 异常: {e}")
        return random.choice(fallback_replies)


def _process_reply(reply: str, max_length: int) -> str:
    """处理回复文本：截断、去引号"""
    if len(reply) > max_length:
        reply = reply[:max_length]
    return reply.strip('"\'')


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
    print("🧪 LLM回复测试 (推广模式)")
    print("=" * 40)
    
    for comment in test_comments:
        reply = generate_reply(comment)
        print(f"\n评论: {comment}")
        print(f"回复: {reply} ({len(reply)}字)")
