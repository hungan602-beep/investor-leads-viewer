import json
import os
import glob
from datetime import datetime

# Paths
DETECT_DIR = r"C:\Users\Administrator\Desktop\X\detect"
V3_RESULTS_FILE = os.path.join(DETECT_DIR, "data", "validation_results_v3.json")
OUTPUT_FILE = os.path.join(DETECT_DIR, "final_leads_v3.html")

def load_all_metadata():
    """Builds a comprehensive username -> profile map by scanning all data sources."""
    metadata_map = {}
    
    # 1. Start with fetched_profiles.json
    base_profiles = os.path.join(DETECT_DIR, "data", "fetched_profiles.json")
    if os.path.exists(base_profiles):
        print(f"Loading base profiles from {base_profiles}...")
        try:
            with open(base_profiles, 'r', encoding='utf-8') as f:
                profiles = json.load(f)
                for p in profiles:
                    metadata_map[p['username']] = p
        except Exception as e:
            print(f"Error loading {base_profiles}: {e}")

    # 2. Add profiles from harvest directory (where many missing leads like TKS8798 are located)
    harvest_dir = os.path.join(DETECT_DIR, "data", "harvest")
    if os.path.exists(harvest_dir):
        print(f"Scanning {harvest_dir} for additional metadata...")
        for json_file in glob.glob(os.path.join(harvest_dir, "*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle both list formats and object formats with 'users' key
                    users = data if isinstance(data, list) else data.get('users', [])
                    for p in users:
                        if isinstance(p, dict) and 'username' in p:
                            # Prefer richer data if we already have a skeleton
                            if p['username'] not in metadata_map or p.get('followers_count', 0) > 0:
                                metadata_map[p['username']] = p
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
                    users = data if isinstance(data, list) else data.get('users', [])
                    for p in users:
                        if isinstance(p, dict) and 'username' in p:
                            if p['username'] not in metadata_map or p.get('followers_count', 0) > 0:
                                metadata_map[p['username']] = p
            except Exception as e:
                print(f"Warning: could not read {json_file}: {e}")

    return metadata_map

def prepare_leads():
    print(f"Loading AI results from {V3_RESULTS_FILE}...")
    if not os.path.exists(V3_RESULTS_FILE):
        print(f"CRITICAL: {V3_RESULTS_FILE} not found.")
        return

    with open(V3_RESULTS_FILE, 'r', encoding='utf-8') as f:
        v3_data = json.load(f)
    
    all_results = v3_data.get('results', [])
    v3_humans = [r for r in all_results if r.get('claude_label', '').lower() == 'human']
    print(f"Found {len(v3_humans)} 'human' leads from AI validation.")

    metadata_map = load_all_metadata()
    print(f"Total reference profiles loaded: {len(metadata_map)}")

    # Merge and format for the JS-driven Premium table
    leads_json_data = []
    count_zero_metadata = 0
    
    for r in v3_humans:
        u = r['username']
        m = metadata_map.get(u, {})
        
        fl = m.get("followers_count", 0)
        fg = m.get("following_count", 0)
        tw = m.get("tweet_count", 0)
        
        if fl == 0 and fg == 0:
            count_zero_metadata += 1

        leads_json_data.append({
            "u": u,
            "n": m.get("name", u),
            "b": m.get("description", "").replace("\n", " ").replace('"', "'"),
            "s": r.get("ml_score", 0),
            "fl": fl,
            "fg": fg,
            "tw": tw,
            "img": m.get("profile_image_url", "").replace("_normal", "_bigger"),
            "reason": r.get("claude_reason", "").replace('"', "'"),
            "conf": r.get("claude_confidence", 0)
        })

    print(f"Total leads prepared: {len(leads_json_data)}")
    print(f"Leads still missing metadata: {count_zero_metadata}")

    # Clean text for JSON safety
    for lead in leads_json_data:
        for key in ['n', 'b', 'reason']:
            if isinstance(lead.get(key), str):
                # Remove newlines that can break some parsers, even if JSON escaped
                lead[key] = lead[key].replace('\n', ' ').strip()

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Final Investor Leads (DeepSeek-V3 Validated)</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0a0a;color:#e0e0e0;padding:12px}}
.header{{text-align:center;padding:20px 0;border-bottom:1px solid #222}}
.header h1{{font-size:1.5rem;color:#fff;margin-bottom:4px}}
.header .sub{{color:#888;font-size:0.85rem}}
.stats{{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin:16px 0}}
.stat-card{{background:#161616;border:1px solid #2a2a2a;border-radius:8px;padding:12px 18px;text-align:center;min-width:100px}}
.stat-card .val{{font-size:1.3rem;font-weight:700;color:#4fc3f7}}
.stat-card .label{{font-size:0.7rem;color:#888;margin-top:2px}}
.controls{{display:flex;gap:10px;margin:16px 0;flex-wrap:wrap;align-items:center}}
.search{{flex:1;min-width:200px;padding:10px 14px;border-radius:8px;border:1px solid #333;background:#161616;color:#e0e0e0;font-size:0.9rem}}
.search:focus{{outline:none;border-color:#4fc3f7}}
.sort-btn{{padding:8px 14px;border-radius:6px;border:1px solid #333;background:#1a1a1a;color:#aaa;cursor:pointer;font-size:0.8rem;white-space:nowrap}}
.sort-btn:hover,.sort-btn.active{{background:#222;color:#4fc3f7;border-color:#4fc3f7}}
.count{{color:#888;font-size:0.85rem;padding:8px 0}}
.table-wrap{{overflow-x:auto;-webkit-overflow-scrolling:touch}}
table{{width:100%;border-collapse:collapse;font-size:0.85rem}}
th{{position:sticky;top:0;background:#111;color:#888;font-weight:600;padding:10px 8px;text-align:left;border-bottom:2px solid #333;cursor:pointer;white-space:nowrap;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.5px;z-index:10}}
th:hover{{color:#4fc3f7}}
th.sorted-asc::after{{content:" \\2191";color:#4fc3f7}}
th.sorted-desc::after{{content:" \\2193";color:#4fc3f7}}
td{{padding:12px 8px;border-bottom:1px solid #1a1a1a;vertical-align:top}}
tr:hover{{background:#161616}}
.user-cell{{display:flex;align-items:center;gap:8px;min-width:180px}}
.avatar{{width:32px;height:32px;border-radius:50%;object-fit:cover;border:1px solid #333;flex-shrink:0}}
.user-info{{overflow:hidden}}
.user-link{{color:#4fc3f7;text-decoration:none;font-weight:600;font-size:0.85rem}}
.user-link:hover{{text-decoration:underline}}
.user-name{{color:#888;font-size:0.75rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:150px}}
.bio-cell{{max-width:250px;color:#999;font-size:0.8rem;line-height:1.4}}
.reason-cell{{max-width:350px;color:#888;font-size:0.75rem;font-style:italic;background:#111;padding:8px;border-radius:4px;border-left:2px solid #10b981}}
.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
.score{{font-weight:700;font-size:0.85rem;color:#4fc3f7}}
.pagination{{display:flex;gap:6px;justify-content:center;align-items:center;margin:16px 0;flex-wrap:wrap}}
.page-btn{{padding:6px 12px;border-radius:6px;border:1px solid #333;background:#1a1a1a;color:#aaa;cursor:pointer;font-size:0.85rem}}
.page-btn:hover{{background:#222;color:#fff}}
.page-btn.active{{background:#4fc3f7;color:#000;border-color:#4fc3f7;font-weight:700}}
.page-btn:disabled{{opacity:0.3;cursor:not-allowed}}
.page-info{{color:#888;font-size:0.8rem}}
@media(max-width:768px){{
  .bio-cell, .reason-cell, .hide-mobile {{display:none}}
}}
</style>
</head>
<body>
<div class="header">
  <h1>Final DeepSeek-V3 Validated Leads</h1>
  <div class="sub">Human-only results | Filtered for quality | {len(leads_json_data)} leads</div>
</div>

<div class="stats">
  <div class="stat-card"><div class="val">{len(leads_json_data)}</div><div class="label">Total Humans</div></div>
  <div class="stat-card"><div class="val">{sum(l['fl'] for l in leads_json_data)//len(leads_json_data) if leads_json_data else 0}</div><div class="label">Avg Followers</div></div>
</div>

<div class="controls">
  <input type="text" class="search" id="search" placeholder="Search name, handle, bio, or reason...">
  <button class="sort-btn active" id="btn-fl" onclick="setSort('fl','desc')">Most Followers</button>
  <button class="sort-btn" id="btn-s" onclick="setSort('s','desc')">High ML Score</button>
</div>

<div class="count" id="count"></div>

<div class="table-wrap">
<table>
<thead>
<tr>
  <th data-col="u" onclick="toggleSort('u')">User</th>
  <th data-col="b">Bio</th>
  <th data-col="reason">AI Reasoning</th>
  <th data-col="fl" class="num" onclick="toggleSort('fl')">Followers</th>
  <th data-col="fg" class="num" onclick="toggleSort('fg')">Following</th>
  <th data-col="s" class="num" onclick="toggleSort('s')">Score</th>
</tr>
</thead>
<tbody id="tbody"></tbody>
</table>
</div>
<div class="pagination" id="pagination"></div>

<script id="leads-data" type="application/json">
{json.dumps(leads_json_data)}
</script>

<script>
const DATA = JSON.parse(document.getElementById('leads-data').textContent);
let currentData = [...DATA];
let pageSize = 50;
let currentPage = 1;
let sortBy = 'fl';
let sortDir = 'desc';

function render() {{
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    const pageData = currentData.slice(start, end);
    
    document.getElementById('tbody').innerHTML = pageData.map(l => 
        '<tr>' +
            '<td>' +
                '<div class="user-cell">' +
                    '<img class="avatar" src="' + l.img + '" onerror="this.onerror=null; this.src=\'https://abs.twimg.com/sticky/default_profile_images/default_profile_bigger.png\'">' +
                    '<div class="user-info">' +
                        '<a href="https://x.com/' + l.u + '" target="_blank" class="user-link">@' + l.u + '</a>' +
                        '<div class="user-name">' + l.n + '</div>' +
                    '</div>' +
                '</div>' +
            '</td>' +
            '<td><div class="bio-cell">' + (l.b || '') + '</div></td>' +
            '<td><div class="reason-cell">' + (l.reason || '') + '</div></td>' +
            '<td class="num">' + l.fl.toLocaleString() + '</td>' +
            '<td class="num">' + l.fg.toLocaleString() + '</td>' +
            '<td class="num"><span class="score">' + l.s.toFixed(2) + '</span></td>' +
        '</tr>'
    ).join('');
    
    renderPagination();
    const startNum = currentData.length > 0 ? start + 1 : 0;
    const endNum = Math.min(end, currentData.length);
    document.getElementById('count').innerText = 'Showing ' + startNum + '-' + endNum + ' of ' + currentData.length + ' leads';
}}

function renderPagination() {{
    const totalPages = Math.ceil(currentData.length / pageSize);
    let html = '';
    for(let i=1; i<=totalPages; i++) {{
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {{
            const activeClass = i === currentPage ? 'active' : '';
            html += '<button class="page-btn ' + activeClass + '" onclick="setPage(' + i + ')">' + i + '</button>';
        }} else if (i === currentPage - 3 || i === currentPage + 3) {{
            html += '<span style="color:#444">...</span>';
        }}
    }}
    html += '<span class="page-info">Page ' + currentPage + '/' + totalPages + '</span>';
    document.getElementById('pagination').innerHTML = html;
}}

function setPage(p) {{ currentPage = p; render(); window.scrollTo(0,0); }}

function toggleSort(col) {{
    if (sortBy === col) {{
        sortDir = sortDir === 'asc' ? 'desc' : 'asc';
    }} else {{
        sortBy = col;
        sortDir = 'desc';
    }}
    applySort();
}}

function setSort(col, dir) {{
    sortBy = col;
    sortDir = dir;
    
    document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
    if (col === 'fl') document.getElementById('btn-fl').classList.add('active');
    if (col === 's') document.getElementById('btn-s').classList.add('active');
    
    applySort();
}}

function applySort() {{
    currentData.sort((a,b) => {{
        let v1 = a[sortBy], v2 = b[sortBy];
        if (typeof v1 === 'string') v1 = v1.toLowerCase();
        if (typeof v2 === 'string') v2 = v2.toLowerCase();
        if (v1 < v2) return sortDir === 'asc' ? -1 : 1;
        if (v1 > v2) return sortDir === 'asc' ? 1 : -1;
        return 0;
    }});
    
    document.querySelectorAll('th').forEach(th => {{
        th.classList.remove('sorted-asc', 'sorted-desc');
        if (th.dataset.col === sortBy) {{
            th.classList.add(sortDir === 'asc' ? 'sorted-asc' : 'sorted-desc');
        }}
    }});
    
    currentPage = 1;
    render();
}}

document.getElementById('search').oninput = (e) => {{
    const term = e.target.value.toLowerCase();
    currentData = DATA.filter(l => 
        l.u.toLowerCase().includes(term) || 
        l.n.toLowerCase().includes(term) || 
        l.b.toLowerCase().includes(term) || 
        l.reason.toLowerCase().includes(term)
    );
    currentPage = 1;
    render();
}};

applySort();
</script>
</body>
</html>
"""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Successfully generated PREMIUM report: {OUTPUT_FILE}")

if __name__ == "__main__":
    prepare_leads()
