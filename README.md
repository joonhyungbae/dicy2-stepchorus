# dicy2-stepchorus

**사람이 걸으면 소리가 하나 울립니다.** 그 소리는 몇 초 동안 천천히 사라집니다. 여러 사람이
걸으면 소리가 겹쳐서 하나로 들립니다. 사람이 다 나가면 조용해집니다.

웹캠 한 대, 노트북 한 대, 스피커 두 대로 돕니다. 소리를 고르는 일은 IRCAM 의 생성 엔진
[Dicy2](https://github.com/DYCI2/Dicy2-python)가 맡습니다. 완성된 작품이 아니라 출발점이고,
소리와 규칙을 바꿔 가며 자기 작품으로 만들라고 둔 예제입니다.

《2026 오픈서킷 부산: 아트앤테크 프랙티스》 멘토링 과정에서 만든 예제입니다. 참여 작가와
작업을 구상하다 공통으로 쓸 만한 뼈대가 나와, 참여자 누구나 쓸 수 있도록 공개합니다.

## 1. 깔기

터미널을 엽니다. 윈도우는 시작 메뉴에서 `PowerShell`, 맥은 `터미널`을 찾으면 됩니다.
까만 창에 아래를 붙여 넣고 엔터를 누릅니다. 받는 것부터 설치까지 알아서 합니다.

**맥 · 리눅스**

```bash
curl -fsSL https://raw.githubusercontent.com/joonhyungbae/dicy2-stepchorus/main/install.sh | bash
```

**윈도우 (PowerShell)**

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
irm https://raw.githubusercontent.com/joonhyungbae/dicy2-stepchorus/main/install.ps1 -OutFile "$env:TEMP\sc-install.ps1"
& "$env:TEMP\sc-install.ps1"
```

몇 분 걸립니다. 설치가 네 가지를 챙깁니다.

- conda 환경 `stepchorus` (conda 가 없으면 Miniforge 를 먼저 깝니다)
- 소리를 고르는 **Dicy2 엔진**
- 웹캠으로 사람을 보는 **모델 파일**
- 처음 들어 볼 **소리 묶음**(첼로, 퍼블릭 도메인)

언제나 conda 환경(`stepchorus`)으로 돕니다. 소리와 카메라 쪽이 덜 깨집니다. 이미 conda
(Anaconda, Miniconda)가 있으면 그것을 쓰고, 없으면 [Miniforge](https://conda-forge.org/download/)를
사용자 폴더(`~/miniforge3`)에 먼저 깝니다. 관리자 권한이 필요 없고 터미널 설정 파일은 건드리지 않습니다.

## 2. 켜기

받은 폴더에서 한 줄입니다.

```bash
./start.sh            # 맥 · 리눅스
.\start.ps1           # 윈도우
```

브라우저가 저절로 열립니다. 안 열리면 주소창에 `127.0.0.1:7000` 을 칩니다.
끌 때는 터미널에서 <kbd>Ctrl</kbd>+<kbd>C</kbd> 입니다.

이 한 줄이 알아서 하는 일이 셋입니다. Dicy2 엔진을 켜고, 첼로 소리를 불러오고, 웹캠 모델이
없으면 가짜 관객 모드로 켭니다. 화면 맨 위에 **dicy2 연결됨** 이라고 뜨면 엔진이 소리를
고르고 있는 것입니다.

## 3. 화면에서 무엇을 보나

- **전시장 바닥**: 가로가 공간의 좌우입니다. 점이 사람이고, 점 아래 글자가 그 사람이
  마지막으로 울린 소리의 이름입니다.
- **울리는 소리**: 지금 울리고 있는 소리들입니다. 막대가 짧아질수록 곧 사라집니다.
- **카메라가 보는 것**: 관절과 발목이 그려집니다. 걸음으로 센 순간에는 발목 동그라미가 한 번
  커집니다. 카메라 각도를 잡을 때 이 화면을 봅니다.
- **조절**: 슬라이더를 움직이면 소리가 바로 달라집니다.
- **소리 듣기** (오른쪽 위): 이 브라우저로 소리를 받아 듣습니다. 서버에 스피커가 없거나
  다른 컴퓨터에서 볼 때 씁니다. 브라우저는 사람이 눌러야 소리를 내 줍니다.
- **방금 일어난 일**: 누가 걸었고 어떤 소리가 골라졌는지 적힙니다.

## 4. 바꿔 보기

쉬운 것부터 적었습니다.

1. **대시보드 슬라이더.** 음의 길이를 1초로 줄이면 건반처럼 들리고, 12초로 늘리면 뭉쳐서
   울립니다. 작품의 성격이 여기서 갈립니다.
2. **`stepchorus/settings.py`.** 숫자가 전부 이 파일 하나에 있습니다. 줄마다 무엇을 바꾸는
   값인지 한국어로 적어 두었습니다. 고치고 저장한 뒤 프로그램을 다시 켜면 됩니다.
3. **소리 바꾸기.** 아래 5번입니다. 받아 쓰거나 직접 녹음하면 됩니다.
4. **고르는 규칙.** `stepchorus/agent.py` 의 `consonance` 함수가 「무엇을 어울린다고 볼지」를
   정합니다. 여기를 바꾸면 소리의 성격이 달라집니다.

## 5. 소리 바꾸기

소리가 작품의 전부입니다. 바꾸는 길이 둘 있습니다.

**받아 쓰기.** 퍼블릭 도메인이거나 CC 라이선스인 소리 묶음을 바로 받을 수 있습니다.

```bash
python fetch_corpus.py --list        # 무엇이 있는지 본다
python fetch_corpus.py 싱잉볼          # 받아서 조각으로 자른다
./start.sh --sim --corpus corpus/싱잉볼
```

첼로, 싱잉볼, 징, 오르간, 비 다섯입니다. 설치할 때 첼로는 이미 받아 두었습니다. 받은 소리의
출처와 조건은 `corpus/<이름>/credits.md` 에 적힙니다. 소리 파일은 저장소에 올라가지 않습니다.

**내 녹음 쓰기.** 직접 녹음한 것이 제일 좋습니다.

```bash
python make_corpus.py 내녹음.wav --name 첼로2
./start.sh --sim --corpus corpus/첼로2
```

악기 한 음이든 빗소리든 목소리든 됩니다. 긴 녹음일수록 조각이 많이 나옵니다.

(`python` 으로 직접 칠 때는 conda 환경 안에서 칩니다. `conda activate stepchorus` 를 먼저 하거나,
`conda run -n stepchorus python make_corpus.py ...` 처럼 앞에 붙입니다. `./start.sh` 는 알아서 합니다.)

## 6. 웹캠으로 진짜 사람 받기

설치할 때 웹캠용 모델 파일을 같이 받아 둡니다. 그래서 그냥 켜면 됩니다.

```bash
./start.sh
```

카메라가 보이는 자리에서 걸어 보면 됩니다. 폰으로 대시보드를 보려면
`./start.sh --host 0.0.0.0` 으로 켜고, 터미널에 나오는 주소를 폰 브라우저에 칩니다.

카메라가 없으면 영상 파일로 시험할 수 있습니다. 받는 법은 [sample/README.md](sample/README.md).

```bash
./start.sh --video sample/걷는사람.ogv
```

## 7. 여러 사람일 때

작품의 핵심은 여러 사람의 소리가 겹치는 순간입니다. 두 가지로 볼 수 있습니다.

**가짜 관객 여럿** — 가장 분명하게 들립니다. 사람 수를 바꿔 가며 겹침을 비교해 보세요.

```bash
./start.sh --sim --people 1      # 한 명. 선율처럼 들린다
./start.sh --sim --people 4      # 네 명. 층이 쌓여 하나로 울린다
```

**영상으로** — 한 사람 영상을 네 칸으로 붙여 네 명처럼 만듭니다.

```bash
python make_crowd.py sample/걷는사람.ogv
./start.sh --video sample/여러사람.mp4 --model pose_landmarker_full.task --people 4
```

여러 명을 볼 때는 큰 모델이 낫습니다. 한 번 받아 두면 됩니다.

```bash
curl -fsSL -o pose_landmarker_full.task \
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task"
```

그래도 영상에서는 넷 중 둘셋만 잡히는 때가 많습니다. 사람이 크게 보이고 발이 화면 안에
들어오는 각도일수록 잘 잡힙니다. 전시장에서 카메라 자리를 정할 때 이 점을 먼저 봅니다.
놓치는 정도는 `settings.py` 의 `POSE_CONFIDENCE` 로 조절합니다.

## 8. 안 될 때

| 이런 일이 생기면 | 이렇게 합니다 |
|---|---|
| 소리가 안 들린다 | `./start.sh --offline 30` 으로 30초를 `out.wav` 에 적어 들어 봅니다. 파일이 멀쩡하면 스피커 설정 문제입니다 |
| 소리 장치를 못 연다고 나온다 | 설치 명령을 다시 실행해 conda 환경을 최신으로 맞춥니다. 그래도 안 되면 운영체제 설정에서 스피커가 잡히는지 봅니다 |
| 「conda 환경이 없습니다」가 나온다 | 설치 명령을 다시 실행합니다. 받아 둔 폴더 안에서 `bash install.sh` 로 쳐도 됩니다 |
| 카메라를 못 찾는다 | 맥은 시스템 설정에서 터미널의 카메라 권한을 켭니다. 폴더에 `pose_landmarker_lite.task` 가 있는지도 봅니다 |
| 주소가 안 열린다 | 터미널이 켜져 있는지 봅니다. 껐으면 `./start.sh` 를 다시 칩니다 |
| 화면 숫자가 안 바뀐다 | 그대로 두면 0.4초마다 다시 물어보는 방식으로 저절로 바뀝니다. 그래도 멈춰 있으면 설치를 다시 실행합니다 |
| 포트가 쓰이고 있다고 나온다 | `./start.sh --port 7001` 처럼 숫자를 바꿉니다 |
| 윈도우에서 스크립트가 막힌다 | PowerShell 에 `Set-ExecutionPolicy -Scope Process Bypass -Force` 를 먼저 칩니다 |

## 9. 더 들어가기

코드는 한 파일이 한 가지만 합니다.

```text
settings.py   만지는 숫자가 전부 여기 있다. 여기부터 본다
run.py        시작하는 자리
app.py        걸음 하나가 들어왔을 때 벌어지는 일. 세 줄이다
agent.py      다음에 어떤 소리를 울릴지 고른다. 여기가 작곡이다
dicy2.py      고르는 일을 Dicy2 엔진에게 맡길 때
corpus.py     소리 조각 묶음      audio.py   소리를 겹쳐 내보낸다
vision.py     걸음을 알아챈다      server.py  대시보드 (화면은 web/)
```

소리를 고르는 일은 [Dicy2](https://github.com/DYCI2/Dicy2-python)가 합니다. IRCAM 음악표상팀이
만든 생성 엔진이고, 녹음을 순서가 있는 기록으로 배워서 다음에 올 소리를 골라 줍니다.
설치할 때 `engine/` 아래에 같이 깔리고 `./start.sh` 가 알아서 켭니다. 손으로 할 일은 없습니다.

엔진 없이 돌리려면 `./start.sh --sim --engine rule` 입니다. 그때는 `agent.py` 의 규칙이
소리를 고릅니다. 엔진이 답을 늦게 주는 순간에도 이 규칙이 대신 메웁니다.
주고받는 말은 `stepchorus/dicy2.py` 맨 위에 적어 두었습니다.

왜 이런 구조로 만들었는지는 [docs/notes.md](docs/notes.md)에 있습니다.
Cursor 나 Claude 같은 AI 도구로 이 저장소를 고칠 때의 규칙은 [AGENTS.md](AGENTS.md)에 있습니다.

## 쓰는 것과 라이선스

화면은 [Basecoat](https://basecoatui.com)(MIT), 사람 감지는
[MediaPipe](https://ai.google.dev/edge/mediapipe)(Apache-2.0)입니다. 인터넷 없이도 돌아가도록
필요한 파일을 저장소에 넣어 두었습니다. 전체 목록은 [NOTICE.md](NOTICE.md)에 있습니다.

코드는 [OpenCircuit License v1.0](LICENSE)을 따릅니다. 오픈소스가 아니라 소스를 공개하되
쓰임을 제한하는 쪽입니다.

- **됩니다**: 받아서 쓰고 고치기. 이것으로 만든 **작품**은 전시하고 팔아도 허가가 필요 없습니다.
- **문의해 주세요**: 강좌나 워크숍의 교재로 쓰는 것, 코드 자체를 파는 것. <jh.bae@kaist.ac.kr>

---

<details>
<summary>English</summary>

When someone walks, a long tone rises and slowly fades. With several people the layers overlap
into one sound; when they leave it sinks away. One webcam, one laptop, two speakers.

```bash
curl -fsSL https://raw.githubusercontent.com/joonhyungbae/dicy2-stepchorus/main/install.sh | bash
cd dicy2-stepchorus && ./start.sh      # dashboard at 127.0.0.1:7000
```

The installer always builds a conda environment (`stepchorus`); if no conda is found it first
installs Miniforge to `~/miniforge3`. It also downloads the MediaPipe model. Windows: `install.ps1`.

Walking is detected with MediaPipe. Which sound comes next is decided by the rules in
`stepchorus/agent.py`, or by [Dicy2](https://github.com/DYCI2/Dicy2-python), IRCAM's generative
agent, over OSC. Every number you might want to change lives in `stepchorus/settings.py`.

Source-available, not open source: personal and artistic use is free and the works you make are
entirely yours; teaching with it or selling it needs permission ([LICENSE](LICENSE)).

</details>

<sub>《2026 오픈서킷 부산: 아트앤테크 프랙티스》에서 만든 작품 베이스라인입니다. 다른 도구는
[opencircuit](https://github.com/joonhyungbae/opencircuit)에 모여 있습니다.</sub>
