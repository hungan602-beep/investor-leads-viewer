import json
import os
import glob
from datetime import datetime

# Paths
DETECT_DIR = r"C:\Users\Administrator\Desktop\X\detect"
V3_RESULTS_FILE = os.path.join(DETECT_DIR, "data", "validation_results_v3.json")
OUTPUT_FILE = os.path.join(DETECT_DIR, "final_leads_v3.html")

def load_all_metadata():
    """Builds a comprehensive username -> profile map by scanning all data sources with key normalization."""
    metadata_map = {}
    
    def normalize_profile(p):
        """Standardize keys to match gen_html.py patterns where possible."""
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

    # 1. Start with fetched_profiles.json
    base_profiles = os.path.join(DETECT_DIR, "data", "fetched_profiles.json")
    if os.path.exists(base_profiles):
        print(f"Loading base profiles from {base_profiles}...")
        try:
            with open(base_profiles, 'r', encoding='utf-8') as f:
                profiles = json.load(f)
                for p in profiles:
                    norm = normalize_profile(p)
                    if norm["username"]:
                        metadata_map[norm["username"]] = norm
        except Exception as e:
            print(f"Error loading {base_profiles}: {e}")

    # 2. Add profiles from harvest directory
    harvest_dir = os.path.join(DETECT_DIR, "data", "harvest")
    if os.path.exists(harvest_dir):
        print(f"Scanning {harvest_dir} for additional metadata...")
        for json_file in glob.glob(os.path.join(harvest_dir, "*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    users = data if isinstance(data, list) else data.get('users', [])
                    for p in users:
                        if isinstance(p, dict):
                            norm = normalize_profile(p)
                            if norm["username"]:
                                existing = metadata_map.get(norm["username"])
                                if not existing or norm["followers"] > existing.get("followers", 0):
                                    metadata_map[norm["username"]] = norm
            except Exception as e:
                print(f"Warning: could not read {json_file}: {e}")

    # 3. Add profiles from discovery directory
    discovery_dir = os.path.join(DETECT_DIR, "data", "discovery")
    if os.path.exists(discovery_dir):
        print(f"Scanning {discovery_dir} for additional metadata...")
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
            except Exception as e:
                print(f"Warning: could not read {json_file}: {e}")

    return metadata_map

def load_leads():
    """Loads all human leads from multiple validation files and normalizes them."""
    leads = []
    validation_files = [
        os.path.join(DETECT_DIR, "data", "validation_results_v3.json"),
        os.path.join(DETECT_DIR, "data", "validation_terafab_501.json")
    ]
    
    for v_file in validation_files:
        if not os.path.exists(v_file):
            print(f"Skipping missing validation file: {v_file}")
            continue
            
        print(f"Loading AI results from {v_file}...")
        try:
            with open(v_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Identify format and extract results
            results = data.get('results', [])
            for r in results:
                # Normalize label
                label = r.get('label') or r.get('claude_label') or ''
                if label.lower() != 'human':
                    continue
                    
                # Normalize fields
                leads.append({
                    "username": r.get("username"),
                    "label": label,
                    "reason": r.get("reason") or r.get("claude_reason") or "",
                    "confidence": r.get("confidence") or r.get("claude_confidence") or 0,
                    "ml_score": r.get("ml_score", 0.95) # Default high for R1
                })
        except Exception as e:
            print(f"Error loading {v_file}: {e}")
            
    # Deduplicate by username if needed (prefer newer validation)
    final_map = {}
    for l in leads:
        final_map[l["username"].lower()] = l
        
    return list(final_map.values())

def prepare_leads():
    v_humans = load_leads()
    print(f"Found {len(v_humans)} 'human' leads from all AI validation sources.")

    metadata_map = load_all_metadata()
    print(f"Total reference profiles loaded: {len(metadata_map)}")

    # Merge and format for the JS-driven Premium table
    leads_json_data = []
    count_zero_metadata = 0
    
    for r in v_humans:
        u = r['username']
        m = metadata_map.get(u, {})
        
        fl = m.get("followers", 0)
        fg = m.get("following", 0)
        tw = m.get("tweets", 0)
        
        if fl == 0 and fg == 0:
            count_zero_metadata += 1

        leads_json_data.append({
            "u": u,
            "n": m.get("name", u),
            "b": m.get("bio", "").replace("\n", " ").replace('"', "'"),
            "s": r.get("ml_score", 0),
            "fl": fl,
            "fg": fg,
            "tw": tw,
            "img": (m.get("profile_image") or "").replace("_normal", "_bigger"),
            "year": m.get("year", 0),
            "d": m.get("last_tweet_days", 999),
            "reason": r.get("reason", "").replace('"', "'"),
            "conf": r.get("confidence", 0)
        })

    print(f"Total leads prepared: {len(leads_json_data)}")
    print(f"Leads still missing metadata: {count_zero_metadata}")

    # Clean text for JSON safety
    for lead in leads_json_data:
        for key in ['n', 'b', 'reason']:
            if isinstance(lead.get(key), str):
                lead[key] = lead[key].replace('\n', ' ').strip()

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Final Investor Leads (AI Validated)</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0a0a;color:#e0e0e0;padding:12px;line-height:1.5}}
.header{{text-align:center;padding:30px 0;border-bottom:1px solid #222;margin-bottom:20px}}
.header h1{{font-size:1.8rem;color:#fff;margin-bottom:8px;letter-spacing:-0.5px}}
.header .sub{{color:#888;font-size:0.9rem}}
.stats{{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin:20px 0}}
.stat-card{{background:#161616;border:1px solid #2a2a2a;border-radius:12px;padding:15px 25px;text-align:center;min-width:120px;box-shadow:0 4px 6px rgba(0,0,0,0.3)}}
.stat-card .val{{font-size:1.5rem;font-weight:700;color:#4fc3f7;font-variant-numeric:tabular-nums}}
.stat-card .label{{font-size:0.75rem;color:#888;margin-top:4px;text-transform:uppercase;letter-spacing:1px}}
.controls{{display:flex;gap:12px;margin:20px 0;flex-wrap:wrap;align-items:center}}
.search{{flex:1;min-width:250px;padding:12px 16px;border-radius:10px;border:1px solid #333;background:#161616;color:#e0e0e0;font-size:0.95rem;transition:border-color 0.2s}}
.search:focus{{outline:none;border-color:#4fc3f7}}
.sort-btn{{padding:10px 16px;border-radius:8px;border:1px solid #333;background:#1a1a1a;color:#aaa;cursor:pointer;font-size:0.85rem;font-weight:500;transition:all 0.2s}}
.sort-btn:hover,.sort-btn.active{{background:#222;color:#4fc3f7;border-color:#4fc3f7}}
.count{{color:#888;font-size:0.9rem;padding:10px 0}}
.table-wrap{{overflow-x:auto;-webkit-overflow-scrolling:touch;background:#111;border:1px solid #222;border-radius:12px}}
table{{width:100%;border-collapse:collapse;font-size:0.9rem}}
th{{position:sticky;top:0;background:#1a1a1a;color:#888;font-weight:600;padding:12px 10px;text-align:left;border-bottom:2px solid #333;cursor:pointer;white-space:nowrap;font-size:0.75rem;text-transform:uppercase;letter-spacing:1px;z-index:10;transition:color 0.2s}}
th:hover{{color:#4fc3f7}}
th.sorted-asc::after{{content:" \\2191";color:#4fc3f7}}
th.sorted-desc::after{{content:" \\2193";color:#4fc3f7}}
td{{padding:14px 10px;border-bottom:1px solid #1a1a1a;vertical-align:top}}
tr:hover{{background:#161616}}
.user-cell{{display:flex;align-items:center;gap:12px;min-width:200px}}
.avatar{{width:40px;height:40px;border-radius:50%;object-fit:cover;border:2px solid #333;flex-shrink:0}}
.avatar-placeholder{{width:40px;height:40px;border-radius:50%;background:#222;display:flex;align-items:center;justify-content:center;color:#444;font-weight:bold;border:2px solid #333}}
.user-info{{overflow:hidden}}
.user-link{{color:#4fc3f7;text-decoration:none;font-weight:700;font-size:0.95rem;transition:opacity 0.2s}}
.user-link:hover{{opacity:0.8;text-decoration:underline}}
.user-name{{color:#888;font-size:0.8rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:160px}}
.bio-cell{{max-width:200px;color:#9b9b9b;font-size:0.85rem;line-height:1.5}}
.reason-cell{{max-width:300px;color:#888;font-size:0.8rem;font-style:italic;background:rgba(16,185,129,0.05);padding:10px;border-radius:8px;border-left:3px solid #10b981}}
.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;padding-right:15px}}
.score{{font-weight:700;font-size:0.9rem}}
.score-high{{color:#66bb6a}}
.score-med{{color:#ffa726}}
.score-low{{color:#ef5350}}
.active-cell{{white-space:nowrap;font-size:0.85rem;padding:4px 8px;border-radius:4px;background:#1a1a1a}}
.active-recent{{color:#66bb6a}}
.active-moderate{{color:#ffa726}}
.active-old{{color:#ef5350}}
.pagination{{display:flex;gap:8px;justify-content:center;align-items:center;margin:25px 0;flex-wrap:wrap}}
.page-btn{{padding:8px 16px;border-radius:8px;border:1px solid #333;background:#1a1a1a;color:#aaa;cursor:pointer;font-size:0.9rem;transition:all 0.2s}}
.page-btn:hover:not(:disabled){{background:#222;color:#fff;border-color:#4fc3f7}}
.page-btn.active{{background:#4fc3f7;color:#000;border-color:#4fc3f7;font-weight:700}}
.page-btn:disabled{{opacity:0.3;cursor:not-allowed}}
.page-info{{color:#888;font-size:0.85rem;margin:0 10px}}
@media(max-width:1024px){{
  .bio-cell, .hide-tablet {{display:none}}
}}
@media(max-width:768px){{
  .reason-cell, .hide-mobile {{display:none}}
  .user-cell{{min-width:150px}}
  .avatar{{width:32px;height:32px}}
  th,td{{padding:10px 6px}}
}}
</style>
</head>
<body>
<div class="header">
  <h1>Investor Leads AI Dashboard</h1>
  <div class="sub">Human-only results | Filtered for quality | {len(leads_json_data)} leads</div>
</div>

<div class="stats">
  <div class="stat-card"><div class="val">{len(leads_json_data)}</div><div class="label">Total Leads</div></div>
  <div class="stat-card"><div class="val">{sum(l['fl'] for l in leads_json_data)//len(leads_json_data) if leads_json_data else 0}</div><div class="label">Avg Followers</div></div>
</div>

<div class="controls">
  <input type="text" class="search" id="search" placeholder="Search name, handle, bio, or reason...">
  <button class="sort-btn active" id="btn-fl" onclick="setSort('fl','desc')">Most Followers</button>
  <button class="sort-btn" id="btn-s" onclick="setSort('s','desc')">High Score</button>
  <button class="sort-btn" onclick="setSort('d','asc')">Most Recent</button>
</div>

<div class="count" id="count"></div>

<div class="table-wrap">
<table>
<thead>
<tr>
  <th data-col="u">User</th>
  <th data-col="b" class="hide-tablet">Bio</th>
  <th data-col="reason" class="hide-mobile">AI Reasoning</th>
  <th data-col="fl" class="num">Followers</th>
  <th data-col="fg" class="num hide-mobile">Following</th>
  <th data-col="tw" class="num hide-mobile">Tweets</th>
  <th data-col="year" class="num hide-mobile">Since</th>
  <th data-col="d" class="num">Active</th>
  <th data-col="s" class="num">Score</th>
</tr>
</thead>
<tbody id="tbody"></tbody>
</table>
</div>

<div class="pagination" id="pagination"></div>

<script>
const DATA = {json.dumps(leads_json_data)};
const PER_PAGE = 50;
let filtered = [...DATA];
let page = 1;
let sortCol = 'fl', sortDir = 'desc';

const $ = id => document.getElementById(id);
const tbody = $('tbody');
const search = $('search');

function scoreClass(s) {{ return s > 0.8 ? 'score-high' : s > 0.5 ? 'score-med' : 'score-low'; }}
function activeClass(d) {{ return d <= 14 ? 'active-recent' : d <= 60 ? 'active-moderate' : 'active-old'; }}
function activeText(d) {{ return d <= 0 ? 'Today' : d === 1 ? '1d ago' : d < 30 ? d + 'd ago' : d < 60 ? Math.floor(d / 7) + 'w ago' : d >= 999 ? 'Unknown' : Math.floor(d / 30) + 'mo ago'; }}
function esc(s) {{ if (!s) return ''; const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }}

function render() {{
    const start = (page - 1) * PER_PAGE;
    const slice = filtered.slice(start, start + PER_PAGE);
    let h = '';
    
    slice.forEach(p => {{
        const imgHtml = p.img ? `<img class="avatar" src="${{esc(p.img)}}" alt="" loading="lazy" onerror="this.outerHTML='<div class=avatar-placeholder>?</div>'">` : '<div class="avatar-placeholder">?</div>';
        
        h += `<tr>
            <td><div class="user-cell">${{imgHtml}}<div class="user-info"><a class="user-link" href="https://x.com/${{esc(p.u)}}" target="_blank" rel="noopener">@${{esc(p.u)}}</a><div class="user-name">${{esc(p.n)}}</div></div></div></td>
            <td class="bio-cell hide-tablet">${{esc(p.b)}}</td>
            <td class="reason-cell hide-mobile">${{esc(p.reason)}}</td>
            <td class="num">${{(p.fl || 0).toLocaleString()}}</td>
            <td class="num hide-mobile">${{(p.fg || 0).toLocaleString()}}</td>
            <td class="num hide-mobile">${{(p.tw || 0).toLocaleString()}}</td>
            <td class="num hide-mobile">${{p.year || '-'}}</td>
            <td class="num"><span class="active-cell ${{activeClass(p.d)}}">${{activeText(p.d)}}</span></td>
            <td class="num"><span class="score ${{scoreClass(p.s)}}">${{(p.s || 0).toFixed(2)}}</span></td>
        </tr>`;
    }});
    
    tbody.innerHTML = h;
    $('count').textContent = `Showing ${{filtered.length > 0 ? start + 1 : 0}}-${{Math.min(start + PER_PAGE, filtered.length)}} of ${{filtered.length.toLocaleString()}} leads`;
    renderPagination();
}}

function renderPagination() {{
    const totalPages = Math.ceil(filtered.length / PER_PAGE);
    const container = $('pagination');
    container.innerHTML = '';
    if (totalPages <= 1) return;

    let h = `<button class="page-btn" onclick="goPage(1)" ${{page === 1 ? 'disabled' : ''}}>First</button>`;
    h += `<button class="page-btn" onclick="goPage(${{page - 1}})" ${{page === 1 ? 'disabled' : ''}}>Prev</button>`;
    
    const start = Math.max(1, page - 2), end = Math.min(totalPages, page + 2);
    for (let i = start; i <= end; i++) {{
        h += `<button class="page-btn ${{i === page ? 'active' : ''}}" onclick="goPage(${{i}})">${{i}}</button>`;
    }}
    
    h += `<button class="page-btn" onclick="goPage(${{page + 1}})" ${{page === totalPages ? 'disabled' : ''}}>Next</button>`;
    h += `<button class="page-btn" onclick="goPage(${{totalPages}})" ${{page === totalPages ? 'disabled' : ''}}>Last</button>`;
    
    const info = document.createElement('span');
    info.className = 'page-info';
    info.textContent = `Page ${{page}}/${{totalPages}}`;
    
    container.innerHTML = h;
    container.appendChild(info);
}}

function goPage(p) {{ page = p; render(); window.scrollTo({{top: 0, behavior: 'smooth'}}); }}

function applySort() {{
    filtered.sort((a, b) => {{
        let va = a[sortCol], vb = b[sortCol];
        if (typeof va === 'string') va = va.toLowerCase();
        if (typeof vb === 'string') vb = vb.toLowerCase();
        if (va < vb) return sortDir === 'asc' ? -1 : 1;
        if (va > vb) return sortDir === 'asc' ? 1 : -1;
        return 0;
    }});
    
    document.querySelectorAll('th').forEach(th => {{
        th.classList.remove('sorted-asc', 'sorted-desc');
        if (th.dataset.col === sortCol) {{
            th.classList.add(sortDir === 'asc' ? 'sorted-asc' : 'sorted-desc');
        }}
    }});
}}

function setSort(col, dir) {{
    sortCol = col; sortDir = dir;
    applySort(); page = 1; render();
    document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
    if (col === 'fl') $('btn-fl').classList.add('active');
    if (col === 's') $('btn-s').classList.add('active');
}}

document.querySelectorAll('th').forEach(th => {{
    th.addEventListener('click', () => {{
        const col = th.dataset.col;
        if (sortCol === col) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
        else {{ sortCol = col; sortDir = 'desc'; }}
        applySort(); page = 1; render();
    }});
}});

search.addEventListener('input', () => {{
    const q = search.value.toLowerCase().trim();
    filtered = q ? DATA.filter(p => (p.u + ' ' + p.n + ' ' + p.b + ' ' + p.reason).toLowerCase().includes(q)) : [...DATA];
    applySort(); page = 1; render();
}});

applySort(); render();
</script>
</body>
</html>
"""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Successfully generated PREMIUM report: {OUTPUT_FILE}")

if __name__ == "__main__":
    prepare_leads()
