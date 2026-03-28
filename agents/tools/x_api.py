"""X (Twitter) API client using tweepy for OAuth 1.0a."""

from __future__ import annotations
import tweepy
import base64
import httpx
from config import X_CONSUMER_KEY, X_CONSUMER_SECRET, X_BEARER_TOKEN, X_CALLBACK_URL


def _get_client(access_token: str, access_token_secret: str) -> tweepy.Client:
    return tweepy.Client(
        bearer_token=X_BEARER_TOKEN,
        consumer_key=X_CONSUMER_KEY,
        consumer_secret=X_CONSUMER_SECRET,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )


def _get_api_v1(access_token: str, access_token_secret: str) -> tweepy.API:
    """API v1.1 client (needed for media upload)."""
    auth = tweepy.OAuth1UserHandler(
        X_CONSUMER_KEY, X_CONSUMER_SECRET, access_token, access_token_secret
    )
    return tweepy.API(auth)


# --- OAuth flow ---

def get_request_token() -> dict:
    """Step 1: Get request token for OAuth flow."""
    oauth_handler = tweepy.OAuth1UserHandler(
        X_CONSUMER_KEY, X_CONSUMER_SECRET, callback=X_CALLBACK_URL
    )
    redirect_url = oauth_handler.get_authorization_url()
    request_token = oauth_handler.request_token["oauth_token"]
    request_token_secret = oauth_handler.request_token["oauth_token_secret"]
    return {
        "redirect_url": redirect_url,
        "request_token": request_token,
        "request_token_secret": request_token_secret,
    }


def exchange_verifier_for_tokens(
    request_token: str,
    request_token_secret: str,
    oauth_verifier: str,
) -> dict:
    """Step 2: Exchange verifier for access tokens."""
    oauth_handler = tweepy.OAuth1UserHandler(X_CONSUMER_KEY, X_CONSUMER_SECRET)
    oauth_handler.request_token = {
        "oauth_token": request_token,
        "oauth_token_secret": request_token_secret,
    }
    access_token, access_token_secret = oauth_handler.get_access_token(oauth_verifier)

    # Get user info
    api = _get_api_v1(access_token, access_token_secret)
    user = api.verify_credentials()

    return {
        "access_token": access_token,
        "access_token_secret": access_token_secret,
        "screen_name": user.screen_name,
        "user_id": str(user.id),
    }


# --- Publishing ---

async def post_tweet(
    text: str,
    media_ids: list[str] | None = None,
    reply_to_id: str | None = None,
    access_token: str | None = None,
    access_token_secret: str | None = None,
) -> str:
    """Post a single tweet. Returns tweet ID."""
    if not access_token or not access_token_secret:
        raise ValueError("X access tokens required for posting")

    client = _get_client(access_token, access_token_secret)

    kwargs: dict = {"text": text}
    if media_ids:
        kwargs["media_ids"] = media_ids
    if reply_to_id:
        kwargs["in_reply_to_tweet_id"] = reply_to_id

    response = client.create_tweet(**kwargs)
    return str(response.data["id"])


async def post_thread(
    tweets: list[str],
    access_token: str | None = None,
    access_token_secret: str | None = None,
) -> list[str]:
    """Post a thread. Returns list of tweet IDs."""
    if not access_token or not access_token_secret:
        raise ValueError("X access tokens required")

    client = _get_client(access_token, access_token_secret)
    tweet_ids = []
    reply_to_id = None

    for tweet_text in tweets:
        kwargs: dict = {"text": tweet_text}
        if reply_to_id:
            kwargs["in_reply_to_tweet_id"] = reply_to_id

        response = client.create_tweet(**kwargs)
        tweet_id = str(response.data["id"])
        tweet_ids.append(tweet_id)
        reply_to_id = tweet_id

    return tweet_ids


async def upload_media(
    image_data: str,
    access_token: str | None,
    access_token_secret: str | None,
) -> str | None:
    """Upload media to X. image_data can be URL or base64 data URI."""
    if not access_token or not access_token_secret:
        return None

    try:
        api = _get_api_v1(access_token, access_token_secret)

        if image_data.startswith("data:"):
            # Base64 data URI
            header, b64_data = image_data.split(",", 1)
            image_bytes = base64.b64decode(b64_data)

            import tempfile, os
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(image_bytes)
                tmp_path = f.name

            media = api.media_upload(filename=tmp_path)
            os.unlink(tmp_path)
        else:
            # Download from URL first
            async with httpx.AsyncClient() as client:
                resp = await client.get(image_data)
                image_bytes = resp.content

            import tempfile, os
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(image_bytes)
                tmp_path = f.name

            media = api.media_upload(filename=tmp_path)
            os.unlink(tmp_path)

        return str(media.media_id)
    except Exception as e:
        print(f"Media upload error: {e}")
        return None


async def schedule_tweet(
    text: str,
    scheduled_at: str,
    access_token: str | None,
    access_token_secret: str | None,
) -> str | None:
    """Note: X API free tier doesn't support scheduling. Posts immediately."""
    return await post_tweet(text, access_token=access_token, access_token_secret=access_token_secret)
