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

from PIL import ImageDraw, ImageFont, ImageEnhance
import random
import os


COLORS = [
    "#FF9AA2", "#FFDAC1", "#E2F0CB", "#B5EAD7",
    "#C7CEEA", "#A0C4FF", "#FFD6A5", "#FFB7B2",
    "#FF8FAB", "#FDE4CF", "#FFD700", "#FF69B4"
]

FONT_CANDIDATES = [
    "assets/fonts/Poppins-Bold.ttf",
    "assets/fonts/Poppins-SemiBold.ttf",
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


def draw_confetti(draw, width=1280, height=720, count=60):
    for _ in range(count):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(5, 12)
        color = random.choice(COLORS)
        if random.random() > 0.5:
            draw.rectangle([x, y, x + size, y + size // 2], fill=color)
        else:
            draw.ellipse([x, y, x + size, y + size], fill=color)


def draw_sparkles(draw, width=1280, height=720, count=25):
    for _ in range(count):
        x = random.randint(40, width - 40)
        y = random.randint(40, height - 40)
        size = random.randint(4, 8)
        color = random.choice(["#FFD700", "#FFFFFF", "#FFF8DC"])
        draw.line([(x - size, y), (x + size, y)], fill=color, width=2)
        draw.line([(x, y - size), (x, y + size)], fill=color, width=2)


def apply_vignette(img):
    width, height = img.size
    vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vignette)
    for i in range(60):
        alpha = int(i * 1.5)
        draw.rectangle([i, i, width - i, height - i], outline=(0, 0, 0, alpha))
    return Image.alpha_composite(img.convert("RGBA"), vignette)


def create_slide(text, background, duration, output_file):
    img = Image.open(background).convert("RGBA")
    img = img.resize((1280, 720), Image.LANCZOS)

    dark = Image.new("RGBA", img.size, (0, 0, 0, 95))
    img = Image.alpha_composite(img, dark)

    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.12)

    draw = ImageDraw.Draw(img)

    # Smart font size
    if "Thank You for Watching" in text or "Subscribe" in text:
        font_size = 50
        x_pos, y_pos = 55, 150
    else:
        font_size = random.randint(64, 72)
        x_pos = random.randint(50, 90)
        y_pos = random.randint(200, 260)

    font = None
    for fpath in FONT_CANDIDATES:
        try:
            font = ImageFont.truetype(fpath, font_size)
            break
        except:
            continue
    if font is None:
        font = ImageFont.load_default()

    # Shadow + Text
    draw.multiline_text((x_pos + 3, y_pos + 3), text, font=font, fill=(0, 0, 0, 200), spacing=12, align="center")
    draw.multiline_text((x_pos, y_pos), text, font=font, fill=random.choice(COLORS), spacing=12, align="center")

    # Frame
    draw.rounded_rectangle((30, 120, 1250, 600), radius=28, outline=(255, 255, 255, 160), width=3)

    draw_confetti(draw, count=random.randint(40, 70))
    draw_sparkles(draw, count=random.randint(15, 25))

    img = apply_vignette(img)
    img = img.convert("RGB")
    img.save(output_file, quality=95)

    clip = ImageClip(output_file).set_duration(duration)
    zoom = random.uniform(1.08, 1.14)
    clip = clip.resize(lambda t: 1 + (zoom - 1) * t / duration)
    clip = clip.fadein(1.0).fadeout(1.0)

    return clip


def create_video(name: str, message: str, audio_file: str, repeats: int = 1):
    """
    repeats: 1 to 5
    End slide is added only once at the very end.
    """
    repeats = max(1, min(5, int(repeats)))

    # Clean old slides
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

    # ---------- BUILD ONE BASE CYCLE (Intro + Main slides) ----------
    base_clips = []

    # Intro
    intro_text = f"A Special Birthday Video\nFor\n{name}"
    intro_bg = background_images[0]
    used_files["images"].append(os.path.basename(intro_bg))
    base_clips.append(create_slide(intro_text, intro_bg, 8, "generated/slide_intro.png"))

    # Main slides
    main_texts = [
        f"Happy Birthday\n{name}",
        "Wishing You\nAll the Happiness",
        message,
        "May Your Day\nBe Filled with Joy",
        "Celebrate in\nStyle Today!",
        f"Cheers to You\n{name}",
        "Lots of Love\n& Best Wishes",
        "Have an Amazing\nBirthday!",
    ]

    for i, text in enumerate(main_texts):
        bg = background_images[(i + 1) % len(background_images)]
        used_files["images"].append(os.path.basename(bg))
        base_clips.append(create_slide(text, bg, 15, f"generated/slide_{i}.png"))

    base_video = concatenate_videoclips(base_clips, method="compose")

    # ---------- REPEAT THE BASE VIDEO ----------
    repeated_clips = [base_video] * repeats
    main_part = concatenate_videoclips(repeated_clips, method="compose")

    # ---------- END SLIDE (only once at the end) ----------
    end_text = (
        "Thank You for Watching!\n\n"
        "Please Like 👍  Share ❤️\n"
        "Comment & Subscribe\n\n"
        "Request Custom Video:\n"
        "yourwebsite.com/custom"          # ← Change this
    )
    end_bg = background_images[-1]
    used_files["images"].append(os.path.basename(end_bg))
    end_clip = create_slide(end_text, end_bg, 16, "generated/slide_end.png")

    # Final video = repeated content + end slide
    final_video = concatenate_videoclips([main_part, end_clip], method="compose")

    # ---------- AUDIO ----------
    total_duration = final_video.duration
    if audio.duration < total_duration:
        loops = int(total_duration // audio.duration) + 1
        audio = concatenate_audioclips([audio] * loops)

    audio = audio.subclip(0, total_duration).audio_fadein(1.2).audio_fadeout(2.0)
    final_video = final_video.set_audio(audio)

    # ---------- EXPORT ----------
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
    audio.close()

    return output_path, used_files