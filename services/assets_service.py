import os
import random


def get_random_background():

    background_folder = "assets/backgrounds"

    files = [
        os.path.join(background_folder, file)
        for file in os.listdir(background_folder)
        if file.lower().endswith(
            (".jpg", ".jpeg", ".png")
        )
    ]

    if not files:
        raise Exception(
            "No background images found"
        )

    return random.choice(files)

def get_random_music():

    folder = "assets/music"

    files = [
        os.path.join(folder, file)
        for file in os.listdir(folder)
        if file.lower().endswith(
            (".mp3", ".wav")
        )
    ]

    if not files:
        raise Exception(
            "No music files found in assets/music"
        )

    return random.choice(files)
