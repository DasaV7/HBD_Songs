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
    "#FF8FAB", "#FDE4CF", "#FFD700", "#FF69B4",
    "#FFE4E1", "#E6E6FA"
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


def draw_confetti(draw, width=1280, height=720, count=70):
    for _ in range(count):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(5, 14)
        color = random.choice(COLORS)
        if random.random() > 0.5:
            draw.rectangle([x, y, x + size, y + size // 2], fill=color)
        else:
            draw.ellipse([x, y, x + size, y + size], fill=color)


def draw_sparkles(draw, width=1280, height=720, count=30):
    for _ in range(count):
        x = random.randint(40, width - 40)
        y = random.randint(40, height - 40)
        size = random.randint(4, 9)
        color = random.choice(["#FFD700", "#FFFFFF", "#FFF8DC", "#FFE4B5"])
        draw.line([(x - size, y), (x + size, y)], fill=color, width=2)
        draw.line([(x, y - size), (x, y + size)], fill=color, width=2)


def apply_vignette(img):
    width, height = img.size
    vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vignette)

    for i in range(70):
        alpha = int(i * 1.6)
        draw.rectangle([i, i, width - i, height - i], outline=(0, 0, 0, alpha))
    return Image.alpha_composite(img.convert("RGBA"), vignette)


def create_slide(text, background, duration, output_file):
    img = Image.open(background).convert("RGBA")
    img = img.resize((1280, 720), Image.LANCZOS)

    # Soft dark overlay
    dark = Image.new("RGBA", img.size, (0, 0, 0, 95))
    img = Image.alpha_composite(img, dark)

    # Slight color boost
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.12)

    draw = ImageDraw.Draw(img)

    # Load font
    font = None
    for fpath in FONT_CANDIDATES:
        try:
            font = ImageFont.truetype(fpath, random.randint(62, 74))
            break
        except:
            continue
    if font is None:
        font = ImageFont.load_default()

    # Text position
    x_pos = random.randint(50, 90)
    y_pos = random.randint(180, 260)

    # Soft shadow
    draw.multiline_text((x_pos + 4, y_pos + 4), text, font=font, fill=(0, 0, 0, 200), spacing=14, align="center")
    draw.multiline_text((x_pos, y_pos), text, font=font, fill=random.choice(COLORS), spacing=14, align="center")

    # Elegant frame
    draw.rounded_rectangle(
        (35, 130, 1245, 590),
        radius=30,
        outline=(255, 255, 255, 160),
        width=3
    )

    # Effects
    draw_confetti(draw, count=random.randint(45, 80))
    draw_sparkles(draw, count=random.randint(18, 32))

    # Vignette
    img = apply_vignette(img)

    img = img.convert("RGB")
    img.save(output_file, quality=95)

    # Ken Burns zoom
    clip = ImageClip(output_file).set_duration(duration)
    zoom = random.uniform(1.09, 1.16)
    clip = clip.resize(lambda t: 1 + (zoom - 1) * t / duration)
    clip = clip.fadein(1.2).fadeout(1.2)

    return clip


def create_video(name: str, message: str, audio_file: str):
    # Clean previous slides
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

    clips = []

    # ====================== 1. INTRO SLIDE ======================
    intro_text = f"A Special Birthday Video\nFor\n{name}"
    intro_bg = background_images[0]
    used_files["images"].append(os.path.basename(intro_bg))

    intro_clip = create_slide(
        intro_text,
        intro_bg,
        9,
        "generated/slide_intro.png"
    )
    clips.append(intro_clip)

    # ====================== 3. END SLIDE ======================
    end_text = (
        "Thank You for Watching!\n\n"
        "Please Like 👍   Share ❤️\n"
        "Comment & Subscribe\n\n"
        "Request Custom Video:\n"
        "yourwebsite.com/custom"
    )

    end_bg = background_images[-1]
    used_files["images"].append(os.path.basename(end_bg))

    end_clip = create_slide(
        end_text,
        end_bg,
        18,                          # Longer duration so it’s clearly visible
        "generated/slide_end.png"
    )
    clips.append(end_clip)
    # # ====================== 3. END SLIDE ======================
    # end_text = (
    #     f"Thank You for Watching!\n\n"
    #     f"Please Like 👍  Share ❤️  & Comment\n"
    #     f"Subscribe for more Birthday Videos\n\n"
    #     f"Request Custom Video:\n"
    #     f"https://hbdsongs.streamlit.app"          # ← Change this to your real link
    # )

    # end_bg = background_images[-1]
    # used_files["images"].append(os.path.basename(end_bg))

    # end_clip = create_slide(
    #     end_text,
    #     end_bg,
    #     15,
    #     "generated/slide_end.png"
    # )
    # clips.append(end_clip)

    # ====================== FINAL ASSEMBLY ======================
    final_clips = [clips[0]]
    for clip in clips[1:]:
        final_clips.append(clip.crossfadein(1.1))

    base_video = concatenate_videoclips(final_clips, method="compose", padding=-1.1)

    # Audio handling
    if audio.duration < base_video.duration:
        loops = int(base_video.duration // audio.duration) + 1
        audio = concatenate_audioclips([audio] * loops)

    audio = audio.subclip(0, base_video.duration).audio_fadein(1.5).audio_fadeout(2.5)
    base_video = base_video.set_audio(audio)

    # Loop once → longer video
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
