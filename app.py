import streamlit as st
import asyncio
import os
import time

from services.lyrics_service import generate_lyrics
from services.audio_service import generate_audio
from services.video_service import create_video
from services.youtube_service import upload_video

os.makedirs("generated", exist_ok=True)

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="Birthday Video Generator | Batch Studio",
    page_icon="🎂",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ====================== CUSTOM CSS ======================
st.markdown("""
<style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        text-align: center;
        color: #888;
        margin-bottom: 2rem;
        font-size: 1.05rem;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    .status-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #1e1e2f;
        border: 1px solid #333;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ====================== HEADER ======================
st.markdown('<div class="main-title">🎂 Birthday Video Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Batch Studio • Create & Upload Personalized Birthday Videos</div>', unsafe_allow_html=True)

# ====================== SESSION STATE ======================
if "batch_running" not in st.session_state:
    st.session_state.batch_running = False
if "batch_names" not in st.session_state:
    st.session_state.batch_names = []
if "batch_index" not in st.session_state:
    st.session_state.batch_index = 0
if "batch_results" not in st.session_state:
    st.session_state.batch_results = []
if "current_video" not in st.session_state:
    st.session_state.current_video = None
if "stop_batch" not in st.session_state:
    st.session_state.stop_batch = False

# ====================== INPUT SECTION ======================
with st.container():
    st.markdown("### 1. Enter Names")
    names_input = st.text_area(
        "One name per line",
        height=150,
        placeholder="Vikram\nSai\nAbhinav\nPriya\nRahul\nAnanya",
        label_visibility="collapsed"
    )

    col1, col2 = st.columns(2)
    with col1:
        max_videos = st.selectbox("Number of videos", [5, 10], index=0)
    with col2:
        auto_upload = st.selectbox("Auto Upload to YouTube", ["Enabled", "Disabled"], index=0)

    st.caption("Message format: **Happy Birthday {name}!**")

st.markdown("---")

# ====================== CONTROL BUTTONS ======================
col_a, col_b, col_c = st.columns(3)

with col_a:
    start_btn = st.button("🚀 Start Batch", type="primary", use_container_width=True, disabled=st.session_state.batch_running)

with col_b:
    if st.button("🛑 Stop Batch", use_container_width=True):
        st.session_state.stop_batch = True
        st.session_state.batch_running = False
        st.toast("Stopping after current video...", icon="🛑")

with col_c:
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.batch_results = []
        st.session_state.current_video = None
        st.session_state.batch_index = 0
        st.session_state.batch_running = False
        st.session_state.stop_batch = False
        st.rerun()

# ====================== START BATCH ======================
if start_btn:
    names = [n.strip() for n in names_input.strip().split("\n") if n.strip()]

    if not names:
        st.error("Please enter at least one name.")
        st.stop()

    names = names[:max_videos]

    st.session_state.batch_names = names
    st.session_state.batch_index = 0
    st.session_state.batch_results = []
    st.session_state.batch_running = True
    st.session_state.stop_batch = False
    st.session_state.current_video = None
    st.session_state.auto_upload = (auto_upload == "Enabled")
    st.rerun()

# ====================== BATCH PROCESSING ======================
if st.session_state.batch_running and not st.session_state.stop_batch:

    names = st.session_state.batch_names
    idx = st.session_state.batch_index

    if idx >= len(names):
        st.session_state.batch_running = False
        st.success("🎉 All videos completed successfully!")
        st.balloons()
        st.rerun()

    current_name = names[idx]
    personalized_message = f"Happy Birthday {current_name}!"

    # Progress Header
    st.markdown(f"### Processing {idx + 1} of {len(names)}")
    st.markdown(f"**Current Name:** `{current_name}`")
    
    progress_value = idx / len(names)
    st.progress(progress_value, text=f"{int(progress_value * 100)}% completed")

    # Previous video
    if st.session_state.current_video and os.path.exists(st.session_state.current_video):
        with st.expander("▶️ Previous Video (still playing)", expanded=True):
            st.video(st.session_state.current_video)
            st.caption("Keep watching while the next video is generating...")

    status = st.empty()

    try:
        # Generate
        with st.status(f"Generating video for **{current_name}**...", expanded=True) as s:
            st.write("Creating lyrics & audio...")
            lyrics = generate_lyrics(current_name, personalized_message)
            audio_file = f"generated/{current_name}.mp3"
            asyncio.run(generate_audio(lyrics, audio_file))
            time.sleep(0.3)

            st.write("Rendering video with effects...")
            video_path, used_files = create_video(current_name, personalized_message, audio_file)
            s.update(label="Video generated successfully!", state="complete")

        # Upload
        link = None
        if st.session_state.get("auto_upload", True):
            with st.status(f"Uploading **{current_name}** to YouTube...", expanded=True) as s:
                try:
                    link = upload_video(
                        video_path,
                        f"Happy Birthday {current_name}",
                        personalized_message,
                        name=current_name
                    )
                    upload_status = "✅ Uploaded + Thumbnail + Added to Playlists"
                    s.update(label="Upload completed!", state="complete")
                except Exception as e:
                    upload_status = f"❌ Upload failed: {str(e)}"
                    s.update(label="Upload failed", state="error")
        else:
            upload_status = "⏸️ Upload skipped (Auto Upload Disabled)"

        # Save result
        result = {
            "name": current_name,
            "video_path": video_path,
            "link": link,
            "status": upload_status,
            "used_files": used_files
        }
        st.session_state.batch_results.append(result)
        st.session_state.current_video = video_path
        st.session_state.batch_index += 1

        # Show new video
        st.success(f"Video ready for **{current_name}**")
        st.video(video_path)
        st.info(upload_status)

        # Countdown
        countdown = st.empty()
        for sec in range(10, 0, -1):
            if st.session_state.stop_batch:
                break
            countdown.warning(f"Next video starting in **{sec}** seconds...")
            time.sleep(1)

        countdown.empty()
        st.rerun()

    except Exception as e:
        st.error(f"Error processing {current_name}: {e}")
        st.session_state.batch_running = False

# ====================== RESULTS ======================
if st.session_state.batch_results:
    st.markdown("---")
    st.markdown("### 📋 Batch Results")

    for res in reversed(st.session_state.batch_results):
        with st.expander(f"**{res['name']}** — {res['status']}", expanded=False):
            if res["video_path"] and os.path.exists(res["video_path"]):
                st.video(res["video_path"])
            if res.get("link"):
                st.markdown(f"[▶ Watch on YouTube]({res['link']})")
