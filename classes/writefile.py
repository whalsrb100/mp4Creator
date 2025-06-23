import json
import yaml
from pathlib import Path
from typing import Union, Dict, Any

class WriteFile:
    def __init__(self, data: Union[Dict[str, Any], list], file_type: str, file_path: str):
        """
        데이터를 파일로 저장하는 클래스
        
        Args:
            data (Union[Dict[str, Any], list]): 저장할 데이터
            file_type (str): 저장할 파일 타입 ('json' 또는 'yaml')
            file_path (str): 저장할 파일의 경로
        """
        self.data = data
        self.file_type = file_type.lower()
        self.file_path = Path(file_path)
        
        if self.file_type not in ['json', 'yaml']:
            raise ValueError("file_type must be either 'json' or 'yaml'")
    
    def write(self) -> None:
        """
        데이터를 지정된 형식으로 파일에 저장
        """
        try:
            # 디렉토리가 없으면 생성
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                if self.file_type == 'json':
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
                else:  # yaml
                    yaml.dump(self.data, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            raise Exception(f"Error writing file: {str(e)}") 