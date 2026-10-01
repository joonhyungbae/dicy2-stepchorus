"""
에이전트 — 다음에 어떤 조각을 울릴지 고른다. 이 작품의 음악이 여기서 결정된다.

고르는 방식 두 가지가 들어 있다.

  rule    이 파일 안의 규칙. 지금 울리고 있는 소리와 어울리는 조각을 고른다.
  dicy2   IRCAM Dicy2 의 생성 엔진에게 묻는다. 코퍼스를 듣고 이어 갈 조각을 돌려준다.
          Dicy2 서버(dicy2_server.py)를 따로 띄워 두어야 한다. settings.json 에서 켠다.

규칙 쪽부터 읽는 것을 권한다. 무엇을 「어울린다」고 부를지 정하는 일이 곧 작곡이다.
숫자를 바꾸면 작품의 성격이 바뀐다.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from . import settings
from .corpus import Corpus, Slice


def consonance(a: int, b: int) -> float:
    """두 배음이 얼마나 잘 어울리는지. 1 에 가까울수록 어울린다.

    3 과 6 처럼 간단한 비율(1:2)이면 잘 섞이고, 8 과 9 처럼 가까운 수끼리는
    맥놀이가 생겨 거칠게 들린다. 사람 귀가 실제로 그렇게 듣는다.
    """
    if a == b:
        return 0.75  # 같은 음을 겹치면 두꺼워지지만 새로운 일이 생기지는 않는다
    g = math.gcd(a, b)
    ratio_complexity = (a // g) + (b // g)
    return 1.0 / (1.0 + 0.25 * (ratio_complexity - 2))


@dataclass
class Choice:
    slice_: Slice
    score: float
    why: str


@dataclass
class RuleAgent:
    """지금 울리는 소리와 어울리면서, 방금 쓴 것과는 다른 조각을 고른다."""

    corpus: Corpus
    weight_consonance: float = settings.WEIGHT_CONSONANCE
    weight_novelty: float = settings.WEIGHT_NOVELTY
    weight_register: float = settings.WEIGHT_REGISTER
    recent: list[str] = field(default_factory=list)

    def choose(self, sounding: list[int], track_seed: int) -> Choice:
        """sounding 은 지금 울리고 있는 조각들의 partial 목록."""
        best: Choice | None = None
        rnd = random.Random()
        for s in self.corpus.slices:
            if sounding:
                fit = sum(consonance(s.partial, p) for p in sounding) / len(sounding)
            else:
                fit = 0.6
            novelty = 0.0 if s.id in self.recent[-3:] else 1.0
            # 사람마다 음역을 다르게 둔다. 같은 자리에서 겹치면 서로를 가린다.
            want = (track_seed * 3) % max(len(self.corpus), 1)
            register = 1.0 - abs(self.corpus.slices.index(s) - want) / max(len(self.corpus), 1)
            score = (
                self.weight_consonance * fit
                + self.weight_novelty * novelty
                + self.weight_register * register
                + rnd.uniform(0, settings.RANDOM_SPREAD)
            )
            why = f"어울림 {fit:.2f} · 새로움 {novelty:.0f} · 음역 {register:.2f}"
            if best is None or score > best.score:
                best = Choice(s, score, why)
        assert best is not None
        self.recent.append(best.slice_.id)
        self.recent = self.recent[-8:]
        return best


class Dicy2Agent:
    """Dicy2 가 고른 것을 쓰고, 답이 늦으면 규칙으로 메운다.

    전시장에서 소리가 멎는 쪽이 더 나쁘기 때문에 기다리지 않는다. 미리 물어 두고,
    답이 와 있으면 그것을 쓰고, 없으면 규칙이 고른 것을 쓴다.
    서버 띄우는 법은 dicy2.py 의 맨 위에 적어 두었다.
    """

    def __init__(self, corpus: Corpus, **kwargs):
        from .dicy2 import Dicy2Link

        self.corpus = corpus
        self.by_id = {s.id: s for s in corpus.slices}
        self.link = Dicy2Link(corpus, **kwargs)
        self.fallback = RuleAgent(corpus)
        self.used = 0
        self.missed = 0

    @property
    def note(self) -> str:
        return f"{self.link.note} · 엔진이 고른 것 {self.used}회, 규칙으로 메운 것 {self.missed}회"

    def choose(self, sounding: list[int], track_seed: int) -> Choice:
        self.link.request(sounding)
        slice_id = self.link.take()
        if slice_id and slice_id in self.by_id:
            self.used += 1
            return Choice(self.by_id[slice_id], 1.0, "dicy2 가 고름")
        self.missed += 1
        choice = self.fallback.choose(sounding, track_seed)
        return Choice(choice.slice_, choice.score, f"규칙으로 메움 ({choice.why})")


def make_agent(kind: str, corpus: Corpus) -> RuleAgent | Dicy2Agent:
    if kind == "dicy2":
        return Dicy2Agent(corpus)
    return RuleAgent(corpus)
