"""应用设置持久化：记住上次目录、音量、评分类型、参考文件夹等。"""

from PySide6.QtCore import QSettings

_ORG = "AudioScorer"
_APP = "MOS-SMOS-Scorer"


class Settings:
    def __init__(self):
        self._s = QSettings(_ORG, _APP)

    # ---- 上次目录 ----
    def last_dir(self) -> str:
        return self._s.value("last_dir", "", str)

    def set_last_dir(self, path: str):
        self._s.setValue("last_dir", path)

    # ---- 音量 (0-100) ----
    def volume(self) -> int:
        return self._s.value("volume", 100, int)

    def set_volume(self, v: int):
        self._s.setValue("volume", max(0, min(100, int(v))))

    # ---- 评分类型 ----
    def score_type(self) -> str:
        return self._s.value("score_type", "MOS", str)

    def set_score_type(self, key: str):
        self._s.setValue("score_type", key)

    # ---- 参考文件夹 ----
    def reference(self) -> str:
        return self._s.value("reference", "", str)

    def set_reference(self, name: str):
        self._s.setValue("reference", name)

    # ---- 盲测 ----
    def blind(self) -> bool:
        return self._s.value("blind", False, bool)

    def set_blind(self, b: bool):
        self._s.setValue("blind", b)

    # ---- 窗口几何 ----
    def geometry(self):
        return self._s.value("geometry", None)

    def set_geometry(self, geo):
        self._s.setValue("geometry", geo)


# 全局单例
_settings: Settings = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
