import streamlit as st
import asyncio
import os

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
if st.button("Generate Video"):

    if not name.strip():
        st.error("Please enter a birthday name.")
        st.stop()

    if not message.strip():
        message = "Wishing you happiness, joy and success!"

    with st.spinner("Generating Birthday Video..."):
        try:
            # Generate lyrics
            lyrics = generate_lyrics(name, message)

            # Audio path
            audio_file = f"generated/{name}.mp3"

            # Generate audio
            asyncio.run(generate_audio(lyrics, audio_file))

            if not os.path.exists(audio_file):
                st.error("Audio file was not created.")
                st.stop()

            st.success("Music Loaded Successfully")

            # Create video
            #video_path = create_video(name, message, audio_file)
            video_path, used_files = create_video(name, message, audio_file)
            
            st.success("🎉 Birthday Video Ready!")
            st.video(video_path)          # This should now play properly
            
            st.markdown("### 📁 Files used in this video:")
            st.write(f"**Music:** `{used_files['audio']}`")
            st.write(f"**Images:** {', '.join(used_files['images'])}")
            st.write(f"**Videos:** {', '.join(used_files['videos']) if used_files['videos'] else 'None'}")

            if not os.path.exists(video_path):
                st.error("Video file was not created.")
                st.stop()

            # Save important data in session state
            st.session_state["last_video_path"] = video_path
            st.session_state["last_title"] = f"Happy Birthday {name}"
            st.session_state["last_description"] = message
            st.session_state["last_name"] = name

            st.success("🎉 Birthday Video Ready!")

        except Exception as e:
            st.error(f"Error while generating video: {str(e)}")
            st.stop()

# ====================== SHOW VIDEO + DOWNLOAD + UPLOAD ======================
if "last_video_path" in st.session_state and os.path.exists(st.session_state["last_video_path"]):

    st.video(st.session_state["last_video_path"])

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
        with st.spinner("Uploading to YouTube... Please wait"):
            try:
                link = upload_video(
                    st.session_state["last_video_path"],
                    st.session_state["last_title"],
                    st.session_state["last_description"],
                    name=st.session_state.get("last_name", "")
                )
                st.success("✅ Uploaded successfully!")
                st.markdown(f"**Watch on YouTube:** [Click here]({link})")
            except Exception as e:
                st.error(f"Upload failed: {e}")
