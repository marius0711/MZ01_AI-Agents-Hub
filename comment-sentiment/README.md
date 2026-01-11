# Creator Community Sentiment Monitor (MVP)
## What problem does this solve?

Creators often rely on:
- gut feeling
- a few loud comments
- sporadic manual reading

This leads to:
- overreacting to isolated criticism
- missing slow sentiment shifts
- unnecessary uncertainty

This tool provides:
- structured, explainable insights
- without dashboards
- without black-box AI judgments
- a few loud comments
- sporadic manual reading

This leads to:
- overreacting to isolated criticism
- missing slow sentiment shifts
- unnecessary uncertainty

This tool provides:
- structured, explainable insights
- without dashboards
- without black-box AI judgments

---

## Core idea

The system separates **reading** from **judging**:

- **AI (Claude)** is only used to classify individual comments
- All insights, scores and recommendations are derived from **deterministic logic**

This makes the output:
- explainable
- reproducible
- trustworthy

---

## What the system does

1. Fetches YouTube comments for a channel (last X days)
2. Annotates each comment with:
   - sentiment
   - intent
   - emotion intensity
   - abstract topics
3. Aggregates results over time
4. Computes simple, explainable metrics:
   - sentiment ratios
   - intent shifts
   - topic repetition
   - escalation indicator
5. Generates a **one-page decision-oriented report**

---

## Example output

The final output is a short report answering questions like:

- Is the community stable or changing?
- Is criticism fragmented or focused on one topic?
- Is there a need to react — or is observation enough?

The report always includes:
- a clear status (stable / watch / critical)
- a recommendation
- the numbers used to justify that recommendation

---

## Visual output

The system generates minimal visualizations to support interpretation of community feedback:

- **Sentiment trend** (`sentiment_trend.png`):  
  Shows the weekly share of positive, neutral, and negative top-level comments over time. Helps track overall mood and detect shifts in community sentiment.

- **Intent shift** (`intent_shift.png`):  
  Illustrates how the type of comments (supportive, neutral discussion, critical) evolves week by week. Supports understanding of changing community focus or priorities.

Both graphics are stored in `/output` and embedded in the final report for easy reference.

---

## Project structure

```bash
comment-sentiment/
├── data/
│   ├── raw_comments.json
│   ├── annotated_comments.json
│   └── aggregated_metrics.json
├── scripts/
│   ├── fetch_comments.py
│   ├── annotate_comments.py
│   ├── compute_metrics.py
│   ├── plot_sentiment_trend.py
│   └── plot_intent_shift.py
├── generate_report.py
├── output/
│   ├── report_*.md
│   ├── sentiment_trend.png
│   └── plot_intent_shift.png 
└── README.md
```

---

## Requirements

This project uses a small set of dependencies:

anthropic
pandas
matplotlib
tqdm
python-dateutil


Install via:
```bash
pip install -r requirements.txt
```
---

## How to run (MVP)

1. Fetch comments

```bash
python scripts/fetch_comments.py
```

2. Annotate comments (Claude API required)

```bash
python scripts/annotate_comments.py
```
3. Compute metrics

```bash
python scripts/compute_metrics.py
```

4. Generate sentiment trend graphic

```bash
python scripts/plot_sentiment_trend.py
python scripts/plot_intent_shift.py
```

5. Generate report

```bash
python generate_report.py
```
---

Current limitations (by design)
- Only top-level comments (no replies)
- No real-time monitoring
- No dashboards
- No cross-platform support