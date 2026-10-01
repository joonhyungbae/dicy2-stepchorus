"""
대시보드 — 브라우저에서 보고 만진다.

전시장에서는 노트북 앞에 가지 않고 폰으로 상태를 본다. 작업 중에는 값을 바꿔 가며
소리를 맞춘다. 코드를 고치지 않고 만질 수 있는 자리를 여기에 모아 둔다.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import settings
from .app import Piece

WEB = Path(__file__).parent / "web"


def create_app(piece: Piece) -> FastAPI:
    api = FastAPI(title="dicy2-stepchorus")
    # 화면 파일(css·js·Basecoat)을 그대로 내준다. 인터넷이 없어도 뜬다.
    api.mount("/static", StaticFiles(directory=WEB), name="static")

    @api.middleware("http")
    async def no_cache(request, call_next):  # noqa: ANN001
        """브라우저가 옛 화면을 들고 있지 않게 한다. 고치면서 쓰는 도구라 캐시가 방해가 된다."""
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    @api.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return (WEB / "index.html").read_text(encoding="utf-8")

    @api.get("/api/state")
    async def state() -> JSONResponse:
        return JSONResponse(piece.snapshot())

    @api.post("/api/params")
    async def params(data: dict) -> JSONResponse:
        piece.set_params(data)
        return JSONResponse(piece.snapshot()["params"])

    @api.get("/camera")
    async def camera() -> StreamingResponse:
        """카메라가 보는 것을 그대로 보낸다. 브라우저가 <img> 하나로 받는다."""

        async def frames():
            piece.vision.want_preview = True
            try:
                while True:
                    jpeg = piece.vision.jpeg
                    if jpeg:
                        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
                    await asyncio.sleep(1 / 12)
            finally:
                piece.vision.want_preview = False

        return StreamingResponse(frames(), media_type="multipart/x-mixed-replace; boundary=frame")

    @api.websocket("/audio")
    async def audio(socket: WebSocket) -> None:
        """브라우저로 소리를 보낸다. 서버에 스피커가 없거나 멀리서 들을 때 쓴다."""
        await socket.accept()
        piece.mixer.tap_on = True
        piece.mixer.tap.clear()
        try:
            await socket.send_text(json.dumps({"rate": 44100, "channels": 2}))
            while True:
                data = piece.mixer.take_tap()
                if data:
                    await socket.send_bytes(data)
                await asyncio.sleep(0.1)
        except (WebSocketDisconnect, Exception):
            return
        finally:
            piece.mixer.tap_on = False

    @api.websocket("/ws")
    async def ws(socket: WebSocket) -> None:
        await socket.accept()
        try:
            while True:
                await socket.send_text(json.dumps(piece.snapshot(), ensure_ascii=False))
                await asyncio.sleep(settings.PUSH_SECONDS)
        except WebSocketDisconnect:
            return
        except Exception:
            return

    return api
