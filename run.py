#!/usr/bin/env python3
"""
걸음이 합주가 된다 — 시작하는 자리.

  python run.py                     웹캠으로 돌린다. 브라우저에서 http://127.0.0.1:7000
  python run.py --sim               카메라 없이 가짜 관객으로 돌린다
  python run.py --offline 30        스피커 없이 30초를 out.wav 로 적는다
  python run.py --engine dicy2      Dicy2 생성 엔진에 물어본다 (서버를 따로 띄워 둘 것)

처음이면 --sim 으로 한 번 띄워 대시보드부터 보는 것을 권한다.
"""

from __future__ import annotations

import argparse
import threading
import time
from pathlib import Path

from stepchorus import settings
from stepchorus.app import Piece
from stepchorus.audio import BLOCK, Recorder, Speaker
from stepchorus.vision import CameraVision, SimVision

HERE = Path(__file__).parent


def main() -> None:
    ap = argparse.ArgumentParser(description="걸음이 합주가 되는 예제")
    ap.add_argument("--sim", action="store_true", help="카메라 없이 가짜 관객으로 돌린다")
    ap.add_argument("--people", type=int, default=None,
                    help="동시에 몇 명까지 볼지. --sim 이면 가짜 관객 수가 된다")
    ap.add_argument("--offline", type=float, default=0, help="초 단위. 스피커 대신 wav 로 적는다")
    ap.add_argument("--out", default="out.wav", help="--offline 일 때 적을 파일")
    ap.add_argument("--port", type=int, default=settings.PORT)
    ap.add_argument("--host", default=settings.HOST, help="폰으로 보려면 0.0.0.0")
    ap.add_argument("--corpus", default=str(HERE / "corpus" / "default"))
    ap.add_argument("--engine", default="rule", choices=["rule", "dicy2"])
    ap.add_argument("--dicy2-recv", type=int, default=None,
                    help="Dicy2 서버가 보내는 포트. 여러 번 켤 때 겹치지 않게 한다")
    ap.add_argument("--camera", type=int, default=0, help="웹캠이 여러 대일 때 번호")
    ap.add_argument("--video", default=None, help="웹캠 대신 영상 파일로 시험한다")
    ap.add_argument("--model", default=None, help="사람을 찾는 모델 파일. 여러 명이면 full 모델이 낫다")
    args = ap.parse_args()

    if args.dicy2_recv:
        settings.DICY2_RECV_PORT = args.dicy2_recv
    if args.people:
        settings.SIM_MAX_PEOPLE = args.people
        settings.MAX_PEOPLE = args.people
    piece = Piece(Path(args.corpus), engine=args.engine)
    print(f"코퍼스: {piece.corpus.name} · 조각 {len(piece.corpus)}개")

    # 소리 없이 숫자만 보고 싶을 때를 위해 녹음과 재생을 갈라 둔다.
    if args.offline:
        rec = Recorder(piece.mixer)
        sim = SimVision(piece.on_event, piece.vision, max_people=settings.SIM_MAX_PEOPLE)
        walkers: dict = {}
        blocks = int(args.offline * 44100 / BLOCK)
        for i in range(blocks):
            sim.tick(i * BLOCK / 44100, walkers)
            rec.tick(BLOCK)
        seconds = rec.save(args.out)
        print(f"{args.out} 에 {seconds:.1f}초를 적었습니다. 걸음 {piece.total_steps}번.")
        for row in list(piece.log)[:10]:
            print(f"  {row['t']}  {row['text']}")
        return

    speaker = Speaker(piece.mixer)
    speaker.start()
    if speaker.error:
        print(f"소리 장치를 열지 못했습니다: {speaker.error}")
        print("대시보드는 그대로 뜹니다. 숫자와 로그로 확인할 수 있습니다.")

        # 스피커가 없어도 소리는 계속 흘러가야 한다. 안 그러면 겹이 쌓인 채로 멈춰 있어
        # 대시보드가 거짓말을 하고, 브라우저로 보내는 소리도 끊긴다.
        #
        # 돌 때마다 sleep(한 블록 시간) 을 하면 계산 시간만큼 매번 늦어져서 실시간보다
        # 느려진다. 그래서 다음에 깨어날 시각을 미리 정해 두고 그 시각에 맞춘다.
        def drain() -> None:
            frames = BLOCK * 4
            period = frames / 44100
            next_at = time.monotonic()
            while True:
                piece.mixer.render(frames)
                next_at += period
                delay = next_at - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
                else:
                    next_at = time.monotonic()  # 많이 밀렸으면 다시 맞춘다

        threading.Thread(target=drain, daemon=True).start()

    if args.sim:
        vision = SimVision(piece.on_event, piece.vision, max_people=settings.SIM_MAX_PEOPLE)
    else:
        vision = CameraVision(piece.on_event, piece.vision, max_people=settings.MAX_PEOPLE,
                              camera=args.video or args.camera, model=args.model or "")
    vision.start()

    import uvicorn

    from stepchorus.server import create_app

    print(f"대시보드: http://{args.host if args.host != '0.0.0.0' else '<이 컴퓨터 주소>'}:{args.port}")
    try:
        uvicorn.run(create_app(piece), host=args.host, port=args.port, log_level="warning")
    finally:
        vision.stop()
        speaker.stop()


if __name__ == "__main__":
    main()
