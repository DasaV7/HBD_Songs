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
    """High-visibility thumbnail with large text"""
    from PIL import Image, ImageDraw, ImageFont
    import os

    width, height = 1280, 720

    # Solid rich purple background
    img = Image.new("RGB", (width, height), color=(75, 0, 130))
    draw = ImageDraw.Draw(img)

    # Soft gradient
    for y in range(height):
        r = int(90 + (y / height) * 40)
        g = int(20 + (y / height) * 30)
        b = int(140 + (y / height) * 50)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Load the largest possible font
    font_main = None
    font_sub = None

    for size in [140, 130, 120, 110]:
        try:
            font_main = ImageFont.truetype("assets/fonts/Poppins-Bold.ttf", size)
            break
        except:
            continue

    try:
        font_sub = ImageFont.truetype("assets/fonts/Poppins-SemiBold.ttf", 48)
    except:
        pass

    if font_main is None:
        font_main = ImageFont.load_default()
    if font_sub is None:
        font_sub = ImageFont.load_default()

    # ========== MAIN TEXT ==========
    line1 = "Happy Birthday"
    line2 = name + "!"

    # Calculate center position
    def get_text_size(text, font):
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except:
            return 400, 80

    w1, h1 = get_text_size(line1, font_main)
    w2, h2 = get_text_size(line2, font_main)

    x1 = (width - w1) // 2
    x2 = (width - w2) // 2
    y1 = 180
    y2 = y1 + h1 + 20

    # Strong black shadow
    for offset in range(6, 0, -1):
        draw.text((x1 + offset, y1 + offset), line1, font=font_main, fill=(0, 0, 0))
        draw.text((x2 + offset, y2 + offset), line2, font=font_main, fill=(0, 0, 0))

    # Bright gold text
    draw.text((x1, y1), line1, font=font_main, fill="#FFD700")
    draw.text((x2, y2), line2, font=font_main, fill="#FFD700")

    # ========== BOTTOM BANNER ==========
    draw.rectangle([0, 600, width, 720], fill=(0, 0, 0))

    banner = "Elegant Birthday Video  •  4K"
    bw, bh = get_text_size(banner, font_sub)
    draw.text(((width - bw) // 2, 640), banner, font=font_sub, fill="white")

    # Decorative circles
    draw.ellipse([50, 50, 140, 140], fill="#FF69B4")
    draw.ellipse([width-160, 60, width-60, 160], fill="#FFD700")

    os.makedirs(os.path.dirname(output_path) or "generated", exist_ok=True)
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
            #thumb_path = create_thumbnail(name)
            
            safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).replace(" ", "_")
            thumb_path = create_thumbnail(name, output_path=f"generated/{safe_name}_thumbnail.jpg")
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
