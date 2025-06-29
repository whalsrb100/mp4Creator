from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from classes.tts import TextToSpeech
from classes.settings import Settings
import tempfile
import os
import asyncio

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/tts", response_class=HTMLResponse)
async def tts_page(request: Request):
    """음성 생성 페이지"""
    settings = Settings()
    
    # 사용 가능한 목소리 옵션
    voices_list = settings.voices_list
    voice_options = []
    for voice_name, voice_code in voices_list.items():
        voice_options.append({
            "value": voice_name,
            "label": f"{voice_name} - {voice_code}"
        })
    
    return templates.TemplateResponse("tts.html", {
        "request": request,
        "voice_options": voice_options
    })

@router.post("/api/generate-audio")
async def generate_audio_api(
    text: str = Form(...),
    voice: str = Form(...),
    speed: str = Form("1.0"),
    pause: float = Form(0.0)  # 쉼 옵션 추가
):
    """음성 생성 API"""
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="텍스트가 비어있습니다.")
        
        # TTS 객체 생성
        tts = TextToSpeech(output_dir="outputs")
        tts.set_voice(voice)
        tts.set_speed(speed)
        
        # 쉼 옵션이 있으면 텍스트 끝에 추가
        if pause > 0:
            text = text + f" [쉼:{pause}]"
        
        # 음성 생성
        result = await tts.convert(text)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        audio_path = result['audio_path']
        subtitles = result['subtitles']
        
        # 파일 크기 계산
        file_size = os.path.getsize(audio_path)
        file_size_mb = round(file_size / (1024 * 1024), 2)
        
        # 총 재생 시간 계산
        total_duration = max([sub['end_time'] for sub in subtitles]) if subtitles else 0
        
        return JSONResponse(content={
            "success": True,
            "message": "음성이 성공적으로 생성되었습니다.",
            "file_path": audio_path,
            "file_size": f"{file_size_mb} MB",
            "duration": f"{total_duration:.2f}초",
            "subtitles": subtitles,  # 자막 정보 추가
            "download_url": f"/download-audio?file={os.path.basename(audio_path)}"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"음성 생성 중 오류가 발생했습니다: {str(e)}")

@router.get("/download-audio")
async def download_audio(file: str):
    """생성된 음성 파일 다운로드"""
    file_path = os.path.join("outputs", file)
    
    if not os.path.exists(file_path):
        # 임시 디렉토리에서도 찾아보기
        temp_path = os.path.join(tempfile.gettempdir(), file)
        if os.path.exists(temp_path):
            file_path = temp_path
        else:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    
    return FileResponse(
        path=file_path,
        filename=file,
        media_type='audio/mpeg'
    )

@router.post("/api/generate-srt")
async def generate_srt_api(
    text: str = Form(...),
    voice: str = Form(...),
    speed: str = Form("1.0")
):
    """텍스트에서 자막 파일 생성 API"""
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="텍스트가 비어있습니다.")
        
        # TTS 객체 생성하여 자막 정보만 생성
        tts = TextToSpeech(output_dir="outputs")
        tts.set_voice(voice)
        tts.set_speed(speed)
        
        result = await tts.convert(text)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        subtitles = result['subtitles']
        
        # SRT 파일 생성
        srt_content = tts.subtitles_to_srt(subtitles)
        
        # 임시 SRT 파일 생성
        temp_srt = tempfile.mktemp(suffix='.srt')
        with open(temp_srt, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        return FileResponse(
            path=temp_srt,
            filename="subtitles.srt",
            media_type='text/plain'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SRT 파일 생성 중 오류가 발생했습니다: {str(e)}")

def format_srt_time(seconds: float) -> str:
    """초를 SRT 시간 형식(HH:MM:SS,mmm)으로 변환"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
