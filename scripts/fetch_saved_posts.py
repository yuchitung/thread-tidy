#!/usr/bin/env python3
"""
Fetch saved posts from Threads using saved session cookies.
More reliable than automated login, especially for Instagram-linked accounts.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from playwright.sync_api import sync_playwright, Page

# Configuration constants
TIMEOUT_CONFIG = {
    "page_load": 10000,        # Page load timeout (ms)
    "initial_wait": 3000,      # Initial wait time (ms)
    "scroll_wait": 4000,       # Wait time after scrolling (ms)
    "ui_interaction": 1000     # UI interaction wait time (ms)
}

SCROLL_CONFIG = {
    "smart_mode_max": 50,      # Max scrolls in smart mode
    "full_mode_max": 100,      # Max scrolls in full mode
    "no_new_posts_limit": 20,   # Stop threshold for consecutive no new posts
    "save_interval": 10        # Save every N scrolls
}

CONTENT_CONFIG = {
    "min_content_length": 10,  # Minimum content length
    "excluded_keywords": ['icon', 'logo', 'button', 'avatar']  # Media keywords to exclude
}

# URL configuration
URLS = {
    "base": "https://www.threads.com",
    "saved_posts": "https://www.threads.com/saved"
}

# Selector configuration
SELECTORS = {
    "posts": [
        '[data-testid="post"]',
        'article',
        '[role="article"]',
        'div[data-pressable-container="true"]'
    ],
    "username": [
        'a[href^="/@"]',
        '[data-testid="username"]',
        '.x1i10hfl.xjbqb8w.x1ejq31n.xd10rxx'
    ],
    "display_name": [
        '[data-testid="username"]',
        '.x1i10hfl.xjbqb8w.x1ejq31n.xd10rxx span',
        'h3', 'h4'
    ],
    "content": [
        'span[dir="auto"]',
        '[data-testid="post-text"]',
        '[data-testid="text-post-content"]',
        'div[dir="auto"]',
        'div > span'
    ],
    "timestamp": [
        'time',
        '[datetime]',
        'a[href*="/post/"] time'
    ]
}


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_cookies_path() -> Path:
    """Get the cookies.json file path."""
    return get_project_root() / "cookies.json"


def get_posts_path() -> Path:
    """Get the posts.json file path."""
    return get_project_root() / "public" / "posts.json"


def load_cookies() -> List[Dict]:
    """Load cookies from cookies.json file."""
    cookies_path = get_cookies_path()
    
    if not cookies_path.exists():
        print("❌ cookies.json not found!")
        print("💡 How to get cookies:")
        print("   1. Open Threads in your browser")
        print("   2. Login normally with your Instagram account")
        print("   3. Press F12 → Application → Cookies → threads.com")
        print("   4. Copy all cookies to cookies.json (see cookies.example.json)")
        return []
    
    try:
        with open(cookies_path, "r") as f:
            cookies = json.load(f)
        print(f"🍪 Loaded {len(cookies)} cookies")
        return cookies
    except Exception as e:
        print(f"❌ Error loading cookies: {e}")
        return []


def navigate_to_saved_posts(page: Page) -> bool:
    """Navigate to the saved posts page."""
    try:
        print("📁 Navigating to saved posts...")
        
        # Go to Threads homepage first
        page.goto(URLS["base"])
        page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_CONFIG["page_load"])
        
        print(f"📍 Homepage: {page.url}")
        
        # Check if we're logged in
        if "login" in page.url.lower():
            print("❌ Not logged in - cookies may be expired")
            return False
        
        # Navigate to saved posts
        page.goto(URLS["saved_posts"])
        page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_CONFIG["page_load"])
        
        print(f"📍 Saved page: {page.url}")
        
        # If direct URL doesn't work, try clicking through UI
        if "saved" not in page.url.lower():
            # Click profile menu
            page.click('[aria-label="More"]')
            page.wait_for_timeout(TIMEOUT_CONFIG["ui_interaction"])
            
            # Look for saved posts option
            page.click('text="Saved"')
            page.wait_for_load_state("networkidle")
        
        print("✅ Reached saved posts page")
        return True
        
    except Exception as e:
        print(f"❌ Navigation error: {e}")
        print("💡 Tip: The saved posts URL or UI elements may have changed")
        return False


def find_element_by_selectors(element: Any, selectors: List[str], attribute: Optional[str] = None) -> str:
    """Generic function to traverse selectors and find elements"""
    for selector in selectors:
        found = element.query_selector(selector)
        if found:
            if attribute:
                result = found.get_attribute(attribute)
                if result:
                    return result
            else:
                result = found.inner_text().strip()
                if result:
                    return result
    return ""


def extract_post_url_and_id(post_element: Any) -> Tuple[str, str]:
    """Extract post URL and ID"""
    post_link = post_element.query_selector('a[href*="/post/"]')
    if not post_link:
        # Try alternative selector
        post_link = post_element.query_selector('a[href*="threads.com"]')
    
    post_url = post_link.get_attribute("href") if post_link else ""
    post_id = ""
    
    if "/post/" in post_url:
        post_id = post_url.split("/post/")[-1].split("?")[0]
    
    # Ensure URL is complete
    if post_url.startswith("/"):
        post_url = f"{URLS['base']}{post_url}"
    
    return post_url, post_id or f"unknown_{datetime.now().timestamp()}"


def extract_author_info(post_element: Any) -> Dict[str, str]:
    """Extract author information (username, display_name)"""
    username = ""
    display_name = ""
    
    # Extract username
    for selector in SELECTORS["username"]:
        username_element = post_element.query_selector(selector)
        if username_element:
            username_text = username_element.get_attribute("href") or username_element.inner_text()
            if username_text:
                if username_text.startswith("/@"):
                    username = username_text[2:]
                elif username_text.startswith("@"):
                    username = username_text[1:]
                else:
                    username = username_text
                break
    
    # Extract display name
    display_name = find_element_by_selectors(post_element, SELECTORS["display_name"])
    if display_name.startswith("@"):
        display_name = ""
    
    return {
        "username": username,
        "display_name": display_name or username
    }


def extract_post_content(post_element: Any) -> str:
    """Extract post content, choosing the longest valid text"""
    content_texts = []
    
    for selector in SELECTORS["content"]:
        elements = post_element.query_selector_all(selector)
        for elem in elements:
            text = elem.inner_text().strip()
            if text and len(text) > CONTENT_CONFIG["min_content_length"] and not text.startswith("@"):
                content_texts.append(text)
        if content_texts:
            break
    
    # Choose the longest text as main content
    return max(content_texts, key=len) if content_texts else ""


def extract_media_info(post_element: Any) -> List[Dict[str, str]]:
    """Extract media information (images, videos)"""
    media = []
    
    # Find images
    img_elements = post_element.query_selector_all('img')
    for img in img_elements:
        src = img.get_attribute("src")
        if src and src.startswith('http') and not any(keyword in src.lower() for keyword in CONTENT_CONFIG["excluded_keywords"]):
            media.append({"type": "image", "url": src})
    
    # Find videos
    video_elements = post_element.query_selector_all('video')
    for video in video_elements:
        src = video.get_attribute("src") or video.get_attribute("poster")
        if src and src.startswith('http'):
            media.append({"type": "video", "url": src})
    
    # Find video source tags
    source_elements = post_element.query_selector_all('video source')
    for source in source_elements:
        src = source.get_attribute("src")
        if src and src.startswith('http'):
            media.append({"type": "video", "url": src})
    
    return media


def extract_timestamp(post_element: Any) -> str:
    """Extract timestamp"""
    for selector in SELECTORS["timestamp"]:
        time_element = post_element.query_selector(selector)
        if time_element:
            datetime_attr = time_element.get_attribute("datetime")
            if datetime_attr:
                return datetime_attr
    return ""


def extract_post_data(post_element: Any) -> Optional[Dict[str, Any]]:
    """Extract all data from post element"""
    try:
        post_url, post_id = extract_post_url_and_id(post_element)
        author_info = extract_author_info(post_element)
        content = extract_post_content(post_element)
        media = extract_media_info(post_element)
        timestamp = extract_timestamp(post_element)
        
        return {
            "post_id": post_id,
            "url": post_url,
            "author": author_info,
            "content": content,
            "media": media,
            "timestamp": timestamp,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "categories": [],
            "keywords": []
        }
        
    except Exception as e:
        # Only log real errors, filter out normal empty value cases
        if "post_id" not in str(e) and "NoneType" not in str(e):
            print(f"⚠️ Error extracting post data: {e}")
        return None


def collect_post_elements_on_page(page: Page) -> List[Any]:
    """Collect post elements on current page"""
    post_elements = []
    for selector in SELECTORS["posts"]:
        elements = page.query_selector_all(selector)
        if elements:
            # Filter out containers that are obviously not posts
            filtered_elements = []
            for elem in elements:
                try:
                    # Check if contains post link or content
                    has_post_link = elem.query_selector('a[href*="/post/"]')
                    has_content = elem.query_selector('span[dir="auto"]')
                    
                    if has_post_link or has_content:
                        filtered_elements.append(elem)
                except Exception:
                    # Ignore elements where selector query fails
                    continue
                    
            post_elements = filtered_elements
            print(f"✅ Found {len(filtered_elements)} valid posts (from {len(elements)} total containers)")
            break
    
    return post_elements


def extract_posts_from_elements(post_elements: List[Any], seen_post_ids: set, existing_post_ids: Optional[set] = None) -> Tuple[List[Dict[str, Any]], int]:
    """Extract data from post elements, return (new posts list, existing posts count)"""
    new_posts = []
    existing_found_count = 0
    stop_on_existing = existing_post_ids is not None
    
    for element in post_elements:
        post_data = extract_post_data(element)
        
        if post_data and post_data["post_id"] not in seen_post_ids:
            post_id = post_data["post_id"]
            
            # Check if this is an existing post
            if stop_on_existing and existing_post_ids and post_id in existing_post_ids:
                existing_found_count += 1
                print(f"🔍 Found existing post: {post_id}")
            else:
                # Basic validation
                if post_data["content"] or post_data["media"] or post_data["post_id"]:
                    new_posts.append(post_data)
                    seen_post_ids.add(post_data["post_id"])
        else:
            print("⚠️ Failed to extract post data from element")
    
    return new_posts, existing_found_count


def scroll_and_extract_posts(page: Page, existing_post_ids: Optional[set] = None) -> List[Dict[str, Any]]:
    """Scroll through saved posts and extract all post data."""
    posts = []
    seen_post_ids = set()
    
    print("📜 Scrolling and extracting posts...")
    
    # Wait for initial content
    page.wait_for_timeout(TIMEOUT_CONFIG["initial_wait"])
    
    # Use smart mode if existing posts found, otherwise use full mode
    if existing_post_ids:
        print(f"🧠 Smart mode: Will stop when hitting existing posts (found {len(existing_post_ids)} existing)")
        max_scrolls = SCROLL_CONFIG["smart_mode_max"]
    else:
        print("🔄 Full mode: Will crawl all posts")
        max_scrolls = SCROLL_CONFIG["full_mode_max"]
    
    no_new_posts_count = 0
    
    for scroll_count in range(max_scrolls):
        # Collect post elements on current page
        post_elements = collect_post_elements_on_page(page)
        
        if not post_elements:
            print("⚠️ No post elements found - page structure may have changed")
            break
        
        # Extract post data from elements
        new_posts_batch, existing_found_count = extract_posts_from_elements(
            post_elements, seen_post_ids, existing_post_ids
        )
        
        # Add new posts to total list
        posts.extend(new_posts_batch)
        current_batch_count = len(new_posts_batch)
        
        print(f"📊 Scroll {scroll_count + 1}: Found {current_batch_count} new posts, {existing_found_count} existing (Total: {len(posts)})")
        
        # Simple stop condition: stop after N consecutive scrolls with no new posts
        if current_batch_count == 0:
            no_new_posts_count += 1
            if no_new_posts_count >= SCROLL_CONFIG["no_new_posts_limit"]:
                print(f"✅ Smart stop: No new posts in last {SCROLL_CONFIG['no_new_posts_limit']} scrolls")
                break
        else:
            no_new_posts_count = 0
        
        # Scroll down
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(TIMEOUT_CONFIG["scroll_wait"])
        
        # Save every N scrolls to avoid data loss
        if (scroll_count + 1) % SCROLL_CONFIG["save_interval"] == 0:
            print(f"📝 Mid-save: Scraped {len(posts)} posts")
            save_posts_to_json(posts)
    
    return posts


def load_existing_posts() -> List[Dict[str, Any]]:
    """Load existing posts from public/posts.json."""
    posts_path = get_posts_path()
    
    if not posts_path.exists():
        print("📝 No existing posts.json found, will create new file")
        return []
    
    try:
        with open(posts_path, "r", encoding="utf-8") as f:
            existing_posts = json.load(f)
        print(f"📖 Loaded {len(existing_posts)} existing posts")
        return existing_posts
    except Exception as e:
        print(f"⚠️ Error loading existing posts: {e}")
        return []


def merge_posts(existing_posts: List[Dict[str, Any]], new_posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge new posts with existing posts, avoiding duplicates."""
    existing_ids = {post.get("post_id") for post in existing_posts}
    
    # Filter out duplicates from new posts
    unique_new_posts = [post for post in new_posts if post.get("post_id") not in existing_ids]
    
    # Combine existing + new posts
    merged_posts = existing_posts + unique_new_posts
    
    # Sort by saved_at timestamp (newest first)
    try:
        merged_posts.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
    except (TypeError, ValueError):
        # Fallback sorting if timestamp format is inconsistent
        merged_posts.sort(key=lambda x: x.get("post_id", ""), reverse=True)
    
    print(f"📊 Merge summary:")
    print(f"   Existing posts: {len(existing_posts)}")
    print(f"   New posts found: {len(unique_new_posts)}")
    print(f"   Total after merge: {len(merged_posts)}")
    
    return merged_posts


def save_posts_to_json(posts: List[Dict[str, Any]], incremental: bool = True) -> None:
    """Save posts to public/posts.json with optional incremental merge."""
    output_path = get_posts_path()
    
    if incremental:
        # Load existing posts and merge
        existing_posts = load_existing_posts()
        final_posts = merge_posts(existing_posts, posts)
    else:
        # Overwrite completely
        final_posts = posts
        print(f"🔄 Overwriting with {len(posts)} posts")
    
    # Create backup of existing file
    if output_path.exists() and incremental:
        backup_path = get_project_root() / "public" / f"posts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import shutil
        shutil.copy2(output_path, backup_path)
        print(f"💾 Backup saved to: {backup_path}")
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_posts, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {len(final_posts)} posts to {output_path}")
        
    except Exception as e:
        print(f"❌ Error saving posts: {e}")


def main():
    """Main function to fetch saved posts using cookies."""
    print("🧵 ThreadTidy - Fetch Saved Posts")
    print("=" * 50)
    
    # Load cookies
    cookies = load_cookies()
    if not cookies:
        sys.exit(1)
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        
        # Add cookies to context
        context.add_cookies(cookies)
        
        page = context.new_page()
        
        try:
            # Navigate to saved posts
            if not navigate_to_saved_posts(page):
                print("💡 Tips for debugging:")
                print("   - Check if cookies are still valid")
                print("   - Try updating cookies from browser")
                print("   - Threads UI may have changed")
                sys.exit(1)
            
            # Load existing posts to enable smart crawling
            existing_posts = load_existing_posts()
            existing_post_ids = {post.get("post_id") for post in existing_posts} if existing_posts else set()
            
            # Extract all posts
            posts = scroll_and_extract_posts(page, existing_post_ids)
            
            if posts:
                save_posts_to_json(posts)
                print(f"🎉 Successfully fetched {len(posts)} saved posts!")
            else:
                print("⚠️ No posts found")
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            
        finally:
            browser.close()


if __name__ == "__main__":
    main()