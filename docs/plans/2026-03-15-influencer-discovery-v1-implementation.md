# Influencer Discovery v1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract 1,000 repliers from Trump's finance seed tweet and qualify them as influencers.

**Architecture:** Use `TwScrapeScraper` to batch fetch replies, normalize user data, and apply a finance-specific scoring matrix.

**Tech Stack:** Python 3.12, twscrape, asyncio.

---

### Task 1: Create Extraction Script
Create a specialized script to harvest 1,000 replies and save raw data.

**Files:**
- Create: `scripts/discovery_harvest_v1.py`

**Step 1: Write initial implementation**
```python
import asyncio
import json
import os
import sys
from datetime import datetime

# Root path for imports
PROJECT_ROOT = r"c:\Users\Administrator\Desktop\X\detect"
sys.path.insert(0, PROJECT_ROOT)
from scrapers import get_scraper

async def main():
    tweet_id = "2004012442427277591" # Seed identified in brainstorming
    target_limit = 1000
    
    scraper = get_scraper("twscrape")
    print(f"Harvesting up to {target_limit} replies for Tweet {tweet_id}...")
    
    # fetch_replies is limited but we can call it directly on the api if needed
    # or use the wrapper. The wrapper in free.py uses api.tweet_replies
    replies = scraper.fetch_replies(tweet_id, limit=target_limit)
    
    output_path = os.path.join(PROJECT_ROOT, "data/discovery/raw_replies_v1.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(replies, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(replies)} replies to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: Run verification**
Run: `c:\Users\Administrator\Desktop\X\detect\.venv\Scripts\python.exe scripts/discovery_harvest_v1.py`
Expected: "Saved [X] replies to data/discovery/raw_replies_v1.json"

**Step 3: Commit**
```bash
git add scripts/discovery_harvest_v1.py
git commit -m "feat: add discovery harvesting script"
```

---

### Task 2: Create Scoring & Categorization Script
Create a script to filter and rank the harvested users.

**Files:**
- Create: `scripts/discovery_analyze_v1.py`

**Step 1: Write implementation**
```python
import json
import os
import math

PROJECT_ROOT = r"c:\Users\Administrator\Desktop\X\detect"

PRIMARY_KEYWORDS = ["investor", "economist", "macro", "trader", "crypto"]
SECONDARY_KEYWORDS = ["wealth", "funds", "vc", "stock", "feds"]

def score_user(user):
    followers = user.get("author", {}).get("followers", 0)
    bio = (user.get("author", {}).get("description", "") or "").lower()
    
    if followers < 5000: return -1 # Filter low influence
    
    score = math.log10(followers) if followers > 0 else 0
    
    for kw in PRIMARY_KEYWORDS:
        if kw in bio: score += 5
    for kw in SECONDARY_KEYWORDS:
        if kw in bio: score += 2
        
    return round(score, 2)

def main():
    input_path = os.path.join(PROJECT_ROOT, "data/discovery/raw_replies_v1.json")
    with open(input_path, "r", encoding="utf-8") as f:
        replies = json.load(f)
        
    leads = []
    seen = set()
    for r in replies:
        author = r.get("author", {})
        uname = author.get("userName")
        if not uname or uname in seen: continue
        
        score = score_user(r)
        if score > 0:
            leads.append({
                "userName": uname,
                "name": author.get("name"),
                "bio": author.get("description"),
                "followers": author.get("followers"),
                "score": score,
                "reply": r.get("text")
            })
            seen.add(uname)
            
    leads.sort(key=lambda x: x['score'], reverse=True)
    
    output_path = os.path.join(PROJECT_ROOT, "data/discovery/top_influencers_v1.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)
    
    print(f"Analyzed {len(replies)} replies. Found {len(leads)} qualified influencers.")

if __name__ == "__main__":
    main()
```

**Step 2: Run verification**
Run: `c:\Users\Administrator\Desktop\X\detect\.venv\Scripts\python.exe scripts/discovery_analyze_v1.py`
Expected: Output with count of qualified influencers.

**Step 3: Commit**
```bash
git add scripts/discovery_analyze_v1.py
git commit -m "feat: add discovery analysis script"
```
