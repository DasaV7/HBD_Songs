# services/video_service.py

from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
    concatenate_audioclips
)

from PIL import ImageDraw, ImageFont
import random
import os
import re


COLORS = [
    "#FF9AA2", "#FFDAC1", "#E2F0CB", "#B5EAD7",
    "#C7CEEA", "#A0C4FF", "#FFD6A5", "#FFB7B2",
    "#FFD700", "#FF69B4"
]

FONT_CANDIDATES = [
    "assets/fonts/Poppins-Bold.ttf",
    "assets/fonts/Poppins-SemiBold.ttf",
    "assets/fonts/Montserrat-Bold.ttf",
]


def get_media_files(folder, extensions):
    if not os.path.exists(folder):
        return []
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(extensions)
    ]

def get_text_position(filename: str, is_end: bool = False):
    name = filename.lower().replace("_", " ").replace("-", " ").replace(".", " ")

    if "top left" in name:
        return "right", 390
    elif "top right" in name:
        return "left", 390
    elif "bottom left" in name:
        return "right", 150
    elif "bottom right" in name:
        return "left", 150
    elif "left" in name and "right" not in name:
        return "right", 280
    elif "right" in name and "left" not in name:
        return "left", 280
    else:
        return "left", 160 if is_end else 240


def create_slide(text, background, duration, output_file, is_end=False):
    img = Image.open(background).convert("RGBA")
    img = img.resize((1280, 720), Image.LANCZOS)

    dark = Image.new("RGBA", img.size, (0, 0, 0, 90))
    img = Image.alpha_composite(img, dark)
    draw = ImageDraw.Draw(img)

    font_size = 40 if is_end else 56

    font = None
    for fpath in FONT_CANDIDATES:
        try:
            font = ImageFont.truetype(fpath, font_size)
            break
        except:
            continue
    if font is None:
        font = ImageFont.load_default()

    filename = os.path.basename(background)
    side, y_pos = get_text_position(filename, is_end=is_end)

    lines = text.split("\n")

    # ========== TRUE RIGHT ALIGNMENT (safe) ==========
    if side == "right":
        right_edge = 1190          # safe right edge inside white box
        align = "right"

        # Find the widest line
        max_width = 0
        for line in lines:
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]
                if w > max_width:
                    max_width = w
            except:
                max_width = 500

        # Calculate starting x so the longest line ends at right_edge
        x_pos = right_edge - max_width
        if x_pos < 60:
            x_pos = 60

    else:
        x_pos = 80
        align = "left"

    # Vertical position
    try:
        bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=12)
        text_height = bbox[3] - bbox[1]
    except:
        text_height = 140

    y_pos = max(120, min(y_pos, 580 - text_height))

    # Draw shadow
    draw.multiline_text(
        (x_pos + 3, y_pos + 3),
        text,
        font=font,
        fill=(0, 0, 0, 180),
        spacing=12,
        align=align
    )

    # Main text
    draw.multiline_text(
        (x_pos, y_pos),
        text,
        font=font,
        fill=random.choice(COLORS),
        spacing=12,
        align=align
    )

    # Frame
    if is_end:
        draw.rounded_rectangle((30, 90, 1250, 630), radius=25, outline=(255, 255, 255, 160), width=3)
    else:
        draw.rounded_rectangle((40, 110, 1240, 610), radius=25, outline=(255, 255, 255, 150), width=3)

    img = img.convert("RGB")
    img.save(output_file, quality=90)

    clip = (ImageClip(output_file)
            .set_duration(duration)
            .fadein(0.8)
            .fadeout(0.8))
    return clip
    

def create_video(name: str, message: str, audio_file: str, repeats: int = 1):
    repeats = max(1, min(5, int(repeats)))

    # Clean old files
    for f in os.listdir("generated"):
        if f.startswith("slide") or f.endswith(".mp4"):
            try:
                os.remove(os.path.join("generated", f))
            except:
                pass

    audio = AudioFileClip(audio_file)
    background_images = get_media_files("assets/backgrounds", (".jpg", ".jpeg", ".png"))

    if len(background_images) < 5:
        raise Exception("Need at least 5 background images")

    random.shuffle(background_images)

    used_files = {
        "audio": os.path.basename(audio_file),
        "images": [],
        "videos": []
    }

    base_clips = []

    # 1. Intro
    intro_text = f"A Special Birthday Video\nFor\n{name}"
    base_clips.append(create_slide(intro_text, background_images[0], 7, "generated/slide_intro.png"))
    used_files["images"].append(os.path.basename(background_images[0]))

    # 2. Main slides
    main_texts = [
        f"Happy Birthday\n{name}",
        "Wishing You\nAll the Happiness",
        message,
        "May Your Day\nBe Full of Joy",
        "Celebrate Your\nSpecial Day!",
        f"Cheers to You\n{name}",
        "Lots of Love &\nBest Wishes",
        "Have an Amazing\nBirthday!"
    ]

    for i, text in enumerate(main_texts):
        bg = background_images[(i + 1) % len(background_images)]
        used_files["images"].append(os.path.basename(bg))
        base_clips.append(create_slide(text, bg, 12, f"generated/slide_{i}.png"))

    base_video = concatenate_videoclips(base_clips, method="compose")

    # Repeat
    if repeats > 1:
        main_part = concatenate_videoclips([base_video] * repeats, method="compose")
    else:
        main_part = base_video

    # End slide
    end_text = (
        "Thank You for Watching!\n\n"
        "Please Like • Share • Comment\n"
        "And Subscribe for more videos\n\n"
        "Request Custom Video:\n"
        "https://hbdsongs.streamlit.app"
    )
    end_clip = create_slide(end_text, background_images[-1], 14, "generated/slide_end.png", is_end=True)
    used_files["images"].append(os.path.basename(background_images[-1]))

    final_video = concatenate_videoclips([main_part, end_clip], method="compose")

    # Audio
    total_duration = final_video.duration
    if audio.duration < total_duration:
        loops = int(total_duration / audio.duration) + 1
        audio = concatenate_audioclips([audio] * loops)

    audio = audio.subclip(0, total_duration)
    final_video = final_video.set_audio(audio)

    # Export
    safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).replace(" ", "_")
    output_path = f"generated/{safe_name}.mp4"

    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="generated/temp-audio.m4a",
        remove_temp=True,
        threads=2,
        logger=None,
        preset="ultrafast"
    )

    final_video.close()
    audio.close()

    return output_path, used_files
