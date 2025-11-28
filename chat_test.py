"""
LLM 对话测试脚本
从 config/config.yaml 读取配置
根据 use_openai 自动选择模型
"""
import os
import yaml

# 加载配置
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')

def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return {}

def chat_openai(api_key, base_url, model, system_prompt, user_input):
    """调用 OpenAI"""
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        max_tokens=200,
        temperature=0.8,
    )
    return response.choices[0].message.content.strip()

def chat_dashscope(api_key, model, system_prompt, user_input):
    """调用通义千问"""
    import dashscope
    from dashscope import Generation
    dashscope.api_key = api_key
    response = Generation.call(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        result_format='message',
        max_tokens=200,
        temperature=0.8,
    )
    if response.status_code == 200:
        return response.output.choices[0].message.content.strip()
    else:
        return f"❌ 错误: {response.code} - {response.message}"

def main():
    config = load_config()
    llm_config = config.get('llm', {})
    promo_config = config.get('promotion', {})
    
    use_openai = llm_config.get('use_openai', False)
    system_prompt = llm_config.get('system_prompt', '你是一个助手')
    
    if use_openai:
        oa_config = llm_config.get('openai', {})
        api_key = oa_config.get('api_key')
        base_url = oa_config.get('base_url')
        model = oa_config.get('model')
        provider_name = "OpenAI"
    else:
        ds_config = llm_config.get('dashscope', {})
        api_key = ds_config.get('api_key')
        model = ds_config.get('model')
        base_url = None
        provider_name = "通义千问"
    
    # 获取产品信息
    brand = promo_config.get('brand', '')
    products = promo_config.get('products', [])
    product_info = "\n".join([f"- {p['name']}: {p['effect']}" for p in products])
    
    print("=" * 50)
    print("🤖 LLM 对话测试")
    print("=" * 50)
    print(f"📌 模型: {provider_name} ({model})")
    print(f"📌 品牌: {brand}")
    print(f"📌 产品: {[p['name'] for p in products]}")
    print("-" * 50)
    print("输入 'quit' 或 'q' 退出")
    print("=" * 50)
    
    if not api_key:
        print(f"❌ 未配置 {provider_name} API Key")
        return
    
    # 构建完整的系统提示（包含产品信息）
    full_system = f"""{system_prompt}

推广品牌：{brand}
产品清单：
{product_info}
"""
    
    while True:
        try:
            user_input = input("\n👤 你: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['quit', 'q', 'exit']:
                print("👋 再见!")
                break
            
            # 根据配置调用不同模型
            if use_openai:
                reply = chat_openai(api_key, base_url, model, full_system, user_input)
            else:
                reply = chat_dashscope(api_key, model, full_system, user_input)
            
            print(f"🤖 {provider_name}: {reply}")
            
        except KeyboardInterrupt:
            print("\n👋 再见!")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()
