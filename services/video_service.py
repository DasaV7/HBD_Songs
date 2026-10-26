# services/video_service.py

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips
)

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import random
import os


# Apple-inspired colors
COLORS = [
    "#0A84FF",  # Blue
    "#64D2FF",  # Cyan
    "#5E5CE6",  # Indigo
    "#BF5AF2",  # Purple
    "#FF375F",  # Pink
    "#30D158",  # Green
    "#FFD60A"   # Yellow
]

def create_slide(
    text,
    background,
    duration,
    output_file
):

    img = Image.open(background)

    img = img.convert("RGBA")

    img = img.resize(
        (1280, 720),
        Image.LANCZOS
    )

    # Dark overlay
    overlay = Image.new(
        "RGBA",
        img.size,
        (0, 0, 0, 80)
    )

    img = Image.alpha_composite(
        img,
        overlay
    )

    draw = ImageDraw.Draw(img)

    # IMPORTANT
    # Verify exact filename:
    # assets/fonts/Montserrat-Bold.ttf

    font = ImageFont.truetype(
        "assets/fonts/Montserrat-Black.ttf",
        100
    )

    # Fixed position instead of bbox calculations

    draw.multiline_text(
        (80, 220),
        text.upper(),
        font=font,
        fill=(255,255,255),
        stroke_width=8,
        stroke_fill=(0,0,0),
        spacing=25
    )

    # Confetti overlay

    try:

        confetti = Image.open(
            "assets/overlays/confetti.png"
        )

        confetti = confetti.convert("RGBA")

        confetti = confetti.resize(
            (1280,720)
        )

        img.paste(
            confetti,
            (0,0),
            confetti
        )

    except:
        pass

    img = img.convert("RGB")

    img.save(output_file)

    clip = (
        ImageClip(output_file)
        .set_duration(duration)
        .fadein(1)
        .fadeout(1)
    )

    return clip


def create_video(
    name,
    message,
    audio_file
):

    audio = AudioFileClip(audio_file)

    duration = audio.duration

    slide_duration = duration / 5

    images = [
        os.path.join(
            "assets/backgrounds",
            f
        )
        for f in os.listdir(
            "assets/backgrounds"
        )
        if f.lower().endswith(
            (
                ".jpg",
                ".jpeg",
                ".png"
            )
        )
    ]

    if len(images) < 5:

        raise Exception(
            f"Need at least 5 images in assets/backgrounds. Found {len(images)}"
        )

    random.shuffle(images)

    slides = [

        create_slide(
            f"🎂\nHappy Birthday\n{name}",
            images[0],
            slide_duration,
            "generated/slide1.png"
        ),

        create_slide(
            "Wishing You\nJoy & Happiness",
            images[1],
            slide_duration,
            "generated/slide2.png"
        ),

        create_slide(
            message,
            images[2],
            slide_duration,
            "generated/slide3.png"
        ),

        create_slide(
            "Celebrate\nYour Special Day!",
            images[3],
            slide_duration,
            "generated/slide4.png"
        ),

        create_slide(
            f"Thank You\n{name}",
            images[4],
            slide_duration,
            "generated/slide5.png"
        )

    ]

    final_video = concatenate_videoclips(
        slides,
        method="compose"
    )

    final_video = final_video.set_audio(audio)

    safe_name = "".join(
        c for c in name
        if c.isalnum() or c in (" ", "_", "-")
    )

    safe_name = safe_name.replace(
        " ",
        "_"
    )

    output = f"generated/{safe_name}.mp4"

    # final_video.write_videofile(
    #     output,
    #     fps=24,
    #     codec="libx264",
    #     audio_codec="aac"
    # )
    final_video.write_videofile(
    output,
    fps=24,
    codec="libx264",
    audio_codec="aac",
    temp_audiofile="generated/temp_audio.m4a",
    remove_temp=True
    )

    return output
