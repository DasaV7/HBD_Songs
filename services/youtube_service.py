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
    """iOS pastel style thumbnail with birthday celebration elements"""
    from PIL import Image, ImageDraw, ImageFont
    import random
    import os

    width, height = 1280, 720

    # ========== iOS Pastel Gradient Background ==========
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Soft pastel gradient (pink → peach → lavender)
    for y in range(height):
        ratio = y / height
        r = int(255 - ratio * 40)
        g = int(220 - ratio * 60)
        b = int(230 - ratio * 30)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # ========== Soft decorative circles (iOS style) ==========
    pastel_colors = [
        (255, 182, 193, 90),   # light pink
        (255, 218, 185, 80),   # peach
        (221, 160, 221, 70),   # plum
        (176, 224, 230, 80),   # powder blue
        (255, 255, 224, 70),   # light yellow
    ]

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    for _ in range(14):
        x = random.randint(0, width)
        y = random.randint(0, height)
        radius = random.randint(50, 160)
        color = random.choice(pastel_colors)
        overlay_draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color)

    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ========== Load Bold Font ==========
    font_main = None
    font_banner = None

    for path in ["assets/fonts/Poppins-Bold.ttf", "assets/fonts/Montserrat-Bold.ttf"]:
        try:
            font_main = ImageFont.truetype(path, 125)
            font_banner = ImageFont.truetype(path, 46)
            break
        except:
            continue

    if font_main is None:
        font_main = ImageFont.load_default()
        font_banner = ImageFont.load_default()

    # ========== Main Text ==========
    line1 = "Happy Birthday"
    line2 = f"{name}!"

    def get_size(text, font):
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except:
            return 500, 80

    w1, h1 = get_size(line1, font_main)
    w2, h2 = get_size(line2, font_main)

    x1 = (width - w1) // 2
    x2 = (width - w2) // 2
    y1 = 190
    y2 = y1 + h1 + 15

    # Soft shadow
    for i in range(6, 0, -1):
        draw.text((x1 + i, y1 + i), line1, font=font_main, fill=(80, 40, 60))
        draw.text((x2 + i, y2 + i), line2, font=font_main, fill=(80, 40, 60))

    # Beautiful text color
    draw.text((x1, y1), line1, font=font_main, fill="#FF6B8B")      # soft pink
    draw.text((x2, y2), line2, font=font_main, fill="#FF6B8B")

    # ========== Birthday Icons (simple shapes) ==========
    # Cake
    draw.rectangle([110, 480, 190, 560], fill="#FFB6C1")
    draw.rectangle([120, 450, 180, 480], fill="#FFF0F5")
    draw.ellipse([130, 430, 170, 455], fill="#FF69B4")

    # Balloon 1
    draw.ellipse([1050, 420, 1130, 520], fill="#FF69B4")
    draw.line([1090, 520, 1090, 580], fill="#FF69B4", width=3)

    # Balloon 2
    draw.ellipse([980, 450, 1050, 540], fill="#87CEFA")
    draw.line([1015, 540, 1015, 590], fill="#87CEFA", width=3)

    # Confetti dots
    for _ in range(25):
        x = random.randint(50, width-50)
        y = random.randint(50, 650)
        size = random.randint(6, 12)
        color = random.choice(["#FF69B4", "#FFD700", "#87CEFA", "#FFA07A", "#DDA0DD"])
        draw.ellipse([x, y, x+size, y+size], fill=color)

    # ========== Bottom Banner ==========
    draw.rectangle([0, 610, width, 720], fill=(255, 255, 255, 220))
    
    banner = "Elegant Birthday Video  •  4K"
    bw, bh = get_size(banner, font_banner)
    draw.text(((width - bw) // 2, 645), banner, font=font_banner, fill="#FF6B8B")

    os.makedirs("generated", exist_ok=True)
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
