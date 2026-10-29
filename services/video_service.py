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


COLORS = [
    "#FF9AA2", "#FFDAC1", "#E2F0CB", "#B5EAD7",
    "#C7CEEA", "#A0C4FF", "#FFD6A5", "#FFB7B2"
]


def get_media_files(folder, extensions):
    if not os.path.exists(folder):
        return []
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(extensions)
    ]


from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random
import os


def remove_background(overlay_path):
    """
    Better background removal for both white and black backgrounds.
    """
    img = Image.open(overlay_path).convert("RGBA")
    arr = np.array(img)

    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

    # Detect near-white pixels
    white_mask = (r > 230) & (g > 230) & (b > 230)

    # Detect near-black pixels
    black_mask = (r < 40) & (g < 40) & (b < 40)

    # Make both transparent
    arr[:, :, 3] = np.where(white_mask | black_mask, 0, a)

    return Image.fromarray(arr)


def create_slide(text, background, duration, output_file, overlays_folder="assets/overlays"):
    # Base background
    img = Image.open(background).convert("RGBA")
    img = img.resize((1280, 720), Image.LANCZOS)

    # Darken background slightly for better text contrast
    dark = Image.new("RGBA", img.size, (0, 0, 0, 100))
    img = Image.alpha_composite(img, dark)

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("assets/fonts/Poppins-SemiBold.ttf", 68)
    except:
        font = ImageFont.load_default()

    # ========== SAFE OVERLAY PLACEMENT ==========
    overlay_files = get_media_files(overlays_folder, (".jpg", ".jpeg", ".png"))

    if overlay_files:
        selected = random.sample(overlay_files, k=min(2, len(overlay_files)))

        # Safe zones (completely away from center text)
        safe_positions = [
            (20, 20),                             # top-left
            (1280 - 320, 20),                     # top-right
            (20, 720 - 280),                      # bottom-left
            (1280 - 320, 720 - 280),              # bottom-right
        ]

        random.shuffle(safe_positions)

        for i, overlay_path in enumerate(selected):
            try:
                ov = remove_background(overlay_path)

                # Resize to reasonable size
                ov.thumbnail((300, 300), Image.LANCZOS)

                # Use safe position
                pos = safe_positions[i % len(safe_positions)]

                img.paste(ov, pos, ov)

            except Exception as e:
                print(f"Overlay error: {e}")
                continue

    # ========== TEXT ON TOP (always readable) ==========
    draw.multiline_text(
        (70, 230),
        text,
        font=font,
        fill=random.choice(COLORS),
        spacing=16,
        align="center"
    )

    # Frame
    draw.rounded_rectangle(
        (40, 150, 1240, 570),
        radius=30,
        outline=(255, 255, 255, 160),
        width=3
    )

    # Save
    final = img.convert("RGB")
    final.save(output_file, quality=95)

    return (ImageClip(output_file)
            .set_duration(duration)
            .fadein(1.0)
            .fadeout(1.0))

def create_video(name: str, message: str, audio_file: str):
    # Clean old temp slides
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

    # ---------- 10 SLIDES × ~16-18 seconds = ~3 minutes ----------
    slide_texts = [
        f"Happy Birthday\n{name}",
        "Wishing You\nAll the Happiness",
        message[:55] + ("..." if len(message) > 55 else ""),
        "May Your Day\nBe Filled with Joy",
        "Celebrate in\nStyle Today!",
        f"Cheers to You\n{name}",
        "Lots of Love\n& Best Wishes",
        "Have an Amazing\nBirthday!",
        f"Thank You\n{name} 💖",
        "Enjoy Your\nSpecial Day!"
    ]

    clips = []
    slide_duration = 17  # seconds per slide (adjust between 15-18 if you want)

    for i, text in enumerate(slide_texts):
        bg = background_images[i % len(background_images)]
        used_files["images"].append(os.path.basename(bg))

        slide = create_slide(
            text,
            bg,
            slide_duration,
            f"generated/slide_{i}.png"
        )
        clips.append(slide)

    # Create base video (~ 10 × 17s = 170 seconds ≈ 2.8 min)
    base_video = concatenate_videoclips(clips, method="compose")

    # Match audio length to base video
    if audio.duration < base_video.duration:
        loops_needed = int(base_video.duration // audio.duration) + 1
        audio = concatenate_audioclips([audio] * loops_needed)

    audio = audio.subclip(0, base_video.duration)
    base_video = base_video.set_audio(audio)

    # ---------- LOOP ONCE → Final ~6 minutes ----------
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

    # Cleanup
    final_video.close()
    base_video.close()
    audio.close()

    return output_path, used_files
