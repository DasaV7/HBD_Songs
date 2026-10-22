from moviepy.editor import *
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from services.assets_service import (
    get_random_background
)

import os


def create_video(
        name,
        audio_file):

    background = get_random_background()

    audio = AudioFileClip(
        audio_file
    )

    duration = audio.duration

    clip = (
        ImageClip(background)
        .set_duration(duration)
    )

    txt = Image.new(
        "RGBA",
        (1280, 720),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(txt)

    try:
        font = ImageFont.truetype(
            "DejaVuSans.ttf",
            70
        )
    except:
        font = ImageFont.load_default()

    draw.text(
        (100, 250),
        f"🎂 Happy Birthday\n{name}",
        fill="white",
        font=font
    )

    text_file = (
        f"generated/{name}_text.png"
    )

    txt.save(text_file)

    text_clip = (
        ImageClip(text_file)
        .set_duration(duration)
    )

    final = CompositeVideoClip(
        [
            clip,
            text_clip
        ]
    )

    final.audio = audio

    output = (
        f"generated/{name}.mp4"
    )

    final.write_videofile(
        output,
        codec="libx264",
        audio_codec="aac",
        fps=24
    )

    return output
