"""
감지 — 누가 들어왔고, 어디 있고, 언제 발이 닿았는지.

내보내는 것은 네 가지뿐이다.

  enter(track)        사람이 들어왔다
  step(track, x)      발이 바닥에 닿았다. x 는 화면 좌우 위치(0~1)
  move(track, x)      그 사람이 지금 어디 있는지
  leave(track)        사람이 나갔다

카메라가 없거나 --sim 으로 돌리면 가짜 사람들이 걸어 다닌다. 소리와 대시보드를
장비 없이 만들어 보려고 둔 것이다.
"""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass
from typing import Callable

from . import settings

Emit = Callable[[str, int, float], None]


@dataclass
class VisionStatus:
    source: str = "sim"
    people: int = 0
    note: str = ""
    fps: float = 0.0
    # 대시보드가 「카메라가 보는 것」을 열면 want 가 켜지고, 그때만 그림을 그려 보낸다.
    want_preview: bool = False
    jpeg: bytes = b""


class SimVision:
    """가짜 관객. 들어오고, 걷고, 나간다."""

    def __init__(self, emit: Emit, status: VisionStatus, max_people: int = settings.SIM_MAX_PEOPLE):
        self.emit = emit
        self.status = status
        self.max_people = max_people
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self.status.source = "시뮬레이션"
        self.status.note = "가짜 관객이 걷는 중"
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def tick(self, now: float, walkers: dict) -> None:
        """시간 한 칸을 진행한다. --offline 에서는 이 함수만 불러 쓴다."""
        rnd = random.Random(int(now * 1000) % 100000)
        if len(walkers) < self.max_people and rnd.random() < settings.SIM_ENTER_CHANCE:
            track = (max(walkers) + 1) if walkers else 1
            walkers[track] = {"x": rnd.random(), "dir": rnd.choice([-1, 1]), "next": now + 0.3, "until": now + rnd.uniform(*settings.SIM_STAY)}
            self.emit("enter", track, walkers[track]["x"])
        for track in list(walkers):
            w = walkers[track]
            w["x"] += w["dir"] * settings.SIM_SPEED
            if not 0.05 < w["x"] < 0.95:
                w["dir"] *= -1
                w["x"] = min(max(w["x"], 0.05), 0.95)
            self.emit("move", track, w["x"])
            if now >= w["next"]:
                self.emit("step", track, w["x"])
                w["next"] = now + rnd.uniform(*settings.SIM_STEP_GAP)
            if now >= w["until"]:
                self.emit("leave", track, w["x"])
                del walkers[track]
        self.status.people = len(walkers)

    def _run(self) -> None:
        walkers: dict = {}
        t0 = time.time()
        while not self._stop.is_set():
            self.tick(time.time() - t0, walkers)
            time.sleep(0.03)


class CameraVision:
    """웹캠 + MediaPipe. 발목이 내려갔다 멈추는 순간을 걸음으로 본다.

    모델 파일이 필요하다. 설치 스크립트가 받아 두고, 없으면 여기서 받는다.
      https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task

    camera 자리에 영상 파일 경로를 주면 그 영상을 카메라처럼 쓴다. 카메라가 없는 컴퓨터나
    전시 전에 걷는 영상으로 시험할 때 쓴다. 영상이 끝나면 처음부터 다시 돈다.
    """

    def __init__(self, emit: Emit, status: VisionStatus, max_people: int = settings.MAX_PEOPLE,
                 camera: int | str = 0, model: str = ""):
        self.emit = emit
        self.status = status
        self.max_people = max_people
        self.camera = camera
        self.is_file = isinstance(camera, str)
        self.model = model or settings.POSE_MODEL
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        try:
            import cv2  # type: ignore
            import mediapipe as mp  # type: ignore
            from mediapipe.tasks import python as mp_python  # type: ignore
            from mediapipe.tasks.python import vision as mp_vision  # type: ignore
        except Exception as exc:
            self.status.source = "카메라 없음"
            self.status.note = f"mediapipe·opencv 를 불러오지 못했습니다 ({exc}). --sim 으로 돌려 보세요."
            return

        try:
            options = mp_vision.PoseLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=self.model),
                running_mode=mp_vision.RunningMode.VIDEO,
                num_poses=self.max_people,
                # 문턱을 낮추면 여러 명이 있을 때 덜 놓친다. settings.py 에서 바꾼다.
                min_pose_detection_confidence=settings.POSE_CONFIDENCE,
                min_pose_presence_confidence=settings.POSE_CONFIDENCE,
            )
            landmarker = mp_vision.PoseLandmarker.create_from_options(options)
        except Exception as exc:
            self.status.source = "카메라 없음"
            self.status.note = f"모델 파일({self.model})을 찾지 못했습니다 ({exc})"
            return

        def draw_preview(frame, poses, marks: dict) -> None:
            """카메라 화면에 다리와 발목을 그린다. 무엇을 보고 걸음으로 세는지 눈에 보이게."""
            small = cv2.resize(frame, (480, int(480 * frame.shape[0] / frame.shape[1])))
            h, w = small.shape[:2]
            for track, pose in enumerate(poses):
                pt = lambda i: (int(pose[i].x * w), int(pose[i].y * h))  # noqa: E731
                for a, b in ((23, 25), (25, 27), (24, 26), (26, 28), (23, 24)):
                    cv2.line(small, pt(a), pt(b), (180, 180, 180), 2)
                for ankle in (27, 28):
                    cv2.circle(small, pt(ankle), 7, (120, 200, 90), 2)
                hip = ((pose[23].x + pose[24].x) / 2, (pose[23].y + pose[24].y) / 2)
                cv2.circle(small, (int(hip[0] * w), int(hip[1] * h)), 5, (230, 170, 60), -1)
                # 방금 걸음으로 센 발목에는 꽉 찬 동그라미를 잠깐 둔다
                if marks.get(track, 0) > time.time() - 0.4:
                    for ankle in (27, 28):
                        cv2.circle(small, pt(ankle), 11, (90, 230, 230), 3)
                cv2.putText(small, f"#{track}", (int(hip[0] * w) + 8, int(hip[1] * h) - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (230, 170, 60), 1, cv2.LINE_AA)
            ok, buf = cv2.imencode(".jpg", small, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
            if ok:
                self.status.jpeg = buf.tobytes()

        last_preview = 0.0
        step_marks: dict[int, float] = {}

        cap = cv2.VideoCapture(self.camera)
        if not cap.isOpened():
            self.status.source = "카메라 없음"
            self.status.note = ("영상 파일을 열지 못했습니다" if self.is_file else "웹캠을 열지 못했습니다")
            return

        self.status.source = "영상 파일" if self.is_file else "웹캠"
        self.status.note = "사람을 찾는 중"
        # 영상은 원래 속도로 돌린다. 안 그러면 걸음이 뭉쳐서 들어온다.
        frame_gap = 1.0 / max(cap.get(cv2.CAP_PROP_FPS) or 25.0, 1.0) if self.is_file else 0.0
        prev_ankle: dict[int, float] = {}
        going_down: dict[int, bool] = {}
        last_step: dict[int, float] = {}
        seen: set[int] = set()
        t0 = time.time()
        frames = 0

        while not self._stop.is_set():
            ok, frame = cap.read()
            if not ok:
                if self.is_file:  # 영상이 끝났다. 처음부터 다시 돈다
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                time.sleep(0.05)
                continue
            if frame_gap:
                time.sleep(frame_gap)
            frames += 1
            now = time.time()
            self.status.fps = frames / max(now - t0, 1e-6)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect_for_video(image, int(now * 1000))

            alive: set[int] = set()
            for track, pose in enumerate(result.pose_landmarks or []):
                alive.add(track)
                if track not in seen:
                    seen.add(track)
                    self.emit("enter", track, 0.5)
                # 27·28 이 발목이다. 화면 좌우 위치는 엉덩이(23·24) 평균으로 본다.
                ankle = max(pose[27].y, pose[28].y)
                x = float((pose[23].x + pose[24].x) / 2)
                self.emit("move", track, x)
                prev = prev_ankle.get(track, ankle)
                if ankle > prev + settings.ANKLE_DROP:
                    going_down[track] = True
                elif going_down.get(track) and ankle < prev + settings.ANKLE_SETTLE:
                    if now - last_step.get(track, 0) > settings.STEP_MIN_GAP:
                        self.emit("step", track, x)
                        last_step[track] = now
                        step_marks[track] = now
                    going_down[track] = False
                prev_ankle[track] = ankle

            for track in list(seen - alive):
                self.emit("leave", track, 0.5)
                seen.discard(track)
            self.status.people = len(alive)

            # 보는 사람이 있을 때만 그린다. 초당 열두 장이면 충분하다.
            if self.status.want_preview and now - last_preview > 1 / 12:
                last_preview = now
                draw_preview(frame, result.pose_landmarks or [], step_marks)

        cap.release()
