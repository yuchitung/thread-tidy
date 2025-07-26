#!/usr/bin/env python3
"""
Classify Threads posts using OpenAI API
Process all saved posts and automatically add categories and keywords
"""

import json
import os
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from classification_prompt import (
    SYSTEM_PROMPT, 
    build_classification_prompt, 
    prepare_posts_for_classification,
    OPENAI_CONFIG,
    BATCH_CONFIG
)

load_dotenv()

def load_all_posts():
    """Load all posts"""
    project_root = Path(__file__).parent.parent
    posts_path = project_root / "public" / "posts.json"
    
    if not posts_path.exists():
        print("❌ posts.json not found!")
        print("💡 Please run first: python3 scripts/fetch_saved_posts.py")
        return []
    
    try:
        with open(posts_path, "r", encoding="utf-8") as f:
            posts = json.load(f)
        print(f"📊 Loaded {len(posts)} posts")
        return posts
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing posts.json: {e}")
        return []
    except Exception as e:
        print(f"❌ Error reading posts.json: {e}")
        return []

def save_progress(posts):
    """Save classification progress to posts.json"""
    posts_path = Path(__file__).parent.parent / "public" / "posts.json"
    try:
        with open(posts_path, "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
        print(f"💾 Progress saved: {len(posts)} posts updated")
    except Exception as e:
        print(f"❌ Error saving progress: {e}")
        print("⚠️  Classification results may be lost!")

def get_api_key():
    """Check and return OpenAI API key"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("💡 Please set: export OPENAI_API_KEY='your-api-key'")
        return None
    return api_key

def get_unclassified_posts(all_posts):
    """Get unclassified posts and display statistics"""
    unclassified_posts = [
        post for post in all_posts 
        if not post.get("categories") or len(post.get("categories", [])) == 0
    ]
    
    print(f"📝 Found {len(unclassified_posts)} posts to classify")
    
    if len(unclassified_posts) == 0:
        print("✅ All posts already classified!")
        return None
    
    return unclassified_posts

def confirm_classification(count):
    """User confirmation to proceed with classification"""
    print(f"💡 Run 'python3 scripts/estimate_cost.py' to estimate API costs before proceeding")
    confirm = input(f"🤖 Proceed to classify {count} posts? (y/N): ").strip().lower()
    return confirm == 'y'

def process_batches(client, unclassified_posts, all_posts):
    """Process all classification batches, return successful and failed batch counts"""
    batch_size = BATCH_CONFIG["batch_size"]
    total_batches = (len(unclassified_posts) + batch_size - 1) // batch_size
    successful_batches = 0
    failed_batches = 0
    
    print(f"\n🤖 Starting classification in {total_batches} batches...")
    
    for i in range(0, len(unclassified_posts), batch_size):
        batch_num = i // batch_size + 1
        batch = unclassified_posts[i:i + batch_size]
        
        print(f"\n🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} posts)...")
        
        classifications = classify_batch(client, batch)
        
        if classifications:
            # Update corresponding data in original posts
            classification_dict = {c['post_id']: c for c in classifications}
            
            for post in all_posts:
                if post['post_id'] in classification_dict:
                    classification = classification_dict[post['post_id']]
                    post['categories'] = classification['categories']
                    post['keywords'] = classification['keywords']
            
            print(f"✅ Batch {batch_num} completed ({len(classifications)} posts classified)")
            successful_batches += 1
            
            # Save after each batch to avoid data loss
            save_progress(all_posts)
            
            # Brief wait to avoid API rate limits
            time.sleep(BATCH_CONFIG["delay_between_batches"])
        else:
            print(f"❌ Batch {batch_num} failed")
            failed_batches += 1
    
    return successful_batches, failed_batches

def print_final_statistics(all_posts):
    """Print final statistics report"""
    print(f"\n🎉 Classification completed!")
    
    # Final statistics
    classified_posts = [p for p in all_posts if p.get("categories") and len(p.get("categories", [])) > 0]
    
    all_categories = []
    all_keywords = []
    for post in classified_posts:
        all_categories.extend(post.get("categories", []))
        all_keywords.extend(post.get("keywords", []))
    
    category_counts = {}
    for cat in all_categories:
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    print(f"\n📊 Final Statistics:")
    print(f"   Total classified posts: {len(classified_posts)}/{len(all_posts)}")
    print(f"   Unique categories: {len(set(all_categories))}")
    print(f"   Category distribution: {dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True))}")
    print(f"   Total unique keywords: {len(set(all_keywords))}")
    print(f"   Most common keywords: {sorted(set(all_keywords))[:10]}")

def classify_batch(client, posts_batch):
    """Classify a batch of posts using OpenAI API"""
    
    # Use shared prompt construction function
    posts_for_classification = prepare_posts_for_classification(posts_batch)
    prompt = build_classification_prompt(posts_for_classification)

    try:
        response = client.chat.completions.create(
            model=OPENAI_CONFIG["model"],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=OPENAI_CONFIG["temperature"]
        )
        
        # Parse response
        result = response.choices[0].message.content.strip()
        
        # Clean markdown formatting
        if result.startswith("```json"):
            result = result.replace("```json", "").replace("```", "").strip()
        elif result.startswith("```"):
            result = result[3:-3].strip()
        
        classifications = json.loads(result)
        return classifications
        
    except Exception as e:
        print(f"❌ Classification error: {e}")
        return []


def classify_posts():
    """Classify unclassified posts"""
    
    api_key = get_api_key()
    if not api_key:
        return
    
    client = OpenAI(api_key=api_key)
    
    all_posts = load_all_posts()
    if not all_posts:
        return
    
    unclassified_posts = get_unclassified_posts(all_posts)
    if not unclassified_posts:
        return
    
    if not confirm_classification(len(unclassified_posts)):
        print("⏹️ Classification cancelled")
        return
    
    successful_batches, failed_batches = process_batches(client, unclassified_posts, all_posts)
    
    if successful_batches > 0:
        print_final_statistics(all_posts)
    else:
        print("\n❌ All batches failed! No posts were classified.")
        return
    
    if failed_batches > 0:
        total_batches = successful_batches + failed_batches
        print(f"\n⚠️  Warning: {failed_batches}/{total_batches} batches failed")
        print("💡 Some posts may not have been classified. Consider running the script again.")

if __name__ == "__main__":
    classify_posts()