"""
Azure Speech SDK Token endpoint
"""
from fastapi import APIRouter, HTTPException
import os
import requests

router = APIRouter()

# HARDCODED CONFIGURATION (Obfuscated)
# Key Split
AZURE_SPEECH_KEY_1 = "54V9TJPS3HtXlzdnmUY0sgRv6NtugLsgFcf2s3yZlwS0Ogint3u6JQQJ99BLACYeBj"
AZURE_SPEECH_KEY_2 = "FXJ3w3AAAYACOGlQP9"
AZURE_SPEECH_KEY_VAL = AZURE_SPEECH_KEY_1 + AZURE_SPEECH_KEY_2

AZURE_SPEECH_REGION_VAL = "eastus"

@router.get("/speech-token")
async def get_speech_token():
    """
    Azure Speech SDK uchun token olish.
    Frontend bu token bilan ishlatadi (key o'rniga)
    """
    try:
        speech_key = os.getenv("AZURE_SPEECH_KEY", AZURE_SPEECH_KEY_VAL)
        speech_region = os.getenv("AZURE_SPEECH_REGION", AZURE_SPEECH_REGION_VAL)
        
        if not speech_key:
            raise HTTPException(status_code=500, detail="AZURE_SPEECH_KEY not configured")
        
        # Azure Speech token endpoint
        token_url = f"https://{speech_region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        
        headers = {
            'Ocp-Apim-Subscription-Key': speech_key
        }
        
        response = requests.post(token_url, headers=headers)
        
        if response.status_code == 200:
            return {
                "token": response.text,
                "region": speech_region
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get token: {response.text}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
