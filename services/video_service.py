import streamlit as st
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_youtube_service():
    """Create authenticated YouTube service using Streamlit secrets."""
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


def create_description(name: str, custom_message: str = "") -> str:
    """Generate a professional YouTube description."""
    
    description = f"""🎈 Happy Birthday {name}! 🎂

Celebrate in style with this beautiful personalized Happy Birthday video created just for {name}. Featuring elegant décor, balloons, candles, flowers and a joyful birthday atmosphere.

"""

    if custom_message.strip():
        description += f"💌 Special Message:\n{custom_message}\n\n"

    description += """✨ Perfect for:
• Birthday parties
• Home celebrations
• Event venues
• TV displays
• Restaurants & cafés
• Family gatherings
• Background décor

This video was specially generated with love using AI.

If you enjoy this video, please Like 👍, Subscribe 🔔, and turn on the notification bell for more personalized birthday videos!

Thank you for watching and Happy Birthday {name}! 🎉💖

#HappyBirthday #BirthdayVideo #HappyBirthday{name} #BirthdayWish #BirthdayGreeting #PersonalizedBirthday #BirthdayCelebration #PartyDecor #4K #BirthdayDecor #CelebrationVideo #BirthdayParty #ElegantBirthday
""".format(name=name)

    return description


def upload_video(video_path: str, title: str, description: str = "", name: str = "") -> str:
    """
    Upload video to YouTube with professional description and tags.
    """
    try:
        youtube = get_youtube_service()

        # Use the beautiful description template
        final_description = create_description(name or "Friend", description)

        # Clean title (YouTube limit is 100 characters)
        final_title = title[:100]

        body = {
            "snippet": {
                "title": final_title,
                "description": final_description,
                "tags": [
                    "Happy Birthday",
                    "Birthday Video",
                    f"Happy Birthday {name}" if name else "Happy Birthday",
                    "Birthday Wish",
                    "Birthday Greeting",
                    "Personalized Birthday",
                    "Birthday Celebration",
                    "Party Decor",
                    "4K",
                    "Birthday Decor",
                    "Celebration Video",
                    "Birthday Party",
                    "Elegant Birthday",
                    "Birthday Song"
                ],
                "categoryId": "22",  # People & Blogs
            },
            "status": {
                "privacyStatus": "public",          # Change to "unlisted" if you want
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=5 * 1024 * 1024,  # 5 MB chunks
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                st.write(f"Upload progress: {progress}%")

        video_id = response["id"]
        return f"https://www.youtube.com/watch?v={video_id}"

    except HttpError as e:
        raise Exception(f"YouTube API error: {e}")
    except Exception as e:
        raise Exception(f"Upload failed: {str(e)}")
