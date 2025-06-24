from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from classes.settings import Settings
import uvicorn
import os

app = FastAPI()
settings = Settings()

# 정적 파일 제공 (CSS 등)
if not os.path.exists('static'):
    os.makedirs('static')
app.mount("/static", StaticFiles(directory="static"), name="static")

# 기본 페이지 (다크테마)
@app.get("/", response_class=HTMLResponse)
def read_root():
    return f"""
    <!DOCTYPE html>
    <html lang='ko'>
    <head>
        <meta charset='UTF-8'>
        <title>{settings.app_title or 'mp4Creator'}</title>
        <link rel='stylesheet' href='/static/dark.css'>
    </head>
    <body>
        <div class='container'>
            <h1>{settings.app_title or 'mp4Creator'}</h1>
            <a href='/settings'>설정 페이지로 이동</a>
        </div>
    </body>
    </html>
    """

# 설정 페이지 (클래스 활용)
@app.get("/settings", response_class=HTMLResponse)
def get_settings():
    return f"""
    <!DOCTYPE html>
    <html lang='ko'>
    <head>
        <meta charset='UTF-8'>
        <title>설정</title>
        <link rel='stylesheet' href='/static/dark.css'>
    </head>
    <body>
        <div class='container'>
            <h2>설정</h2>
            <form method='post'>
                <label>앱 타이틀: <input type='text' name='app_title' value='{settings.app_title}' /></label><br>
                <label>테마: <select name='theme'>
                    {''.join([f'<option value="{t}" {'selected' if t==settings.theme else ''}>{t}</option>' for t in settings.themes_list])}
                </select></label><br>
                <button type='submit'>저장</button>
            </form>
            <a href='/'>메인으로</a>
        </div>
    </body>
    </html>
    """

@app.post("/settings", response_class=HTMLResponse)
def post_settings(app_title: str = Form(...), theme: str = Form(...)):
    settings.app_title = app_title
    settings.theme = theme
    settings._save_settings()
    return RedirectResponse(url="/settings", status_code=303)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
