from moviepy.editor import *
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


def create_video(
        name,
        audio_file):

    audio = AudioFileClip(audio_file)

    duration = audio.duration

    img = Image.new(
        "RGB",
        (1280,720),
        color=(255,102,204)
    )

    draw = ImageDraw.Draw(img)

    text = f"Happy Birthday\n{name}"

    draw.text(
        (300,250),
        text,
        fill="white"
    )

    image_path = f"generated/{name}.png"

    img.save(image_path)

    clip = ImageClip(
        image_path
    ).set_duration(duration)

    clip = clip.set_audio(audio)

    output = f"generated/{name}.mp4"

    clip.write_videofile(
        output,
        fps=24
    )

    return output
