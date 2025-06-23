import httpx
from typing import Dict, List, Any, Optional
from classes.settings import Settings

class GiphySearch:
    def __init__(self):
        """Giphy API를 사용하여 이미지를 검색하는 클래스"""
        self._settings = Settings()
        self._search_query: str = ""
        self._limit: int = 10
        self._api_key: str = self._settings.giphy_api_key
    
    @property
    def search_query(self) -> str:
        """검색어를 반환"""
        return self._search_query
    
    @search_query.setter
    def search_query(self, value: str) -> None:
        """검색어를 설정"""
        self._search_query = value
    
    @property
    def limit(self) -> int:
        """검색할 이미지 개수를 반환"""
        return self._limit
    
    @limit.setter
    def limit(self, value: int) -> None:
        """검색할 이미지 개수를 설정"""
        if value < 1:
            raise ValueError("Limit must be greater than 0")
        self._limit = value
    
    @property
    def api_key(self) -> str:
        """Giphy API 키를 반환"""
        return self._api_key
    
    @api_key.setter
    def api_key(self, value: str) -> None:
        """Giphy API 키를 설정"""
        self._api_key = value
        # Settings에도 저장
        self._settings.giphy_api_key = value
    
    def search(self) -> List[Dict[str, Any]]:
        """
        Giphy API를 사용하여 이미지를 검색
        
        Returns:
            List[Dict[str, Any]]: 검색된 이미지 정보 리스트
            
        Raises:
            ValueError: 필수 설정이 누락된 경우
            Exception: API 호출 실패 시
        """
        # 필수 설정 확인
        if not self._search_query:
            raise ValueError("Search query is not set")
        if not self._api_key:
            raise ValueError("API key is not set")
        
        try:
            # Giphy API 호출
            url = "https://api.giphy.com/v1/gifs/search"
            params = {
                "api_key": self._api_key,
                "q": self._search_query,
                "limit": self._limit,
                "rating": "g",
                "lang": "ko"
            }
            
            with httpx.Client() as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # 결과 정리
                results = []
                for gif in data["data"]:
                    results.append({
                        "id": gif["id"],
                        "title": gif["title"],
                        "url": gif["images"]["original"]["url"],
                        "width": gif["images"]["original"]["width"],
                        "height": gif["images"]["original"]["height"],
                        "size": gif["images"]["original"]["size"]
                    })
                
                return results
                
        except Exception as e:
            raise Exception(f"Failed to search Giphy: {str(e)}") 