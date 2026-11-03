import streamlit as st
import asyncio
import os
import time
from datetime import datetime

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
    initial_sidebar_state="expanded"
)

# ====================== CUSTOM CSS ======================
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
        font-size: 1.05rem;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🎂 Birthday Video Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Batch Studio + Daily Auto Mode</div>', unsafe_allow_html=True)

# ====================== HELPER FUNCTIONS ======================
def load_names(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def save_names(filepath, names):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(names) + ("\n" if names else ""))

def get_now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def initialize_name_files():
    if not os.path.exists("remaining_names.txt"):
        master = load_names("birthday_names.txt")
        if master:
            save_names("remaining_names.txt", master)

def select_today_names(count=2):
    remaining = load_names("remaining_names.txt")
    if not remaining:
        return []
    selected = remaining[:count]
    save_names("today_names.txt", selected)
    return selected

def remove_name_from_remaining(name):
    """Remove a single name immediately after successful upload"""
    remaining = load_names("remaining_names.txt")
    if name in remaining:
        remaining.remove(name)
        save_names("remaining_names.txt", remaining)
        return True
    return False

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

initialize_name_files()

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("📋 Name Lists")
    
    master_count = len(load_names("birthday_names.txt"))
    remaining_count = len(load_names("remaining_names.txt"))
    today_names = load_names("today_names.txt")
    
    st.metric("Master List", master_count)
    st.metric("Remaining", remaining_count)
    st.metric("Today's Names", len(today_names))
    
    if today_names:
        st.write("**Today:**")
        for n in today_names:
            st.write(f"• {n}")
    
    st.markdown("---")
    if st.button("🔄 Reset Remaining from Master"):
        master = load_names("birthday_names.txt")
        save_names("remaining_names.txt", master)
        st.success("Remaining list reset!")
        st.rerun()

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
        if st.button("🗑️ Clear", use_container_width=True):
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
    st.info("Picks the next 2 names from `remaining_names.txt`, generates + uploads them, then removes them from the remaining list.")

    col1, col2 = st.columns(2)
    with col1:
        auto_repeats = st.selectbox("Video Length", [1, 2, 3], index=0, key="auto_repeats")
    with col2:
        delay_minutes = st.number_input("Delay between videos (minutes)", min_value=5, max_value=60, value=30)

    st.markdown("---")

    last_run = None
    if os.path.exists("last_run.txt"):
        with open("last_run.txt", "r") as f:
            last_run = f.read().strip()

    st.write(f"**Last Auto Run:** `{last_run if last_run else 'Never'}`")
    st.write(f"**Remaining Names:** `{len(load_names('remaining_names.txt'))}`")

    if st.button("▶️ Run Daily Auto Batch Now", type="primary", use_container_width=True):
        today_names = select_today_names(count=2)
        
        if not today_names:
            st.error("No names left in remaining_names.txt")
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
        
        with open("last_run.txt", "w") as f:
            f.write(get_now_str())
        
        st.rerun()

# ====================== BATCH PROCESSING ENGINE ======================
if st.session_state.batch_running and not st.session_state.stop_batch:

    names = st.session_state.batch_names
    idx = st.session_state.batch_index
    current_repeats = st.session_state.get("repeats", 1)
    is_daily = st.session_state.get("is_daily_mode", False)

    if idx >= len(names):
        st.session_state.batch_running = False
        st.session_state.is_daily_mode = False
        
        uploaded_count = sum(1 for r in st.session_state.batch_results if "Uploaded successfully" in r.get("status", ""))
        
        st.success(f"""
        ### Batch Completed
        - Total processed: **{len(st.session_state.batch_results)}**
        - Successfully uploaded: **{uploaded_count}**
        - Remaining names now: **{len(load_names('remaining_names.txt'))}**
        """)
        st.balloons()
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
            time.sleep(0.4)

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
        upload_time = get_now_str()

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
                    upload_time = get_now_str()
                    
                    # ★★★ IMPORTANT: Remove name immediately after success ★★★
                    remove_name_from_remaining(current_name)
                    
                    s.update(label="Uploaded + Name removed from remaining list", state="complete")
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

        # Delay between videos only if more names remain
        if is_daily and idx + 1 < len(names):
            delay = st.session_state.get("delay_minutes", 15) * 60
            st.warning(f"Waiting {st.session_state.get('delay_minutes', 15)} minutes before next video...")
            time.sleep(delay)

        time.sleep(1.5)
        st.rerun()

    except Exception as e:
        st.error(f"Error on {current_name}: {e}")
        
        # Save the error result so we don't lose progress
        result = {
            "name": current_name,
            "video_path": None,
            "link": None,
            "status": f"❌ Error: {str(e)}",
            "upload_time": get_now_str()
        }
        st.session_state.batch_results.append(result)
        st.session_state.batch_index += 1   # Move to next name even on error
        
        time.sleep(3)
        st.rerun()

# ====================== RESULTS TABLE ======================
if st.session_state.batch_results:
    st.markdown("---")
    st.markdown("### Upload Results")

    # Create table data
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

    # Also keep expanders for video preview
    with st.expander("Video Previews"):
        for res in reversed(st.session_state.batch_results):
            st.markdown(f"**{res['name']}** — {res['status']}")
            if res.get("video_path") and os.path.exists(res["video_path"]):
                st.video(res["video_path"])
            if res.get("link"):
                st.markdown(f"[Watch on YouTube]({res['link']})")
            st.markdown("---")
