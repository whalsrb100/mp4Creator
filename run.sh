#!/bin/bash
# 가상환경 활성화
source venv/bin/activate
# FastAPI 앱 실행
uvicorn app.main:app --reload
