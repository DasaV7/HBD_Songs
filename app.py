import streamlit as st
import asyncio
import os
import streamlit as st

from services.lyrics_service import (
    generate_lyrics
)

from services.audio_service import (
    generate_audio
)

from services.video_service import (
    create_video
)
from services.youtube_service import (
    upload_video
)
# Create generated folder

os.makedirs(
    "generated",
    exist_ok=True
)

# Streamlit Page

st.set_page_config(
    page_title="Birthday Video Generator",
    page_icon="🎂",
    layout="centered"
)

st.title("🎂 Birthday Video Generator")

st.write(
    "Create beautiful birthday videos with music and slides."
)

if st.checkbox("Debug Secrets"):

    st.write(
        "Client ID exists:",
        "YOUTUBE_CLIENT_ID" in st.secrets
    )

    st.write(
        "Client Secret exists:",
        "YOUTUBE_CLIENT_SECRET" in st.secrets
    )

    st.write(
        "Channel ID exists:",
        "YOUTUBE_CHANNEL_ID" in st.secrets
    )

# User Inputs

name = st.text_input(
    "Birthday Person Name"
)

message = st.text_area(
    "Custom Birthday Message"
)

# Generate Video

if st.button("Generate Video"):

    if not name.strip():

        st.error(
            "Please enter a birthday name."
        )

        st.stop()

    if not message.strip():

        message = (
            "Wishing you happiness, joy and success!"
        )

    with st.spinner(
        "Generating Birthday Video..."
    ):

        try:

            # Generate lyrics

            lyrics = generate_lyrics(
                name,
                message
            )

            # Audio output file

            audio_file = (
                f"generated/{name}.mp3"
            )

            # generate_audio()
            # simply copies random music file

            asyncio.run(
                generate_audio(
                    lyrics,
                    audio_file
                )
            )

            # Verify audio exists

            if not os.path.exists(
                audio_file
            ):

                st.error(
                    "Audio file was not created."
                )

                st.stop()

            st.success(
                "Music Loaded Successfully"
            )

            # Create video

            video_path = create_video(
                name,
                message,
                audio_file
            )

            # Verify video exists

            if not os.path.exists(
                video_path
            ):

                st.error(
                    "Video file was not created."
                )

                st.stop()

            st.success(
                "🎉 Birthday Video Ready!"
            )

            st.video(
                video_path
            )
            if st.button(
                "Upload To YouTube"
            ):
            
                youtube_link = upload_video(
                    video_path,
                    f"Happy Birthday {name}",
                    message
                )
            
                st.success(
                    youtube_link
                )
            # Download Button

            with open(
                video_path,
                "rb"
            ) as video_file:

                st.download_button(
                    label="⬇️ Download Video",
                    data=video_file,
                    file_name=f"{name}.mp4",
                    mime="video/mp4"
                )

        except Exception as e:

            st.error(
                f"Error: {str(e)}"
            )
