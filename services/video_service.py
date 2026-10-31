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
import math


COLORS = [
    "#FF9AA2", "#FFDAC1", "#E2F0CB", "#B5EAD7",
    "#C7CEEA", "#A0C4FF", "#FFD6A5", "#FFB7B2",
    "#FF8FAB", "#FDE4CF", "#FFD700", "#FF69B4"
]

FONT_CANDIDATES = [
    "assets/fonts/Poppins-SemiBold.ttf",
    "assets/fonts/Poppins-Bold.ttf",
    "assets/fonts/Montserrat-Bold.ttf",
    "assets/fonts/Montserrat-SemiBold.ttf",
]


def get_media_files(folder, extensions):
    if not os.path.exists(folder):
        return []
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(extensions)
    ]


def draw_confetti(draw, width=1280, height=720, count=80):
    """Draw simple colorful confetti particles"""
    for _ in range(count):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(4, 12)
        color = random.choice(COLORS)
        shape = random.choice(["rect", "circle"])

        if shape == "rect":
            draw.rectangle([x, y, x + size, y + size//2], fill=color)
        else:
            draw.ellipse([x, y, x + size, y + size], fill=color)


def draw_sparkles(draw, width=1280, height=720, count=25):
    """Draw small sparkle/star effects"""
    for _ in range(count):
        x = random.randint(50, width - 50)
        y = random.randint(50, height - 50)
        size = random.randint(3, 7)
        color = random.choice(["#FFD700", "#FFFFFF", "#FFE4B5"])
        
        # Simple cross sparkle
        draw.line([(x - size, y), (x + size, y)], fill=color, width=2)
        draw.line([(x, y - size), (x, y + size)], fill=color, width=2)


def create_slide(text, background, duration, output_file):
    img = Image.open(background).convert("RGBA")
    img = img.resize((1280, 720), Image.LANCZOS)

    # Soft dark overlay
    dark = Image.new("RGBA", img.size, (0, 0, 0, 95))
    img = Image.alpha_composite(img, dark)

    draw = ImageDraw.Draw(img)

    # Load a random available font
    font = None
    for fpath in FONT_CANDIDATES:
        try:
            font = ImageFont.truetype(fpath, random.randint(64, 74))
            break
        except:
            continue
    if font is None:
        font = ImageFont.load_default()

    # Random text position (still readable)
    x_pos = random.randint(60, 100)
    y_pos = random.randint(200, 260)

    # Draw text with slight shadow for elegance
    shadow_color = (0, 0, 0, 180)
    draw.multiline_text((x_pos+3, y_pos+3), text, font=font, fill=shadow_color, spacing=14, align="center")
    draw.multiline_text((x_pos, y_pos), text, font=font, fill=random.choice(COLORS), spacing=14, align="center")

    # Elegant frame
    draw.rounded_rectangle(
        (40, 140, 1240, 580),
        radius=28,
        outline=(255, 255, 255, 160),
        width=3
    )

    # Programmatic confetti + sparkles (elegant, not too much)
    draw_confetti(draw, count=random.randint(40, 70))
    draw_sparkles(draw, count=random.randint(15, 25))

    img = img.convert("RGB")
    img.save(output_file, quality=95)

    # Ken Burns slow zoom
    clip = ImageClip(output_file).set_duration(duration)
    zoom_factor = random.uniform(1.07, 1.14)
    clip = clip.resize(lambda t: 1 + (zoom_factor - 1) * t / duration)
    clip = clip.fadein(1.1).fadeout(1.1)

    return clip


def create_video(name: str, message: str, audio_file: str):
    for f in os.listdir("generated"):
        if f.startswith("slide"):
            try:
                os.remove(os.path.join("generated", f))
            except:
                pass

    audio = AudioFileClip(audio_file)
    background_images = get_media_files("assets/backgrounds", (".jpg", ".jpeg", ".png"))

    if len(background_images) < 5:
        raise Exception("Need at least 5 images in assets/backgrounds")

    random.shuffle(background_images)

    used_files = {
        "audio": os.path.basename(audio_file),
        "images": [],
        "videos": []
    }

    slide_texts = [
        f"Happy Birthday\n{name}",
        "Wishing You\nAll the Happiness",
        message,
        "May Your Day\nBe Filled with Joy",
        "Celebrate in\nStyle Today!",
        f"Cheers to You\n{name}",
        "Lots of Love\n& Best Wishes",
        "Have an Amazing\nBirthday!",
        f"Thank You\n{name} 💖",
        "Enjoy Your\nSpecial Day!"
    ]

    clips = []
    slide_duration = 17

    for i, text in enumerate(slide_texts):
        bg = background_images[i % len(background_images)]
        used_files["images"].append(os.path.basename(bg))

        slide = create_slide(text, bg, slide_duration, f"generated/slide_{i}.png")
        clips.append(slide)

    base_video = concatenate_videoclips(clips, method="compose")

    if audio.duration < base_video.duration:
        loops = int(base_video.duration // audio.duration) + 1
        audio = concatenate_audioclips([audio] * loops)

    audio = audio.subclip(0, base_video.duration)
    base_video = base_video.set_audio(audio)

    final_video = concatenate_videoclips([base_video, base_video])

    safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).replace(" ", "_")
    output_path = f"generated/{safe_name}.mp4"

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

    final_video.close()
    base_video.close()
    audio.close()

    return output_path, used_files
