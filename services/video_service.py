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

    LEFT_X = 80
    RIGHT_X = 1180          # Safe right edge
    TOP_Y = 150
    BOTTOM_Y = 390
    MIDDLE_Y = 280

    if "top left" in name:
        return RIGHT_X, BOTTOM_Y, "right"
    elif "top right" in name:
        return LEFT_X, BOTTOM_Y, "left"
    elif "bottom left" in name:
        return RIGHT_X, TOP_Y, "right"
    elif "bottom right" in name:
        return LEFT_X, TOP_Y, "left"
    elif "left" in name and "right" not in name:
        return RIGHT_X, MIDDLE_Y, "right"
    elif "right" in name and "left" not in name:
        return LEFT_X, MIDDLE_Y, "left"
    else:
        return LEFT_X, 160 if is_end else 240, "left"


def create_slide(text, background, duration, output_file, is_end=False):
    img = Image.open(background).convert("RGBA")
    img = img.resize((1280, 720), Image.LANCZOS)

    dark = Image.new("RGBA", img.size, (0, 0, 0, 95))
    img = Image.alpha_composite(img, dark)
    draw = ImageDraw.Draw(img)

    # Font size
    font_size = 40 if is_end else 60

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
    x_pos, y_pos, align = get_text_position(filename, is_end=is_end)

    # Measure text
    try:
        bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=12, align=align)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except:
        text_width = 500
        text_height = 150

    # ========== STRICT SAFE AREA ==========
    SAFE_LEFT = 70
    SAFE_RIGHT = 1210
    SAFE_TOP = 120
    SAFE_BOTTOM = 580

    if align == "right":
        # Force right edge to stay inside the frame
        x_pos = min(x_pos, SAFE_RIGHT)
        # Ensure the whole text block fits
        if (x_pos - text_width) < SAFE_LEFT:
            x_pos = SAFE_LEFT + text_width
            x_pos = min(x_pos, SAFE_RIGHT)
    else:
        x_pos = max(SAFE_LEFT, min(x_pos, SAFE_RIGHT - text_width))

    y_pos = max(SAFE_TOP, min(y_pos, SAFE_BOTTOM - text_height))

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
