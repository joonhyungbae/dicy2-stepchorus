#!/usr/bin/env python3
"""
바로 받아 쓰는 소리 묶음.

녹음할 것이 아직 없어도 이것만 받으면 진짜 소리로 들어 볼 수 있다.

  python fetch_corpus.py --list        무엇이 있는지 본다
  python fetch_corpus.py 첼로           받아서 조각으로 자른다
  ./start.sh --sim --corpus corpus/첼로  그 소리로 켠다

소리는 위키미디어 공용(Wikimedia Commons)에서 받는다. 퍼블릭 도메인이거나 CC 라이선스인
것만 골랐다. 받은 소리와 거기서 자른 조각은 저장소에 올라가지 않는다. 만든 작품을 공개할 때는
corpus/<이름>/credits.md 에 적힌 조건을 지키면 된다. 내 녹음을 쓰려면 make_corpus.py 를 쓴다.
"""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

from stepchorus.corpus import build_corpus_from_audio

UA = {"User-Agent": "dicy2-stepchorus (https://github.com/joonhyungbae/dicy2-stepchorus)"}

PACKS: dict[str, dict] = {
    "첼로": {
        "about": "바흐를 연주하는 첼로 독주. 긴 활 소리라 겹쳐도 탁해지지 않는다",
        "seconds": 6.0,
        "hop": 3.0,
        "files": [
            {
                "url": "https://upload.wikimedia.org/wikipedia/commons/d/d4/JOHN_MICHEL_CELLO-BACH_AVE_MARIA.ogg",
                "page": "https://commons.wikimedia.org/wiki/File:JOHN_MICHEL_CELLO-BACH_AVE_MARIA.ogg",
                "by": "John Michel (연주) · Charles Gounod (작곡)",
                "license": "퍼블릭 도메인",
            }
        ],
    },
    "싱잉볼": {
        "about": "티베트 싱잉볼. 한 번 치면 오래 울려서 층이 잘 쌓인다",
        "seconds": 8.0,
        "hop": 4.0,
        "files": [
            {
                "url": "https://upload.wikimedia.org/wikipedia/commons/a/a4/Tibetan_Singing_Bowl_4.5inch.flac",
                "page": "https://commons.wikimedia.org/wiki/File:Tibetan_Singing_Bowl_4.5inch.flac",
                "by": "Wikimedia Commons 기여자",
                "license": "CC BY-SA 4.0",
            },
            {
                "url": "https://upload.wikimedia.org/wikipedia/commons/e/e1/Tibetan_Singing_Bowl_hit_11inch.flac",
                "page": "https://commons.wikimedia.org/wiki/File:Tibetan_Singing_Bowl_hit_11inch.flac",
                "by": "Wikimedia Commons 기여자",
                "license": "CC BY-SA 4.0",
            },
        ],
    },
    "징": {
        "about": "중국 징. 낮고 두꺼운 울림. 사람이 많을수록 바닥이 흔들리는 느낌이 난다",
        "seconds": 8.0,
        "hop": 4.0,
        "files": [
            {
                "url": "https://upload.wikimedia.org/wikipedia/commons/1/16/240382_the-very-real-horst_chinese-gong-finish-session-2014-06-10-29-143.wav",
                "page": "https://commons.wikimedia.org/wiki/File:240382_the-very-real-horst_chinese-gong-finish-session-2014-06-10-29-143.wav",
                "by": "the-very-real-horst",
                "license": "CC0",
            }
        ],
    },
    "오르간": {
        "about": "파이프 오르간 즉흥. 소리가 끊기지 않아서 공간이 꽉 찬다",
        "seconds": 6.0,
        "hop": 3.0,
        "files": [
            {
                "url": "https://upload.wikimedia.org/wikipedia/commons/5/54/Improvisation_Entrada.ogg",
                "page": "https://commons.wikimedia.org/wiki/File:Improvisation_Entrada.ogg",
                "by": "Wikimedia Commons 기여자",
                "license": "CC BY-SA 4.0",
            }
        ],
    },
    "비": {
        "about": "빗소리. 음높이가 없는 소리라 겹쳐도 화음이 아니라 두께가 생긴다",
        "seconds": 5.0,
        "hop": 2.5,
        "files": [
            {
                "url": "https://upload.wikimedia.org/wikipedia/commons/7/73/Rain_and_wind_in_London_2026_08_28.wav",
                "page": "https://commons.wikimedia.org/wiki/File:Rain_and_wind_in_London_2026_08_28.wav",
                "by": "Acabashi",
                "license": "CC BY-SA 4.0",
            }
        ],
    },
}


def show_list() -> None:
    print("받아서 바로 쓸 수 있는 소리 묶음\n")
    for name, pack in PACKS.items():
        licenses = ", ".join(sorted({f["license"] for f in pack["files"]}))
        print(f"  {name:6} {pack['about']}")
        print(f"         ({licenses})")
    print("\n받기:  python fetch_corpus.py 첼로")


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request) as response, open(dest, "wb") as out:
        out.write(response.read())


def write_credits(pack_name: str, pack: dict, out: Path) -> None:
    lines = [
        f"# {pack_name} — 소리 출처",
        "",
        "이 폴더의 소리는 아래에서 받아 잘라 둔 것입니다. 작품을 공개할 때 아래 조건을 지키면 됩니다.",
        "",
    ]
    for f in pack["files"]:
        lines += [f"- {f['by']} · {f['license']}", f"  {f['page']}", ""]
    (out / "credits.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="공개된 소리 묶음을 받아 코퍼스로 만든다")
    ap.add_argument("name", nargs="?", help="받을 묶음 이름")
    ap.add_argument("--list", action="store_true", help="무엇이 있는지 본다")
    args = ap.parse_args()

    if args.list or not args.name:
        show_list()
        return
    if args.name not in PACKS:
        print(f"그런 묶음이 없습니다: {args.name}")
        show_list()
        raise SystemExit(1)

    pack = PACKS[args.name]
    out = Path("corpus") / args.name
    sources = []
    for i, f in enumerate(pack["files"]):
        suffix = Path(f["url"]).suffix or ".wav"
        dest = out / "source" / f"{i:02d}{suffix}"
        print(f"받는 중: {f['page']}")
        download(f["url"], dest)
        sources.append(dest)

    print("조각으로 자르는 중")
    try:
        corpus = build_corpus_from_audio(sources, out, args.name, pack["seconds"], pack["hop"])
    except Exception as exc:  # 형식을 못 읽는 경우가 대부분이다
        raise SystemExit(
            f"소리 파일을 읽지 못했습니다 ({exc}).\n"
            f"{out / 'source'} 의 파일을 지우고 다시 받아 보세요. 그래도 안 되면 알려 주세요."
        )
    write_credits(args.name, pack, out)

    print(f"\n{out} 에 조각 {len(corpus)}개를 만들었습니다. 출처는 {out}/credits.md 에 적었습니다.")
    print(f"들어 보려면:  ./start.sh --sim --corpus {out}")


if __name__ == "__main__":
    main()
