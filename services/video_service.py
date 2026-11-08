# services/video_service.py

from PIL import Image, ImageDraw, ImageFont
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

import random
import os
import traceback

# Create the folder immediately
os.makedirs("generated", exist_ok=True)

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
    concatenate_audioclips
)

COLORS = [
    "#FF9AA2", "#FFDAC1", "#E2F0CB", "#B5EAD7",
    "#C7CEEA", "#A0C4FF", "#FFD6A5", "#FFB7B2",
    "#FFD700", "#FF69B4"
]

FONT_CANDIDATES = [
    "assets/fonts/Poppins-Bold.ttf",
    "assets/fonts/Poppins-SemiBold.ttf",
    "assets/fonts/Montserrat-Bold.ttf",
]


def get_media_files(folder, extensions):
    if not os.path.exists(folder):
        return []
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(extensions)
    ]


def get_text_position(filename: str, is_end: bool = False):
    name = filename.lower().replace("_", " ").replace("-", " ").replace(".", " ")

    if "top left" in name:
        return "right", 390
    elif "top right" in name:
        return "left", 390
    elif "bottom left" in name:
        return "right", 150
    elif "bottom right" in name:
        return "left", 150
    elif "left" in name and "right" not in name:
        return "right", 280
    elif "right" in name and "left" not in name:
        return "left", 280
    else:
        return "left", 160 if is_end else 240


def fit_image_cover(img: Image.Image, target_size=(1280, 720)) -> Image.Image:
    target_w, target_h = target_size
    img_w, img_h = img.size
    scale = max(target_w / img_w, target_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def get_gif_category(filename: str) -> str:
    name = filename.lower()
    if "balloon" in name:
        return "balloon"
    if "firework" in name or "fire-work" in name or "ire-works" in name:
        return "firework"
    if "confetti" in name or "dots" in name:
        return "confetti"
    if "gift" in name:
        return "gift"
    if "sparkle" in name or "glitter" in name or "pattern" in name:
        return "sparkle"
    if "heart" in name:
        return "heart"
    if "celebration" in name or "happy" in name:
        return "celebration"
    return "other"


def load_gif_safely(gif_path, duration, scale_range=(0.5, 0.8)):
    """Safely load a GIF and return a MoviePy clip or None"""
    try:
        pil_gif = Image.open(gif_path)
        frames = []

        try:
            while True:
                frame = pil_gif.convert("RGBA")
                frames.append(np.array(frame))
                pil_gif.seek(pil_gif.tell() + 1)
        except EOFError:
            pass

        if len(frames) < 2:
            return None

        gif = ImageSequenceClip(frames, fps=10)

        scale = random.uniform(*scale_range)
        gif = gif.resize(scale)

        max_x = max(20, 1280 - int(gif.w))
        max_y = max(20, 720 - int(gif.h))
        pos_x = random.randint(20, max_x)
        pos_y = random.randint(20, max_y)

        gif = gif.set_position((pos_x, pos_y))

        if gif.duration < duration:
            gif = gif.loop(duration=duration)
        else:
            gif = gif.subclip(0, duration)

        gif = gif.set_opacity(0.72)
        return gif

    except Exception as e:
        print(f"GIF skipped ({os.path.basename(gif_path)}): {e}")
        return None


def create_slide(text, background, duration, output_file, is_end=False, gif_overlays=None):
    # Background
    img = Image.open(background).convert("RGBA")
    img = fit_image_cover(img, (1280, 720))

    dark = Image.new("RGBA", img.size, (0, 0, 0, 80))
    img = Image.alpha_composite(img, dark)
    draw = ImageDraw.Draw(img)

    # Font
    font_size = 40 if is_end else 56
    font = None
    for fpath in FONT_CANDIDATES:
        try:
            font = ImageFont.truetype(fpath, font_size)
            break
        except:
            continue
    if font is None:
        font = ImageFont.load_default()

    filename = os.path.basename(background)
    side, y_pos = get_text_position(filename, is_end=is_end)
    lines = text.split("\n")

    # Text position
    if side == "right":
        right_edge = 1190
        align = "right"
        max_width = 0
        for line in lines:
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]
                if w > max_width:
                    max_width = w
            except:
                max_width = 500
        x_pos = max(60, right_edge - max_width)
    else:
        x_pos = 80
        align = "left"

    try:
        bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=12)
        text_height = bbox[3] - bbox[1]
    except:
        text_height = 140

    y_pos = max(120, min(y_pos, 580 - text_height))

    # Draw text
    draw.multiline_text((x_pos + 3, y_pos + 3), text, font=font,
                        fill=(0, 0, 0, 180), spacing=12, align=align)
    draw.multiline_text((x_pos, y_pos), text, font=font,
                        fill=random.choice(COLORS), spacing=12, align=align)

    # Frame
    if is_end:
        draw.rounded_rectangle((20, 70, 1260, 650), radius=30,
                               outline=(255, 255, 255, 170), width=2)
    else:
        draw.rounded_rectangle((15, 70, 1260, 650), radius=30,
                               outline=(255, 255, 255, 160), width=2)

    img = img.convert("RGB")
    img.save(output_file, quality=90)

    # Base clip
    base_clip = ImageClip(output_file).set_duration(duration)
    clips = [base_clip]

    # Add GIF overlays safely
    if gif_overlays:
        for gif_path in gif_overlays:
            gif_clip = load_gif_safely(gif_path, duration)
            if gif_clip:
                clips.append(gif_clip)

    final_clip = CompositeVideoClip(clips, size=(1280, 720))
    final_clip = final_clip.fadein(0.7).fadeout(0.7)
    return final_clip


def create_video(name: str, message: str, audio_file: str, repeats: int = 1):
    repeats = max(1, min(5, int(repeats)))

    for f in os.listdir("generated"):
        if f.startswith("slide") or f.endswith((".mp4", ".png")):
            try:
                os.remove(os.path.join("generated", f))
            except:
                pass

    audio = AudioFileClip(audio_file)

    background_images = get_media_files("assets/backgrounds", (".jpg", ".jpeg", ".png"))
    gif_files = get_media_files("assets/overlays", (".gif",))

    if len(background_images) < 5:
        raise Exception("Need at least 5 background images")

    random.shuffle(background_images)

    used_files = {
        "audio": os.path.basename(audio_file),
        "images": [],
        "gifs": []
    }

    def get_unique_gifs(count=2):
        if not gif_files:
            return []

        random.shuffle(gif_files)
        selected = []
        used_categories = set()

        for gif in gif_files:
            cat = get_gif_category(os.path.basename(gif))
            if cat not in used_categories:
                selected.append(gif)
                used_categories.add(cat)
                used_files["gifs"].append(os.path.basename(gif))
            if len(selected) >= count:
                break

        if not selected and gif_files:
            selected = [random.choice(gif_files)]
            used_files["gifs"].append(os.path.basename(selected[0]))

        return selected

    base_clips = []

    # Intro
    intro_text = f"A Special Birthday Video\nFor\n{name}"
    bg = background_images[0]
    used_files["images"].append(os.path.basename(bg))
    gifs = get_unique_gifs(count=random.choice([1, 2]))
    base_clips.append(create_slide(intro_text, bg, 7, "generated/slide_intro.png", gif_overlays=gifs))

    # Main slides
    main_texts = [
        f"Happy Birthday\n{name}",
        "Wishing You\nAll the Happiness",
        message,
        "May Your Day\nBe Full of Joy",
        "Celebrate Your\nSpecial Day!",
        f"Cheers to You\n{name}",
        "Lots of Love &\nBest Wishes",
        "Have an Amazing\nBirthday!"
    ]

    for i, text in enumerate(main_texts):
        bg = background_images[(i + 1) % len(background_images)]
        used_files["images"].append(os.path.basename(bg))
        gifs = get_unique_gifs(count=random.choice([1, 2]))
        base_clips.append(create_slide(text, bg, 12, f"generated/slide_{i}.png", gif_overlays=gifs))

    base_video = concatenate_videoclips(base_clips, method="compose")

    if repeats > 1:
        main_part = concatenate_videoclips([base_video] * repeats, method="compose")
    else:
        main_part = base_video

    # End slide
    end_text = (
        "Thank You for Watching!\n\n"
        "Please Like • Share • Comment\n"
        "And Subscribe for more videos\n\n"
        "Request Custom Video:\n"
        "https://hbdsongs.streamlit.app"
    )
    end_bg = background_images[-1]
    used_files["images"].append(os.path.basename(end_bg))
    gifs = get_unique_gifs(count=1)
    end_clip = create_slide(end_text, end_bg, 14, "generated/slide_end.png", is_end=True, gif_overlays=gifs)

    final_video = concatenate_videoclips([main_part, end_clip], method="compose")

    # Audio
    total_duration = final_video.duration
    if audio.duration < total_duration:
        loops = int(total_duration / audio.duration) + 1
        audio = concatenate_audioclips([audio] * loops)

    audio = audio.subclip(0, total_duration)
    final_video = final_video.set_audio(audio)

    safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).replace(" ", "_")
    output_path = f"generated/{safe_name}.mp4"

    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="generated/temp-audio.m4a",
        remove_temp=True,
        threads=2,
        logger=None,
        preset="ultrafast"
    )

    final_video.close()
    audio.close()

    return output_path, used_files
