# Influencer Discovery: Gravity + Intersection

## Overview
A assumption-free discovery pipeline to identify top finance/Tesla influencers by observing network "gravity" (incoming engagement) and expanding via institutional "intersections" (who the experts follow).

## Discovery Stages

### 1. Gravity Seed Discovery
- **Action**: Search for high-engagement tweets using keywords (`Tesla`, `$TSLA`, `Macro Finance`).
- **Logic**: Use `scripts/find_hot_tweets.py` (already implemented) to identify "Heat Spots" in the conversation.
- **Goal**: Identify the 5-10 most viral accounts in the last 24-48 hours.

### 2. Engagement Traversal (The Harvester)
- **Action**: Scrape all unique "Engagers" (replies, quotes, retweets) from the seeds identified in Stage 1.
- **Logic**: Use the existing `harvest.py` logic but optimized for discovery (filtering for accounts with >5k-10k followers).
- **Goal**: Build a raw candidate pool of active participants.

### 3. Profile Expansion (The Whale Intersection)
- **Action**: Take the top 5 candidates from Stage 2. Fetch their "Following" lists.
- **Logic**: Find the overlapping accounts (intersection). If Account A, B, and C all follow Account X, then Account X is a high-probability "Hidden Whale".
- **Goal**: Discover the "Institutional" tier of influencers that may not be viral but are highly respected.

## Technical Components

### `scripts/discover_influencers.py`
The orchestration script that ties these stages together.
- Inputs: Keywords, Min-Follower Threshold.
- Outputs: `data/discovery/influencer_report.json`.

### Data Flow
1. **Search** -> `Hot Tweets`
2. **Harvest** -> `Candidate Pool`
3. **Filter** -> `Top Candidates`
4. **Intersect** -> `Final Influencer List`

## Next Steps
1. Create `docs/plans/2026-03-12-influencer-discovery-implementation.md`.
2. Implement Stage 2 & 3 scripts.
3. Run the first full-cycle discovery scan.
