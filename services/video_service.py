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

    os.makedirs(
        "generated",
        exist_ok=True
    )

    background = get_random_background()

    audio = AudioFileClip(
        audio_file
    )

    duration = audio.duration

    clip = (
        ImageClip(background)
        .set_duration(duration)
    )

    clip = clip.resize(
        width=1280
    )

    txt_image = Image.new(
        "RGBA",
        (1280,720),
        (0,0,0,0)
    )

    draw = ImageDraw.Draw(
        txt_image
    )

    try:

        font = ImageFont.truetype(
            "DejaVuSans.ttf",
            80
        )

    except:

        font = ImageFont.load_default()

    draw.text(
        (150,250),
        f"🎂 Happy Birthday\n{name}",
        font=font,
        fill="white"
    )

    text_path = (
        f"generated/{name}_text.png"
    )

    txt_image.save(
        text_path
    )

    text_clip = (
        ImageClip(text_path)
        .set_duration(duration)
    )

    final = CompositeVideoClip(
        [
            clip,
            text_clip
        ]
    )

    final = final.set_audio(
        audio
    )

    output = (
        f"generated/{name}.mp4"
    )

    final.write_videofile(
        output,
        fps=24
    )

    return output
