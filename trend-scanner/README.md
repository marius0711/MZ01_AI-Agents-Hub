# Trend Scanner (Reddit MVP)

A minimal MVP for daily trend scanning and content ideation based on Reddit data.

Ingests recent Reddit posts from selected subreddits, stores them in SQLite, and generates a daily Markdown digest.

## Status

✅ End-to-end pipeline (Reddit → SQLite → Digest.md)
✅ OAuth-free Reddit ingestion via public JSON endpoints
✅ Data persistence with de-duplication
✅ Daily Markdown digest generation

## Data Model

Stored in `data/trend_scanner.sqlite`:
- subreddit, author, title, body
- score, number_of_comments
- creation timestamp, Reddit permalink

## Project Structure

```
trend-scanner/
├─ scripts/run_daily.py
├─ src/trend_scanner/
│  ├─ config/
│  ├─ db/
│  ├─ ingest/
│  └─ delivery/
├─ data/
└─ out/
```

## Usage

```bash
source ../.venv/bin/activate
python scripts/run_daily.py
```

Output: `out/digest.md`

## Configuration

Set in `trend-scanner/.env`:
```
REDDIT_USER_AGENT=trend-scanner-mvp/0.1 by <username>
SUBREDDITS=Fitness,Running,nutrition
POST_LIMIT=50
```

## Known Limitations

- No OAuth / private API access
- No topic clustering or trend velocity analysis
- No content gap detection or dashboard

## Slack Channel

https://app.slack.com/client/T0A9SPEUBRB/D0AAQFE6T88

✅ Weekly PDF digest with private Slack delivery (DM + threaded highlights)

## Next Steps

- Implement topic clustering for trend velocity analysis
- Add content gap detection across subreddits
- Build dashboard for digest visualization
- Integrate OAuth for private subreddit access

