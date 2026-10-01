"""
코퍼스 — 작품이 고르는 소리 조각들.

조각 하나는 wav 파일 하나다. 조각마다 라벨이 붙는다. 에이전트는 이 라벨을 보고 고른다.

  partial  이 소리가 기본음의 몇 배인지 (1, 2, 3, 4, 5, 6, 8, 9 ...)
  bright   밝기. 높은 배음일수록 크다
  seconds  길이

기본 코퍼스는 처음 실행할 때 저절로 만들어진다. 기본음 하나의 배음들이라 아무렇게나
겹쳐도 어울린다. 소리가 심심한 것이 정상이다. 자기 녹음으로 바꾸는 것이 다음 단계이고,
그건 make_corpus.py 가 한다.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

from . import settings

SR = settings.SAMPLE_RATE
DEFAULT_PARTIALS = settings.DEFAULT_PARTIALS
DEFAULT_BASE_HZ = settings.BASE_HZ


@dataclass
class Slice:
    """코퍼스의 조각 하나."""

    id: str
    file: str
    partial: int
    bright: float
    seconds: float

    def load(self, root: Path) -> np.ndarray:
        import soundfile as sf

        data, sr = sf.read(root / self.file, dtype="float32", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)
        if sr != SR:
            # 길이만 맞춘다. 음높이가 조금 변하지만 베이스라인에서는 충분하다.
            idx = np.linspace(0, len(data) - 1, int(len(data) * SR / sr))
            data = np.interp(idx, np.arange(len(data)), data).astype("float32")
        return data


class Corpus:
    def __init__(self, root: Path):
        self.root = Path(root)
        meta = json.loads((self.root / "slices.json").read_text(encoding="utf-8"))
        self.name: str = meta.get("name", self.root.name)
        self.slices: list[Slice] = [Slice(**s) for s in meta["slices"]]
        self._cache: dict[str, np.ndarray] = {}

    def samples(self, slice_: Slice) -> np.ndarray:
        if slice_.id not in self._cache:
            self._cache[slice_.id] = slice_.load(self.root)
        return self._cache[slice_.id]

    def __len__(self) -> int:
        return len(self.slices)


def make_default_corpus(root: Path, base_hz: float = DEFAULT_BASE_HZ,
                        seconds: float = settings.DEFAULT_SLICE_SECONDS) -> Corpus:
    """배음으로 만든 기본 코퍼스를 wav 로 적는다. 이미 있으면 그대로 쓴다."""
    import soundfile as sf

    root = Path(root)
    if (root / "slices.json").exists():
        return Corpus(root)

    root.mkdir(parents=True, exist_ok=True)
    t = np.arange(int(SR * seconds), dtype=np.float32) / SR
    slices: list[Slice] = []
    for n in DEFAULT_PARTIALS:
        freq = base_hz * n
        # 아주 조금 어긋난 두 음을 겹쳐 두께를 준다. 완전히 같은 두 음은 기계처럼 들린다.
        wave = np.sin(2 * math.pi * freq * t) + 0.7 * np.sin(2 * math.pi * freq * 1.003 * t)
        wave += 0.25 * np.sin(2 * math.pi * freq * 2 * t)
        wave *= np.exp(-t / (seconds * 0.6))  # 천천히 사그라든다
        wave = (wave / np.max(np.abs(wave)) * 0.6).astype(np.float32)
        name = f"partial-{n:02d}.wav"
        sf.write(root / name, wave, SR)
        slices.append(
            Slice(id=f"p{n:02d}", file=name, partial=n, bright=float(n), seconds=seconds)
        )

    (root / "slices.json").write_text(
        json.dumps(
            {"name": "기본 배음", "base_hz": base_hz, "slices": [asdict(s) for s in slices]},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return Corpus(root)


def load_corpus(root: Path) -> Corpus:
    root = Path(root)
    if not (root / "slices.json").exists():
        return make_default_corpus(root)
    return Corpus(root)


def dominant_hz(x: np.ndarray, sr: int) -> float:
    """조각에서 가장 두드러진 주파수. 조각이 기본음의 몇 배인지 재는 데 쓴다."""
    window = x[: sr * 2] * np.hanning(min(len(x), sr * 2))
    spec = np.abs(np.fft.rfft(window))
    freqs = np.fft.rfftfreq(len(window), 1 / sr)
    band = (freqs > 50) & (freqs < 2000)
    if not band.any():
        return 0.0
    return float(freqs[band][int(np.argmax(spec[band]))])


def build_corpus_from_audio(
    sources: list[Path],
    out: Path,
    name: str,
    seconds: float = 6.0,
    hop: float = 3.0,
    base_hz: float = DEFAULT_BASE_HZ,
) -> Corpus:
    """녹음 파일을 조각으로 잘라 코퍼스로 만든다. 조용한 구간은 버린다."""
    import soundfile as sf

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    slices: list[Slice] = []
    index = 0

    for source in sources:
        data, sr = sf.read(source, dtype="float32", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)
        step = int(hop * sr)
        length = int(seconds * sr)
        fade = max(int(0.05 * sr), 1)
        env = np.ones(length, dtype=np.float32)
        env[:fade] = np.linspace(0, 1, fade)
        env[-fade * 4 :] = np.linspace(1, 0, fade * 4)

        for start in range(0, max(len(data) - length, 1), step):
            chunk = data[start : start + length]
            if len(chunk) < length:
                break
            peak = float(np.max(np.abs(chunk)))
            if peak < 0.01:  # 조용한 구간은 버린다
                continue
            chunk = (chunk / peak * 0.7 * env).astype(np.float32)
            hz = dominant_hz(chunk, sr)
            file_name = f"slice-{index:03d}.wav"
            sf.write(out / file_name, chunk, sr)
            slices.append(
                Slice(
                    id=f"s{index:03d}",
                    file=file_name,
                    partial=max(1, int(round(hz / base_hz))) if hz else 1,
                    bright=round(hz / base_hz, 2) if hz else 1.0,
                    seconds=seconds,
                )
            )
            index += 1

    if not slices:
        raise SystemExit("조각을 하나도 만들지 못했습니다. 더 긴 녹음이나 더 짧은 --seconds 로 해 보세요.")

    (out / "slices.json").write_text(
        json.dumps(
            {"name": name, "base_hz": base_hz, "slices": [asdict(s) for s in slices]},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return Corpus(out)
