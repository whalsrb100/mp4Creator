from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from typing import Optional
from classes.settings import Settings

class DriveUpload:
    def __init__(self):
        """구글 드라이브 파일 업로드 클래스"""
        self._settings = Settings()
        self._service_account_key_path: str = self._settings.service_account_key_path
        self._upload_directory_id: str = self._settings.image_directory_id
        self._upload_filename: str = ""
        self._service = None
    
    @property
    def service_account_key_path(self) -> str:
        """서비스 계정 키 파일 경로를 반환"""
        return self._service_account_key_path
    
    @service_account_key_path.setter
    def service_account_key_path(self, value: str) -> None:
        """서비스 계정 키 파일 경로를 설정"""
        self._service_account_key_path = value
        # Settings에도 저장
        self._settings.service_account_key_path = value
        # 서비스 객체 초기화
        self._service = None
    
    @property
    def upload_directory_id(self) -> str:
        """업로드할 디렉토리 ID를 반환"""
        return self._upload_directory_id
    
    @upload_directory_id.setter
    def upload_directory_id(self, value: str) -> None:
        """업로드할 디렉토리 ID를 설정"""
        self._upload_directory_id = value
        # Settings에도 저장
        self._settings.image_directory_id = value
    
    @property
    def upload_filename(self) -> str:
        """업로드할 파일 이름을 반환"""
        return self._upload_filename
    
    @upload_filename.setter
    def upload_filename(self, value: str) -> None:
        """업로드할 파일 이름을 설정"""
        self._upload_filename = value
    
    def _get_service(self):
        """구글 드라이브 서비스 객체를 생성"""
        if not self._service:
            credentials = service_account.Credentials.from_service_account_file(
                self._service_account_key_path,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            self._service = build('drive', 'v3', credentials=credentials)
        return self._service
    
    def upload(self, file_path: str) -> dict:
        """
        파일을 구글 드라이브에 업로드
        
        Args:
            file_path (str): 업로드할 파일의 경로
            
        Returns:
            dict: 업로드된 파일의 정보
            
        Raises:
            ValueError: 필수 설정이 누락된 경우
            Exception: 업로드 실패 시
        """
        # 필수 설정 확인
        if not self._service_account_key_path:
            raise ValueError("Service account key path is not set")
        if not self._upload_directory_id:
            raise ValueError("Upload directory ID is not set")
        if not self._upload_filename:
            raise ValueError("Upload filename is not set")
        
        try:
            service = self._get_service()
            
            # 파일 메타데이터 설정
            file_metadata = {
                'name': self._upload_filename,
                'parents': [self._upload_directory_id]
            }
            
            # 파일 업로드
            media = MediaFileUpload(
                file_path,
                resumable=True
            )
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, size, mimeType'
            ).execute()
            
            # anyoneWithLink 권한 부여 제거 (서비스 어카운트 인증만 사용)
            # 업로드 후 권한 부여 코드 삭제
            
            return {
                'id': file.get('id'),
                'name': file.get('name'),
                'size': file.get('size'),
                'mimeType': file.get('mimeType')
            }
        
        except Exception as e:
            raise Exception(f"Failed to upload file: {str(e)}")