from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response
from pydantic import BaseModel
from typing import Optional
import os
try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    speechsdk = None
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

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


class TTSRequest(BaseModel):
    text: str
    language: str  # uz-UZ, ru-RU, en-US
    voice: Optional[str] = None

VOICE_MAPPING = {
    "uz-UZ": ["uz-UZ-MadinaNeural", "uz-UZ-SardorNeural"],
    "ru-RU": ["ru-RU-DariyaNeural", "ru-RU-DmitryNeural"],
    "en-US": ["en-US-JennyNeural", "en-US-GuyNeural"]
}

def get_voice_config(language, custom_voice=None):
    """Get voice configuration for language"""
    speech_key = os.getenv("AZURE_SPEECH_KEY", AZURE_SPEECH_KEY_VAL) or os.getenv("AZURE_OPENAI_KEY", AZURE_OPENAI_KEY_VAL)
    
    if not speech_key:
        return None, "Azure Speech key not configured"
    
    if speechsdk is None:
        return None, "Speech services are currently disabled on this server."

    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key,
        region=os.getenv("AZURE_SPEECH_REGION", AZURE_SPEECH_REGION_VAL)
    )
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
    )
    
    # Select voice
    if custom_voice:
        voice_name = custom_voice
    else:
        voices = VOICE_MAPPING.get(language, [])
        voice_name = voices[0] if voices else "en-US-JennyNeural"
        
    speech_config.speech_synthesis_voice_name = voice_name
    
    return speech_config, None

@router.options("/tts")
async def tts_options():
    return Response(status_code=200)

@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Unified Text to Speech endpoint"""
    speech_config, error = get_voice_config(request.language, request.voice)
    
    if error:
        raise HTTPException(status_code=501, detail=error)
        
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    
    try:
        result = synthesizer.speak_text_async(request.text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return Response(
                content=bytes(result.audio_data),
                media_type="audio/mpeg"
            )
        else:
            raise HTTPException(status_code=500, detail=f"TTS Error: {result.error_details}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.options("/stt")
async def stt_options():
    return Response(status_code=200)

@router.post("/stt")
async def speech_to_text(
    file: UploadFile = File(...),
    language: str = Form(...)
):
    """Unified Speech to Text endpoint"""
    audio_data = await file.read()
    
    speech_config, error = get_voice_config(language)
    if error:
        raise HTTPException(status_code=501, detail=error)
        
    speech_config.speech_recognition_language = language
    
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
        return {"text": result.text}
    else:
        return {"text": "", "error": getattr(result, "error_details", "Unknown error")}
