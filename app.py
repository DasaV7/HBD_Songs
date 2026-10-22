import streamlit as st
import asyncio

import os

os.makedirs(
    "generated",
    exist_ok=True
)

from services.lyrics_service import (
    generate_lyrics
)

from services.audio_service import (
    generate_audio
)

from services.video_service import (
    create_video
)

from services.music_service import (
    merge_with_background_music
)

st.set_page_config(
    page_title="Birthday Video Generator"
)

st.title("🎂 Birthday Video Generator")

name = st.text_input(
    "Birthday Name"
)

message = st.text_area(
    "Custom Message"
)

if st.button("Generate Video"):

    with st.spinner(
        "Generating..."
    ):

        lyrics = generate_lyrics(
            name,
            message
        )

        audio_file = (
            f"generated/{name}.mp3"
        )

        asyncio.run(
            generate_audio(
                lyrics,
                audio_file
            )
        )

        voice_file = audio_file

        audio_file = (
            f"generated/{name}_final.mp3"
        )
        
        merge_with_background_music(
            voice_file,
            audio_file
        )

        video_path = create_video(
            name,
            audio_file
        )

        st.success(
            "Video Ready"
        )

        st.video(
            video_path
        )
