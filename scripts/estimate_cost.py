#!/usr/bin/env python3
"""
Estimate OpenAI API classification costs
Analyze post content length and calculate expected token consumption and costs
"""

import json
import tiktoken
from pathlib import Path
from classification_prompt import (
    SYSTEM_PROMPT,
    CLASSIFICATION_RULES,
    prepare_posts_for_classification,
    PRICING,
    BATCH_CONFIG,
    CONTENT_CONFIG
)

def load_posts():
    """Load posts data"""
    project_root = Path(__file__).parent.parent
    posts_path = project_root / "public" / "posts.json"
    
    if not posts_path.exists():
        print("❌ posts.json not found!")
        return []
    
    with open(posts_path, "r", encoding="utf-8") as f:
        posts = json.load(f)
    
    return posts

def estimate_tokens(text, model="gpt-4o-mini"):
    """Estimate token count for text"""
    # GPT-4o-mini uses cl100k_base encoding
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def estimate_classification_cost():
    """Estimate classification costs"""
    
    posts = load_posts()
    if not posts:
        return
    
    print(f"📊 Analyzing {len(posts)} posts...")
    
    # Find unclassified posts
    unclassified_posts = [
        post for post in posts 
        if not post.get("categories") or len(post.get("categories", [])) == 0
    ]
    
    print(f"📝 Found {len(unclassified_posts)} unclassified posts")
    
    if len(unclassified_posts) == 0:
        print("✅ All posts already classified!")
        return
    
    # Analyze content length
    content_lengths = []
    total_input_tokens = 0
    
    # Use shared prompt content
    system_tokens = estimate_tokens(SYSTEM_PROMPT)
    rules_tokens = estimate_tokens(CLASSIFICATION_RULES)
    
    # Use shared batch configuration
    batch_size = BATCH_CONFIG["batch_size"]
    total_batches = (len(unclassified_posts) + batch_size - 1) // batch_size
    
    for i in range(0, len(unclassified_posts), batch_size):
        batch = unclassified_posts[i:i + batch_size]
        
        # Use shared post preparation function
        batch_content = prepare_posts_for_classification(batch)
        
        # Record content length for statistics
        for post_data in batch_content:
            content_lengths.append(len(post_data["content"]))
        
        # Calculate tokens for this batch
        batch_json = json.dumps(batch_content, ensure_ascii=False, indent=2)
        batch_content_tokens = estimate_tokens(batch_json)
        
        # Total input tokens = system prompt + rules + content
        batch_input_tokens = system_tokens + rules_tokens + batch_content_tokens
        total_input_tokens += batch_input_tokens
    
    # Estimate output tokens
    total_output_tokens = len(unclassified_posts) * PRICING["estimated_output_tokens_per_post"]
    
    # Calculate costs
    input_cost = (total_input_tokens / 1000) * PRICING["input_cost_per_1k_tokens"]
    output_cost = (total_output_tokens / 1000) * PRICING["output_cost_per_1k_tokens"]
    total_cost = input_cost + output_cost
    
    # Content statistics
    avg_content_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
    max_content_length = max(content_lengths) if content_lengths else 0
    min_content_length = min(content_lengths) if content_lengths else 0
    
    print(f"\n📈 Content Analysis:")
    print(f"   Average content length: {avg_content_length:.0f} characters")
    print(f"   Max content length: {max_content_length} characters")
    print(f"   Min content length: {min_content_length} characters")
    
    print(f"\n🤖 Token Estimation:")
    print(f"   Total input tokens: {total_input_tokens:,}")
    print(f"   Estimated output tokens: {total_output_tokens:,}")
    print(f"   Total tokens: {total_input_tokens + total_output_tokens:,}")
    
    print(f"\n💰 Cost Estimation (GPT-4o-mini):")
    print(f"   Input cost: ${input_cost:.4f}")
    print(f"   Output cost: ${output_cost:.4f}")
    print(f"   Total estimated cost: ${total_cost:.4f}")
    print(f"   Cost per post: ${total_cost/len(unclassified_posts):.6f}")
    
    print(f"\n📦 Processing Plan:")
    print(f"   Batch size: {batch_size} posts per batch")
    print(f"   Total batches: {total_batches}")
    print(f"   Estimated time: ~{total_batches * 3} seconds (with 1s delays)")
    
    return {
        "unclassified_count": len(unclassified_posts),
        "total_cost": total_cost,
        "cost_per_post": total_cost/len(unclassified_posts),
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "batches": total_batches
    }

if __name__ == "__main__":
    estimate_classification_cost()