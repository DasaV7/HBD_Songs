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

    img.thumbnail((1280,720))

    canvas = Image.new(
        "RGB",
        (1280,720),
        (0,0,0)
    )

    x_img = (1280 - img.width)//2
    y_img = (720 - img.height)//2

    canvas.paste(
        img,
        (x_img,y_img)
    )

    img = canvas.convert("RGBA")

    overlay = Image.new(
        "RGBA",
        img.size,
        (0,0,0,120)
    )

    img = Image.alpha_composite(
        img,
        overlay
    )

    draw = ImageDraw.Draw(img)

    COLORS = [
        "#0A84FF",
        "#64D2FF",
        "#5E5CE6",
        "#BF5AF2",
        "#FF375F",
        "#30D158",
        "#FFD60A"
    ]

    text_color = random.choice(
        COLORS
    )

    try:
        font = ImageFont.truetype(
            "DejaVuSans-Bold.ttf",
            240
        )
    except:
        font = ImageFont.load_default()

    bbox = draw.multiline_textbbox(
        (0,0),
        text,
        font=font
    )

    text_width = bbox[2]-bbox[0]
    text_height = bbox[3]-bbox[1]

    x = (
        1280 - text_width
    ) // 2

    y = (
        720 - text_height
    ) // 2

    # Shadow
    # draw.multiline_text(
    #     (x,y),
    #     text,
    #     fill="#FFD60A",
    #     font=font,
    #     align="center",
    #     stroke_width=6,
    #     stroke_fill="black"
    # )
    # draw.multiline_text(
    #     (x+2,y+1),
    #     text,
    #     fill=(0,0,0),
    #     font=font,
    #     align="center"
    # )

    # Main Text

    # draw.multiline_text(
    #     (x,y),
    #     text,
    #     fill=text_color,
    #     font=font,
    #     align="center"
    # )
    draw.multiline_text(
        (x,y),
        text,
        fill="#FFD60A",
        font=font,
        align="center",
        stroke_width=6,
        stroke_fill="black"
    )

    img = img.convert(
        "RGB"
    )

    try:
        confetti = Image.open(
            "assets/overlays/confetti.png"
        )
    
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
        
    img.save(
        output_file
    )

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

    final_video.write_videofile(
        output,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )

    return output
