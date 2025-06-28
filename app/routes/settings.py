from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from classes.settings import Settings
from fastapi.templating import Jinja2Templates

import typing

templates = Jinja2Templates(directory="templates")
settings = Settings()

router = APIRouter()

@router.get("/settings", response_class=HTMLResponse)
def get_settings(request: Request):
    # settings._settings는 settings.json 전체 딕셔너리
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "settings": settings._settings,
    })

@router.post("/settings", response_class=HTMLResponse)
async def post_settings(request: Request):
    form = await request.form()
    # 폼 데이터로 settings.json 전체 갱신 (단순화 예시)
    for k, v in form.items():
        keys = k.split(".")
        d = settings._settings
        for key in keys[:-1]:
            # 리스트면 인덱스를 int로 변환
            if isinstance(d, list):
                key = int(key)
            d = d[key]
        last_key = keys[-1]
        if isinstance(d, list):
            last_key = int(last_key)
        d[last_key] = v
    settings._save_settings()
    return RedirectResponse(url="/settings", status_code=303)
