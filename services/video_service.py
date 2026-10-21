from moviepy.editor import *


def create_video(
        name,
        audio_file):

    audio = AudioFileClip(
        audio_file
    )

    duration = audio.duration

    bg = ColorClip(
        size=(1280,720),
        color=(255,102,204),
        duration=duration
    )

    text = TextClip(
        f"Happy Birthday {name}",
        fontsize=80,
        color="white"
    )

    text = text.set_duration(
        duration
    )

    text = text.set_position(
        "center"
    )

    final = CompositeVideoClip(
        [bg,text]
    )

    final = final.set_audio(
        audio
    )

    output = f"generated/{name}.mp4"

    final.write_videofile(
        output,
        fps=24
    )

    return output
