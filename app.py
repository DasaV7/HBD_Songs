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
    reset_remaining_from_master
)

os.makedirs("generated", exist_ok=True)

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="Birthday Video Generator",
    page_icon="🎂",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-title {font-size: 2.2rem; font-weight: 700; text-align: center; margin-bottom: 0.2rem;}
    .sub-title {text-align: center; color: #888; margin-bottom: 1.5rem;}
    .stButton>button {border-radius: 8px; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

# ====================== LOGIN SYSTEM ======================
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = None

    if st.session_state.logged_in:
        return True

    st.markdown('<div class="main-title">🎂 Birthday Video Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Please login to continue</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            admin_user = st.secrets.get("ADMIN_USERNAME", "admin")
            admin_pass = st.secrets.get("ADMIN_PASSWORD", "admin123")
            user_user = st.secrets.get("USER_USERNAME", "user")
            user_pass = st.secrets.get("USER_PASSWORD", "user123")

            if username == admin_user and password == admin_pass:
                st.session_state.logged_in = True
                st.session_state.role = "admin"
                st.rerun()
            elif username == user_user and password == user_pass:
                st.session_state.logged_in = True
                st.session_state.role = "user"
                st.rerun()
            else:
                st.error("Invalid username or password")

    st.stop()

check_login()

# ====================== HEADER ======================
st.markdown('<div class="main-title">🎂 Birthday Video Generator</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">Logged in as: <b>{st.session_state.role.upper()}</b></div>', unsafe_allow_html=True)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

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
if "stats" not in st.session_state:
    st.session_state.stats = {"master": 0, "remaining": 0, "history": 0}

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("📋 Name Lists")

    # Safer: only refresh when button is clicked
    if st.button("🔄 Refresh Stats"):
        try:
            st.session_state.stats = get_stats()
            st.success("Stats updated!")
        except Exception as e:
            st.error(f"Failed to refresh: {e}")

    stats = st.session_state.stats
    st.metric("Master List", stats.get("master", 0))
    st.metric("Remaining", stats.get("remaining", 0))
    st.metric("History (Uploaded)", stats.get("history", 0))

    if st.session_state.role == "admin":
        st.markdown("---")
        if st.button("🔄 Reset Remaining from Master"):
            try:
                count = reset_remaining_from_master()
                st.session_state.stats = get_stats()  # refresh after reset
                st.success(f"Reset done! {count} names copied.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ====================== TABS ======================
if st.session_state.role == "admin":
    tab1, tab2 = st.tabs(["🚀 Manual Batch", "⏰ Daily Auto Mode"])
else:
    tab1 = st.container()
    tab2 = None

# ====================== MANUAL BATCH ======================
with tab1:
    st.markdown("### Manual Batch Processing")

    names_input = st.text_area("Enter names (one per line)", height=140, placeholder="Vikram\nSai\nAbhinav")

    col1, col2, col3 = st.columns(3)
    with col1:
        max_videos = st.selectbox("Number of videos", [2, 5, 10], index=0, key="manual_max")
    with col2:
        auto_upload = st.selectbox("Auto Upload", ["Enabled", "Disabled"], index=0, key="manual_upload")
    with col3:
        repeats = st.selectbox("Length Multiplier", [1, 2, 3], index=0, key="manual_repeats")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        start_btn = st.button("🚀 Start Batch", type="primary", use_container_width=True,
                              disabled=st.session_state.batch_running, key="start_manual")
    with col_b:
        if st.button("🛑 Stop", use_container_width=True, key="stop_manual"):
            st.session_state.stop_batch = True
            st.session_state.batch_running = False
    with col_c:
        if st.button("🗑️ Clear Results", use_container_width=True, key="clear_manual"):
            st.session_state.batch_results = []
            st.session_state.current_video = None
            st.session_state.batch_index = 0
            st.rerun()

    if start_btn:
        names = [n.strip() for n in names_input.strip().split("\n") if n.strip()]
        if not names:
            st.error("Please enter at least one name.")
            st.stop()

        st.session_state.batch_names = names[:max_videos]
        st.session_state.batch_index = 0
        st.session_state.batch_results = []
        st.session_state.batch_running = True
        st.session_state.stop_batch = False
        st.session_state.current_video = None
        st.session_state.auto_upload = (auto_upload == "Enabled")
        st.session_state.repeats = repeats
        st.session_state.is_daily_mode = False
        st.rerun()

# ====================== DAILY AUTO MODE (Admin only) ======================
if st.session_state.role == "admin" and tab2 is not None:
    with tab2:
        st.markdown("### Daily Automatic Mode")
        st.info("Takes next 2 names from Google Sheet → generates + uploads → moves to History.")

        col1, col2 = st.columns(2)
        with col1:
            auto_repeats = st.selectbox("Video Length", [1, 2, 3], index=0, key="auto_repeats")
        with col2:
            delay_minutes = st.number_input("Delay between videos (minutes)", min_value=5, max_value=60, value=15)

        st.write(f"**Remaining Names:** `{stats.get('remaining', 0)}`")

        if st.button("▶️ Run Daily Auto Batch Now", type="primary", use_container_width=True):
            today_names = select_next_names(count=2)
            if not today_names:
                st.error("No names left in Remaining sheet.")
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
            st.write("Creating lyrics & audio...")
            lyrics = generate_lyrics(current_name, personalized_message)
            audio_file = f"generated/{current_name}.mp3"
            asyncio.run(generate_audio(lyrics, audio_file))
            time.sleep(0.3)
        
            st.write("Rendering video...")
            video_path, used_files = create_video(
                current_name,
                personalized_message,
                audio_file,
                repeats=current_repeats
            )
            s.update(label="Video ready", state="complete")
        
        # ===== Generate Thumbnail AFTER the status block (safer) =====
        thumb_path = None
        try:
            from services.youtube_service import create_thumbnail
            safe_name = "".join(c for c in current_name if c.isalnum() or c in (" ", "_", "-")).replace(" ", "_")
            thumb_path = f"generated/{safe_name}_thumbnail.jpg"
            create_thumbnail(current_name, output_path=thumb_path)
        except Exception as e:
            st.warning(f"Thumbnail skipped: {e}")

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

                    # Always log to History
                    add_to_history(current_name, link or "")

                    # Only remove from Remaining in Daily mode
                    if is_daily:
                        remove_name_from_remaining(current_name)

                    s.update(label="Uploaded + History updated", state="complete")
                except Exception as e:
                    upload_status = f"❌ Upload failed: {e}"
                    s.update(label="Upload failed", state="error")
        result = {
            "name": current_name,
            "video_path": video_path,
            "thumbnail_path": thumb_path,          # ← add this
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

# ====================== RESULTS ======================
if st.session_state.batch_results:
    st.markdown("---")
    st.markdown("### Results")

    for res in st.session_state.batch_results:
        st.markdown(f"#### {res['name']} — {res['status']}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Video Preview**")
            if res.get("video_path") and os.path.exists(res["video_path"]):
                st.video(res["video_path"])
            else:
                st.info("Video not available")

        with col2:
            st.markdown("**Thumbnail Preview**")
            thumb_path = res.get("thumbnail_path")
            if thumb_path and os.path.exists(thumb_path):
                st.image(thumb_path, use_container_width=True)
            else:
                st.info("Thumbnail not available")

        if res.get("link"):
            st.markdown(f"[▶ Watch on YouTube]({res['link']})")

        st.markdown("---")

    # Status Table
    st.markdown("#### Upload Status Table")
    table_data = []
    for res in st.session_state.batch_results:
        table_data.append({
            "Name": res["name"],
            "Status": res["status"],
            "Date & Time": res.get("upload_time", "-"),
            "YouTube Link": res["link"] if res.get("link") else "-"
        })

    st.dataframe(
        table_data,
        use_container_width=True,
        column_config={
            "YouTube Link": st.column_config.LinkColumn("YouTube Link")
        }
    )
