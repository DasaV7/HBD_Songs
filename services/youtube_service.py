from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload"
]


def get_service():

    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json",
        SCOPES
    )

    creds = flow.run_local_server(
        port=0
    )

    return build(
        "youtube",
        "v3",
        credentials=creds
    )


def upload_video(
    video_path,
    title,
    description
):

    youtube = get_service()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(
            video_path
        )
    )

    response = request.execute()

    return (
        "https://youtube.com/watch?v="
        + response["id"]
    )
