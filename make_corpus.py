#!/usr/bin/env python3
"""
내 녹음을 소리 조각 묶음(코퍼스)으로 자른다.

  python make_corpus.py 내녹음.wav --name 첼로
  ./start.sh --sim --corpus corpus/첼로

악기 한 음이든 빗소리든 목소리든 된다. 긴 녹음일수록 조각이 많이 나온다.
받아서 바로 쓸 수 있는 소리 묶음은 fetch_corpus.py 에 있다.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from stepchorus.corpus import build_corpus_from_audio
from stepchorus.settings import BASE_HZ


def main() -> None:
    ap = argparse.ArgumentParser(description="녹음 파일을 코퍼스로 자른다")
    ap.add_argument("audio", nargs="+", help="wav · flac · ogg 파일")
    ap.add_argument("--name", default="내 코퍼스")
    ap.add_argument("--seconds", type=float, default=6.0, help="조각 하나의 길이")
    ap.add_argument("--hop", type=float, default=3.0, help="몇 초마다 자를지")
    ap.add_argument("--base", type=float, default=BASE_HZ, help="기본음(Hz). 배수를 재는 기준")
    ap.add_argument("--out", default=None, help="corpus/<이름> 폴더")
    args = ap.parse_args()

    out = Path(args.out or (Path("corpus") / args.name))
    corpus = build_corpus_from_audio(
        [Path(a) for a in args.audio], out, args.name, args.seconds, args.hop, args.base
    )
    print(f"{out} 에 조각 {len(corpus)}개를 만들었습니다.")
    print(f"들어 보려면:  ./start.sh --sim --corpus {out}")


if __name__ == "__main__":
    main()
