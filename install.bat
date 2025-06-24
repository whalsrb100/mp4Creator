@echo off
REM venv 폴더가 있으면 삭제
IF EXIST venv (
    rmdir /s /q venv
)
REM 가상환경 생성
python -m venv venv
REM 가상환경 활성화
call venv\Scripts\activate
REM pip 최신화
python -m pip install --upgrade pip
REM requirements.txt 설치
pip install -r requirements.txt
echo 설치 완료!
