"""Generate mobile-friendly HTML dashboard for active human profiles."""
import argparse
import json
import os
import sys

DETECT_DIR = os.path.dirname(os.path.abspath(__file__))

TARGETS = {
    "spomboy": {
        "data": os.path.join(DETECT_DIR, "data", "active_humans.json"),
        "output": os.path.join(DETECT_DIR, "spomboy_humans.html"),
        "title": "@spomboy Active Human Followers",
        "subtitle": "High-confidence humans (ML score &lt; 0.20) | Followers &amp; Following &lt; 2,500 | Active within 90 days",
    },
    "hayekandkeynes": {
        "data": os.path.join(DETECT_DIR, "data", "active_humans_hayekandkeynes.json"),
        "output": os.path.join(DETECT_DIR, "hayekandkeynes_humans.html"),
        "title": "@HayekAndKeynes Active Human Followers",
        "subtitle": "High-confidence humans (ML score &lt; 0.20) | Followers &amp; Following &lt; 2,000 | Active within 90 days",
    },
    "marionawfal": {
        "data": os.path.join(DETECT_DIR, "data", "active_humans_marionawfal.json"),
        "output": os.path.join(DETECT_DIR, "marionawfal_humans.html"),
        "title": "@MarioNawfal Human Followers",
        "subtitle": "LLM-validated humans (DeepSeek VALIDATION prompt) | Followers &amp; Following &lt; 1,000 | 9,324 confirmed leads",
    },
}


def generate_dashboard(target_name):
    cfg = TARGETS[target_name]
    with open(cfg["data"], "r", encoding="utf-8") as f:
        profiles = json.load(f)

    # Minify and remap keys for smaller HTML
    minified = []
    for p in profiles:
        img = (p.get("profile_image") or "").replace("_normal", "_bigger")
        ca = p.get("created_at", "")
        year = 0
        if ca:
            try:
                # Handle both 'Wed Jan 15 00:00:00 +0000 2020' and '2020-01-15T...'
                if "T" in ca:
                    year = int(ca[:4])
                else:
                    year = int(ca.split()[-1])
            except Exception:
                pass
        bio = p.get("bio", "")
        if len(bio) > 200:
            bio = bio[:197] + "..."
        minified.append({
            "u": p["username"],
            "n": p.get("name", ""),
            "b": bio,
            "s": round(p["bot_score"], 4),
            "fl": p["followers"],
            "fg": p["following"],
            "tw": p["tweets"],
            "d": p["last_tweet_days"],
            "img": img,
            "year": year,
        })

    data_json = json.dumps(minified, ensure_ascii=False, separators=(",", ":"))

    total = len(minified)
    if total == 0:
        print(f"ERROR: No profiles in {cfg['data']}")
        return
    avg_score = sum(m["s"] for m in minified) / total
    avg_fl = sum(m["fl"] for m in minified) / total
    avg_fg = sum(m["fg"] for m in minified) / total
    avg_tw = sum(m["tw"] for m in minified) / total

    title = cfg["title"]
    subtitle = cfg["subtitle"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} ({total:,})</title>
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
td{{padding:8px;border-bottom:1px solid #1a1a1a;vertical-align:middle}}
tr:hover{{background:#161616}}
.user-cell{{display:flex;align-items:center;gap:8px;min-width:180px}}
.avatar{{width:32px;height:32px;border-radius:50%;object-fit:cover;border:1px solid #333;flex-shrink:0}}
.avatar-placeholder{{width:32px;height:32px;border-radius:50%;background:#333;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:12px;color:#666}}
.user-info{{overflow:hidden}}
.user-link{{color:#4fc3f7;text-decoration:none;font-weight:600;font-size:0.85rem}}
.user-link:hover{{text-decoration:underline}}
.user-name{{color:#888;font-size:0.75rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:150px}}
.bio-cell{{max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#999;font-size:0.8rem}}
.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
.score{{font-weight:700;font-size:0.85rem}}
.score-low{{color:#66bb6a}}
.score-med{{color:#ffa726}}
.score-high{{color:#ef5350}}
.active-cell{{white-space:nowrap;font-size:0.8rem}}
.active-recent{{color:#66bb6a}}
.active-moderate{{color:#ffa726}}
.active-old{{color:#ef5350}}
.pagination{{display:flex;gap:6px;justify-content:center;align-items:center;margin:16px 0;flex-wrap:wrap}}
.page-btn{{padding:6px 12px;border-radius:6px;border:1px solid #333;background:#1a1a1a;color:#aaa;cursor:pointer;font-size:0.85rem}}
.page-btn:hover{{background:#222;color:#fff}}
.page-btn.active{{background:#4fc3f7;color:#000;border-color:#4fc3f7;font-weight:700}}
.page-btn:disabled{{opacity:0.3;cursor:not-allowed}}
.page-info{{color:#888;font-size:0.8rem}}
@media(max-width:768px){{
  body{{padding:6px}}
  .header h1{{font-size:1.2rem}}
  .stats{{gap:6px}}
  .stat-card{{padding:8px 12px;min-width:70px}}
  .stat-card .val{{font-size:1rem}}
  table{{font-size:0.78rem}}
  th,td{{padding:6px 4px}}
  .avatar{{width:28px;height:28px}}
  .bio-cell{{max-width:120px}}
  .user-cell{{min-width:140px}}
  .hide-mobile{{display:none}}
}}
</style>
</head>
<body>
<div class="header">
  <h1>{title}</h1>
  <div class="sub">{subtitle}</div>
</div>
<div class="stats">
  <div class="stat-card"><div class="val">{total:,}</div><div class="label">Total Profiles</div></div>
  <div class="stat-card"><div class="val">{avg_score:.2f}</div><div class="label">Avg Bot Score</div></div>
  <div class="stat-card"><div class="val">{avg_fl:,.0f}</div><div class="label">Avg Followers</div></div>
  <div class="stat-card"><div class="val">{avg_fg:,.0f}</div><div class="label">Avg Following</div></div>
  <div class="stat-card"><div class="val">{avg_tw:,.0f}</div><div class="label">Avg Tweets</div></div>
</div>
<div class="controls">
  <input type="text" class="search" id="search" placeholder="Search username, name, or bio...">
  <button class="sort-btn" onclick="setSort('s','asc')">Score Low</button>
  <button class="sort-btn" onclick="setSort('s','desc')">Score High</button>
  <button class="sort-btn" onclick="setSort('fl','desc')">Most Followers</button>
  <button class="sort-btn" onclick="setSort('d','asc')">Most Recent</button>
</div>
<div class="count" id="count"></div>
<div class="table-wrap">
<table>
<thead>
<tr>
  <th data-col="u">User</th>
  <th data-col="b" class="hide-mobile">Bio</th>
  <th data-col="fl">Followers</th>
  <th data-col="fg">Following</th>
  <th data-col="tw" class="hide-mobile">Tweets</th>
  <th data-col="s">Bot Score</th>
  <th data-col="year" class="hide-mobile">Since</th>
  <th data-col="d">Last Active</th>
</tr>
</thead>
<tbody id="tbody"></tbody>
</table>
</div>
<div class="pagination" id="pagination"></div>
<script>
const DATA=REPLACE_DATA;
const PER_PAGE=50;
let filtered=DATA.slice();
let sortCol='s',sortDir='asc';
let page=1;
const $=id=>document.getElementById(id);
const tbody=$('tbody');
const search=$('search');

function scoreClass(s){{return s<0.08?'score-low':s<0.15?'score-med':'score-high'}}
function activeClass(d){{return d<=14?'active-recent':d<=60?'active-moderate':'active-old'}}
function activeText(d){{return d<=0?'Today':d===1?'1d ago':d<30?d+'d ago':d<60?Math.floor(d/7)+'w ago':Math.floor(d/30)+'mo ago'}}
function esc(s){{if(!s)return'';const d=document.createElement('div');d.textContent=s;return d.innerHTML}}

function render(){{
  const start=(page-1)*PER_PAGE;
  const slice=filtered.slice(start,start+PER_PAGE);
  let h='';
  for(const p of slice){{
    const imgHtml=p.img?'<img class="avatar" src="'+esc(p.img)+'" alt="" loading="lazy" onerror="this.outerHTML=\\'<div class=avatar-placeholder>?</div>\\'">' :'<div class="avatar-placeholder">?</div>';
    h+='<tr>'
      +'<td><div class="user-cell">'+imgHtml+'<div class="user-info"><a class="user-link" href="https://x.com/'+esc(p.u)+'" target="_blank" rel="noopener">@'+esc(p.u)+'</a><div class="user-name">'+esc(p.n)+'</div></div></div></td>'
      +'<td class="bio-cell hide-mobile" title="'+esc(p.b)+'">'+esc(p.b)+'</td>'
      +'<td class="num">'+p.fl.toLocaleString()+'</td>'
      +'<td class="num">'+p.fg.toLocaleString()+'</td>'
      +'<td class="num hide-mobile">'+p.tw.toLocaleString()+'</td>'
      +'<td class="num"><span class="score '+scoreClass(p.s)+'">'+p.s.toFixed(4)+'</span></td>'
      +'<td class="num hide-mobile">'+(p.year||'-')+'</td>'
      +'<td class="num"><span class="active-cell '+activeClass(p.d)+'">'+activeText(p.d)+'</span></td>'
      +'</tr>';
  }}
  tbody.innerHTML=h;
  $('count').textContent='Showing '+(start+1)+'-'+Math.min(start+PER_PAGE,filtered.length)+' of '+filtered.length.toLocaleString()+' profiles';
  renderPagination();
}}

function renderPagination(){{
  const totalPages=Math.ceil(filtered.length/PER_PAGE);
  if(totalPages<=1){{$('pagination').innerHTML='';return}}
  let h='<button class="page-btn" onclick="goPage(1)" '+(page===1?'disabled':'')+'>First</button>';
  h+='<button class="page-btn" onclick="goPage('+(page-1)+')" '+(page===1?'disabled':'')+'>Prev</button>';
  const start=Math.max(1,page-3),end=Math.min(totalPages,page+3);
  for(let i=start;i<=end;i++){{
    h+='<button class="page-btn '+(i===page?'active':'')+'" onclick="goPage('+i+')">'+i+'</button>';
  }}
  h+='<button class="page-btn" onclick="goPage('+(page+1)+')" '+(page===totalPages?'disabled':'')+'>Next</button>';
  h+='<button class="page-btn" onclick="goPage('+totalPages+')" '+(page===totalPages?'disabled':'')+'>Last</button>';
  h+='<span class="page-info">Page '+page+'/'+totalPages+'</span>';
  $('pagination').innerHTML=h;
}}

function goPage(p){{const tp=Math.ceil(filtered.length/PER_PAGE);page=Math.max(1,Math.min(tp,p));render();window.scrollTo({{top:0,behavior:'smooth'}})}}

function doSort(){{
  filtered.sort((a,b)=>{{
    let va=a[sortCol],vb=b[sortCol];
    if(typeof va==='string')va=va.toLowerCase();
    if(typeof vb==='string')vb=vb.toLowerCase();
    if(va<vb)return sortDir==='asc'?-1:1;
    if(va>vb)return sortDir==='asc'?1:-1;
    return 0;
  }});
  document.querySelectorAll('th').forEach(th=>{{th.classList.remove('sorted-asc','sorted-desc')}});
  const th=document.querySelector('th[data-col="'+sortCol+'"]');
  if(th)th.classList.add(sortDir==='asc'?'sorted-asc':'sorted-desc');
}}

function setSort(col,dir){{sortCol=col;sortDir=dir;doSort();page=1;render();
  document.querySelectorAll('.sort-btn').forEach(b=>b.classList.remove('active'));
}}

document.querySelectorAll('th').forEach(th=>{{
  th.addEventListener('click',()=>{{
    const col=th.dataset.col;
    if(sortCol===col)sortDir=sortDir==='asc'?'desc':'asc';
    else{{sortCol=col;sortDir='asc'}}
    doSort();page=1;render();
  }});
}});

let debounce;
search.addEventListener('input',()=>{{
  clearTimeout(debounce);
  debounce=setTimeout(()=>{{
    const q=search.value.toLowerCase().trim();
    filtered=q?DATA.filter(p=>(p.u+' '+p.n+' '+p.b).toLowerCase().includes(q)):DATA.slice();
    doSort();page=1;render();
  }},200);
}});

doSort();render();
</script>
</body>
</html>"""

    # Replace the placeholder with actual data
    html = html.replace("REPLACE_DATA", data_json)

    with open(cfg["output"], "w", encoding="utf-8") as f:
        f.write(html)

    size = os.path.getsize(cfg["output"])
    print(f"Generated: {cfg['output']}")
    print(f"Size: {size:,} bytes ({size/1024/1024:.1f} MB)")
    print(f"Profiles: {total}")
    return cfg["output"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate HTML dashboard")
    parser.add_argument("--target", type=str, default="all",
                        choices=list(TARGETS.keys()) + ["all"],
                        help="Target to generate (default: all)")
    args = parser.parse_args()

    if args.target == "all":
        for name in TARGETS:
            if os.path.exists(TARGETS[name]["data"]):
                print(f"\n--- Generating {name} ---")
                generate_dashboard(name)
            else:
                print(f"\n--- Skipping {name} (no data file) ---")
    else:
        generate_dashboard(args.target)
