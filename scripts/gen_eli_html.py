
import json
import os
from datetime import datetime

# Configuration
INPUT_FILE = r'c:\Users\Administrator\Desktop\X\detect\data\harvest\eli_leads_qualified_enriched.json'
OUTPUT_FILE = r'c:\Users\Administrator\Desktop\X\detect\eli_leads_v1.html'

def load_data():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, dict):
            return data.get('leads', [])
        return data

def get_year(date_str):
    if not date_str:
        return "N/A"
    try:
        # Format: 2023-05-13T03:20:02Z
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return str(dt.year)
    except:
        return "N/A"

def generate_html(leads):
    leads_json = json.dumps(leads, ensure_ascii=False)
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CaptainEli Qualified Leads Dashboard</title>
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
.pagination{{display:flex;gap:8px;justify-content:center;align-items:center;margin:25px 0;flex-wrap:wrap}}
.page-btn{{padding:8px 16px;border-radius:8px;border:1px solid #333;background:#1a1a1a;color:#aaa;cursor:pointer;font-size:0.9rem;transition:all 0.2s}}
.page-btn:hover:not(:disabled){{background:#222;color:#fff;border-color:#4fc3f7}}
.page-btn.active{{background:#4fc3f7;color:#000;border-color:#4fc3f7;font-weight:700}}
.page-btn:disabled{{opacity:0.3;cursor:not-allowed}}
.page-info{{color:#888;font-size:0.85rem;margin:0 10px}}
@media(max-width:1024px){{.bio-cell,.hide-tablet{{display:none}}}}
@media(max-width:768px){{.reason-cell,.hide-mobile{{display:none}}.user-cell{{min-width:150px}}.avatar{{width:32px;height:32px}}th,td{{padding:10px 6px}}}}
</style>
</head>
<body>
<div class="header">
    <h1>CaptainEli Qualified Leads</h1>
    <div class="sub">Verified Humans | Qualified for Outreach | 566 Leads</div>
</div>

<div class="stats">
    <div class="stat-card"><div class="val">{len(leads)}</div><div class="label">Total Humans</div></div>
    <div class="stat-card"><div class="val">566</div><div class="label">Qualified</div></div>
</div>

<div class="controls">
    <input type="text" class="search" id="search" placeholder="Search name, handle, bio, or reason...">
    <button class="sort-btn active" id="btn-fl" onclick="setSort('fl','desc')">Most Followers</button>
    <button class="sort-btn" id="btn-s" onclick="setSort('s','desc')">High Recency</button>
</div>

<div class="count" id="count"></div>

<div class="table-wrap">
    <table>
        <thead>
            <tr>
                <th data-col="u">User</th>
                <th data-col="b" class="hide-tablet">Bio</th>
                <th data-col="reason" class="hide-mobile">DeepSeek Reasoning</th>
                <th data-col="fl" class="num">Followers</th>
                <th data-col="tw" class="num hide-mobile">Tweets</th>
                <th data-col="year" class="num hide-mobile">Since</th>
                <th data-col="d" class="num">Active</th>
            </tr>
        </thead>
        <tbody id="tbody"></tbody>
    </table>
</div>

<div class="pagination" id="pagination"></div>

<script>
const DATA = {leads_json}; 
const PAGE_SIZE = 50;
let page = 1;
let filtered = [...DATA];
let sortKey = 'fl';
let sortDir = 'desc';

function $(id){{return document.getElementById(id)}}

function getYear(dateStr) {{
    if (!dateStr) return '2024';
    return dateStr.split('-')[0];
}}

function activeText(d){{
    if (d === undefined || d === null) return 'Unknown';
    return d <= 0 ? 'Today' : d === 1 ? '1d ago' : d < 30 ? d + 'd ago' : Math.floor(d / 30) + 'mo ago';
}}

function setSort(key, dir){{
    sortKey = key; sortDir = dir;
    document.querySelectorAll('.sort-btn').forEach(b=>b.classList.remove('active'));
    if(key==='fl') $('btn-fl').classList.add('active');
    if(key==='s') $('btn-s').classList.add('active');
    apply();
}}

function apply(){{
    const q = $('search').value.toLowerCase();
    filtered = DATA.filter(p => {{
        const reason = p.deepseek_qualification?.reason || '';
        return (p.userName + ' ' + (p.name||'') + ' ' + (p.description||'') + ' ' + reason).toLowerCase().includes(q);
    }});
    
    filtered.sort((a,b) => {{
        let v1, v2;
        if (sortKey === 's') {{
            v1 = a.last_tweet_days === undefined ? 9999 : a.last_tweet_days;
            v2 = b.last_tweet_days === undefined ? 9999 : b.last_tweet_days;
            return sortDir === 'asc' ? v1 - v2 : v2 - v1;
        }} else if (sortKey === 'year') {{
            v1 = getYear(a.createdAt);
            v2 = getYear(b.createdAt);
        }} else {{
            v1 = a[sortKey]; v2 = b[sortKey];
        }}
        
        if(typeof v1 === 'string') v1 = v1.toLowerCase();
        if(typeof v2 === 'string') v2 = v2.toLowerCase();
        if(v1 < v2) return sortDir === 'asc' ? -1 : 1;
        if(v1 > v2) return sortDir === 'asc' ? 1 : -1;
        return 0;
    }});

    $('count').textContent = `Showing ${{filtered.length}} leads`;
    page = 1;
    render();
}}

function render(){{
    const start = (page-1)*PAGE_SIZE;
    const end = start + PAGE_SIZE;
    const slice = filtered.slice(start, end);
    
    $('tbody').innerHTML = slice.map(p => {{
        const reason = p.deepseek_qualification?.reason || '';
        const year = getYear(p.createdAt);
        const active = activeText(p.last_tweet_days);
        
        return `
            <tr>
                <td>
                    <div class="user-cell">
                        <div class="avatar-placeholder">${{p.userName[0].toUpperCase()}}</div>
                        <div class="user-info">
                            <a href="https://x.com/${{p.userName}}" target="_blank" class="user-link">@${{p.userName}}</a>
                            <div class="user-name">${{p.name}}</div>
                        </div>
                    </div>
                </td>
                <td class="bio-cell">${{p.description || ''}}</td>
                <td class="reason-cell">${{reason}}</td>
                <td class="num">${{(p.followers || 0).toLocaleString()}}</td>
                <td class="num hide-mobile">${{(p.statusesCount || 0).toLocaleString()}}</td>
                <td class="num hide-mobile">${{year}}</td>
                <td class="num">${{active}}</td>
            </tr>
        `;
    }}).join('');
    
    renderPager();
}}

function renderPager(){{
    const total = Math.ceil(filtered.length / PAGE_SIZE);
    const p = $('pagination');
    p.innerHTML = '';
    if(total <= 1) return;
    
    for(let i=1; i<=total; i++){{
        if(i===1 || i===total || (i >= page-1 && i <= page+1)){{
            const btn = document.createElement('button');
            btn.className = `page-btn ${{i===page?'active':''}}`;
            btn.textContent = i;
            btn.onclick = () => {{ page=i; render(); window.scrollTo(0,0); }};
            p.appendChild(btn);
        }} else if (i === page-2 || i === page+2) {{
            const span = document.createElement('span');
            span.textContent = '...';
            span.style.color = '#444';
            p.appendChild(span);
        }}
    }}
}}

$('search').oninput = apply;
document.querySelectorAll('th[data-col]').forEach(th => {{
    th.onclick = () => {{
        const k = th.dataset.col;
        if(sortKey === k) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
        else {{ sortKey = k; sortDir = 'desc'; }}
        
        document.querySelectorAll('th').forEach(t => t.classList.remove('sorted-asc', 'sorted-desc'));
        th.classList.add(sortDir==='asc'?'sorted-asc':'sorted-desc');
        apply();
    }};
}});

setSort('fl', 'desc');
</script>
</body>
</html>"""
    return html_template

if __name__ == "__main__":
    leads = load_data()
    print(f"Generating HTML for {len(leads)} leads...")
    html_content = generate_html(leads)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Saved to {OUTPUT_FILE}")
