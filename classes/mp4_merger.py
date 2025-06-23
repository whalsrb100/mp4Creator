import os
import subprocess
from typing import List
from dataclasses import dataclass
import tempfile

class MP4Merger:
    def __init__(self):
        self._mp4_files: List[str] = []
        self._output_path: str = ""
        self._temp_file = None

    @property
    def mp4_files(self) -> List[str]:
        """입력 MP4 파일들의 경로 리스트를 반환"""
        return self._mp4_files

    @mp4_files.setter
    def mp4_files(self, files: List[str]):
        """입력 MP4 파일들의 경로 리스트를 설정"""
        if not isinstance(files, list):
            raise ValueError("mp4_files는 리스트 타입이어야 합니다")
        
        # 파일 존재 여부 확인
        for file in files:
            if not os.path.exists(file):
                raise FileNotFoundError(f"파일이 존재하지 않습니다: {file}")
            if not file.lower().endswith('.mp4'):
                raise ValueError(f"MP4 파일이 아닙니다: {file}")
        
        self._mp4_files = files

    @property
    def output_path(self) -> str:
        """통합된 MP4 파일의 출력 경로를 반환"""
        return self._output_path

    @output_path.setter
    def output_path(self, path: str):
        """통합된 MP4 파일의 출력 경로를 설정"""
        if not isinstance(path, str):
            raise ValueError("output_path는 문자열 타입이어야 합니다")
        if not path.lower().endswith('.mp4'):
            raise ValueError("output_path는 .mp4 확장자여야 합니다")
        
        dir_path = os.path.dirname(path)
        if dir_path and not os.path.exists(dir_path):
            raise FileNotFoundError(f"출력 경로의 디렉토리가 존재하지 않습니다: {dir_path}")
        
        self._output_path = path

    def _create_ffmpeg_input_file(self) -> str:
        """ffmpeg용 입력 파일 리스트를 생성"""
        # 현재 디렉토리에 임시 파일 생성
        temp_file = open("ffmpeg_input_list.txt", "w", encoding="utf-8")
        for file in self._mp4_files:
            temp_file.write(f"file '{file}'\n")
        temp_file.close()
        self._temp_file = "ffmpeg_input_list.txt"
        return self._temp_file

    def merge(self) -> str:
        """MP4 파일들을 통합하여 새로운 MP4 파일 생성"""
        if not self._mp4_files:
            raise ValueError("통합할 MP4 파일들이 설정되지 않았습니다")
        if not self._output_path:
            raise ValueError("출력 경로가 설정되지 않았습니다")

        try:
            # ffmpeg 입력 파일 생성
            input_file = self._create_ffmpeg_input_file()
            
            # ffmpeg 명령어 실행
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', input_file,
                '-c', 'copy',
                self._output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"ffmpeg 오류: {result.stderr}")
            
            return self._output_path
            
        finally:
            # 임시 파일 정리
            if self._temp_file and os.path.exists(self._temp_file):
                os.remove(self._temp_file)
                self._temp_file = None
