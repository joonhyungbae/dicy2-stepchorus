# AGENTS.md — 이 저장소에서 일하는 AI 에이전트에게

Cursor, Claude Code, Codex 등 어떤 도구로 들어왔든 이 파일을 먼저 읽습니다.
사람에게 설명하는 글은 [README.md](README.md) 에 있습니다. 여기는 작업자용입니다.

## 이 저장소가 하는 일

관객의 걸음을 받아 소리 조각을 긴 음으로 겹치는 사운드 설치 작품의 **출발점**입니다.
완성품이 아니라 작가가 고쳐 쓰라고 둔 예제입니다. 쓰는 사람은 대개 코딩을 해 본 적이
없는 예술가입니다. 그 전제가 아래 규칙 대부분의 이유입니다.

```
웹캠 → vision.py → 걸음 사건 → agent.py 또는 dicy2.py → audio.py → 스피커 2채널
                                    ↕
                            server.py + web/  (브라우저 대시보드)
```

## 먼저 돌려 보기

```bash
./start.sh --sim                 # 카메라·스피커 없이. 엔진과 코퍼스는 알아서 붙는다
./start.sh --offline 20          # 소리 장치 없이 20초를 out.wav 로 적는다 (검증용으로 제일 빠름)
python fetch_corpus.py --list    # 받아서 쓰는 소리 묶음
```

고친 뒤에는 최소한 이 둘이 통과해야 합니다.

```bash
./start.sh --offline 10 --engine rule     # 규칙 경로
./start.sh --offline 10                   # Dicy2 경로 (엔진이 깔려 있으면 자동)
```

대시보드까지 보려면 `./start.sh --sim --port 7001` 로 띄우고 `/api/state` 를 읽습니다.

## 파일과 책임

| 파일 | 책임 | 건드릴 때 주의 |
|---|---|---|
| `stepchorus/settings.py` | **숫자의 유일한 출처** | 다른 파일에 숫자를 하드코딩하지 않는다. 여기에 추가하고 참조한다 |
| `run.py` | 인자 해석, 세 조각 연결 | 로직을 여기 쌓지 않는다 |
| `stepchorus/app.py` | 걸음 하나가 들어왔을 때의 흐름 | 세 줄짜리 흐름을 유지한다 |
| `stepchorus/agent.py` | 규칙으로 조각 고르기 | Dicy2 가 없을 때의 **대체 경로**다. 항상 동작해야 한다 |
| `stepchorus/dicy2.py` | Dicy2 서버와 OSC | 답을 기다리며 블로킹하지 않는다. 큐에서 꺼내 쓰고 없으면 규칙으로 |
| `stepchorus/audio.py` | 믹서, 스피커, 오프라인 녹음 | 오디오 콜백 안에서 무거운 일을 하지 않는다 |
| `stepchorus/corpus.py` | 조각 묶음 읽기·만들기 | 자르는 코드는 `build_corpus_from_audio` 하나뿐이다 |
| `stepchorus/vision.py` | 걸음 감지와 가짜 관객 | 네 가지 사건(enter·move·step·leave)만 내보낸다. `--video` 로 영상 파일도 카메라처럼 받는다 |
| `stepchorus/server.py`, `web/` | 대시보드 | 외부 CDN 을 쓰지 않는다 |

## 깨뜨리면 안 되는 것

1. **인터넷 없이 떠야 한다.** 전시장에서 네트워크가 끊깁니다. 대시보드는 `web/vendor/` 의
   CSS 만 씁니다. CDN 링크, 구글 폰트, 외부 스크립트를 추가하지 않습니다.
2. **소리는 멎지 않는다.** Dicy2 서버가 없거나 늦으면 규칙이 대신 고릅니다. 카메라가 없으면
   `--sim`, 스피커가 없으면 `--offline` 으로 돌아갑니다. 새 기능도 이 성질을 유지합니다.
3. **숫자는 `settings.py` 에.** 작가가 코드를 못 읽어도 값은 바꿀 수 있어야 합니다.
4. **주석과 문서는 한국어.** 쓰는 사람이 한국어 사용자입니다. 영어 요약은 README 맨 아래에만
   둡니다. 긴 대시(—)를 쓰지 않고 쉼표와 마침표로 끊습니다.
5. **Dicy2 는 벤더링하지 않는다.** GPL-3.0 입니다. `engine/Dicy2-python` 에 따로 받아 별도
   프로세스로 띄우고 OSC 로만 주고받습니다. 코드를 이 저장소에 복사해 넣지 않습니다.
6. **소리 파일을 커밋하지 않는다.** `corpus/` 와 `engine/` 은 `.gitignore` 에 있습니다.
   받은 소리에는 각자의 라이선스가 있고 출처는 `corpus/<이름>/credits.md` 에 적힙니다.
7. **언제나 conda 환경으로 돈다.** 설치와 켜기는 `scripts/conda.sh`(윈도우 `conda.ps1`)로 conda 를
   찾고, 없으면 Miniforge 를 `~/miniforge3` 에 깝니다. venv 나 시스템 파이썬으로 켜는 길을 만들지 않습니다.
   패키지는 `environment.yml` 에만 더합니다(pip 로만 받는 것은 `pip:` 아래).
8. **라이선스.** 이 코드는 소스 공개(OpenCircuit License v1.0)이고 오픈소스가 아닙니다.
   README 나 설명에서 "오픈소스"라고 부르지 않습니다.

## 자주 하는 작업

- **소리의 성격을 바꾼다** → `agent.py` 의 `consonance` 와 `settings.py` 의 가중치 셋.
- **입력을 바꾼다**(걸음 말고 다른 것) → `vision.py` 에서 같은 네 사건을 내보내면 나머지는
  그대로 돕니다. 바닥 센서, 마이크, 마우스 어느 것이든 됩니다.
- **대시보드에 값을 더한다** → `app.py` 의 `snapshot()` 에 넣고 `web/app.js` 의 `draw()` 에서
  그립니다. 슬라이더는 `set_params()` 와 `SLIDERS` 배열 양쪽에 추가합니다.
- **Dicy2 질의를 손본다** → `dicy2.py` 의 `request()`. 메시지 형식은 파일 맨 위 주석에 있고,
  실제 서버 문서는 `engine/Dicy2-python/docs/` 입니다.

## 함정

- Dicy2 는 UDP 라 코퍼스를 한꺼번에 쏟으면 몇 개가 사라집니다. 스무 개마다 쉬는 코드가
  `dicy2.py` 에 있습니다. 지우지 마세요.
- `--offline` 은 실시간보다 빠르게 계산합니다. 그래서 Dicy2 가 학습을 마치기 전에 끝나고
  규칙으로 메울 수 있습니다. 엔진을 검증하려면 `--sim` 으로 띄우고 `/api/state` 의
  `engine_note` 를 봅니다.
- 리눅스에도 `open` 이라는 다른 명령이 있어서 `start.sh` 는 `uname` 을 먼저 봅니다.
- conda 는 터미널 설정을 읽지 않는 자리(curl | bash, 더블클릭)에서도 찾아야 합니다. `scripts/conda.sh` 의
  `find_conda` 가 흔한 설치 위치를 차례로 봅니다. `conda activate` 대신 `conda run --no-capture-output -n stepchorus` 를 씁니다.
- conda 환경 이름은 `stepchorus` 입니다. 저장소 이름(하이픈 있음)과 파이썬 패키지
  이름(하이픈 없음)이 다른 것은 의도한 것입니다.
- 소리를 실시간 속도로 만들어야 합니다. 돌 때마다 `sleep(한 블록)` 을 하면 계산 시간만큼
  매번 늦어져 5% 쯤 느려지고, 브라우저에서 규칙적으로 끊깁니다. `run.py` 의 `drain` 은
  다음에 깨어날 시각을 정해 두고 거기에 맞춥니다. 같은 방식을 유지하세요.
- 소리 장치가 없는 기계에서는 대시보드의 「소리 듣기」로 브라우저가 받아 듣습니다
  (`/audio` 통로, 16비트 PCM). 듣는 사람이 없으면 아무것도 쌓지 않습니다.
- 소리 장치가 없는 기계에서도 대시보드는 떠야 합니다. `run.py` 가 무음으로 믹서를 돌립니다.
- uvicorn 에 `websockets` 가 없으면 `/ws` 가 404 가 됩니다. 의존성에서 빼지 마세요. 그런 경우에도
  화면이 멈추지 않도록 `web/app.js` 가 0.4초 폴링으로 저절로 바꿉니다.

## 비슷한 예제를 새로 만들 때

이 저장소를 베끼지 말고 규칙과 틀을 쓰세요. 오픈서킷 허브에 있습니다.

- 규칙: https://github.com/joonhyungbae/opencircuit/blob/main/docs/example-repo.md
- 틀: https://github.com/joonhyungbae/opencircuit/tree/main/templates/example-repo
- 이 저장소는 그 규칙을 실제로 지킨 참고 구현입니다.

## 작업을 마칠 때

고친 내용이 사람에게 보이는 것이면 README 도 같이 고칩니다. 설명을 길게 쓰지 말고,
무엇을 치면 되는지와 무엇이 보이는지를 적습니다. 커밋 메시지는 한국어로, 무엇을 왜 바꿨는지
한 줄로 적습니다.
