#!/bin/bash
# venv 폴더가 있으면 삭제
if [ -d "venv" ]; then
    rm -rf venv
fi
# 가상환경 생성
python3 -m venv venv
# 가상환경 활성화
source venv/bin/activate
# pip 최신화
python3 -m pip install --upgrade pip
# requirements.txt 설치
pip install -r requirements.txt
echo "설치 완료!"
