# services/insta_service.py

import time
import requests
import streamlit as st
from datetime import datetime

# Re-use your existing Cloudinary helpers
from services.cloudinary_service import (   # or whatever you named the file
    upload_reel_to_cloudinary,
    upload_post_to_cloudinary
)


def _get_ig_credentials():
    try:
        return (
            st.secrets["instagram"]["ACCESS_TOKEN"],
            st.secrets["instagram"]["IG_USER_ID"]
        )
    except Exception:
        raise Exception(
            "Missing Instagram secrets. "
            "Add [instagram] ACCESS_TOKEN and IG_USER_ID"
        )


def _wait_until_finished(creation_id: str, access_token: str, max_tries: int = 40):
    url = f"https://graph.facebook.com/v21.0/{creation_id}"
    params = {"fields": "status_code", "access_token": access_token}

    for _ in range(max_tries):
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        status = data.get("status_code")

        if status == "FINISHED":
            return True
        if status == "ERROR":
            raise Exception(f"Instagram processing error: {data}")

        time.sleep(4)

    raise Exception("Timeout waiting for Instagram media container")


def publish_instagram_reel(video_public_url: str, caption: str) -> str:
    """
    Publish a Reel using a public video URL (from Cloudinary).
    Returns the Instagram permalink.
    """
    access_token, ig_user_id = _get_ig_credentials()

    # 1. Create container
    create_url = f"https://graph.facebook.com/v21.0/{ig_user_id}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_public_url,
        "caption": caption,
        "share_to_feed": "true",
        "access_token": access_token
    }

    r = requests.post(create_url, data=payload, timeout=60)
    data = r.json()

    if "id" not in data:
        raise Exception(f"Failed to create Reel container: {data}")

    creation_id = data["id"]

    # 2. Wait until Instagram finishes processing
    _wait_until_finished(creation_id, access_token)

    # 3. Publish
    publish_url = f"https://graph.facebook.com/v21.0/{ig_user_id}/media_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": access_token
    }

    r2 = requests.post(publish_url, data=publish_payload, timeout=30)
    pub_data = r2.json()

    if "id" not in pub_data:
        raise Exception(f"Failed to publish Reel: {pub_data}")

    media_id = pub_data["id"]

    # 4. Get permalink
    permalink_url = f"https://graph.facebook.com/v21.0/{media_id}"
    r3 = requests.get(
        permalink_url,
        params={"fields": "permalink", "access_token": access_token},
        timeout=20
    )
    return r3.json().get("permalink", f"https://www.instagram.com/reel/{media_id}/")


def publish_instagram_post(image_public_url: str, caption: str) -> str:
    """
    Publish a single image post using a public image URL.
    Returns the Instagram permalink.
    """
    access_token, ig_user_id = _get_ig_credentials()

    # 1. Create container
    create_url = f"https://graph.facebook.com/v21.0/{ig_user_id}/media"
    payload = {
        "image_url": image_public_url,
        "caption": caption,
        "access_token": access_token
    }

    r = requests.post(create_url, data=payload, timeout=30)
    data = r.json()

    if "id" not in data:
        raise Exception(f"Failed to create Post container: {data}")

    creation_id = data["id"]

    # 2. Publish (images are usually ready immediately)
    publish_url = f"https://graph.facebook.com/v21.0/{ig_user_id}/media_publish"
    r2 = requests.post(
        publish_url,
        data={"creation_id": creation_id, "access_token": access_token},
        timeout=30
    )
    pub_data = r2.json()

    if "id" not in pub_data:
        raise Exception(f"Failed to publish Post: {pub_data}")

    media_id = pub_data["id"]

    # 3. Get permalink
    r3 = requests.get(
        f"https://graph.facebook.com/v21.0/{media_id}",
        params={"fields": "permalink", "access_token": access_token},
        timeout=20
    )
    return r3.json().get("permalink", "")


def build_caption(name: str, youtube_link: str) -> str:
    return f"""🎂 Happy Birthday {name}! 🎉

Full video is live on YouTube:
{youtube_link}

Follow for daily birthday videos ❤️
Comment your name below!

#HappyBirthday #{name.replace(" ", "")} #BirthdayReel #BirthdayWishes
"""