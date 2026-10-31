# services/youtube_service.py

import streamlit as st
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from PIL import Image, ImageDraw, ImageFont
import os
import random


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]


def get_youtube_service():
    client_id = st.secrets["YOUTUBE_CLIENT_ID"]
    client_secret = st.secrets["YOUTUBE_CLIENT_SECRET"]
    refresh_token = st.secrets["YOUTUBE_REFRESH_TOKEN"]

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )

    if not creds.valid:
        creds.refresh(Request())

    return build("youtube", "v3", credentials=creds)


def create_thumbnail(name: str, output_path: str = "generated/thumbnail.jpg"):
    """Create a simple but attractive thumbnail automatically"""
    width, height = 1280, 720
    img = Image.new("RGB", (width, height), color=(30, 20, 40))

    # Gradient-like background
    draw = ImageDraw.Draw(img)
    for y in range(height):
        r = int(40 + (y / height) * 40)
        g = int(20 + (y / height) * 30)
        b = int(60 + (y / height) * 50)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Add confetti dots
    for _ in range(60):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(4, 10)
        color = random.choice(["#FF9AA2", "#FFD700", "#FF69B4", "#FFFFFF", "#A0C4FF"])
        draw.ellipse([x, y, x+size, y+size], fill=color)

    # Main text
    try:
        font_large = ImageFont.truetype("assets/fonts/Poppins-Bold.ttf", 90)
        font_small = ImageFont.truetype("assets/fonts/Poppins-SemiBold.ttf", 40)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    text = f"Happy Birthday\n{name}!"
    # Shadow
    draw.multiline_text((width//2 - 280 + 4, 250 + 4), text, font=font_large, fill=(0,0,0), align="center", spacing=10)
    draw.multiline_text((width//2 - 280, 250), text, font=font_large, fill="#FFD700", align="center", spacing=10)

    draw.text((width//2 - 180, 520), "Elegant Birthday Video", font=font_small, fill="white")

    img.save(output_path, quality=95)
    return output_path


def get_or_create_playlist(youtube, title: str, description: str = ""):
    """Get existing playlist or create new one"""
    # Search existing playlists
    request = youtube.playlists().list(part="snippet", mine=True, maxResults=50)
    response = request.execute()

    for item in response.get("items", []):
        if item["snippet"]["title"] == title:
            return item["id"]

    # Create new playlist
    body = {
        "snippet": {
            "title": title,
            "description": description
        },
        "status": {
            "privacyStatus": "public"
        }
    }
    response = youtube.playlists().insert(part="snippet,status", body=body).execute()
    return response["id"]


def add_video_to_playlist(youtube, playlist_id: str, video_id: str):
    body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id
            }
        }
    }
    youtube.playlistItems().insert(part="snippet", body=body).execute()


def upload_video(video_path: str, title: str, description: str = "", name: str = "") -> str:
    try:
        youtube = get_youtube_service()

        # Better title
        final_title = f"Happy Birthday {name}! 🎂 Elegant Birthday Video | 4K Screensaver"[:100]

        # Better description
        final_description = f"""🎈 Happy Birthday {name}! 🎂

Celebrate in style with this elegant personalized Happy Birthday video for {name}.
Perfect as a birthday party background, TV screensaver, or heartfelt birthday wish.

✨ Perfect for:
• Birthday parties & home celebrations
• TV displays & event venues
• Restaurants & cafés
• Family gatherings

This video was created with love using AI.

If you enjoy this video, please Like 👍, Subscribe 🔔 and share it!

Thank you for watching and Happy Birthday {name}! 🎉💖

#HappyBirthday #HappyBirthday{name.replace(" ", "")} #BirthdayVideo #BirthdayWishes #BirthdayScreensaver #4KBirthday #PartyDecor #BirthdayBackground #BirthdayCelebration
"""

        body = {
            "snippet": {
                "title": final_title,
                "description": final_description,
                "tags": [
                    "Happy Birthday", f"Happy Birthday {name}", "Birthday Video",
                    "Birthday Wishes", "Birthday Screensaver", "4K Birthday",
                    "Party Decor", "Birthday Background", "Elegant Birthday",
                    "Birthday Celebration", "Birthday Song"
                ],
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=5*1024*1024)

        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                st.write(f"Upload progress: {int(status.progress() * 100)}%")

        video_id = response["id"]

        # ===== Auto Thumbnail =====
        try:
            thumb_path = create_thumbnail(name)
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumb_path)
            ).execute()
            st.write("Thumbnail uploaded successfully")
        except Exception as e:
            st.write(f"Thumbnail skipped: {e}")

        # ===== Add to Playlists =====
        try:
            playlist1 = get_or_create_playlist(youtube, "Happy Birthday Videos 2025", "Collection of elegant birthday videos")
            playlist2 = get_or_create_playlist(youtube, "Elegant Birthday Screensavers", "Beautiful birthday screensaver videos")

            add_video_to_playlist(youtube, playlist1, video_id)
            add_video_to_playlist(youtube, playlist2, video_id)
            st.write("Added to playlists")
        except Exception as e:
            st.write(f"Playlist error: {e}")

        return f"https://www.youtube.com/watch?v={video_id}"

    except HttpError as e:
        raise Exception(f"YouTube API error: {e}")
    except Exception as e:
        raise Exception(f"Upload failed: {str(e)}")
