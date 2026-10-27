import streamlit as st
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_youtube_service():
    """Build an authenticated YouTube service using refresh token from secrets."""
    client_id = st.secrets["youtube"]["client_id"]
    client_secret = st.secrets["youtube"]["client_secret"]
    refresh_token = st.secrets["youtube"]["refresh_token"]

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )

    # Refresh the access token if needed
    if not creds.valid:
        creds.refresh(Request())

    return build("youtube", "v3", credentials=creds)


def upload_video(video_path: str, title: str, description: str = "") -> str:
    """
    Upload a video to YouTube and return the watch URL.
    """
    try:
        youtube = get_youtube_service()

        body = {
            "snippet": {
                "title": title[:100],          # YouTube limit
                "description": description[:5000],
                "categoryId": "22",            # People & Blogs (good default)
            },
            "status": {
                "privacyStatus": "public",     # or "unlisted" / "private"
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=1024 * 1024 * 5,         # 5 MB chunks
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
                # Optional: show progress in Streamlit
                progress = int(status.progress() * 100)
                st.write(f"Upload progress: {progress}%")

        video_id = response["id"]
        return f"https://www.youtube.com/watch?v={video_id}"

    except HttpError as e:
        raise Exception(f"YouTube API error: {e}")
    except Exception as e:
        raise Exception(f"Upload failed: {str(e)}")
