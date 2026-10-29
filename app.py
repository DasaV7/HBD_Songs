import streamlit as st
import asyncio
import os
import time

from services.lyrics_service import generate_lyrics
from services.audio_service import generate_audio
from services.video_service import create_video
from services.youtube_service import upload_video

os.makedirs("generated", exist_ok=True)

st.set_page_config(
    page_title="Birthday Video Generator - Batch",
    page_icon="🎂",
    layout="centered"
)

st.title("🎂 Birthday Video Generator — Batch Mode")

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
st.subheader("1. Enter Names")
names_input = st.text_area(
    "Enter names (one name per line)",
    height=160,
    placeholder="Vikram\nSai\nAbhinav\nPriya\nRahul\nAnanya"
)

col1, col2, col3 = st.columns(3)

with col1:
    max_videos = st.selectbox("How many videos?", [5, 10], index=0)

with col2:
    auto_upload = st.selectbox(
        "Auto Upload to YouTube",
        ["Enabled", "Disabled"],
        index=0
    )

with col3:
    default_message = st.text_input(
        "Default Message",
        value="Wishing you happiness, joy and success!"
    )

# ====================== CONTROL BUTTONS ======================
col_a, col_b, col_c = st.columns(3)

with col_a:
    start_btn = st.button("🚀 Start Batch", type="primary", disabled=st.session_state.batch_running)

with col_b:
    if st.button("🛑 Stop Batch"):
        st.session_state.stop_batch = True
        st.session_state.batch_running = False
        st.warning("Stopping batch after current video...")

with col_c:
    if st.button("🗑️ Clear All"):
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
        st.success("🎉 All videos completed!")
        st.balloons()
        st.rerun()

    current_name = names[idx]

    st.markdown(f"### Processing {idx + 1} of {len(names)}: `{current_name}`")
    st.progress(idx / len(names))

    # Show previous video while generating
    if st.session_state.current_video and os.path.exists(st.session_state.current_video):
        st.markdown("#### ▶️ Previous Video (still playing)")
        st.video(st.session_state.current_video)
        st.caption("Keep watching while the next video is generating...")

    status = st.empty()

    try:
        # Generate video
        status.info(f"🔄 Generating video for **{current_name}**...")

        lyrics = generate_lyrics(current_name, default_message)
        audio_file = f"generated/{current_name}.mp3"
        asyncio.run(generate_audio(lyrics, audio_file))
        time.sleep(0.3)

        video_path, used_files = create_video(current_name, default_message, audio_file)

        # Upload only if enabled
        link = None
        if st.session_state.get("auto_upload", True):
            status.info(f"📤 Uploading **{current_name}** to YouTube...")
            try:
                link = upload_video(
                    video_path,
                    f"Happy Birthday {current_name}",
                    default_message,
                    name=current_name
                )
                upload_status = "✅ Uploaded successfully"
            except Exception as e:
                upload_status = f"❌ Upload failed: {str(e)}"
        else:
            upload_status = "⏸️ Upload skipped (Auto Upload is Disabled)"

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

        # Show new video + countdown
        status.success(f"✅ Video ready: **{current_name}**")
        st.video(video_path)
        st.write(upload_status)

        countdown = st.empty()
        for sec in range(10, 0, -1):
            if st.session_state.stop_batch:
                break
            countdown.warning(f"⏱ Next video in **{sec}** seconds...")
            time.sleep(1)

        countdown.empty()
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error on {current_name}: {e}")
        st.session_state.batch_running = False

# ====================== RESULTS ======================
if st.session_state.batch_results:
    st.markdown("---")
    st.subheader("📋 Batch Results")

    for res in reversed(st.session_state.batch_results):
        with st.expander(f"{res['name']} — {res['status']}", expanded=False):
            if res["video_path"] and os.path.exists(res["video_path"]):
                st.video(res["video_path"])
            if res.get("link"):
                st.markdown(f"[▶ Watch on YouTube]({res['link']})")
