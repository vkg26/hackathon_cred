import os
from openai import OpenAI
import openai

import os
import openai

from client import client

def transcribe_audio(file_path):
    try:
        print(f"🔊 Transcribing audio file: {file_path}")
        
        # Transcribe using GPT-4o via LiteLLM
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=open(file_path, "rb"),
            response_format="json",
            language="en",
        )

        print(f"✅ Transcription complete: {transcript.text.strip()}")
        return transcript.text.strip()

    except Exception as e:
        print(f"❌ Error during transcription: {e}")
        return None

if __name__ == "__main__":
    file_path = r"bengali_audio.mp3"  # Path to your audio file
    transcribe_audio(file_path)
