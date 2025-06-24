# mp4Creator 프로젝트

FastAPI 기반 웹앱

## 구조

- app/main.py : FastAPI 앱 진입점
- app/routes/ : 라우터(페이지별)
- app/services/ : 서비스/비즈니스 로직
- classes/ : 핵심 클래스
- static/css/ : CSS 파일(페이지/기능별)
- static/js/ : JS 파일(페이지/기능별)
- templates/ : Jinja2 템플릿(페이지별)
- templates/base.html : 모든 템플릿의 베이스

## 개발 규칙
- CSS/JS/HTML 파일은 기능별로 분리, 중복 없이 관리
- 템플릿은 base.html 상속
- HTML 내에 직접 style/script 작성 금지(외부 파일만 include)