# services/video_service.py

from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import (
    ImageClip,
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    CompositeVideoClip,
    concatenate_audioclips
)

from PIL import ImageDraw, ImageFont
import random
import os
import shutil


COLORS = [
    "#FF9AA2", "#FFDAC1", "#E2F0CB", "#B5EAD7",
    "#C7CEEA", "#A0C4FF", "#FFD6A5", "#FFB7B2"
]


def get_media_files(folder, extensions):
    if not os.path.exists(folder):
        return []
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(extensions)
    ]


def create_slide(text, background, duration, output_file):
    img = Image.open(background).convert("RGBA")
    img = img.resize((1280, 720), Image.LANCZOS)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 100))
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("assets/fonts/Poppins-SemiBold.ttf", 70)
    except:
        font = ImageFont.load_default()

    draw.multiline_text(
        (80, 230),
        text,
        font=font,
        fill=random.choice(COLORS),
        spacing=16,
        align="center"
    )

    draw.rounded_rectangle(
        (50, 150, 1230, 570),
        radius=35,
        outline=(255, 255, 255, 130),
        width=3
    )

    try:
        confetti = Image.open("assets/overlays/confetti.png").convert("RGBA")
        confetti = confetti.resize((1280, 720))
        img.paste(confetti, (0, 0), confetti)
    except:
        pass

    img = img.convert("RGB")
    img.save(output_file, quality=95)

    return (ImageClip(output_file)
            .set_duration(duration)
            .fadein(0.7)
            .fadeout(0.7))


def create_video(name: str, message: str, audio_file: str):
    # Clean previous temp files
    for f in os.listdir("generated"):
        if f.startswith("slide") or f.startswith("temp"):
            try:
                os.remove(os.path.join("generated", f))
            except:
                pass

    audio = AudioFileClip(audio_file)
    
    # We want final video around 10 minutes → make base ~5 min then loop
    target_base_duration = 5 * 60  # 5 minutes

    background_images = get_media_files("assets/backgrounds", (".jpg", ".jpeg", ".png"))
    video_clips_list = get_media_files("assets/videos", (".mp4", ".mov", ".avi", ".mkv"))
    video_clips_list += get_media_files("assets/shorts", (".mp4", ".mov", ".avi", ".mkv"))

    if len(background_images) < 5:
        raise Exception("Need at least 5 images in assets/backgrounds")

    random.shuffle(background_images)
    random.shuffle(video_clips_list)

    used_files = {
        "audio": os.path.basename(audio_file),
        "images": [],
        "videos": []
    }

    clips = []
    remaining = target_base_duration

    # ---------- 8-9 SLIDES + VIDEOS ----------
    slide_texts = [
        f"Happy Birthday\n{name}",
        "Wishing You\nAll the Happiness",
        message[:50] + ("..." if len(message) > 50 else ""),
        "May Your Day\nBe Filled with Joy",
        "Celebrate in\nStyle Today!",
        f"Cheers to You\n{name}",
        "Lots of Love\n& Best Wishes",
        f"Thank You\n{name} 💖",
        "Have an Amazing\nBirthday!"
    ]

    img_index = 0
    video_index = 0

    for i, text in enumerate(slide_texts):
        if remaining < 4:
            break

        # Insert a video every 3rd slide if available
        if video_clips_list and i % 3 == 1 and video_index < len(video_clips_list) and remaining > 8:
            try:
                vpath = video_clips_list[video_index]
                vclip = VideoFileClip(vpath)
                dur = min(7, vclip.duration, remaining * 0.2)
                start = 0 if vclip.duration <= dur else random.uniform(0, vclip.duration - dur)

                vclip = (vclip.subclip(start, start + dur)
                             .resize(height=720)
                             .fadein(0.5)
                             .fadeout(0.5))

                if vclip.w < 1280:
                    bg = ImageClip(background_images[img_index % len(background_images)]).set_duration(dur).resize((1280,720))
                    vclip = CompositeVideoClip([bg, vclip.set_position("center")])

                clips.append(vclip)
                used_files["videos"].append(os.path.basename(vpath))
                remaining -= dur
                video_index += 1
            except Exception as e:
                print(f"Video skip: {e}")

        # Normal slide
        bg = background_images[img_index % len(background_images)]
        used_files["images"].append(os.path.basename(bg))
        
        dur = min(8, remaining * 0.18)
        slide = create_slide(text, bg, dur, f"generated/slide_{i}.png")
        clips.append(slide)
        remaining -= dur
        img_index += 1

    if not clips:
        raise Exception("No clips created")

    # Create base video (~5 min)
    base_video = concatenate_videoclips(clips, method="compose")

    # Loop audio to match base duration if needed
    if audio.duration < base_video.duration:
        loops = int(base_video.duration // audio.duration) + 1
        audio = concatenate_audioclips([audio] * loops).subclip(0, base_video.duration)
    else:
        audio = audio.subclip(0, base_video.duration)

    base_video = base_video.set_audio(audio)

    # ---------- LOOP THE VIDEO TO MAKE ~10 MINUTES ----------
    final_video = concatenate_videoclips([base_video, base_video])

    safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).replace(" ", "_")
    output_path = f"generated/{safe_name}.mp4"

    # final_video.write_videofile(
    #     output_path,
    #     fps=24,
    #     codec="libx264",
    #     audio_codec="aac",
    #     temp_audiofile="generated/temp_audio.m4a",
    #     remove_temp=True,
    #     threads=4,
    #     logger=None,
    #     preset="medium"
    # )
    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="generated/temp_audio.m4a",
        remove_temp=True,
        threads=4,
        logger=None,
        preset="medium",
        ffmpeg_params=["-movflags", "+faststart"]
    )

    # Cleanup
    final_video.close()
    base_video.close()
    audio.close()

    return output_path, used_files
