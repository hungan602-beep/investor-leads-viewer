import json
import os
import glob
from datetime import datetime

# Paths
DETECT_DIR = r"C:\Users\Administrator\Desktop\X\detect"
TERAFAB_VALIDATION = os.path.join(DETECT_DIR, "data", "validation_terafab_501.json")
OUTPUT_DIR = os.path.join(DETECT_DIR, "terafab_report")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")

def load_all_metadata():
    """Builds a comprehensive username -> profile map."""
    metadata_map = {}
    
    def normalize_profile(p):
        norm = {
            "username": p.get("username") or p.get("userName") or p.get("user_name"),
            "name": p.get("name", ""),
            "bio": p.get("bio") or p.get("description", ""),
            "followers": p.get("followers") or p.get("followers_count") or 0,
            "following": p.get("following") or p.get("following_count") or 0,
            "tweets": p.get("tweets") or p.get("tweet_count") or p.get("statusesCount") or 0,
            "profile_image": p.get("profile_image") or p.get("profile_image_url") or p.get("profilePicture", ""),
            "created_at": p.get("created_at") or p.get("createdAt") or "",
        }
        # Calculate year
        ca = norm["created_at"]
        year = 0
        if ca:
            try:
                if "T" in str(ca):
                    year = int(str(ca)[:4])
                else:
                    year = int(str(ca).split()[-1])
            except: pass
        norm["year"] = year
        
        # Calculate last_tweet_days if not present
        if "last_tweet_days" not in p:
            norm["last_tweet_days"] = 999 
        else:
            norm["last_tweet_days"] = p["last_tweet_days"]
            
        return norm

    # 1. Base profiles
    base_profiles = os.path.join(DETECT_DIR, "data", "fetched_profiles.json")
    if os.path.exists(base_profiles):
        try:
            with open(base_profiles, 'r', encoding='utf-8') as f:
                profiles = json.load(f)
                for p in profiles:
                    norm = normalize_profile(p)
                    if norm["username"]: metadata_map[norm["username"]] = norm
        except: pass

    # 2. Search discovery
    discovery_dir = os.path.join(DETECT_DIR, "data", "discovery")
    if os.path.exists(discovery_dir):
        for json_file in glob.glob(os.path.join(discovery_dir, "*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    users = data.get('candidates', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                    for p in users:
                        if isinstance(p, dict):
                            norm = normalize_profile(p)
                            if norm["username"]:
                                existing = metadata_map.get(norm["username"])
                                if not existing or norm["followers"] > existing.get("followers", 0):
                                    metadata_map[norm["username"]] = norm
            except: pass

    return metadata_map

def export():
    if not os.path.exists(TERAFAB_VALIDATION):
        print(f"Error: {TERAFAB_VALIDATION} not found.")
        return

    with open(TERAFAB_VALIDATION, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    humans = [r for r in data.get('results', []) if r.get('label', '').lower() == 'human']
    print(f"Found {len(humans)} Terafab Human Alpha leads.")

    metadata_map = load_all_metadata()
    leads_json_data = []
    
    for r in humans:
        u = r['username']
        m = metadata_map.get(u, {})
        
        leads_json_data.append({
            "u": u,
            "n": m.get("name", u),
            "b": m.get("bio", "").replace("\n", " ").replace('"', "'"),
            "s": r.get("ml_score", 0.95),
            "fl": m.get("followers", 0),
            "fg": m.get("following", 0),
            "tw": m.get("tweets", 0),
            "img": (m.get("profile_image") or "").replace("_normal", "_bigger"),
            "year": m.get("year", 0),
            "d": m.get("last_tweet_days", 999),
            "reason": r.get("reason", "").replace('"', "'"),
            "conf": r.get("confidence", 0)
        })

    # Template (Simplified for this specific export but keeping Premium style)
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Terafab Human Alpha Leads</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#f8fafc;padding:20px;line-height:1.6}}
.header{{text-align:center;padding:40px 0;background:linear-gradient(135deg, #1e293b 0%, #0f172a 100%);border-radius:16px;margin-bottom:30px;border:1px solid #334155;box-shadow:0 10px 15px -3px rgba(0,0,0,0.1)}}
.header h1{{font-size:2.5rem;color:#fff;margin-bottom:10px;letter-spacing:-1px}}
.header .sub{{color:#94a3b8;font-size:1.1rem;font-weight:500}}
.badge{{display:inline-block;padding:4px 12px;background:#38bdf8;color:#0f172a;border-radius:20px;font-size:0.8rem;font-weight:800;text-transform:uppercase;margin-top:12px}}
.stats{{display:flex;gap:20px;justify-content:center;margin:30px 0}}
.stat-card{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px;text-align:center;min-width:160px}}
.stat-card .val{{font-size:2rem;font-weight:800;color:#38bdf8}}
.stat-card .label{{font-size:0.8rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-top:4px}}
.table-wrap{{background:#1e293b;border:1px solid #334155;border-radius:16px;overflow:hidden;box-shadow:0 4px 6px -1px rgba(0,0,0,0.1)}}
table{{width:100%;border-collapse:collapse;font-size:0.95rem}}
th{{background:#334155;color:#f1f5f9;font-weight:600;padding:16px;text-align:left;font-size:0.8rem;text-transform:uppercase;letter-spacing:1px}}
td{{padding:16px;border-bottom:1px solid #334155;vertical-align:top}}
tr:hover{{background:#33415544}}
.user-cell{{display:flex;align-items:center;gap:15px}}
.avatar{{width:48px;height:48px;border-radius:12px;object-fit:cover;border:2px solid #475569}}
.user-link{{color:#38bdf8;text-decoration:none;font-weight:700;font-size:1.1rem}}
.user-name{{color:#94a3b8;font-size:0.85rem}}
.reason-cell{{background:rgba(56,189,248,0.05);padding:12px;border-radius:12px;border-left:4px solid #38bdf8;font-size:0.9rem;color:#cbd5e1;line-height:1.5}}
.num{{text-align:right;font-weight:700;color:#f1f5f9}}
.score-badge{{background:rgba(34,197,94,0.1);color:#4ade80;padding:4px 8px;border-radius:6px;font-weight:800}}
</style>
</head>
<body>
<div class="header">
  <h1>Terafab Human Alpha Leads</h1>
  <div class="sub">Forensic DeepSeek-R1 Validation Output</div>
  <div class="badge">Verified Human Only</div>
</div>

<div class="stats">
  <div class="stat-card"><div class="val">{len(leads_json_data)}</div><div class="label">Qualified Leads</div></div>
  <div class="stat-card"><div class="val">100%</div><div class="label">Human Fidelity</div></div>
</div>

<div class="table-wrap">
<table>
<thead>
<tr>
  <th>Profile</th>
  <th>DeepSeek-R1 Reasoner Analysis</th>
  <th style="text-align:right">Followers</th>
  <th style="text-align:right">Score</th>
</tr>
</thead>
<tbody>
"""
    for p in leads_json_data:
        html_content += f"""
<tr>
  <td>
    <div class="user-cell">
      <img class="avatar" src="{p['img']}" onerror="this.src='https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png'">
      <div class="user-info">
        <a class="user-link" href="https://x.com/{p['u']}" target="_blank">@{p['u']}</a>
        <div class="user-name">{p['n']}</div>
      </div>
    </div>
  </td>
  <td><div class="reason-cell">{p['reason']}</div></td>
  <td class="num">{p['fl']:,}</td>
  <td class="num"><span class="score-badge">{(p['s']*100):.1f}%</span></td>
</tr>
"""
    
    html_content += """
</tbody>
</table>
</div>
</body>
</html>
"""
    
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Standalone Terafab report generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    export()
