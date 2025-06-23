import json
import yaml
from pathlib import Path
from typing import Union, Dict, Any

class ReadFile:
    def __init__(self, file_path: str, file_type: str):
        """
        파일을 읽어서 JSON 형식으로 반환하는 클래스
        
        Args:
            file_path (str): 읽을 파일의 경로
            file_type (str): 파일 타입 ('json' 또는 'yaml')
        """
        self.file_path = Path(file_path)
        self.file_type = file_type.lower()
        
        if self.file_type not in ['json', 'yaml']:
            raise ValueError("file_type must be either 'json' or 'yaml'")
    
    def read(self) -> Dict[str, Any]:
        """
        파일을 읽어서 JSON 형식으로 반환
        
        Returns:
            Dict[str, Any]: 파일 내용을 딕셔너리 형태로 반환
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                if self.file_type == 'json':
                    return json.load(f)
                else:  # yaml
                    return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}") 