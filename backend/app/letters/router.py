"""
Unified Letters Learning Router - Supports Uzbek and Russian
"""
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
import os
import requests as http_requests
from xml.sax.saxutils import escape
from app.core.config import settings

router = APIRouter()


class TextToSpeechRequest(BaseModel):
    text: str
    language: str = "uz-UZ"  # uz-UZ or ru-RU


def normalize_uzbek(text: str) -> str:
    """Normalize Uzbek text"""
    if not text:
        return text
    return (text
        .replace("ʼ", "'")
        .replace("ʻ", "'")
        .replace("`", "'")
        .replace("O'", "Oʻ")
        .replace("G'", "Gʻ")
        .replace("o'", "oʻ")
        .replace("g'", "gʻ"))


def normalize_russian(text: str) -> str:
    """Normalize Russian text"""
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


def build_uzbek_ssml(text: str) -> str:
    """Build SSML for special Uzbek letters"""
    lower = text.lower().strip()
    
    if lower == "sh" or lower.startswith("sh harfi"):
        return f'''<speak version="1.0" xml:lang="uz-UZ">
                    <voice name="uz-UZ-MadinaNeural">
                        <phoneme alphabet="ipa" ph="ʃ">sh</phoneme>
                        {" harfi" if lower != "sh" else ""}
                    </voice>
                </speak>'''
    
    if lower == "ch" or lower.startswith("ch harfi"):
        return f'''<speak version="1.0" xml:lang="uz-UZ">
                    <voice name="uz-UZ-MadinaNeural">
                        <phoneme alphabet="ipa" ph="tʃ">ch</phoneme>
                        {" harfi" if lower != "ch" else ""}
                    </voice>
                </speak>'''
    
    if lower in ["gʻ", "g'"] or lower.startswith("gʻ harfi") or lower.startswith("g' harfi"):
        return f'''<speak version="1.0" xml:lang="uz-UZ">
                    <voice name="uz-UZ-MadinaNeural">
                        <phoneme alphabet="ipa" ph="ɣ">gʻ</phoneme>
                        {" harfi" if "harfi" in lower else ""}
                    </voice>
                </speak>'''
    
    if lower in ["oʻ", "o'"] or lower.startswith("oʻ harfi") or lower.startswith("o' harfi"):
        return f'''<speak version="1.0" xml:lang="uz-UZ">
                    <voice name="uz-UZ-MadinaNeural">
                        <phoneme alphabet="ipa" ph="oʊ">oʻ</phoneme>
                        {" harfi" if "harfi" in lower else ""}
                    </voice>
                </speak>'''
    
    return None


def get_voice_name(language: str) -> str:
    """Get appropriate voice name for language"""
    voices = {
        "uz-UZ": "uz-UZ-MadinaNeural",
        "ru-RU": "ru-RU-DariyaNeural",
    }
    return voices.get(language, "uz-UZ-MadinaNeural")


@router.post("/text-to-speech")
async def text_to_speech(request: TextToSpeechRequest):
    """
    Convert text to speech for any supported language
    Supported languages: uz-UZ (Uzbek), ru-RU (Russian)
    """
    if not request.text:
        error_messages = {
            "uz-UZ": "Matn kiritilmagan.",
            "ru-RU": "Текст не введен."
        }
        raise HTTPException(
            status_code=400, 
            detail=error_messages.get(request.language, "Text not provided.")
        )
    
    # Normalize text based on language
    if request.language == "uz-UZ":
        norm_text = normalize_uzbek(request.text)
    elif request.language == "ru-RU":
        norm_text = normalize_russian(request.text)
    else:
        norm_text = request.text
    
    # Configure Azure Speech via REST API
    speech_key = settings.AZURE_SPEECH_KEY
    speech_region = settings.AZURE_SPEECH_REGION
    
    if not speech_key:
        raise HTTPException(
            status_code=501, 
            detail="Azure Speech key not configured"
        )
    
    voice_name = get_voice_name(request.language)
    
    # Check if we need special SSML (only for Uzbek special characters)
    ssml = None
    if request.language == "uz-UZ":
        ssml = build_uzbek_ssml(norm_text)
    
    # If no special SSML, build a standard one with prosody for children
    if not ssml:
        escaped = escape(norm_text)
        lang = request.language or "uz-UZ"
        ssml = f"""<speak version='1.0' xml:lang='{lang}'>
            <voice name='{voice_name}'>
                <prosody rate='-20%'>{escaped}</prosody>
            </voice>
        </speak>"""
    
    try:
        # Get token
        token_url = f"https://{speech_region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        token_resp = http_requests.post(token_url, headers={"Ocp-Apim-Subscription-Key": speech_key})
        token_resp.raise_for_status()
        
        # TTS via REST
        tts_url = f"https://{speech_region}.tts.speech.microsoft.com/cognitiveservices/v1"
        tts_resp = http_requests.post(tts_url, headers={
            "Authorization": f"Bearer {token_resp.text}",
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
            "User-Agent": "Alif24-Backend"
        }, data=ssml.encode('utf-8'))
        tts_resp.raise_for_status()
        
        return Response(content=tts_resp.content, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during speech synthesis: {str(e)}"
        )


@router.get("/")
async def letters_home():
    """Letters module home"""
    return {
        "module": "letters",
        "status": "active",
        "supported_languages": ["uz-UZ", "ru-RU"],
        "endpoints": [
            {"path": "/text-to-speech", "method": "POST", "description": "Convert text to speech"}
        ]
    }
