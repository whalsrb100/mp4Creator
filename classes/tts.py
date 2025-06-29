import edge_tts
import asyncio
import re
import os
import time
import tempfile
import logging
from typing import List, Dict, Tuple, Optional
from pydub import AudioSegment
from .settings import Settings

logger = logging.getLogger(__name__)

class TextToSpeech:
    def __init__(self, output_dir: str = "outputs"):
        """텍스트를 음성으로 변환하는 클래스"""
        self.settings = Settings()
        self.output_dir = output_dir
        self.voices = self.settings.voices_list  # settings.json의 voices_list
        self.voice = self.voices.get("여자1", "ko-KR-SunHiNeural")  # 기본 목소리
        self.speed = "+0%"  # 기본 속도 (백분율 형태)
        
        # 출력 디렉토리 생성
        os.makedirs(self.output_dir, exist_ok=True)
    
    def set_voice(self, voice_key: str):
        """목소리 설정"""
        print(f"🎤 설정할 목소리: '{voice_key}'")
        print(f"🎤 사용 가능한 목소리: {list(self.voices.keys())}")
        
        if voice_key in self.voices:
            self.voice = self.voices[voice_key]
            print(f"🎤 선택된 목소리: {self.voice}")
        else:
            print(f"🎤 목소리 키를 찾을 수 없음, 직접 설정: {voice_key}")
            self.voice = voice_key  # 직접 음성 ID 지정
    
    def set_speed(self, speed: str):
        """속도 설정 (예: "0.5", "1.0", "1.5", "2.0")"""
        self.speed = speed
    
    def _convert_speed_to_rate(self, speed: str) -> str:
        """속도를 Edge-TTS rate 형식으로 변환 (부호 있는 백분율 입력)"""
        print(f"🎵 속도 변환 시작: '{speed}' (타입: {type(speed)})")
        
        # 이미 백분율 형태인지 확인
        if '%' in speed:
            # 부호 있는 백분율 형태를 그대로 반환
            speed = speed.strip()
            print(f"🎵 백분율 입력: {speed}")
            
            # 백분율 값 검증 및 정규화
            try:
                # +50%, -20% 등에서 숫자 부분 추출
                match = re.match(r'([+-]?\d+)%', speed)
                if match:
                    percentage = int(match.group(1))
                    # 범위 제한: -50% ~ +100%
                    percentage = max(-50, min(100, percentage))
                    result = f"{percentage:+d}%"
                    print(f"🎵 정규화된 백분율: {result}")
                    return result
                else:
                    print(f"🎵 잘못된 백분율 형식: {speed}")
                    return "+0%"
            except:
                print(f"🎵 백분율 파싱 오류: {speed}")
                return "+0%"
        
        # 레거시 숫자 형태 (1.5 등) 지원 - 점진적 마이그레이션
        try:
            speed_float = float(speed)
            print(f"🎵 레거시 숫자 입력: {speed_float}")
            
            if speed_float <= 0.0:
                result = "-50%"  # 최소 속도
            elif speed_float < 1.0:
                # 0.5 ~ 1.0 범위: -50% ~ 0%
                if speed_float <= 0.5:
                    percentage = -50
                else:
                    percentage = int((speed_float - 0.5) / 0.5 * 50 - 50)
                result = f"{percentage:+d}%"
            elif speed_float == 1.0:
                result = "+0%"  # 기본 속도
            elif speed_float <= 2.0:
                # 1.0 ~ 2.0 범위: 0% ~ +100%
                percentage = int((speed_float - 1.0) / 1.0 * 100)
                result = f"+{percentage}%"
            else:
                result = "+100%"
            
            print(f"🎵 레거시 변환 결과: {result}")
            return result
        except:
            print(f"🎵 속도 변환 오류: {speed}")
            return "+0%"
    
    def _convert_percentage_to_multiplier(self, speed: str) -> float:
        """백분율 속도를 배수로 변환 (pydub용)"""
        if '%' in speed:
            try:
                # +50%, -20% 등에서 숫자 부분 추출
                match = re.match(r'([+-]?\d+)%', speed)
                if match:
                    percentage = int(match.group(1))
                    # 백분율을 배수로 변환: +50% = 1.5배, -20% = 0.8배
                    multiplier = 1.0 + (percentage / 100.0)
                    return max(0.1, min(3.0, multiplier))  # 0.1~3.0 범위 제한
                else:
                    return 1.0
            except:
                return 1.0
        else:
            # 레거시 숫자 형태
            try:
                return float(speed)
            except:
                return 1.0
    
    def _extract_voice_speed_options(self, text: str) -> Tuple[str, Optional[str], Optional[str]]:
        """텍스트에서 목소리와 속도 옵션을 추출하고 정리된 텍스트 반환"""
        voice = None
        speed = None
        clean_text = text
        
        print(f"🔍 옵션 추출 시작: '{text}'")
        
        # 목소리 옵션 패턴
        voice_pattern = r'\[(목소리|VOICE):([^\]]+)\]'
        voice_match = re.search(voice_pattern, text)
        if voice_match:
            voice = voice_match.group(2)
            clean_text = re.sub(voice_pattern, '', clean_text)
            print(f"🎤 목소리 옵션 발견: {voice}")
        
        # 속도 옵션 패턴
        speed_pattern = r'\[(속도|SPEED):([^\]]+)\]'
        speed_match = re.search(speed_pattern, text)
        if speed_match:
            speed = speed_match.group(2)
            clean_text = re.sub(speed_pattern, '', clean_text)
            print(f"🎵 속도 옵션 발견: {speed}")
        
        # 기타 옵션 제거 (GIPHY, GOOGLE 등)
        other_pattern = r'\[(GIPHY|GOOGLE|GIPHY_URL|GOOGLE_URL|검색어):([^\]]+)\]'
        clean_text = re.sub(other_pattern, '', clean_text)
        
        print(f"🔍 추출 결과 - 음성: {voice}, 속도: {speed}, 정리된 텍스트: '{clean_text.strip()}'")
        return clean_text.strip(), voice, speed
    
    def _process_line_with_pauses(self, line: str) -> List[Dict]:
        """한 줄의 텍스트를 쉼 명령어 기준으로 분리하여 처리"""
        # 쉼 명령어 패턴
        pause_pattern = r'\[쉼:([^\]]+)\]'
        
        segments = []
        current_pos = 0
        
        for match in re.finditer(pause_pattern, line):
            # 쉼 명령어 앞의 텍스트
            before_text = line[current_pos:match.start()].strip()
            if before_text:
                segments.append({'type': 'text', 'content': before_text})
            
            # 쉼 명령어
            try:
                pause_duration = float(match.group(1))
                segments.append({'type': 'pause', 'duration': pause_duration})
            except ValueError:
                pass
            
            current_pos = match.end()
        
        # 마지막 남은 텍스트
        remaining_text = line[current_pos:].strip()
        if remaining_text:
            segments.append({'type': 'text', 'content': remaining_text})
        
        return segments
    
    async def convert(self, text: str) -> Dict:
        """
        텍스트를 음성으로 변환
        
        동작 방식:
        1. 줄별로 분리하여 처리
        2. 각 줄에서 목소리/속도 옵션이 있으면 그 줄 전체에 적용 (줄바꿈 전까지 유지)
        3. 쉼 명령어는 그 자리에서 즉시 무음 삽입
        4. 다음 줄로 넘어가면 목소리/속도는 기본값으로 초기화
        
        Args:
            text: 변환할 텍스트
            
        Returns:
            dict: 
                - success: 성공 여부
                - audio_path: 생성된 음성 파일 경로 (성공시)
                - error: 오류 메시지 (실패시)
                - subtitles: 자막 정보 (성공시)
        """
        try:
            if not text.strip():
                return {
                    'success': False,
                    'error': '변환할 텍스트가 없습니다.'
                }
            
            # 줄별로 분리
            lines = text.strip().split('\n')
            audio_segments = []
            subtitles = []
            current_time = 0.0
            
            for line in lines:
                if not line.strip():
                    continue
                
                # 이 줄에서 목소리/속도 옵션 추출 (줄 전체에 적용)
                line_without_options, line_voice, line_speed = self._extract_voice_speed_options(line)
                
                # 이 줄에서 사용할 목소리와 속도 설정
                current_voice = self.voice  # 기본값으로 시작
                current_rate = self._convert_speed_to_rate(self.speed)  # 기본값으로 시작
                
                if line_voice:
                    if line_voice in self.voices:
                        current_voice = self.voices[line_voice]
                    else:
                        current_voice = line_voice  # 직접 지정된 음성
                
                if line_speed:
                    current_rate = self._convert_speed_to_rate(line_speed)
                    print(f"🎵 줄별 속도 설정: {line_speed} -> {current_rate}")
                
                print(f"🎤 현재 음성: {current_voice}, 속도: {current_rate}")
                
                # 이 줄을 쉼 명령어 기준으로 세그먼트 분리
                segments = self._process_line_with_pauses(line_without_options)
                
                for segment in segments:
                    if segment['type'] == 'pause':
                        # 쉼 명령어 처리 - 무음 추가
                        duration = segment['duration']
                        silence = AudioSegment.silent(duration=int(duration * 1000))
                        audio_segments.append(silence)
                        current_time += duration
                        
                    elif segment['type'] == 'text':
                        clean_text = segment['content'].strip()
                        if not clean_text:
                            continue
                        
                        # Edge-TTS로 음성 생성
                        print(f"🎵 TTS 생성 전 - 텍스트: '{clean_text}', 음성: {current_voice}, 속도: {current_rate}")
                        
                        # Edge-TTS에서 속도 설정 방법 개선
                        tts_communicate = edge_tts.Communicate(
                            text=clean_text,
                            voice=current_voice,
                            rate=current_rate  # 생성자에서 직접 설정
                        )
                        
                        print(f"🎵 TTS 객체 설정 완료 - rate: {current_rate}")
                        
                        # 임시 파일에 저장
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                        temp_file.close()
                        
                        print(f"🎵 음성 파일 생성 시작: {temp_file.name}")
                        start_time = time.time()
                        
                        try:
                            await tts_communicate.save(temp_file.name)
                            end_time = time.time()
                            generation_time = end_time - start_time
                            print(f"🎵 음성 파일 생성 완료: {generation_time:.2f}초 소요")
                            
                            # AudioSegment로 로드
                            audio_segment = AudioSegment.from_mp3(temp_file.name)
                            
                            # 속도 조절을 pydub로 처리 (Edge-TTS가 제대로 적용하지 않는 경우)
                            if line_speed and line_speed not in ["1.0", "+0%"]:
                                speed_multiplier = self._convert_percentage_to_multiplier(line_speed)
                                print(f"🎵 pydub로 속도 조절: {line_speed} -> {speed_multiplier}배")
                                
                                # 속도 조절: 빠르게 하려면 frame_rate를 높이고, 느리게 하려면 낮춘다
                                # 그 후 원래 sample_rate로 되돌린다
                                if speed_multiplier != 1.0:
                                    # 속도 조절 적용
                                    new_sample_rate = int(audio_segment.frame_rate * speed_multiplier)
                                    audio_segment = audio_segment._spawn(audio_segment.raw_data, 
                                                                       overrides={"frame_rate": new_sample_rate})
                                    audio_segment = audio_segment.set_frame_rate(22050)  # 원래 샘플레이트로 복원
                            
                            segment_duration = len(audio_segment) / 1000.0
                            print(f"🎵 최종 음성 길이: {segment_duration:.2f}초")
                            
                            audio_segments.append(audio_segment)
                            
                            # 자막 정보 추가
                            subtitles.append({
                                'start_time': current_time,
                                'end_time': current_time + segment_duration,
                                'text': clean_text
                            })
                            current_time += segment_duration
                            
                        finally:
                            if os.path.exists(temp_file.name):
                                os.unlink(temp_file.name)
            
            if not audio_segments:
                return {
                    'success': False,
                    'error': '변환할 텍스트가 없습니다.'
                }
            
            # 모든 세그먼트 합치기
            final_audio = audio_segments[0]
            for segment in audio_segments[1:]:
                final_audio += segment
            
            # 최종 파일 저장
            output_path = os.path.join(self.output_dir, f"tts_{int(time.time())}.mp3")
            final_audio.export(output_path, format="mp3")
            
            return {
                'success': True,
                'audio_path': output_path,
                'subtitles': subtitles
            }
            
        except Exception as e:
            logger.error(f"TTS 변환 오류: {str(e)}")
            return {
                'success': False,
                'error': f"TTS 변환 실패: {str(e)}"
            }
    
    def subtitles_to_srt(self, subtitles: List[Dict]) -> str:
        """자막 정보를 SRT 형식으로 변환"""
        srt_content = []
        
        for i, subtitle in enumerate(subtitles, 1):
            start_time = self._seconds_to_srt_time(subtitle['start_time'])
            end_time = self._seconds_to_srt_time(subtitle['end_time'])
            text = subtitle['text']
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(text)
            srt_content.append("")  # 빈 줄
        
        return '\n'.join(srt_content)
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """초를 SRT 시간 형식으로 변환 (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"