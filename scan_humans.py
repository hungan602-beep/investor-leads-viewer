# by nichxbt
"""Scan all human accounts (<=1K followers & following) with DeepSeek chat + VALIDATION prompt.

Usage:
    python scan_humans.py                          # scan all 15,166
    python scan_humans.py --can-dm-only            # scan only 4,929 can_dm=True
    python scan_humans.py --summary-only           # print summary from existing results
"""

import argparse
import json
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from label import build_evidence_prompt, VALIDATION_SYSTEM_PROMPT

_DETECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR     = os.path.join(_DETECT_DIR, "data")
TWEETS_DIR   = os.path.join(DATA_DIR, "user_tweets")
SCAN_PATH    = os.path.join(DATA_DIR, "scan_results.json")
HARVEST_PATH = os.path.join(DATA_DIR, "harvest", "marionawfal.json")
OUT_PATH     = os.path.join(DATA_DIR, "validation_results_humans_1k.json")

load_dotenv(os.path.join(_DETECT_DIR, ".env"), override=True)


def load_profiles(can_dm_only=False):
    with open(SCAN_PATH, encoding="utf-8") as f:
        scan = json.load(f)
    with open(HARVEST_PATH, encoding="utf-8") as f:
        harvest = json.load(f)

    users = harvest.get("users", [])
    if isinstance(users, dict):
        users = list(users.values())
    harvest_idx = {
        (u.get("username") or u.get("userName") or "").lower(): u
        for u in users
    }

    targets = []
    for p in scan["profiles"]:
        if p["label"] != "human":
            continue
        if p.get("followers_count", 0) > 1000 or p.get("following_count", 0) > 1000:
            continue

        uname = p["username"].lower()
        full = harvest_idx.get(uname, {})

        if can_dm_only:
            raw = full.get("_raw", {})
            if not (isinstance(raw, dict) and raw.get("can_dm")):
                continue

        # inject tweet stats
        tweet_file = os.path.join(TWEETS_DIR, f"{p['username']}.json")
        if os.path.exists(tweet_file):
            try:
                with open(tweet_file, encoding="utf-8", errors="replace") as f:
                    cached = json.load(f)
                full["_tweet_stats"] = cached.get("_stats", {})
            except Exception:
                pass

        targets.append({
            "username":  p["username"],
            "ml_score":  p["bot_score"],
            "ml_label":  p["label"],
            "followers": p.get("followers_count", 0),
            "following": p.get("following_count", 0),
            "has_tweets": bool(p.get("has_tweets")),
            "profile":   full,
        })

    return targets


def _label_one(client, model, item, idx, total):
    import re as _re
    username = item["username"]
    prompt   = build_evidence_prompt(item["profile"])
    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=512,
            temperature=0.0,
            messages=[
                {"role": "system", "content": VALIDATION_SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
        )
        text = (response.choices[0].message.content or "").strip()
        m = _re.search(r'\{[^}]+\}', text)
        result = json.loads(m.group() if m else text)
        label_str  = result.get("label", "UNCERTAIN").upper()
        confidence = int(result.get("confidence", 50))
        reason     = result.get("reason", "")
        return idx, {"label": label_str, "confidence": confidence,
                     "reason": reason, "error": None}
    except Exception as e:
        return idx, {"label": "UNCERTAIN", "confidence": 0,
                     "reason": f"Error: {e}", "error": str(e)}


def _label_with_retry(client, model, item, idx, total, max_retries=3):
    for attempt in range(max_retries + 1):
        idx_out, result = _label_one(client, model, item, idx, total)
        if result["error"] and attempt < max_retries:
            err = str(result["error"])
            if any(x in err for x in ["529", "500", "502", "503", "Connection"]):
                time.sleep(2 ** attempt + random.random())
                continue
        return idx_out, result
    return idx, result


def run(targets, concurrency=20, model="deepseek-chat"):
    from openai import OpenAI
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        print("ERROR: DEEPSEEK_API_KEY not set")
        sys.exit(1)
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    # Load existing results (resume support)
    results = []
    existing = set()
    if os.path.exists(OUT_PATH):
        try:
            with open(OUT_PATH, encoding="utf-8") as f:
                old = json.load(f)
            results = old.get("results", [])
            existing = {r["username"].lower() for r in results}
            print(f"  Resuming: {len(existing):,} already done")
        except Exception:
            pass

    work = [t for t in targets if t["username"].lower() not in existing]
    total = len(work)

    if total == 0:
        print("  All profiles already validated.")
        return results

    print(f"\n{'='*60}")
    print(f"  Scanning {total:,} profiles  (model={model}, concurrency={concurrency})")
    print(f"{'='*60}")

    completed = errors = 0
    save_every = 500  # checkpoint every 500

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(_label_with_retry, client, model, item, i, total): item
            for i, item in enumerate(work)
        }
        for future in as_completed(futures):
            item = futures[future]
            idx, result = future.result()
            completed += 1

            lbl = result["label"]
            conf = result["confidence"]
            reason = result["reason"]
            is_error = bool(result["error"])
            if is_error:
                errors += 1

            claude_label = {"BOT": "bot", "HUMAN": "human"}.get(lbl, "uncertain")
            agrees = (item["ml_label"] == claude_label)

            entry = {
                "username":          item["username"],
                "ml_score":          item["ml_score"],
                "ml_label":          item["ml_label"],
                "followers_count":   item["followers"],
                "following_count":   item["following"],
                "has_tweets":        item["has_tweets"],
                "claude_label":      claude_label,
                "claude_confidence": conf,
                "claude_reason":     reason,
                "agrees":            agrees,
            }
            results.append(entry)

            marker = "ERR" if is_error else ("OK " if agrees else "!= ")
            print(f"  [{completed:>5}/{total}] {marker} @{item['username']:22s} "
                  f"ML={item['ml_label']}({item['ml_score']:.2f}) "
                  f"LLM={claude_label}(conf={conf}) "
                  f"-- {reason[:60]}", flush=True)

            # Checkpoint save
            if completed % save_every == 0:
                _save(results, model)
                print(f"  [checkpoint] saved {len(results):,} results", flush=True)

    _save(results, model)
    print(f"\n  Done: {completed:,} processed, {errors:,} errors")
    return results


def _save(results, model):
    bots     = sum(1 for r in results if r["claude_label"] == "bot")
    humans   = sum(1 for r in results if r["claude_label"] == "human")
    unc      = sum(1 for r in results if r["claude_label"] == "uncertain")
    output = {
        "scanned_at":   datetime.now().isoformat(),
        "model":        model,
        "prompt":       "validation",
        "total":        len(results),
        "llm_bot":      bots,
        "llm_human":    humans,
        "llm_uncertain": unc,
        "results":      results,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def print_summary():
    if not os.path.exists(OUT_PATH):
        print("No results yet. Run scan first.")
        return
    with open(OUT_PATH, encoding="utf-8") as f:
        data = json.load(f)
    results = data["results"]
    total   = len(results)
    bots    = sum(1 for r in results if r["claude_label"] == "bot")
    humans  = sum(1 for r in results if r["claude_label"] == "human")
    unc     = sum(1 for r in results if r["claude_label"] == "uncertain")
    print(f"\n{'='*50}")
    print(f"  LLM Validation Summary  ({data.get('model','?')})")
    print(f"{'='*50}")
    print(f"  Scanned at:  {data.get('scanned_at','?')}")
    print(f"  Total:       {total:,}")
    print(f"  LLM human:   {humans:,}  ({round(humans/total*100,1)}%)")
    print(f"  LLM bot:     {bots:,}  ({round(bots/total*100,1)}%)")
    print(f"  Uncertain:   {unc:,}  ({round(unc/total*100,1)}%)")

    # can_dm breakdown
    with open(HARVEST_PATH, encoding="utf-8") as f:
        harvest = json.load(f)
    users = harvest.get("users", [])
    if isinstance(users, dict):
        users = list(users.values())
    harvest_idx = {
        (u.get("username") or u.get("userName") or "").lower(): u for u in users
    }
    dm_human = dm_bot = 0
    for r in results:
        h = harvest_idx.get(r["username"].lower(), {})
        raw = h.get("_raw", {})
        can_dm = isinstance(raw, dict) and raw.get("can_dm")
        if can_dm and r["claude_label"] == "human":
            dm_human += 1
        elif can_dm and r["claude_label"] == "bot":
            dm_bot += 1
    print(f"\n  can_dm=True breakdown:")
    print(f"    LLM human (DM-able leads): {dm_human:,}")
    print(f"    LLM bot   (DM-able false+): {dm_bot:,}")


def main():
    parser = argparse.ArgumentParser(description="Scan human accounts with DeepSeek VALIDATION prompt")
    parser.add_argument("--can-dm-only",    action="store_true", help="Only scan can_dm=True accounts")
    parser.add_argument("--concurrency",    type=int, default=20)
    parser.add_argument("--model",          type=str, default="deepseek-chat")
    parser.add_argument("--summary-only",   action="store_true")
    args = parser.parse_args()

    if args.summary_only:
        print_summary()
        return

    print(f"\n{'='*60}")
    print(f"  Loading profiles...")
    print(f"{'='*60}")
    targets = load_profiles(can_dm_only=args.can_dm_only)
    label = "can_dm=True only" if args.can_dm_only else "all humans <=1K/1K"
    print(f"  Loaded {len(targets):,} profiles  ({label})")

    results = run(targets, concurrency=args.concurrency, model=args.model)
    print_summary()


if __name__ == "__main__":
    main()
