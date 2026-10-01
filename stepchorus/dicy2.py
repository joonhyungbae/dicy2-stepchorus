"""
Dicy2 — 코퍼스를 듣고 이어 갈 조각을 골라 주는 생성 엔진.

IRCAM 음악표상팀이 만든 것이고, Max 없이 파이썬 서버로 돈다. 우리 쪽은 OSC 로 말을 건다.
서버를 먼저 띄워야 한다.

    git clone --recurse-submodules https://github.com/DYCI2/Dicy2-python
    cd Dicy2-python && pip install maxosc python-osc
    python dicy2_server.py          # 받는 포트 4566, 보내는 포트 1233

규칙(agent.py) 과 무엇이 다른가. 규칙은 조각 하나하나를 점수로 고른다. Dicy2 는 코퍼스를
**순서가 있는 기록**으로 배운다. 그래서 「이 조각 다음에는 저 조각이 오곤 했다」를 쓴다.
녹음을 시간 순서대로 자른 코퍼스일수록 이쪽이 살아난다.

주고받는 말은 이렇다.

    보냄  /server create_agent /stepchorus listlabel
    보냄  /stepchorus learn_event listlabel P03 p03
    보냄  /stepchorus query q1 0 relative 4                      (자유 질의)
    보냄  /stepchorus query q1 0 relative None listlabel [ P03 P02 ]   (지금 울리는 소리에 맞춰 달라)
    받음  /stepchorus query_result_iterative q1 1 4 p06
"""

from __future__ import annotations

import threading
import time
from collections import deque

from . import settings
from .corpus import Corpus


class Dicy2Link:
    """Dicy2 서버와 주고받는 자리. 답은 큐에 쌓아 두고 필요할 때 꺼내 쓴다."""

    def __init__(
        self,
        corpus: Corpus,
        host: str = settings.DICY2_HOST,
        send_port: int = settings.DICY2_SEND_PORT,
        recv_port: int = settings.DICY2_RECV_PORT,
        agent: str = settings.DICY2_AGENT,
        max_continuity: int = settings.DICY2_MAX_CONTINUITY,
    ):
        self.corpus = corpus
        self.agent = agent
        self.max_continuity = max_continuity
        self.queue: deque[str] = deque(maxlen=16)
        self.ready = False
        self.note = "아직 붙지 않음"
        self._n = 0
        self._last_query = 0.0
        self._ids = {s.id for s in corpus.slices}

        try:
            from pythonosc.dispatcher import Dispatcher
            from pythonosc.osc_server import ThreadingOSCUDPServer
            from pythonosc.udp_client import SimpleUDPClient
        except Exception as exc:
            self.note = f"python-osc 가 없습니다 ({exc})"
            self.client = None
            return

        self.client = SimpleUDPClient(host, send_port)
        dispatcher = Dispatcher()
        dispatcher.set_default_handler(self._on_message)
        # 앞서 켠 것이 포트를 놓는 데 잠깐 걸린다. 몇 초 기다려 본다.
        self.server = None
        for _ in range(10):
            try:
                self.server = ThreadingOSCUDPServer(("127.0.0.1", recv_port), dispatcher)
                break
            except OSError:
                time.sleep(0.5)
        if self.server is None:
            self.note = f"받는 포트 {recv_port} 이 쓰이고 있습니다. 이전에 켠 것을 끄고 다시 켜세요."
            self.client = None
            return
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        threading.Thread(target=self._setup, daemon=True).start()

    # 서버에서 오는 말
    def _on_message(self, address: str, *args) -> None:  # noqa: ANN002
        if not args:
            return
        kind = args[0]
        if kind == "query_result_iterative" and len(args) >= 5:
            content = str(args[4])
            if content in self._ids:
                self.queue.append(content)
        elif kind == "initialized":
            self.ready = True
            self.note = "붙었습니다"

    # 서버에게 거는 말
    def _setup(self) -> None:
        assert self.client is not None
        self.client.send_message("/server", ["create_agent", self.agent, "listlabel"])
        time.sleep(1.0)
        self.client.send_message(
            self.agent,
            ["set_control_parameter", "generator::prospector::_navigator::max_continuity", self.max_continuity],
        )
        self.client.send_message(self.agent, ["set_control_parameter", "generator::force_output", 1])
        self.client.send_message(self.agent, ["clear", "listlabel"])
        time.sleep(0.3)
        # 코퍼스를 순서대로 배우게 한다. 조각의 순서가 곧 「이렇게 이어지곤 했다」는 기록이다.
        # 한꺼번에 쏟으면 UDP 라 몇 개가 흘러내린다. 조금씩 쉬어 가며 보낸다.
        for i, s in enumerate(self.corpus.slices):
            self.client.send_message(self.agent, ["learn_event", "listlabel", f"P{s.partial:02d}", s.id])
            if i % 20 == 19:
                time.sleep(0.05)
        time.sleep(0.5)
        self.ready = True
        self.note = f"붙었습니다 · 조각 {len(self.corpus)}개를 배웠습니다"
        self.request([])

    def request(self, sounding: list[int], count: int = 4) -> None:
        """다음 조각들을 미리 받아 둔다. 걸음이 들어올 때 기다리지 않으려고 앞서 묻는다."""
        if self.client is None or not self.ready:
            return
        now = time.time()
        if now - self._last_query < settings.DICY2_QUERY_GAP:
            return
        self._last_query = now
        self._n += 1
        name = f"q{self._n}"
        # 지금 울리는 소리에 맞춰 달라고만 하면 같은 자리를 맴돈다. 가끔은 그냥 이어 가게 둔다.
        if sounding and self._n % 3 != 0:
            labels = [f"P{p:02d}" for p in sounding[-4:]]
            args = [name, 0, "relative", "None", "listlabel", "[", *labels, "]"]
        else:
            args = [name, 0, "relative", count]
        self.client.send_message(self.agent, ["query", *args])

    def take(self) -> str | None:
        return self.queue.popleft() if self.queue else None

    def stop(self) -> None:
        server = getattr(self, "server", None)
        if server is not None:
            server.shutdown()
