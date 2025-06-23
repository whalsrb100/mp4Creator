from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import Optional, Dict, List
from classes.settings import Settings

class SpreadsheetUpdate:
    def __init__(self):
        """구글 스프레드시트 업데이트 클래스"""
        self._settings = Settings()
        self._service_account_key_path: str = self._settings.service_account_key_path
        self._spreadsheet_id: str = self._settings.google_drive_settings.get('script_spreadsheet_id', '')
        self._sheet_name: Optional[str] = self._settings.google_drive_settings.get('script_spreadsheet_sheet_name', 'Sheet1')
        self._giphy_url: str = ""
        self._google_url: str = ""
        self._search_query: str = ""
        self._filename: str = ""
        self._description: str = ""
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
    def giphy_url(self) -> str:
        """Giphy URL을 반환"""
        return self._giphy_url
    
    @giphy_url.setter
    def giphy_url(self, value: str) -> None:
        """Giphy URL을 설정"""
        self._giphy_url = value
    
    @property
    def google_url(self) -> str:
        """Google URL을 반환"""
        return self._google_url
    
    @google_url.setter
    def google_url(self, value: str) -> None:
        """Google URL을 설정"""
        self._google_url = value
    
    @property
    def search_query(self) -> str:
        """검색어를 반환"""
        return self._search_query
    
    @search_query.setter
    def search_query(self, value: str) -> None:
        """검색어를 설정"""
        self._search_query = value
    
    @property
    def filename(self) -> str:
        """파일명을 반환"""
        return self._filename
    
    @filename.setter
    def filename(self, value: str) -> None:
        """파일명을 설정"""
        self._filename = value
    
    @property
    def description(self) -> str:
        """이미지 설명을 반환"""
        return self._description
    
    @description.setter
    def description(self, value: str) -> None:
        """이미지 설명을 설정"""
        self._description = value
    
    def _get_service(self):
        """구글 스프레드시트 서비스 객체를 생성"""
        if not self._service:
            credentials = service_account.Credentials.from_service_account_file(
                self._service_account_key_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self._service = build('sheets', 'v4', credentials=credentials)
        return self._service
    
    def _get_sheet_id(self, sheet_name: Optional[str] = None) -> int:
        """
        시트 ID를 가져옴
        
        Args:
            sheet_name (Optional[str]): 시트 이름. None이면 첫 번째 시트 사용
            
        Returns:
            int: 시트 ID
            
        Raises:
            Exception: 시트를 찾을 수 없는 경우
        """
        service = self._get_service()
        spreadsheet = service.spreadsheets().get(spreadsheetId=self._spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        
        if not sheet_name:
            # 첫 번째 시트 사용
            return sheets[0]['properties']['sheetId']
        
        # 지정된 이름의 시트 찾기
        for sheet in sheets:
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
        
        # 시트가 없으면 새로 생성
        request = {
            'addSheet': {
                'properties': {
                    'title': sheet_name
                }
            }
        }
        
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=self._spreadsheet_id,
            body={'requests': [request]}
        ).execute()
        
        return response['replies'][0]['addSheet']['properties']['sheetId']
    
    def _ensure_headers(self, sheet_name: Optional[str] = None):
        """
        시트에 헤더가 없으면 추가
        
        Args:
            sheet_name (Optional[str]): 시트 이름
        """
        service = self._get_service()
        range_name = f"{sheet_name or 'Sheet1'}!A1:E1"
        
        # 현재 데이터 확인
        result = service.spreadsheets().values().get(
            spreadsheetId=self._spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        # 헤더가 없으면 추가
        if not values:
            headers = ['Giphy URL', 'Google URL', '검색어', '파일명', '설명']
            body = {
                'values': [headers]
            }
            service.spreadsheets().values().update(
                spreadsheetId=self._spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
    
    def _ensure_sheet_and_headers(self, sheet_name: str, headers: list = None):
        """
        시트가 없으면 생성하고, 첫째 줄에 헤더가 없으면 추가
        headers: 추가할 헤더 리스트 (없으면 기존 방식)
        """
        service = self._get_service()
        spreadsheet = service.spreadsheets().get(spreadsheetId=self._spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        sheet_titles = [sheet['properties']['title'] for sheet in sheets]
        # 시트가 없으면 생성
        if sheet_name not in sheet_titles:
            request = {
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }
            service.spreadsheets().batchUpdate(
                spreadsheetId=self._spreadsheet_id,
                body={'requests': [request]}
            ).execute()
        # 헤더 확인 및 추가/수정
        if headers is None:
            if any(x in sheet_name.lower() for x in ['script', '스크립트', '대본']):
                headers = ['ID', '대본']
            else:
                headers = ['Giphy URL', 'Google URL', '검색어', '파일명', '설명']
        col_end = chr(ord('A') + len(headers) - 1)
        range_name = f"{sheet_name}!A1:{col_end}1"
        result = service.spreadsheets().values().get(
            spreadsheetId=self._spreadsheet_id,
            range=range_name
        ).execute()
        values = result.get('values', [])
        # 헤더가 없거나, 기존 헤더가 다르면 강제로 업데이트
        if not values or values[0] != headers:
            body = {
                'values': [headers]
            }
            service.spreadsheets().values().update(
                spreadsheetId=self._spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
    
    def update(self) -> Dict:
        """
        스프레드시트에 데이터 추가
        
        Returns:
            Dict: 업데이트 결과
            
        Raises:
            ValueError: 필수 설정이 누락된 경우
            Exception: 업데이트 실패 시
        """
        # 필수 설정 확인
        if not self._service_account_key_path:
            raise ValueError("Service account key path is not set")
        if not self._spreadsheet_id:
            raise ValueError("Spreadsheet ID is not set")
        if not self._giphy_url:
            raise ValueError("Giphy URL is not set")
        if not self._google_url:
            raise ValueError("Google URL is not set")
        if not self._search_query:
            raise ValueError("Search query is not set")
        if not self._filename:
            raise ValueError("Filename is not set")
        
        try:
            service = self._get_service()
            # 시트명 설정: 설정에서 불러오도록
            sheet_name = self._sheet_name or self._settings.image_spreadsheet_sheet_name
            # 시트 및 헤더 보장
            self._ensure_sheet_and_headers(sheet_name)
            # 시트 ID 가져오기
            sheet_id = self._get_sheet_id(sheet_name)
            # 데이터 추가
            range_name = f"{sheet_name}!A:E"
            values = [[
                self._giphy_url,
                self._google_url,
                self._search_query,
                self._filename,
                self._description
            ]]
            body = {
                'values': values
            }
            result = service.spreadsheets().values().append(
                spreadsheetId=self._spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            return {
                'updatedRange': result.get('updates', {}).get('updatedRange'),
                'updatedRows': result.get('updates', {}).get('updatedRows'),
                'updatedColumns': result.get('updates', {}).get('updatedColumns'),
                'updatedCells': result.get('updates', {}).get('updatedCells')
            }
        except Exception as e:
            raise Exception(f"Failed to update spreadsheet: {str(e)}")
    
    def overwrite(self):
        """
        self.headers와 self.data를 사용해 시트 전체를 덮어씀 (대본 등 임의 구조용)
        """
        if not self._service_account_key_path:
            raise ValueError("Service account key path is not set")
        if not self._spreadsheet_id:
            raise ValueError("Spreadsheet ID is not set")
        if not hasattr(self, 'headers') or not hasattr(self, 'data'):
            raise ValueError("headers와 data 속성이 필요합니다.")
        service = self._get_service()
        sheet_name = self._sheet_name or 'Sheet1'
        # 시트 및 헤더 보장
        self._ensure_sheet_and_headers(sheet_name)
        # 시트 전체 데이터 clear (기존 데이터 완전 삭제)
        clear_range = f"'{sheet_name}'"
        service.spreadsheets().values().clear(
            spreadsheetId=self._spreadsheet_id,
            range=clear_range,
            body={}
        ).execute()
        # 전체 데이터 준비 (headers와 data의 컬럼 수를 항상 맞춤)
        values = [self.headers] + [[row.get(h, '') for h in self.headers] for row in self.data]
        row_count = len(values)
        col_count = len(self.headers)
        col_end = chr(ord('A') + col_count - 1)
        range_name = f"'{sheet_name}'!A1:{col_end}{row_count}"
        body = {'values': values}
        result = service.spreadsheets().values().update(
            spreadsheetId=self._spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        return result