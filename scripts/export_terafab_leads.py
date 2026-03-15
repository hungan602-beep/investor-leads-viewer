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
    \"\"\"Builds a comprehensive username -> profile map.\"\"\"
    metadata_map = {}
    
    def normalize_profile(p):
        norm = {
            "username": p.get("username") or p.get("userName") or p.get("user_name"),
            "name": p.get("name", ""),
            "bio": p.get("bio") or p.get("description", ""),
            "followers": p.get("followers_count") or p.get("followers") or 0,
            "following": p.get("friends_count") or p.get("following") or 0,
            "tweets": p.get("statuses_count") or p.get("tweets") or 0,
            "profile_image": p.get("profile_image_url_https") or p.get("profile_image") or "",
            "created_at": p.get("created_at") or ""
        }
        
        # Year extraction
        try:
            if norm["created_at"]:
                if isinstance(norm["created_at"], str):
                    if " " in norm["created_at"]:
                        norm["year"] = norm["created_at"].split()[-1]
                    else:
                        norm["year"] = norm["created_at"][:4]
                else:
                    norm["year"] = str(norm["created_at"])[:4]
        except:
            norm["year"] = "2024"
            
        return norm

    # 1. Load from fetched_profiles.json
    profiles_path = os.path.join(DETECT_DIR, "data", "fetched_profiles.json")
    if os.path.exists(profiles_path):
        try:
            with open(profiles_path, 'r', encoding='utf-8') as f:
                p_data = json.load(f)
                for p in p_data:
                    norm = normalize_profile(p)
                    if norm["username"]:
                        metadata_map[norm["username"].lower()] = norm
        except: pass

    # 2. Load from discovery/*.json
    discovery_files = glob.glob(os.path.join(DETECT_DIR, "data", "discovery", "*.json"))
    for f_path in discovery_files:
        try:
            with open(f_path, 'r', encoding='utf-8') as f:
                d_data = json.load(f)
                items = d_data if isinstance(d_data, list) else d_data.get('data', [])
                if not isinstance(items, list): continue
                for p in items:
                    norm = normalize_profile(p)
                    if norm["username"]:
                        u_lower = norm["username"].lower()
                        if u_lower not in metadata_map or not metadata_map[u_lower].get("followers"):
                            metadata_map[u_lower] = norm
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
        m = metadata_map.get(u.lower(), {})
        
        leads_json_data.append({
            "u": u,
            "n": m.get("name", u),
            "b": m.get("bio", "").replace("\\n", " ").replace('"', "'"),
            "s": r.get("ml_score", 0.95),
            "fl": int(m.get("followers", 0)),
            "fg": int(m.get("following", 0)),
            "tw": int(m.get("tweets", 0)),
            "img": (m.get("profile_image") or "").replace("_normal", "_bigger"),
            "year": m.get("year", 0),
            "d": m.get("last_tweet_days", 1),
            "reason": r.get("reason", "").replace('"', "'"),
            "conf": r.get("confidence", 0)
        })

    # Template from final_leads_v3.html (Vanilla CSS/JS)
    html_template = \"\"\"<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>Terafab Human Alpha Leads - Dashboard</title>
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
td{padding:14px 10px;border-bottom:1px solid #1a1a1a;vertical-align:top}
tr:hover{background:#161616}
.user-cell{display:flex;align-items:center;gap:12px;min-width:200px}
.avatar{width:40px;height:40px;border-radius:50%;object-fit:cover;border:2px solid #333;flex-shrink:0}
.user-link{color:#4fc3f7;text-decoration:none;font-weight:700;font-size:0.95rem;transition:opacity 0.2s}
.user-link:hover{opacity:0.8;text-decoration:underline}
.user-name{color:#888;font-size:0.8rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:160px}
.bio-cell{max-width:200px;color:#9b9b9b;font-size:0.85rem;line-height:1.5}
.reason-cell{max-width:300px;color:#888;font-size:0.8rem;font-style:italic;background:rgba(16,185,129,0.05);padding:10px;border-radius:8px;border-left:3px solid #10b981}
.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;padding-right:15px}
.score{font-weight:700;font-size:0.9rem;color:#66bb6a}
.pagination{display:flex;gap:8px;justify-content:center;align-items:center;margin:25px 0;flex-wrap:wrap}
.page-btn{padding:8px 16px;border-radius:8px;border:1px solid #333;background:#1a1a1a;color:#aaa;cursor:pointer;font-size:0.9rem;transition:all 0.2s}
.page-btn:hover:not(:disabled){background:#222;color:#fff;border-color:#4fc3f7}
.page-btn.active{background:#4fc3f7;color:#000;border-color:#4fc3f7;font-weight:700}
.page-btn:disabled{opacity:0.3;cursor:not-allowed}
.page-info{color:#888;font-size:0.85rem;margin:0 10px}
@media(max-width:1024px){.bio-cell, .hide-tablet {display:none}}
@media(max-width:768px){.reason-cell, .hide-mobile {display:none}}
</style>
</head>
<body>
<div class=\"header\">
  <h1>Terafab Human Alpha Leads</h1>
  <div class=\"sub\">Forensic DeepSeek-R1 Validation | Human Only | <span id=\"leads-count\">0</span> leads</div>
</div>

<div class=\"stats\">
  <div class=\"stat-card\"><div class=\"val\" id=\"stat-total\">0</div><div class=\"label\">Total Humans</div></div>
  <div class=\"stat-card\"><div class=\"val\" id=\"stat-avg-followers\">0</div><div class=\"label\">Avg Followers</div></div>
</div>

<div class=\"controls\">
  <input type=\"text\" class=\"search\" id=\"search\" placeholder=\"Search name, handle, bio, or reason...\">
  <button class=\"sort-btn active\" id=\"btn-fl\" onclick=\"setSort('fl','desc')\">Most Followers</button>
  <button class=\"sort-btn\" id=\"btn-s\" onclick=\"setSort('s','desc')\">High Score</button>
  <button class=\"sort-btn\" onclick=\"setSort('d','asc')\">Most Recent</button>
</div>

<div class=\"count\" id=\"count\"></div>

<div class=\"table-wrap\">
<table>
<thead>
<tr>
  <th>User</th>
  <th class=\"hide-tablet\">Bio</th>
  <th class=\"hide-mobile\">AI Reasoning</th>
  <th class=\"num\">Followers</th>
  <th class=\"num hide-mobile\">Tweets</th>
  <th class=\"num hide-mobile\">Since</th>
  <th class=\"num\">Active</th>
  <th class=\"num\">Score</th>
</tr>
</thead>
<tbody id=\"tbody\"></tbody>
</table>
</div>

<div class=\"pagination\" id=\"pagination\"></div>

<script>
const DATA = \"\"\" + json.dumps(leads_json_data) + \"\"\";
let filteredData = [...DATA];
let currentPage = 1;
const itemsPerPage = 50;
let sortCol = 'fl';
let sortDesc = true;

function setSort(col, dir) {
  sortCol = col;
  sortDesc = dir === 'desc';
  document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
  if(col === 'fl') document.getElementById('btn-fl').classList.add('active');
  if(col === 's') document.getElementById('btn-s').classList.add('active');
  applyFilters();
}

function applyFilters() {
  const query = document.getElementById('search').value.toLowerCase();
  filteredData = DATA.filter(d => 
    d.u.toLowerCase().includes(query) || 
    d.n.toLowerCase().includes(query) || 
    (d.b && d.b.toLowerCase().includes(query)) ||
    (d.reason && d.reason.toLowerCase().includes(query))
  );
  
  filteredData.sort((a, b) => {
    let vA = a[sortCol];
    let vB = b[sortCol];
    if(sortDesc) return vB - vA;
    return vA - vB;
  });
  
  currentPage = 1;
  render();
}

function render() {
  const totalLeads = DATA.length;
  const avgFollowers = totalLeads > 0 ? Math.round(DATA.reduce((acc, d) => acc + d.fl, 0) / totalLeads) : 0;
  document.getElementById('stat-total').innerText = totalLeads;
  document.getElementById('stat-avg-followers').innerText = avgFollowers.toLocaleString();
  document.getElementById('leads-count').innerText = totalLeads;

  const start = (currentPage - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  const pageItems = filteredData.slice(start, end);
  
  const tbody = document.getElementById('tbody');
  tbody.innerHTML = pageItems.map(d => `
    <tr>
      <td>
        <div class=\"user-cell\">
          <img class=\"avatar\" src=\"\${d.img}\" onerror=\"this.src='https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png'\">
          <div class=\"user-info\">
            <a href=\"https://x.com/\${d.u}\" target=\"_blank\" class=\"user-link\">@\${d.u}</a>
            <div class=\"user-name\">\${d.n}</div>
          </div>
        </div>
      </td>
      <td class=\"bio-cell\">\${d.b || ''}</td>
      <td class=\"reason-cell\">\${d.reason || ''}</td>
      <td class=\"num\">\${d.fl.toLocaleString()}</td>
      <td class=\"num hide-mobile\">\${d.tw.toLocaleString()}</td>
      <td class=\"num hide-mobile\">\${d.year || ''}</td>
      <td class=\"num\">\${d.d}d</td>
      <td class=\"num\"><span class=\"score\">\${(d.s * 100).toFixed(0)}%</span></td>
    </tr>
  \`).join('');
  
  renderPagination();
  document.getElementById('count').innerText = \`Showing \${start+1}-\${Math.min(end, filteredData.length)} of \${filteredData.length} leads\`;
}

function renderPagination() {
  const totalPages = Math.ceil(filteredData.length / itemsPerPage);
  const wrap = document.getElementById('pagination');
  if(totalPages <= 1) { wrap.innerHTML = ''; return; }
  
  let html = \`<button class=\"page-btn\" \${currentPage === 1 ? 'disabled' : ''} onclick=\"changePage(\${currentPage-1})\">Prev</button>\`;
  
  let startPage = Math.max(1, currentPage - 2);
  let endPage = Math.min(totalPages, startPage + 4);
  if(endPage - startPage < 4) startPage = Math.max(1, endPage - 4);
  
  for(let i=startPage; i<=endPage; i++) {
    html += \`<button class=\"page-btn \${i === currentPage ? 'active' : ''}\" onclick=\"changePage(\${i})\">\${i}</button>\`;
  }
  
  html += \`<button class=\"page-btn\" \${currentPage === totalPages ? 'disabled' : ''} onclick=\"changePage(\${currentPage+1})\">Next</button>\`;
  wrap.innerHTML = html;
}

function changePage(p) {
  currentPage = p;
  render();
  window.scrollTo(0,0);
}

document.getElementById('search').addEventListener('input', applyFilters);
applyFilters();
</script>
</body>
</html>\"\"\"
    
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f\"Standalone Terafab report generated: {OUTPUT_FILE}\")

if __name__ == \"__main__\":
    export()
