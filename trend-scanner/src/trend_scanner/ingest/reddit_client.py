import praw


def make_reddit(client_id: str, client_secret: str, user_agent: str) -> praw.Reddit:
    if not client_id or not client_secret or not user_agent:
        raise ValueError(
            "Missing Reddit credentials. Check .env: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT"
        )

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
