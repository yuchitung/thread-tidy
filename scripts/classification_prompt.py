#!/usr/bin/env python3
"""
OpenAI classification prompt templates
Shared by classify.py and estimate_cost.py
"""

import json

# System prompt
SYSTEM_PROMPT = "你是專業的中文社群媒體內容分類專家，擅長為 Threads 貼文進行精確分類。"

# Classification rules
CLASSIFICATION_RULES = """請分析以下 Threads 貼文，為每篇貼文分配合適的分類和關鍵字。

分類規則：
1. Categories (1-2個主要分類)：技術、健康、美食、食譜、旅行、生活、學習、工作、娛樂、攝影、設計、投資、職場、運動、韓流、語言學習、流行、寵物
   - 如果內容為空或極短（少於5個字符），請分類為 ["未分類"]
   - 如果無法從內容判斷明確分類，也請分類為 ["未分類"]
   - 如果不符合以上分類，可以創建新的中文分類
2. Keywords (2-5個關鍵字)：具體的標籤，如地點、工具、食物、概念等
   - 對於 "未分類" 的貼文，keywords 可以設為 ["需要手動檢查"]

回傳格式：請回傳 JSON 陣列，每個物件包含 post_id、categories、keywords

請直接回傳 JSON 格式的分類結果，不要包含任何其他文字。"""

def build_classification_prompt(posts_batch):
    """
    Build complete classification prompt
    
    Args:
        posts_batch: List of posts to classify, format:
                    [{"post_id": str, "content": str}, ...]
    
    Returns:
        str: Complete prompt content
    """
    posts_json = json.dumps(posts_batch, ensure_ascii=False, indent=2)
    
    return f"""{CLASSIFICATION_RULES}

貼文內容：
{posts_json}"""

def prepare_posts_for_classification(posts):
    """
    Prepare post data for classification
    
    Args:
        posts: Original posts list
        
    Returns:
        list: Formatted posts list
    """
    max_length = CONTENT_CONFIG["max_content_length"]
    posts_for_classification = []
    
    for post in posts:
        content = post["content"]
        
        # Truncate content to specified length
        if len(content) > max_length:
            content = content[:max_length].rstrip() + CONTENT_CONFIG["truncate_suffix"]
        
        posts_for_classification.append({
            "post_id": post["post_id"],
            "content": content
        })
    return posts_for_classification

# OpenAI API configuration
OPENAI_CONFIG = {
    "model": "gpt-4o-mini",
    "temperature": 0.3
}

# Pricing information (2024 rates)
PRICING = {
    "input_cost_per_1k_tokens": 0.00015,   # $0.00015 per 1k input tokens
    "output_cost_per_1k_tokens": 0.0006,   # $0.0006 per 1k output tokens
    "estimated_output_tokens_per_post": 75  # Estimated output tokens per post
}

# Batch processing configuration
BATCH_CONFIG = {
    "batch_size": 10,
    "delay_between_batches": 1  # seconds
}

# Content processing configuration
CONTENT_CONFIG = {
    "max_content_length": 500,  # Maximum characters per post (approx 350 Chinese chars)
    "truncate_suffix": "..."    # Suffix when truncating (optional)
}