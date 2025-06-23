import edge_tts
import asyncio
import re
from typing import List, Dict, Tuple
from .settings import Settings
import subprocess
import os

class TextToSpeech:
    def __init__(self):
        """텍스트를 MP3로 변환하는 클래스"""
        self._settings = Settings()
        self._text: str = ""
        self._output_path: str = ""
        self._voice: str = self._settings.voices_list["여자1"]
        self._rate: str = "+50%"
        self.pauses: List[float] = []
        self.subtitles: List[Dict] = []  # 자막 타임라인 데이터
    
    @property
    def text(self) -> str:
        """변환할 텍스트를 반환"""
        return self._text
    
    @text.setter
    def text(self, value: str) -> None:
        """변환할 텍스트를 설정"""
        self._text = value
    
    @property
    def output_path(self) -> str:
        """MP3 저장 경로를 반환"""
        return self._output_path
    
    @output_path.setter
    def output_path(self, value: str) -> None:
        """MP3 저장 경로를 설정"""
        self._output_path = value
    
    def _extract_options(self, text: str) -> Tuple[str, Dict]:
        """텍스트에서 옵션을 추출하고 정리된 텍스트 반환"""
        # 옵션 패턴: [VOICE:값], [SPEED:값], [PAUSE:값], [GIPHY:값], [GOOGLE:값], [GIPHY_URL:값], [GOOGLE_URL:값], [목소리:값], [속도:값], [쉼:값], [검색어:값]
        pattern = r'\[(VOICE|SPEED|PAUSE|GIPHY|GOOGLE|GIPHY_URL|GOOGLE_URL|목소리|속도|쉼|검색어):([^\]]+)\]'
        
        # 옵션 추출
        options = {}
        clean_text = text
        
        for match in re.finditer(pattern, text):
            option_type = match.group(1)
            option_value = match.group(2)
            
            if option_type in ('목소리', 'VOICE'):
                options['voice'] = option_value
            elif option_type in ('속도', 'SPEED'):
                options['rate'] = option_value
            elif option_type in ('쉼', 'PAUSE'):
                try:
                    options['pause'] = float(option_value)
                except Exception:
                    pass
            # GIPHY, GOOGLE, URL, 검색어 옵션은 무시
        
        # 옵션 제거
        clean_text = re.sub(pattern, '', text)
        return clean_text.strip(), options
    
    def _split_text_into_segments(self, text: str) -> List[str]:
        """텍스트를 자막 세그먼트로 분리"""
        # 문장 단위로 분리 (마침표, 물음표, 느낌표 기준)
        segments = re.split(r'([.!?])', text)
        result = []
        
        for i in range(0, len(segments)-1, 2):
            if i+1 < len(segments):
                result.append(segments[i] + segments[i+1])
            else:
                result.append(segments[i])
        
        if len(segments) % 2 == 1:
            result.append(segments[-1])
        
        return [s.strip() for s in result if s.strip()]
    
    async def _generate_mp3(self, text: str, options: Dict, output_path: str) -> float:
        """MP3 파일 생성 및 길이 반환 (ffmpeg로 길이 측정)"""
        # options['voice']가 한글이면 실제 edge-tts voice id로 변환
        voice = options.get('voice', self._voice)
        voices_map = self._settings.voices_list
        if voice in voices_map:
            voice = voices_map[voice]
        communicate = edge_tts.Communicate(text, voice)
        if 'rate' in options:
            communicate.rate = options['rate']
        await communicate.save(output_path)
        # ffmpeg로 mp3 길이 측정
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', output_path
        ], capture_output=True, text=True)
        try:
            duration = float(result.stdout.strip())
        except Exception:
            duration = 0.0
        return duration
    
    def _concat_mp3_files(self, segment_paths: List[str], output_path: str):
        """여러 mp3 파일을 ffmpeg로 합치기"""
        # concat용 임시 파일 생성
        concat_list_path = output_path + '.concat.txt'
        with open(concat_list_path, 'w') as f:
            for path in segment_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")
        # ffmpeg concat 실행
        cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_list_path, '-c', 'copy', output_path
        ]
        subprocess.run(cmd, capture_output=True)
        os.remove(concat_list_path)
    
    def convert(self) -> Tuple[str, List[Dict]]:
        """텍스트를 MP3로 변환하고 자막 타임라인 반환"""
        if not self._text:
            raise ValueError("변환할 텍스트가 없습니다.")
        if not self._output_path:
            raise ValueError("출력 파일 경로가 없습니다.")

        # 텍스트를 세그먼트로 분리
        segments = self._split_text_into_segments(self._text)
        current_time = 0.0
        self.subtitles = []
        segment_paths = []

        # 각 세그먼트별로 MP3 생성 및 자막 타임라인 생성
        for i, segment in enumerate(segments):
            # 세그먼트별 옵션 추출
            clean_text, options = self._extract_options(segment)
            if not clean_text:
                continue
            # 세그먼트별 MP3 생성
            segment_path = f"{self._output_path}.segment{i}.mp3"
            duration = asyncio.run(self._generate_mp3(clean_text, options, segment_path))
            segment_paths.append(segment_path)
            # 자막 타임라인 추가
            self.subtitles.append({
                "text": clean_text,
                "start": current_time,
                "end": current_time + duration
            })
            # 다음 세그먼트 시작 시간 계산
            current_time += duration
            if 'pause' in options:
                current_time += options['pause']
        # 모든 세그먼트 MP3 파일을 하나로 합치기 (ffmpeg)
        self._concat_mp3_files(segment_paths, self._output_path)
        # 임시 세그먼트 파일 삭제
        for path in segment_paths:
            os.remove(path)
        return self._output_path, self.subtitles