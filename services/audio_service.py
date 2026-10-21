import asyncio
import edge-tts


async def generate_audio(
        text,
        output_file):

    communicate = edge-tts.Communicate(
        text,
        voice="en-US-JennyNeural"
    )

    await communicate.save(
        output_file
    )
