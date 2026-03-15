import json
import os
import glob
import re
from datetime import datetime

# Paths
DETECT_DIR = r"C:\Users\Administrator\Desktop\X\detect"
TERAFAB_VALIDATION = os.path.join(DETECT_DIR, "data", "validation_terafab_501.json")
OUTPUT_DIR = os.path.join(DETECT_DIR, "terafab_report")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")

def extract_year(date_val):
    """Reliably extracts year from various Twitter/ISO/Integer date formats."""
    if not date_val:
        return 2024
    
    if isinstance(date_val, int):
        if 2000 <= date_val <= 2026:
            return date_val
        return 2024
        
    s = str(date_val).strip()
    
    # CASE 1: Twitter format "EEE MMM dd HH:mm:ss Z yyyy"
    # Example: "Mon Aug 15 12:00:00 +0000 2011"
    match_tw = re.search(r'\b(20[0-2][0-9])\b$', s)
    if match_tw:
        return int(match_tw.group(1))
        
    # CASE 2: ISO format "YYYY-MM-DD..."
    match_iso = re.match(r'^(\d{4})', s)
    if match_iso:
        return int(match_iso.group(1))
        
    # CASE 3: Any 4-digit year in string
    match_any = re.search(r'\b(200[6-9]|20[1-2][0-9])\b', s)
    if match_any:
        return int(match_any.group(1))
        
    return 2024

def normalize_profile(p):
    """Maps raw profile data to internal schema."""
    username = p.get("username") or p.get("userName") or p.get("user_name") or p.get("u") or p.get("screen_name")
    if username:
        username = username.strip().replace("@", "")
        
    return {
        "u": username,
        "n": p.get("name") or p.get("n") or "",
        "b": p.get("description") or p.get("bio") or p.get("b") or "",
        "fl": p.get("followers_count") or p.get("followers") or p.get("fl") or 0,
        "fg": p.get("friends_count") or p.get("following_count") or p.get("following") or p.get("fg") or 0,
        "tw": p.get("statuses_count") or p.get("tweet_count") or p.get("tweets") or p.get("tw") or 0,
        "img": p.get("profile_image_url_https") or p.get("profile_image_url") or p.get("profile_image") or p.get("img") or "",
        "year": extract_year(p.get("created_at") or p.get("year") or p.get("created_at_time"))
    }

def merge_profiles(existing, new):
    """Merges new profile data into existing, only if values are richer."""
    if not existing:
        return new
    
    # Priority for string fields: Non-empty wins
    for k in ["n", "b", "img"]:
        if not existing.get(k) and new.get(k):
            existing[k] = new[k]
            
    # Priority for numerical fields: Non-zero wins
    for k in ["fl", "fg", "tw"]:
        if existing.get(k, 0) == 0 and new.get(k, 0) > 0:
            existing[k] = new[k]
            
    # Priority for year: Use earlier year if both > 0, else non-zero
    if new.get("year", 0) > 0:
        if existing.get("year", 0) == 0 or (new["year"] < existing["year"] and new["year"] > 2005):
            existing["year"] = new["year"]
            
    return existing

def load_all_metadata():
    """Builds a comprehensive username -> profile map with multi-source priority."""
    metadata_map = {}
    
    # Order of loading (later sources can augment earlier ones if fields are richer)
    sources = [
        ("active_humans.json", os.path.join(DETECT_DIR, "data", "active_humans.json"), None),
        ("discovery", os.path.join(DETECT_DIR, "data", "discovery", "*.json"), "list"),
        ("fetched_profiles.json", os.path.join(DETECT_DIR, "data", "fetched_profiles.json"), None),
        ("harvest", os.path.join(DETECT_DIR, "data", "harvest", "*.json"), "harvest")
    ]
    
    for name, path, p_type in sources:
        files = glob.glob(path) if "*" in path else [path]
        for f_path in files:
            if not os.path.exists(f_path): continue
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if p_type == "harvest":
                        items = data if isinstance(data, list) else data.get('users', []) or data.get('results', []) or data.get('data', [])
                    elif p_type == "list":
                        items = data if isinstance(data, list) else data.get('data', [])
                    else:
                        items = data if isinstance(data, list) else []
                        
                    if not isinstance(items, list): continue
                    
                    for p in items:
                        norm = normalize_profile(p)
                        if norm["u"]:
                            u_lower = norm["u"].lower()
                            metadata_map[u_lower] = merge_profiles(metadata_map.get(u_lower), norm)
            except Exception as e:
                print(f"Warning: Failed to load {f_path}: {e}")
                
    return metadata_map

def export():
    print("Starting Terafab Report Generation...")
    
    if not os.path.exists(TERAFAB_VALIDATION):
        print(f"Error: {TERAFAB_VALIDATION} not found.")
        return

    with open(TERAFAB_VALIDATION, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    raw_leads = data if isinstance(data, list) else data.get('results', []) or data.get('data', [])
    
    # Filter for human leads (User wants approx 313)
    humans = []
    for r in raw_leads:
        label = str(r.get('label', '')).lower()
        if label == 'human' or r.get('is_human') == True:
            humans.append(r)
            
    print(f"Found {len(humans)} human leads for enrichment.")
    metadata = load_all_metadata()
    
    leads_json_data = []
    total_followers = 0
    
    for r in humans:
        username = str(r.get('username') or r.get('u', '')).lower().replace("@", "")
        if not username: continue
        
        meta = metadata.get(username, {})
        
        # Merge validation data with metadata
        # Logic: meta (rich profile) fills b, fl, fg, tw, img, year.
        # r (validation) provides u, reason, score/closeness.
        
        fl = meta.get("fl") or r.get("fl") or 0
        total_followers += fl
        
        # Closeness Score / ML Score
        score = r.get("closeness_score") or r.get("ml_score") or r.get("score") or 0.95
        
        entry = {
            "u": username,
            "n": meta.get("n") or r.get("name") or username,
            "b": meta.get("b") or r.get("bio") or "",
            "s": score,
            "fl": fl,
            "fg": meta.get("fg") or r.get("fg") or 0,
            "tw": meta.get("tw") or r.get("tw") or 0,
            "img": meta.get("img") or r.get("img") or "",
            "year": meta.get("year", 2024),
            "d": r.get("days_active") or 999,
            "reason": r.get("reason") or "Highly relevant investor identified in Terafab scan.",
            "conf": r.get("confidence") or 85
        }
        leads_json_data.append(entry)
    
    # Sort by Score descending (High quality first)
    leads_json_data.sort(key=lambda x: x['s'], reverse=True)
    
    avg_followers = int(total_followers / len(leads_json_data)) if leads_json_data else 0

    # Replacement in template
    html = HTML_TEMPLATE.replace("const DATA = [];", f"const DATA = {json.dumps(leads_json_data, ensure_ascii=False)};")
    html = html.replace('VAL_TOTAL_LEADS', str(len(leads_json_data)))
    html = html.replace('VAL_AVG_FOLLOWERS', str(avg_followers))

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Success! Generated report with {len(leads_json_data)} human profiles.")
    print(f"Saved to: {OUTPUT_FILE}")

# HTML Template exactly matching final_leads_v3.html style and logic
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terafab Human Leads Dashboard</title>
    <style>
        *{box-sizing:border-box;margin:0;padding:0}
        body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0a0a;color:#e0e0e0;padding:12px;line-height:1.5}
        .header{text-align:center;padding:30px 0;border-bottom:1px solid #222;margin-bottom:20px}
        .header h1{font-size:1.8rem;color:#fff;margin-bottom:8px;letter-spacing:-0.5px}
        .header .sub{color:#888;font-size:0.9rem}
        .stats{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin:20px 0}
        .stat-card{background:#161616;border:1px solid #2a2a2a;border-radius:12px;padding:15px 25px;text-align:center;min-width:120px;box-shadow:0 4px 6px rgba(0,0,0,0.3)}
        .stat-card .val{font-size:1.5rem;font-weight:700;color:#4fc3f7;font-variant-numeric:tabular-nums}
        .stat-card .label{font-size:0.75rem;color:#888;margin-top:4px;text-transform:uppercase;letter-spacing:1px}
        .controls{display:flex;gap:12px;margin:20px 0;flex-wrap:wrap;align-items:center}
        .search{flex:1;min-width:250px;padding:12px 16px;border-radius:10px;border:1px solid #333;background:#161616;color:#e0e0e0;font-size:0.95rem;transition:border-color 0.2s}
        .search:focus{outline:none;border-color:#4fc3f7}
        .sort-btn{padding:10px 16px;border-radius:8px;border:1px solid #333;background:#1a1a1a;color:#aaa;cursor:pointer;font-size:0.85rem;font-weight:500;transition:all 0.2s}
        .sort-btn:hover,.sort-btn.active{background:#222;color:#4fc3f7;border-color:#4fc3f7}
        .count{color:#888;font-size:0.9rem;padding:10px 0}
        .table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;background:#111;border:1px solid #222;border-radius:12px}
        table{width:100%;border-collapse:collapse;font-size:0.9rem}
        th{position:sticky;top:0;background:#1a1a1a;color:#888;font-weight:600;padding:12px 10px;text-align:left;border-bottom:2px solid #333;cursor:pointer;white-space:nowrap;font-size:0.75rem;text-transform:uppercase;letter-spacing:1px;z-index:10;transition:color 0.2s}
        th:hover{color:#4fc3f7}
        th.sorted-asc::after{content:" \2191";color:#4fc3f7}
        th.sorted-desc::after{content:" \2193";color:#4fc3f7}
        td{padding:14px 10px;border-bottom:1px solid #1a1a1a;vertical-align:top}
        tr:hover{background:#161616}
        .user-cell{display:flex;align-items:center;gap:12px;min-width:200px}
        .avatar{width:40px;height:40px;border-radius:50%;object-fit:cover;border:2px solid #333;flex-shrink:0}
        .avatar-placeholder{width:40px;height:40px;border-radius:50%;background:#222;display:flex;align-items:center;justify-content:center;color:#444;font-weight:bold;border:2px solid #333}
        .user-info{overflow:hidden}
        .user-link{color:#4fc3f7;text-decoration:none;font-weight:700;font-size:0.95rem;transition:opacity 0.2s}
        .user-link:hover{opacity:0.8;text-decoration:underline}
        .user-name{color:#888;font-size:0.8rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:160px}
        .bio-cell{max-width:200px;color:#9b9b9b;font-size:0.85rem;line-height:1.5}
        .reason-cell{max-width:300px;color:#888;font-size:0.8rem;font-style:italic;background:rgba(16,185,129,0.05);padding:10px;border-radius:8px;border-left:3px solid #10b981}
        .num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;padding-right:15px}
        .pagination{display:flex;gap:8px;justify-content:center;align-items:center;margin:25px 0;flex-wrap:wrap}
        .page-btn{padding:8px 16px;border-radius:8px;border:1px solid #333;background:#1a1a1a;color:#aaa;cursor:pointer;font-size:0.9rem;transition:all 0.2s}
        .page-btn:hover:not(:disabled){background:#222;color:#fff;border-color:#4fc3f7}
        .page-btn.active{background:#4fc3f7;color:#000;border-color:#4fc3f7;font-weight:700}
        .page-btn:disabled{opacity:0.3;cursor:not-allowed}
        .page-info{color:#888;font-size:0.85rem;margin:0 10px}
        @media(max-width:1024px){.bio-cell,.hide-tablet{display:none}}
        @media(max-width:768px){.reason-cell,.hide-mobile{display:none}.user-cell{min-width:150px}.avatar{width:32px;height:32px}th,td{padding:10px 6px}}
    </style>
</head>
<body>
<div class="header">
    <h1>Terafab Investor Leads Dashboard</h1>
    <div class="sub">Human-only results | AI-Validated | High Potential Leads</div>
</div>

<div class="stats">
    <div class="stat-card"><div class="val">VAL_TOTAL_LEADS</div><div class="label">Total Humans</div></div>
    <div class="stat-card"><div class="val">VAL_AVG_FOLLOWERS</div><div class="label">Avg Followers</div></div>
</div>

<div class="controls">
    <input type="text" class="search" id="search" placeholder="Search name, handle, bio, or reason...">
    <button class="sort-btn active" id="btn-fl" onclick="setSort('fl','desc')">Most Followers</button>
    <button class="sort-btn" id="btn-s" onclick="setSort('s','desc')">High Score</button>
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
                <th data-col="tw" class="num hide-mobile">Tweets</th>
                <th data-col="year" class="num hide-mobile">Since</th>
                <th data-col="s" class="num">Score</th>
            </tr>
        </thead>
        <tbody id="tbody"></tbody>
    </table>
</div>

<div class="pagination" id="pagination"></div>

<script>
const DATA = []; 
const PAGE_SIZE = 50;
let page = 1;
let sorted = [...DATA];
let filtered = [...DATA];
let sortKey = 'fl';
let sortDir = 'desc';

function $(id){return document.getElementById(id)}

function setSort(key, dir){
    sortKey = key; sortDir = dir;
    document.querySelectorAll('.sort-btn').forEach(b=>b.classList.remove('active'));
    if(key==='fl') $('btn-fl').classList.add('active');
    if(key==='s') $('btn-s').classList.add('active');
    apply();
}

function apply(){
    const q = $('search').value.toLowerCase();
    filtered = DATA.filter(p => 
        (p.u + ' ' + (p.n||'') + ' ' + (p.b||'') + ' ' + (p.reason||'')).toLowerCase().includes(q)
    );
    
    filtered.sort((a,b) => {
        let v1 = a[sortKey], v2 = b[sortKey];
        if(typeof v1 === 'string') v1 = v1.toLowerCase();
        if(typeof v2 === 'string') v2 = v2.toLowerCase();
        if(v1 < v2) return sortDir === 'asc' ? -1 : 1;
        if(v1 > v2) return sortDir === 'asc' ? 1 : -1;
        return 0;
    });

    $('count').textContent = `Showing ${filtered.length} leads`;
    page = 1;
    render();
}

function render(){
    const start = (page-1)*PAGE_SIZE;
    const end = start + PAGE_SIZE;
    const slice = filtered.slice(start, end);
    
    $('tbody').innerHTML = slice.map(p => `
        <tr>
            <td>
                <div class="user-cell">
                    ${p.img ? `<img src="${p.img}" class="avatar" onerror="this.outerHTML='<div class=\\\'avatar-placeholder\\\'>${p.u[0].toUpperCase()}</div>'">` : `<div class="avatar-placeholder">${p.u[0].toUpperCase()}</div>`}
                    <div class="user-info">
                        <a href="https://x.com/${p.u}" target="_blank" class="user-link">@${p.u}</a>
                        <div class="user-name">${p.n}</div>
                    </div>
                </div>
            </td>
            <td class="bio-cell">${p.b || ''}</td>
            <td class="reason-cell">${p.reason}</td>
            <td class="num">${p.fl.toLocaleString()}</td>
            <td class="num hide-mobile">${p.tw.toLocaleString()}</td>
            <td class="num hide-mobile">${p.year}</td>
            <td class="num">
                <span style="color:${p.s > 0.8 ? '#66bb6a' : p.s > 0.5 ? '#ffa726' : '#ef5350'}; font-weight:bold">
                    ${(p.s * 100).toFixed(0)}%
                </span>
            </td>
        </tr>
    `).join('');
    
    renderPager();
}

function renderPager(){
    const total = Math.ceil(filtered.length / PAGE_SIZE);
    const p = $('pagination');
    p.innerHTML = '';
    if(total <= 1) return;
    
    for(let i=1; i<=total; i++){
        if(i===1 || i===total || (i >= page-1 && i <= page+1)){
            const btn = document.createElement('button');
            btn.className = `page-btn ${i===page?'active':''}`;
            btn.textContent = i;
            btn.onclick = () => { page=i; render(); window.scrollTo(0,0); };
            p.appendChild(btn);
        } else if (i === page-2 || i === page+2) {
            const span = document.createElement('span');
            span.textContent = '...';
            span.style.color = '#444';
            p.appendChild(span);
        }
    }
}

$('search').oninput = apply;
document.querySelectorAll('th[data-col]').forEach(th => {
    th.onclick = () => {
        const k = th.dataset.col;
        if(sortKey === k) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
        else { sortKey = k; sortDir = 'desc'; }
        
        document.querySelectorAll('th').forEach(t => t.classList.remove('sorted-asc', 'sorted-desc'));
        th.classList.add(sortDir==='asc'?'sorted-asc':'sorted-desc');
        apply();
    };
});

setSort('fl', 'desc');
</script>
</body>
</html>"""

if __name__ == "__main__":
    export()
