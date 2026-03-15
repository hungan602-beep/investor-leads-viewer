# Design Document: Financial Influencer Discovery (Approach 1)

## Overview
A systematic pipeline to identify and rank financial influencers on X by analyzing engagement on high-signal economic policy posts from @realDonaldTrump.

## Objective
Extract the top 1,000 active engagers (repliers) from a specific "finance-heavy" seed tweet and categorize them based on influence (followers) and professional relevance (bio keywords).

## Seed Selection
- **Source**: @realDonaldTrump
- **Tweet ID**: `2004012442427277591`
- **Topic**: Economic Report (GDP, Stock Market, Tariffs, Inflation).

## Components

### 1. Data Harvesting Module
- **Input**: Tweet ID, limit=1000.
- **Process**: Iterate through top-level replies using `twscrape`.
- **Output**: Raw JSON containing user profiles and reply content.

### 2. Analysis & Scoring Engine
- **Follower Filtering**: focus on users with >5,000 followers.
- **Keyword Matching**:
    - **Primary**: `investor`, `economist`, `macro`, `trader`, `crypto`.
    - **Secondary**: `wealth`, `funds`, `VC`, `stock`, `feds`.
- **Scoring Matrix**:
    - `Base Score = Log10(Followers)`
    - `Bonus +5` for Primary Keyword match.
    - `Bonus +2` for Secondary Keyword match.

### 3. Reporting Utility
- **Format**: CSV for lead generation and JSON for system persistence.
- **Dashboard**: Simple HTML summary for visual verification.

## Error Handling
- **Rate Limits**: Automatic backoff via `twscrape` account rotation.
- **Data Gaps**: Handle null bios or missing metrics gracefully.

## Success Criteria
- Collection of 1,000 unique engagers.
- Identification of at least 50 high-signal influencers (>50k followers + finance keywords).
