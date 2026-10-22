from moviepy.editor import *
from services.assets_service import get_random_music


def merge_with_background_music(
        voice_file,
        output_file):

    music_file = get_random_music()

    print("VOICE:", voice_file)
    print("MUSIC:", music_file)

    try:

        voice = AudioFileClip(
            voice_file
        )

        music = AudioFileClip(
            music_file
        )

        except Exception as e:
        
            print("MUSIC FILE:", music_file)
            print("ERROR:", str(e))
        
            raise

    music = music.volumex(0.1)

    if music.duration > voice.duration:

        music = music.subclip(
            0,
            voice.duration
        )

    final_audio = CompositeAudioClip(
        [music, voice]
    )

    final_audio.write_audiofile(
            output_file,
            fps=44100
    )

    return output_file
