import os
import subprocess


def convert_gifs_to_webm(folder="assets/overlays"):

    for filename in os.listdir(folder):

        if not filename.lower().endswith(".gif"):
            continue

        gif_file = os.path.join(folder, filename)

        webm_file = os.path.join(
            folder,
            os.path.splitext(filename)[0] + ".webm"
        )

        # Skip if already converted
        if os.path.exists(webm_file):
            print(f"Skipping {filename} (already converted)")
            continue

        try:

            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i", gif_file,
                    "-c:v", "libvpx-vp9",
                    "-pix_fmt", "yuva420p",
                    "-lossless", "1",
                    webm_file
                ],
                check=True
            )

            print(f"✅ Converted: {filename}")

        except Exception as e:

            print(f"❌ Failed: {filename}")
            print(e)


if __name__ == "__main__":
    convert_gifs_to_webm()
