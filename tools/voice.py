import os
import logging
from groq import AsyncGroq

logger = logging.getLogger(__name__)

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", ""))


async def transcribe(file_path: str) -> str:
    """Транскрибирует аудиофайл через Whisper на Groq."""
    try:
        with open(file_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                file=(os.path.basename(file_path), audio_file),
                model="whisper-large-v3-turbo",
                language="ru",
                response_format="text"
            )
        return transcription.strip()
    except Exception as e:
        logger.error(f"Ошибка транскрибации: {e}")
        return ""
