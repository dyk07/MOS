"""音频播放器：基于 pygame，支持音量调节。"""

import os
import threading
from typing import Optional

import pygame


class AudioPlayer:
    def __init__(self):
        self._lock = threading.Lock()
        self._init = False
        self._volume = 1.0
        self._current: Optional[str] = None
        self._playing = False

    def _ensure_init(self):
        if self._init:
            return
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        pygame.mixer.music.set_volume(self._volume)
        self._init = True

    def set_volume(self, v: float):
        self._volume = max(0.0, min(1.0, float(v)))
        if self._init:
            pygame.mixer.music.set_volume(self._volume)

    def volume(self) -> float:
        return self._volume

    def play(self, path: str) -> bool:
        if not path or not os.path.isfile(path):
            return False
        with self._lock:
            try:
                self._ensure_init()
                pygame.mixer.music.stop()
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
                self._current = path
                self._playing = True
                return True
            except pygame.error:
                self._playing = False
                return False

    def stop(self):
        if not self._init:
            return
        with self._lock:
            try:
                pygame.mixer.music.stop()
            except pygame.error:
                pass
            self._playing = False

    def pause(self):
        if not self._init:
            return
        with self._lock:
            try:
                pygame.mixer.music.pause()
                self._playing = False
            except pygame.error:
                pass

    def unpause(self):
        if not self._init:
            return
        with self._lock:
            try:
                pygame.mixer.music.unpause()
                self._playing = True
            except pygame.error:
                pass

    def is_playing(self) -> bool:
        if not self._init:
            return False
        try:
            return bool(pygame.mixer.music.get_busy())
        except pygame.error:
            return False

    def toggle(self):
        if self.is_playing():
            self.pause()
        else:
            self.unpause()

    def quit(self):
        if self._init:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except pygame.error:
                pass
            self._init = False


# 全局单例
_player: Optional[AudioPlayer] = None


def get_player() -> AudioPlayer:
    global _player
    if _player is None:
        _player = AudioPlayer()
    return _player
