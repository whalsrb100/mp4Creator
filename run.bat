@echo off
REM 가상환경 활성화
call venv\Scripts\activate
REM FastAPI 앱 실행
uvicorn app.main:app --reload
