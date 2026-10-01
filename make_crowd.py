#!/usr/bin/env python3
"""
여러 사람이 걷는 영상 만들기.

한 사람이 걷는 영상을 네 칸으로 붙여 네 명이 걷는 것처럼 만든다. 칸마다 시작 지점을
어긋나게 해서 걸음이 겹친다. 여러 명일 때 소리가 어떻게 쌓이는지 보려고 둔 것이다.

  python make_crowd.py sample/걷는사람.ogv
  ./start.sh --video sample/여러사람.mp4

진짜 관객 넷과 같지는 않다. 사람마다 걸음 폭과 속도가 다른 상황을 보려면
./start.sh --sim --people 4 쪽이 낫다. 둘 다 해 보고 비교하는 편이 좋다.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2


def main() -> None:
    ap = argparse.ArgumentParser(description="한 사람 영상을 여러 사람 영상으로 붙인다")
    ap.add_argument("video", help="원본 영상")
    ap.add_argument("--out", default="sample/여러사람.mp4")
    ap.add_argument("--cols", type=int, default=2)
    ap.add_argument("--rows", type=int, default=2)
    ap.add_argument("--seconds", type=float, default=20.0, help="만들 길이")
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise SystemExit(f"영상을 열지 못했습니다: {args.video}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cells = args.cols * args.rows
    # 칸마다 다른 지점에서 시작한다. 그래야 네 사람이 따로 걷는 것처럼 보인다.
    offsets = [int(total * i / cells) for i in range(cells)]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width * args.cols, height * args.rows)
    )
    if not writer.isOpened():
        raise SystemExit("영상을 쓰지 못했습니다. 다른 이름(.avi)으로 해 보세요.")

    frames = int(args.seconds * fps)
    for n in range(frames):
        tiles = []
        for offset in offsets:
            cap.set(cv2.CAP_PROP_POS_FRAMES, (offset + n) % total)
            ok, frame = cap.read()
            if not ok:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = cap.read()
            tiles.append(cv2.resize(frame, (width, height)))
        rows = [
            cv2.hconcat(tiles[r * args.cols : (r + 1) * args.cols]) for r in range(args.rows)
        ]
        writer.write(cv2.vconcat(rows))
        if n % 50 == 0:
            print(f"  {n}/{frames}")

    writer.release()
    cap.release()
    print(f"\n{out_path} 를 만들었습니다 ({cells}명, {args.seconds:.0f}초)")
    print(f"들어 보려면:  ./start.sh --video {out_path}")


if __name__ == "__main__":
    main()
