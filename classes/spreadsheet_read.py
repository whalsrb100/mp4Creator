from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import Optional, Dict, List
from classes.settings import Settings
from classes.spreadsheet import SpreadsheetUpdate

class SpreadsheetRead:
    def __init__(self):
        """구글 스프레드시트 읽기 클래스"""
        self._settings = Settings()
        self._service_account_key_path: str = self._settings.service_account_key_path
        self._spreadsheet_id: str = self._settings.google_drive_settings.get('script_spreadsheet_id', '')
        self._sheet_name: Optional[str] = self._settings.google_drive_settings.get('script_spreadsheet_sheet_name', 'Sheet1')
        self._service = None
        self._headers: List[str] = []
    
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
    def spreadsheet_id(self) -> str:
        """스프레드시트 ID를 반환"""
        return self._spreadsheet_id
    
    @spreadsheet_id.setter
    def spreadsheet_id(self, value: str) -> None:
        """스프레드시트 ID를 설정"""
        self._spreadsheet_id = value
        # Settings에도 저장
        self._settings.image_spreadsheet_id = value
    
    @property
    def sheet_name(self) -> Optional[str]:
        """시트 이름을 반환"""
        return self._sheet_name
    
    @sheet_name.setter
    def sheet_name(self, value: Optional[str]) -> None:
        """시트 이름을 설정"""
        self._sheet_name = value
    
    @property
    def headers(self) -> List[str]:
        """스프레드시트의 필드명(헤더)을 반환"""
        return self._headers
    
    def _get_service(self):
        """구글 스프레드시트 서비스 객체를 생성"""
        if not self._service:
            credentials = service_account.Credentials.from_service_account_file(
                self._service_account_key_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            self._service = build('sheets', 'v4', credentials=credentials)
        return self._service
    
    def _get_sheet_name(self) -> str:
        """
        실제 사용할 시트 이름을 반환
        
        Returns:
            str: 시트 이름. sheet_name이 None이면 첫 번째 시트의 이름을 반환
        """
        if self._sheet_name:
            return self._sheet_name
        
        service = self._get_service()
        spreadsheet = service.spreadsheets().get(spreadsheetId=self._spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        
        if not sheets:
            raise Exception("No sheets found in the spreadsheet")
        
        return sheets[0]['properties']['title']
    
    def read(self) -> List[Dict]:
        """
        스프레드시트에서 데이터를 읽어옴
        
        Returns:
            List[Dict]: 필드명을 키로 하는 딕셔너리 리스트
            
        Raises:
            ValueError: 필수 설정이 누락된 경우
            Exception: 데이터 읽기 실패 시
        """
        # 필수 설정 확인
        if not self._service_account_key_path:
            raise ValueError("Service account key path is not set")
        if not self._spreadsheet_id:
            raise ValueError("Spreadsheet ID is not set")
        
        try:
            service = self._get_service()
            sheet_name = self._get_sheet_name() if self._sheet_name else 'Sheet1'
            safe_sheet_name = f"'{sheet_name}'"
            # 데이터 범위 설정 (A1:B, 시트명은 항상 작은따옴표로 감쌈)
            range_name = f"{safe_sheet_name}!A1:B"
            try:
                # 데이터 읽기 시도
                result = service.spreadsheets().values().get(
                    spreadsheetId=self._spreadsheet_id,
                    range=range_name
                ).execute()
                print('DEBUG raw values:', result.get('values', []))
            except Exception as e:
                # 시트가 없으면 자동 생성 (헤더는 ['ID', '대본']로 고정)
                if 'Unable to parse range' in str(e) or 'not found' in str(e):
                    updater = SpreadsheetUpdate()
                    updater.spreadsheet_id = self._spreadsheet_id
                    updater.sheet_name = sheet_name
                    updater._ensure_sheet_and_headers(sheet_name, headers=['ID', '대본'])
                    # 생성 후 재시도
                    result = service.spreadsheets().values().get(
                        spreadsheetId=self._spreadsheet_id,
                        range=range_name
                    ).execute()
                    print('DEBUG raw values (after create):', result.get('values', []))
                else:
                    raise
            values = result.get('values', [])
            
            if not values:
                return []
            
            # 헤더(필드명) 저장
            self._headers = values[0]
            
            # 데이터 행을 딕셔너리로 변환
            data = []
            for row in values[1:]:
                # 행의 길이가 헤더보다 짧을 경우 빈 문자열로 채움
                row_data = row + [''] * (len(self._headers) - len(row))
                data.append(dict(zip(self._headers, row_data)))
            
            return data
            
        except Exception as e:
            raise Exception(f"Failed to read spreadsheet: {str(e)}")