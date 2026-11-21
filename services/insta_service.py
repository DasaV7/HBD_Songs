# services/insta_service.py

import os
import time
import requests
import streamlit as st


def _get_instagram_credentials():
    """Load Instagram credentials from Streamlit secrets."""
    try:
        access_token = st.secrets["instagram"]["ACCESS_TOKEN"]
        ig_user_id = st.secrets["instagram"]["IG_USER_ID"]
        return access_token, ig_user_id
    except Exception as e:
        raise Exception(
            "Instagram secrets missing. "
            "Please add [instagram] ACCESS_TOKEN and IG_USER_ID in Streamlit secrets."
        ) from e


def _wait_for_container(creation_id: str, access_token: str, max_attempts: int = 30):
    """Wait until Instagram finishes processing the media container."""
    url = f"https://graph.facebook.com/v21.0/{creation_id}"
    params = {
        "fields": "status_code",
        "access_token": access_token
    }

    for _ in range(max_attempts):
        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        status = data.get("status_code")
        if status == "FINISHED":
            return True
        if status == "ERROR":
            raise Exception(f"Instagram container error: {data}")

        time.sleep(3)

    raise Exception("Timeout waiting for Instagram media container")


def upload_instagram_post(image_path: str, caption: str) -> str:
    """
    Upload a single image as Instagram Feed Post.
    Returns the permalink of the published post.
    Note: image must be publicly accessible via URL for the simplest method.
    For local files we first need a public URL (see notes below).
    """
    if not os.path.exists(image_path):
        raise Exception(f"Image not found: {image_path}")

    access_token, ig_user_id = _get_instagram_credentials()

    # For production you should upload the image to a public storage
    # (Cloudinary, S3, etc.) and use that URL.
    # Below is the standard Graph API flow assuming you have a public image_url.

    raise Exception(
        "Direct local image upload is not supported by Instagram Graph API.\n"
        "Please host the image on a public URL (Cloudinary / S3 / Imgur) "
        "and pass the public URL instead of local path."
    )


def upload_instagram_reel(video_path: str, caption: str) -> str:
    """
    Upload a Reel using Instagram Graph API.
    Returns the permalink of the published Reel.
    """
    if not os.path.exists(video_path):
        raise Exception(f"Video not found: {video_path}")

    access_token, ig_user_id = _get_instagram_credentials()

    # Instagram requires a publicly accessible video URL
    # or a more complex resumable upload.
    # For Streamlit Cloud the simplest reliable way is:
    # 1. Upload the reel to Cloudinary / S3 / similar
    # 2. Use the returned public URL here

    raise Exception(
        "Direct local video upload for Reels is complex on Streamlit Cloud.\n"
        "Recommended: Upload the reel file to a public storage first, "
        "then use the public URL with the Graph API."
    )


def build_caption(name: str, youtube_link: str) -> str:
    """Create a nice caption that includes the YouTube link."""
    return f"""🎂 Happy Birthday {name}! 🎉

Full video is live on YouTube:
{youtube_link}

Follow for daily birthday videos ❤️
Comment your name below for a shoutout!

#HappyBirthday #{name.replace(" ", "")} #BirthdayReel #BirthdayWishes #hbdsongs
"""