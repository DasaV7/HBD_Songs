import shutil
from services.assets_service import (
    get_random_music
)


async def generate_audio(
        text,
        output_file):

    music_file = get_random_music()

    shutil.copy(
        music_file,
        output_file
    )

    return output_file
