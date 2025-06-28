from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes import settings as settings_route
import os

app = FastAPI()

# 정적 파일 제공
if not os.path.exists('static'):
    os.makedirs('static')
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# 라우터 등록
app.include_router(settings_route.router)

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/help")
def help_page(request: Request):
    return templates.TemplateResponse("help.html", {"request": request})
