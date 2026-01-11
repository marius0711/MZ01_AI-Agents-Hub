# Creator Community Sentiment Monitor – Quick Start

This one-pager explains how to use the tool **end-to-end** – from raw data to the decision report.

---

## Prerequisites

- **Python ≥ 3.10**
- API Keys:
    - YouTube Data API v3
    - Anthropic (Claude)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configuration (config.py)
```python
YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"
CHANNEL_HANDLE = "YOUR_CHANNEL_HANDLE"
CLAUDE_API_KEY = "YOUR_CLAUDE_API_KEY"
```

### Optional Adjustments (MVP-Limits)
```python
DAYS_BACK = 90
MAX_VIDEOS = 50
MAX_COMMENTS = 1000
BATCH_SIZE = 25
```

### Recommended Usage Flow (End-to-End)
1️⃣ Fetch Comments
```bash
python scripts/fetch_comments.py
```
**Result**
```bash
data/raw_comments.json
```
**Properties**
- Only top-level comments
- Time-limited
- Intentionally capped (MVP-safe)

2️⃣ Annotate Comments (AI reads, does not judge)
```bash
python scripts/annotate_comments.py
```
**Result**
```bash
data/annotated_comments.json
```
**Features**
- Batch processing
- Crash-resistant (intermediate storage)
- Resumable
- Deterministic (temperature=0)
- Conservative classification (neutrality in uncertainty)

The AI classifies, it does not evaluate.

3️⃣ Calculate Metrics (deterministic)
```bash
python scripts/compute_metrics.py
```
**Result**
```bash
data/aggregated_metrics.json
```
➡️ The central decision artifact (all trends, shares, escalation signals)

4️⃣ Generate Visualization
```bash
python scripts/plot_sentiment_trend.py
python scripts/plot_intent_shift.py
```
**Result**
```bash
output/sentiment_trend.png
output/intent_shift.png
```
Minimal, explanatory, supportive – no dashboards.

5️⃣ Generate Decision Report
```bash
python generate_report.py
```
**Result**
```bash
output/report_<channel>_YYYY-MM-DD.md
```
➡️ The actual product

The report includes:
- Clear classification: stable / noteworthy / critical
- Concrete recommendation
- Transparent justification based on the numbers
- Visual support

### Usage Recommendation
Run once a week or month.

Focus on the report, not on individual comments.


### Glossary – Key Terms

**Status / Classification**
Indicates community stability:
- **Stable**: No anomalies detected
- **Noteworthy**: Elevated attention recommended
- **Critical**: Active intervention recommended

**Recommendation**
Action suggestion based on status: monitor or respond actively.

**Negative Comment Share**
Percentage of all comments classified as negative.
~17% → typical baseline for this channel.

**Avg. Emotional Intensity (Negative)**
Measures emotional strength of negative comments (0 = neutral, 1 = highly emotional).

**Escalation Indicator**
Tracks sentiment trajectory:
- **Trending up**: negative sentiment increasing
- **Stable**: no significant change
- **Trending down**: negative sentiment decreasing

**Low** (<0.1) → Normal, no action required
**Medium** (0.1–0.2) → Worthy of attention, consider monitoring community sentiment
**High** (>0.2) → Critical, active intervention recommended

