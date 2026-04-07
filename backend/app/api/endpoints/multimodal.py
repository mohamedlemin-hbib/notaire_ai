from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.services.voice_service import transcribe_voice_message

router = APIRouter()

@router.post("/voice-to-text")
async def voice_to_text(file: UploadFile = File(...)):
    """
    Endpoint pour envoyer un message vocal et obtenir une transcription/intention.
    """
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un audio.")

    try:
        audio_content = await file.read()
        result = transcribe_voice_message(audio_content, mime_type=file.content_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.close()
