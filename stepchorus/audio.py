"""
소리 — 코퍼스 조각을 겹쳐 내보낸다.

걸음 한 번에 긴 소리 하나가 피어오르고 천천히 사라진다. 그래서 연주가 되지 않는다.
빨리 걷는다고 빠른 선율이 나오지 않고, 사람이 늘면 층이 두꺼워질 뿐이다.

재생 장치가 없거나 --offline 으로 돌리면 스피커 대신 wav 파일로 적는다.
전시장 장비 없이도 결과를 들어 볼 수 있다.
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field

import numpy as np

from . import settings

SR = settings.SAMPLE_RATE
BLOCK = settings.BLOCK


@dataclass
class Voice:
    """지금 울리고 있는 소리 하나."""

    slice_id: str
    samples: np.ndarray
    pan: float  # 0 왼쪽, 1 오른쪽
    gain: float
    pos: int = 0
    releasing: bool = False
    rel_gain: float = 1.0
    track: int = -1

    def done(self) -> bool:
        return self.pos >= len(self.samples) or self.rel_gain < 1e-4


@dataclass
class Params:
    """대시보드에서 바꾸는 값들."""

    volume: float = settings.VOLUME
    note_seconds: float = settings.NOTE_SECONDS
    max_voices: int = settings.MAX_VOICES
    fade_seconds: float = settings.FADE_SECONDS


class Mixer:
    def __init__(self, params: Params):
        self.params = params
        self.voices: list[Voice] = []
        self.lock = threading.Lock()
        self.peak = 0.0
        # 브라우저로 보낼 소리를 잠깐 쟁여 두는 자리. 듣는 사람이 없으면 쌓지 않는다.
        self.tap_on = False
        self.tap: deque[bytes] = deque(maxlen=120)

    def add(self, slice_id: str, samples: np.ndarray, pan: float, gain: float, track: int) -> None:
        with self.lock:
            # 겹을 넘기면 오래된 것부터 놓아 준다. 그래도 넘치면 잘라 낸다.
            while len(self.voices) >= self.params.max_voices:
                oldest = max(self.voices, key=lambda v: v.pos)
                if oldest.releasing:
                    self.voices.remove(oldest)
                else:
                    oldest.releasing = True
                    if len([v for v in self.voices if not v.releasing]) < self.params.max_voices:
                        break
            self.voices.append(Voice(slice_id, samples, pan, gain, track=track))

    def release_track(self, track: int) -> None:
        """사람이 나가면 그 사람의 소리를 천천히 거둔다."""
        with self.lock:
            for v in self.voices:
                if v.track == track:
                    v.releasing = True

    def render(self, frames: int) -> np.ndarray:
        out = np.zeros((frames, 2), dtype=np.float32)
        rel_coef = float(np.exp(-frames / (SR * max(self.params.fade_seconds, 0.05))))
        with self.lock:
            for v in list(self.voices):
                chunk = v.samples[v.pos : v.pos + frames]
                if len(chunk) < frames:
                    chunk = np.pad(chunk, (0, frames - len(chunk)))
                v.pos += frames
                if v.releasing:
                    v.rel_gain *= rel_coef
                g = v.gain * v.rel_gain * self.params.volume
                left = g * (1.0 - v.pan) ** 0.5
                right = g * v.pan**0.5
                out[:, 0] += chunk * left
                out[:, 1] += chunk * right
                if v.done():
                    self.voices.remove(v)
        # 층이 많이 겹쳤을 때 찌그러지지 않게 부드럽게 누른다.
        out = np.tanh(out * 1.2) * 0.9
        self.peak = float(np.max(np.abs(out))) if frames else 0.0
        if self.tap_on and frames:
            # 16비트로 줄여 보낸다. 대역폭이 줄고 브라우저가 그대로 받는다.
            self.tap.append((out * 32767).astype(np.int16).tobytes())
        return out

    def take_tap(self) -> bytes:
        """쟁여 둔 소리를 꺼내 준다. 브라우저가 0.1초마다 가져간다."""
        chunks = []
        while self.tap:
            chunks.append(self.tap.popleft())
        return b"".join(chunks)

    def count(self) -> int:
        with self.lock:
            return len(self.voices)

    def sounding_now(self) -> list[dict]:
        """대시보드가 보여 줄 「지금 울리는 소리」. 남은 길이를 0~1 로 준다."""
        with self.lock:
            rows = []
            for v in self.voices:
                total = max(len(v.samples), 1)
                rows.append(
                    {
                        "slice": v.slice_id,
                        "track": v.track,
                        "pan": round(v.pan, 3),
                        "left": round(max(0.0, 1 - v.pos / total), 3),
                        "fading": v.releasing,
                    }
                )
            return sorted(rows, key=lambda r: (-r["left"], r["slice"]))


class Speaker:
    """sounddevice 로 소리를 낸다. 장치가 없으면 조용히 실패하고 무음으로 돈다."""

    def __init__(self, mixer: Mixer):
        self.mixer = mixer
        self.stream = None
        self.error: str | None = None

    def start(self) -> None:
        try:
            import sounddevice as sd
        except Exception as exc:  # 드라이버 없음, 설치 안 됨
            self.error = f"{exc}"
            return

        def callback(outdata, frames, time_info, status):  # noqa: ANN001
            outdata[:] = self.mixer.render(frames)

        try:
            self.stream = sd.OutputStream(
                samplerate=SR, channels=2, blocksize=BLOCK, dtype="float32", callback=callback
            )
            self.stream.start()
        except Exception as exc:
            self.error = f"{exc}"
            self.stream = None

    def stop(self) -> None:
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None


class Recorder:
    """스피커 대신 wav 로 적는다. --offline 에서 쓴다."""

    def __init__(self, mixer: Mixer):
        self.mixer = mixer
        self.blocks: list[np.ndarray] = []

    def tick(self, frames: int = BLOCK) -> None:
        self.blocks.append(self.mixer.render(frames))

    def save(self, path: str) -> float:
        import soundfile as sf

        if not self.blocks:
            return 0.0
        data = np.concatenate(self.blocks, axis=0)
        sf.write(path, data, SR)
        return len(data) / SR
