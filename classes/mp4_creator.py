import os
import subprocess
from typing import List, Dict, Tuple, Optional
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ImageClip
from PIL import Image, ImageDraw, ImageFont
import requests
import tempfile
from classes.settings import Settings
from classes.tts import TextToSpeech
from classes.giphy import GiphySearch
from classes.spreadsheet_read import SpreadsheetRead
from classes.drive import DriveUpload
import asyncio

class MP4Creator:
    def __init__(self):
        """MP4 동영상 생성 클래스"""
        self._settings = Settings()
        self._script_text: str = ""
        self._output_path: str = ""
        self._video_width: int = 1920
        self._video_height: int = 1080
        self._fps: int = 30
        self._background_color: str = "#000000"
        self._subtitle_font_size: int = 48  # 일반보다 큰 폰트
        self._subtitle_position: str = "bottom"  # 화면 중간보다 아래
        self._temp_files: List[str] = []
        self._external_audio_file: Optional[str] = None  # 외부 음성 파일
        self._external_subtitles: Optional[List[Dict]] = None  # 외부 자막 정보
    
    @property
    def script_text(self) -> str:
        """대본 텍스트를 반환"""
        return self._script_text
    
    @script_text.setter
    def script_text(self, value: str) -> None:
        """대본 텍스트를 설정"""
        self._script_text = value
    
    @property
    def output_path(self) -> str:
        """출력 MP4 파일 경로를 반환"""
        return self._output_path
    
    @output_path.setter
    def output_path(self, value: str) -> None:
        """출력 MP4 파일 경로를 설정"""
        self._output_path = value
    
    def _download_image(self, url: str, output_path: str) -> str:
        """이미지 URL에서 파일을 다운로드"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self._temp_files.append(output_path)
            return output_path
        except Exception as e:
            raise Exception(f"이미지 다운로드 실패: {str(e)}")
    
    def _search_images_for_text(self, text: str, limit: int = 1) -> List[str]:
        """텍스트에서 키워드를 추출하여 이미지 검색"""
        # [검색어:키워드] 패턴 찾기
        import re
        search_pattern = r'\[검색어:([^\]]+)\]'
        matches = re.findall(search_pattern, text)
        
        image_urls = []
        giphy = GiphySearch()
        
        for keyword in matches:
            try:
                giphy.search_query = keyword
                giphy.limit = limit
                results = giphy.search()
                
                if results:
                    image_urls.append(results[0]['url'])
            except Exception as e:
                print(f"이미지 검색 실패 ({keyword}): {e}")
        
        return image_urls
    
    def _create_subtitle_clip(self, text: str, start_time: float, end_time: float) -> TextClip:
        """자막 클립 생성 (화면 중간보다 아래, 큰 폰트)"""
        # 자막 위치 계산 (화면 중간보다 아래)
        y_position = int(self._video_height * 0.75)  # 화면의 75% 지점
        
        subtitle_clip = TextClip(
            text,
            fontsize=self._subtitle_font_size,
            color='white',
            font='Noto-Sans-CJK-KR-Bold',
            stroke_color='black',
            stroke_width=2
        ).set_position(('center', y_position)).set_start(start_time).set_end(end_time)
        
        return subtitle_clip
    
    def _create_video_from_image(self, image_path: str, duration: float) -> ImageClip:
        """이미지로부터 비디오 클립 생성"""
        # 이미지를 비디오 해상도에 맞게 리사이즈
        with Image.open(image_path) as img:
            # 이미지 비율 유지하면서 리사이즈
            img_ratio = img.width / img.height
            video_ratio = self._video_width / self._video_height
            
            if img_ratio > video_ratio:
                # 이미지가 더 넓음 - 높이를 비디오 높이에 맞춤
                new_height = self._video_height
                new_width = int(new_height * img_ratio)
            else:
                # 이미지가 더 높음 - 너비를 비디오 너비에 맞춤
                new_width = self._video_width
                new_height = int(new_width / img_ratio)
            
            # 리사이즈
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 비디오 크기의 검은 배경 생성
            background = Image.new('RGB', (self._video_width, self._video_height), self._background_color)
            
            # 이미지를 중앙에 배치
            x_offset = (self._video_width - new_width) // 2
            y_offset = (self._video_height - new_height) // 2
            background.paste(img_resized, (x_offset, y_offset))
            
            # 임시 파일로 저장
            temp_image_path = tempfile.mktemp(suffix='.png')
            background.save(temp_image_path)
            self._temp_files.append(temp_image_path)
        
        # MoviePy로 비디오 클립 생성
        video_clip = ImageClip(temp_image_path).set_duration(duration)
        return video_clip
    
    def _cleanup_temp_files(self):
        """임시 파일들 정리"""
        for file_path in self._temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
        self._temp_files = []
    
    async def create_mp4(self) -> str:
        """MP4 동영상 생성"""
        if not self._script_text and not self._external_audio_file:
            raise ValueError("대본 텍스트 또는 외부 음성 파일이 설정되지 않았습니다")
        if not self._output_path:
            raise ValueError("출력 경로가 설정되지 않았습니다")
        
        try:
            # 1. 음성 파일 준비 (외부 파일이 있으면 사용, 없으면 TTS 생성)
            if self._external_audio_file and os.path.exists(self._external_audio_file):
                print("🎤 외부 음성 파일 사용 중...")
                audio_file = self._external_audio_file
                subtitles = self._external_subtitles or []
            else:
                print("🎤 음성 파일 생성 중...")
                tts = TextToSpeech()
                tts.text = self._script_text
                audio_path = tempfile.mktemp(suffix='.mp3')
                tts.output_path = audio_path
                
                audio_file, subtitles = await tts.convert()
                self._temp_files.append(audio_file)
            
            # 2. 이미지 검색 및 다운로드
            print("🖼️ 이미지 검색 중...")
            # 외부 음성 사용 시 script_text가 없을 수 있으므로 자막 텍스트에서 검색
            search_text = self._script_text
            if not search_text and subtitles:
                search_text = " ".join([sub['text'] for sub in subtitles])
            
            image_urls = self._search_images_for_text(search_text)
            
            # 3. 비디오 클립들 생성
            video_clips = []
            subtitle_clips = []
            current_time = 0.0
            
            # 오디오 클립 로드
            audio_clip = AudioFileClip(audio_file)
            total_duration = audio_clip.duration
            
            if image_urls:
                # 이미지가 있는 경우
                image_duration = total_duration / len(image_urls)
                
                for i, image_url in enumerate(image_urls):
                    print(f"📥 이미지 다운로드 중... ({i+1}/{len(image_urls)})")
                    
                    # 이미지 다운로드
                    temp_image_path = tempfile.mktemp(suffix='.jpg')
                    downloaded_image = self._download_image(image_url, temp_image_path)
                    
                    # 비디오 클립 생성
                    video_clip = self._create_video_from_image(downloaded_image, image_duration)
                    video_clip = video_clip.set_start(current_time)
                    video_clips.append(video_clip)
                    
                    current_time += image_duration
            else:
                # 이미지가 없는 경우 단순한 배경
                print("🎨 기본 배경 생성 중...")
                temp_bg_path = tempfile.mktemp(suffix='.png')
                
                # 단순한 배경 이미지 생성
                background = Image.new('RGB', (self._video_width, self._video_height), self._background_color)
                background.save(temp_bg_path)
                self._temp_files.append(temp_bg_path)
                
                video_clip = self._create_video_from_image(temp_bg_path, total_duration)
                video_clips.append(video_clip)
            
            # 4. 자막 클립 생성
            print("📝 자막 생성 중...")
            for subtitle in subtitles:
                # 키 이름 확인 (start/end 또는 start_time/end_time)
                start_time = subtitle.get('start_time', subtitle.get('start', 0))
                end_time = subtitle.get('end_time', subtitle.get('end', 0))
                text = subtitle.get('text', '')
                
                subtitle_clip = self._create_subtitle_clip(
                    text,
                    start_time,
                    end_time
                )
                subtitle_clips.append(subtitle_clip)
            
            # 5. 모든 클립 합성
            print("🎬 비디오 합성 중...")
            
            # 비디오 클립들 합치기
            if len(video_clips) > 1:
                final_video = CompositeVideoClip(video_clips, size=(self._video_width, self._video_height))
            else:
                final_video = video_clips[0]
            
            # 자막 추가
            if subtitle_clips:
                final_video = CompositeVideoClip([final_video] + subtitle_clips)
            
            # 오디오 추가
            final_video = final_video.set_audio(audio_clip)
            
            # 6. MP4 파일로 출력
            print("💾 MP4 파일 저장 중...")
            final_video.write_videofile(
                self._output_path,
                fps=self._fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=tempfile.mktemp(suffix='.m4a'),
                remove_temp=True
            )
            
            print("✅ MP4 생성 완료!")
            return self._output_path
            
        except Exception as e:
            raise Exception(f"MP4 생성 실패: {str(e)}")
        
        finally:
            # 임시 파일 정리
            self._cleanup_temp_files()
    
    async def create_from_spreadsheet(self, script_id: str) -> str:
        """스프레드시트에서 대본을 읽어와서 MP4 생성"""
        try:
            # 스프레드시트에서 대본 읽기
            spreadsheet = SpreadsheetRead()
            data = spreadsheet.read()
            
            # 지정된 ID의 대본 찾기
            script_data = None
            for row in data:
                if row.get('ID') == script_id:
                    script_data = row
                    break
            
            if not script_data:
                raise ValueError(f"ID '{script_id}'에 해당하는 대본을 찾을 수 없습니다")
            
            # 대본 텍스트 설정
            self.script_text = script_data.get('대본', '')
            
            if not self.script_text:
                raise ValueError("대본 내용이 비어있습니다")
            
            # MP4 생성
            return await self.create_mp4() # await 추가
            
        except Exception as e:
            raise Exception(f"스프레드시트에서 MP4 생성 실패: {str(e)}")
    
    async def upload_to_drive(self, local_path: str, filename: str) -> dict:
        """생성된 MP4를 구글 드라이브에 업로드"""
        try:
            uploader = DriveUpload()
            uploader.upload_filename = filename
            return uploader.upload(local_path)
        except Exception as e:
            raise Exception(f"드라이브 업로드 실패: {str(e)}")
    
    def set_external_audio(self, audio_file: str, subtitles: List[Dict] = None) -> None:
        """외부에서 생성된 음성 파일과 자막 정보를 설정"""
        self._external_audio_file = audio_file
        self._external_subtitles = subtitles or []
