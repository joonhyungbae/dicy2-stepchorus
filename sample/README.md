# sample — 카메라 대신 쓸 영상

웹캠이 없는 컴퓨터에서 시험할 때 씁니다. 영상 파일을 카메라처럼 넣습니다.

```bash
./start.sh --video sample/걷는사람.ogv
```

영상은 저장소에 올라가지 않습니다. 아래 한 줄로 받으면 됩니다.

```bash
curl -fsSL -o sample/걷는사람.ogv \
  "https://upload.wikimedia.org/wikipedia/commons/1/1d/A-novel-walking-speed-estimation-scheme-and-its-application-to-treadmill-control-for-gait-1743-0003-9-62-S1.ogv"
```

출처: 위키미디어 공용, CC BY 2.0.
https://commons.wikimedia.org/wiki/File:A-novel-walking-speed-estimation-scheme-and-its-application-to-treadmill-control-for-gait-1743-0003-9-62-S1.ogv

자기 영상을 써도 됩니다. 사람의 온몸이 보이고 발이 화면 안에 들어오는 영상이 잘 잡힙니다.
