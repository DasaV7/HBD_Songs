from moviepy.editor import *

from services.assets_service import (
    get_random_music
)

def merge_with_background_music(
        voice_file,
        output_file):

    music_file = get_random_music()

    print("Selected music:", music_file)

    voice = AudioFileClip(
        voice_file
    )

    music = AudioFileClip(
        music_file
    )

    music = music.volumex(0.10)

    if music.duration > voice.duration:

        music = music.subclip(
            0,
            voice.duration
        )

    final_audio = CompositeAudioClip(
        [
            music,
            voice
        ]
    )

    final_audio.write_audiofile(
        output_file
    )

    return output_file
