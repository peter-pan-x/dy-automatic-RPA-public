#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试LLM模块简化后的效果"""

import sys
import os

# 添加项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src.llm_reply import generate_reply

def test_performance():
    """测试回复生成性能"""
    test_comments = [
        "最近总是失眠，有什么好产品推荐吗？",
        "这个茶研官牌子怎么样？",
        "熬夜太多需要补气，求推荐",
        "人参茶真的有用吗？",
        "哪里能买到正品？"
    ]

    import time

    print("=" * 50)
    print("性能测试 - 预设回复模式")
    print("=" * 50)

    total_time = 0
    for i, comment in enumerate(test_comments, 1):
        start_time = time.time()
        reply = generate_reply(comment)
        end_time = time.time()

        duration = (end_time - start_time) * 1000  # 转换为毫秒
        total_time += duration

        print(f"\n{i}. 评论: {comment}")
        print(f"   回复: {reply}")
        print(f"   耗时: {duration:.2f}ms")

    print("\n" + "=" * 50)
    print(f"总测试: {len(test_comments)} 条评论")
    print(f"总耗时: {total_time:.2f}ms")
    print(f"平均耗时: {total_time/len(test_comments):.2f}ms")
    print("✅ 预设回复模式 - 响应极快，无网络延迟！")
    print("=" * 50)

if __name__ == "__main__":
    test_performance()