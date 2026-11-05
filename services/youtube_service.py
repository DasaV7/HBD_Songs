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
    """
    Create a clear, high-contrast, attractive YouTube thumbnail
    """
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import random
    import os

    width, height = 1280, 720

    # ========== 1. Create a clean gradient background ==========
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Nice purple → deep blue gradient
    for y in range(height):
        r = int(70 + (y / height) * 50)
        g = int(30 + (y / height) * 40)
        b = int(120 + (y / height) * 80)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # ========== 2. Soft glowing orbs (elegant bokeh) ==========
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    colors = [
        (255, 105, 180, 50),   # pink
        (255, 215, 0, 45),     # gold
        (186, 85, 211, 40),    # purple
        (255, 255, 255, 30),   # white
    ]

    for _ in range(12):
        x = random.randint(50, width - 50)
        y = random.randint(50, height - 50)
        radius = random.randint(60, 140)
        color = random.choice(colors)
        overlay_draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=color
        )

    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ========== 3. Load large bold fonts ==========
    try:
        font_large = ImageFont.truetype("assets/fonts/Poppins-Bold.ttf", 120)
        font_medium = ImageFont.truetype("assets/fonts/Poppins-SemiBold.ttf", 48)
    except:
        try:
            font_large = ImageFont.truetype("assets/fonts/Montserrat-Bold.ttf", 120)
            font_medium = ImageFont.truetype("assets/fonts/Montserrat-SemiBold.ttf", 48)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()

    # ========== 4. Main Text ==========
    main_text = f"Happy Birthday\n{name}!"

    # Strong multi-layer shadow for maximum readability
    shadow_color = (0, 0, 0)
    for i in range(8, 0, -1):
        draw.multiline_text(
            ((width - 700) // 2 + i, 160 + i),
            main_text,
            font=font_large,
            fill=shadow_color,
            align="center",
            spacing=12
        )

    # Bright gold text
    draw.multiline_text(
        ((width - 700) // 2, 160),
        main_text,
        font=font_large,
        fill="#FFD700",
        align="center",
        spacing=12
    )

    # ========== 5. Bottom banner ==========
    draw.rectangle([0, 580, width, 720], fill=(0, 0, 0, 180))

    # Banner text
    banner_text = "Elegant Birthday Video  •  4K"
    try:
        bbox = draw.textbbox((0, 0), banner_text, font=font_medium)
        text_width = bbox[2] - bbox[0]
    except:
        text_width = 500

    draw.text(
        ((width - text_width) // 2, 615),
        banner_text,
        font=font_medium,
        fill="white"
    )

    # ========== 6. Small decorative circles ==========
    draw.ellipse([60, 60, 130, 130], fill="#FF69B4")
    draw.ellipse([width - 150, 70, width - 80, 140], fill="#FFD700")

    # Save
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
