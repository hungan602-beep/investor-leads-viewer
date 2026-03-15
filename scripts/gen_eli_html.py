
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
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }}
        .glass {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); }}
        .card-hover:hover {{ transform: translateY(-2px); transition: all 0.2s; border-color: #38bdf8; }}
        input::placeholder {{ color: #94a3b8; }}
        .status-active {{ color: #4ade80; }}
        .status-stale {{ color: #94a3b8; }}
        .status-mid {{ color: #fbbf24; }}
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-7xl mx-auto">
        <!-- Header -->
        <div class="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
            <div>
                <h1 class="text-3xl font-bold bg-gradient-to-r from-sky-400 to-indigo-500 bg-clip-text text-transparent">
                    CaptainEli Qualified Leads
                </h1>
                <p class="text-slate-400 mt-1">Found {len(leads)} verified human profiles for outreach</p>
            </div>
            <div class="flex gap-4 w-full md:w-auto">
                <input type="text" id="search" placeholder="Search bio, name, handle..." 
                       class="glass w-full md:w-80 px-4 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500">
            </div>
        </div>

        <!-- Controls -->
        <div class="flex flex-wrap gap-4 mb-6">
            <select id="sort" class="glass px-4 py-2 rounded-xl focus:outline-none cursor-pointer">
                <option value="followers">Sort by Followers</option>
                <option value="last_active">Sort by Last Active</option>
                <option value="year">Sort by Age (Year)</option>
                <option value="statusesCount">Sort by Tweets</option>
            </select>
            <div class="flex items-center gap-2 glass px-4 py-2 rounded-xl">
                <span class="text-sm text-slate-400">Total Humans:</span>
                <span class="font-bold text-sky-400" id="count-display">{len(leads)}</span>
            </div>
        </div>

        <!-- Grid -->
        <div id="leads-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <!-- Cards injected here -->
        </div>
    </div>

    <script>
        const leads = {leads_json};

        function getStatusColor(days) {{
            if (days === undefined || days === null) return 'status-stale';
            if (days <= 7) return 'status-active';
            if (days <= 30) return 'status-mid';
            return 'status-stale';
        }}

        function getYear(dateStr) {{
            if (!dateStr) return 'N/A';
            return dateStr.split('-')[0];
        }}

        function renderLeads(filteredLeads) {{
            const grid = document.getElementById('leads-grid');
            grid.innerHTML = filteredLeads.map(lead => {{
                const days = lead.last_tweet_days;
                const statusColor = getStatusColor(days);
                const lastActive = days === undefined ? 'Unknown' : (days === 0 ? 'Today' : `${{days}}d ago`);
                const reason = lead.deepseek_qualification?.reason || '';
                
                return `
                    <div class="glass p-6 rounded-2xl card-hover flex flex-col h-full">
                        <div class="flex justify-between items-start mb-4">
                            <div>
                                <h3 class="font-bold text-lg text-white">@${{lead.userName}}</h3>
                                <p class="text-slate-400 text-sm">${{lead.name}}</p>
                            </div>
                            <span class="px-3 py-1 bg-sky-500/10 text-sky-400 rounded-full text-xs font-semibold">
                                ${{getYear(lead.createdAt)}}
                            </span>
                        </div>
                        
                        <p class="text-slate-300 text-sm mb-4 flex-grow italic">
                            "${{lead.description || 'No bio...'}}"
                        </p>

                        <!-- Qualification Context -->
                        <div class="mb-4 p-3 bg-indigo-500/5 border border-indigo-500/10 rounded-lg">
                            <p class="text-[10px] uppercase tracking-wider text-indigo-400 font-bold mb-1">DeepSeek Reason</p>
                            <p class="text-xs text-slate-400 line-clamp-2">${{reason}}</p>
                        </div>

                        <div class="grid grid-cols-2 gap-4 mb-4">
                            <div class="bg-slate-800/50 p-2 rounded-lg text-center">
                                <p class="text-[10px] text-slate-500 uppercase">Followers</p>
                                <p class="font-bold">${{lead.followers?.toLocaleString() || 0}}</p>
                            </div>
                            <div class="bg-slate-800/50 p-2 rounded-lg text-center">
                                <p class="text-[10px] text-slate-500 uppercase">Tweets</p>
                                <p class="font-bold">${{lead.statusesCount?.toLocaleString() || 0}}</p>
                            </div>
                        </div>

                        <div class="flex justify-between items-center pt-4 border-t border-slate-700/50 mt-auto">
                            <div class="flex items-center gap-2">
                                <span class="w-2 h-2 rounded-full ${{statusColor}} bg-current animate-pulse"></span>
                                <span class="text-xs text-slate-400">Last Active: ${{lastActive}}</span>
                            </div>
                            <a href="https://x.com/${{lead.userName}}" target="_blank" 
                               class="text-xs bg-sky-500 hover:bg-sky-400 text-white px-4 py-2 rounded-lg transition-colors font-medium">
                                Profile
                            </a>
                        </div>
                    </div>
                `;
            }}).join('');
            document.getElementById('count-display').textContent = filteredLeads.length;
        }}

        // Search & Filter Logic
        const searchInput = document.getElementById('search');
        const sortSelect = document.getElementById('sort');

        function update() {{
            const query = searchInput.value.toLowerCase();
            const sortBy = sortSelect.value;

            let filtered = leads.filter(l => 
                (l.userName || '').toLowerCase().includes(query) ||
                (l.name || '').toLowerCase().includes(query) ||
                (l.description || '').toLowerCase().includes(query)
            );

            filtered.sort((a, b) => {{
                if (sortBy === 'followers') return (b.followers || 0) - (a.followers || 0);
                if (sortBy === 'statusesCount') return (b.statusesCount || 0) - (a.statusesCount || 0);
                if (sortBy === 'year') return getYear(b.createdAt).localeCompare(getYear(a.createdAt));
                if (sortBy === 'last_active') {{
                    const da = a.last_tweet_days === undefined ? 9999 : a.last_tweet_days;
                    const db = b.last_tweet_days === undefined ? 9999 : b.last_tweet_days;
                    return da - db;
                }}
                return 0;
            }});

            renderLeads(filtered);
        }}

        searchInput.addEventListener('input', update);
        sortSelect.addEventListener('change', update);

        // Initial render
        update();
    </script>
</body>
</html>
"""
    return html_template

if __name__ == "__main__":
    leads = load_data()
    print(f"Generating HTML for {len(leads)} leads...")
    html_content = generate_html(leads)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Saved to {OUTPUT_FILE}")
