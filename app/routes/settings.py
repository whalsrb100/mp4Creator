from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from classes.settings import Settings
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
settings = Settings()

router = APIRouter()

@router.get("/settings", response_class=HTMLResponse)
def get_settings(request: Request):
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "settings": settings,
    })

@router.post("/settings", response_class=HTMLResponse)
def post_settings(request: Request, app_title: str = Form(...), theme: str = Form(...)):
    settings.app_title = app_title
    settings.theme = theme
    settings._save_settings()
    return RedirectResponse(url="/settings", status_code=303)
