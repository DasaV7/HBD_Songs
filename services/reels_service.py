import os
import random

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips
)


# ======================================
# CONFIG
# ======================================

VERTICAL_W = 1080
VERTICAL_H = 1920

FONT_PATHS = [
    "assets/fonts/Poppins-Bold.ttf",
    "assets/fonts/Montserrat-Bold.ttf"
]


# ======================================
# FONT HELPER
# ======================================

def get_font(size):

    for path in FONT_PATHS:

        try:
            return ImageFont.truetype(path, size)

        except:
            continue

    return ImageFont.load_default()


# ======================================
# IMAGE TO VERTICAL CLIP
# ======================================

def slide_to_vertical(slide_path):

    clip = ImageClip(slide_path)

    clip = clip.resize(height=VERTICAL_H)

    if clip.w > VERTICAL_W:

        clip = clip.crop(
            x_center=clip.w / 2,
            width=VERTICAL_W,
            height=VERTICAL_H
        )

    return clip


# ======================================
# INSTAGRAM POST
# ======================================

def create_instagram_post(name):

    output_path = f"generated/{name}_post.jpg"

    img = Image.new(
        "RGB",
        (1080, 1080),
        (255, 239, 245)
    )

    draw = ImageDraw.Draw(img)

    title_font = get_font(90)

    text = (
        "🎂\n\n"
        f"Happy Birthday\n{name}"
    )

    draw.multiline_text(
        (150, 280),
        text,
        fill=(120, 80, 140),
        font=title_font,
        align="center"
    )

    draw.text(
        (120, 920),
        "Follow for Daily Birthday Videos",
        fill=(90, 90, 90),
        font=get_font(42)
    )

    img.save(output_path)

    return output_path


# ======================================
# OUTRO SLIDE
# ======================================

def create_reel_outro(name):

    outro_path = f"generated/{name}_reel_outro.png"

    image = Image.new(
        "RGB",
        (1080, 1920),
        (35, 35, 35)
    )

    draw = ImageDraw.Draw(image)

    font = get_font(60)

    outro_text = (
        "🎉 Enjoyed This Birthday Video?\n\n"
        "❤️ Follow For Daily Birthdays\n\n"
        "💬 Comment Your Name Below\n\n"
        "▶ Watch Full Video On YouTube\n\n"
        "🌐 hbdsongs.streamlit.app"
    )

    draw.multiline_text(
        (70, 550),
        outro_text,
        fill="white",
        font=font,
        align="center"
    )

    image.save(outro_path)

    return outro_path


# ======================================
# INSTAGRAM REEL
# ======================================

def create_instagram_reel(
        name,
        audio_file
):

    slide_files = []

    intro_slide = "generated/slide_intro.png"

    if os.path.exists(intro_slide):
        slide_files.append(intro_slide)

    available_main = []

    for i in range(8):

        slide_path = f"generated/slide_{i}.png"

        if os.path.exists(slide_path):
            available_main.append(slide_path)

    random.shuffle(available_main)

    selected = available_main[
        :random.randint(4, 6)
    ]

    slide_files.extend(selected)

    clips = []

    # INTRO

    intro = (
        slide_to_vertical(slide_files[0])
        .set_duration(3)
        .fadein(0.4)
        .fadeout(0.4)
    )

    clips.append(intro)

    # MID SLIDES

    for slide in slide_files[1:]:

        clip = (
            slide_to_vertical(slide)
            .set_duration(2.5)
            .fadein(0.4)
            .fadeout(0.4)
        )

        clips.append(clip)

    # OUTRO

    outro_img = create_reel_outro(name)

    outro_clip = (
        ImageClip(outro_img)
        .set_duration(4)
        .fadein(0.6)
        .fadeout(0.6)
    )

    clips.append(outro_clip)

    reel = concatenate_videoclips(
        clips,
        method="compose",
        padding=-0.25
    )

    # AUDIO

    if os.path.exists(audio_file):

        audio = AudioFileClip(audio_file)

        audio = audio.subclip(
            0,
            min(audio.duration, reel.duration)
        )

        reel = reel.set_audio(audio)

    output_path = f"generated/{name}_reel.mp4"

    reel.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="ultrafast",
        logger=None
    )

    reel.close()

    return output_path
