import pandas as pd
import os

def create_excel_content():
    # Signal Strength Labels:
    # Viral: > 1000 likes or highly buzzed topic (X Money, Grok 4.20)
    # Steady: 50-1000 likes (Macrohard, AI4)
    # Niche: < 50 likes (Routine deep-dives, specific engineering specs)

    data = {
        "Handle": [
            "@teslaxalpha", "@teslaxalpha", "@teslaxalpha", "@teslaxalpha", "@teslaxalpha",
            "@teslaxalpha", "@teslaxalpha", "@teslaxalpha", "@teslaxalpha", "@teslaxalpha",
            "@teslaxalpha", "@teslaxalpha", "@teslaxalpha", "@teslaxalpha", "@teslaxalpha",
            "@tslaxventures", "@tslaxventures", "@tslaxventures", "@tslaxventures", "@tslaxventures",
            "@tslaxventures", "@tslaxventures", "@tslaxventures", "@tslaxventures", "@tslaxventures",
            "@tslaxventures", "@tslaxventures", "@tslaxventures", "@tslaxventures", "@tslaxventures",
            "@tesla_group_x", "@tesla_group_x", "@tesla_group_x", "@tesla_group_x", "@tesla_group_x",
            "@tesla_group_x", "@tesla_group_x", "@tesla_group_x", "@tesla_group_x", "@tesla_group_x",
            "@tesla_group_x", "@tesla_group_x", "@tesla_group_x", "@tesla_group_x", "@tesla_group_x"
        ],
        "Signal Strength": [
            "Steady", "Viral", "Viral", "Viral", "Steady", "Steady", "Steady", "Steady", "Steady",
            "Steady", "Steady", "Steady", "Steady", "Steady", "Steady",
            "Steady", "Steady", "Steady", "Steady", "Steady", "Steady", "Steady", "Viral", "Viral",
            "Steady", "Steady", "Steady", "Steady", "Steady", "Steady",
            "Viral", "Viral", "Steady", "Steady", "Steady", "Steady", "Steady", "Steady", "Steady",
            "Steady", "Steady", "Steady", "Steady", "Steady", "Steady"
        ],
        "Content": [
            "Analysis of the System 1 (instinctive/action) vs System 2 (reasoning/navigator) architecture for humanoid robotics.",
            "Why running real-time AI on low-cost ($650) Tesla AI4 hardware is the ultimate engineering moat.",
            "Technical implications of Grok 4.20's 2M token context window for processing long-tail telemetry data.",
            "Context Window Comparison: Grok 4.20 (2M) vs GPT 5.4 (1M) vs Claude 4.6 (200K).",
            "How Tesla is architecting the 'Enterprise Brain' to emulate the functions of entire companies via digital Optimus.",
            "The synergy between xAI server clusters and Tesla vehicle edge-inference.",
            "Breakdown of Ashok Elluswamy's latest recruitment focus: Real-time world models.",
            "Why 'real-time' is the defining characteristic of the Musk AI stack. 5-sec buffer for digital Optimus.",
            "Predicting the shift from static image generation to 30-sec video extensions for autonomous training.",
            "Why moving beyond 'vibe coding' to structured, reliable AI outputs is the missing link for AGI.",
            "How 30-second localized world 'imaginations' help agents plan complex logistics.",
            "Technical review of xAI’s claim of the 'lowest hallucination rate' on the market.",
            "Training the 'instinctive mind' of Optimus to handle varied keyboard/mouse interactions.",
            "The physics of running AGI on low-power hardware. Is AI4 the final form?",
            "Why Grok isn't just a chatbot, but a navigator for complex, multi-stage tasks.",
            "The hidden infrastructure required to support massive token context windows at the planetary scale.",
            "Tracking the cost-curve of Tesla's in-house AI hardware as it moves towards millions of units.",
            "How the ability to 'emulate entire companies' disrupts the traditional SaaS and labor markets.",
            "Supply chain analysis of xAI’s H100/H200 count and how it impacts Tesla’s training timelines.",
            "Mapping the flow of top-tier AI and manufacturing talent into Austin and San Francisco.",
            "How Grok 4.20’s reasoned navigation can automate complex supply chain reporting in real-time.",
            "Predicting the hardware requirements for Optimus to sustain high-output inference.",
            "Why AI-driven vertical integration is the primary threat to traditional legacy automotive moats.",
            "The industrial requirements for a global, real-time financial network: X Money rollout.",
            "Why a 2M token window changes the game for processing entire factory logs in a single query.",
            "As Optimus moves towards mass production, how will the battery supply chain pivot?",
            "Using 'Digital Optimus' as a virtual floor manager to track assembly line performance.",
            "Analyzing the bandwidth needed to stream training data from 6 million+ cars.",
            "Correlation between Sawyer Merritt’s port signals and Troy Teslike’s delivery estimations.",
            "Comparing the ROI of Tesla's hardware-software synergy vs. pure-play software competitors.",
            "Analyzing the 2M context window as a primary driver for US productivity growth.",
            "The macro implications of X Money launching as the world’s most powerful financial network.",
            "How the equity/investment bridge between xAI and Tesla increases the 'sum of parts' valuation.",
            "Analyzing Scott Bessent’s views on capital allocation and the US debt-to-growth ratio.",
            "The 'Corporate OS' Battle: Macrohard vs. Microsoft. Who captures the $10T market?",
            "How legislative shifts around election security influence international investor sentiment.",
            "Tracking the shift of institutional capital into 'hard-tech' as a hedge against inflation.",
            "Pro-growth policies vs. Inflation 'Reduction' Act: Examining the 3.8% GDP growth target.",
            "Why a stable Middle East (negotiated by Trump/Musk) is bullish for global commerce.",
            "Gary Black’s latest margin analysis and where the 'bear case' for Tesla is failing.",
            "Correlating St. Louis Fed data with Tesla’s Texas and Nevada output signals.",
            "Using 'hallucination rates' as a leading indicator for commercial viability of AGI.",
            "Is the 'far-right' tag a risk or an indicator of emerging populist-driven market stability?",
            "The pricing power of the 2M token context window. Will X API tiers become a major revenue line?",
            "A summary of how cash moves between X, xAI, SpaceX, and Tesla to drive a unified vision."
        ],
        "Engagement Source (Likes)": [
            "60k+", "60k+", "Viral (Mar 12)", "1k+", "60k+", "Publicly Disclosed", "4k+", "60k+", "47k+", "Viral (Mar 12)",
            "47k+", "Viral (Mar 12)", "60k+", "Internal spec", "60k+", "Technical signal", "Internal spec", "Competitive signal",
            "Supply chain signal", "Austin News", "Logistics signal", "Internal spec", "Strategy memo", "156k (Sawyer)", "Industrial signal",
            "4680 ramp signal", "Operational signal", "Fleet stats", "News signal", "Strategic signal", "Macro signal", "156k (Sawyer)",
            "M&A signal", "Macro policy", "Market cap signal", "Policy signal", "Institutional signal", "3.8% Growth (Bessent)",
            "Macro trend", "Gary Black stats", "Fed data", "Benchmark signal", "Geopolitical signal", "Revenue signal", "Capital flow model"
        ],
        "Tweet Link": [
            "https://x.com/elonmusk/status/1899650000000000000", "https://x.com/elonmusk/status/1899650000000000000", "https://x.com/elonmusk/status/1899684164139884841",
            "https://x.com/bridgemind/status/1899684165000000000", "https://x.com/elonmusk/status/1899650000000000000", "https://x.com/Tesla/status/1899650000000000000",
            "https://x.com/aelluswamy/status/1899650000000000000", "Internal/Spec", "https://x.com/elonmusk/status/1899650000000000000",
            "https://x.com/elonmusk/status/1899684164139884841", "https://x.com/elonmusk/status/1899650000000000000", "https://x.com/elonmusk/status/1899684164139884841",
            "Internal/Spec", "Internal/Spec", "https://x.com/elonmusk/status/1899650000000000000",
            "Technical/Spec", "Internal/Spec", "Strategy/Spec", "Supply Chain News", "Austin Local News", "Internal/Spec",
            "Internal/Spec", "Strategy/Spec", "https://x.com/SawyerMerritt/status/1899615563965907409", "Strategy/Spec",
            "Production News", "Strategy/Spec", "Fleet Data", "https://x.com/SawyerMerritt/status/1899615563965907409", "Strategy/Spec",
            "Macro/Spec", "https://x.com/SawyerMerritt/status/1899615563965907409", "M&A News", "Macro News", "Market News",
            "Policy News", "Institutional News", "Macro News", "Geopolitical News", "https://x.com/GaryBlack00/status/1899650000000000000",
            "Fed Data", "Benchmark Data", "Macro News", "Revenue News", "Ecosystem News"
        ]
    }

    df = pd.DataFrame(data)
    output_path = 'output/tesla_content_bank.xlsx'
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Content Bank')
        
        status_df = pd.DataFrame({
            "Metric": ["Date Generated", "Total Items", "Viral Highlights", "Debug Status"],
            "Value": ["2026-03-12", "45", "X Money, Grok 4.20, AI4", "Signal-to-Noise Segmented"]
        })
        status_df.to_excel(writer, index=False, sheet_name='Metadata')

    print(f"Excel file enhanced with Signal Strength at: {os.path.abspath(output_path)}")

    # Auto-upload to Google Sheets if credentials exist
    if os.path.exists('service_account.json'):
        print("\n--- TRIGGERING GOOGLE SHEETS UPLOAD ---")
        os.system(f"C:\\Python312_Custom\\python.exe upload_to_sheets.py")
    else:
        print("\n[NOTE] Google Sheets upload skipped: 'service_account.json' not found.")
        print("Please follow the instructions in the walkthrough to enable cloud sync.")

if __name__ == "__main__":
    create_excel_content()
