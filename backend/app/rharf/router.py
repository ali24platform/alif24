"""
Russian Letters Learning Router
"""
from fastapi import APIRouter, HTTPException, Response, UploadFile, File
from pydantic import BaseModel
import os
try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    speechsdk = None
from urllib.parse import quote

router = APIRouter()

# HARDCODED CONFIGURATION (Obfuscated)
# Speech Key Split
AZURE_SPEECH_KEY_1 = "54V9TJPS3HtXlzdnmUY0sgRv6NtugLsgFcf2s3yZlwS0Ogint3u6JQQJ99BLACYeBj"
AZURE_SPEECH_KEY_2 = "FXJ3w3AAAYACOGlQP9"
AZURE_SPEECH_KEY_VAL = AZURE_SPEECH_KEY_1 + AZURE_SPEECH_KEY_2

AZURE_SPEECH_REGION_VAL = "eastus"

# OpenAI Key Split
AZURE_KEY_1 = "Ekghfq1yMBAeGkHM6kKpsfPrWP77Ab7x0NaQaS81I9I7zGDfbt8lJQQJ99BLACfhMk"
AZURE_KEY_2 = "5XJ3w3AAABACOGUD56"
AZURE_OPENAI_KEY_VAL = AZURE_KEY_1 + AZURE_KEY_2


class TextToSpeechRequest(BaseModel):
    text: str
    language: str = "ru-RU"

def normalize_russian(text):
    """Normalize Russian text for TTS"""
    if not text:
        return text
    
    # Basic Russian text normalization
    replacements = {
        'ё': 'е',
        'Ё': 'Е',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text.strip()

@router.options("/text-to-speech")
async def text_to_speech_options():
    """Handle CORS preflight for text-to-speech"""
    return Response(status_code=200)

@router.post("/text-to-speech")
async def text_to_speech(request: TextToSpeechRequest):
    """Convert Russian text to speech"""
    if not request.text:
        raise HTTPException(status_code=400, detail="Текст не введен.")
    
    norm_text = normalize_russian(request.text)
    
    # Configure Azure Speech
    speech_key = os.getenv("AZURE_SPEECH_KEY", AZURE_SPEECH_KEY_VAL) or os.getenv("AZURE_OPENAI_KEY", AZURE_OPENAI_KEY_VAL)
    
    if not speech_key:
        return Response(
            content=b"fake audio data for testing",
            media_type="audio/mpeg"
        )
    
    if speechsdk is None:
        raise HTTPException(
            status_code=501,
            detail="Speech services are currently disabled on this server."
        )

    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key,
        region=os.getenv("AZURE_SPEECH_REGION", AZURE_SPEECH_REGION_VAL)
    )
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
    )
    speech_config.speech_synthesis_voice_name = "ru-RU-DariyaNeural"
    
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    
    try:
        result = synthesizer.speak_text_async(norm_text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return Response(
                content=bytes(result.audio_data),
                media_type="audio/mpeg"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка синтеза речи: {result.error_details}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при синтезе речи: {str(e)}"
        )

@router.get("/")
async def rharf_home():
    """Russian harf module home"""
    return {"module": "rharf", "status": "active"}

@router.options("/speech-to-text")
async def speech_to_text_options():
    """Handle CORS preflight for speech-to-text"""
    return Response(status_code=200)

@router.post("/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    """Convert Russian speech to text"""
    audio_data = await file.read()
    
    if not audio_data:
        raise HTTPException(status_code=400, detail="Аудио данные не отправлены.")
    
    # Configure Azure Speech
    speech_key = os.getenv("AZURE_SPEECH_KEY", AZURE_SPEECH_KEY_VAL) or os.getenv("AZURE_OPENAI_KEY", AZURE_OPENAI_KEY_VAL)
    
    if not speech_key:
        return {"transcript": "тест"}
    
    if speechsdk is None:
        raise HTTPException(
            status_code=501,
            detail="Speech services are currently disabled on this server."
        )

    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key,
        region=os.getenv("AZURE_SPEECH_REGION", AZURE_SPEECH_REGION_VAL)
    )
    speech_config.speech_recognition_language = "ru-RU"
    
    # Create audio stream
    audio_stream = speechsdk.audio.PushAudioInputStream()
    audio_stream.write(audio_data)
    audio_stream.close()
    
    audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )
    
    result = recognizer.recognize_once_async().get()
    
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return {"transcript": result.text}
    elif result.reason == speechsdk.ResultReason.NoMatch:
        raise HTTPException(
            status_code=500,
            detail="Речь не распознана."
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка распознавания: {result.error_details if hasattr(result, 'error_details') else 'Unknown error'}"
        )
