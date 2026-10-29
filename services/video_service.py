# services/video_service.py

from moviepy.editor import (
    ImageClip,
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    CompositeVideoClip
)

from PIL import Image, ImageDraw, ImageFont
import random
import os


COLORS = [
    "#FF9AA2",  # pastel pink
    "#FFDAC1",  # peach
    "#E2F0CB",  # mint
    "#B5EAD7",  # aqua
    "#C7CEEA",  # lavender
    "#A0C4FF",  # sky blue
    "#FFD6A5"   # soft orange
]


def create_slide(text, background, duration, output_file):
    img = Image.open(background)
    img = img.convert("RGBA")
    img = img.resize((1280, 720), Image.LANCZOS)

    # Dark overlay
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 90))
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("assets/fonts/Poppins-SemiBold.ttf", 75)
    except:
        font = ImageFont.load_default()

    # Center-ish text
    draw.multiline_text(
        (100, 240),
        text,
        font=font,
        fill=random.choice(COLORS),
        spacing=18,
        align="center"
    )

    # Optional decorative frame
    draw.rounded_rectangle(
        (60, 160, 1220, 560),
        radius=40,
        outline=(255, 255, 255, 120),
        width=3
    )

    # Confetti overlay
    try:
        confetti = Image.open("assets/overlays/confetti.png").convert("RGBA")
        confetti = confetti.resize((1280, 720))
        img.paste(confetti, (0, 0), confetti)
    except:
        pass

    img = img.convert("RGB")
    img.save(output_file)

    clip = (
        ImageClip(output_file)
        .set_duration(duration)
        .fadein(0.8)
        .fadeout(0.8)
    )
    return clip


def get_media_files(folder, extensions):
    """Helper to get list of media files"""
    if not os.path.exists(folder):
        return []
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(extensions)
    ]


def create_video(name: str, message: str, audio_file: str):
    audio = AudioFileClip(audio_file)
    total_duration = audio.duration

    # ---------- Collect media ----------
    background_images = get_media_files("assets/backgrounds", (".jpg", ".jpeg", ".png"))
    video_clips_list = get_media_files("assets/videos", (".mp4", ".mov", ".avi", ".mkv"))
    # You can also put shorts in assets/shorts if you want
    video_clips_list += get_media_files("assets/shorts", (".mp4", ".mov", ".avi", ".mkv"))

    if len(background_images) < 3:
        raise Exception("Need at least 3 images in assets/backgrounds")

    random.shuffle(background_images)
    random.shuffle(video_clips_list)

    # ---------- Build timeline ----------
    # We will create a mix of slides + video clips
    clips = []
    remaining_duration = total_duration

    # 1. Opening slide
    slide1 = create_slide(
        f"Happy Birthday\n{name}",
        background_images[0],
        min(6, remaining_duration * 0.18),
        "generated/slide1.png"
    )
    clips.append(slide1)
    remaining_duration -= slide1.duration

    # 2. Insert 1-2 short video clips if available
    for i, video_path in enumerate(video_clips_list[:2]):
        if remaining_duration < 4:
            break
        try:
            vclip = VideoFileClip(video_path)
            
            # Take a random short portion (max 6-8 seconds)
            max_len = min(7, vclip.duration, remaining_duration * 0.25)
            start = 0 if vclip.duration <= max_len else random.uniform(0, vclip.duration - max_len)
            
            vclip = (vclip
                     .subclip(start, start + max_len)
                     .resize(height=720)
                     .fadein(0.6)
                     .fadeout(0.6))
            
            # Center the video if needed
            if vclip.w < 1280:
                vclip = vclip.set_position("center")
                bg = ImageClip(background_images[(i+1) % len(background_images)]).set_duration(vclip.duration).resize((1280,720))
                vclip = CompositeVideoClip([bg, vclip])

            clips.append(vclip)
            remaining_duration -= vclip.duration
        except Exception as e:
            print(f"Skipping video {video_path}: {e}")
            continue

    # 3. Message slide
    if remaining_duration > 3:
        slide_msg = create_slide(
            message[:60] + ("..." if len(message) > 60 else ""),
            background_images[1],
            min(7, remaining_duration * 0.3),
            "generated/slide_msg.png"
        )
        clips.append(slide_msg)
        remaining_duration -= slide_msg.duration

    # 4. Another video clip if time left
    if video_clips_list and remaining_duration > 5:
        try:
            vclip = VideoFileClip(video_clips_list[-1])
            max_len = min(8, vclip.duration, remaining_duration * 0.4)
            start = 0 if vclip.duration <= max_len else random.uniform(0, vclip.duration - max_len)
            vclip = (vclip.subclip(start, start + max_len)
                         .resize(height=720)
                         .fadein(0.5)
                         .fadeout(0.5))
            clips.append(vclip)
            remaining_duration -= vclip.duration
        except:
            pass

    # 5. Closing slides
    if remaining_duration > 3:
        slide_close = create_slide(
            "Celebrate Your\nSpecial Day!",
            background_images[2],
            remaining_duration * 0.5,
            "generated/slide_close.png"
        )
        clips.append(slide_close)
        remaining_duration -= slide_close.duration

    if remaining_duration > 2:
        slide_end = create_slide(
            f"Thank You\n{name} 💖",
            background_images[0],
            remaining_duration,
            "generated/slide_end.png"
        )
        clips.append(slide_end)

    # ---------- Final assembly ----------
    final_video = concatenate_videoclips(clips, method="compose")
    final_video = final_video.set_audio(audio)

    # Make sure duration matches audio
    if final_video.duration > audio.duration:
        final_video = final_video.subclip(0, audio.duration)

    # Safe filename
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

    # Cleanup
    final_video.close()
    audio.close()

    return output_path
