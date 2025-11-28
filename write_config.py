import os

content = """# ============================================================
# 抖音RPA项目统一配置文件
# ============================================================

# -------------------- 推广产品配置 --------------------
promotion:
  # 1. 推荐品牌
  brand: "茶研官"
  
  # 2 & 3. 产品清单与功效
  products:
    - name: "白芸豆"
      effect: "大餐救星，阻断糖分"
    - name: "胶原蛋白"
      effect: "补充胶原，皮肤变好"
    - name: "睡美人"
      effect: "助眠安神，美容觉"

# -------------------- LLM大模型配置 --------------------
llm:
  # 启用OpenAI (设置为 true 使用OpenAI，false 使用通义千问)
  use_openai: true

  # === 通义千问配置 (Dashscope) ===
  dashscope:
    api_key: "sk-10db66fac896427ca5850157f7e773cc"
    model: "qwen-plus"  # qwen-turbo / qwen-plus / qwen-max

  # === OpenAI配置 ===
  openai:
    api_key: "sk-ObqKkQJhBwblgn0F5oNDoqXDh0bQ0oQHQqesVmI"
    base_url: "https://api.chatanywhere.org"  # API 端点
    model: "gpt-5.1"  # gpt-5.1 或 gpt-5.1-chat-latest

  # === 通用回复配置 ===
  # 回复最大字数
  max_reply_length: 15
  
  # 系统提示词 (定义回复风格)
  system_prompt: |
    你是一个热心的种草达人，在评论区回复用户。
    
    回复原则：
    1. 必须根据用户评论内容，从提供的【产品清单】中选择最合适的一款产品进行推荐。
    2. 如果无法匹配特定产品（或用户未提及具体功效需求），则直接推荐【品牌】。
    3. 严禁引导查看主页、头像或私信。直接给出品牌名或产品名。
    4. 语气自然，像闺蜜推荐，可以使用“亲测有效”、“无限回购”、“墙裂推荐”等词。
    5. 字数严格控制在15字以内。
  
  # 用户提示词模板
  user_prompt_template: |
    推广品牌：{brand}
    产品清单：
    {product_info}
    
    用户评论："{comment}"
    
    请推荐最合适的产品或品牌（15字内）：
  
  # API失败时的备用回复
  fallback_replies:
    - "茶研官这个牌子很不错！"
    - "强推茶研官，亲测有效！"
    - "去搜茶研官，你会回来的"
    - "闺蜜推荐的茶研官，好用"

# -------------------- 评论拦截配置 --------------------
intercept:
  # 触发回复的关键词
  keywords:
    - "有没有"
    - "求推荐"
    - "哪里"
    - "能喝吗"
    - "能吃吗"
    - "什么牌子"
    - "怎么买"
    - "多少钱"
    - "链接"
    - "在哪买"
    - "怎么选"
"""

with open('config/config.yaml', 'w', encoding='utf-8') as f:
    f.write(content)
print("Config written successfully")
