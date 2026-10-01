/*
 * 대시보드 동작.
 *
 * 하는 일은 셋뿐이다.
 *   1. 서버가 0.2초마다 보내 주는 상태를 받는다 (WebSocket)
 *   2. 그 값을 화면에 그린다 (draw 함수 하나)
 *   3. 슬라이더를 움직이면 서버에 보낸다
 */

const $ = (id) => document.getElementById(id);
const SLIDERS = ["volume", "note_seconds", "fade_seconds", "max_voices"];
let dragging = false; // 슬라이더를 잡고 있는 동안에는 서버 값으로 되돌리지 않는다

/* ── 밝기 ─────────────────────────────────────────────── */
const themes = ["auto", "light", "dark"];
const themeNames = { auto: "밝기 자동", light: "밝게", dark: "어둡게" };

function applyTheme(name) {
  const dark = name === "dark" || (name === "auto" && matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.classList.toggle("dark", dark);
  $("theme").textContent = themeNames[name];
  try { localStorage.setItem("theme", name); } catch (e) { /* 저장이 막혀 있어도 그냥 쓴다 */ }
}

let theme = "auto";
try { theme = localStorage.getItem("theme") || "auto"; } catch (e) { /* 무시 */ }
applyTheme(theme);
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => applyTheme(theme));
$("theme").addEventListener("click", () => {
  theme = themes[(themes.indexOf(theme) + 1) % themes.length];
  applyTheme(theme);
});

/* ── 소리 듣기 ─────────────────────────────────────────────
 * 서버에 스피커가 없거나 멀리서 볼 때, 소리를 이 브라우저로 받아 듣는다.
 * 브라우저는 사람이 단추를 눌러야 소리를 내 준다. 그래서 단추가 있다.
 */
let audioCtx = null;
let audioWs = null;
let playAt = 0;

function note(text) {
  const el = $("listen-note");
  if (el) el.textContent = text;
}

async function startListening() {
  try {
    // 44100 을 못 쓰는 기기가 있다. 그럴 때는 기본값으로 연다.
    try {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 44100 });
    } catch (e) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    // 브라우저는 소리를 멈춘 채로 열어 준다. 사람이 누른 지금 깨운다.
    if (audioCtx.state !== "running") await audioCtx.resume();
  } catch (e) {
    note("이 브라우저가 소리를 열지 못했습니다: " + e.message);
    return;
  }

  playAt = audioCtx.currentTime + 0.4; // 앞서 잡아 두는 만큼 네트워크가 흔들려도 버틴다
  audioWs = new WebSocket(`ws://${location.host}/audio`);
  audioWs.binaryType = "arraybuffer";

  audioWs.onopen = () => note("소리를 받는 중입니다");
  audioWs.onerror = () => note("소리 통로를 열지 못했습니다");
  audioWs.onmessage = (event) => {
    if (typeof event.data === "string") return; // 첫 줄은 설정값이다
    if (!audioCtx) return;
    if (audioCtx.state !== "running") audioCtx.resume();
    const pcm = new Int16Array(event.data);
    const frames = pcm.length / 2;
    if (!frames) return;
    const buffer = audioCtx.createBuffer(2, frames, 44100);
    const left = buffer.getChannelData(0);
    const right = buffer.getChannelData(1);
    for (let i = 0; i < frames; i++) {
      left[i] = pcm[i * 2] / 32768;
      right[i] = pcm[i * 2 + 1] / 32768;
    }
    const source = audioCtx.createBufferSource();
    source.buffer = buffer;
    source.connect(audioCtx.destination);
    const now = audioCtx.currentTime;
    if (playAt < now + 0.08) playAt = now + 0.4; // 밀렸으면 여유를 다시 확보한다
    source.start(playAt);
    playAt += buffer.duration;
  };
  audioWs.onclose = () => stopListening();

  $("listen").textContent = "소리 끄기";
  $("listen").classList.add("on");
}

function stopListening() {
  if (audioWs) { audioWs.onclose = null; audioWs.close(); audioWs = null; }
  if (audioCtx) { audioCtx.close(); audioCtx = null; }
  note("");
  $("listen").textContent = "소리 듣기";
  $("listen").classList.remove("on");
}

$("listen").addEventListener("click", () => (audioWs ? stopListening() : startListening()));

/* ── 서버에 값 보내기 ──────────────────────────────────── */
function send(body) {
  fetch("/api/params", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

SLIDERS.forEach((key) => {
  const el = $(key);
  el.addEventListener("pointerdown", () => (dragging = true));
  el.addEventListener("pointerup", () => (dragging = false));
  el.addEventListener("input", () => {
    $(key + "-v").textContent = el.value;
    send({ [key]: Number(el.value) });
  });
});

$("toggle").addEventListener("click", () => send({ running: $("toggle").dataset.paused === "yes" }));

/* ── 화면 그리기 ───────────────────────────────────────── */
function badge(text, tone) {
  return `<span class="badge" style="${tone ? `color:${tone};border-color:${tone}` : ""}">${text}</span>`;
}

function drawChips(s) {
  const engineOn = s.engine === "dicy2" && /붙었습니다/.test(s.engine_note || "");
  const engineText = s.engine === "dicy2" ? (engineOn ? "dicy2 연결됨" : "dicy2 기다리는 중") : "규칙으로 고름";
  $("chips").innerHTML =
    badge(engineText, s.engine === "dicy2" ? (engineOn ? "var(--step-engine)" : "var(--step-rule)") : "") +
    badge(s.vision.source + (s.vision.fps ? ` ${s.vision.fps}fps` : "")) +
    badge(s.running ? "소리 켜짐" : "소리 멈춤", s.running ? "" : "var(--step-rule)");
}

function drawFloor(s) {
  const floor = $("floor");
  floor.querySelectorAll(".walker").forEach((n) => n.remove());
  if (!s.tracks.length) {
    floor.insertAdjacentHTML(
      "beforeend",
      `<div class="walker" style="left:50%;top:70px"><div class="who">아직 아무도 없습니다</div></div>`
    );
    return;
  }
  s.tracks.forEach((t, i) => {
    floor.insertAdjacentHTML(
      "beforeend",
      `<div class="walker" style="left:${(t.x * 100).toFixed(1)}%;top:${24 + (i % 3) * 36}px">
         <div class="dot"></div>
         <div class="slice">${t.slice || "―"}</div>
         <div class="who">${t.track}번 · ${t.steps}걸음</div>
       </div>`
    );
  });
}

function drawVoices(s) {
  $("voices-list").innerHTML = s.sounding.length
    ? s.sounding
        .map(
          (v) => `<li class="${v.fading ? "fading" : ""}">
            <span>${v.slice}</span>
            <span class="bar"><i style="width:${(v.left * 100).toFixed(0)}%"></i></span>
            <span class="who">${v.track}번</span>
          </li>`
        )
        .join("")
    : `<li><span class="quiet">조용합니다</span></li>`;
}

function drawLog(s) {
  $("log").innerHTML = s.log
    .map((row) => {
      let kind = "";
      if (/dicy2 가 고름/.test(row.text)) kind = "engine";
      else if (/어울림|규칙으로 메움/.test(row.text)) kind = "rule";
      return `<li class="${kind}"><i class="dot"></i><time>${row.t}</time><span>${row.text}</span></li>`;
    })
    .join("");
}

/* 카메라 화면은 보일 때만 받아 온다. 가짜 관객 모드에서는 칸 자체를 숨긴다. */
let cameraOn = false;

function drawCamera(s) {
  const card = $("camera-card");
  if (!s.vision.camera) {
    card.hidden = true;
    if (cameraOn) {
      $("camera").removeAttribute("src");
      cameraOn = false;
    }
    return;
  }
  card.hidden = false;
  if (!cameraOn) {
    $("camera").src = "/camera";
    cameraOn = true;
  }
}

function draw(s) {
  $("corpus-line").textContent = `${s.corpus.name} · 조각 ${s.corpus.slices}개`;
  $("people").textContent = s.people;
  $("voices").textContent = s.voices;
  $("steps").textContent = s.steps;
  $("uptime").textContent = Math.floor(s.uptime / 60) + "분";
  $("peak").style.width = Math.min(100, s.peak * 100) + "%";
  $("peaknum").textContent = s.peak.toFixed(2);
  $("vision-note").textContent = s.vision.note;
  $("engine-note").textContent = s.engine_note || "";

  drawChips(s);
  drawCamera(s);
  drawFloor(s);
  drawVoices(s);
  drawLog(s);

  if (!dragging) {
    SLIDERS.forEach((key) => {
      $(key).value = s.params[key];
      $(key + "-v").textContent = s.params[key];
    });
  }
  $("toggle").textContent = s.running ? "소리 멈추기" : "소리 켜기";
  $("toggle").dataset.paused = s.running ? "no" : "yes";
}

/* ── 연결 ──────────────────────────────────────────────────
 * 평소에는 WebSocket 으로 받는다. 그게 안 되는 환경이면(uvicorn 에 websockets 가
 * 없을 때 등) 0.4초마다 물어보는 쪽으로 저절로 바꾼다. 화면은 어느 쪽이든 뜬다.
 */
let polling = null;

function startPolling() {
  if (polling) return;
  polling = setInterval(async () => {
    try {
      draw(await (await fetch("/api/state")).json());
    } catch (e) {
      /* 서버가 꺼진 것이다. 다음 번에 다시 해 본다 */
    }
  }, 400);
}

function stopPolling() {
  if (polling) {
    clearInterval(polling);
    polling = null;
  }
}

function connect() {
  let opened = false;
  const ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onopen = () => {
    opened = true;
    stopPolling();
  };
  ws.onmessage = (event) => draw(JSON.parse(event.data));
  ws.onclose = () => {
    if (!opened) startPolling();
    setTimeout(connect, 3000);
  };
  ws.onerror = () => ws.close();
}
connect();
