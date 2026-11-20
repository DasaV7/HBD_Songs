# services/reels_service.py

import os
import random
from PIL import Image, ImageDraw, ImageFont
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
    "assets/fonts/Poppins-SemiBold.ttf",
    "assets/fonts/Montserrat-Bold.ttf",
]

COLORS = [
    "#FF9AA2", "#FFDAC1", "#E2F0CB", "#B5EAD7",
    "#C7CEEA", "#A0C4FF", "#FFD6A5", "#FFB7B2",
    "#FFD700", "#FF69B4", "#FFFFFF"
]


# ======================================
# HELPERS
# ======================================

def get_font(size: int):
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def get_media_files(folder, extensions):
    if not os.path.exists(folder):
        return []
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(extensions)
    ]


def fit_cover(img: Image.Image, target_w=VERTICAL_W, target_h=VERTICAL_H) -> Image.Image:
    """Cover crop that keeps aspect ratio and fills the frame."""
    img_w, img_h = img.size
    scale = max(target_w / img_w, target_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def create_vertical_slide(
    text: str,
    background_path: str,
    output_path: str,
    is_outro: bool = False
) -> str:
    """
    Creates a clean 1080×1920 slide with properly fitted text.
    """
    img = Image.open(background_path).convert("RGBA")
    img = fit_cover(img, VERTICAL_W, VERTICAL_H)

    # Soft dark overlay so text is readable
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 110 if is_outro else 90))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Font size depends on whether it is outro or normal slide
    if is_outro:
        font_size = 52
        y_start = 480
    else:
        font_size = 68
        y_start = 620

    font = get_font(font_size)
    lines = text.strip().split("\n")

    # Measure total text height for better centering
    try:
        bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=18, align="center")
        text_height = bbox[3] - bbox[1]
    except Exception:
        text_height = len(lines) * (font_size + 18)

    # Keep text nicely inside the safe area
    y_pos = max(180, min(y_start, VERTICAL_H - text_height - 200))

    # Shadow
    draw.multiline_text(
        (VERTICAL_W // 2 + 4, y_pos + 4),
        text,
        font=font,
        fill=(0, 0, 0, 200),
        spacing=18,
        align="center",
        anchor="ma"
    )

    # Main text
    draw.multiline_text(
        (VERTICAL_W // 2, y_pos),
        text,
        font=font,
        fill=random.choice(COLORS),
        spacing=18,
        align="center",
        anchor="ma"
    )

    # Elegant frame
    draw.rounded_rectangle(
        (40, 80, VERTICAL_W - 40, VERTICAL_H - 80),
        radius=40,
        outline=(255, 255, 255, 160),
        width=3
    )

    img = img.convert("RGB")
    img.save(output_path, quality=92)
    return output_path


# ======================================
# INSTAGRAM POST (1080×1080)
# ======================================

def create_instagram_post(name: str) -> str:
    output_path = f"generated/{name}_post.jpg"

    img = Image.new("RGB", (1080, 1080), (255, 239, 245))
    draw = ImageDraw.Draw(img)

    title_font = get_font(78)
    subtitle_font = get_font(38)

    text = f"🎂\nHappy Birthday\n{name}"
    draw.multiline_text(
        (540, 420),
        text,
        fill=(120, 80, 140),
        font=title_font,
        align="center",
        anchor="mm",
        spacing=12
    )

    draw.text(
        (540, 920),
        "Follow for Daily Birthday Videos",
        fill=(90, 90, 90),
        font=subtitle_font,
        anchor="mm"
    )

    img.save(output_path, quality=92)
    return output_path


# ======================================
# INSTAGRAM REEL (1080×1920)
# ======================================

def create_instagram_reel(name: str, audio_file: str) -> str:
    os.makedirs("generated", exist_ok=True)

    # Load vertical backgrounds
    backgrounds = get_media_files(
        "assets/reels_backgrounds",
        (".jpg", ".jpeg", ".png")
    )

    if len(backgrounds) < 3:
        raise Exception(
            "Need at least 3 images in assets/reels_backgrounds/ "
            "for Instagram Reels."
        )

    random.shuffle(backgrounds)

    clips = []
    used_bgs = []

    # ---------- Intro ----------
    intro_text = f"A Special Birthday Video\nFor\n{name}"
    intro_path = f"generated/{name}_reel_intro.png"
    create_vertical_slide(intro_text, backgrounds[0], intro_path)
    used_bgs.append(backgrounds[0])

    intro_clip = (
        ImageClip(intro_path)
        .set_duration(3.2)
        .fadein(0.5)
        .fadeout(0.5)
    )
    clips.append(intro_clip)

    # ---------- Main slides ----------
    main_texts = [
        f"Happy Birthday\n{name}",
        "Wishing You\nAll the Happiness",
        "May Your Day\nBe Full of Joy",
        "Celebrate Your\nSpecial Day!",
        f"Cheers to You\n{name}",
        "Lots of Love &\nBest Wishes",
    ]

    # Use 4–5 main slides
    selected_texts = random.sample(main_texts, k=min(5, len(main_texts)))

    for i, text in enumerate(selected_texts):
        bg = backgrounds[(i + 1) % len(backgrounds)]
        slide_path = f"generated/{name}_reel_slide_{i}.png"
        create_vertical_slide(text, bg, slide_path)
        used_bgs.append(bg)

        clip = (
            ImageClip(slide_path)
            .set_duration(2.8)
            .fadein(0.4)
            .fadeout(0.4)
        )
        clips.append(clip)

    # ---------- Outro ----------
    outro_text = (
        "🎉 Enjoyed This Birthday Video?\n\n"
        "❤️ Follow For Daily Birthdays\n\n"
        "💬 Comment Your Name Below\n\n"
        "▶ Watch Full Video On YouTube\n\n"
        "🌐 hbdsongs.streamlit.app"
    )
    outro_path = f"generated/{name}_reel_outro.png"
    create_vertical_slide(outro_text, backgrounds[-1], outro_path, is_outro=True)

    outro_clip = (
        ImageClip(outro_path)
        .set_duration(4.5)
        .fadein(0.6)
        .fadeout(0.6)
    )
    clips.append(outro_clip)

    # Concatenate
    reel = concatenate_videoclips(clips, method="compose")

    # Audio
    if os.path.exists(audio_file):
        audio = AudioFileClip(audio_file)
        audio = audio.subclip(0, min(audio.duration, reel.duration))
        reel = reel.set_audio(audio)

    output_path = f"generated/{name}_reel.mp4"

    reel.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="ultrafast",
        threads=2,
        logger=None
    )

    reel.close()
    if os.path.exists(audio_file):
        try:
            audio.close()
        except Exception:
            pass

    return output_path
