from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    concatenate_audioclips
)

from services.assets_service import get_random_music


def merge_with_background_music(
    voice_file,
    output_file
):

    music_file = get_random_music()

    voice = AudioFileClip(
        voice_file
    )

    music = AudioFileClip(
        music_file
    )

    if music.duration < voice.duration:

        loops = int(
            voice.duration / music.duration
        ) + 1

        music = concatenate_audioclips(
            [music] * loops
        )

    music = music.subclip(
        0,
        voice.duration
    )

    music = music.volumex(
        0.10
    )

    final_audio = CompositeAudioClip(
        [music, voice]
    )

    final_audio.fps = 44100

    final_audio.write_audiofile(
        output_file,
        fps=44100
    )

    return output_file
