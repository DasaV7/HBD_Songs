import streamlit as st
import asyncio
import os
import time
from datetime import datetime

from services.lyrics_service import generate_lyrics
from services.audio_service import generate_audio
from services.video_service import create_video
from services.youtube_service import upload_video
from services.sheets_service import (
    get_stats,
    select_next_names,
    remove_name_from_remaining,
    add_to_history,
    reset_remaining_from_master,
    get_all_names
)

os.makedirs("generated", exist_ok=True)

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="Birthday Video Generator | Batch Studio",
    page_icon="🎂",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.3rem;
    }
    .sub-title {
        text-align: center;
        color: #888;
        margin-bottom: 1.8rem;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🎂 Birthday Video Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Batch Studio + Google Sheets</div>', unsafe_allow_html=True)

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

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("📋 Name Lists (Google Sheets)")
    
    try:
        stats = get_stats()
        st.metric("Master List", stats["master"])
        st.metric("Remaining", stats["remaining"])
        st.metric("History (Uploaded)", stats["history"])
    except Exception as e:
        st.error(f"Sheets connection error: {e}")
        stats = {"master": 0, "remaining": 0, "history": 0}

    st.markdown("---")
    if st.button("🔄 Reset Remaining from Master"):
        try:
            count = reset_remaining_from_master()
            st.success(f"Reset done! {count} names copied to Remaining.")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(str(e))

# ====================== TABS ======================
tab1, tab2 = st.tabs(["🚀 Manual Batch", "⏰ Daily Auto Mode"])

# ====================== TAB 1: MANUAL ======================
with tab1:
    st.markdown("### Manual Batch Processing")
    
    names_input = st.text_area("Enter names (one per line)", height=140, placeholder="Vikram\nSai\nAbhinav")

    col1, col2, col3 = st.columns(3)
    with col1:
        max_videos = st.selectbox("Number of videos", [2, 5, 10], index=0)
    with col2:
        auto_upload = st.selectbox("Auto Upload", ["Enabled", "Disabled"], index=0)
    with col3:
        repeats = st.selectbox("Length Multiplier", [1, 2, 3], index=0)

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        start_btn = st.button("🚀 Start Batch", type="primary", use_container_width=True, disabled=st.session_state.batch_running)
    with col_b:
        if st.button("🛑 Stop", use_container_width=True):
            st.session_state.stop_batch = True
            st.session_state.batch_running = False
    with col_c:
        if st.button("🗑️ Clear Results", use_container_width=True):
            st.session_state.batch_results = []
            st.session_state.current_video = None
            st.session_state.batch_index = 0
            st.rerun()

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
        st.session_state.repeats = repeats
        st.session_state.is_daily_mode = False
        st.rerun()

# ====================== TAB 2: DAILY AUTO ======================
with tab2:
    st.markdown("### Daily Automatic Mode")
    st.info("Takes the next 2 names from Google Sheet (Remaining), generates + uploads them, then moves them to History.")

    col1, col2 = st.columns(2)
    with col1:
        auto_repeats = st.selectbox("Video Length", [1, 2, 3], index=0, key="auto_repeats")
    with col2:
        delay_minutes = st.number_input("Delay between videos (minutes)", min_value=5, max_value=60, value=15)

    st.markdown("---")
    st.write(f"**Remaining Names:** `{stats.get('remaining', 0)}`")

    if st.button("▶️ Run Daily Auto Batch Now", type="primary", use_container_width=True):
        today_names = select_next_names(count=2)
        
        if not today_names:
            st.error("No names left in the Remaining sheet.")
            st.stop()

        st.session_state.batch_names = today_names
        st.session_state.batch_index = 0
        st.session_state.batch_results = []
        st.session_state.batch_running = True
        st.session_state.stop_batch = False
        st.session_state.current_video = None
        st.session_state.auto_upload = True
        st.session_state.repeats = auto_repeats
        st.session_state.is_daily_mode = True
        st.session_state.delay_minutes = delay_minutes
        st.rerun()

# ====================== BATCH PROCESSING ENGINE ======================
if st.session_state.batch_running and not st.session_state.stop_batch:

    names = st.session_state.batch_names
    idx = st.session_state.batch_index
    current_repeats = st.session_state.get("repeats", 1)
    is_daily = st.session_state.get("is_daily_mode", False)

    if idx >= len(names):
        uploaded_count = sum(1 for r in st.session_state.batch_results if "Uploaded successfully" in r.get("status", ""))
        
        st.success(f"""
        ### Batch Completed!
        - Processed: **{len(st.session_state.batch_results)}**
        - Successfully uploaded: **{uploaded_count}**
        - Remaining names now: **{get_stats()['remaining']}**
        """)
        st.balloons()
        
        st.session_state.batch_running = False
        st.session_state.is_daily_mode = False
        st.rerun()

    current_name = names[idx]
    personalized_message = f"Happy Birthday {current_name}!"

    st.markdown(f"### Processing {idx + 1} of {len(names)}: `{current_name}`")
    st.progress(idx / max(len(names), 1))

    if st.session_state.current_video and os.path.exists(st.session_state.current_video):
        with st.expander("Previous Video", expanded=False):
            st.video(st.session_state.current_video)

    try:
        with st.status(f"Generating **{current_name}**...", expanded=True) as s:
            lyrics = generate_lyrics(current_name, personalized_message)
            audio_file = f"generated/{current_name}.mp3"
            asyncio.run(generate_audio(lyrics, audio_file))
            time.sleep(0.3)

            video_path, used_files = create_video(
                current_name,
                personalized_message,
                audio_file,
                repeats=current_repeats
            )
            s.update(label="Video ready", state="complete")

        # Upload
        link = None
        upload_status = "⏸️ Skipped"
        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if st.session_state.get("auto_upload", True):
            with st.status("Uploading to YouTube...", expanded=True) as s:
                try:
                    link = upload_video(
                        video_path,
                        f"Happy Birthday {current_name}",
                        personalized_message,
                        name=current_name
                    )
                    upload_status = "✅ Uploaded successfully"
                    
                    # Update Google Sheet immediately
                    remove_name_from_remaining(current_name)
                    add_to_history(current_name, link or "")
                    
                    s.update(label="Uploaded + Sheet updated", state="complete")
                except Exception as e:
                    upload_status = f"❌ Upload failed: {e}"
                    s.update(label="Upload failed", state="error")

        # Save result
        result = {
            "name": current_name,
            "video_path": video_path,
            "link": link,
            "status": upload_status,
            "upload_time": upload_time
        }
        st.session_state.batch_results.append(result)
        st.session_state.current_video = video_path
        st.session_state.batch_index += 1

        st.success(f"Finished: **{current_name}**")
        st.video(video_path)
        st.write(upload_status)

        if is_daily and idx + 1 < len(names):
            delay = st.session_state.get("delay_minutes", 15) * 60
            st.warning(f"Waiting {st.session_state.get('delay_minutes', 15)} minutes...")
            time.sleep(delay)

        time.sleep(1.5)
        st.rerun()

    except Exception as e:
        st.error(f"Error on {current_name}: {e}")
        result = {
            "name": current_name,
            "video_path": None,
            "link": None,
            "status": f"❌ Error: {str(e)}",
            "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.batch_results.append(result)
        st.session_state.batch_index += 1
        time.sleep(2)
        st.rerun()

# ====================== RESULTS TABLE ======================
if st.session_state.batch_results:
    st.markdown("---")
    st.markdown("### Upload Results")

    table_data = []
    for res in st.session_state.batch_results:
        table_data.append({
            "Name": res["name"],
            "Status": res["status"],
            "Upload Date & Time": res.get("upload_time", "-"),
            "YouTube Link": res["link"] if res.get("link") else "-"
        })

    st.dataframe(
        table_data,
        use_container_width=True,
        column_config={
            "YouTube Link": st.column_config.LinkColumn("YouTube Link")
        }
    )
