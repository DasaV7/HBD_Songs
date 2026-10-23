from moviepy.editor import *
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import random
import os


def create_slide(
    text,
    background,
    duration,
    output_file
):

    img = Image.open(background)

    img = img.resize((1280,720))

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(
            "DejaVuSans.ttf",
            70
        )
    except:
        font = ImageFont.load_default()

    draw.text(
        (100,300),
        text,
        fill="white",
        font=font
    )

    img.save(output_file)

    return (
        ImageClip(output_file)
        .set_duration(duration)
        .fadein(1)
        .fadeout(1)
        .resize(lambda t: 1 + (0.05 * t)

def create_video(
        name,
        message,
        audio_file):

    audio = AudioFileClip(
        audio_file
    )

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

    random.shuffle(images)

    slides = [

        create_slide(
            f"🎂 Happy Birthday {name}",
            images[0],
            slide_duration,
            "generated/slide1.png"
        ),

        create_slide(
            "Today Is Your Special Day",
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
            "Enjoy Your Celebration",
            images[3],
            slide_duration,
            "generated/slide4.png"
        ),

        create_slide(
            f"Thank You {name}",
            images[4],
            slide_duration,
            "generated/slide5.png"
        )
    ]

    final_video = concatenate_videoclips(
        slides,
        method="compose"
    )

    final_video = final_video.set_audio(
        audio
    )

    output = f"generated/{name}.mp4"

    final_video.write_videofile(
        output,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )

    return output
