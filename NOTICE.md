# NOTICE — 제3자 구성요소

이 저장소의 코드는 [LICENSE](LICENSE) 를 따릅니다. 아래 것들은 각 원저작자의 라이선스를 그대로 따릅니다.

## 코드에 포함한 것

| 경로 | 출처 | 원저작자 | 라이선스 | 수정 여부 |
|---|---|---|---|---|
| `stepchorus/web/vendor/basecoat.min.css` | https://cdn.jsdelivr.net/npm/basecoat-css@1.0.2/dist/basecoat.cdn.min.css | Basecoat (hunvreus) · Tailwind Labs | **MIT** | 수정 없음 |

전시장에서 인터넷이 끊겨도 화면이 뜨도록 CDN 대신 파일을 넣어 두었습니다.
글꼴은 내려받지 않고 운영체제에 있는 것을 씁니다.

## 실행할 때 설치하는 것 (environment.yml)

| 패키지 | 쓰는 곳 | 라이선스 |
|---|---|---|
| numpy | 소리 계산 | BSD-3-Clause |
| soundfile | wav 읽기·쓰기 | BSD-3-Clause (libsndfile 은 LGPL-2.1) |
| sounddevice | 스피커 출력 | MIT (PortAudio 는 MIT 계열) |
| fastapi · uvicorn | 대시보드 | MIT · BSD-3-Clause |
| mediapipe | 사람·발목 위치 | Apache-2.0 |
| opencv-python | 웹캠 입력 | Apache-2.0 |
| python-osc | Dicy2 서버와 주고받기 | Unlicense |

mediapipe·opencv·sounddevice 는 카메라와 스피커를 쓸 때만 필요합니다. `--sim` 과 `--offline` 만으로는 없어도 돕니다.

## 따로 받아 쓰는 것

| 대상 | 출처 | 라이선스 | 비고 |
|---|---|---|---|
| Dicy2-python | https://github.com/DYCI2/Dicy2-python | **GPL-3.0** | 저장소에 넣지 않는다. 설치 스크립트가 `engine/Dicy2-python` 에 따로 받고(이 폴더는 커밋되지 않는다), 별도 프로세스로 띄워 OSC 로만 주고받는다 |
| MediaPipe Pose Landmarker 모델 (`pose_landmarker_lite.task`) | https://storage.googleapis.com/mediapipe-models/ | Apache-2.0 | 커밋하지 않는다. 처음 한 번 내려받는다 |

## 받아서 쓰는 소리 묶음

`fetch_corpus.py` 가 받는 소리는 위키미디어 공용에서 옵니다. 퍼블릭 도메인, CC0, CC BY-SA 인
것만 골랐습니다. 받은 소리와 거기서 자른 조각은 이 저장소에 들어 있지 않고 각자 컴퓨터에만
남습니다. 출처와 조건은 받을 때 `corpus/<이름>/credits.md` 에 적힙니다.

| 묶음 | 라이선스 |
|---|---|
| 첼로 (John Michel 연주, Gounod 작곡) | 퍼블릭 도메인 |
| 싱잉볼 | CC BY-SA 4.0 |
| 징 (the-very-real-horst) | CC0 |
| 오르간 | CC BY-SA 4.0 |
| 비 (Acabashi) | CC BY-SA 4.0 |

CC BY-SA 소리로 만든 작품을 공개할 때는 그 라이선스를 따릅니다. 그게 번거로우면 퍼블릭
도메인이나 CC0 묶음을 쓰거나 직접 녹음하면 됩니다.

## 기본 코퍼스

`corpus/default/` 의 wav 파일은 `corpus.py` 가 사인파로 만든 것입니다. 녹음이 아니고
제3자 저작물이 아닙니다. 자기 녹음으로 바꾸는 방법은 README 의 `make_corpus.py` 절에 있습니다.
