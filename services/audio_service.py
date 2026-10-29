import shutil
import os
import time
from services.assets_service import get_random_music


async def generate_audio(text, output_file):
    """
    Copy a random music file to the output path with verification.
    """
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            music_file = get_random_music()

            # Make sure source file is valid
            if not os.path.exists(music_file) or os.path.getsize(music_file) < 10000:
                raise Exception(f"Source music file is invalid: {music_file}")

            # Remove old output if exists
            if os.path.exists(output_file):
                os.remove(output_file)

            # Copy the file
            shutil.copy2(music_file, output_file)

            # Wait a tiny bit for filesystem
            time.sleep(0.3)

            # Verify the copied file
            if not os.path.exists(output_file):
                raise Exception("Copied file does not exist")

            if os.path.getsize(output_file) < 10000:
                raise Exception("Copied file is too small / incomplete")

            # Success
            return output_file

        except Exception as e:
            print(f"Audio attempt {attempt + 1} failed: {e}")
            if attempt == max_attempts - 1:
                raise Exception(f"Failed to generate valid audio after {max_attempts} attempts: {e}")
            time.sleep(0.5)
