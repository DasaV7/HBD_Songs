import streamlit as st
import asyncio
import os
import time

from services.lyrics_service import generate_lyrics
from services.audio_service import generate_audio
from services.video_service import create_video
from services.youtube_service import upload_video

# Create generated folder
os.makedirs("generated", exist_ok=True)

# Page config
st.set_page_config(
    page_title="Birthday Video Generator",
    page_icon="🎂",
    layout="centered"
)

st.title("🎂 Birthday Video Generator")
st.write("Create beautiful birthday videos with music and slides.")

# Optional debug
if st.checkbox("Debug Secrets"):
    st.write("Client ID exists:", "YOUTUBE_CLIENT_ID" in st.secrets)
    st.write("Client Secret exists:", "YOUTUBE_CLIENT_SECRET" in st.secrets)
    st.write("Refresh Token exists:", "YOUTUBE_REFRESH_TOKEN" in st.secrets)
    st.write("Channel ID exists:", "YOUTUBE_CHANNEL_ID" in st.secrets)

# User inputs
name = st.text_input("Birthday Person Name")
message = st.text_area("Custom Birthday Message")

# ====================== GENERATE VIDEO ======================
if st.button("Generate Video", type="primary"):

    if not name.strip():
        st.error("Please enter a birthday name.")
        st.stop()

    if not message.strip():
        message = "Wishing you happiness, joy and success!"

    with st.spinner("Generating Birthday Video... Please wait"):
        try:
            # 1. Generate lyrics
            lyrics = generate_lyrics(name, message)

            # 2. Audio
            audio_file = f"generated/{name}.mp3"
            asyncio.run(generate_audio(lyrics, audio_file))

            # Verify audio
            time.sleep(0.4)
            if not os.path.exists(audio_file) or os.path.getsize(audio_file) < 10000:
                st.warning("Audio issue detected, retrying...")
                asyncio.run(generate_audio(lyrics, audio_file))
                time.sleep(0.4)

            if not os.path.exists(audio_file) or os.path.getsize(audio_file) < 10000:
                st.error("Failed to create valid audio file.")
                st.stop()

            st.success("Music Loaded Successfully")

            # 3. Create video
            video_path, used_files = create_video(name, message, audio_file)

            if not os.path.exists(video_path) or os.path.getsize(video_path) < 100000:
                st.error("Video file was not created properly.")
                st.stop()

            # Save to session state
            st.session_state["last_video_path"] = video_path
            st.session_state["last_title"] = f"Happy Birthday {name}"
            st.session_state["last_description"] = message
            st.session_state["last_name"] = name
            st.session_state["used_files"] = used_files

            st.success("🎉 Birthday Video Ready!")
            st.balloons()

        except Exception as e:
            st.error(f"Error while generating video: {str(e)}")
            st.stop()

# ====================== SHOW RESULTS ======================
if "last_video_path" in st.session_state and os.path.exists(st.session_state["last_video_path"]):

    st.markdown("---")
    st.subheader("Your Birthday Video")

    # Single video player
    st.video(st.session_state["last_video_path"])

    # Show used files
    if "used_files" in st.session_state:
        used = st.session_state["used_files"]
        with st.expander("📁 Files used in this video", expanded=False):
            st.write(f"**Music:** `{used.get('audio', 'N/A')}`")
            st.write(f"**Images ({len(used.get('images', []))}):**")
            st.write(", ".join(used.get("images", [])))
            st.write(f"**Videos ({len(used.get('videos', []))}):**")
            st.write(", ".join(used.get("videos", [])) if used.get("videos") else "None")

    st.markdown("---")

    # Download button
    with open(st.session_state["last_video_path"], "rb") as f:
        st.download_button(
            label="⬇️ Download Video",
            data=f,
            file_name=f"{st.session_state.get('last_name', 'birthday')}.mp4",
            mime="video/mp4",
            key="download_btn"
        )

    # Upload button
    if st.button("📤 Upload To YouTube", key="upload_btn"):
        with st.spinner("Uploading to YouTube... Please wait (this can take a few minutes)"):
            try:
                link = upload_video(
                    st.session_state["last_video_path"],
                    st.session_state["last_title"],
                    st.session_state["last_description"],
                    name=st.session_state.get("last_name", "")
                )
                st.success("✅ Uploaded successfully!")
                st.markdown(f"**Watch on YouTube:** [Click here]({link})")
                st.balloons()
            except Exception as e:
                st.error(f"Upload failed: {e}")
