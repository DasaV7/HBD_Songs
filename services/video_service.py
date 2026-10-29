def create_video(name: str, message: str, audio_file: str):
    audio = AudioFileClip(audio_file)
    total_duration = audio.duration

    # ---------- Collect media ----------
    background_images = get_media_files("assets/backgrounds", (".jpg", ".jpeg", ".png"))
    video_clips_list = get_media_files("assets/videos", (".mp4", ".mov", ".avi", ".mkv"))
    video_clips_list += get_media_files("assets/shorts", (".mp4", ".mov", ".avi", ".mkv"))

    print("=== DEBUG INFO ===")
    print(f"Found images: {len(background_images)}")
    print(f"Found videos: {len(video_clips_list)}")
    print("Video files:", video_clips_list)

    if len(background_images) < 3:
        raise Exception("Need at least 3 images in assets/backgrounds")

    random.shuffle(background_images)
    random.shuffle(video_clips_list)

    used_files = {
        "audio": os.path.basename(audio_file),
        "images": [],
        "videos": []
    }

    clips = []
    remaining_duration = total_duration

    # 1. Opening slide (shorter so we have more room for videos)
    used_files["images"].append(os.path.basename(background_images[0]))
    slide1 = create_slide(
        f"Happy Birthday\n{name}",
        background_images[0],
        min(5, remaining_duration * 0.15),
        "generated/slide1.png"
    )
    clips.append(slide1)
    remaining_duration -= slide1.duration

    # 2. FORCE insert videos if available
    videos_added = 0
    for video_path in video_clips_list:
        if videos_added >= 2 or remaining_duration < 5:
            break

        try:
            print(f"Trying to load video: {video_path}")
            vclip = VideoFileClip(video_path)

            # Take a reasonable portion
            desired_len = min(8, vclip.duration, remaining_duration * 0.35)
            if desired_len < 3:
                vclip.close()
                continue

            start = 0 if vclip.duration <= desired_len else random.uniform(0, max(0.1, vclip.duration - desired_len))

            vclip = (vclip
                     .subclip(start, start + desired_len)
                     .resize(height=720)
                     .fadein(0.5)
                     .fadeout(0.5))

            # Center if needed
            if vclip.w < 1280:
                bg = (ImageClip(background_images[videos_added % len(background_images)])
                      .set_duration(vclip.duration)
                      .resize((1280, 720)))
                vclip = vclip.set_position("center")
                vclip = CompositeVideoClip([bg, vclip])

            clips.append(vclip)
            used_files["videos"].append(os.path.basename(video_path))
            remaining_duration -= vclip.duration
            videos_added += 1
            print(f"Successfully added video: {os.path.basename(video_path)}")

        except Exception as e:
            print(f"Failed to load video {video_path}: {str(e)}")
            continue

    # 3. Message slide
    if remaining_duration > 4:
        used_files["images"].append(os.path.basename(background_images[1]))
        slide_msg = create_slide(
            message[:55] + ("..." if len(message) > 55 else ""),
            background_images[1],
            min(6, remaining_duration * 0.3),
            "generated/slide_msg.png"
        )
        clips.append(slide_msg)
        remaining_duration -= slide_msg.duration

    # 4. Closing slides
    if remaining_duration > 3:
        used_files["images"].append(os.path.basename(background_images[2]))
        slide_close = create_slide(
            "Celebrate Your\nSpecial Day!",
            background_images[2],
            remaining_duration * 0.55,
            "generated/slide_close.png"
        )
        clips.append(slide_close)
        remaining_duration -= slide_close.duration

    if remaining_duration > 2:
        used_files["images"].append(os.path.basename(background_images[0]))
        slide_end = create_slide(
            f"Thank You\n{name} 💖",
            background_images[0],
            remaining_duration,
            "generated/slide_end.png"
        )
        clips.append(slide_end)

    # ---------- Final assembly ----------
    if not clips:
        raise Exception("No clips were created")

    final_video = concatenate_videoclips(clips, method="compose")
    final_video = final_video.set_audio(audio)

    if final_video.duration > audio.duration:
        final_video = final_video.subclip(0, audio.duration)

    safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).replace(" ", "_")
    output_path = f"generated/{safe_name}.mp4"

    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="generated/temp_audio.m4a",
        remove_temp=True,
        threads=4,
        logger=None
    )
    
    video_path, used_files = create_video(name, message, audio_file)

    st.write("### Debug - Used Files")
    st.json(used_files)

    final_video.close()
    audio.close()

    return output_path, used_files
