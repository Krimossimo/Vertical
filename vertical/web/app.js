/* Vertical — interface (vanilla JS, aucune étape de build) */
"use strict";

const S = {
  status: null, settings: null, profiles: [], layouts: [], fonts: [], version: "",
  project: null, tab: "analyse", sel: null, job: null, poll: null,
  video: null, videoPid: null, useProxy: false, exportResult: null,
};
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const main = () => $("#main");
const KOFI = "https://ko-fi.com/krimossimo";

/* ------------------------------------------------------------------ langue */
let LANG = (() => { try { return localStorage.getItem("vx.lang") || "en"; } catch (_) { return "en"; } })();
/** Texte bilingue : anglais par défaut, français si choisi dans les réglages. */
function T(en, fr) { return LANG === "fr" && fr != null ? fr : en; }
function plural(n, en1, enN, fr1, frN) { return n > 1 ? T(enN, frN) : T(en1, fr1); }
function setLang(l) { LANG = l === "fr" ? "fr" : "en"; document.documentElement.lang = LANG; try { localStorage.setItem("vx.lang", LANG); } catch (_) { } }
function setAccent(a) { document.documentElement.dataset.accent = a || "iris"; try { localStorage.setItem("vx.accent", a || "iris"); } catch (_) { } }
const ACCENTS = [["iris", "#8B7CFF", "#C26CFF"], ["ocean", "#4C9BFF", "#38D3F5"], ["mint", "#2FCB9A", "#8BE36B"],
  ["sunset", "#FF7A59", "#FFB547"], ["rose", "#FF5C93", "#FF8BD0"], ["mono", "#E8E9EF", "#A9ADBD"]];
const LAYOUT_NAMES = {
  facecam_fixed: ["Facecam on top + fixed game", "Facecam en haut + jeu fixe"],
  facecam_top: ["Facecam on top + game follows the action", "Facecam en haut + jeu qui suit l'action"],
  smart_crop: ["Full screen, follows the action", "Plein écran, suit l'action"],
  center_crop: ["Full screen, fixed frame", "Plein écran, cadre fixe"],
  blur_fill: ["Whole picture + blurred background", "Image entière + fond flou"],
};
function layoutName(k) { const n = LAYOUT_NAMES[k]; return n ? T(n[0], n[1]) : k; }
function catName(c) { return c.category_ui || c.category_label || c.category || ""; }
function reasonsOf(c) { return c.reasons_ui || c.reasons || []; }
function profName(pr) { return LANG === "fr" ? pr.name : (pr.name_en || pr.name); }

/* ------------------------------------------------------------------ icônes */
const ICONS = {
  folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  film: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4"/>',
  reimport: '<path d="M9 14 4 9l5-5"/><path d="M4 9h11a5 5 0 0 1 0 10h-3"/>',
  sliders: '<path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1"/><circle cx="15" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="17" cy="18" r="2"/>',
  heart: '<path d="M19.5 12.6 12 20l-7.5-7.4A4.8 4.8 0 0 1 12 6.3a4.8 4.8 0 0 1 7.5 6.3z"/>',
  coffee: '<path d="M4 9h13v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M17 10h1.5a2.5 2.5 0 0 1 0 5H17"/><path d="M8 2.5v3M12 2.5v3"/>',
  keyboard: '<rect x="2.5" y="6" width="19" height="12" rx="2"/><path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M7 14h10"/>',
  check: '<path d="M20 6 9 17l-5-5"/>', x: '<path d="M18 6 6 18M6 6l12 12"/>',
  left: '<path d="m15 18-6-6 6-6"/>', right: '<path d="m9 18 6-6-6-6"/>',
  arrowR: '<path d="M5 12h14M13 6l6 6-6 6"/>', arrowL: '<path d="M19 12H5M11 6l-6 6 6 6"/>',
  play: '<path d="M7 4.5v15a1 1 0 0 0 1.5.86l12.4-7.5a1 1 0 0 0 0-1.72L8.5 3.64A1 1 0 0 0 7 4.5z"/>',
  pause: '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>',
  replay: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>', search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  captions: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 15h4M14 15h3M7 11h2M12 11h5"/>',
  crop: '<path d="M6 2v14a2 2 0 0 0 2 2h14"/><path d="M18 22V8a2 2 0 0 0-2-2H2"/>',
  webcam: '<circle cx="12" cy="10" r="7"/><circle cx="12" cy="10" r="3"/><path d="M8 21h8M12 17v4"/>',
  phone: '<rect x="7" y="2" width="10" height="20" rx="2.5"/><path d="M11 18h2"/>',
  edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
  trash: '<path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  star: '<path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1 6.2L12 17.3 6.5 20.2l1-6.2L3 9.6l6.2-.9z"/>',
  sparkles: '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
  download: '<path d="M12 3v12M7 10l5 5 5-5"/><path d="M5 21h14"/>',
  copy: '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1"/>',
  external: '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
  file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>',
  wand: '<path d="M15 4V2M15 10V8M11 6H9M21 6h-2M18.4 3.6 17 5M18.4 8.4 17 7"/><path d="m3 21 11-11"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
  mic: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>',
  volume: '<path d="M11 5 6 9H3v6h3l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13"/>',
  gamepad: '<rect x="2" y="7" width="20" height="11" rx="5"/><path d="M7 11v3M5.5 12.5h3M15 12h.01M18 13h.01"/>',
  cpu: '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9.5" y="9.5" width="5" height="5"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
  scissors: '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M20 4 8.1 15.9M14.5 14.5 20 20M8.1 8.1 12 12"/>',
  alert: '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 16v-5M12 8h.01"/>',
  eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  image: '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-5-5L5 21"/>',
  type: '<path d="M4 7V5h16v2M9 19h6M12 5v14"/>', video: '<rect x="2" y="6" width="14" height="12" rx="2"/><path d="m16 10 6-3v10l-6-3z"/>',
  zap: '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>', timer: '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2M9 2h6"/>',
  droplet: '<path d="M12 3s7 7.5 7 12a7 7 0 0 1-14 0c0-4.5 7-12 7-12z"/>',
  bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10 21a2 2 0 0 0 4 0"/>',
  refresh: '<path d="M21 12a9 9 0 0 1-15.5 6.2L3 16"/><path d="M3 12a9 9 0 0 1 15.5-6.2L21 8"/><path d="M21 3v5h-5M3 21v-5h5"/>',
  listcheck: '<path d="M3 6h11M3 12h11M3 18h7"/><path d="m15 17 2 2 4-4"/>', hash: '<path d="M5 9h14M5 15h14M10 3 8 21M16 3l-2 18"/>',
  layers: '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>', tag: '<path d="M3 12V4a1 1 0 0 1 1-1h8l9 9-9 9z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
  undo: '<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>', home: '<path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10"/>',
  flag: '<path d="M4 22V4M4 4h13l-2 4 2 4H4"/>', github: '<path d="M9 19c-4 1.5-4-2-6-2.5M15 22v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12 12 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V22"/>',
};
const FILLED = new Set(["play", "pause"]);
function ic(name, cls = "") { return `<svg class="i ${FILLED.has(name) ? "fill" : ""} ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ""}</svg>`; }

/* ------------------------------------------------------------------ utilitaires */
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function fmt(t) {
  t = Math.max(0, Math.round(t || 0));
  const h = Math.floor(t / 3600), m = Math.floor(t % 3600 / 60), s = t % 60;
  return h ? `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}` : `${m}:${String(s).padStart(2, "0")}`;
}
function fmtP(t) {
  t = Math.max(0, t || 0);
  const m = Math.floor(t / 60), s = (t % 60).toFixed(1).padStart(4, "0");
  const h = Math.floor(m / 60);
  return h ? `${h}:${String(m % 60).padStart(2, "0")}:${s}` : `${m}:${s}`;
}
function fmtDur(s) {
  if (s == null) return "";
  s = Math.round(s);
  if (s < 60) return `${s} s`;
  const m = Math.floor(s / 60);
  return m >= 60 ? `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")}` : `${m} min ${String(s % 60).padStart(2, "0")}`;
}
async function api(method, url, body) {
  const opt = { method, headers: {} };
  if (body !== undefined) { opt.body = JSON.stringify(body); opt.headers["Content-Type"] = "application/json"; }
  const r = await fetch(url, opt);
  let data = null;
  try { data = await r.json(); } catch (_) { }
  if (!r.ok) throw new Error((data && data.error) || T(`Error ${r.status}`, `Erreur ${r.status}`));
  return data;
}
function toast(msg, kind = "") {
  const el = document.createElement("div");
  el.className = "toast " + kind;
  el.innerHTML = `<span class="ti">${ic(kind === "err" ? "x" : kind === "ok" ? "check" : "info")}</span><span></span>`;
  el.lastChild.textContent = String(msg).replace(/\s*[✓✔]\s*$/, "");
  $("#toasts").appendChild(el);
  setTimeout(() => { el.classList.add("out"); setTimeout(() => el.remove(), 300); }, kind === "err" ? 7000 : 3500);
}
function modal(title, body, { wide = false, footer = "", cls = "", flush = false } = {}) {
  const bg = document.createElement("div");
  bg.className = "modal-bg";
  bg.innerHTML = `<div class="modal ${wide ? "wide" : ""} ${cls}" role="dialog"><div class="mh"><h2>${title}</h2><button class="iconbtn" data-x title="${T("Close", "Fermer")} (Esc)">${ic("x")}</button></div>
    <div class="mb ${flush ? "flush" : ""}">${body}</div>${footer ? `<div class="mf">${footer}</div>` : ""}</div>`;
  document.body.appendChild(bg);
  const onKey = e => { if (e.key === "Escape" && $$(".modal-bg").pop() === bg) close(); };
  const close = () => { bg.remove(); document.removeEventListener("keydown", onKey); };
  document.addEventListener("keydown", onKey);
  bg.addEventListener("mousedown", e => { if (e.target === bg) close(); });
  $("[data-x]", bg).onclick = close;
  return { el: bg, close };
}
async function copyText(text) {
  try { await navigator.clipboard.writeText(text); return true; } catch (_) {
    const ta = document.createElement("textarea");
    ta.value = text; document.body.appendChild(ta); ta.select();
    const ok = document.execCommand("copy"); ta.remove(); return ok;
  }
}
function scoreClass(s) { return s == null ? "s-lo" : s >= 70 ? "s-hi" : s >= 45 ? "s-md" : "s-lo"; }
function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
function confirmBox(text, { ok = T("Confirm", "Confirmer"), danger = false } = {}) {
  return new Promise(res => {
    const m = modal(T("Please confirm", "Confirmation"), `<div class="muted" style="font-size:14px">${text}</div>`,
      { footer: `<button class="btn ghost" id="cfNo">${T("Cancel", "Annuler")}</button><button class="btn ${danger ? "danger" : "primary"}" id="cfOk">${ok}</button>` });
    let done = false;
    const fin = v => { if (done) return; done = true; m.close(); res(v); };
    $("#cfOk", m.el).onclick = () => fin(true); $("#cfNo", m.el).onclick = () => fin(false);
    new MutationObserver((_, o) => { if (!document.body.contains(m.el)) { o.disconnect(); fin(false); } }).observe(document.body, { childList: true });
    setTimeout(() => $("#cfOk", m.el).focus(), 30);
  });
}
/* remplissage coloré des curseurs */
function paintRange(r) { const p = ((r.value - r.min) / ((r.max - r.min) || 1)) * 100; r.style.setProperty("--p", p + "%"); }
document.addEventListener("input", e => { if (e.target.type === "range") paintRange(e.target); });
new MutationObserver(() => $$('input[type=range]').forEach(r => { if (!r.dataset.pr) { r.dataset.pr = 1; paintRange(r); } })).observe(document.documentElement, { childList: true, subtree: true });
/* effet « ripple » sur les boutons */
document.addEventListener("pointerdown", e => {
  const b = e.target.closest(".btn"); if (!b || b.disabled || b.classList.contains("pp")) return;
  const r = b.getBoundingClientRect(), d = Math.max(r.width, r.height), s = document.createElement("span");
  s.className = "ripple"; Object.assign(s.style, { width: d + "px", height: d + "px", left: e.clientX - r.left - d / 2 + "px", top: e.clientY - r.top - d / 2 + "px" });
  b.appendChild(s); setTimeout(() => s.remove(), 650);
});
/* son discret + notification quand une longue tâche se termine */
function chime(ok = true) {
  if (!S.settings || S.settings.sound === false) return;
  try {
    const ac = new (window.AudioContext || window.webkitAudioContext)(), t = ac.currentTime;
    (ok ? [660, 880, 1320] : [440, 330]).forEach((f, i) => {
      const o = ac.createOscillator(), g = ac.createGain();
      o.type = "sine"; o.frequency.value = f; o.connect(g); g.connect(ac.destination);
      g.gain.setValueAtTime(0, t + i * .11); g.gain.linearRampToValueAtTime(.12, t + i * .11 + .02); g.gain.exponentialRampToValueAtTime(.0001, t + i * .11 + .5);
      o.start(t + i * .11); o.stop(t + i * .11 + .55);
    });
  } catch (_) { }
  if (document.hidden && "Notification" in window && Notification.permission === "granted") {
    try { new Notification("Vertical", { body: ok ? T("Task finished", "Tâche terminée") : T("Task failed", "Tâche en échec"), icon: "/static/icon.svg" }); } catch (_) { }
  }
}

/* ------------------------------------------------------------------ routage */
function go(hash) { if (location.hash !== hash) location.hash = hash; else route(); }
window.addEventListener("hashchange", route);
async function route() {
  stopPoll();
  $$(".modal-bg").forEach(m => m.remove());
  const m = location.hash.match(/^#\/p\/([a-z0-9-]+)(?:\/(\w+))?/);
  if (m) {
    S.tab = m[2] || null;
    await openProject(m[1]);
  } else {
    S.project = null;
    renderHome();
  }
}

/* ------------------------------------------------------------------ démarrage : écran de chargement */
function splashMsg(t) { const el = $("#spMsg"); if (el) { el.style.opacity = 0; setTimeout(() => { el.textContent = t; el.style.opacity = 1; }, 150); } }
function hideSplash() { const sp = $("#splash"); if (sp) { sp.classList.add("out"); setTimeout(() => sp.remove(), 700); } }
async function boot() {
  $("#spTag").textContent = T("Your best Twitch moments, ready for Shorts", "Tes meilleurs moments Twitch, prêts pour les Shorts");
  splashMsg(T("Starting the engine…", "Démarrage du moteur…"));
  const t0 = Date.now();
  let st = null, tries = 0;
  while (true) {
    try {
      st = await api("GET", "/api/status?ollama=0");
      if (!S.settings) applyStatus(st);
      if (st.ready || Date.now() - t0 > 30000) break;
      splashMsg(tries++ < 2 ? T("Checking your GPU, FFmpeg and AI models…", "Vérification du GPU, de FFmpeg et des modèles d'IA…")
        : T("Almost ready…", "Presque prêt…"));
    } catch (e) { splashMsg(T("Waiting for the local server…", "En attente du serveur local…")); }
    await new Promise(r => setTimeout(r, 450));
  }
  applyStatus(st);
  splashMsg(T("Loading your projects…", "Chargement de tes projets…"));
  const wait = Math.max(0, 900 - (Date.now() - t0));
  setTimeout(() => {
    hideSplash();
    route();
    if (!S.settings.welcomed) setTimeout(openWelcome, 250);
  }, wait);
  setTimeout(refreshStatus, 1500); // état d'Ollama, sans bloquer le démarrage
}
function applyStatus(st) {
  if (!st) return;
  Object.assign(S, { status: st.env, settings: st.settings, profiles: st.profiles, layouts: st.layouts, fonts: st.fonts, version: st.version });
  if (st.settings.ui_lang && st.settings.ui_lang !== LANG) setLang(st.settings.ui_lang);
  setAccent(st.settings.accent);
  renderChrome();
}
async function refreshStatus() {
  try { const st = await api("GET", "/api/status"); Object.assign(S, { status: st.env }); renderPills(); } catch (_) { }
}
function renderChrome() {
  $("#goHome").onclick = () => go("#/");
  $("#goHome").title = T("Home", "Accueil");
  const b = (id, icon, title, fn) => { const el = $(id); el.innerHTML = ic(icon, "lg"); el.title = title; el.onclick = fn; };
  b("#btnKeys", "keyboard", T("Keyboard shortcuts (?)", "Raccourcis clavier (?)"), openKeys);
  b("#btnSettings", "sliders", T("Settings", "Réglages"), () => openSettings());
  b("#btnAbout", "heart", T("About Vertical", "À propos de Vertical"), openAbout);
  renderPills();
}
function renderPills() {
  const e = S.status;
  if (!e) { $("#envPills").innerHTML = `<span class="pill wait"><span class="dot"></span>${T("Checking system…", "Vérification…")}</span>`; return; }
  const issues = [], warns = [];
  if (!e.ffmpeg || !e.ffmpeg.available) issues.push("FFmpeg");
  if (!e.faster_whisper) issues.push("Whisper");
  if (!(e.gpu && e.gpu.cuda)) warns.push("GPU");
  if (!(e.torch && e.transformers)) warns.push(T("AI", "IA"));
  const kind = issues.length ? "bad" : warns.length ? "warn" : "ok";
  const gpu = e.gpu && e.gpu.cuda ? e.gpu.name.replace("NVIDIA GeForce ", "") : T("CPU only", "CPU uniquement");
  const label = issues.length ? T(`${issues.join(", ")} missing`, `${issues.join(", ")} absent`) : gpu;
  $("#envPills").innerHTML = `<span class="pill ${kind}" title="${T("System diagnostics", "Diagnostic du système")}"><span class="dot"></span>${esc(label)}${e.ffmpeg && e.ffmpeg.nvenc ? " · NVENC" : ""}${e.ollama && e.ollama.running ? " · Ollama" : ""}</span>`;
  $$("#envPills .pill").forEach(p => p.onclick = openEnv);
}
function crumb(html) { $("#crumb").innerHTML = html; }
function projCrumb() { const p = S.project; crumb(p ? `${ic("right")}<b title="${esc(p.vod_path)}">${esc(p.name)}</b>` : ""); }

/* ------------------------------------------------------------------ bienvenue */
function openWelcome() {
  let lang = LANG, accent = (S.settings && S.settings.accent) || "iris";
  const bg = document.createElement("div");
  bg.className = "welcome-bg";
  const draw = () => {
    bg.innerHTML = `<div class="welcome">
      <div class="wh"><img src="/static/icon.svg" alt=""><div class="dim small" style="font-weight:600;letter-spacing:1px;text-transform:uppercase">${T("Welcome to", "Bienvenue dans")} Vertical</div></div>
      <div style="display:grid;gap:14px"><h1>${T("Turn hours of streaming into", "Transforme des heures de live en")} <span class="grad">${T("Shorts that hit.", "Shorts qui claquent.")}</span></h1>
        <p class="lead">${T("Vertical watches and listens to your VODs, finds your best reactions and exports polished 9:16 clips with animated subtitles — 100% on your PC, free, no subscription.",
          "Vertical regarde et écoute tes VODs, trouve tes meilleures réactions et exporte des clips 9:16 soignés avec sous-titres animés — 100 % sur ton PC, gratuit, sans abonnement.")}</p></div>
      <div class="wsteps">
        <div class="wstep"><div class="ico">${ic("film")}</div><b>${T("1 · Drop a VOD", "1 · Choisis une VOD")}</b><span>${T("Any length. Whisper transcribes, AI spots fights, deaths, wins and laughs.", "N'importe quelle durée. Whisper transcrit, l'IA repère combats, morts, victoires et rires.")}</span></div>
        <div class="wstep"><div class="ico">${ic("listcheck")}</div><b>${T("2 · Review", "2 · Trie")}</b><span>${T("Accept or reject each moment, trim it, fix subtitles in one click.", "Valide ou rejette chaque moment, ajuste-le, corrige les sous-titres en un clic.")}</span></div>
        <div class="wstep"><div class="ico">${ic("phone")}</div><b>${T("3 · Export", "3 · Exporte")}</b><span>${T("Facecam layout, smart crop, titles & hashtags for YouTube, TikTok and Reels.", "Facecam, recadrage intelligent, titres et hashtags pour YouTube, TikTok et Reels.")}</span></div>
      </div>
      <div class="wpick">
        <div class="grp"><h3>${T("Language", "Langue")}</h3><div class="langs">
          <div class="lang ${lang === "en" ? "on" : ""}" data-l="en"><span class="fl">EN</span>English</div>
          <div class="lang ${lang === "fr" ? "on" : ""}" data-l="fr"><span class="fl">FR</span>Français</div></div></div>
        <div class="grp"><h3>${T("Accent color", "Couleur d'accent")}</h3><div class="swatches">${ACCENTS.map(([k, a, b]) => `<div class="sw ${accent === k ? "on" : ""}" data-a="${k}" title="${k}" style="background:linear-gradient(135deg,${a},${b})"></div>`).join("")}</div></div>
        <button class="btn primary big" id="wGo">${T("Get started", "C'est parti")} ${ic("arrowR")}</button>
      </div>
      <div class="small dim">${T("You can change all of this later in Settings.", "Tu pourras tout changer plus tard dans les Réglages.")}</div>
    </div>`;
    $$(".lang", bg).forEach(el => el.onclick = () => { lang = el.dataset.l; setLang(lang); draw(); });
    $$(".sw", bg).forEach(el => el.onclick = () => { accent = el.dataset.a; setAccent(accent); draw(); });
    $("#wGo", bg).onclick = async () => {
      S.settings = await api("POST", "/api/settings", { welcomed: true, ui_lang: lang, accent });
      bg.style.transition = "opacity .4s"; bg.style.opacity = 0; setTimeout(() => bg.remove(), 400);
      if ("Notification" in window && Notification.permission === "default") { try { Notification.requestPermission(); } catch (_) { } }
      await refreshStatus(); renderChrome(); route();
    };
  };
  draw();
  document.body.appendChild(bg);
}

/* ------------------------------------------------------------------ à propos */
function openAbout() {
  const m = modal(T("About", "À propos"), `<div class="about">
      <img src="/static/icon.svg" alt="">
      <div class="nm">Vertical</div>
      <div class="ver small dim">${T("Version", "Version")} ${esc(S.version || "")}</div>
      <p>${T("Turns your Twitch VODs into ready-to-post Shorts for YouTube, TikTok and Reels. Everything runs locally on your PC — free, private, no subscription and no paid API.",
        "Transforme tes VODs Twitch en Shorts prêts à publier sur YouTube, TikTok et Reels. Tout tourne en local sur ton PC — gratuit, privé, sans abonnement ni API payante.")}</p>
      <div class="by"><div class="av">K</div><div class="who"><span class="small dim">${T("Created by", "Créé par")}</span><b>Krimossimo</b></div>
        <button class="btn kofi" id="abKofi">${ic("coffee")} ${T("Support on Ko-fi", "Soutenir sur Ko-fi")}</button></div>
      <div class="small muted">${T("If Vertical saves you time, a coffee helps keep it free and growing. Thank you!", "Si Vertical te fait gagner du temps, un café aide à le garder gratuit et à le faire grandir. Merci !")} ${ic("heart")}</div>
      <div class="sep" style="width:100%;margin:6px 0"></div>
      <div class="credits">${T("Built with open-source software", "Construit avec des logiciels libres")}: faster-whisper (OpenAI Whisper), FFmpeg, PyTorch, CLIP, Audio Spectrogram Transformer, OpenCV, Silero VAD, Starlette, pywebview. ${T("Fonts", "Polices")}: Inter, Sora, JetBrains Mono, Anton, Bebas Neue.</div>
    </div>`, { footer: `<button class="btn ghost left" id="abEnv">${ic("cpu")} ${T("Diagnostics", "Diagnostic")}</button><button class="btn" id="abLink">${ic("external")} ko-fi.com/krimossimo</button>` });
  const open = () => api("POST", "/api/open-url", { url: KOFI }).catch(() => window.open(KOFI, "_blank"));
  $("#abKofi", m.el).onclick = open; $("#abLink", m.el).onclick = open;
  $("#abEnv", m.el).onclick = () => { m.close(); openEnv(); };
}

/* ------------------------------------------------------------------ raccourcis */
function openKeys() {
  const k = (keys, label) => `<div><span>${label}</span><span>${keys.map(x => `<span class="kbd">${x}</span>`).join(" ")}</span></div>`;
  modal(T("Keyboard shortcuts", "Raccourcis clavier"), `<div class="keys">
    <h3>${T("Reviewing moments", "Tri des moments")}</h3>
    ${k(["V"], T("Accept", "Valider"))}${k(["R"], T("Reject", "Rejeter"))}
    ${k(["→"], T("Next moment", "Moment suivant"))}${k(["←"], T("Previous moment", "Moment précédent"))}
    ${k([T("Space", "Espace")], T("Play / pause", "Lecture / pause"))}${k(["J"], T("Back 5 s", "Reculer de 5 s"))}
    ${k(["L"], T("Forward 5 s", "Avancer de 5 s"))}${k(["I"], T("Set start here", "Début ici"))}
    ${k(["O"], T("Set end here", "Fin ici"))}${k(["P"], T("9:16 preview", "Aperçu 9:16"))}
    <h3>${T("Subtitles", "Sous-titres")}</h3>
    ${k(["Ctrl", "Z"], T("Undo last correction", "Annuler la dernière correction"))}${k([T("Enter", "Entrée")], T("Save line & go to next", "Valider et ligne suivante"))}
    ${k([T("Esc", "Échap")], T("Cancel line edit", "Annuler la ligne"))}${k(["↑", "↓"], T("Previous / next line", "Ligne précédente / suivante"))}
    <h3>${T("Everywhere", "Partout")}</h3>
    ${k(["?"], T("Show this help", "Afficher cette aide"))}${k(["Ctrl", ","], T("Settings", "Réglages"))}
    ${k([T("Esc", "Échap")], T("Close a window", "Fermer une fenêtre"))}
  </div>`);
}
document.addEventListener("keydown", e => {
  const ae = document.activeElement, typing = ae && (ae.tagName === "TEXTAREA" || ae.tagName === "SELECT" || (ae.tagName === "INPUT" && !["checkbox", "range", "radio"].includes(ae.type)));
  if (typing) return;
  if (e.key === "?" && !$(".modal-bg")) { e.preventDefault(); openKeys(); }
  else if ((e.ctrlKey || e.metaKey) && e.key === ",") { e.preventDefault(); if (!$(".modal-bg")) openSettings(); }
});

/* ------------------------------------------------------------------ accueil */
async function renderHome() {
  crumb("");
  const notes = (S.status && S.status.notes) || [];
  main().innerHTML = `<div class="view">
    <div class="hero">
      <div class="drop" id="drop">
        <span class="eyebrow">${ic("sparkles")} ${T("100% local · free · no subscription", "100 % local · gratuit · sans abonnement")}</span>
        <h1>${T("Your VOD.", "Ta VOD.")}<br><span>${T("Your best Shorts.", "Tes meilleurs Shorts.")}</span></h1>
        <p>${T("Pick a Twitch VOD: Vertical listens to your reactions, watches the gameplay and suggests the best moments, ready to post in 9:16 with subtitles.",
          "Choisis une VOD Twitch : Vertical écoute tes réactions, regarde le gameplay et te propose les meilleurs moments, prêts à publier en 9:16 avec sous-titres.")}</p>
        <div class="row" style="flex-wrap:wrap"><button class="btn primary big" id="pick">${ic("folder", "lg")} ${T("Choose a VOD", "Choisir une VOD")}</button>
          <button class="btn big" id="reimp" title="${T("Open an exported Short to fix its subtitles and export it again", "Ouvre un Short déjà exporté pour corriger ses sous-titres et le ré-exporter")}">${ic("reimport", "lg")} ${T("Fix an exported Short", "Corriger un Short exporté")}</button></div>
        <div class="row pathrow"><input type="text" id="pathIn" placeholder="${T("…or paste the full path, e.g. D:\\VODs\\stream.mp4", "…ou colle le chemin complet, ex. D:\\VODs\\stream.mp4")}">
          <button class="btn" id="openPath">${T("Open", "Ouvrir")}</button></div>
      </div>
      <div class="card howto">
        <h3>${T("How it works", "Comment ça marche")}</h3>
        <div class="step"><div class="num">${ic("cpu")}</div><div><b>${T("Fully local analysis", "Analyse 100 % locale")}</b><div class="muted small">${T("Whisper transcribes, audio spots screams and laughs, AI recognises fights, deaths and wins on screen.", "Whisper transcrit, l'audio repère cris et rires, l'IA reconnaît combats, morts et victoires à l'écran.")}</div></div></div>
        <div class="step"><div class="num">${ic("listcheck")}</div><div><b>${T("You choose", "Tu choisis")}</b><div class="muted small">${T("Preview each moment, adjust start and end, accept or reject.", "Prévisualise chaque moment, ajuste le début et la fin, valide ou rejette.")}</div></div></div>
        <div class="step"><div class="num">${ic("phone")}</div><div><b>${T("9:16 export", "Export 9:16")}</b><div class="muted small">${T("Action-tracking crop, facecam, animated subtitles, titles and hashtags for YouTube, TikTok and Reels.", "Recadrage qui suit l'action, facecam, sous-titres animés, titres et hashtags pour YouTube, TikTok et Reels.")}</div></div></div>
        ${notes.length ? `<div class="sep" style="margin:0"></div><div class="claude-note warn">${notes.map(n => `<div class="small">${ic("alert")} ${esc(n)}</div>`).join("")}</div>` : ""}
      </div>
    </div>
    <div class="recent"><div class="recent-h"><h2>${T("Recent VODs", "VOD récentes")}</h2>
        <div class="search">${ic("search")}<input type="text" id="rSearch" placeholder="${T("Search…", "Rechercher…")}"></div></div>
      <div class="recent-grid" id="recent"><div class="muted">${T("Loading…", "Chargement…")}</div></div></div>
  </div>`;
  $("#pick").onclick = pickFile;
  $("#reimp").onclick = reimportShort;
  $("#openPath").onclick = () => openPath($("#pathIn").value);
  $("#pathIn").onkeydown = e => { if (e.key === "Enter") openPath($("#pathIn").value); };
  const drop = $("#drop");
  drop.ondragover = e => { e.preventDefault(); drop.classList.add("over"); };
  drop.ondragleave = () => drop.classList.remove("over");
  drop.ondrop = e => {
    e.preventDefault(); drop.classList.remove("over");
    const f = e.dataTransfer.files[0];
    const p = f && (f.pywebviewFullPath || f.path);
    if (p) openPath(p); else toast(T("Drag & drop isn't available here: use “Choose a VOD” or paste the path.", "Glisser-déposer indisponible ici : utilise « Choisir une VOD » ou colle le chemin."), "err");
  };
  let list = [];
  const ST = { ready: T("Analysed", "Analysée"), analyzing: T("Analysis running / interrupted", "Analyse en cours / interrompue"), new: T("Not analysed yet", "Pas encore analysée"), error: T("Error", "Erreur") };
  const draw = () => {
    const q = ($("#rSearch").value || "").toLowerCase().trim();
    const items = list.filter(p => !q || (p.name + " " + (p.game || "")).toLowerCase().includes(q));
    $("#recent").innerHTML = items.length ? items.map((p, i) => `
      <div class="pcard" data-id="${p.id}" style="animation-delay:${Math.min(i, 12) * 35}ms">
        <div class="th" style="background-image:${p.thumb ? `url(/api/projects/${p.id}/thumb/${p.thumb})` : "none"}">${p.thumb ? "" : `<div class="noimg">${ic("film", "xl")}</div>`}<span class="dur">${fmtDur(p.duration)}</span></div>
        <div class="bd"><div class="nm" title="${esc(p.vod_path)}">${esc(p.name)}</div>
          <div class="small muted">${p.game ? esc(p.game) + " · " : ""}${p.n_clips} ${plural(p.n_clips, "moment", "moments", "moment", "moments")}</div>
          <div class="st ${p.status}">${ST[p.status] || p.status}</div></div>
        <button class="btn sm del" data-del="${p.id}" title="${T("Delete project (your VOD is not touched)", "Supprimer le projet (la VOD n'est pas touchée)")}">${ic("trash")}</button>
      </div>`).join("") : `<div class="empty-state">${ic(q ? "search" : "film")}<b>${q ? T("No match", "Aucun résultat") : T("No VOD yet", "Aucune VOD pour l'instant")}</b><span class="small dim">${q ? "" : T("Choose a VOD above to get your first Shorts.", "Choisis une VOD ci-dessus pour obtenir tes premiers Shorts.")}</span></div>`;
    $$(".pcard").forEach(c => c.onclick = e => { if (!e.target.closest("[data-del]")) go(`#/p/${c.dataset.id}`); });
    $$("[data-del]").forEach(b => b.onclick = async () => {
      if (!await confirmBox(T("Delete this project? Analysis and previews are removed; your VOD and exported Shorts stay untouched.", "Supprimer ce projet ? L'analyse et les aperçus sont effacés ; la VOD et les Shorts exportés restent intacts."), { ok: T("Delete", "Supprimer"), danger: true })) return;
      await api("DELETE", `/api/projects/${b.dataset.del}`); list = list.filter(x => x.id !== b.dataset.del); draw();
    });
  };
  $("#rSearch").oninput = draw;
  try { list = await api("GET", "/api/projects"); draw(); }
  catch (e) { $("#recent").innerHTML = `<div class="muted">${esc(e.message)}</div>`; }
}
async function pickFile() {
  try {
    const r = await api("POST", "/api/pick/file");
    if (r.path) openPath(r.path);
  } catch (e) { toast(e.message, "err"); }
}
async function reimportShort() {
  try {
    const f = await api("POST", "/api/pick/file");
    if (!f.path) return;
    const r = await api("POST", "/api/reimport", { path: f.path });
    S.sel = r.clip_id; S.listTab = null; S.videoPid = null;
    location.hash = `#/p/${r.project_id}/moments`;
    setTimeout(() => { S.sel = r.clip_id; if (S.tab === "moments") renderMoments(); }, 600);
    toast(r.vod_exists ? T("Short found — fix the subtitles, then “Re-export this Short”", "Short retrouvé — corrige les sous-titres puis « Ré-exporter ce Short »")
      : T("Short found, but the original VOD is missing: it can't be rendered again.", "Short retrouvé, mais la VOD d'origine est introuvable : impossible de refaire le rendu."), r.vod_exists ? "ok" : "err");
  } catch (e) { toast(e.message, "err"); }
}
async function openPath(path) {
  path = (path || "").trim().replace(/^"|"$/g, "");
  if (!path) return toast(T("Please choose a video file.", "Indique un fichier vidéo."), "err");
  try {
    const p = await api("POST", "/api/projects", { path });
    go(`#/p/${p.id}`);
  } catch (e) { toast(e.message, "err"); }
}

/* ------------------------------------------------------------------ projet */
async function loadProject(pid) {
  S.project = await api("GET", `/api/projects/${pid}`);
  return S.project;
}
async function openProject(pid) {
  try { await loadProject(pid); } catch (e) { toast(e.message, "err"); return go("#/"); }
  const p = S.project;
  if (S.videoPid !== pid) { S.video = null; S.videoPid = pid; S.useProxy = false; S.sel = null; S.exportResult = null; }
  if (!S.tab) S.tab = p.active_job ? "analyse" : (p.clips.length ? "moments" : "analyse");
  projCrumb();
  renderProject();
  if (p.active_job) attachJob(p.active_job);
}
function renameProject() {
  const p = S.project;
  const m = modal(T("Rename VOD", "Renommer la VOD"), `
    <label class="f"><span>${T("VOD name in Vertical", "Nom de la VOD dans Vertical")}</span><input type="text" id="rnName" value="${esc(p.name)}" placeholder="${T("e.g. Phantom Blade Zero EP1", "ex. Phantom Blade Zero EP1")}"></label>
    <div class="small muted">${T("Used for the export folder", "Utilisé pour le dossier d'export")} (<b id="rnDir"></b>) ${T("and, if chosen in the Export tab, for file names:", "et, si tu le choisis dans l'onglet Export, pour les noms des fichiers :")} <b id="rnEx"></b>. ${T("Your original video file is not renamed.", "Le fichier vidéo d'origine n'est pas renommé.")}</div>`,
    { footer: `<button class="btn ghost" data-cancel>${T("Cancel", "Annuler")}</button><button class="btn primary" id="rnOk">${T("Rename", "Renommer")}</button>` });
  const inp = $("#rnName", m.el);
  const upd = () => { const n = inp.value.trim() || "…"; $("#rnDir", m.el).textContent = `${n} - Shorts`; $("#rnEx", m.el).textContent = `${n} - Short 1.mp4, ${n} - Short 2.mp4…`; };
  inp.oninput = upd; upd();
  $("[data-cancel]", m.el).onclick = m.close;
  const doIt = async () => {
    try { await api("PATCH", `/api/projects/${p.id}`, { name: inp.value }); await loadProject(p.id); m.close(); projCrumb(); renderProject(); toast(T("VOD renamed", "VOD renommée"), "ok"); }
    catch (e) { toast(e.message, "err"); }
  };
  $("#rnOk", m.el).onclick = doIt;
  inp.onkeydown = e => { if (e.key === "Enter") doIt(); };
  setTimeout(() => { inp.focus(); inp.select(); }, 50);
}
function safeName(s, max = 60) {
  return (s || "").replace(/[<>:"/\\|?*\x00-\x1f]/g, "").replace(/[\u{10000}-\u{10FFFF}]/gu, "").replace(/\s+/g, " ").trim().replace(/[ .]+$/, "").slice(0, max).trim() || "short";
}
function shortNumbers() {
  const acc = S.project.clips.filter(c => c.status === "accepted").sort((a, b) => a.start - b.start);
  return Object.fromEntries(acc.map((c, i) => [c.id, i + 1]));
}
function fileStem(c, mode) {
  const n = shortNumbers()[c.id] || 0, series = safeName(S.project.name, 80), title = safeName(c.title);
  if (mode === "series") return `${series} - Short ${n}`;
  if (mode === "series_title") return `${series} - Short ${n} - ${title}`;
  return `${String(n).padStart(2, "0")} - ${title}`;
}
function setTab(t) { S.tab = t; history.replaceState(null, "", `#/p/${S.project.id}/${t}`); renderProject(); }
function renderProject() {
  const p = S.project;
  const info = p.info || {};
  const acc = p.clips.filter(c => c.status === "accepted").length;
  main().innerHTML = `<div class="view">
    <div class="phead">
      <div style="flex:1;min-width:280px">
        <div class="pname"><h2 title="${esc(p.vod_path)}">${esc(p.name)}</h2><button class="btn sm ghost" id="renameP" title="${T("Rename this VOD (e.g. Phantom Blade Zero EP1) — used for the folder and Short names", "Renommer cette VOD (ex. Phantom Blade Zero EP1) — utilisé pour le dossier et les noms des Shorts")}">${ic("edit")} ${T("Rename", "Renommer")}</button></div>
        <div class="meta-line"><span>${ic("clock")}<b>${fmtDur(info.duration)}</b></span><span>${ic("video")}${info.width || "?"}×${info.height || "?"} · ${Math.round(info.fps || 0)} fps</span>
          ${p.game && (p.game.name || p.game.profile) ? `<span>${ic("gamepad")}<b>${esc(p.game.name || (S.profiles.find(x => x.id === p.game.profile) ? profName(S.profiles.find(x => x.id === p.game.profile)) : p.game.profile))}</b></span>` : ""}
          ${p.facecam ? `<span>${ic("webcam")}facecam</span>` : ""}
          ${!p.vod_exists ? `<span class="bad">${ic("alert")}${T("VOD file not found", "fichier VOD introuvable")}</span>` : ""}</div>
      </div>
      <div class="tabs">
        <div class="tab ${S.tab === "analyse" ? "on" : ""}" data-t="analyse"><span class="n">1</span>${T("Analysis", "Analyse")}</div>
        <div class="tab ${S.tab === "moments" ? "on" : ""} ${p.clips.length ? "" : "disabled"}" data-t="moments"><span class="n">2</span>${T("Moments", "Moments")} ${p.clips.length ? `<span class="cnt">${p.clips.length}</span>` : ""}</div>
        <div class="tab ${S.tab === "export" ? "on" : ""} ${p.clips.length ? "" : "disabled"}" data-t="export"><span class="n">3</span>Export ${acc ? `<span class="cnt">${acc}</span>` : ""}</div>
      </div>
    </div>
    <div id="tabBody"></div></div>`;
  $$(".tab").forEach(t => t.onclick = () => setTab(t.dataset.t));
  $("#renameP").onclick = renameProject;
  ({ analyse: renderAnalyse, moments: renderMoments, export: renderExport })[S.tab || "analyse"]();
}

/* ------------------------------------------------------------------ onglet Analyse */
const DURATIONS = [[15, 30, ["Ultra short", "Ultra court"]], [25, 50, ["Recommended", "Recommandé"]], [45, 60, ["Long", "Long"]], [60, 90, ["Very long", "Très long"]]];
function renderAnalyse() {
  const p = S.project, st = S.settings;
  const body = $("#tabBody");
  if (S.job && S.job.status === "running" && ["analyze", "reselect", "proxy"].includes(S.job.kind)) return renderJob(body);
  const a = (p.analysis && p.analysis.settings) || {};
  const manual = p.game && p.game.profile && ["manual", "choix manuel"].includes(p.game.detected_by);
  const cur = { game: manual ? p.game.profile : st.game || "auto",
    language: a.language || st.language, clip_count: a.clip_count || st.clip_count,
    duration_min: a.duration_min || st.duration_min, duration_max: a.duration_max || st.duration_max,
    analysis_mode: a.analysis_mode || st.analysis_mode, game_name: (p.game && p.game.name) || "" };
  const aiOk = S.status && S.status.torch && S.status.transformers;
  const mins = Math.max(4, Math.round(((p.info || {}).duration || 7200) / 7200 * 15));
  body.innerHTML = `<div class="analyze-grid">
    <div class="card" style="display:grid;gap:20px">
      ${p.clips.length ? `<div class="claude-note row" style="justify-content:space-between;flex-wrap:wrap">${ic("check")} <span style="flex:1">${T(`This VOD was already analysed (${p.clips.length} moments). Running again reuses the transcription and audio already computed.`, `Cette VOD a déjà été analysée (${p.clips.length} moments). Relancer réutilise la transcription et l'audio déjà calculés.`)}</span>
        <button class="btn sm" id="seeMoments">${T("See moments", "Voir les moments")} ${ic("arrowR")}</button></div>` : ""}
      ${p.status === "error" || p.error ? `<div class="claude-note bad">${ic("alert")} ${T("The last analysis was interrupted. You can run it again.", "Dernière analyse interrompue. Tu peux la relancer.")}</div>` : ""}
      <div class="grid2">
        <label class="f"><span>${T("Game", "Jeu")}</span><select id="fGame"><option value="auto">${T("Auto-detect", "Détection automatique")}</option>
          ${S.profiles.map(pr => `<option value="${pr.id}" ${cur.game === pr.id ? "selected" : ""}>${esc(profName(pr))}</option>`).join("")}</select></label>
        <label class="f"><span>${T("Game name", "Nom du jeu")} <span class="hint">${T("(titles & hashtags)", "(titres & hashtags)")}</span></span><input type="text" id="fGameName" placeholder="${T("e.g. Phantom Blade Zero", "ex. Phantom Blade Zero")}" value="${esc(cur.game_name)}"></label>
      </div>
      <div class="grid2">
        <label class="f"><span>${T("Spoken language", "Langue parlée")}</span><select id="fLang">
          ${[["fr", T("French", "Français")], ["en", T("English", "Anglais")], ["auto", T("Auto-detect", "Détection automatique")]].map(([v, l]) => `<option value="${v}" ${cur.language === v ? "selected" : ""}>${l}</option>`).join("")}</select></label>
        <label class="f"><span>${T("Shorts to suggest", "Nombre de Shorts proposés")}: <b id="nVal">${cur.clip_count}</b></span>
          <input type="range" id="fCount" min="5" max="10" value="${cur.clip_count}"></label>
      </div>
      <div class="f"><span class="lab">${T("Short length", "Durée des Shorts")}</span>
        <div class="chips" id="durChips">${DURATIONS.map(([a1, b1, l]) => `<div class="chip ${cur.duration_min == a1 && cur.duration_max == b1 ? "on" : ""}" data-a="${a1}" data-b="${b1}">${T(l[0], l[1])} · ${a1}–${b1} s</div>`).join("")}</div>
        <div class="row small muted" style="margin-top:6px;gap:8px">${T("Custom:", "Personnalisé :")} <input type="number" id="fMin" value="${cur.duration_min}" min="5" max="170" style="width:80px"> ${T("to", "à")}
          <input type="number" id="fMax" value="${cur.duration_max}" min="10" max="180" style="width:80px"> ${T("seconds", "secondes")}</div></div>
      <div class="f"><span class="lab">${T("Analysis depth", "Profondeur d'analyse")}</span>
        <div class="chips" id="modeChips">
          <div class="chip ${cur.analysis_mode !== "rapide" ? "on" : ""}" data-m="complet">${T("Full — picture + sound AI", "Complète — IA image + son")} ${aiOk ? "" : T("(unavailable)", "(indisponible)")}</div>
          <div class="chip ${cur.analysis_mode === "rapide" ? "on" : ""}" data-m="rapide">${T("Fast — audio/video signals", "Rapide — signaux audio/vidéo")}</div></div></div>
      <div class="row" style="gap:10px;flex-wrap:wrap">
        <button class="btn primary big" id="run" ${p.vod_exists ? "" : "disabled"}>${p.clips.length ? ic("refresh", "lg") + " " + T("Run analysis again", "Relancer l'analyse") : ic("play", "lg") + " " + T("Start analysis", "Lancer l'analyse")}</button>
        ${p.clips.length ? `<button class="btn" id="reselectBtn" title="${T("Only recompute the selection (a few seconds)", "Recalcule seulement la sélection (quelques secondes)")}">${ic("listcheck")} ${T("Re-select only", "Re-sélectionner seulement")}</button>
          <button class="btn ghost" id="force" title="${T("Clear the cache and start over", "Efface le cache et recommence tout")}">${T("Recompute everything", "Tout recalculer")}</button>` : ""}
      </div>
    </div>
    <div class="card" style="display:grid;gap:16px;align-content:start">
      <h3>${T("What happens next", "Ce qui va se passer")}</h3>
      <div class="time-est">${ic("timer")}<div>${T(`For this VOD, expect about <b>${mins}–${mins * 2} minutes</b> on an RTX 3060 (Whisper transcription is the biggest part). You can keep using your PC meanwhile.`,
        `Pour cette VOD, compte environ <b>${mins} à ${mins * 2} minutes</b> sur une RTX 3060 (la transcription Whisper représente la plus grosse part). Tu peux utiliser ton PC pendant ce temps.`)}</div></div>
      <div class="feat"><div class="ico">${ic("mic")}</div><div><b>${T("Transcription", "Transcription")}</b><span>${T("Whisper large-v3-turbo on GPU, word-level timestamps", "Whisper large-v3-turbo sur GPU, timestamps au mot")}</span></div></div>
      <div class="feat"><div class="ico">${ic("volume")}</div><div><b>${T("Reactions", "Réactions")}</b><span>${T("Volume peaks, screams, laughs, exclamations, repetitions", "Pics de volume, cris, rires, exclamations, répétitions")}</span></div></div>
      <div class="feat"><div class="ico">${ic("eye")}</div><div><b>${T("Picture", "Image")}</b><span>${T("Action intensity, flashes, death / victory screens", "Intensité de l'action, flashs, écrans de mort / victoire")}${aiOk ? T(", CLIP recognition", ", reconnaissance CLIP") : ""}</span></div></div>
      <div class="feat"><div class="ico">${ic("gamepad")}</div><div><b>${T("Game profile", "Profil de jeu")}</b><span>${T("Keywords and events tuned per genre (souls-like, FPS, MOBA, fighting…)", "Mots-clés et événements adaptés (souls-like, FPS, MOBA, combat…)")}</span></div></div>
      <div class="feat"><div class="ico">${ic("scissors")}</div><div><b>${T("Clean cuts", "Découpe propre")}</b><span>${T("Context before the action, cuts aligned on speech pauses", "Contexte avant l'action, coupes calées sur les pauses de parole")}</span></div></div>
      ${S.status && S.status.notes && S.status.notes.length ? `<div class="claude-note warn">${S.status.notes.map(n => `<div class="small">${ic("alert")} ${esc(n)}</div>`).join("")}</div>` : ""}
    </div></div>`;
  $("#fCount").oninput = e => $("#nVal").textContent = e.target.value;
  $$("#durChips .chip").forEach(c => c.onclick = () => {
    $$("#durChips .chip").forEach(x => x.classList.remove("on")); c.classList.add("on");
    $("#fMin").value = c.dataset.a; $("#fMax").value = c.dataset.b;
  });
  $$("#modeChips .chip").forEach(c => c.onclick = () => { $$("#modeChips .chip").forEach(x => x.classList.remove("on")); c.classList.add("on"); });
  const opts = () => ({
    game: $("#fGame").value, game_name: $("#fGameName").value.trim(), language: $("#fLang").value,
    clip_count: +$("#fCount").value, duration_min: +$("#fMin").value, duration_max: Math.max(+$("#fMax").value, +$("#fMin").value + 5),
    analysis_mode: $(".chip.on", $("#modeChips")).dataset.m,
  });
  const launch = async (force) => {
    const o = opts();
    api("POST", "/api/settings", { game: o.game, language: o.language, clip_count: o.clip_count, duration_min: o.duration_min, duration_max: o.duration_max, analysis_mode: o.analysis_mode }).then(s => S.settings = s);
    try {
      const r = await api("POST", `/api/projects/${p.id}/analyze`, { ...o, force });
      attachJob(r.job);
    } catch (e) { toast(e.message, "err"); }
  };
  $("#run").onclick = () => launch(false);
  if ($("#force")) $("#force").onclick = async () => { if (await confirmBox(T("Clear the cache (including the transcription) and recompute everything?", "Effacer le cache (transcription comprise) et tout recalculer ?"), { ok: T("Recompute", "Tout recalculer"), danger: true })) launch(true); };
  if ($("#seeMoments")) $("#seeMoments").onclick = () => setTab("moments");
  if ($("#reselectBtn")) $("#reselectBtn").onclick = async () => {
    const o = opts();
    if (!await confirmBox(T("Recompute the selection with these settings? Moments you haven't edited will be replaced.", "Recalculer la sélection avec ces réglages ? Les passages non retouchés seront remplacés."), { ok: T("Re-select", "Re-sélectionner") })) return;
    try { const r = await api("POST", `/api/projects/${p.id}/reselect`, { ...o, reset: false }); attachJob(r.job); } catch (e) { toast(e.message, "err"); }
  };
}

/* ------------------------------------------------------------------ suivi des tâches */
function stopPoll() { if (S.poll) clearTimeout(S.poll); S.poll = null; }
function attachJob(jid) {
  stopPoll();
  const tick = async () => {
    let j;
    try { j = await api("GET", `/api/jobs/${jid}`); } catch (e) { S.job = null; return; }
    S.job = j;
    if (!S.project || S.project.id !== j.project_id) return;
    if (j.status === "running") {
      if (["analyze", "reselect", "proxy"].includes(j.kind)) { if (S.tab !== "analyse") { S.tab = "analyse"; renderProject(); } else renderJob($("#tabBody")); }
      if (j.kind === "export") renderExportJob();
      S.poll = setTimeout(tick, 800);
    } else {
      S.job = null;
      await loadProject(j.project_id);
      if (j.status === "done") {
        chime(true);
        if (j.kind === "export") {
          S.exportResult = j.result; toast(T("Export complete", "Export terminé"), "ok"); S.tab = "export";
          if (S.settings.open_after_export && j.result && j.result.dir) api("POST", "/api/open-folder", { path: j.result.dir }).catch(() => { });
        }
        else if (j.kind === "proxy") { S.useProxy = true; S.video = null; toast(T("Preview version ready", "Version de prévisualisation prête"), "ok"); S.tab = "moments"; }
        else { toast(T(`${S.project.clips.length} moments found`, `${S.project.clips.length} moments trouvés`), "ok"); S.tab = "moments"; S.sel = null; S.listTab = null; }
      } else if (j.status === "error") { chime(false); toast(T("Error: ", "Erreur : ") + j.error, "err"); }
      else toast(T("Task cancelled", "Tâche annulée"));
      history.replaceState(null, "", `#/p/${S.project.id}/${S.tab}`);
      renderProject();
    }
  };
  tick();
}
function stepIcon(st) { return st === "done" ? ic("check") : st === "error" ? "!" : st === "skipped" ? "–" : ""; }
function renderJob(body) {
  const j = S.job; if (!body || !j) return;
  const pct = Math.round(j.overall * 100);
  const steps = j.steps.map(s => `<div class="stepl ${s.status}">
      <div class="ic">${stepIcon(s.status)}</div>
      <div style="min-width:0"><div class="lb">${esc(s.label)}</div>${s.message ? `<div class="msg" title="${esc(s.message)}">${esc(s.message)}</div>` : ""}
        ${s.status === "running" ? `<div class="progress thin" style="margin-top:7px"><i style="width:${Math.round(s.progress * 100)}%"></i></div>` : ""}</div>
      <div class="pct">${s.status === "running" ? Math.round(s.progress * 100) + " %" : ""}</div></div>`).join("");
  const existing = $("#jobView", body);
  const html = `<div class="row" style="align-items:flex-end;gap:28px;flex-wrap:wrap">
        <div class="bigpct">${pct}<small>%</small></div>
        <div style="flex:1;min-width:240px"><div class="muted small" style="margin-bottom:8px">${j.kind === "proxy" ? T("Creating the preview version", "Création de la version de prévisualisation") : T("Analysis in progress", "Analyse en cours")} · ${fmt(j.elapsed)} ${T("elapsed", "écoulé")}${j.eta ? ` · ${T("about", "reste ≈")} ${fmt(j.eta)} ${T("left", "")}` : ""}</div>
          <div class="progress"><i style="width:${pct}%"></i></div></div>
        <button class="btn" id="cancelJob">${ic("x")} ${T("Cancel", "Annuler")}</button></div>
      <div class="analyze-grid" style="margin-top:8px"><div class="steps">${steps}</div>
        <div><h3 style="margin:18px 0 10px">${T("Log", "Journal")}</h3><div class="logbox" id="logbox">${esc(j.log.join("\n"))}</div>
          <div class="small dim" style="margin-top:10px">${ic("bell")} ${T("A sound plays when it's done — feel free to do something else.", "Un son retentit à la fin — tu peux faire autre chose en attendant.")}</div></div></div>`;
  if (existing) existing.innerHTML = html; else body.innerHTML = `<div class="card" id="jobView">${html}</div>`;
  const lb = $("#logbox"); if (lb) lb.scrollTop = lb.scrollHeight;
  $("#cancelJob").onclick = () => api("POST", `/api/jobs/${j.id}/cancel`);
}

/* ------------------------------------------------------------------ onglet Moments */
function clipById(id) { return S.project.clips.find(c => c.id === id); }
const FACECAM = ["facecam_top", "facecam_fixed"], TRACKING = ["facecam_top", "smart_crop"];
function resolveLayout(c) {
  let l = c.layout || "auto";
  if (l === "auto") l = S.settings.layout || "auto";
  if (l === "auto") {
    if (S.project.facecam) l = (layoutCfg().track && !c.game_crop) ? "facecam_top" : "facecam_fixed";
    else l = c.game_crop ? "center_crop" : "smart_crop";
  }
  if (FACECAM.includes(l) && !S.project.facecam) l = l === "facecam_top" ? "smart_crop" : "center_crop";
  return l;
}
function gameRect(c) { // zone fixe du jeu utilisée au rendu (null = suivi de l'action ou centré)
  const lay = resolveLayout(c), lc = layoutCfg();
  if (TRACKING.includes(lay)) return null;
  if (c.game_crop) return c.game_crop;
  if (lay === "blur_fill") return null;
  return lc.game || null;
}
function renderMoments() {
  const p = S.project, body = $("#tabBody");
  if (!p.clips.length) { body.innerHTML = `<div class="empty">${T("No moments yet. Run the analysis.", "Aucun moment pour l'instant. Lance l'analyse.")}</div>`; return; }
  if (!S.sel || !clipById(S.sel)) S.sel = p.clips[0].id;
  const acc = p.clips.filter(c => c.status === "accepted").length;
  const pend = p.clips.filter(c => statusOf(c) === "pending").length;
  body.innerHTML = `
    <div class="toolbar">
      ${pend ? `<div class="batch" title="${T("Accept every pending moment at or above this score", "Valide tous les moments à trier ayant au moins ce score")}"><span class="small muted">${T("Accept all ≥", "Valider tout ≥")}</span>
        <input type="range" id="bThr" min="0" max="100" step="5" value="${S.batchThr ?? 60}"><b class="small" id="bThrV">${S.batchThr ?? 60}</b>
        <button class="btn sm" id="bBatch">${ic("listcheck")} <span id="bBatchN"></span></button></div>` : ""}
      <div style="flex:1"></div>
      <button class="btn sm ghost" id="bKeys" title="${T("Keyboard shortcuts", "Raccourcis clavier")}">${ic("keyboard")} ${T("Shortcuts", "Raccourcis")}</button>
      <button class="btn sm" id="bAdd" title="${T("Add a moment around the playhead", "Ajoute un passage autour de la position de lecture")}">${ic("plus")} ${T("Manual moment", "Passage manuel")}</button>
      <button class="btn sm" id="bClaude" title="${T("Uses your Claude Pro subscription, no API key", "Utilise ton abonnement Claude Pro, sans clé API")}">${ic("sparkles")} ${T("Claude review", "Analyse Claude")}</button>
      <button class="btn sm primary" id="bNext" ${acc ? "" : "disabled"}>${exportLabel(acc)}</button>
    </div>
    ${(p.notes_text || []).map(n => `<div class="claude-note warn" style="margin-bottom:12px">${ic("alert")} ${esc(n)}</div>`).join("")}
    <div class="moments"><div class="mcol"><div class="lsort" id="lsort"></div><div class="ltabs" id="ltabs"></div><div class="mlist" id="mlist"></div></div><div class="editor" id="editor"></div></div>`;
  renderList();
  renderEditor();
  $("#bNext").onclick = () => setTab("export");
  $("#bClaude").onclick = openClaude;
  $("#bAdd").onclick = addManual;
  $("#bKeys").onclick = openKeys;
  if ($("#bThr")) {
    const upd = () => {
      S.batchThr = +$("#bThr").value; $("#bThrV").textContent = S.batchThr;
      const n = p.clips.filter(c => statusOf(c) === "pending" && (c.score ?? 0) >= S.batchThr).length;
      $("#bBatchN").textContent = T(`Accept ${n}`, `Valider ${n}`); $("#bBatch").disabled = !n;
    };
    $("#bThr").oninput = upd; upd();
    $("#bBatch").onclick = async () => {
      const list = p.clips.filter(c => statusOf(c) === "pending" && (c.score ?? 0) >= S.batchThr);
      for (const c of list) { c.status = "accepted"; await patchClip(c, { status: "accepted" }); }
      toast(T(`${list.length} moments accepted`, `${list.length} moments validés`), "ok");
      S.listTab = null; renderMoments();
    };
  }
}
function exportLabel(n) { return `${T("Export", "Exporter")} ${n || ""} ${plural(n, "Short", "Shorts", "Short", "Shorts")} ${ic("arrowR")}`; }
const LIST_TABS = [["pending", ["To review", "À trier"]], ["accepted", ["Accepted", "Validés"]], ["rejected", ["Rejected", "Rejetés"]]];
function statusOf(c) { return c.status === "accepted" || c.status === "rejected" ? c.status : "pending"; }
function sortMode() { return (S.settings && S.settings.moments_sort) || "score"; }
function sortedClips() {
  const cl = [...S.project.clips];
  if (sortMode() === "time") return cl.sort((a, b) => a.start - b.start);
  return cl.sort((a, b) => ((b.score ?? -1) - (a.score ?? -1)) || ((a.rank || 99) - (b.rank || 99)));
}
function fmtVod(t) { // position dans la VOD : 1h27:05 ou 27:05
  t = Math.max(0, Math.round(t || 0));
  const h = Math.floor(t / 3600), m = Math.floor(t % 3600 / 60), s = t % 60;
  return h ? `${h}h${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}` : `${m}:${String(s).padStart(2, "0")}`;
}
function renderList() {
  const p = S.project;
  if (!S.listTab) S.listTab = p.clips.some(c => statusOf(c) === "pending") ? "pending" : "accepted";
  const counts = { pending: 0, accepted: 0, rejected: 0 };
  p.clips.forEach(c => counts[statusOf(c)]++);
  $("#ltabs").innerHTML = LIST_TABS.map(([k, l]) => `<div class="ltab ${k} ${S.listTab === k ? "on" : ""}" data-f="${k}">${T(l[0], l[1])}<b>${counts[k]}</b></div>`).join("");
  $$("#ltabs .ltab").forEach(t => t.onclick = () => { S.listTab = t.dataset.f; renderList(); });
  $("#lsort").innerHTML = `<span class="small muted">${T("Sort by", "Trier par")}</span>
    <div class="seg"><div class="${sortMode() === "score" ? "on" : ""}" data-s="score" title="${T("Best moments first", "Les meilleurs moments d'abord")}">${ic("star")} Score</div>
    <div class="${sortMode() === "time" ? "on" : ""}" data-s="time" title="${T("In the order they happen in the VOD", "Dans l'ordre où ils apparaissent dans la VOD")}">${ic("clock")} ${T("VOD order", "Ordre de la VOD")}</div></div>`;
  $$("#lsort [data-s]").forEach(b => b.onclick = async () => {
    S.settings.moments_sort = b.dataset.s; renderList();
    S.settings = await api("POST", "/api/settings", { moments_sort: b.dataset.s });
  });
  const sorted = sortedClips().filter(c => statusOf(c) === S.listTab);
  if (!sorted.length) {
    $("#mlist").innerHTML = `<div class="empty small" style="padding:30px 10px">${{ pending: counts.accepted ? T("All sorted! Move on to export whenever you like.", "Tout est trié ! Passe à l'export quand tu veux.") : T("Nothing to review.", "Rien à trier."),
      accepted: T("No accepted moment yet.", "Aucun passage validé pour l'instant."), rejected: T("No rejected moment.", "Aucun passage rejeté.") }[S.listTab]}</div>`;
    return;
  }
  const timeIdx = Object.fromEntries([...p.clips].sort((a, b) => a.start - b.start).map((c, i) => [c.id, i + 1]));
  $("#mlist").innerHTML = sorted.map(c => `
    <div class="mcard ${c.id === S.sel ? "sel" : ""} ${c.status}" data-id="${c.id}">
      <div class="th" style="background-image:${c.thumb ? `url(/api/projects/${p.id}/thumb/${c.id})` : "none"}">
        <span class="rk">${sortMode() === "time" ? (timeIdx[c.id] || "") : "#" + c.rank}</span><span class="du">${Math.round(c.end - c.start)} s</span></div>
      <div style="min-width:0">
        <div class="tt">${esc(c.title || catName(c))}</div>
        <div class="sub"><span class="score ${scoreClass(c.score)}">${c.score != null ? Math.round(c.score) : "—"}</span>
          <span class="vt" title="${T("Position in the VOD", "Position dans la VOD")}">${ic("clock")}${fmtVod(c.start)}</span><span class="cat">${esc(catName(c))}</span></div>
        <div class="why">${esc(reasonsOf(c)[0] || "")}</div>
      </div>
      ${c.status === "accepted" || c.status === "rejected" ? `<span class="stbadge ${c.status}">${ic(c.status === "accepted" ? "check" : "x")}</span>` : ""}
    </div>`).join("");
  $$(".mcard").forEach(el => el.onclick = () => { S.sel = el.dataset.id; $$(".mcard").forEach(x => x.classList.toggle("sel", x === el)); renderEditor(); });
}
function ppIcon(paused) { return ic(paused ? "play" : "pause"); }
function getVideo() {
  if (!S.video) {
    const v = document.createElement("video");
    v.preload = "metadata"; v.controls = true;
    const syncPP = () => { const b = $("#ppBtn"); if (b) b.innerHTML = ppIcon(v.paused); };
    v.addEventListener("play", syncPP); v.addEventListener("pause", syncPP);
    v.src = `/api/projects/${S.project.id}/media${S.useProxy ? "?proxy=1" : ""}`;
    v.addEventListener("error", () => {
      const w = v.parentElement; if (!w || $(".vwarn", w)) return;
      const d = document.createElement("div");
      d.className = "vwarn";
      d.innerHTML = `<div><h2>${T("Direct preview isn't possible for this video format", "Aperçu direct impossible pour ce format vidéo")}</h2>
        <p class="muted">${T("The built-in player can't read this file as is", "Le lecteur intégré ne sait pas lire ce fichier tel quel")} (${esc((S.project.info || {}).vcodec || "")} / ${esc(((S.project.vod_path || "").split(".").pop() || "").toUpperCase())}). ${T("Export will work normally.", "L'export, lui, fonctionnera normalement.")}</p>
        <div class="row" style="justify-content:center;gap:10px">${S.project.has_proxy ? `<button class="btn primary" id="useProxy">${T("Use the preview version", "Utiliser la version de prévisualisation")}</button>` : `<button class="btn primary" id="mkProxy">${T("Create a preview version (540p)", "Créer une version de prévisualisation (540p)")}</button>`}</div></div>`;
      w.appendChild(d);
      const up = $("#useProxy", d); if (up) up.onclick = () => { S.useProxy = true; S.video = null; renderEditor(); };
      const mk = $("#mkProxy", d); if (mk) mk.onclick = async () => { const r = await api("POST", `/api/projects/${S.project.id}/proxy`); attachJob(r.job); };
    });
    S.video = v;
  }
  return S.video;
}
function renderEditor() {
  const p = S.project, c = clipById(S.sel), ed = $("#editor");
  if (!c || !ed) return;
  if (S.edClip !== c.id) { S.edClip = c.id; S.undo = []; S.lines = null; }
  if (!S.edTab) S.edTab = "subs";
  ed.innerHTML = `
    <div class="ed-head">
      <div class="ed-title">
        <span class="rk">#${c.rank || "–"}</span>
        <div style="min-width:0"><div class="nm" title="${esc(c.title || "")}">${esc(c.title || catName(c))}</div>
          <div class="row small muted" style="gap:8px;margin-top:4px"><span class="score ${scoreClass(c.score)}">${c.score != null ? Math.round(c.score) : "—"}</span>
            <span class="cat">${esc(catName(c))}</span><span class="vt" title="${T("Position in the VOD", "Position dans la VOD")}">${ic("clock")}${fmtVod(c.start)} → ${fmtVod(c.end)}</span>${c.export ? `<span class="tag ok">${ic("check")} ${T("exported", "exporté")}</span>` : ""}</div></div>
      </div>
      <div class="ed-actions">
        <button class="btn ghost" id="prevC" title="${T("Previous", "Précédent")} (←)">${ic("left")}</button>
        <button class="btn ok ${c.status === "accepted" ? "on" : ""}" id="acc" title="${T("Accept", "Valider")} (V)">${ic("check")} ${T("Accept", "Valider")}</button>
        <button class="btn bad ${c.status === "rejected" ? "on" : ""}" id="rej" title="${T("Reject", "Rejeter")} (R)">${ic("x")} ${T("Reject", "Rejeter")}</button>
        <button class="btn primary ${statusOf(c) !== "pending" ? "pulse" : ""}" id="nextC" title="${T("Next", "Suivant")} (→)">${T("Next", "Suivant")} ${ic("arrowR")}</button>
      </div>
    </div>
    <div class="playerwrap" id="pw"><div class="overlay9" id="ov9" style="display:none"></div><div class="overlayCam" id="ovCam" style="display:none"></div><div class="subLive" id="subLive"></div></div>
    <div class="timeline" id="tl"><div class="wave" id="wave"></div><div class="sel" id="tlSel"></div>
      <div class="hd" id="hS"></div><div class="hd" id="hE"></div><div class="ph" id="tlPh"></div><div class="pk" id="tlPk" title="${T("Peak of the moment", "Point culminant")}"></div></div>
    <div class="tl-ctrl">
      <div class="grp" title="${T("Short start", "Début du Short")}"><span class="lbl">${T("Start", "Début")}</span><button class="btn sm" data-n="s-1">−1</button><span class="tval" id="vS">${fmtP(c.start)}</span><button class="btn sm" data-n="s+1">+1</button>
        <button class="btn sm" id="setS" title="${T("Start = playhead (I)", "Début = position de lecture (I)")}">${T("⇤ here", "⇤ ici")}</button></div>
      <div class="grp"><button class="btn sm ghost" id="playClip" title="${T("Replay from the start", "Relire depuis le début du passage")}">${ic("replay")}</button><button class="btn pp" id="ppBtn" title="${T("Play / pause (Space)", "Lecture / pause (Espace)")}">${ppIcon(getVideo().paused)}</button>
        <span class="tval" id="vD" title="${T("Short length", "Durée du Short")}">${(c.end - c.start).toFixed(1)} s</span><button class="btn sm ghost" id="resetT" title="${T("Back to suggested bounds", "Revenir aux bornes proposées")}">${ic("undo")}</button></div>
      <div class="grp" title="${T("Short end", "Fin du Short")}"><button class="btn sm" id="setE" title="${T("End = playhead (O)", "Fin = position de lecture (O)")}">${T("here ⇥", "ici ⇥")}</button><button class="btn sm" data-n="e-1">−1</button>
        <span class="tval" id="vE">${fmtP(c.end)}</span><button class="btn sm" data-n="e+1">+1</button><span class="lbl">${T("End", "Fin")}</span></div>
    </div>
    <div class="etabs" id="etabs">
      <div class="etab" data-t="subs">${ic("captions")} ${T("Subtitles", "Sous-titres")}</div>
      <div class="etab" data-t="frame">${ic("crop")} ${T("Framing", "Cadrage")}${c.game_crop ? " <i class='dot'></i>" : ""}</div>
      <div class="etab" data-t="pub">${ic("hash")} ${T("Publishing", "Publication")}</div>
      <div class="etab" data-t="why">${ic("search")} ${T("Why this moment", "Pourquoi ce moment")}</div>
    </div>
    <div class="card etab-body" id="etBody"></div>`;
  const pw = $("#pw");
  const v = getVideo();
  pw.prepend(v);
  if ($(".vwarn", pw) == null && v.error) v.dispatchEvent(new Event("error"));
  const want = Math.max(0, c.start);
  const seekStart = () => { if (Math.abs(v.currentTime - want) > 0.5 && (v.currentTime < c.start - 25 || v.currentTime > c.end + 25 || v.paused)) v.currentTime = want; };
  if (v.readyState >= 1) seekStart(); else v.addEventListener("loadedmetadata", seekStart, { once: true });
  mountTimeline(c);
  drawOverlay(c);
  window.onresize = () => drawOverlay(c);
  v.onloadedmetadata = () => drawOverlay(c);
  $$("[data-n]", ed).forEach(b => b.onclick = () => {
    const [k, d] = [b.dataset.n[0], +b.dataset.n.slice(1)];
    if (k === "s") c.start = Math.max(0, Math.min(c.end - 1, c.start + d)); else c.end = Math.min(p.info.duration, Math.max(c.start + 1, c.end + d));
    updateTimes(c); saveTimes(c);
  });
  $("#setS").onclick = () => { c.start = Math.min(v.currentTime, c.end - 1); updateTimes(c); saveTimes(c); };
  $("#setE").onclick = () => { c.end = Math.max(v.currentTime, c.start + 1); updateTimes(c); saveTimes(c); };
  $("#resetT").onclick = () => { c.start = c.auto_start; c.end = c.auto_end; mountTimeline(c); updateTimes(c); saveTimes(c); };
  $("#playClip").onclick = () => playRange(c);
  $("#ppBtn").onclick = e => { e.currentTarget.blur(); togglePlay(c); };
  $("#acc").onclick = () => setStatus(c, c.status === "accepted" ? "pending" : "accepted");
  $("#rej").onclick = () => setStatus(c, c.status === "rejected" ? "pending" : "rejected");
  $("#nextC").onclick = () => nextClip(1);
  $("#prevC").onclick = () => nextClip(-1);
  $$("#etabs .etab").forEach(t => t.onclick = () => { S.edTab = t.dataset.t; renderEdTab(c); });
  loadSubWords(c);
  renderEdTab(c);
}
function renderEdTab(c) {
  const p = S.project, body = $("#etBody"); if (!body) return;
  $$("#etabs .etab").forEach(t => t.classList.toggle("on", t.dataset.t === S.edTab));
  S.lines = S.edTab === "subs" ? S.lines : null;
  if (S.edTab === "subs") return renderSubsTab(c);
  if (S.edTab === "frame") {
    const layout = resolveLayout(c);
    body.innerHTML = `
      <div class="grid2">
        <label class="f"><span>${T("Layout of this Short", "Cadrage de ce Short")}</span><select id="lay">
          <option value="auto" ${(c.layout || "auto") === "auto" ? "selected" : ""}>${T("Automatic", "Automatique")} (${esc(layoutName(layout))})</option>
          ${S.layouts.map(k => `<option value="${k}" ${c.layout === k ? "selected" : ""} ${FACECAM.includes(k) && !p.facecam ? "disabled" : ""}>${esc(layoutName(k))}${FACECAM.includes(k) && !p.facecam ? T(" — no camera", " — aucune caméra") : ""}</option>`).join("")}</select></label>
        <div class="f"><span class="lab">${T("On the video", "Affichage sur la vidéo")}</span>
          <label class="toggle small" style="margin-top:8px"><input type="checkbox" class="switch" id="showOv" ${S.showOv === false ? "" : "checked"}> ${T("Show the area kept in the Short", "Montrer la zone gardée dans le Short")}</label></div>
      </div>
      <div class="tiles">
        <button class="tile" id="cropEd"><div class="ico">${ic("crop")}</div><b>${T("Reframe the scene", "Recadrer la scène")}</b><span>${T("Choose the game area kept in this Short", "Choisis la zone du jeu gardée dans ce Short")}${c.game_crop ? ` · <em>${T("manual framing on", "réglage manuel actif")}</em>` : TRACKING.includes(layout) ? T(" · currently: follows the action", " · actuellement : suit l'action") : T(" · currently: fixed area", " · actuellement : zone fixe")}</span></button>
        <button class="tile" id="camEd"><div class="ico">${ic("webcam")}</div><b>${T("Camera", "Caméra")}</b><span>${T("Where your webcam is, its size and position (top/bottom) — for the whole VOD", "Position de ta webcam, taille et place (haut/bas) — pour toute la VOD")}${p.facecam ? "" : ` · <em>${T("no camera set", "aucune caméra définie")}</em>`}</span></button>
        <button class="tile" id="prev9"><div class="ico">${ic("phone")}</div><b>${T("9:16 preview", "Aperçu 9:16")}</b><span>${T("Quick render of the Short as it will be exported (P)", "Rendu rapide du Short tel qu'il sera exporté (P)")}</span></button>
      </div>`;
    $("#lay").onchange = e => { c.layout = e.target.value; patchClip(c, { layout: c.layout }); drawOverlay(c); };
    $("#showOv").onchange = e => { S.showOv = e.target.checked; drawOverlay(c); };
    $("#cropEd").onclick = () => startCrop(c);
    $("#camEd").onclick = openFacecam;
    $("#prev9").onclick = () => preview9(c);
    return;
  }
  if (S.edTab === "pub") {
    body.innerHTML = `
      ${c.export ? `<div class="reexp"><span class="small">${ic("check")} ${T("Already exported. After a correction, replace the file:", "Déjà exporté. Après une correction, remplace le fichier :")}</span><button class="btn sm primary" id="reExp">${ic("refresh")} ${T("Re-export this Short", "Ré-exporter ce Short")}</button></div>` : ""}
      <label class="f"><span>${T("Title", "Titre")} <span class="hint">${esc(c.meta_source || "")}</span> <span class="hint" id="tLen" style="float:right"></span></span>
        <input type="text" id="mTitle" value="${esc(c.title || "")}" maxlength="100"></label>
      ${(() => { const n = shortNumbers()[c.id]; const opts = (c.title_options || []).filter(t => t !== c.title).slice(0, 4);
        if (n) opts.push(`${p.name} - Short ${n}`);
        return opts.length ? `<div class="chips">${opts.filter(t => t !== c.title).map(t => `<div class="chip small" data-title="${esc(t)}">${esc(t)}</div>`).join("")}</div>` : ""; })()}
      <div class="grid2" style="align-items:start">
        <label class="f"><span>Description</span><textarea id="mDesc" rows="6">${esc(c.description || "")}</textarea></label>
        <div style="display:grid;gap:12px"><label class="f"><span>Hashtags</span><input type="text" id="mTags" value="${esc((c.hashtags || []).join(" "))}"></label>
          <div class="row" style="flex-wrap:wrap;gap:8px"><button class="btn sm" id="cpAll">${ic("copy")} ${T("Copy title + description", "Copier titre + description")}</button>
            <button class="btn sm ghost" id="cpTags">${ic("hash")} ${T("Copy hashtags", "Copier les hashtags")}</button></div></div>
      </div>`;
    const lenInfo = () => { const n = (c.title || "").length; $("#tLen").textContent = `${n}/100`; $("#tLen").style.color = n > 70 ? "var(--warn)" : ""; };
    lenInfo();
    const saveMeta = debounce(() => patchClip(c, { title: c.title, description: c.description, hashtags: c.hashtags }), 600);
    $("#mTitle").oninput = e => { c.title = e.target.value; lenInfo(); saveMeta(); const t = $(`.mcard[data-id="${c.id}"] .tt`); if (t) t.textContent = c.title; const h = $(".ed-title .nm"); if (h) h.textContent = c.title; };
    $("#mDesc").oninput = e => { c.description = e.target.value; saveMeta(); };
    $("#mTags").oninput = e => { c.hashtags = e.target.value.split(/[\s,]+/).filter(Boolean).map(t => t.startsWith("#") ? t : "#" + t); saveMeta(); };
    $$("[data-title]", body).forEach(ch => ch.onclick = () => { $("#mTitle").value = ch.dataset.title; $("#mTitle").dispatchEvent(new Event("input")); });
    $("#cpAll").onclick = async () => { await copyText(`${c.title}\n\n${c.description}`); toast(T("Copied", "Copié"), "ok"); };
    $("#cpTags").onclick = async () => { await copyText((c.hashtags || []).join(" ")); toast(T("Hashtags copied", "Hashtags copiés"), "ok"); };
    if ($("#reExp")) $("#reExp").onclick = () => reexportClip(c);
    return;
  }
  body.innerHTML = `
    <ul class="reasons">${reasonsOf(c).map(r => `<li>${esc(r)}</li>`).join("")}</ul>
    ${c.claude_comment ? `<div class="claude-note">${ic("sparkles")} Claude${c.claude_score != null ? ` (${c.claude_score}/100)` : ""} : ${esc(c.claude_comment)}</div>` : ""}
    ${barsHtml(c)}`;
}
const SIGNAL_LABELS = { loud: ["Your voice volume", "Volume de ta voix"], game_loud: ["Game sound", "Son du jeu"], onset: ["Sudden rise", "Montée soudaine"], scream: ["Scream", "Cri"],
  laugh: ["Laughter (audio)", "Rire (audio)"], excl: ["Exclamations", "Exclamations"], laugh_txt: ["Laughter (words)", "Rire (paroles)"],
  game_kw: ["Game keywords", "Mots-clés jeu"], rate: ["Speech rate", "Débit de parole"], repeat: ["Repetitions", "Répétitions"], motion: ["On-screen action", "Action à l'écran"],
  flash: ["Flashes", "Flashs"], red: ["Red tint", "Teinte rouge"], fade_dark: ["Fade to black", "Fondu au noir"], clip_event: ["Picture event (AI)", "Événement image (IA)"],
  ast_laugh: ["Laughter (AI)", "Rire (IA)"], ast_scream: ["Scream (AI)", "Cri (IA)"], ast_cheer: ["Cheering (AI)", "Acclamations (IA)"],
  ast_boom: ["Explosions (AI)", "Explosions (IA)"], ast_impact: ["Impacts (AI)", "Impacts (IA)"], ast_gasp: ["Gasp (AI)", "Souffle (IA)"] };
function barsHtml(c) {
  const e = Object.entries(c.contrib || {}).filter(([k]) => SIGNAL_LABELS[k]).sort((a, b) => b[1] - a[1]).slice(0, 6);
  if (!e.length) return "";
  const mx = Math.max(...e.map(x => x[1]), 0.01);
  return `<div><h3 style="margin:6px 0 10px">${T("Strongest signals", "Signaux les plus forts")}</h3><div class="bars">${e.map(([k, v]) => `<div class="bar"><span>${T(...SIGNAL_LABELS[k])}</span><div><i style="width:${Math.round(v / mx * 100)}%"></i></div><span>${v.toFixed(2)}</span></div>`).join("")}</div></div>`;
}
async function patchClip(c, data) {
  try {
    const r = await api("PATCH", `/api/projects/${S.project.id}/clips/${c.id}`, data);
    Object.assign(c, { start: r.start, end: r.end });
  } catch (e) { toast(e.message, "err"); }
}
const saveTimes = debounce(c => patchClip(c, { start: +c.start.toFixed(2), end: +c.end.toFixed(2) }), 350);
function setStatus(c, st) {
  c.status = st; patchClip(c, { status: st });
  renderList();
  $("#acc").classList.toggle("on", st === "accepted"); $("#rej").classList.toggle("on", st === "rejected");
  const acc = S.project.clips.filter(x => x.status === "accepted").length;
  const nb = $("#bNext"); nb.disabled = !acc; nb.innerHTML = exportLabel(acc);
  const nx = $("#nextC");
  if (nx) { nx.classList.toggle("pulse", st !== "pending"); }
}
function nextClip(dir = 1) {
  const all = sortedClips();
  const cur = clipById(S.sel);
  const i = all.indexOf(cur);
  // priorité aux passages encore à trier, dans l'ordre du classement
  const pend = all.filter(x => statusOf(x) === "pending" && x !== cur);
  let target = null;
  if (pend.length) {
    const after = dir > 0 ? pend.filter(x => all.indexOf(x) > i) : pend.filter(x => all.indexOf(x) < i).reverse();
    target = after[0] || (dir > 0 ? pend[0] : pend[pend.length - 1]);
  } else {
    target = all[(i + dir + all.length) % all.length];
    if (statusOf(cur) !== "pending" && !all.some(x => statusOf(x) === "pending")) toast(T("All sorted — you can move on to export.", "Tout est trié — tu peux passer à l'export."), "ok");
  }
  if (!target || target === cur) return;
  S.sel = target.id;
  if (statusOf(target) !== S.listTab && S.listTab !== "pending") S.listTab = statusOf(target);
  if (S.listTab === "pending" && statusOf(target) !== "pending") S.listTab = statusOf(target);
  renderList(); renderEditor();
  const el = $(`.mcard[data-id="${target.id}"]`); if (el) el.scrollIntoView({ block: "nearest" });
}
document.addEventListener("keydown", e => {
  const ae = document.activeElement;
  const typing = ae && (ae.tagName === "TEXTAREA" || ae.tagName === "SELECT" || (ae.tagName === "INPUT" && !["checkbox", "range", "radio"].includes(ae.type)));
  if (S.tab !== "moments" || !S.project || $(".modal-bg") || $(".welcome-bg") || typing || e.ctrlKey || e.metaKey || e.altKey) return;
  const c = clipById(S.sel); if (!c) return;
  const v = S.video, k = e.key.toLowerCase();
  if (k === "v") { setStatus(c, "accepted"); e.preventDefault(); }
  else if (k === "r") { setStatus(c, "rejected"); e.preventDefault(); }
  else if (e.key === "ArrowRight" && !e.target.closest("video")) { nextClip(1); e.preventDefault(); }
  else if (e.key === "ArrowLeft" && !e.target.closest("video")) { nextClip(-1); e.preventDefault(); }
  else if (e.key === " " || e.code === "Space") { e.preventDefault(); if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur(); togglePlay(c); }
  else if (k === "j" && v) { v.currentTime = Math.max(0, v.currentTime - 5); }
  else if (k === "l" && v) { v.currentTime = v.currentTime + 5; }
  else if (k === "i" && $("#setS")) { $("#setS").click(); }
  else if (k === "o" && $("#setE")) { $("#setE").click(); }
  else if (k === "p") { preview9(c); }
});
let TL = null;
function mountTimeline(c) {
  const dur = S.project.info.duration;
  const pad = Math.max(15, (c.end - c.start) * 0.6);
  TL = { ws: Math.max(0, Math.min(c.start, c.auto_start ?? c.start) - pad), we: Math.min(dur, Math.max(c.end, c.auto_end ?? c.end) + pad), c };
  const tl = $("#tl");
  const x2t = x => TL.ws + (x / tl.clientWidth) * (TL.we - TL.ws);
  const t2p = t => ((t - TL.ws) / (TL.we - TL.ws) * 100);
  $$(".tk", tl).forEach(e => e.remove());
  const span = TL.we - TL.ws, stepT = span > 120 ? 30 : span > 60 ? 10 : 5;
  for (let t = Math.ceil(TL.ws / stepT) * stepT; t < TL.we; t += stepT) {
    const d = document.createElement("div"); d.className = "tk"; d.style.left = t2p(t) + "%"; d.textContent = fmt(t); tl.appendChild(d);
  }
  $("#tlPk").style.left = t2p(c.peak) + "%";
  api("GET", `/api/projects/${S.project.id}/curve?start=${Math.floor(TL.ws)}&end=${Math.ceil(TL.we)}`).then(r => {
    $("#wave").innerHTML = r.values.map(v => `<i style="height:${Math.max(4, Math.min(100, v * 85))}%"></i>`).join("");
  }).catch(() => { });
  const place = () => {
    $("#tlSel").style.left = t2p(c.start) + "%"; $("#tlSel").style.width = (t2p(c.end) - t2p(c.start)) + "%";
    $("#hS").style.left = t2p(c.start) + "%"; $("#hE").style.left = t2p(c.end) + "%";
  };
  TL.place = place; TL.t2p = t2p;
  place();
  const drag = (h, key) => {
    h.onpointerdown = e => {
      e.stopPropagation(); h.setPointerCapture(e.pointerId);
      h.onpointermove = ev => {
        const r = tl.getBoundingClientRect();
        let t = x2t(Math.max(0, Math.min(r.width, ev.clientX - r.left)));
        if (key === "start") c.start = Math.max(0, Math.min(t, c.end - 1)); else c.end = Math.min(dur, Math.max(t, c.start + 1));
        updateTimes(c);
        const v = getVideo(); v.currentTime = key === "start" ? c.start : c.end;
      };
      h.onpointerup = () => { h.onpointermove = null; saveTimes(c); };
    };
  };
  drag($("#hS"), "start"); drag($("#hE"), "end");
  tl.onpointerdown = e => {
    if (e.target.closest(".hd")) return;
    const r = tl.getBoundingClientRect(); getVideo().currentTime = x2t(e.clientX - r.left);
  };
  const v = getVideo();
  v.ontimeupdate = () => {
    if (!TL || TL.c !== c) return;
    $("#tlPh") && ($("#tlPh").style.left = Math.max(0, Math.min(100, t2p(v.currentTime))) + "%");
    if (S.playEnd != null && v.currentTime >= S.playEnd) { v.pause(); S.playEnd = null; }
    renderSubLive(v.currentTime);
  };
  v.onplay = () => { const loop = () => { if (v.paused || !TL || TL.c !== c) return; renderSubLive(v.currentTime); requestAnimationFrame(loop); }; requestAnimationFrame(loop); };
  v.onseeked = () => renderSubLive(v.currentTime, true);
}
function updateTimes(c) {
  $("#vS").textContent = fmtP(c.start); $("#vE").textContent = fmtP(c.end); $("#vD").textContent = (c.end - c.start).toFixed(1) + " s";
  if (TL) TL.place();
  const du = $(`.mcard[data-id="${c.id}"] .du`); if (du) du.textContent = Math.round(c.end - c.start) + " s";
}
function togglePlay(c) {
  const v = getVideo();
  if (v.paused) {
    if (v.currentTime < c.start - 0.05 || v.currentTime >= c.end - 0.05) v.currentTime = c.start;
    S.playEnd = c.end; v.play();
  } else v.pause();
}
function playRange(c) { const v = getVideo(); v.currentTime = c.start; S.playEnd = c.end; v.play(); }

/* ---- sous-titres en direct : karaoké sur le lecteur + correction au bon moment ---- */
const SW = { clip: null, words: [] };
async function loadSubWords(c) {
  SW.clip = c.id; SW.words = []; SW.ready = false;
  try {
    const r = await api("GET", `/api/projects/${S.project.id}/transcript?start=${c.start - 1}&end=${c.end + 1}`);
    if (SW.clip !== c.id) return;
    SW.words = r.words.filter(w => w.end > c.start && w.start < c.end)
      .map(w => ({ s: w.start, e: w.end, orig: w.word.trim(), w: w.word.trim(), del: false, p: w.p ?? 1, edited: !!w.edited }));
  } catch (_) { }
  SW.ready = true;
  if (S.edTab === "subs" && S.edClip === c.id) renderLines(c);
  renderSubLive(getVideo().currentTime, true);
}
function subDisplay(w) {
  const t = w.replace(/[,.;:…]+$/, "");
  return S.settings.subtitles.uppercase ? t.toUpperCase() : t;
}
function subChunks() {
  const st = S.settings.subtitles, maxW = st.max_words, maxC = Math.max(8, Math.floor(20 * 82 / Math.max(40, st.size)));
  const ws = SW.words.filter(w => !w.del && w.w.trim());
  const chunks = []; let cur = [];
  for (const w of ws) {
    if (cur.length) {
      const last = cur[cur.length - 1], gap = w.s - last.e;
      const len = cur.reduce((n, x) => n + subDisplay(x.w).length + 1, 0) + subDisplay(w.w).length;
      if (cur.length >= maxW || len > maxC || gap > 0.6 || /[.!?]$/.test(last.w)) { chunks.push(cur); cur = []; }
    }
    cur.push(w);
  }
  if (cur.length) chunks.push(cur);
  return chunks.map((ch, i) => {
    const next = chunks[i + 1] ? chunks[i + 1][0].s : Infinity;
    return { ws: ch, start: ch[0].s, end: Math.max(ch[0].s + 0.25, Math.min(ch[ch.length - 1].e + 0.35, next)) };
  });
}
function renderSubLive(t, force = false) {
  const box = $("#subLive"); if (!box) return;
  const show = S.showSubs !== false;
  const ch = show && SW.words.length ? subChunks().find(k => t >= k.start - 0.02 && t < k.end) : null;
  let active = null;
  if (ch) { for (const w of ch.ws) if (w.s <= t + 0.02) active = w; if (!active) active = ch.ws[0]; }
  $$("#tlines .tline").forEach(row => {
    const on = t >= +row.dataset.a - 0.02 && t < +row.dataset.e + 0.3;
    if (on !== row.classList.contains("speaking")) {
      row.classList.toggle("speaking", on);
      if (on && !getVideo().paused) {
        const box2 = $("#tlines"); if (box2 && document.activeElement?.tagName !== "INPUT") { const top = row.offsetTop - box2.offsetTop; if (top < box2.scrollTop || top > box2.scrollTop + box2.clientHeight - 50) box2.scrollTop = top - 60; }
      }
    }
  });
  const key = ch ? ch.start + "|" + (active && active.s) + "|" + ch.ws.map(w => w.w).join(" ") : "";
  if (!force && box.dataset.key === key) return;
  box.dataset.key = key;
  if (!ch) { box.innerHTML = ""; return; }
  const st = S.settings.subtitles, pw = $("#pw"), H = pw ? pw.clientHeight : 400;
  Object.assign(box.style, { fontFamily: `"${st.font}", Impact, sans-serif`, fontSize: Math.round(H * 0.075 * st.size / 82) + "px",
    WebkitTextStroke: `${Math.max(1, st.outline * H / 1080 * 1.2)}px ${st.outline_color}` });
  box.innerHTML = ch.ws.map(w => `<span data-s="${w.s}" class="${w === active ? "on" : ""} ${w.p < 0.5 && !w.edited ? "unsure" : ""}" style="color:${w === active ? st.highlight : st.color}" title="${T("Click to fix this word", "Clique pour corriger ce mot")}">${esc(subDisplay(w.w))}</span>`).join(" ");
  $$("span", box).forEach(sp => sp.onclick = e => { e.stopPropagation(); pickWord(+sp.dataset.s); });
}
/* ---- éditeur de sous-titres : toujours actif, enregistrement automatique, annulation ---- */
function buildLines(c) {
  S.lines = subChunks().map((ch, i) => ({ id: "L" + i + "_" + Math.round(ch.start * 1000), toks: ch.ws.slice(), a: ch.ws[0].s,
    lastStart: ch.ws[ch.ws.length - 1].s, e: ch.ws[ch.ws.length - 1].e, orig: ch.ws.map(w => w.w).join(" "),
    unsure: ch.ws.some(w => w.p < 0.5 && !w.edited), clip: c.id }));
}
function undoLabel(n) { return `${ic("undo")} ${T("Undo", "Annuler")}${n ? ` (${n})` : ""}`; }
function renderSubsTab(c) {
  const body = $("#etBody"); if (!body) return;
  const nUndo = (S.undo || []).length;
  body.innerHTML = `
    <div class="subs-bar">
      <div class="row" style="gap:6px;flex-wrap:wrap">
        <button class="btn sm primary" id="sbAdd" title="${T("Add a word or sentence at the playhead", "Ajouter un mot ou une phrase à la position de lecture")}">${ic("plus")} ${T("Add", "Ajouter")}</button>
        <button class="btn sm" id="sbFind">${ic("search")} ${T("Replace", "Remplacer")}</button>
        <button class="btn sm" id="sbRedo" title="${T("Redo the transcription with maximum accuracy", "Refaire la transcription avec la précision maximale")}">${ic("target")} ${T("Recompute", "Recalculer")}</button>
        <button class="btn sm" id="sbPos">${ic("type")} ${T("Position", "Position")}${c.sub_pos ? " " + ic("check") : ""}</button>
        <button class="btn sm ghost" id="sbUndo" ${nUndo ? "" : "disabled"} title="${T("Undo the last change (Ctrl+Z)", "Annuler la dernière modification (Ctrl+Z)")}">${undoLabel(nUndo)}</button>
      </div>
      <div class="row" style="gap:16px;flex-wrap:wrap">
        <label class="toggle small muted"><input type="checkbox" class="switch" id="sbShow" ${S.showSubs === false ? "" : "checked"}> ${T("On video", "Sur la vidéo")}</label>
        <label class="toggle small muted"><input type="checkbox" class="switch" id="sbUnsure" ${S.onlyUnsure ? "checked" : ""}> ${T("Uncertain only", "Douteux seulement")} <span class="unsure-badge" id="sbUnsureN">0</span></label>
        <span class="small" id="sbState"></span>
      </div>
    </div>
    <div class="subs-hint small muted">${T("Click a word <b>on the video</b> to fix it · edit a line like normal text, it saves by itself", "Clique un mot <b>sur la vidéo</b> pour le corriger · modifie une ligne comme un texte normal, c'est enregistré tout seul")} · <span class="kbd">${T("Enter", "Entrée")}</span> ${T("next line", "ligne suivante")} · <span class="kbd">${T("Esc", "Échap")}</span> ${T("cancel line", "annule la ligne")} · ${ic("timer")} ${T("precise timing", "timing précis")} · ${ic("plus")} ${T("insert after", "insérer après")}</div>
    <div class="tlines" id="tlines"><div class="muted small">${T("Loading…", "Chargement…")}</div></div>`;
  $("#sbAdd").onclick = () => openTiming(c, null);
  $("#sbFind").onclick = () => openReplace(c);
  $("#sbRedo").onclick = () => openRedo(c);
  $("#sbPos").onclick = () => openSubPos(c);
  $("#sbUndo").onclick = () => undoSub(c);
  $("#sbShow").onchange = e => { S.showSubs = e.target.checked; renderSubLive(getVideo().currentTime, true); };
  $("#sbUnsure").onchange = e => { S.onlyUnsure = e.target.checked; renderLines(c); };
  if (SW.clip === c.id && SW.ready) renderLines(c);
}
function renderLines(c, focusId) {
  const box = $("#tlines"); if (!box || S.edTab !== "subs") return;
  buildLines(c);
  const n = S.lines.filter(l => l.unsure).length;
  if ($("#sbUnsureN")) $("#sbUnsureN").textContent = n;
  if (!S.lines.length) {
    box.innerHTML = `<div class="empty small" style="padding:24px">${T("No subtitles on this moment.", "Aucun sous-titre sur ce passage.")}<br><br><button class="btn sm primary" id="emAdd">${ic("plus")} ${T("Add a sentence", "Ajouter une phrase")}</button> <button class="btn sm" id="emRedo">${ic("target")} ${T("Recompute the transcription", "Recalculer la transcription")}</button></div>`;
    $("#emAdd").onclick = () => openTiming(c, null); $("#emRedo").onclick = () => openRedo(c);
    return;
  }
  box.innerHTML = S.lines.map(l => `<div class="tline ${l.unsure ? "unsure" : ""}" data-id="${l.id}" data-a="${l.a}" data-e="${l.e}" style="${S.onlyUnsure && !l.unsure ? "display:none" : ""}">
      <button class="tt" title="${T("Listen to this line", "Écouter cette ligne")}">${fmtP(l.a)}</button>
      <input type="text" value="${esc(l.orig)}" spellcheck="true">
      <span class="warn" title="${l.unsure ? T("Whisper isn't sure about some words", "Whisper n'est pas sûr de certains mots") : ""}">${l.unsure ? ic("alert") : ""}</span>
      <button class="ic" data-k="time" title="${T("Precise word timing", "Timing précis des mots")}">${ic("timer")}</button>
      <button class="ic" data-k="ins" title="${T("Insert a subtitle after this line", "Insérer un sous-titre après cette ligne")}">${ic("plus")}</button>
      <button class="ic del" data-k="del" title="${T("Delete this subtitle", "Supprimer ce sous-titre")}">${ic("trash")}</button></div>`).join("");
  const v = getVideo();
  $$(".tline", box).forEach(row => {
    const L = S.lines.find(x => x.id === row.dataset.id), inp = $("input", row);
    const autosave = debounce(() => { if (document.activeElement === inp) commitLine(c, L, row, inp.value); }, 1500);
    inp.oninput = () => { previewLine(L, inp.value); row.classList.toggle("dirty", inp.value.trim() !== L.orig); setState(""); autosave(); };
    inp.onfocus = () => { if (v.paused) v.currentTime = L.a + 0.01; };
    inp.onblur = () => commitLine(c, L, row, inp.value);
    inp.onkeydown = e => {
      if (e.key === "Enter") { e.preventDefault(); const nx = nextRow(row, 1); commitLine(c, L, row, inp.value); if (nx) $("input", nx).focus(); }
      else if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); inp.value = L.orig; previewLine(L, L.orig); row.classList.remove("dirty"); inp.blur(); }
      else if (e.key === "ArrowDown" || e.key === "ArrowUp") { const nx = nextRow(row, e.key === "ArrowDown" ? 1 : -1); if (nx) { e.preventDefault(); $("input", nx).focus(); } }
    };
    $(".tt", row).onclick = () => { v.currentTime = L.a; S.playEnd = L.e + 0.4; v.play(); };
    $("[data-k=time]", row).onclick = () => openTiming(c, L);
    $("[data-k=ins]", row).onclick = () => { v.pause(); v.currentTime = L.e + 0.05; openTiming(c, null, { t0: L.e + 0.05 }); };
    $("[data-k=del]", row).onclick = () => commitLine(c, L, row, "");
  });
  if (focusId) { const r = $(`.tline[data-id="${focusId}"] input`, box); if (r) r.focus(); }
  renderSubLive(v.currentTime, true);
}
function nextRow(row, dir) { let n = dir > 0 ? row.nextElementSibling : row.previousElementSibling; while (n && n.style.display === "none") n = dir > 0 ? n.nextElementSibling : n.previousElementSibling; return n; }
function setState(html, kind = "") { const el = $("#sbState"); if (el) { el.innerHTML = html; el.className = "small " + kind; } }
function previewLine(L, text) {
  text = text.trim();
  const old = L.preview || L.toks;
  SW.words = SW.words.filter(w => !old.includes(w));
  L.preview = text === L.orig ? null : distributeWords(text, L.a, L.e);
  (L.preview || L.toks).forEach(w => SW.words.push(w));
  SW.words.sort((x, y) => x.s - y.s);
  renderSubLive(getVideo().currentTime, true);
}
async function commitLine(c, L, row, text) {
  text = (text || "").trim();
  if (!L || L.saving || text === L.orig) return;
  const newToks = text ? (L.preview && L.preview.length ? L.preview : distributeWords(text, L.a, L.e)) : [];
  L.saving = true; setState(T("Saving…", "Enregistrement…"));
  const oldWords = L.toks.map(w => ({ word: w.w, start: +w.s.toFixed(3), end: +w.e.toFixed(3) }));
  try {
    await api("POST", `/api/projects/${S.project.id}/transcript/words`, { a: L.a, b: L.lastStart,
      words: newToks.map(w => ({ word: w.w, start: +w.s.toFixed(3), end: +w.e.toFixed(3) })) });
    S.undo = S.undo || [];
    S.undo.push(newToks.length ? { a: +newToks[0].s.toFixed(3), b: +newToks[newToks.length - 1].s.toFixed(3), words: oldWords }
      : { a: null, b: null, words: oldWords });
    SW.words = SW.words.filter(w => !L.toks.includes(w) && !(L.preview || []).includes(w));
    newToks.forEach(w => { w.edited = true; SW.words.push(w); });
    SW.words.sort((x, y) => x.s - y.s);
    L.toks = newToks; L.preview = null; L.orig = text;
    if (newToks.length) { L.a = newToks[0].s; L.lastStart = newToks[newToks.length - 1].s; L.e = newToks[newToks.length - 1].e; }
    if (row) { row.classList.remove("dirty", "unsure"); row.dataset.a = L.a; row.dataset.e = L.e; const w = $(".warn", row); if (w) w.innerHTML = "";
      if (!text) { row.classList.add("gone"); setTimeout(() => row.remove(), 250); S.lines = S.lines.filter(x => x !== L); }
      else { row.classList.add("saved"); setTimeout(() => row.classList.remove("saved"), 900); } }
    setState(ic("check") + " " + (text ? T("Saved", "Enregistré") : T("Subtitle deleted", "Sous-titre supprimé")), "ok");
    updateUndoBtn();
    renderSubLive(getVideo().currentTime, true);
  } catch (e) { setState(T("Couldn't save", "Erreur d'enregistrement"), "err"); toast(e.message, "err"); }
  L.saving = false;
}
function updateUndoBtn() { const b = $("#sbUndo"); if (!b) return; const n = (S.undo || []).length; b.disabled = !n; b.innerHTML = undoLabel(n); }
async function undoSub(c) {
  const u = (S.undo || []).pop(); if (!u) return;
  try {
    await api("POST", `/api/projects/${S.project.id}/transcript/words`, u);
    await loadSubWords(c); setState(ic("undo") + " " + T("Change undone", "Modification annulée"));
  } catch (e) { toast(e.message, "err"); }
  updateUndoBtn();
}
document.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z" && S.tab === "moments" && !$(".modal-bg")) {
    const ae = document.activeElement;
    if (ae && ae.tagName === "INPUT" && ae.closest(".tline") && ae.value.trim() !== (S.lines || []).find(l => l.id === ae.closest(".tline").dataset.id)?.orig) return; // annulation native du texte en cours
    const c = clipById(S.sel); if (c && (S.undo || []).length) { e.preventDefault(); undoSub(c); }
  }
});
async function pickWord(s) {
  const v = getVideo(); v.pause();
  const c = clipById(S.sel); if (!c) return;
  if (S.edTab !== "subs") { S.edTab = "subs"; renderEdTab(c); }
  if (!S.lines) renderLines(c);
  const L = (S.lines || []).find(l => (l.preview || l.toks).some(w => Math.abs(w.s - s) < 0.001));
  if (!L) return;
  let row = $(`#tlines .tline[data-id="${L.id}"]`); if (!row) return;
  if (row.style.display === "none") { S.onlyUnsure = false; const f = $("#sbUnsure"); if (f) f.checked = false; renderLines(c); row = $(`#tlines .tline[data-id="${L.id}"]`); }
  const inp = $("input", row);
  let off = 0, sel = [0, 0];
  for (const w of (L.preview || L.toks)) { const len = w.w.length; if (Math.abs(w.s - s) < 0.001) { sel = [off, off + len]; break; } off += len + 1; }
  const box = $("#tlines"); box.scrollTop = row.offsetTop - box.offsetTop - 60;
  inp.focus({ preventScroll: true }); inp.setSelectionRange(sel[0], sel[1]);
  row.classList.add("flash"); setTimeout(() => row.classList.remove("flash"), 700);
}
function distributeWords(text, a, b) {
  const toks = text.split(/\s+/).filter(Boolean);
  if (!toks.length) return [];
  b = Math.max(b, a + 0.12 * toks.length);
  const total = toks.reduce((n, t) => n + t.length + 1, 0);
  let t = a;
  return toks.map(tok => { const d = (b - a) * (tok.length + 1) / total; const w = { s: +t.toFixed(3), e: +(t + d * 0.92).toFixed(3), orig: tok, w: tok, del: false, p: 1, edited: true }; t += d; return w; });
}
/* ---- éditeur de timing mot par mot (ajout d'un sous-titre oublié / resynchronisation) ---- */
async function openTiming(c, L, opts = {}) {
  const v = getVideo(); v.pause();
  if (L && document.activeElement && document.activeElement.closest && document.activeElement.closest(".tline")) document.activeElement.blur();
  const st = S.settings.subtitles;
  let words = L ? (L.preview || L.toks).map(w => ({ w: w.w, s: w.s, e: w.e })) : [];
  const t0 = opts.t0 != null ? opts.t0 : Math.max(c.start, Math.min(c.end - 1, v.currentTime || c.start));
  let ws, we;
  const frame = () => {
    const a = words.length ? words[0].s : t0, b = words.length ? words[words.length - 1].e : t0 + 2;
    ws = Math.max(0, a - 1.2); we = Math.max(b + 1.2, ws + 4);
  };
  frame();
  let sel = 0, rate = 1, sync = null, wave = { start: ws, values: [] };
  const listenTxt = () => `${ic("play")} ${T("Listen", "Écouter")}`, pauseTxt = () => `${ic("pause")} Pause`, syncTxt = () => `${ic("mic")} ${T("Sync by tapping", "Synchroniser en tapant")}`;
  const m = modal(L ? T("Word timing", "Timing des mots") : T("Add a word or sentence", "Ajouter un mot ou une phrase"), `
    <label class="f"><span>${L ? T("Line text", "Texte de la ligne") : T("Missing word or sentence", "Mot ou phrase oubliés")} <span class="hint">— ${T("words are placed from the playhead, then adjustable", "les mots sont placés à partir de la position de lecture, puis ajustables")}</span></span>
      <input type="text" id="tmText" value="${esc(words.map(w => w.w).join(" "))}" placeholder="${T("e.g. what is this boss", "ex. mais c'est quoi ce boss")}"></label>
    <div class="tm-prev" id="tmPrev"></div>
    <div class="tm-tl" id="tmTl"><canvas id="tmWave"></canvas><div id="tmBlocks"></div><div class="tm-ph" id="tmPh"></div><div class="tm-ruler" id="tmRuler"></div></div>
    <div class="row" style="flex-wrap:wrap;gap:10px;justify-content:space-between">
      <div class="row" style="gap:8px;flex-wrap:wrap">
        <button class="btn sm primary" id="tmPlay">${listenTxt()}</button>
        <div class="chips" id="tmRate"><div class="chip small on" data-r="1">1×</div><div class="chip small" data-r="0.75">0.75×</div><div class="chip small" data-r="0.5">0.5×</div></div>
        <button class="btn sm" id="tmSync" title="${T("Starts playback: press Space (or the button) at the start of each word", "Lance la lecture : tape Espace (ou le bouton) au début de chaque mot")}">${syncTxt()}</button>
      </div>
      <div class="row small" style="gap:6px" id="tmSel"></div>
    </div>
    <div class="small muted" id="tmHelp">${T("Drag a word to move it, drag its edges to change when it <b>lights up</b> (start) and when it ends. The subtitle appears at the start of its first word.", "Glisse un mot pour le déplacer, ses bords pour changer quand il <b>s'allume</b> (début) et quand il se termine. Le sous-titre apparaît au début de son premier mot.")} <span class="kbd">${T("Space", "Espace")}</span> = ${T("play / pause", "écouter / pause")}.</div>`,
    { wide: true, footer: `<button class="btn ghost" id="tmCancel">${T("Cancel", "Annuler")}</button><button class="btn primary" id="tmSave">${ic("check")} ${T("Save", "Enregistrer")}</button>` });
  const tl = $("#tmTl", m.el), cv = $("#tmWave", m.el), blocks = $("#tmBlocks", m.el), ph = $("#tmPh", m.el), prev = $("#tmPrev", m.el);
  const W = () => tl.clientWidth;
  const t2x = t => (t - ws) / (we - ws) * W(), x2t = x => ws + x / W() * (we - ws);
  const loadWave = async () => {
    try { wave = await api("GET", `/api/projects/${S.project.id}/wave?start=${ws}&end=${we}`); } catch (_) { wave = { start: ws, values: [] }; }
    drawWave();
  };
  const drawWave = () => {
    cv.width = W(); cv.height = tl.clientHeight - 18;
    const ctx = cv.getContext("2d"); ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = `rgba(${getComputedStyle(document.documentElement).getPropertyValue("--accent-rgb")}, .55)`;
    const mid = cv.height / 2;
    (wave.values || []).forEach((val, i) => { const t = wave.start + i / wave.rate; const x = t2x(t); if (x < 0 || x > cv.width) return; const h = val * mid * 0.95; ctx.fillRect(x, mid - h, Math.max(1, cv.width / ((we - ws) * 100)), h * 2); });
    const r = $("#tmRuler", m.el); r.innerHTML = "";
    const step = (we - ws) > 8 ? 1 : 0.5;
    for (let t = Math.ceil(ws / step) * step; t < we; t += step) { const d = document.createElement("span"); d.style.left = t2x(t) + "px"; d.textContent = fmtP(t); r.appendChild(d); }
  };
  const renderSel = () => {
    const w = words[sel], box = $("#tmSel", m.el);
    if (!w) { box.innerHTML = ""; return; }
    box.innerHTML = `<b>« ${esc(w.w)} »</b> ${T("lights up at", "s'allume à")} <button class="btn sm" data-n="s,-0.05">−</button><span class="tval">${fmtP(w.s)}</span><button class="btn sm" data-n="s,0.05">+</button>
      ${T("end", "fin")} <button class="btn sm" data-n="e,-0.05">−</button><span class="tval">${fmtP(w.e)}</span><button class="btn sm" data-n="e,0.05">+</button>`;
    $$("[data-n]", box).forEach(b => b.onclick = () => { const [k, d] = b.dataset.n.split(","); nudge(sel, k, +d); });
  };
  const clampW = i => {
    const w = words[i], p = words[i - 1], n = words[i + 1];
    w.s = Math.max(p ? p.s + 0.03 : 0, w.s); w.e = Math.max(w.s + 0.05, w.e);
    if (n && w.e > n.s) w.e = Math.max(w.s + 0.05, n.s - 0.01);
  };
  const nudge = (i, k, d) => { const w = words[i]; w[k] = +(w[k] + d).toFixed(3); clampW(i); if (k === "s") v.currentTime = w.s; renderBlocks(); };
  const renderBlocks = () => {
    blocks.innerHTML = words.map((w, i) => `<div class="tm-w ${i === sel ? "sel" : ""}" data-i="${i}" style="left:${t2x(w.s)}px;width:${Math.max(6, t2x(w.e) - t2x(w.s))}px"><i class="l"></i><span>${esc(w.w)}</span><i class="r"></i></div>`).join("");
    $$(".tm-w", blocks).forEach(el => {
      el.onpointerdown = e => {
        e.preventDefault();
        const i = +el.dataset.i, w = words[i], mode = e.target.classList.contains("l") ? "l" : e.target.classList.contains("r") ? "r" : "m";
        const sx = e.clientX, s0 = w.s, e0 = w.e; sel = i; renderSel();
        $$(".tm-w", blocks).forEach(x => x.classList.toggle("sel", x === el));
        el.setPointerCapture(e.pointerId);
        let moved = false;
        el.onpointermove = ev => {
          const dt = (ev.clientX - sx) / W() * (we - ws); if (Math.abs(ev.clientX - sx) > 2) moved = true;
          const p = words[i - 1], n = words[i + 1];
          if (mode === "m") { const len = e0 - s0; let ns = s0 + dt; ns = Math.max(p ? p.e + 0.01 : ws, Math.min((n ? n.s - 0.01 : we) - len, ns)); w.s = ns; w.e = ns + len; }
          else if (mode === "l") w.s = Math.max(p ? p.e + 0.01 : ws, Math.min(w.e - 0.05, s0 + dt));
          else w.e = Math.min(n ? n.s - 0.01 : we, Math.max(w.s + 0.05, e0 + dt));
          el.style.left = t2x(w.s) + "px"; el.style.width = Math.max(6, t2x(w.e) - t2x(w.s)) + "px"; renderSel();
        };
        el.onpointerup = () => { el.onpointermove = null; v.currentTime = mode === "r" ? Math.max(w.s, w.e - 0.4) : w.s; if (!moved) v.currentTime = w.s; };
      };
    });
    renderSel();
  };
  const textToWords = () => {
    const toks = $("#tmText", m.el).value.split(/\s+/).filter(Boolean);
    if (!toks.length) { words = []; renderBlocks(); return; }
    const a = words.length ? words[0].s : t0;
    const b = words.length ? words[words.length - 1].e : a + 0.32 * toks.length;
    const span = Math.max(b - a, 0.25 * toks.length);
    if (toks.length === words.length) words.forEach((w, i) => w.w = toks[i]);
    else {
      const total = toks.reduce((n, t) => n + t.length + 1, 0); let t = a;
      words = toks.map(tok => { const d = span * (tok.length + 1) / total; const w = { w: tok, s: t, e: t + d * 0.9 }; t += d; return w; });
    }
    sel = Math.min(sel, words.length - 1);
    const oldWs = ws, oldWe = we; frame(); if (oldWs !== ws || oldWe !== we) loadWave();
    renderBlocks();
  };
  $("#tmText", m.el).oninput = textToWords;
  const renderPrev = t => {
    let active = null; for (const w of words) if (w.s <= t + 0.01) active = w;
    const on = words.length && t >= words[0].s - 0.01 && t < words[words.length - 1].e + 0.35;
    prev.classList.toggle("off", !on);
    Object.assign(prev.style, { fontFamily: `"${st.font}", Impact, sans-serif`, WebkitTextStroke: `${Math.max(1, st.outline * 0.45)}px ${st.outline_color}` });
    prev.innerHTML = words.length ? words.map(w => `<span style="color:${on && w === active ? st.highlight : st.color}">${esc(subDisplay(w.w))}</span>`).join(" ") : `<span class="dim" style="-webkit-text-stroke:0;font-family:var(--font);font-size:15px">${T("Type your text above", "Tape ton texte ci-dessus")}</span>`;
    ph.style.left = t2x(t) + "px";
  };
  let alive = true;
  const loop = () => { if (!alive) return; renderPrev(v.currentTime); if (!v.paused && v.currentTime >= we) v.pause(); requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
  const play = () => { if (v.paused) { if (v.currentTime < ws || v.currentTime >= we - 0.05) v.currentTime = ws; v.playbackRate = rate; S.playEnd = we; v.play(); } else v.pause(); };
  $("#tmPlay", m.el).onclick = play;
  v.addEventListener("play", () => { const b = $("#tmPlay", m.el); if (b) b.innerHTML = pauseTxt(); });
  v.addEventListener("pause", () => { const b = $("#tmPlay", m.el); if (b) b.innerHTML = listenTxt(); if (sync) stopSync(); });
  $$("#tmRate .chip", m.el).forEach(ch => ch.onclick = () => { $$("#tmRate .chip", m.el).forEach(x => x.classList.remove("on")); ch.classList.add("on"); rate = +ch.dataset.r; v.playbackRate = rate; });
  tl.onpointerdown = e => { if (e.target === tl || e.target === cv || e.target.id === "tmRuler") { const r = tl.getBoundingClientRect(); v.currentTime = x2t(e.clientX - r.left); } };
  // synchronisation en tapant : un appui = début du mot suivant, un dernier appui = fin du dernier mot
  const help = $("#tmHelp", m.el), helpTxt = help.innerHTML;
  const stopSync = () => { sync = null; $("#tmSync", m.el).classList.remove("on"); $("#tmSync", m.el).innerHTML = syncTxt(); help.innerHTML = helpTxt; v.playbackRate = 1; const o1 = ws, o2 = we; frame(); if (o1 !== ws || o2 !== we) loadWave(); renderBlocks(); };
  const tap = () => {
    if (!sync) return;
    const t = v.currentTime, i = sync.i;
    if (i < words.length) {
      const len = words[i].e - words[i].s;
      words[i].s = t; words[i].e = t + Math.min(len, 0.6);
      if (i > 0) words[i - 1].e = Math.max(words[i - 1].s + 0.05, t - 0.02);
      sync.i++;
      help.innerHTML = sync.i < words.length ? `${T("Next word:", "Mot suivant :")} <b>« ${esc(words[sync.i].w)} »</b> — ${T("press", "appuie sur")} <span class="kbd">${T("Space", "Espace")}</span> ${T("when it starts.", "quand il commence.")}` : `${T("Press one last time when", "Appuie une dernière fois quand")} <b>« ${esc(words[words.length - 1].w)} »</b> ${T("ends.", "se termine.")}`;
    } else { words[i - 1].e = Math.max(words[i - 1].s + 0.05, t); v.pause(); stopSync(); }
    renderBlocks();
  };
  $("#tmSync", m.el).onclick = () => {
    if (sync) { v.pause(); return stopSync(); }
    if (!words.length) return toast(T("Type the text first.", "Tape d'abord le texte."), "err");
    sync = { i: 0 };
    $("#tmSync", m.el).classList.add("on"); $("#tmSync", m.el).innerHTML = `${ic("x")} ${T("Stop", "Arrêter")}`;
    help.innerHTML = `${T("Listen… press", "Écoute… appuie sur")} <span class="kbd">${T("Space", "Espace")}</span> ${T("when", "quand")} <b>« ${esc(words[0].w)} »</b> ${T("starts.", "commence.")}`;
    v.currentTime = Math.max(ws, words[0].s - 1.2); v.playbackRate = rate; S.playEnd = we + 5; v.play();
  };
  const onKey = e => {
    if (!document.body.contains(m.el)) return document.removeEventListener("keydown", onKey, true);
    if (document.activeElement && document.activeElement.id === "tmText") return;
    if (e.code === "Space") { e.preventDefault(); e.stopPropagation(); if (sync) tap(); else play(); }
  };
  document.addEventListener("keydown", onKey, true);
  const close = () => { alive = false; v.pause(); v.playbackRate = 1; document.removeEventListener("keydown", onKey, true); m.close(); };
  $("#tmCancel", m.el).onclick = close;
  $("[data-x]", m.el).addEventListener("click", () => { alive = false; v.playbackRate = 1; document.removeEventListener("keydown", onKey, true); });
  $("#tmSave", m.el).onclick = async () => {
    if (!words.length && !L) return close();
    const sorted = words.slice().sort((x, y) => x.s - y.s);
    const payload = sorted.map(w => ({ word: w.w, start: +w.s.toFixed(3), end: +w.e.toFixed(3) }));
    try {
      if (L && L.saving) await new Promise(r => setTimeout(r, 400));
      await api("POST", `/api/projects/${S.project.id}/transcript/words`, { a: L ? L.a : null, b: L ? L.lastStart : null, words: payload });
      S.undo = S.undo || [];
      const oldWords = L ? L.toks.map(w => ({ word: w.w, start: +w.s.toFixed(3), end: +w.e.toFixed(3) })) : [];
      if (payload.length) S.undo.push({ a: payload[0].start, b: payload[payload.length - 1].start, words: oldWords });
      else if (L) S.undo.push({ a: null, b: null, words: oldWords });
      close();
      toast(L ? T("Timing saved", "Timing enregistré") : T("Subtitle added", "Sous-titre ajouté"), "ok");
      await loadSubWords(c);
      updateUndoBtn();
    } catch (e) { toast(e.message, "err"); }
  };
  renderBlocks(); await loadWave(); renderBlocks();
  if (!L) setTimeout(() => $("#tmText", m.el).focus(), 50);
}
async function reexportClip(c) {
  const m = modal(T("Re-exporting the Short", "Ré-export du Short"), `<div class="small muted">${T("The existing file is replaced:", "Le fichier existant est remplacé :")}</div><div class="mono small" style="word-break:break-all">${esc((c.export || {}).file || "")}</div>
    <div class="progress"><i id="rxBar"></i></div><div class="small muted" id="rxMsg">${T("Rendering…", "Rendu en cours…")}</div>`);
  try {
    const r = await api("POST", `/api/projects/${S.project.id}/export`, { clip_ids: [c.id], reexport: true });
    const tick = async () => {
      const j = await api("GET", `/api/jobs/${r.job}`);
      const b = $("#rxBar", m.el); if (b) b.style.width = Math.round(j.overall * 100) + "%";
      if (j.status === "running") return setTimeout(tick, 600);
      if (j.status === "done") { chime(true); $("#rxMsg", m.el).innerHTML = `<span class="yes">${ic("check")} ${T("Short re-exported.", "Short ré-exporté.")}</span> <a href="#" id="rxOpen">${T("Open folder", "Ouvrir le dossier")}</a>`; $("#rxOpen", m.el).onclick = e => { e.preventDefault(); api("POST", "/api/open-folder", { path: j.result.files[0] }); }; await loadProject(S.project.id); }
      else $("#rxMsg", m.el).textContent = T("Error: ", "Erreur : ") + j.error;
    };
    tick();
  } catch (e) { $("#rxMsg", m.el).textContent = e.message; }
}
const SCOPES = [["clip", ["This Short", "Ce Short"]], ["accepted", ["Accepted Shorts", "Shorts validés"]], ["clips", ["All suggested moments", "Tous les moments proposés"]], ["all", ["Whole VOD", "Toute la VOD"]]];
function openReplace(c) {
  const m = modal(T("Find / replace in subtitles", "Rechercher / remplacer dans les sous-titres"), `
    <div class="grid2">
      <label class="f"><span>${T("Word or phrase to find", "Mot ou expression à trouver")}</span><input type="text" id="rpFind" placeholder="${T("e.g. wesh", "ex. wesh")}"></label>
      <label class="f"><span>${T("Replace with", "Remplacer par")} <span class="hint">${T("(empty = delete)", "(vide = supprimer)")}</span></span><input type="text" id="rpWith" placeholder="${T("e.g. that's crazy", "ex. c'est ouf")}"></label>
    </div>
    <div class="row" style="gap:12px;flex-wrap:wrap"><span class="small muted">${T("Where:", "Où :")}</span>
      <div class="chips" id="rpScope">${SCOPES.map(([k, l]) => `<div class="chip small ${k === "accepted" ? "on" : ""}" data-k="${k}">${T(l[0], l[1])}</div>`).join("")}</div></div>
    <div class="small muted">${T("Case, accents and punctuation are ignored. A multi-word phrase is replaced as a block, keeping its timing.", "Majuscules, accents et ponctuation sont ignorés. Une expression de plusieurs mots est remplacée en bloc, avec son timing.")}</div>
    <div id="rpRes" class="rp-res"></div>`, { wide: true, footer: `<button class="btn" id="rpSearch">${ic("search")} ${T("Search", "Rechercher")}</button><button class="btn primary" id="rpGo" disabled>${T("Replace all", "Remplacer tout")}</button>` });
  const scope = () => $(".chip.on", $("#rpScope", m.el)).dataset.k;
  $$("#rpScope .chip", m.el).forEach(ch => ch.onclick = () => { $$("#rpScope .chip", m.el).forEach(x => x.classList.remove("on")); ch.classList.add("on"); search(); });
  const body = () => ({ find: $("#rpFind", m.el).value, replace: $("#rpWith", m.el).value, scope: scope(), clip_id: c.id });
  const search = async () => {
    if (!$("#rpFind", m.el).value.trim()) return;
    try {
      const r = await api("POST", `/api/projects/${S.project.id}/transcript/replace`, { ...body(), preview: true });
      $("#rpGo", m.el).disabled = !r.count;
      $("#rpGo", m.el).textContent = r.count ? T(`Replace ${r.count} occurrence(s)`, `Remplacer les ${r.count} occurrence(s)`) : T("Replace all", "Remplacer tout");
      $("#rpRes", m.el).innerHTML = r.count ? r.matches.map(x => `<div class="rp-row" data-t="${x.t}"><span class="mono small dim">${fmt(x.t)}</span>
        <span>…${esc(x.before)} <mark>${esc(x.match)}</mark> ${esc(x.after)}…</span></div>`).join("") : `<div class="muted small">${T("No match.", "Aucune occurrence.")}</div>`;
      $$(".rp-row", m.el).forEach(r2 => r2.onclick = () => { getVideo().currentTime = +r2.dataset.t; });
    } catch (e) { toast(e.message, "err"); }
  };
  $("#rpFind", m.el).onkeydown = e => { if (e.key === "Enter") search(); };
  $("#rpWith", m.el).onkeydown = e => { if (e.key === "Enter") search(); };
  $("#rpSearch", m.el).onclick = search;
  $("#rpGo", m.el).onclick = async () => {
    try {
      const r = await api("POST", `/api/projects/${S.project.id}/transcript/replace`, body());
      m.close(); toast(T(`${r.count} occurrence(s) replaced`, `${r.count} occurrence(s) remplacée(s)`), "ok"); S.undo = []; await loadSubWords(c); updateUndoBtn();
    } catch (e) { toast(e.message, "err"); }
  };
  setTimeout(() => $("#rpFind", m.el).focus(), 50);
}
function openRedo(c) {
  const st = S.settings;
  const game = (S.project.game || {}).name || "";
  const m = modal(T("Recompute subtitles", "Recalculer les sous-titres"), `
    <div class="claude-note">${ic("info")} ${T("Whisper listens again to the chosen moments with the most accurate settings (<b>large-v3</b> model, deeper search, anti-hallucination filter). <b>Manual corrections on these moments will be replaced.</b>",
      "Whisper réécoute les passages choisis avec les réglages les plus précis (modèle <b>large-v3</b>, recherche approfondie, filtre anti-hallucinations). <b>Les corrections manuelles de ces passages seront remplacées.</b>")}</div>
    <div class="row" style="gap:12px;flex-wrap:wrap"><span class="small muted">${T("Which moments:", "Quels passages :")}</span>
      <div class="chips" id="rdScope">${SCOPES.filter(x => x[0] !== "all").map(([k, l]) => `<div class="chip small ${k === "clip" ? "on" : ""}" data-k="${k}">${T(l[0], l[1])}</div>`).join("")}</div></div>
    <div class="row" style="gap:12px;flex-wrap:wrap"><span class="small muted">${T("Accuracy:", "Précision :")}</span>
      <div class="chips" id="rdPrec"><div class="chip small on" data-k="max">${T("Maximum — large-v3 (first use: ~3 GB download)", "Maximale — large-v3 (1er usage : téléchargement ~3 Go)")}</div><div class="chip small" data-k="fast">${T("Fast — large-v3-turbo", "Rapide — large-v3-turbo")}</div></div></div>
    <label class="f"><span>${T("Words to recognise well", "Mots à bien reconnaître")} <span class="hint">${T("(names, game terms, nicknames — comma separated)", "(noms propres, termes du jeu, pseudos — séparés par des virgules)")}</span></span>
      <textarea id="rdVocab" rows="3" placeholder="${T("e.g. Phantom Blade Zero, Soul, parry, Krimossimo", "ex. Phantom Blade Zero, Soul, parade, Krimossimo")}">${esc(st.vocabulary || game)}</textarea></label>
    <div id="rdProg" style="display:none"><div class="small muted" id="rdMsg">${T("Starting…", "Démarrage…")}</div><div class="progress" style="margin-top:8px"><i id="rdBar"></i></div></div>`,
    { wide: true, footer: `<button class="btn primary" id="rdGo">${ic("target")} ${T("Recompute", "Recalculer")}</button>` });
  const pick = id => { $$(`#${id} .chip`, m.el).forEach(ch => ch.onclick = () => { $$(`#${id} .chip`, m.el).forEach(x => x.classList.remove("on")); ch.classList.add("on"); }); };
  pick("rdScope"); pick("rdPrec");
  $("#rdGo", m.el).onclick = async () => {
    const b = { scope: $("#rdScope .chip.on", m.el).dataset.k, precision: $("#rdPrec .chip.on", m.el).dataset.k, vocabulary: $("#rdVocab", m.el).value.trim(), clip_id: c.id };
    $("#rdGo", m.el).disabled = true; $("#rdProg", m.el).style.display = "block";
    try {
      const r = await api("POST", `/api/projects/${S.project.id}/transcript/redo`, b);
      S.settings.vocabulary = b.vocabulary;
      const tick = async () => {
        const j = await api("GET", `/api/jobs/${r.job}`);
        const stp = j.steps[0] || {};
        if ($("#rdMsg", m.el)) { $("#rdMsg", m.el).textContent = stp.message || (j.status === "running" ? T("Waiting…", "En attente…") : ""); $("#rdBar", m.el).style.width = Math.round(j.overall * 100) + "%"; }
        if (j.status === "running") return setTimeout(tick, 700);
        if (j.status === "done") { chime(true); m.close(); toast(T(`Subtitles recomputed (${j.result.words} words)`, `Sous-titres recalculés (${j.result.words} mots)`), "ok"); S.undo = []; await loadProject(S.project.id); renderEditor(); }
        else { $("#rdGo", m.el).disabled = false; toast(T("Error: ", "Erreur : ") + j.error, "err"); }
      };
      tick();
    } catch (e) { $("#rdGo", m.el).disabled = false; toast(e.message, "err"); }
  };
}
function drawShort(ctx, img, c, CW, CH, opts = {}) {
  const info = S.project.info, IW = info.width, IH = info.height, k = img.naturalWidth / IW;
  const lay = opts.layout || resolveLayout(c), lc = layoutCfg();
  ctx.fillStyle = "#000"; ctx.fillRect(0, 0, CW, CH);
  if (!img.naturalWidth) return;
  const center = ar => { const w = Math.min(IW, IH * ar), h = Math.min(IH, w / ar); return { x: (IW - w) / 2, y: (IH - h) / 2, w, h }; };
  const fit = (r, ar) => coverRect({ ...r }, ar, IW, IH);
  const blit = (r, dx, dy, dw, dh) => ctx.drawImage(img, r.x * k, r.y * k, r.w * k, r.h * k, dx, dy, dw, dh);
  const gr = gameRect(c);
  if (FACECAM.includes(lay) && S.project.facecam) {
    const ch = Math.round(CH * lc.cam_frac), gh = CH - ch, gar = CW / gh, car = CW / ch;
    const g = gr ? fit(gr, gar) : center(gar);
    const bottom = lc.cam_pos === "bottom";
    blit(g, 0, bottom ? 0 : ch, CW, gh);
    blit(fit(S.project.facecam, car), 0, bottom ? gh : 0, CW, ch);
  } else if (lay === "blur_fill") {
    ctx.save(); ctx.filter = "blur(10px) brightness(.85)"; blit(center(CW / CH), -10, -10, CW + 20, CH + 20); ctx.restore();
    const g = gr ? fit(gr, 16 / 9) : { x: 0, y: 0, w: IW, h: IH };
    const h = CW / (g.w / g.h); blit(g, 0, (CH - h) / 2, CW, h);
  } else {
    blit(gr ? fit(gr, CW / CH) : center(CW / CH), 0, 0, CW, CH);
  }
}
function defaultSubY(c) {
  const lay = resolveLayout(c), lc = layoutCfg(), st = S.settings.subtitles;
  if (c.sub_pos) return c.sub_pos;
  if (st.position === "custom" && st.pos) return st.pos;
  let pos = st.position === "custom" ? "auto" : st.position;
  if (pos === "auto") pos = FACECAM.includes(lay) ? "seam" : lay === "blur_fill" ? "bas" : "bh";
  const seam = lc.cam_pos === "bottom" ? 1 - lc.cam_frac - 0.09 : lc.cam_frac + 0.09;
  return { x: 0.5, y: { haut: 0.2, milieu: 0.5, bas: 0.8, bh: 0.7, seam }[pos] ?? 0.72 };
}
async function openSubPos(c) {
  const st = S.settings.subtitles;
  let words = [];
  try { words = (await api("GET", `/api/projects/${S.project.id}/transcript?start=${c.start}&end=${c.end}`)).words; } catch (_) { }
  const sample = (words.slice(0, Math.max(1, st.max_words)).map(w => w.word.trim()).join(" ") || T("YOUR SUBTITLES HERE", "TES SOUS-TITRES ICI"));
  let pos = { ...defaultSubY(c) };
  const t = Math.max(c.start, Math.min(c.end, getVideo().currentTime || c.peak));
  const CW = 324, CH = 576;
  const m = modal(T("Subtitle position", "Position des sous-titres"), `
    <div class="lay-ed" style="grid-template-columns:auto 1fr">
      <div class="subwrap" id="subWrap" style="width:${CW}px;height:${CH}px">
        <canvas id="spCv" width="${CW}" height="${CH}"></canvas>
        <div class="guide" id="gH"></div>
        <div class="subdrag" id="subDrag"></div>
        <img id="spImg" src="/api/projects/${S.project.id}/frame?t=${t}&r=${Date.now()}" style="display:none">
      </div>
      <div style="display:grid;gap:14px;align-content:start">
        <div class="small muted">${T("Drag the text where you want it in the Short. It snaps to the horizontal centre. The preview uses your framing and subtitle style (set in the Export tab).", "Glisse le texte à l'endroit voulu dans le Short. Il s'aimante au centre horizontal. L'aperçu reprend ton cadrage et ton style de sous-titres (réglables dans l'onglet Export).")}</div>
        <div class="chips"><div class="chip small" data-y="0.2">${T("Top", "Haut")}</div><div class="chip small" data-y="0.5">${T("Middle", "Milieu")}</div><div class="chip small" data-y="0.8">${T("Bottom", "Bas")}</div><div class="chip small" id="spCenter">${T("Centre horizontally", "Centrer horizontalement")}</div></div>
        <div class="small muted mono" id="spInfo"></div>
      </div>
    </div>`, { wide: true, footer: `<button class="btn ghost left" id="spReset">${T("Automatic position", "Position automatique")}</button><button class="btn" id="spAll">${T("Apply to all Shorts", "Appliquer à tous les Shorts")}</button><button class="btn primary" id="spOne">${T("Apply to this Short", "Appliquer à ce Short")}</button>` });
  const cv = $("#spCv", m.el), ctx = cv.getContext("2d"), img = $("#spImg", m.el), drag = $("#subDrag", m.el), gH = $("#gH", m.el);
  const scale = CW / 1080;
  drag.innerHTML = sample.split(/\s+/).map((w, i) => `<span style="color:${i === Math.min(1, st.max_words - 1) ? st.highlight : st.color}">${esc(st.uppercase ? w.toUpperCase() : w)}</span>`).join(" ");
  Object.assign(drag.style, { fontFamily: `"${st.font}", Impact, sans-serif`, fontSize: st.size * scale + "px",
    WebkitTextStroke: `${st.outline * scale * 2}px ${st.outline_color}`, paintOrder: "stroke fill" });
  const place = () => {
    drag.style.left = pos.x * CW + "px"; drag.style.top = pos.y * CH + "px";
    gH.style.display = Math.abs(pos.x - 0.5) < 0.004 ? "block" : "none";
    $("#spInfo", m.el).textContent = `x ${Math.round(pos.x * 100)} % · y ${Math.round(pos.y * 100)} %`;
  };
  img.onload = () => drawShort(ctx, img, c, CW, CH);
  place();
  drag.onpointerdown = e => {
    e.preventDefault();
    const r = $("#subWrap", m.el).getBoundingClientRect();
    drag.setPointerCapture(e.pointerId);
    drag.onpointermove = ev => {
      let x = (ev.clientX - r.left) / CW, y = (ev.clientY - r.top) / CH;
      x = Math.max(0.08, Math.min(0.92, x)); y = Math.max(0.04, Math.min(0.96, y));
      if (Math.abs(x - 0.5) < 0.03) x = 0.5;
      pos = { x, y }; place();
    };
    drag.onpointerup = () => drag.onpointermove = null;
  };
  $$("[data-y]", m.el).forEach(ch => ch.onclick = () => { pos.y = +ch.dataset.y; place(); });
  $("#spCenter", m.el).onclick = () => { pos.x = 0.5; place(); };
  const r3 = v => Math.round(v * 1000) / 1000;
  $("#spOne", m.el).onclick = async () => {
    c.sub_pos = { x: r3(pos.x), y: r3(pos.y) }; await patchClip(c, { sub_pos: c.sub_pos });
    m.close(); renderEditor(); toast(T("Subtitle position saved for this Short", "Position des sous-titres enregistrée pour ce Short"), "ok");
  };
  $("#spAll", m.el).onclick = async () => {
    const sub = { ...S.settings.subtitles, position: "custom", pos: { x: r3(pos.x), y: r3(pos.y) } };
    S.settings = await api("POST", "/api/settings", { subtitles: sub });
    for (const x of S.project.clips) if (x.sub_pos) { x.sub_pos = null; await patchClip(x, { sub_pos: null }); }
    m.close(); renderEditor(); toast(T("Position applied to all Shorts", "Position appliquée à tous les Shorts"), "ok");
  };
  $("#spReset", m.el).onclick = async () => {
    c.sub_pos = null; await patchClip(c, { sub_pos: null });
    if (S.settings.subtitles.position === "custom") S.settings = await api("POST", "/api/settings", { subtitles: { ...S.settings.subtitles, position: "auto" } });
    m.close(); renderEditor(); toast(T("Automatic position restored", "Position automatique rétablie"));
  };
}

/* ------------------------------------------------------------------ cadrage sur la vidéo */
function drawOverlay(c) {
  const ov = $("#ov9"), cam = $("#ovCam"), pw = $("#pw");
  if (!ov || !pw) return;
  const show = S.showOv !== false;
  const info = S.project.info;
  if (!show || !info) { ov.style.display = cam.style.display = "none"; return; }
  const W = pw.clientWidth, H = pw.clientHeight, ar = info.width / info.height;
  let dw = W, dh = W / ar; if (dh > H) { dh = H; dw = H * ar; }
  const ox = (W - dw) / 2, oy = (H - dh) / 2, sc = dw / info.width;
  const lay = resolveLayout(c);
  let frac = 1;
  if (lay === "smart_crop" || lay === "center_crop") frac = Math.min(1, (info.height * 9 / 16) / info.width);
  const lc = layoutCfg();
  if (FACECAM.includes(lay)) frac = Math.min(1, (info.height * 1080 / (1920 * (1 - lc.cam_frac))) / info.width);
  const gr = gameRect(c);
  if (lay === "blur_fill" && !gr) { ov.style.display = "none"; }
  else if (gr) {
    ov.style.display = "block";
    Object.assign(ov.style, { left: ox + gr.x * sc + "px", top: oy + gr.y * sc + "px", width: gr.w * sc + "px", height: gr.h * sc + "px" });
  } else {
    ov.style.display = "block";
    const w = dw * frac;
    Object.assign(ov.style, { left: ox + (dw - w) / 2 + "px", top: oy + "px", width: w + "px", height: dh + "px" });
  }
  const f = S.project.facecam;
  if (f && FACECAM.includes(lay)) {
    cam.style.display = "block";
    Object.assign(cam.style, { left: ox + f.x * sc + "px", top: oy + f.y * sc + "px", width: f.w * sc + "px", height: f.h * sc + "px" });
  } else cam.style.display = "none";
}
function sceneAspect(c) {
  const lay = resolveLayout(c);
  if (FACECAM.includes(lay)) return 1080 / (1920 * (1 - layoutCfg().cam_frac));
  if (lay === "blur_fill") return 16 / 9;
  return 9 / 16;
}
function startCrop(c) {
  const pw = $("#pw"), info = S.project.info, v = getVideo();
  if (!pw || $("#cropLayer")) return;
  v.pause(); v.controls = false;
  pw.scrollIntoView({ block: "start", behavior: "smooth" });
  const ovPrev = S.showOv; S.showOv = false; drawOverlay(c);
  const ar = sceneAspect(c), IW = info.width, IH = info.height;
  const lc = layoutCfg();
  let r = c.game_crop ? coverRect({ ...c.game_crop }, ar, IW, IH)
    : (FACECAM.includes(resolveLayout(c)) && lc.game) ? coverRect({ ...lc.game }, ar, IW, IH)
      : (() => { const w = Math.min(IW, IH * ar), h = Math.min(IH, w / ar); return { x: (IW - w) / 2, y: (IH - h) / 2, w, h }; })();
  const layer = document.createElement("div");
  layer.id = "cropLayer"; layer.className = "cropLayer";
  layer.innerHTML = `<div class="lrect game" id="cropRect" style="display:block"><span>${T("Scene", "Scène")}</span><div class="rs"></div></div>`;
  const bar = document.createElement("div");
  bar.className = "cropBar";
  bar.innerHTML = `<span class="small">${T("Drag the <b>Scene</b> frame onto the game area to keep · corner = size", "Glisse le cadre <b>Scène</b> sur la zone du jeu à garder · coin = taille")}</span>
    <span style="flex:1"></span><button class="btn sm" id="cropAuto">${ic("wand")} ${T("Follow the action (auto)", "Suivre l'action (auto)")}</button>
    <button class="btn sm ghost" id="cropCancel">${T("Cancel", "Annuler")}</button><button class="btn sm primary" id="cropSave">${ic("check")} ${T("Save", "Enregistrer")}</button>`;
  pw.appendChild(layer); pw.appendChild(bar);
  const rect = $("#cropRect", layer);
  const geo = () => {
    const W = pw.clientWidth, H = pw.clientHeight, a = IW / IH;
    let dw = W, dh = W / a; if (dh > H) { dh = H; dw = H * a; }
    return { ox: (W - dw) / 2, oy: (H - dh) / 2, sc: dw / IW };
  };
  const draw = () => { const g = geo(); Object.assign(rect.style, { left: g.ox + r.x * g.sc + "px", top: g.oy + r.y * g.sc + "px", width: r.w * g.sc + "px", height: r.h * g.sc + "px" }); };
  draw();
  rect.onpointerdown = e => {
    e.preventDefault(); e.stopPropagation();
    const resize = e.target.classList.contains("rs"), sx = e.clientX, sy = e.clientY, b0 = { ...r }, g = geo();
    rect.setPointerCapture(e.pointerId);
    rect.onpointermove = ev => {
      const dx = (ev.clientX - sx) / g.sc, dy = (ev.clientY - sy) / g.sc;
      if (resize) {
        let w = Math.max(60, b0.w + dx), h = w / ar;
        if (b0.x + w > IW) { w = IW - b0.x; h = w / ar; }
        if (b0.y + h > IH) { h = IH - b0.y; w = h * ar; }
        Object.assign(r, { w, h });
      } else { r.x = b0.x + dx; r.y = b0.y + dy; clampRect(r, IW, IH); }
      draw();
    };
    rect.onpointerup = () => rect.onpointermove = null;
  };
  const onRs = () => draw();
  window.addEventListener("resize", onRs);
  const close = () => { layer.remove(); bar.remove(); v.controls = true; window.removeEventListener("resize", onRs); S.showOv = ovPrev; drawOverlay(c); };
  $("#cropCancel", bar).onclick = close;
  $("#cropAuto", bar).onclick = async () => {
    c.game_crop = null; c.layout = S.project.facecam ? "facecam_top" : "smart_crop";
    await patchClip(c, { game_crop: null, layout: c.layout }); close(); renderEditor(); toast(T("This Short will follow the action automatically", "Ce Short suivra l'action automatiquement"));
  };
  $("#cropSave", bar).onclick = async () => {
    c.game_crop = { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.w), h: Math.round(r.h) };
    const upd = { game_crop: c.game_crop };
    if (TRACKING.includes(c.layout)) { c.layout = c.layout === "facecam_top" ? "facecam_fixed" : "center_crop"; upd.layout = c.layout; }
    await patchClip(c, upd); close(); renderEditor(); toast(T("Scene framing saved — check it with the 9:16 preview", "Cadrage de la scène enregistré — vérifie avec l'Aperçu 9:16"), "ok");
  };
}
async function preview9(c) {
  if ($(".modal-bg")) return;
  const m = modal(T("9:16 preview", "Aperçu 9:16"), `<div style="display:grid;place-items:center;gap:14px;min-height:200px" id="pv"><div class="muted">${T("Rendering the preview…", "Rendu de l'aperçu…")}</div>
    <div class="progress" style="width:300px"><i id="pvBar"></i></div></div>`);
  try {
    const r = await api("POST", `/api/projects/${S.project.id}/clips/${c.id}/preview`, {});
    const tick = async () => {
      const j = await api("GET", `/api/jobs/${r.job}`);
      if (j.status === "running") { const b = $("#pvBar", m.el); if (b) b.style.width = Math.round(j.overall * 100) + "%"; setTimeout(tick, 500); return; }
      if (j.status === "error") { $("#pv", m.el).innerHTML = `<div style="color:var(--bad)">${esc(j.error)}</div>`; return; }
      $("#pv", m.el).innerHTML = `<video src="${j.result.url}" controls autoplay style="height:min(70vh,720px);aspect-ratio:9/16;border-radius:24px;background:#000;box-shadow:var(--shadow-3)"></video>
        <div class="small muted">${T("Low-resolution preview — the final export is 1080×1920.", "Aperçu basse résolution — l'export final est en 1080×1920.")}</div>`;
    };
    tick();
  } catch (e) { $("#pv", m.el).innerHTML = `<div style="color:var(--bad)">${esc(e.message)}</div>`; }
}
async function addManual() {
  const v = getVideo(), t = v.currentTime || 0;
  const len = (S.settings.duration_min + S.settings.duration_max) / 2;
  try {
    const c = await api("POST", `/api/projects/${S.project.id}/clips`, { start: Math.max(0, t - len * 0.4), end: Math.min(S.project.info.duration, t + len * 0.6) });
    await loadProject(S.project.id); S.sel = c.id; S.listTab = "accepted"; renderMoments(); toast(T("Moment added and accepted", "Passage ajouté et validé"), "ok");
  } catch (e) { toast(e.message, "err"); }
}

/* ------------------------------------------------------------------ caméra & cadrage (façon clips Twitch) */
function layoutCfg() { return Object.assign({ cam_frac: 0.36, cam_pos: "top", game: null, track: false }, S.project.layout_cfg || {}); }
function coverRect(r, ar, W, H) {
  let { x, y, w, h } = r;
  if (w / h > ar) { const nw = h * ar; x += (w - nw) / 2; w = nw; } else { const nh = w / ar; y += (h - nh) / 2; h = nh; }
  return clampRect({ x, y, w, h }, W, H);
}
function clampRect(r, W, H) {
  r.w = Math.min(r.w, W); r.h = Math.min(r.h, H);
  r.x = Math.max(0, Math.min(W - r.w, r.x)); r.y = Math.max(0, Math.min(H - r.h, r.y));
  return r;
}
function openFacecam() {
  const p = S.project, info = p.info, c = clipById(S.sel);
  const cfg = layoutCfg();
  let frac = cfg.cam_frac, pos = cfg.cam_pos, auto = !!cfg.track;
  const IW = info.width, IH = info.height;
  const camAR = () => 1080 / (1920 * frac), gameAR = () => 1080 / (1920 * (1 - frac));
  let cam = p.facecam ? coverRect({ ...p.facecam }, camAR(), IW, IH) : clampRect({ x: IW * 0.02, y: IH * 0.55, w: IW * 0.15, h: IW * 0.15 / camAR() }, IW, IH);
  let game = cfg.game ? coverRect({ ...cfg.game }, gameAR(), IW, IH) : clampRect({ x: (IW - IH * gameAR()) / 2, y: 0, w: IH * gameAR(), h: IH }, IW, IH);
  const times = [c ? c.peak : info.duration / 2, ...p.clips.map(x => x.peak)];
  let ti = 0;
  const detectTxt = () => `${ic("search")} ${T("Find my camera automatically", "Localiser ma caméra automatiquement")}`;
  const m = modal(T("Camera & Short framing", "Caméra & cadrage du Short"), `
    <div class="lay-ed">
      <div style="min-width:0">
        <div class="small muted" style="margin-bottom:12px">${T("Place the <b>Camera</b> frame on your webcam and the <b>Game</b> frame on the area to keep. Drag to move, pull the corner to resize — the preview on the right shows the final Short.",
          "Place le cadre <b>Caméra</b> sur ta webcam et le cadre <b>Jeu</b> sur la zone à garder. Glisse pour déplacer, tire le coin pour redimensionner — l'aperçu à droite montre le Short final.")}</div>
        <div class="fcbox" id="fcb"><img id="fcImg" src="/api/projects/${p.id}/frame?t=${times[0]}&r=${Date.now()}">
          <div class="lrect cam" id="rCam"><span>${T("Camera", "Caméra")}</span><div class="rs"></div></div>
          <div class="lrect game" id="rGame"><span>${T("Game", "Jeu")}</span><div class="rs"></div></div></div>
        <div class="row" style="flex-wrap:wrap;gap:10px;margin-top:12px">
          <button class="btn sm" id="lDetect">${detectTxt()}</button>
          <div class="seg" id="lMode"><div class="${auto ? "" : "on"}" data-m="fixed" title="${T("The game frame stays still", "Le cadre du jeu ne bouge pas")}">${ic("target")} ${T("Fixed game", "Jeu fixe")}</div><div class="${auto ? "on" : ""}" data-m="track" title="${T("The game area follows the on-screen action", "La zone du jeu suit l'action à l'écran")}">${ic("zap")} ${T("Game follows the action", "Jeu qui suit l'action")}</div></div>
          <button class="btn sm ghost" id="lFrame">${ic("refresh")} ${T("Another frame", "Autre image")}</button>
        </div>
      </div>
      <div style="display:grid;gap:14px;align-content:start;justify-items:center">
        <canvas id="lPrev" width="270" height="480" class="phonec"></canvas>
        <label class="f" style="width:100%"><span>${T("Camera size", "Taille de la caméra")}: <b id="lFracV">${Math.round(frac * 100)} %</b></span>
          <input type="range" id="lFrac" min="18" max="55" value="${Math.round(frac * 100)}"></label>
        <div class="chips"><div class="chip small ${pos !== "bottom" ? "on" : ""}" data-pos="top">${T("Camera on top", "Caméra en haut")}</div><div class="chip small ${pos === "bottom" ? "on" : ""}" data-pos="bottom">${T("Camera at bottom", "Caméra en bas")}</div></div>
      </div>
    </div>`, { wide: true, footer: `<button class="btn ghost left" id="fcNone">${T("No camera", "Pas de caméra")}</button><button class="btn primary" id="fcSave">${ic("check")} ${T("Apply to all Shorts", "Appliquer à tous les Shorts")}</button>` });
  const img = $("#fcImg", m.el), rc = $("#rCam", m.el), rg = $("#rGame", m.el), cv = $("#lPrev", m.el), ctx = cv.getContext("2d");
  const sc = () => img.clientWidth / IW;
  const place = (el, r) => Object.assign(el.style, { display: "block", left: r.x * sc() + "px", top: r.y * sc() + "px", width: r.w * sc() + "px", height: r.h * sc() + "px" });
  const draw = () => {
    place(rc, cam);
    rg.style.display = auto ? "none" : "block"; if (!auto) place(rg, game);
    const k = img.naturalWidth / IW, CW = cv.width, CH = cv.height, ch = Math.round(CH * frac), gh = CH - ch;
    ctx.fillStyle = "#000"; ctx.fillRect(0, 0, CW, CH);
    if (!img.naturalWidth) return;
    const gy = pos === "bottom" ? 0 : ch, cy = pos === "bottom" ? gh : 0;
    let g = game;
    if (auto) { const w = Math.min(IW, IH * gameAR()); g = { x: (IW - w) / 2, y: 0, w, h: Math.min(IH, w / gameAR()) }; }
    ctx.drawImage(img, g.x * k, g.y * k, g.w * k, g.h * k, 0, gy, CW, gh);
    ctx.drawImage(img, cam.x * k, cam.y * k, cam.w * k, cam.h * k, 0, cy, CW, ch);
    ctx.fillStyle = "rgba(255,255,255,.85)"; ctx.fillRect(0, pos === "bottom" ? gh - 1 : ch - 1, CW, 2);
  };
  const conform = () => {
    const ccx = cam.x + cam.w / 2, ccy = cam.y + cam.h / 2;
    cam.h = cam.w / camAR(); if (cam.h > IH) { cam.h = IH; cam.w = IH * camAR(); }
    cam.x = ccx - cam.w / 2; cam.y = ccy - cam.h / 2; clampRect(cam, IW, IH);
    const gcx = game.x + game.w / 2, gcy = game.y + game.h / 2;
    game.h = game.w / gameAR(); if (game.h > IH) { game.h = IH; game.w = IH * gameAR(); }
    if (game.w > IW) { game.w = IW; game.h = IW / gameAR(); }
    game.x = gcx - game.w / 2; game.y = gcy - game.h / 2; clampRect(game, IW, IH);
  };
  const bind = (el, get, arFn) => {
    el.onpointerdown = e => {
      e.preventDefault();
      const r = get(), resize = e.target.classList.contains("rs"), sx = e.clientX, sy = e.clientY, b0 = { ...r };
      el.setPointerCapture(e.pointerId);
      el.onpointermove = ev => {
        const dx = (ev.clientX - sx) / sc(), dy = (ev.clientY - sy) / sc();
        if (resize) {
          let w = Math.max(40, b0.w + dx), h = w / arFn();
          if (b0.x + w > IW) { w = IW - b0.x; h = w / arFn(); }
          if (b0.y + h > IH) { h = IH - b0.y; w = h * arFn(); }
          Object.assign(r, { w, h });
        } else { r.x = b0.x + dx; r.y = b0.y + dy; clampRect(r, IW, IH); }
        draw();
      };
      el.onpointerup = () => el.onpointermove = null;
    };
  };
  bind(rc, () => cam, camAR); bind(rg, () => game, gameAR);
  img.onload = () => { conform(); draw(); };
  window.addEventListener("resize", draw);
  $("#lFrac", m.el).oninput = e => { frac = e.target.value / 100; $("#lFracV", m.el).textContent = e.target.value + " %"; conform(); draw(); };
  $$("[data-pos]", m.el).forEach(ch => ch.onclick = () => { pos = ch.dataset.pos; $$("[data-pos]", m.el).forEach(x => x.classList.toggle("on", x === ch)); draw(); });
  $$("#lMode [data-m]", m.el).forEach(b => b.onclick = () => { auto = b.dataset.m === "track"; $$("#lMode [data-m]", m.el).forEach(x => x.classList.toggle("on", x === b)); draw(); });
  $("#lFrame", m.el).onclick = () => { ti = (ti + 1) % times.length; img.src = `/api/projects/${p.id}/frame?t=${times[ti]}&r=${Date.now()}`; };
  $("#lDetect", m.el).onclick = async () => {
    const b = $("#lDetect", m.el); b.disabled = true; b.innerHTML = `${ic("search")} ${T("Looking for your camera…", "Recherche de ta caméra…")}`;
    try {
      const r = await api("POST", `/api/projects/${p.id}/detect-facecam`);
      if (r.facecam) { cam = coverRect({ ...r.facecam }, camAR(), IW, IH); draw(); toast(T("Camera found — adjust if needed", "Caméra localisée — ajuste si besoin"), "ok"); }
      else toast(T("Camera not found automatically: place the frame by hand.", "Caméra non trouvée automatiquement : place le cadre à la main."), "err");
    } catch (e) { toast(e.message, "err"); }
    b.disabled = false; b.innerHTML = detectTxt();
  };
  $("#fcSave", m.el).onclick = async () => {
    await api("POST", `/api/projects/${p.id}/layout`, { cam, game: auto ? null : game, track: auto, cam_frac: frac, cam_pos: pos, apply_all: true });
    await loadProject(p.id); m.close(); window.removeEventListener("resize", draw); renderProject(); toast(T("Framing saved — applied to all Shorts set to “Automatic”", "Cadrage enregistré — appliqué à tous les Shorts en « Automatique »"), "ok");
  };
  $("#fcNone", m.el).onclick = async () => {
    await api("POST", `/api/projects/${p.id}/layout`, { cam: null, game: null, cam_frac: frac, cam_pos: pos });
    await loadProject(p.id); m.close(); window.removeEventListener("resize", draw); renderProject(); toast(T("Camera disabled", "Caméra désactivée"));
  };
}

/* ------------------------------------------------------------------ Claude manuel */
async function openClaude() {
  const p = S.project;
  let data;
  try { data = await api("GET", `/api/projects/${p.id}/claude-prompt`); } catch (e) { return toast(e.message, "err"); }
  const m = modal(T("Claude review — with your Claude Pro subscription", "Analyse Claude — avec ton abonnement Claude Pro"), `
    <div class="claude-note">${ic("sparkles")} ${T("No API key, no extra cost: you use claude.ai as usual. Claude reviews each moment, gives its opinion, suggests better titles and adjusts the bounds.",
      "Aucune clé API, aucun frais : tu utilises claude.ai comme d'habitude. Claude relit chaque moment, donne son avis, propose de meilleurs titres et ajuste les bornes.")}</div>
    <div><h3 style="margin-bottom:10px">${T("1 · Copy this prompt into a new claude.ai conversation", "1 · Copie ce prompt dans une nouvelle conversation claude.ai")}</h3>
      <textarea readonly rows="8" class="mono small" id="cp">${esc(data.prompt)}</textarea>
      <div class="row" style="margin-top:10px;flex-wrap:wrap;gap:8px"><button class="btn primary" id="cpBtn">${ic("copy")} ${T("Copy prompt", "Copier le prompt")}</button>
        <button class="btn" id="openClaude">${ic("external")} ${T("Open claude.ai", "Ouvrir claude.ai")}</button>
        <button class="btn" id="openImgs" title="${T("Drop these thumbnails into the conversation so Claude can see the pictures", "Glisse ces miniatures dans la conversation pour que Claude voie les images")}">${ic("image")} ${T("Thumbnails folder", "Dossier des miniatures")}</button></div></div>
    <div><h3 style="margin-bottom:10px">${T("2 · Paste Claude's answer here", "2 · Colle ici la réponse de Claude")}</h3>
      <textarea rows="7" class="mono small" id="cr" placeholder='{"clips": [ … ] }'></textarea></div>`,
    { wide: true, footer: `<button class="btn primary" id="crImport">${ic("download")} ${T("Import the answer", "Importer la réponse")}</button>` });
  $("#cpBtn", m.el).onclick = async () => { await copyText(data.prompt); toast(T("Prompt copied", "Prompt copié"), "ok"); };
  $("#openClaude", m.el).onclick = () => api("POST", "/api/open-url", { url: "https://claude.ai/new" });
  $("#openImgs", m.el).onclick = () => api("POST", "/api/open-folder", { path: data.folder });
  $("#crImport", m.el).onclick = async () => {
    try {
      const r = await api("POST", `/api/projects/${p.id}/claude-import`, { text: $("#cr", m.el).value });
      await loadProject(p.id); m.close(); renderProject(); toast(T(`${r.updated.length} moment(s) updated by Claude`, `${r.updated.length} moment(s) mis à jour par Claude`), "ok");
    } catch (e) { toast(e.message, "err"); }
  };
}

/* ------------------------------------------------------------------ onglet Export */
function renderExport() {
  const p = S.project, st = S.settings, body = $("#tabBody");
  const acc = p.clips.filter(c => c.status === "accepted").sort((a, b) => a.start - b.start);
  const sub = st.subtitles;
  const xf = Object.assign({ txt: false, md: false, json: false }, st.export_files || {});
  const hook = Object.assign({ enabled: false, seconds: 3, color: "#7C6CFF" }, st.hook || {});
  const bar = Object.assign({ enabled: false, color: "#FFFFFF", height: 10 }, st.progress_bar || {});
  const wm = Object.assign({ enabled: false, text: "", position: "bottom" }, st.watermark || {});
  const firstThumb = acc[0] || p.clips[0];
  const sel = (id, opts, cur) => `<select id="${id}">${opts.map(([v, l]) => `<option value="${v}" ${String(cur) === String(v) ? "selected" : ""}>${l}</option>`).join("")}</select>`;
  body.innerHTML = `<div class="export-grid">
    <div style="display:grid;gap:18px">
      <div class="card" id="xJob" style="display:none"></div>
      ${S.exportResult ? `<div class="done-box"><h2><span class="ok-ic">${ic("check")}</span>${T(`${S.exportResult.files.length} Short(s) exported`, `${S.exportResult.files.length} Short(s) exporté(s)`)}</h2>
        <div class="small muted mono" style="margin:10px 0 14px;word-break:break-all">${esc(S.exportResult.dir)}</div>
        <div class="row" style="flex-wrap:wrap"><button class="btn primary" id="openOut">${ic("folder")} ${T("Open folder", "Ouvrir le dossier")}</button><span class="small muted">${xf.txt ? T("Each MP4 comes with a .txt holding title, description and hashtags per platform.", "Chaque MP4 est accompagné d'un .txt avec titre, description et hashtags par plateforme.") : T("MP4 videos ready to post.", "Vidéos MP4 prêtes à publier.")}</span></div></div>` : ""}
      <div class="card"><div class="card-h" style="margin-bottom:14px"><h3>${ic("film")} ${T("Accepted Shorts", "Shorts validés")} (${acc.length})</h3>
        <button class="btn sm ghost" id="backM">${ic("arrowL")} ${T("Back to moments", "Retour aux moments")}</button></div>
        <div class="xlist">${acc.length ? acc.map((c, i) => `<div class="xitem">
          <div class="th" style="background-image:url(/api/projects/${p.id}/thumb/${c.id})"></div>
          <div style="min-width:0"><div style="font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${i + 1}. ${esc(c.title)}</div>
            <div class="small muted">${fmtVod(c.start)} → ${fmtVod(c.end)} · ${Math.round(c.end - c.start)} s · ${esc(layoutName(resolveLayout(c)))}</div>
            <div class="mono fname" data-id="${c.id}">${ic("file")}<span>${esc(fileStem(c, st.file_naming || "title"))}.mp4</span></div></div>
          <div class="small">${c.export ? `<span class="tag ok">${ic("check")} ${T("exported", "exporté")}</span>` : ""}</div></div>`).join("")
      : `<div class="muted">${T("No accepted moment. Go back to “Moments” to accept your favourites.", "Aucun passage validé. Retourne dans « Moments » pour valider tes préférés.")}</div>`}</div></div>
      <div class="card" style="display:grid;gap:16px">
        <div class="card-h"><h3>${ic("file")} ${T("File names", "Noms des fichiers")}</h3></div>
        <div class="grid2" style="align-items:end">
          <label class="f"><span>${T("VOD name", "Nom de la VOD")}</span><div class="row" style="gap:8px"><input type="text" id="xName" value="${esc(p.name)}" placeholder="${T("e.g. Phantom Blade Zero EP1", "ex. Phantom Blade Zero EP1")}"><button class="btn" id="xNameOk">${T("Rename", "Renommer")}</button></div></label>
          <div class="chips" id="xNaming">${[["title", T("01 - Short title", "01 - Titre du Short")], ["series", T("VOD name - Short 1", "Nom de la VOD - Short 1")], ["series_title", T("Name - Short 1 - Title", "Nom - Short 1 - Titre")]].map(([k, l]) => `<div class="chip small ${(st.file_naming || "title") === k ? "on" : ""}" data-k="${k}">${l}</div>`).join("")}</div>
        </div>
        <div class="small muted">${T("Shorts are numbered in VOD order (Short 1 = the earliest moment). The export folder is named after the VOD too:", "Les Shorts sont numérotés dans l'ordre de la VOD (Short 1 = le premier moment). Le dossier d'export prend aussi le nom de la VOD :")} <b>${esc(safeName(p.name, 80))} - Shorts</b>.</div>
        <div class="f"><span class="lab">${T("Files to create", "Fichiers à créer")}</span>
          <div class="xfiles">
            <label class="xf on-always"><input type="checkbox" checked disabled> <b>${T("MP4 videos", "Vidéos MP4")}</b><span>${T("always", "toujours")}</span></label>
            <label class="xf"><input type="checkbox" id="xfTxt" ${xf.txt ? "checked" : ""}> <b>${T("Publishing text", "Texte de publication")}</b><span>${T("one .txt per Short: titles, description, YouTube / TikTok / Reels hashtags", "un .txt par Short : titres, description, hashtags YouTube / TikTok / Reels")}</span></label>
            <label class="xf"><input type="checkbox" id="xfMd" ${xf.md ? "checked" : ""}> <b>${T("Summary", "Récapitulatif")}</b><span>${T("PUBLICATION.md: every Short on one page", "PUBLICATION.md : tous les Shorts sur une page")}</span></label>
            <label class="xf"><input type="checkbox" id="xfJson" ${xf.json ? "checked" : ""}> <b>${T("Data", "Données")}</b><span>${T("shorts.json: timings, scores, metadata", "shorts.json : horaires, scores, métadonnées")}</span></label>
          </div></div>
      </div>
      <div class="card" style="display:grid;gap:16px">
        <div class="card-h"><h3>${ic("captions")} ${T("Subtitles", "Sous-titres")}</h3><label class="toggle small"><input type="checkbox" class="switch" id="sEn" ${sub.enabled ? "checked" : ""}> ${T("Animated subtitles", "Sous-titres animés")}</label></div>
        <div class="grid3">
          <label class="f"><span>${T("Font", "Police")}</span><select id="sFont">${S.fonts.map(f => `<option ${sub.font === f.name ? "selected" : ""}>${esc(f.name)}</option>`).join("")}</select></label>
          <label class="f"><span>${T("Size", "Taille")}: <b id="sSizeV">${sub.size}</b></span><input type="range" id="sSize" min="50" max="130" value="${sub.size}"></label>
          <label class="f"><span>${T("Words per line", "Mots par ligne")}: <b id="sMwV">${sub.max_words}</b></span><input type="range" id="sMw" min="1" max="6" value="${sub.max_words}"></label>
        </div>
        <div class="grid3">
          <label class="f"><span>Position</span>${sel("sPos", [["auto", T("Automatic", "Automatique")], ["haut", T("Top", "Haut")], ["milieu", T("Middle", "Milieu")], ["bas", T("Bottom", "Bas")], ["custom", T("Custom (set in Moments)", "Personnalisée (dans Moments)")]], sub.position)}</label>
          <div class="row" style="gap:14px;align-items:flex-end">
            <label class="f"><span>${T("Text", "Texte")}</span><input type="color" id="sCol" value="${sub.color}"></label>
            <label class="f"><span>${T("Active word", "Mot actif")}</span><input type="color" id="sHl" value="${sub.highlight}"></label>
            <label class="f"><span>${T("Outline", "Contour")}</span><input type="color" id="sOc" value="${sub.outline_color}"></label></div>
          <label class="f"><span>${T("Outline width", "Épaisseur contour")}: <b id="sOV">${sub.outline}</b></span><input type="range" id="sOut" min="0" max="12" value="${sub.outline}"></label>
        </div>
        <div class="row" style="gap:22px"><label class="toggle small"><input type="checkbox" id="sUp" ${sub.uppercase ? "checked" : ""}> ${T("UPPERCASE", "MAJUSCULES")}</label>
          <label class="toggle small"><input type="checkbox" id="sAn" ${sub.animation ? "checked" : ""}> ${T("“Pop” animation", "Animation « pop »")}</label></div>
      </div>
      <div class="card" style="display:grid;gap:14px">
        <div class="card-h"><h3>${ic("sparkles")} ${T("Retention boosters", "Boosters de rétention")}</h3><span class="small dim">${T("optional", "optionnel")}</span></div>
        <div class="opts">
          <div class="opt"><input type="checkbox" class="switch" id="hEn" ${hook.enabled ? "checked" : ""}><b>${T("Hook title", "Titre d'accroche")}</b>
            <span class="d">${T("The Short's title pops up at the top during the first seconds.", "Le titre du Short s'affiche en haut pendant les premières secondes.")}</span>
            <div class="more"><label class="f" style="flex:1"><span>${T("Duration", "Durée")}: <b id="hSecV">${hook.seconds}</b> s</span><input type="range" id="hSec" min="1" max="6" step="0.5" value="${hook.seconds}"></label>
              <label class="f"><span>${T("Colour", "Couleur")}</span><input type="color" id="hCol" value="${hook.color}"></label></div></div>
          <div class="opt"><input type="checkbox" class="switch" id="bEn" ${bar.enabled ? "checked" : ""}><b>${T("Progress bar", "Barre de progression")}</b>
            <span class="d">${T("A thin bar fills along the bottom — viewers watch until the end.", "Une fine barre se remplit en bas — on regarde jusqu'au bout.")}</span>
            <div class="more"><label class="f" style="flex:1"><span>${T("Thickness", "Épaisseur")}: <b id="bHV">${bar.height}</b></span><input type="range" id="bH" min="4" max="24" value="${bar.height}"></label>
              <label class="f"><span>${T("Colour", "Couleur")}</span><input type="color" id="bCol" value="${bar.color}"></label></div></div>
          <div class="opt"><input type="checkbox" class="switch" id="wEn" ${wm.enabled ? "checked" : ""}><b>${T("Watermark", "Filigrane")}</b>
            <span class="d">${T("Your channel name, discreet, in a corner.", "Le nom de ta chaîne, discret, dans un coin.")}</span>
            <div class="more"><label class="f" style="flex:1"><span>${T("Text", "Texte")}</span><input type="text" id="wTxt" value="${esc(wm.text)}" placeholder="@Krimossimo"></label>
              <label class="f"><span>${T("Place", "Place")}</span>${sel("wPos", [["top", T("Top", "Haut")], ["top-right", T("Top right", "Haut droite")], ["bottom", T("Bottom", "Bas")], ["bottom-right", T("Bottom right", "Bas droite")], ["bottom-left", T("Bottom left", "Bas gauche")]], wm.position)}</label></div></div>
        </div>
      </div>
      <div class="card" style="display:grid;gap:16px">
        <div class="card-h"><h3>${ic("video")} ${T("Video", "Vidéo")}</h3></div>
        <div class="grid3">
          <label class="f"><span>${T("Default layout", "Cadrage par défaut")}</span><select id="xLay"><option value="auto">${T("Automatic", "Automatique")}</option>${S.layouts.map(k => `<option value="${k}" ${st.layout === k ? "selected" : ""}>${esc(layoutName(k))}</option>`).join("")}</select></label>
          <label class="f"><span>${T("Frame rate", "Images / seconde")}</span>${sel("xFps", [["60", T("60 (smooth)", "60 (fluide)")], ["30", T("30 (lighter)", "30 (plus léger)")]], st.fps)}</label>
          <label class="f"><span>${T("Quality", "Qualité")}</span>${sel("xQ", [["standard", "Standard"], ["haute", T("High (recommended)", "Haute (recommandé)")], ["max", T("Maximum", "Maximale")]], st.quality)}</label>
        </div>
        <div class="row" style="gap:22px;flex-wrap:wrap"><label class="toggle small"><input type="checkbox" id="xLn" ${st.loudnorm ? "checked" : ""}> ${T("Normalised volume (-14 LUFS)", "Volume normalisé (-14 LUFS)")}</label>
          <label class="toggle small"><input type="checkbox" id="xFd" ${st.fade ? "checked" : ""}> ${T("Soft fades in/out", "Fondus doux début/fin")}</label>
          <label class="toggle small"><input type="checkbox" id="xOpen" ${st.open_after_export ? "checked" : ""}> ${T("Open the folder when done", "Ouvrir le dossier à la fin")}</label></div>
        <label class="f"><span>${T("Export folder", "Dossier d'export")}</span><div class="row" style="gap:8px"><input type="text" id="xDir" value="${esc(st.export_dir || "")}" placeholder="${T("Next to the VOD:", "À côté de la VOD :")} ${esc(p.export_dir)}">
          <button class="btn" id="xPick">${ic("folder")} ${T("Browse", "Parcourir")}</button></div></label>
      </div>
    </div>
    <div style="position:sticky;top:0;display:grid;gap:16px">
      <div class="phone" id="phone" style="background-image:url(/api/projects/${p.id}/thumb/${firstThumb ? firstThumb.id : ""})">${p.facecam ? `<div class="cam" style="height:${layoutCfg().cam_frac * 100}%;${layoutCfg().cam_pos === "bottom" ? "top:auto;bottom:0" : ""}"></div>` : ""}
        <div class="hookprev" id="hookprev"></div><div class="subprev" id="subprev"></div><div class="markprev" id="markprev"></div><div class="barprev" id="barprev"></div></div>
      <button class="btn primary big" id="xGo" ${acc.length ? "" : "disabled"}>${ic("download", "lg")} ${T("Export", "Exporter")} ${acc.length} ${plural(acc.length, "Short", "Shorts", "Short", "Shorts")}</button>
      <div class="xsum">MP4 1080×1920 · H.264 ${S.status && S.status.ffmpeg && S.status.ffmpeg.nvenc ? "NVENC (GPU)" : "libx264"} · AAC 192 kb/s</div>
    </div></div>`;
  const ph = $("#phone");
  ph.style.backgroundSize = "cover";
  const readSub = () => ({
    enabled: $("#sEn").checked, font: $("#sFont").value, size: +$("#sSize").value, max_words: +$("#sMw").value, position: $("#sPos").value,
    color: $("#sCol").value, highlight: $("#sHl").value, outline_color: $("#sOc").value, outline: +$("#sOut").value,
    uppercase: $("#sUp").checked, animation: $("#sAn").checked, shadow: sub.shadow, pos: sub.pos,
  });
  const readAll = () => ({
    subtitles: readSub(), layout: $("#xLay").value, fps: +$("#xFps").value, quality: $("#xQ").value,
    loudnorm: $("#xLn").checked, fade: $("#xFd").checked, export_dir: $("#xDir").value.trim(), open_after_export: $("#xOpen").checked,
    file_naming: ($(".chip.on", $("#xNaming")) || { dataset: { k: "title" } }).dataset.k,
    export_files: { txt: $("#xfTxt").checked, md: $("#xfMd").checked, json: $("#xfJson").checked },
    hook: { enabled: $("#hEn").checked, seconds: +$("#hSec").value, color: $("#hCol").value },
    progress_bar: { enabled: $("#bEn").checked, height: +$("#bH").value, color: $("#bCol").value },
    watermark: { enabled: $("#wEn").checked, text: $("#wTxt").value, position: $("#wPos").value },
  });
  const preview = () => {
    const s = readSub(), all = readAll(), el = $("#subprev");
    $("#sSizeV").textContent = s.size; $("#sMwV").textContent = s.max_words; $("#sOV").textContent = s.outline;
    $("#hSecV").textContent = all.hook.seconds; $("#bHV").textContent = all.progress_bar.height;
    const scale = 300 / 1080, lc = layoutCfg();
    if (!s.enabled) el.innerHTML = "";
    else {
      const sample = LANG === "fr" ? ["NON", "MAIS", "C'EST", "PAS", "POSSIBLE", "!"] : ["NO", "WAY", "THAT", "JUST", "HAPPENED", "!"];
      const words = sample.slice(0, Math.max(1, s.max_words)).map(w => s.uppercase ? w : w.toLowerCase());
      el.innerHTML = words.map((w, i) => `<span style="color:${i === Math.min(1, words.length - 1) ? s.highlight : s.color}">${esc(w)}</span>`).join(" ");
      let pos = s.position;
      if (pos === "auto") pos = p.facecam ? "seam" : "bh";
      const seam = lc.cam_pos === "bottom" ? (1 - lc.cam_frac - 0.09) * 100 : (lc.cam_frac + 0.09) * 100;
      let y = { haut: 20, milieu: 50, bas: 80, bh: 70, seam }[pos];
      if (pos === "custom") y = ((sub.pos || {}).y ?? 0.7) * 100;
      Object.assign(el.style, { top: y + "%", fontFamily: `"${s.font}", Impact, sans-serif`, fontSize: s.size * scale + "px",
        WebkitTextStroke: `${s.outline * scale * 2}px ${s.outline_color}`, textShadow: `0 ${2 * scale * 2}px ${3 * scale * 2}px rgba(0,0,0,.6)` });
    }
    const hp = $("#hookprev"), h = all.hook;
    hp.style.display = h.enabled ? "block" : "none";
    if (h.enabled) {
      const top = p.facecam && lc.cam_pos !== "bottom" ? (lc.cam_frac + 0.04) * 100 : 10;
      Object.assign(hp.style, { top: top + "%", background: h.color, fontFamily: `"${s.font}", Impact, sans-serif` });
      const t = (acc[0] && acc[0].title) || T("This boss destroyed me", "Ce boss m'a détruit");
      hp.textContent = s.uppercase ? t.toUpperCase() : t;
    }
    const mp = $("#markprev"), w = all.watermark;
    mp.style.display = w.enabled && w.text.trim() ? "block" : "none";
    if (w.enabled) {
      mp.textContent = w.text; mp.style.fontFamily = `"${s.font}", Impact, sans-serif`;
      const v = w.position.startsWith("top") ? { top: "16px", bottom: "auto" } : { bottom: "18px", top: "auto" };
      const hz = w.position.endsWith("right") ? { right: "14px", left: "auto", transform: "none" } : w.position.endsWith("left") ? { left: "14px", right: "auto", transform: "none" } : { left: "50%", right: "auto", transform: "translateX(-50%)" };
      Object.assign(mp.style, v, hz);
    }
    const bp = $("#barprev"), b = all.progress_bar;
    bp.style.display = b.enabled ? "block" : "none";
    Object.assign(bp.style, { background: b.color, height: Math.max(2, b.height * 300 / 1080 * 1.2) + "px" });
  };
  preview();
  const save = debounce(async () => { S.settings = await api("POST", "/api/settings", readAll()); }, 500);
  $$("input,select", body).forEach(i => { if (i.id === "xName") return; i.addEventListener("input", () => { preview(); save(); }); i.addEventListener("change", () => { preview(); save(); }); });
  $("#backM").onclick = () => setTab("moments");
  const refreshNames = () => { const mode = $(".chip.on", $("#xNaming")).dataset.k; $$(".fname", body).forEach(el => { const c = clipById(el.dataset.id); if (c) $("span", el).textContent = `${fileStem(c, mode)}.mp4`; }); };
  $$("#xNaming .chip").forEach(ch => ch.onclick = () => { $$("#xNaming .chip").forEach(x => x.classList.remove("on")); ch.classList.add("on"); refreshNames(); save(); });
  const doRename = async () => {
    try { await api("PATCH", `/api/projects/${p.id}`, { name: $("#xName").value }); await loadProject(p.id); projCrumb(); renderProject(); toast(T("VOD renamed", "VOD renommée"), "ok"); }
    catch (e) { toast(e.message, "err"); }
  };
  $("#xNameOk").onclick = doRename;
  $("#xName").onkeydown = e => { if (e.key === "Enter") doRename(); };
  $("#xPick").onclick = async () => { const r = await api("POST", "/api/pick/folder"); if (r.path) { $("#xDir").value = r.path; save(); } };
  if ($("#openOut")) $("#openOut").onclick = () => api("POST", "/api/open-folder", { path: S.exportResult.dir });
  $("#xGo").onclick = async () => {
    try {
      S.settings = await api("POST", "/api/settings", readAll());
      S.exportResult = null;
      const r = await api("POST", `/api/projects/${p.id}/export`, { settings: readAll() });
      attachJob(r.job);
    } catch (e) { toast(e.message, "err"); }
  };
  if (S.job && S.job.kind === "export" && S.job.status === "running") renderExportJob();
}
function renderExportJob() {
  const j = S.job, box = $("#xJob");
  if (!box || !j) return;
  box.style.display = "block";
  const pct = Math.round(j.overall * 100);
  box.innerHTML = `<div class="row" style="justify-content:space-between"><h2>${T("Exporting…", "Export en cours…")} ${pct} %</h2><button class="btn sm" id="xCancel">${ic("x")} ${T("Cancel", "Annuler")}</button></div>
    <div class="progress" style="margin:14px 0"><i style="width:${pct}%"></i></div>
    <div class="steps">${j.steps.map(s => `<div class="stepl ${s.status}"><div class="ic">${stepIcon(s.status)}</div>
      <div style="min-width:0"><div class="lb" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(s.label)}</div>${s.message ? `<div class="msg">${esc(s.message)}</div>` : ""}</div>
      <div class="pct">${s.status === "running" ? Math.round(s.progress * 100) + " %" : ""}</div></div>`).join("")}</div>`;
  $("#xGo").disabled = true;
  $("#xCancel").onclick = () => api("POST", `/api/jobs/${j.id}/cancel`);
}

/* ------------------------------------------------------------------ réglages & diagnostic */
function openSettings(section = "general") {
  const s = S.settings;
  const oll = (S.status && S.status.ollama) || { running: false, models: [] };
  const NAV = [["general", "sliders", T("General", "Général")], ["analysis", "mic", T("Analysis", "Analyse")], ["publish", "hash", T("Publishing", "Publication")],
    ["ai", "sparkles", T("AI titles", "Titres par IA")], ["system", "cpu", T("System", "Système")]];
  const row = (title, desc, ctrl) => `<div class="set-row"><div class="t"><b>${title}</b>${desc ? `<span>${desc}</span>` : ""}</div><div class="c">${ctrl}</div></div>`;
  const sw = (id, on) => `<input type="checkbox" class="switch" id="${id}" ${on ? "checked" : ""}>`;
  const m = modal(T("Settings", "Réglages"), `<div class="set-wrap"><div class="set-nav" id="sNav">${NAV.map(([k, i, l]) => `<div data-k="${k}">${ic(i)} ${l}</div>`).join("")}</div><div class="set-body" id="sBody"></div></div>`,
    { wide: true, flush: true, footer: `<span class="small dim left" id="gState"></span><button class="btn primary" id="gDone">${T("Done", "Terminé")}</button>` });
  const saved = () => { const el = $("#gState", m.el); if (el) { el.innerHTML = `<span class="yes">${ic("check")} ${T("Saved", "Enregistré")}</span>`; clearTimeout(el._t); el._t = setTimeout(() => el.innerHTML = "", 1800); } };
  const put = async (data) => { S.settings = await api("POST", "/api/settings", data); saved(); };
  const draw = (k) => {
    $$("#sNav [data-k]", m.el).forEach(d => d.classList.toggle("on", d.dataset.k === k));
    const b = $("#sBody", m.el);
    if (k === "general") {
      b.innerHTML = `<h3>${T("Appearance", "Apparence")}</h3><div>
        ${row(T("Language", "Langue"), T("Language of the interface.", "Langue de l'interface."), `<div class="langs"><div class="lang ${LANG === "en" ? "on" : ""}" data-l="en"><span class="fl">EN</span>English</div><div class="lang ${LANG === "fr" ? "on" : ""}" data-l="fr"><span class="fl">FR</span>Français</div></div>`)}
        ${row(T("Accent colour", "Couleur d'accent"), T("Buttons, highlights and selections.", "Boutons, surlignages et sélections."), `<div class="swatches">${ACCENTS.map(([a, c1, c2]) => `<div class="sw ${(s.accent || "iris") === a ? "on" : ""}" data-a="${a}" title="${a}" style="background:linear-gradient(135deg,${c1},${c2})"></div>`).join("")}</div>`)}
        </div><h3>${T("Behaviour", "Comportement")}</h3><div>
        ${row(T("Sound when a task finishes", "Son à la fin d'une tâche"), T("A soft chime after analysis or export, plus a Windows notification if Vertical is in the background.", "Un petit carillon après une analyse ou un export, plus une notification Windows si Vertical est en arrière-plan."), `<div class="row" style="gap:10px"><button class="btn sm ghost" id="gTest">${ic("volume")} ${T("Test", "Tester")}</button>${sw("gSound", s.sound !== false)}</div>`)}
        ${row(T("Open the folder after export", "Ouvrir le dossier après l'export"), "", sw("gOpen", s.open_after_export))}
        ${row(T("Welcome screen", "Écran de bienvenue"), T("Show the introduction again.", "Revoir la présentation."), `<button class="btn sm" id="gWelcome">${T("Show", "Afficher")}</button>`)}</div>`;
      $$(".lang", b).forEach(el => el.onclick = async () => { setLang(el.dataset.l); await put({ ui_lang: LANG }); await refreshStatus(); m.close(); renderChrome(); await route(); openSettings("general"); });
      $$(".sw", b).forEach(el => el.onclick = async () => { setAccent(el.dataset.a); $$(".sw", b).forEach(x => x.classList.toggle("on", x === el)); await put({ accent: el.dataset.a }); });
      $("#gSound", b).onchange = e => put({ sound: e.target.checked });
      $("#gTest", b).onclick = () => { const was = S.settings.sound; S.settings.sound = true; chime(true); S.settings.sound = was; };
      $("#gOpen", b).onchange = e => put({ open_after_export: e.target.checked });
      $("#gWelcome", b).onclick = () => { m.close(); openWelcome(); };
    } else if (k === "analysis") {
      b.innerHTML = `<h3>${T("Transcription", "Transcription")}</h3>
        <label class="f"><span>${T("Whisper model", "Modèle Whisper")}</span><select id="gW">${[["auto", T("Automatic (large-v3-turbo on GPU)", "Automatique (large-v3-turbo sur GPU)")], ["large-v3-turbo", "large-v3-turbo"], ["large-v3", T("large-v3 (slower, most accurate)", "large-v3 (plus lent, plus précis)")], ["medium", "medium"], ["small", T("small (fast)", "small (rapide)")], ["base", T("base (very fast)", "base (très rapide)")]].map(([v, l]) => `<option value="${v}" ${s.whisper_model === v ? "selected" : ""}>${l}</option>`).join("")}</select></label>
        <label class="f"><span>${T("Vocabulary", "Vocabulaire")} <span class="hint">${T("— names, game terms, nicknames Whisper should recognise (comma separated)", "— noms propres, termes du jeu, pseudos que Whisper doit reconnaître (séparés par des virgules)")}</span></span>
          <textarea id="gVoc" rows="3" placeholder="Phantom Blade Zero, Soul, Krimossimo">${esc(s.vocabulary || "")}</textarea></label>`;
      $("#gW", b).onchange = e => put({ whisper_model: e.target.value });
      $("#gVoc", b).oninput = debounce(e => put({ vocabulary: e.target.value.trim() }), 600);
    } else if (k === "publish") {
      b.innerHTML = `<h3>${T("Publishing", "Publication")}</h3>
        <label class="f"><span>${T("Channel hashtags", "Hashtags de ta chaîne")} <span class="hint">${T("— added to every Short", "— ajoutés à chaque Short")}</span></span><input type="text" id="gTags" value="${esc(s.channel_hashtags)}" placeholder="#krimossimo #twitch"></label>
        <label class="f"><span>${T("Default export folder", "Dossier d'export par défaut")} <span class="hint">${T("— empty = next to the VOD", "— vide = à côté de la VOD")}</span></span><div class="row" style="gap:8px"><input type="text" id="gDir" value="${esc(s.export_dir)}"><button class="btn" id="gPick">${ic("folder")} ${T("Browse", "Parcourir")}</button></div></label>`;
      $("#gTags", b).oninput = debounce(e => put({ channel_hashtags: e.target.value }), 600);
      $("#gDir", b).oninput = debounce(e => put({ export_dir: e.target.value.trim() }), 600);
      $("#gPick", b).onclick = async () => { const r = await api("POST", "/api/pick/folder"); if (r.path) { $("#gDir", b).value = r.path; put({ export_dir: r.path }); } };
    } else if (k === "ai") {
      b.innerHTML = `<h3>Ollama ${T("(optional, free, local)", "(optionnel, gratuit, local)")}</h3>
        <div class="small muted">${T("If", "Si")} <a href="#" id="olLink">Ollama</a> ${T("is installed, a local model writes more natural titles. Otherwise Vertical uses its built-in generator (and the manual Claude review is always available).", "est installé, un modèle local rédige des titres plus naturels. Sinon Vertical utilise son générateur intégré (et l'analyse Claude manuelle reste disponible).")}</div>
        <div class="claude-note ${oll.running ? "" : "warn"}">${oll.running ? `${ic("check")} ${T("Ollama is running", "Ollama est actif")} — ${oll.models.length} ${plural(oll.models.length, "model", "models", "modèle", "modèles")}` : `${ic("info")} ${T("Ollama not detected", "Ollama non détecté")}`}</div>
        <div>${row(T("Use Ollama when it's running", "Utiliser Ollama s'il est lancé"), "", sw("gOl", s.use_ollama))}</div>
        <div class="grid2"><label class="f"><span>${T("Address", "Adresse")}</span><input type="text" id="gOlU" value="${esc(s.ollama_url)}"></label>
          <label class="f"><span>${T("Model", "Modèle")}</span><select id="gOlM"><option value="auto">${T("Automatic", "Automatique")}</option>${oll.models.map(x => `<option ${s.ollama_model === x ? "selected" : ""}>${esc(x)}</option>`).join("")}</select></label></div>`;
      $("#olLink", b).onclick = e => { e.preventDefault(); api("POST", "/api/open-url", { url: "https://ollama.com/download" }); };
      $("#gOl", b).onchange = e => put({ use_ollama: e.target.checked });
      $("#gOlU", b).oninput = debounce(e => put({ ollama_url: e.target.value.trim() }), 600);
      $("#gOlM", b).onchange = e => put({ ollama_model: e.target.value });
    } else {
      b.innerHTML = envHtml() + `<div class="row" style="gap:8px"><button class="btn sm" id="gRefresh">${ic("refresh")} ${T("Refresh", "Actualiser")}</button></div>`;
      $("#gRefresh", b).onclick = async () => { await refreshStatus(); draw("system"); };
    }
  };
  $$("#sNav [data-k]", m.el).forEach(d => d.onclick = () => draw(d.dataset.k));
  $("#gDone", m.el).onclick = m.close;
  draw(section);
}
function envHtml() {
  const e = S.status;
  if (!e) return `<div class="muted">${T("The system check is still running…", "Le diagnostic est encore en cours…")}</div>`;
  const yn = b => b ? `<span class="yes">${ic("check")} ${T("yes", "oui")}</span>` : `<span class="no">${ic("x")} ${T("no", "non")}</span>`;
  return `<table class="env-table">
    <tr><td>Python</td><td>${esc(e.python)}</td></tr>
    <tr><td>FFmpeg</td><td>${e.ffmpeg.available ? esc(e.ffmpeg.version) : yn(false)}</td></tr>
    <tr><td>${T("GPU encoding (NVENC)", "Encodage GPU NVENC")}</td><td>${yn(e.ffmpeg.nvenc)}</td></tr>
    <tr><td>${T("Subtitles (libass)", "Sous-titres (libass)")}</td><td>${yn(e.ffmpeg.libass)}</td></tr>
    <tr><td>GPU CUDA</td><td>${e.gpu.cuda ? esc(`${e.gpu.name} · ${e.gpu.vram_gb} ${T("GB", "Go")}`) : yn(false)}</td></tr>
    <tr><td>${T("Transcription (faster-whisper)", "Transcription faster-whisper")}</td><td>${yn(e.faster_whisper)}</td></tr>
    <tr><td>PyTorch + transformers (CLIP, AST)</td><td>${yn(e.torch && e.transformers)}</td></tr>
    <tr><td>OpenCV (facecam)</td><td>${yn(e.opencv)}</td></tr>
    <tr><td>${T("Native window", "Fenêtre native")}</td><td>${yn(e.webview)}</td></tr>
    <tr><td>Ollama</td><td>${e.ollama && e.ollama.running ? T(`running (${e.ollama.models.length} models)`, `actif (${e.ollama.models.length} modèles)`) : T("not detected (optional)", "non détecté (optionnel)")}</td></tr></table>
    ${e.notes && e.notes.length ? `<div class="claude-note warn">${e.notes.map(n => `<div class="small">${ic("alert")} ${esc(n)}</div>`).join("")}</div>` : `<div class="claude-note"><span class="yes">${ic("check")} ${T("Everything is in order", "Tout est en ordre")}</span></div>`}`;
}
function openEnv() { modal(T("System diagnostics", "Diagnostic du système"), envHtml()); }

boot();
