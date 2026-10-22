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

    music_folder = "assets/music"

    files = []

    for file in os.listdir(music_folder):

        if file.lower().endswith(
            (
                ".mp3",
                ".wav"
            )
        ):

            files.append(
                os.path.join(
                    music_folder,
                    file
                )
            )

    if not files:

        raise Exception(
            "No valid music files found"
        )

    return random.choice(files)
