"""
작품 하나를 들고 있는 자리. 감지·에이전트·소리를 이어 붙인다.

걸음 하나가 들어오면 하는 일은 세 줄이다.
  1. 지금 울리고 있는 소리를 본다
  2. 에이전트에게 다음 조각을 묻는다
  3. 그 조각을 그 사람의 자리(좌우)에서 울린다
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from .agent import Choice, make_agent
from .audio import Mixer, Params
from .corpus import Corpus, load_corpus
from . import settings
from .vision import VisionStatus


@dataclass
class TrackState:
    track: int
    x: float = 0.5
    steps: int = 0
    last_slice: str = ""
    since: float = field(default_factory=time.time)


class Piece:
    def __init__(self, corpus_dir: Path, engine: str = "rule"):
        self.corpus: Corpus = load_corpus(corpus_dir)
        self.params = Params()
        self.mixer = Mixer(self.params)
        self.agent = make_agent(engine, self.corpus)
        self.engine = engine
        self.tracks: dict[int, TrackState] = {}
        self.log: deque[dict] = deque(maxlen=settings.LOG_LINES)
        self.vision = VisionStatus()
        self.started_at = time.time()
        self.total_steps = 0
        self.running = True

    # 감지에서 들어오는 자리
    def on_event(self, kind: str, track: int, x: float) -> None:
        if kind == "enter":
            self.tracks[track] = TrackState(track, x)
            self._note(f"{track}번이 들어왔다")
        elif kind == "move":
            if track in self.tracks:
                self.tracks[track].x = x
        elif kind == "leave":
            self.tracks.pop(track, None)
            self.mixer.release_track(track)
            self._note(f"{track}번이 나갔다")
        elif kind == "step" and self.running:
            self._step(track, x)

    def _step(self, track: int, x: float) -> None:
        state = self.tracks.get(track)
        if state is None:
            state = self.tracks.setdefault(track, TrackState(track, x))
        state.x = x
        state.steps += 1
        self.total_steps += 1

        sounding = self._sounding_partials()
        choice: Choice = self.agent.choose(sounding, track_seed=track)
        samples = self.corpus.samples(choice.slice_)
        use = int(min(len(samples), self.params.note_seconds * settings.SAMPLE_RATE))
        gain = settings.LAYER_GAIN if sounding else settings.FIRST_GAIN  # 겹칠수록 한 겹의 몫을 줄인다
        self.mixer.add(choice.slice_.id, samples[:use], pan=x, gain=gain, track=track)
        state.last_slice = choice.slice_.id
        self._note(f"{track}번 걸음 → {choice.slice_.id} ({choice.why})")

    def _sounding_partials(self) -> list[int]:
        ids = {v.slice_id for v in list(self.mixer.voices)}
        return [s.partial for s in self.corpus.slices if s.id in ids]

    def _note(self, text: str) -> None:
        self.log.appendleft({"t": time.strftime("%H:%M:%S"), "text": text})

    # 대시보드가 읽는 자리
    def snapshot(self) -> dict:
        return {
            "running": self.running,
            "engine": self.engine,
            "engine_note": getattr(self.agent, "note", ""),
            "corpus": {"name": self.corpus.name, "slices": len(self.corpus)},
            "people": len(self.tracks),
            "tracks": [
                {"track": t.track, "x": round(t.x, 3), "steps": t.steps, "slice": t.last_slice}
                for t in sorted(self.tracks.values(), key=lambda s: s.track)
            ],
            "voices": self.mixer.count(),
            "sounding": self.mixer.sounding_now(),
            "peak": round(self.mixer.peak, 3),
            "steps": self.total_steps,
            "uptime": int(time.time() - self.started_at),
            "vision": {
                "source": self.vision.source,
                "note": self.vision.note,
                "fps": round(self.vision.fps, 1),
                "camera": self.vision.source in ("웹캠", "영상 파일"),
            },
            "params": {
                "volume": self.params.volume,
                "note_seconds": self.params.note_seconds,
                "max_voices": self.params.max_voices,
                "fade_seconds": self.params.fade_seconds,
            },
            "log": list(self.log)[:20],
        }

    def set_params(self, data: dict) -> None:
        for key in ("volume", "note_seconds", "fade_seconds"):
            if key in data:
                setattr(self.params, key, float(data[key]))
        if "max_voices" in data:
            self.params.max_voices = int(data["max_voices"])
        if "running" in data:
            self.running = bool(data["running"])
            self._note("소리를 켰다" if self.running else "소리를 멈췄다")
