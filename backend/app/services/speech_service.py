import requests
from fastapi import HTTPException
from app.core.config import settings

class AzureSpeechService:
    def __init__(self):
        self.speech_key = settings.AZURE_SPEECH_KEY
        self.speech_region = settings.AZURE_SPEECH_REGION
        self.token_url = f"https://{self.speech_region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        self.tts_url = f"https://{self.speech_region}.tts.speech.microsoft.com/cognitiveservices/v1"
        self.access_token = None

    def _get_access_token(self):
        """
        Fetch an access token from Azure Cognitive Services.
        Tokens are valid for 10 minutes. 
        For simplicity in this lightweight implementation, we fetch a new one each time 
        or rely on the browser/client to retry if 401. 
         Ideally, cache this for 9 mins.
        """
        headers = {
            "Ocp-Apim-Subscription-Key": self.speech_key
        }
        try:
            response = requests.post(self.token_url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to authenticate with Azure Speech: {e}")

    def generate_speech(self, text: str, voice_name: str = "uz-UZ-MadinaNeural") -> bytes:
        """
        Convert text to speech using Azure TTS REST API.
        Returns raw MP3 audio bytes.
        """
        if not self.speech_key or not self.speech_region:
            raise HTTPException(status_code=500, detail="Azure Speech configuration missing")

        # 1. Get Token
        token = self._get_access_token()

        # 2. Construct SSML
        # Escaping XML chars in text is important, but for now assuming simple text
        # A robust solution needs xml.sax.saxutils.escape(text)
        from xml.sax.saxutils import escape
        escaped_text = escape(text)
        
        ssml = f"""
        <speak version='1.0' xml:lang='uz-UZ'>
            <voice xml:lang='uz-UZ' xml:gender='Female' name='{voice_name}'>
                {escaped_text}
            </voice>
        </speak>
        """

        # 3. Send TTS Request
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
            "User-Agent": "Alif24-Backend"
        }

        try:
            response = requests.post(self.tts_url, headers=headers, data=ssml.encode('utf-8'))
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            # Try to get error text from response
            error_detail = str(e)
            if hasattr(e, 'response') and e.response is not None:
                error_detail = e.response.text
            raise HTTPException(status_code=500, detail=f"Azure TTS failed: {error_detail}")

speech_service = AzureSpeechService()
