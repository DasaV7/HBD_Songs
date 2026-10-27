import streamlit as st
import asyncio
import os

from services.lyrics_service import generate_lyrics
from services.audio_service import generate_audio
from services.video_service import create_video
from services.youtube_service import upload_video

# Create generated folder
os.makedirs("generated", exist_ok=True)

# Streamlit Page Config
st.set_page_config(
    page_title="Birthday Video Generator",
    page_icon="🎂",
    layout="centered"
)

st.title("🎂 Birthday Video Generator")
st.write("Create beautiful birthday videos with music and slides.")

# Debug secrets (optional)
if st.checkbox("Debug Secrets"):
    st.write("Client ID exists:", "YOUTUBE_CLIENT_ID" in st.secrets)
    st.write("Client Secret exists:", "YOUTUBE_CLIENT_SECRET" in st.secrets)
    st.write("Channel ID exists:", "YOUTUBE_CHANNEL_ID" in st.secrets)

# User Inputs
name = st.text_input("Birthday Person Name")
message = st.text_area("Custom Birthday Message")

# ====================== GENERATE VIDEO ======================
if st.button("Generate Video"):

    if not name.strip():
        st.error("Please enter a birthday name.")
        st.stop()

    if not message.strip():
        message = "Wishing you happiness, joy and success!"

    with st.spinner("Generating Birthday Video..."):
        try:
            # 1. Generate lyrics
            lyrics = generate_lyrics(name, message)

            # 2. Audio file path
            audio_file = f"generated/{name}.mp3"

            # 3. Generate audio
            asyncio.run(generate_audio(lyrics, audio_file))

            if not os.path.exists(audio_file):
                st.error("Audio file was not created.")
                st.stop()

            st.success("Music Loaded Successfully")

            # 4. Create video
            video_path = create_video(name, message, audio_file)

            if not os.path.exists(video_path):
                st.error("Video file was not created.")
                st.stop()

            # Save to session state so Upload button can use it later
            st.session_state["last_video_path"] = video_path
            st.session_state["last_title"] = f"Happy Birthday {name}"
            st.session_state["last_description"] = message
            st.session_state["last_name"] = name

            st.success("🎉 Birthday Video Ready!")

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()

# ====================== SHOW VIDEO + BUTTONS ======================
# This part runs on every rerun if a video was already generated
if "last_video_path" in st.session_state and os.path.exists(st.session_state["last_video_path"]):

    st.video(st.session_state["last_video_path"])

    # Download button
    with open(st.session_state["last_video_path"], "rb") as video_file:
        st.download_button(
            label="⬇️ Download Video",
            data=video_file,
            file_name=f"{st.session_state.get('last_name', 'birthday')}.mp4",
            mime="video/mp4",
            key="download_btn"
        )

    # Upload to YouTube button
    if st.button("📤 Upload To YouTube", key="upload_btn"):
        with st.spinner("Uploading to YouTube... Please wait"):
            try:
                link = upload_video(
                    st.session_state["last_video_path"],
                    st.session_state["last_title"],
                    st.session_state["last_description"]
                )
                st.success("✅ Uploaded successfully!")
                st.markdown(f"**Watch here:** [Open on YouTube]({link})")
            except Exception as e:
                st.error(f"Upload failed: {e}")
