import streamlit as st
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_youtube_service():
    """Create authenticated YouTube service using flat secrets."""
    
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

    # Refresh access token if needed
    if not creds.valid:
        creds.refresh(Request())

    return build("youtube", "v3", credentials=creds)


def upload_video(video_path: str, title: str, description: str = "") -> str:
    """
    Upload video to YouTube and return the watch URL.
    """
    try:
        youtube = get_youtube_service()

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "categoryId": "22",  # People & Blogs
            },
            "status": {
                "privacyStatus": "public",  # change to "unlisted" if you want
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
