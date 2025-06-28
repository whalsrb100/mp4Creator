from classes.readfile import ReadFile
from classes.writefile import WriteFile
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class Settings:
    _settings_file: str = "config/settings.json"
    _settings: Dict[str, Any] = None

    def __post_init__(self):
        """초기화 후 설정 로드"""
        self._settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """설정 파일에서 설정을 로드"""
        reader = ReadFile(self._settings_file, "json")
        return reader.read()

    def _save_settings(self) -> None:
        """설정을 파일에 저장"""
        writer = WriteFile(self._settings, "json", self._settings_file)
        writer.write()

    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """여러 설정을 한 번에 갱신 및 저장"""
        self._settings.update(new_settings)
        self._save_settings()

    @property
    def app_title(self) -> str:
        self._settings = self._load_settings()
        return self._settings.get("app_title", "")

    @app_title.setter
    def app_title(self, value: str) -> None:
        self._settings["app_title"] = value

    @property
    def theme(self) -> str:
        self._settings = self._load_settings()
        return self._settings.get("default_theme", "dark")

    @theme.setter
    def theme(self, value: str) -> None:
        self._settings["default_theme"] = value

    @property
    def giphy_settings(self) -> Dict[str, Any]:
        self._settings = self._load_settings()
        return self._settings.get("giphy_settings", {})

    @giphy_settings.setter
    def giphy_settings(self, value: Dict[str, Any]) -> None:
        self._settings["giphy_settings"] = value
        self._save_settings()

    @property
    def giphy_api_key(self) -> str:
        return self.giphy_settings.get("giphy_api_key", "")

    @giphy_api_key.setter
    def giphy_api_key(self, value: str) -> None:
        giphy = self.giphy_settings
        giphy["giphy_api_key"] = value
        self.giphy_settings = giphy

    @property
    def giphy_search_limit(self) -> int:
        return self.giphy_settings.get("search_limit", 10)

    @giphy_search_limit.setter
    def giphy_search_limit(self, value: int) -> None:
        giphy = self.giphy_settings
        giphy["search_limit"] = value
        self.giphy_settings = giphy

    @property
    def voice_settings(self) -> Dict[str, Any]:
        self._settings = self._load_settings()
        return self._settings.get("voice_settings", {})

    @voice_settings.setter
    def voice_settings(self, value: Dict[str, Any]) -> None:
        self._settings["voice_settings"] = value
        self._save_settings()

    @property
    def voice_speed(self) -> str:
        return self.voice_settings.get("default_speed", "+40%")

    @voice_speed.setter
    def voice_speed(self, value: str) -> None:
        self.voice_settings["default_speed"] = value

    @property
    def voice_type(self) -> str:
        return self.voice_settings.get("default_voice", "남자1")

    @voice_type.setter
    def voice_type(self, value: str) -> None:
        self.voice_settings["default_voice"] = value

    @property
    def voices_list(self) -> Dict[str, str]:
        self._settings = self._load_settings()
        return self._settings.get("voices_list", {})

    @voices_list.setter
    def voices_list(self, value: Dict[str, str]) -> None:
        self._settings["voices_list"] = value

    @property
    def google_drive_settings(self) -> Dict[str, Any]:
        self._settings = self._load_settings()
        # 기존 google_drive_settings 대신 google_settings 사용
        return self._settings.get("google_settings", {})

    @google_drive_settings.setter
    def google_drive_settings(self, value: Dict[str, Any]) -> None:
        self._settings["google_settings"] = value
        self._save_settings()

    @property
    def service_account_key_path(self) -> str:
        return self.google_drive_settings.get("service_account_key_path", "")

    @service_account_key_path.setter
    def service_account_key_path(self, value: str) -> None:
        self.google_drive_settings["service_account_key_path"] = value
    
    # Image Directory ID
    @property
    def image_directory_id(self) -> str:
        return self.google_drive_settings.get("image_directory_id", "")
    
    @image_directory_id.setter
    def image_directory_id(self, value: str) -> None:
        self.google_drive_settings["image_directory_id"] = value
    
    # Script Spreadsheet ID
    @property
    def script_spreadsheet_id(self) -> str:
        return self.google_drive_settings.get("script_spreadsheet_id", "")
    
    @script_spreadsheet_id.setter
    def script_spreadsheet_id(self, value: str) -> None:
        self.google_drive_settings["script_spreadsheet_id"] = value
    
    # Image Spreadsheet ID
    @property
    def image_spreadsheet_id(self) -> str:
        return self.google_drive_settings.get("image_spreadsheet_id", "")
    
    @image_spreadsheet_id.setter
    def image_spreadsheet_id(self, value: str) -> None:
        self.google_drive_settings["image_spreadsheet_id"] = value
    
    @property
    def image_spreadsheet_sheet_name(self) -> str:
        return self.google_drive_settings.get("image_sheet_name", "Sheet1")

    @image_spreadsheet_sheet_name.setter
    def image_spreadsheet_sheet_name(self, value: str) -> None:
        google_drive = self.google_drive_settings
        google_drive["image_sheet_name"] = value
        self.google_drive_settings = google_drive

    @property
    def script_spreadsheet_sheet_name(self) -> str:
        return self.google_drive_settings.get("script_sheet_name", "Sheet1")

    @script_spreadsheet_sheet_name.setter
    def script_spreadsheet_sheet_name(self, value: str) -> None:
        google_drive = self.google_drive_settings
        google_drive["script_sheet_name"] = value
        self.google_drive_settings = google_drive

    @property
    def themes_list(self) -> list:
        self._settings = self._load_settings()
        return self._settings.get("themes_list", ["dark", "light"])

    @themes_list.setter
    def themes_list(self, value: list) -> None:
        self._settings["themes_list"] = value

    @property
    def speed_list(self) -> list:
        self._settings = self._load_settings()
        return self._settings.get("speed_list", ["0%"])

    @speed_list.setter
    def speed_list(self, value: list) -> None:
        self._settings["speed_list"] = value