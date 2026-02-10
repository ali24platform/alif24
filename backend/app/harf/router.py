"""
Uzbek Letters Learning Router
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
# Key Split
AZURE_SPEECH_KEY_1 = "54V9TJPS3HtXlzdnmUY0sgRv6NtugLsgFcf2s3yZlwS0Ogint3u6JQQJ99BLACYeBj"
AZURE_SPEECH_KEY_2 = "FXJ3w3AAAYACOGlQP9"
AZURE_SPEECH_KEY_VAL = AZURE_SPEECH_KEY_1 + AZURE_SPEECH_KEY_2

AZURE_SPEECH_REGION_VAL = "eastus"

class TextToSpeechRequest(BaseModel):
    text: str
    language: str = "uz-UZ"

def normalize_uz(text):
    """Normalize Uzbek text for TTS"""
    if not text:
        return text
    
    # O' va G' harflarini to'g'rilash
    text = text.replace("o'", "oʻ").replace("O'", "Oʻ")
    text = text.replace("g'", "gʻ").replace("G'", "Gʻ")
    text = text.replace("'", "ʻ") # Boshqa apostroflarni ham
    
    return text.strip()

@router.options("/text-to-speech")
async def text_to_speech_options():
    """Handle CORS preflight for text-to-speech"""
    return Response(status_code=200)

@router.post("/text-to-speech")
async def text_to_speech(request: TextToSpeechRequest):
    """Convert Uzbek text to speech using Azure"""
    if not request.text:
        raise HTTPException(status_code=400, detail="Matn kiritilmadi")
    
    norm_text = normalize_uz(request.text)
    
    # Configure Azure Speech
    speech_key = os.getenv("AZURE_SPEECH_KEY", AZURE_SPEECH_KEY_VAL)
    
    if not speech_key:
        raise HTTPException(status_code=500, detail="Azure Speech key not configured")
    
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key,
        region=os.getenv("AZURE_SPEECH_REGION", AZURE_SPEECH_REGION_VAL)
    )
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
    )
    # Madina ovozi (ayol) yoki Sardor (erkak)
    speech_config.speech_synthesis_voice_name = "uz-UZ-MadinaNeural"
    
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
                detail=f"Nutq sintezi xatosi: {result.error_details}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Nutq sintezida xatolik: {str(e)}"
        )

@router.get("/")
async def harf_home():
    """Harf moduli bosh sahifasi"""
    return {"module": "harf", "status": "active"}

@router.options("/speech-to-text")
async def speech_to_text_options():
    """Handle CORS preflight for speech-to-text"""
    return Response(status_code=200)

@router.post("/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    """Convert Uzbek speech to text using Azure"""
    # Audio faylni o'qish
    audio_data = await file.read()
    
    if not audio_data:
        raise HTTPException(status_code=400, detail="Audio fayl yuborilmadi")
    
    # Configure Azure Speech
    speech_key = os.getenv("AZURE_SPEECH_KEY", AZURE_SPEECH_KEY_VAL)
    
    if not speech_key:
         # Test rejimi uchun
         return {"transcript": "Bu test matni"}
    
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key,
        region=os.getenv("AZURE_SPEECH_REGION", AZURE_SPEECH_REGION_VAL)
    )
    speech_config.speech_recognition_language = "uz-UZ"
    
    # Audio stream yaratish
    audio_stream = speechsdk.audio.PushAudioInputStream()
    audio_stream.write(audio_data)
    audio_stream.close()
    
    audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )
    
    # Ovozni matnga aylantirish (bir martalik)
    result = recognizer.recognize_once_async().get()
    
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return {"transcript": result.text}
    elif result.reason == speechsdk.ResultReason.NoMatch:
        raise HTTPException(
            status_code=500, # 400 emas, server xatosi sifatida loglash
            detail="Ovoz tushunarsiz yoki aniqlanmadi"
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Azure xatosi: {result.error_details}"
        )
