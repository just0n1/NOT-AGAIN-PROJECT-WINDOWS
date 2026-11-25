import os
import sys
import time
import json
import subprocess
import collections
import ctypes
import ctypes.wintypes as w
from datetime import datetime
from PIL import Image
import mss
import win32gui
import psutil

from detector import NSFWDetector

user32 = ctypes.windll.user32

# ============================================================
# NOT AGAIN v1.0 — Guardian de Pureza
# ============================================================

TARGET_PROCESSES = {
    "chrome.exe", "msedge.exe", "firefox.exe",
    "brave.exe", "opera.exe", "opera_gx.exe", "vivaldi.exe",
    "blender.exe"
}

# --- THRESHOLDS ---
NSFW_INSTANT_THRESHOLD   = 0.90   # 1 frame -> kill inmediato
NSFW_SOFT_THRESHOLD      = 0.40   # frame cuenta como "hit suave"
REQUIRED_HITS_IN_WINDOW  = 4      # subido a 4 hits (evita falsos positivos en scroll y miniaturas)
WINDOW_SIZE              = 8      # memoria de ~3-4 segundos a 2-4 FPS

# Si un artista de riesgo tiene título que parece videoclip -> bloqueo directo
# Sólo se activa cuando el título parece "Artista - Cancion - YouTube" (video en reproducción)
# NO se activa en búsquedas, historiales o páginas de resultados
ARTIST_DIRECT_BLOCK      = True

LOG_FILE      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guardian.log")
TRIGGERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "triggers.json")
CAPTURES_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capturas_bloqueo")

def save_block_capture(full_img, crop_img, reason, score):
    """Guarda capturas de pantalla de los bloqueos para auditar falsos positivos."""
    try:
        os.makedirs(CAPTURES_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"{ts}_{reason}_{int(score*100)}pct"
        full_path = os.path.join(CAPTURES_DIR, f"{prefix}_full.jpg")
        crop_path = os.path.join(CAPTURES_DIR, f"{prefix}_crop.jpg")
        full_img.save(full_path, "JPEG", quality=85)
        crop_img.save(crop_path, "JPEG", quality=85)
        log_event(f"CAPTURA GUARDADA: capturas_bloqueo/{prefix}_*.jpg")
    except Exception as e:
        log_event(f"Error guardando captura: {e}")


# ============================================================
# CAPA 1 ANTI-TAMPER: BLOQUEO EXCLUSIVO DE ARCHIVOS EN MEMORIA
# ============================================================
CRITICAL_HANDLES = []

def lock_critical_files():
    """
    Mantiene abiertos descriptores con dwShareMode = FILE_SHARE_READ (sin FILE_SHARE_DELETE).
    Windows impide fisicamente que el usuario o el explorador borre, renombre o comprima
    los archivos clave o la carpeta del proyecto mientras el guardian este en marcha.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    files_to_lock = [
        os.path.abspath(__file__),
        os.path.join(base_dir, "detector.py"),
        os.path.join(base_dir, "lockscreen.py"),
        os.path.join(base_dir, "verses.json"),
        os.path.join(base_dir, "triggers.json"),
        os.path.join(base_dir, "models", "nsfw_detector_fp32.onnx"),
        os.path.join(base_dir, "models", "nsfw_detector.onnx"),
    ]
    k32 = ctypes.windll.kernel32
    k32.CreateFileW.restype = w.HANDLE
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = 0x00000001
    OPEN_EXISTING = 3

    for path in files_to_lock:
        if os.path.exists(path):
            h = k32.CreateFileW(path, GENERIC_READ, FILE_SHARE_READ, None, OPEN_EXISTING, 0, None)
            if h and h != w.HANDLE(-1).value and h != 0xFFFFFFFFFFFFFFFF:
                CRITICAL_HANDLES.append(h)
    log_event(f"ANTI-TAMPER CAPA 1: {len(CRITICAL_HANDLES)} archivos bloqueados contra borrado/modificacion.")

# ============================================================

def load_triggers():
    defaults = {
        "high_risk_artists": [
            "bad gyal", "anitta", "megan thee stallion", "cardi b",
            "nicki minaj", "ice spice", "tokischa", "doja cat",
            "becky g", "karol g", "rosalia", "j balvin", "maluma",
            "daddy yankee", "don omar", "pitbull", "feid",
            "myke towers", "jhay cortez", "bad bunny", "ozuna", "arcangel", "natti natasha", "rauw alejandro"
            
        ],
        "safe_keywords": [
            "lyric", "lyrics", "letra", "letras",
            "audio", "visualizer", "instrumental", "karaoke"
        ],
        "danger_keywords": [
            "video oficial", "official video", "official music video",
            "videoclip", "video clip", "video musical",
            "twerk", "twerking", "perreo", "hot video", "fap"
        ]
    }
    if os.path.exists(TRIGGERS_FILE):
        try:
            with open(TRIGGERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return defaults

DRY_RUN_MODE = False
_last_log_prune = 0

def prune_old_logs(max_days: int = 30):
    """
    Mantiene el archivo guardian.log limpio y optimizado:
    - Conserva solo eventos relevantes (FIRE, SEMANTIC, LOCKSCREEN, VETO, etc.).
    - Purga automaticamente lineas rutinarias de escaneo y registros con mas de 30 dias.
    """
    if not os.path.exists(LOG_FILE):
        return
    try:
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=max_days)
        kept = []
        with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if "SCAN |" in line:
                    continue
                m = re.search(r"\[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})\]", line)
                if m:
                    dt = datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H:%M:%S")
                    if dt < cutoff:
                        continue
                kept.append(line)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.writelines(kept)
    except Exception:
        pass

def log_event(msg: str):
    global _last_log_prune
    ts    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] {msg}\n"
    if DRY_RUN_MODE:
        try:
            print(entry, end="")
        except Exception:
            pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass
    
    # Auto-mantenimiento cada 6 horas: eliminar lineas de mas de 30 dias
    now = time.time()
    if now - _last_log_prune > 21600:
        _last_log_prune = now
        prune_old_logs(max_days=30)

def get_foreground_info():
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None
        pid = w.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return None
        try:
            proc_name = psutil.Process(pid.value).name().lower()
        except Exception:
            return None
        title = win32gui.GetWindowText(hwnd)
        rect  = win32gui.GetWindowRect(hwnd)
        return pid.value, proc_name, title, rect
    except Exception:
        return None

def kill_browser(pid: int, name: str):
    if DRY_RUN_MODE:
        log_event(f"[DRY-RUN] SIMULACION: Cerraria {name} PID={pid}")
        return
    log_event(f"KILL: {name} PID={pid}")
    try:
        subprocess.run(
            ["taskkill", "/F", "/PID", str(pid), "/T"],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    except Exception as e:
        log_event(f"kill error: {e}")

def show_lockscreen(duration: int = 60):
    if DRY_RUN_MODE:
        log_event(f"[DRY-RUN] SIMULACION: Mostraria pantalla de bloqueo por {duration}s")
        return
    log_event(f"LOCKSCREEN {duration}s")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Si corre como exe compilado (PyInstaller), buscar NotAgainLockscreen.exe al lado
    if getattr(sys, 'frozen', False):
        lockscreen_exe = os.path.join(base_dir, "NotAgainLockscreen.exe")
        cmd = [lockscreen_exe, str(duration)]
    else:
        # Modo script Python normal
        lockscreen_py = os.path.join(base_dir, "lockscreen.py")
        cmd = [sys.executable, lockscreen_py, str(duration)]
    
    subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
    log_event("LOCKSCREEN END")

def _looks_like_video_title(title: str, artist: str) -> bool:
    """
    Distingue título de video en reproducción vs página de búsqueda/resultados.

    Video real en YouTube:      "Megan Thee Stallion - WAP - YouTube"
    Búsqueda en YouTube:        "YouTube - (6) megan thee stallion - YouTube"
    Resultados de búsqueda:     "megan thee stallion - YouTube"  (sin canción en medio)
    """
    t = title.lower().strip()

    # Patrón de búsqueda: empieza con "youtube - " (e.g. "YouTube - (6) query - YouTube")
    if t.startswith("youtube - "):
        return False

    # Sin "- youtube" al final -> no es una pestaña de YouTube
    if " - youtube" not in t:
        return False

    # Quitar el sufijo "- youtube" y ver si hay contenido aparte del artista
    base = t.replace(" - youtube", "").strip()
    base = base.replace(artist.lower(), "").strip(" -")

    # Si tras quitar artista y sufijo queda algo (>= 2 chars) -> hay nombre de canción -> es video
    return len(base) >= 2


import re
import unicodedata

PORN_SITES = [
    "pornhub", "xvideos", "xnxx", "xhamster", "redtube", "youporn",
    "spankbang", "eporner", "tube8", "chaturbate", "stripchat",
    "onlyfans", "brazzers", "rule34", "nhentai"
]
PORN_WORDS = ["porn", "porno", "xxx", "hentai", "nsfw"]

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

def _has_word(text: str, word: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(word)}(?![a-z0-9])", text) is not None

USER_LIST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_blocklist.txt")
_user_cache = {"mtime": 0, "items": []}

def load_user_blocklist():
    try:
        mtime = os.path.getmtime(USER_LIST_FILE)
    except OSError:
        return []
    if mtime != _user_cache["mtime"]:
        try:
            with open(USER_LIST_FILE, "r", encoding="utf-8") as f:
                items = [_norm(l.strip()) for l in f
                         if l.strip() and not l.lstrip().startswith("#")]
            _user_cache["items"] = items
            _user_cache["mtime"] = mtime
        except Exception:
            pass
    return _user_cache["items"]

VIDEO_LABELS = {
    "official video", "official music video", "music video", "video oficial",
    "videoclip", "video clip", "video musical", "clip oficial", "mv"
}

# Palabras seguras en títulos de producción / tutoriales
# Inmunizan contra disparos por acumulación de ventana suave (fondos de dormitorio, camas, ropa deportiva en vlogs)
CREATIVE_SAFE_KEYWORDS = [
    "tutorial", "beat", "beats", "beat remake", "remake", "fl studio",
    "ableton", "logic pro", "cubase", "pro tools", "como se hizo",
    "cómo se hizo", "how to", "breakdown", "music production",
    "produccion musical", "producción musical", "vst", "plugin", "mixing"
]

def _is_creative_safe_title(title: str) -> bool:
    t = _norm(title)
    return any(kw in t for kw in CREATIVE_SAFE_KEYWORDS)

def _is_feed_or_home_navigation(title: str) -> bool:
    """
    Detecta si el usuario esta en la home o navegando feeds de miniaturas
    donde NO hay un video en reproduccion activa (e.g. 'YouTube', 'Inicio - YouTube', buscador).
    """
    t = title.strip().lower()
    # Si el titulo es simplemente 'youtube' o 'youtube - brave' o similar
    if t in ("youtube", "inicio - youtube", "home - youtube", "feed - youtube"):
        return True
    if t.startswith("youtube - ") and not (" - youtube" in t and len(t) > 25):
        return True
    # Si no tiene el clasico 'Titulo del video - YouTube'
    if not t.endswith("- youtube") and "youtube" in t:
        return True
    return False

def evaluate_title(title: str, triggers: dict):
    """Returns: (block_immediately, is_safe_audio, artist_tracking)"""
    t = _norm(title)

    # Excepción para plataformas de desarrollo / código (GitHub, GitLab, StackOverflow):
    # Permite gestionar repositorios con nombres técnicos como 'anti-porn', 'nsfw-filter', etc. sin autocerrarse.
    if any(dev in t for dev in ["github", "gitlab", "stackoverflow"]):
        return False, False, False

    # 0. Sitios/palabras porno -> corte inmediato
    if any(s in t for s in PORN_SITES) or any(_has_word(t, w) for w in PORN_WORDS):
        return True, False, False

    # 0b. Lista local del usuario
    if any(item in t for item in load_user_blocklist()):
        return True, False, False

    # 1. Palabras explícitas (twerk, perreo...) -> siempre bloquean.
    #    Las etiquetas de vídeo NO bloquean por sí solas.
    for kw in triggers.get("danger_keywords", []):
        kw_n = _norm(kw)
        if kw_n in VIDEO_LABELS:
            continue
        if _has_word(t, kw_n):
            return True, False, False

    # 2. Artistas de riesgo
    for artist in triggers.get("high_risk_artists", []):
        artist_n = _norm(artist)
        if not _has_word(t, artist_n):
            continue
        for safe in triggers.get("safe_keywords", []):
            if _has_word(t, _norm(safe)):
                return False, True, False
        # Artista de riesgo + etiqueta de vídeo -> bloquear
        for kw in triggers.get("danger_keywords", []):
            if _has_word(t, _norm(kw)):
                return True, False, False
        if ARTIST_DIRECT_BLOCK:
            if _looks_like_video_title(t, artist_n):
                return True, False, False
            return False, False, True
        return False, False, True

    return False, False, False

def log_shadow(detector, full, score, title):
    """MODO SOMBRA: puntua la ventana completa y solo lo registra (no decide nada)."""
    try:
        s_full = detector.predict(full)["nsfw"]
        log_event(f"SHADOW | crop={score*100:.1f}% | full={s_full*100:.1f}% | '{title[:40]}'")
    except Exception as e:
        log_event(f"SHADOW error: {e}")


def run_guardian(dry_run: bool = False):
    global DRY_RUN_MODE
    DRY_RUN_MODE = dry_run

    log_event("=" * 60)
    mode_tag = " [MODO PRUEBA DRY-RUN - SIN CIERRES]" if dry_run else ""
    log_event(f"NOT AGAIN v1.0 — GUARDIAN ACTIVO (GPU DirectML){mode_tag} + MODO SOMBRA")
    log_event(f"ARTIST_DIRECT_BLOCK = {ARTIST_DIRECT_BLOCK}")
    log_event("=" * 60)

    triggers = load_triggers()
    detector = NSFWDetector()
    sct      = mss.mss()

    if not dry_run:
        lock_critical_files()

    log_event(f"Inferencia en: {detector.active_provider}")

    hits = collections.deque(maxlen=WINDOW_SIZE)

    while True:
        try:
            time.sleep(0.05 if sum(hits) else 0.12)

            info = get_foreground_info()
            if not info:
                hits.clear()
                continue

            pid, proc_name, title, (left, top, right, bottom) = info

            if proc_name not in TARGET_PROCESSES:
                hits.clear()
                continue

            # --- LAYER 1: SEMANTIC ---
            block_now, is_safe, tracking = evaluate_title(title, triggers)

            if is_safe:
                hits.clear()
                continue

            if block_now:
                log_event(f"SEMANTIC BLOCK | {proc_name} | '{title[:60]}'")
                kill_browser(pid, proc_name)
                hits.clear()
                show_lockscreen(60)
                continue

            # --- LAYER 2: VISUAL AI ---
            width  = right - left
            height = bottom - top
            if width < 300 or height < 300:
                continue

            bbox = {"left": max(0, left), "top": max(0, top), "width": width, "height": height}
            try:
                sct_img = sct.grab(bbox)
                full    = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            except Exception:
                continue

            # Centre crop (video player area)
            wp, hp   = full.size
            crop     = full.crop((int(wp*0.10), int(hp*0.05), int(wp*0.90), int(hp*0.90)))
            res      = detector.predict(crop)
            score    = res["nsfw"]

            is_hit = score >= NSFW_SOFT_THRESHOLD
            hits.append(1 if is_hit else 0)
            n_hits = sum(hits)

            is_instant = score >= NSFW_INSTANT_THRESHOLD

            if DRY_RUN_MODE:
                log_event(
                    f"SCAN | {proc_name} | NSFW={score*100:.1f}% | "
                    f"hits={n_hits}/{REQUIRED_HITS_IN_WINDOW} | "
                    f"lat={res['latency_ms']:.0f}ms | '{title[:40]}'"
                )

            if is_instant or n_hits >= REQUIRED_HITS_IN_WINDOW:
                reason = "INSTANT-EXPLICIT" if is_instant else "SOFT-PORN-WINDOW"

                # INMUNIDAD FEED / HOME: En el feed principal de miniaturas, las alarmas suaves no cierran el navegador
                if not is_instant and _is_feed_or_home_navigation(title):
                    log_event(f"INMUNIDAD FEED/HOME | SOFT VETO EVITADO | crop={score*100:.1f}% | '{title[:45]}'")
                    hits.clear()
                    continue

                # INMUNIDAD CREATIVA: Si es solo hit suave pero es un tutorial/beat remake/producción musical
                if not is_instant and _is_creative_safe_title(title):
                    log_event(f"INMUNIDAD CREATIVA | SOFT VETO | '{title[:45]}'")
                    hits.clear()
                    continue
                
                # VETO SOMBRA: Si es alarma suave pero la ventana completa da < 40% (o < 5% normal), es falso positivo por crop
                s_full = detector.predict(full)["nsfw"]
                if not is_instant and s_full < 0.40 and score < 0.85:
                    log_event(f"VETO SOMBRA | FALSO POSITIVO EVITADO | crop={score*100:.1f}% pero full={s_full*100:.1f}% | '{title[:40]}'")
                    save_block_capture(full, crop, "FALSO_POSITIVO_EVITADO", score)
                    hits.clear()
                    continue

                log_event(f"FIRE {reason} | {proc_name} | crop={score*100:.1f}% full={s_full*100:.1f}% | '{title[:50]}'")
                save_block_capture(full, crop, reason, score)
                kill_browser(pid, proc_name)
                hits.clear()
                show_lockscreen(60)
            elif is_hit:
                log_shadow(detector, full, score, title)   # sombra: frames sospechosos

        except Exception as e:
            log_event(f"LOOP ERROR: {e}")
            time.sleep(1)


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    if not is_dry:
        _mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\NotAgainGuardian")
        if ctypes.windll.kernel32.GetLastError() == 183:
            sys.exit(0)
    run_guardian(dry_run=is_dry)