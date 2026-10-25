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
    
    img.thumbnail((1280, 720))
    
    canvas = Image.new(
        "RGB",
        (1280,720),
        (20,20,20)
    )
    
    x = (1280 - img.width) // 2
    y = (720 - img.height) // 2
    
    canvas.paste(img, (x,y))
    
    img = canvas

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(
            "DejaVuSans-Bold.ttf",
            110
        )
    except:
        font = ImageFont.load_default()

    bbox = draw.multiline_textbbox(
        (0, 0),
        text,
        font=font
    )
    
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (1280 - text_width) // 2
    y = (720 - text_height) // 2
    
    draw.multiline_text(
        (x+4, y+4),
        text,
        fill="black",
        font=font,
        align="center"
    )
    
    draw.multiline_text(
        (x, y),
        text,
        fill="white",
        font=font,
        align="center"
    )

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
            f"🎂 Happy Birthday {name} 🎂",
            images[0],
            slide_duration,
            "generated/slide1.png"
        ),
    
        create_slide(
            "Wishing You Joy & Happiness",
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
            "Celebrate Your Special Day!",
            images[3],
            slide_duration,
            "generated/slide4.png"
        ),
    
        create_slide(
            f"Thank You {name}\nHave A Wonderful Year Ahead",
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
