#!/usr/bin/env python3
"""
NOT AGAIN — Panel de Control v1.0
Interfaz de escritorio para gestionar el guardián de pureza.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os, re, json, random, subprocess, sys, collections
from datetime import datetime

try:
    import psutil; HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from PIL import Image, ImageTk; HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ─── Rutas ───────────────────────────────────────────────────────────────────
BASE           = os.path.dirname(os.path.abspath(__file__))
LOG_FILE       = os.path.join(BASE, "guardian.log")
VERSES_FILE    = os.path.join(BASE, "verses.json")
USER_BLOCKLIST = os.path.join(BASE, "user_blocklist.txt")
CAPTURES_DIR   = os.path.join(BASE, "capturas_bloqueo")
ASSETS_DIR     = os.path.join(BASE, "assets")

# ─── Paleta (fiel al mockup) ─────────────────────────────────────────────────
BG      = "#0d0f1a"   # Fondo negro azulado
SIDEBAR = "#080a13"   # Sidebar más oscuro
CARD    = "#182040"   # Tarjeta media
CARD2   = "#1c2850"   # Tarjeta ligeramente más clara
STATUSB = "#152860"   # Barra de estado
ACTIVE  = "#1f2f52"   # Nav activo
WHITE   = "#ffffff"
GRAY    = "#7a8db0"
GREEN   = "#22c55e"
RED     = "#ef4444"
ORANGE  = "#f97316"
ACCENT  = "#5b6cff"
TEXT    = "#c0ccee"

# ─── Tipografía ───────────────────────────────────────────────────────────────
F_TITLE  = ("Impact", 26)
F_LABEL  = ("Arial", 10, "bold")
F_NAV    = ("Arial", 7, "bold")
F_VERSE  = ("Georgia", 11, "italic")
F_SMALL  = ("Arial", 9)
F_BODY   = ("Arial", 10)
F_MONO   = ("Courier New", 9)
F_HEADER = ("Arial", 12, "bold")


# ─── Helpers de datos ─────────────────────────────────────────────────────────
def is_guardian_running():
    if not HAS_PSUTIL:
        return False
    for p in psutil.process_iter(["name"]):
        try:
            name = (p.info["name"] or "").lower()
            if "notagainguardian" in name or "pythonw" in name:
                return True
        except Exception:
            pass
    return False


def load_verse():
    try:
        with open(VERSES_FILE, "r", encoding="utf-8") as f:
            verses = json.load(f)
        v = random.choice(verses)
        if isinstance(v, dict):
            return v.get("text", ""), v.get("reference", "")
        return str(v), ""
    except Exception:
        return (
            "Sobre toda cosa guardada, guarda tu corazón;\nporque de él mana la vida.",
            "Proverbios 4:23"
        )


def calculate_streak():
    """
    Calcula la racha de pureza:
    - Se resetea si hay FIRE INSTANT-EXPLICIT (>=90%) o SEMANTIC BLOCK.
    - Tolera hasta 5 alertas suaves al dia (falsos positivos). Si hay >=6 en un dia, resetea.
    Retorna (dias, horas, soft_hoy, estado_racha)
    """
    if not os.path.exists(LOG_FILE):
        return 0, 0, 0, "Iniciando"
    
    last_reset = None
    soft_hits_by_day = collections.defaultdict(int)
    today_str = datetime.now().strftime("%Y-%m-%d")

    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.search(r"\[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})\]", line)
                if not m:
                    continue
                d_str, t_str = m.group(1), m.group(2)
                dt = datetime.strptime(f"{d_str} {t_str}", "%Y-%m-%d %H:%M:%S")

                if "FIRE INSTANT-EXPLICIT" in line or "SEMANTIC BLOCK" in line:
                    last_reset = dt
                elif "FIRE SOFT-PORN-WINDOW" in line:
                    soft_hits_by_day[d_str] += 1
                    if soft_hits_by_day[d_str] >= 6:
                        last_reset = dt
    except Exception:
        pass

    now = datetime.now()
    if last_reset is None:
        last_reset = datetime(2026, 11, 2, 0, 0, 0)
    
    diff = max(now - last_reset, datetime.min - datetime.min)
    days = diff.days
    hours = int(diff.seconds // 3600)
    soft_today = soft_hits_by_day.get(today_str, 0)

    if days == 0:
        badge = "🌱 Día 1 — Mantente firme"
    elif days < 3:
        badge = "🔥 Escudo Forjándose"
    elif days < 7:
        badge = "⚔️ 1ª Semana de Victoria"
    elif days < 14:
        badge = "🛡️ Fortaleza en Marcha"
    elif days < 30:
        badge = "👑 Dominio Propio"
    else:
        badge = "💎 Mente Renovada (30+ días)"

    return days, hours, soft_today, badge


def load_recent_blocks(n=100):
    blocks = []
    if not os.path.exists(LOG_FILE):
        return blocks
    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        for line in reversed(lines):
            line = line.strip()
            # FIRE
            m = re.search(
                r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] "
                r"FIRE (\S+) \| (\S+) \| [\w.=]+? \| '(.*)'", line)
            if m:
                score_m = re.search(r"crop=([\d.]+)%", line) or re.search(r"\| ([\d.]+)% \|", line)
                score = (score_m.group(1) + "%") if score_m else "?"
                blocks.append({
                    "ts": m.group(1), "tipo": m.group(2),
                    "proc": m.group(3), "score": score,
                    "titulo": m.group(4)[:60], "color": RED
                })
                if len(blocks) >= n: break
                continue
            # SEMANTIC
            m2 = re.search(
                r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] "
                r"SEMANTIC BLOCK \| (\S+) \| '(.*)'", line)
            if m2:
                blocks.append({
                    "ts": m2.group(1), "tipo": "SEMÁNTICO",
                    "proc": m2.group(2), "score": "-",
                    "titulo": m2.group(3)[:60], "color": ORANGE
                })
                if len(blocks) >= n: break
                continue
            # VETO
            m3 = re.search(
                r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] "
                r"VETO SOMBRA \|.*\| '(.*)'", line)
            if m3:
                blocks.append({
                    "ts": m3.group(1), "tipo": "EVITADO",
                    "proc": "-", "score": "-",
                    "titulo": m3.group(2)[:60], "color": GREEN
                })
                if len(blocks) >= n: break
    except Exception:
        pass
    return blocks


def load_blocklist():
    items = []
    if os.path.exists(USER_BLOCKLIST):
        try:
            with open(USER_BLOCKLIST, "r", encoding="utf-8") as f:
                for line in f:
                    l = line.strip()
                    if l and not l.startswith("#"):
                        items.append(l)
        except Exception:
            pass
    return items


def save_blocklist(items):
    with open(USER_BLOCKLIST, "w", encoding="utf-8") as f:
        f.write("# Una palabra o nombre de sitio por línea\n")
        for item in items:
            if item.strip():
                f.write(item.strip() + "\n")


# ─── Aplicación principal ─────────────────────────────────────────────────────
class NotAgainApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Not Again — Panel de Control")
        self.root.geometry("1020x580")
        self.root.minsize(860, 500)
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self._apply_dark_titlebar()

        self.current_page = "home"
        self.logo_img = None
        self._load_assets()

        self._build_sidebar()
        self._build_main_area()
        self._switch("home")
        self._schedule_refresh()

    # ── Sistema ───────────────────────────────────────────────────────────────
    def _apply_dark_titlebar(self):
        try:
            from ctypes import windll, byref, sizeof, c_int
            windll.dwmapi.DwmSetWindowAttribute(
                windll.user32.GetParent(self.root.winfo_id()),
                20, byref(c_int(1)), sizeof(c_int))
        except Exception:
            pass

    def _load_assets(self):
        logo_path = os.path.join(ASSETS_DIR, "logo_shield.png")
        if HAS_PIL and os.path.exists(logo_path):
            try:
                img = Image.open(logo_path).resize((56, 56), Image.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
            except Exception:
                self.logo_img = None

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = tk.Frame(self.root, bg=SIDEBAR, width=82)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.nav_widgets = {}
        nav = [
            ("🏠", "HOME",        "home"),
            ("🚫", "BLOCK\nLIST", "blocklist"),
            ("🕐", "HISTORY",     "history"),
            ("⚙",  "CONFIG",      "config"),
        ]
        for icon, label, page in nav:
            frame = tk.Frame(self.sidebar, bg=SIDEBAR, cursor="hand2")
            frame.pack(fill="x", padx=5, pady=3)

            icon_lbl = tk.Label(frame, text=icon,
                                font=("Segoe UI Emoji", 20),
                                bg=SIDEBAR, fg=WHITE, pady=5)
            icon_lbl.pack()

            text_lbl = tk.Label(frame, text=label,
                                font=F_NAV, bg=SIDEBAR,
                                fg=GRAY, justify="center")
            text_lbl.pack(pady=(0, 7))

            for w in (frame, icon_lbl, text_lbl):
                w.bind("<Button-1>", lambda e, p=page: self._switch(p))

            self.nav_widgets[page] = (frame, icon_lbl, text_lbl)

    def _update_nav(self, active):
        for page, (frm, icon, txt) in self.nav_widgets.items():
            if page == active:
                frm.configure(bg=ACTIVE)
                icon.configure(bg=ACTIVE, fg=WHITE)
                txt.configure(bg=ACTIVE, fg=WHITE)
            else:
                frm.configure(bg=SIDEBAR)
                icon.configure(bg=SIDEBAR, fg=WHITE)
                txt.configure(bg=SIDEBAR, fg=GRAY)

    # ── Área principal ────────────────────────────────────────────────────────
    def _build_main_area(self):
        self.main = tk.Frame(self.root, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)

        # Cabecera fija
        self.hdr = tk.Frame(self.main, bg=BG)
        self.hdr.pack(fill="x", padx=14, pady=(10, 6))

        self.title_lbl = tk.Label(self.hdr, text="HOME 🏠",
                                  font=F_TITLE, bg=BG, fg=WHITE, anchor="w")
        self.title_lbl.pack(side="left")

        # Logo top-right
        logo_bg = tk.Frame(self.hdr, bg="#080b15")
        logo_bg.pack(side="right")
        if self.logo_img:
            tk.Label(logo_bg, image=self.logo_img,
                     bg="#080b15").pack(padx=8, pady=6)
        else:
            tk.Label(logo_bg, text="🛡", font=("Segoe UI Emoji", 30),
                     bg="#080b15", fg=ACCENT).pack(padx=14, pady=8)

        # Contenido dinámico
        self.content = tk.Frame(self.main, bg=BG)
        self.content.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _switch(self, page):
        self.current_page = page
        self._update_nav(page)
        getattr(self, f"_page_{page}")()

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE: HOME
    # ─────────────────────────────────────────────────────────────────────────
    def _page_home(self):
        self._clear()
        self.title_lbl.config(text="HOME 🏠")
        running = is_guardian_running()

        # ── Barra de estado y Racha ──────────────────────────────────────
        status_bar = tk.Frame(self.content, bg=STATUSB)
        status_bar.pack(fill="x", pady=(0, 6))

        dot_color = GREEN if running else RED
        status_text = "Activo  —  GPU DirectML · RTX 2070 · ~34ms" if running else "Inactivo  —  Reinicia restart_guardian.bat"
        tk.Label(status_bar,
                 text=f"  Estado del guardian:  ●  {status_text}  ",
                 font=("Arial", 11, "bold"),
                 bg=STATUSB, fg=dot_color,
                 pady=8, anchor="w").pack(fill="x", padx=10)

        # ── Tarjeta de Recompensa / Racha de Pureza ──────────────────────
        days, hours, soft_today, badge = calculate_streak()
        streak_bar = tk.Frame(self.content, bg=CARD2)
        streak_bar.pack(fill="x", pady=(0, 8))

        st_left = tk.Frame(streak_bar, bg=CARD2)
        st_left.pack(side="left", padx=14, pady=8)

        tk.Label(st_left, text="🛡️ RACHA EN VICTORIA:",
                 font=("Impact", 13), bg=CARD2, fg=WHITE).pack(side="left")
        tk.Label(st_left, text=f"  {days} días  {hours}h  ",
                 font=("Arial", 14, "bold"), bg=CARD2, fg="#38bdf8").pack(side="left")
        tk.Label(st_left, text=f"|  {badge}",
                 font=("Arial", 10, "bold"), bg=CARD2, fg=GREEN).pack(side="left", padx=(6, 0))

        st_right = tk.Frame(streak_bar, bg=CARD2)
        st_right.pack(side="right", padx=14, pady=8)
        soft_color = GRAY if soft_today < 3 else (ORANGE if soft_today < 6 else RED)
        tk.Label(st_right, text=f"Alertas suaves hoy: {soft_today}/5 toleradas",
                 font=F_SMALL, bg=CARD2, fg=soft_color).pack(side="right")

        # ── Cuerpo de 2 columnas ─────────────────────────────────────────
        body = tk.Frame(self.content, bg=BG)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ── Columna izquierda: Versículo ─────────────────────────────────
        verse_card = tk.Frame(body, bg=CARD)
        verse_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        tk.Label(verse_card, text="✝   Palabra del Día",
                 font=F_LABEL, bg=CARD, fg=GRAY,
                 anchor="w").pack(fill="x", padx=16, pady=(14, 6))

        sep = tk.Frame(verse_card, bg=ACCENT, height=2)
        sep.pack(fill="x", padx=16, pady=(0, 10))

        verse_text, verse_ref = load_verse()
        tk.Label(verse_card, text=f'"{verse_text}"',
                 font=F_VERSE, bg=CARD, fg=WHITE,
                 wraplength=360, justify="center").pack(
            fill="both", expand=True, padx=20, pady=6)

        tk.Label(verse_card, text=f"— {verse_ref}",
                 font=("Georgia", 10, "bold italic"),
                 bg=CARD, fg=ACCENT, justify="center").pack(pady=(2, 8))

        tk.Button(verse_card, text="↻  Nuevo versículo",
                  font=F_SMALL, bg=CARD2, fg=GRAY,
                  relief="flat", cursor="hand2", bd=0, pady=7,
                  command=lambda: self._page_home()).pack(
            fill="x", padx=16, pady=(0, 14))

        # ── Columna derecha: Últimos bloqueos ────────────────────────────
        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.rowconfigure(1, weight=1)

        # Cabecera del panel derecho
        blk_header = tk.Frame(right, bg=CARD2)
        blk_header.pack(fill="x", pady=(0, 6))
        tk.Label(blk_header, text="🛡  Últimos Bloqueos:",
                 font=F_HEADER, bg=CARD2, fg=WHITE,
                 anchor="w", pady=10).pack(fill="x", padx=14)

        # Lista de bloqueos
        blk_list = tk.Frame(right, bg=CARD)
        blk_list.pack(fill="both", expand=True)

        blocks = load_recent_blocks(7)
        if not blocks:
            tk.Label(blk_list, text="Sin bloqueos registrados aún.",
                     font=F_SMALL, bg=CARD, fg=GRAY).pack(expand=True)
        else:
            for b in blocks:
                row = tk.Frame(blk_list, bg=CARD)
                row.pack(fill="x", padx=10, pady=(5, 0))

                tk.Label(row, text="●", font=("Arial", 11),
                         bg=CARD, fg=b["color"]).pack(side="left", padx=(0, 6))

                ts = b["ts"][11:16]
                date = b["ts"][5:10]
                info = f"[{date}  {ts}]  {b['tipo']:18s}  {b['score']}"
                tk.Label(row, text=info, font=F_MONO,
                         bg=CARD, fg=TEXT, anchor="w").pack(side="left")

                tk.Label(blk_list,
                         text=f"   └ {b['titulo']}",
                         font=("Arial", 8), bg=CARD, fg=GRAY,
                         anchor="w").pack(fill="x", padx=10, pady=(0, 2))

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE: BLOCKLIST
    # ─────────────────────────────────────────────────────────────────────────
    def _page_blocklist(self):
        self._clear()
        self.title_lbl.config(text="🚫 BLOCK LIST")

        tk.Label(self.content,
                 text="Palabras, sitios y canales bloqueados manualmente",
                 font=F_LABEL, bg=BG, fg=GRAY, anchor="w").pack(
            fill="x", pady=(0, 8))

        # Barra de entrada
        add_bar = tk.Frame(self.content, bg=CARD2)
        add_bar.pack(fill="x", pady=(0, 10))

        self._new_word = tk.StringVar()
        entry = tk.Entry(add_bar, textvariable=self._new_word,
                         font=F_BODY, bg=CARD, fg=WHITE,
                         insertbackground=WHITE, relief="flat", bd=0,
                         width=28)
        entry.pack(side="left", padx=(12, 0), pady=10, ipady=7)
        entry.bind("<Return>", lambda e: self._bl_add())

        tk.Label(add_bar, text="  Escribe la palabra o sitio a bloquear",
                 font=F_SMALL, bg=CARD2, fg=GRAY).pack(side="left")

        tk.Button(add_bar, text="  ➕ Añadir  ",
                  font=F_LABEL, bg=ACCENT, fg=WHITE,
                  relief="flat", cursor="hand2", bd=0,
                  command=self._bl_add, pady=9, padx=12).pack(
            side="right", padx=12, pady=8)

        # Lista actual
        list_card = tk.Frame(self.content, bg=CARD)
        list_card.pack(fill="both", expand=True)

        tk.Label(list_card, text="Lista activa:",
                 font=F_LABEL, bg=CARD, fg=GRAY,
                 anchor="w").pack(fill="x", padx=14, pady=(10, 4))

        self._bl_frame = tk.Frame(list_card, bg=CARD)
        self._bl_frame.pack(fill="both", expand=True, padx=14)
        self._bl_refresh()

    def _bl_refresh(self):
        for w in self._bl_frame.winfo_children():
            w.destroy()
        items = load_blocklist()
        if not items:
            tk.Label(self._bl_frame,
                     text="La lista está vacía. Añade palabras arriba.",
                     font=F_SMALL, bg=CARD, fg=GRAY).pack(pady=20)
            return
        for item in items:
            row = tk.Frame(self._bl_frame, bg=CARD2)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"  🚫  {item}",
                     font=F_BODY, bg=CARD2, fg=WHITE,
                     anchor="w").pack(side="left", pady=8, padx=6)
            tk.Button(row, text=" ✕ ", font=F_SMALL,
                      bg=CARD2, fg=RED, relief="flat",
                      cursor="hand2", bd=0,
                      command=lambda i=item: self._bl_remove(i)).pack(
                side="right", padx=10)

    def _bl_add(self):
        word = self._new_word.get().strip().lower()
        if not word:
            return
        items = load_blocklist()
        if word not in items:
            items.append(word)
            save_blocklist(items)
        self._new_word.set("")
        self._bl_refresh()

    def _bl_remove(self, item):
        items = load_blocklist()
        if item in items:
            items.remove(item)
            save_blocklist(items)
        self._bl_refresh()

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE: HISTORY
    # ─────────────────────────────────────────────────────────────────────────
    def _page_history(self):
        self._clear()
        self.title_lbl.config(text="🕐 HISTORIAL")

        tk.Label(self.content,
                 text="Registro completo de activaciones del guardián",
                 font=F_LABEL, bg=BG, fg=GRAY, anchor="w").pack(
            fill="x", pady=(0, 8))

        # Tabla con scroll
        wrapper = tk.Frame(self.content, bg=CARD)
        wrapper.pack(fill="both", expand=True)

        canvas = tk.Canvas(wrapper, bg=CARD, bd=0, highlightthickness=0)
        sb = ttk.Scrollbar(wrapper, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=CARD)
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Scroll con rueda del ratón
        canvas.bind_all("<MouseWheel>",
                         lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        # Cabecera de tabla
        hdr = tk.Frame(inner, bg="#0e1830")
        hdr.pack(fill="x")
        for col, width in [("Fecha", 10), ("Hora", 8), ("Tipo", 15),
                            ("Score", 7), ("Proceso", 10), ("Título visto", 50)]:
            tk.Label(hdr, text=col, font=("Arial", 9, "bold"),
                     bg="#0e1830", fg=GRAY, anchor="w", width=width).pack(
                side="left", padx=6, pady=8)

        blocks = load_recent_blocks(200)
        if not blocks:
            tk.Label(inner, text="Sin bloqueos registrados aún.",
                     font=F_BODY, bg=CARD, fg=GRAY).pack(pady=30)
        else:
            for i, b in enumerate(blocks):
                row_bg = CARD if i % 2 == 0 else "#182240"
                row = tk.Frame(inner, bg=row_bg)
                row.pack(fill="x", pady=1)
                date, time = b["ts"][:10], b["ts"][11:19]
                data = [(date, 10), (time, 8), (b["tipo"], 15),
                        (b["score"], 7), (b["proc"], 10), (b["titulo"], 50)]
                for j, (val, w) in enumerate(data):
                    fg = b["color"] if j == 2 else TEXT
                    tk.Label(row, text=val, font=F_MONO,
                             bg=row_bg, fg=fg, anchor="w", width=w).pack(
                        side="left", padx=6, pady=5)

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE: CONFIG
    # ─────────────────────────────────────────────────────────────────────────
    def _page_config(self):
        self._clear()
        self.title_lbl.config(text="⚙  CONFIG")

        # Card: control del proceso
        ctrl = tk.Frame(self.content, bg=CARD)
        ctrl.pack(fill="x", pady=(0, 10))

        tk.Label(ctrl, text="⚡  Control del Guardián",
                 font=F_LABEL, bg=CARD, fg=GRAY, anchor="w").pack(
            fill="x", padx=14, pady=(12, 4))

        sep = tk.Frame(ctrl, bg=ACCENT, height=2)
        sep.pack(fill="x", padx=14, pady=(0, 8))

        running = is_guardian_running()
        tk.Label(ctrl,
                 text=f"Estado: {'🟢 ACTIVO — Protegiendo en este momento' if running else '🔴 INACTIVO — Reinicia el guardián'}",
                 font=("Arial", 11, "bold"), bg=CARD,
                 fg=GREEN if running else RED,
                 anchor="w").pack(fill="x", padx=14, pady=4)

        btns = tk.Frame(ctrl, bg=CARD)
        btns.pack(fill="x", padx=14, pady=(6, 14))
        tk.Button(btns, text="▶  Reiniciar Guardián",
                  font=F_LABEL, bg=ACCENT, fg=WHITE,
                  relief="flat", cursor="hand2", bd=0,
                  pady=8, padx=16,
                  command=self._restart_guardian).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="📂  Ver Log",
                  font=F_LABEL, bg=CARD2, fg=TEXT,
                  relief="flat", cursor="hand2", bd=0,
                  pady=8, padx=16,
                  command=lambda: os.startfile(LOG_FILE) if os.path.exists(LOG_FILE) else None
                  ).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="📸  Capturas",
                  font=F_LABEL, bg=CARD2, fg=TEXT,
                  relief="flat", cursor="hand2", bd=0,
                  pady=8, padx=16,
                  command=lambda: os.startfile(CAPTURES_DIR) if os.path.exists(CAPTURES_DIR) else None
                  ).pack(side="left")

        # Card: Umbrales
        thresh = tk.Frame(self.content, bg=CARD)
        thresh.pack(fill="x", pady=(0, 10))

        tk.Label(thresh, text="🎚  Umbrales de detección activos",
                 font=F_LABEL, bg=CARD, fg=GRAY, anchor="w").pack(
            fill="x", padx=14, pady=(12, 4))
        sep2 = tk.Frame(thresh, bg=ACCENT, height=2)
        sep2.pack(fill="x", padx=14, pady=(0, 8))

        for label, val in [
            ("Corte instantáneo (1 frame)",       "90.0 %"),
            ("Score mínimo de hit suave",          "30.0 %"),
            ("Hits necesarios en ventana de 6f",   "2 / 6"),
            ("Veto Modo Sombra (falso positivo)",  "< 5 % en pantalla completa"),
            ("Frecuencia de escaneo",              "~8 FPS (alerta: ~20 FPS)"),
            ("Latencia media por frame",           "~31 ms  (GPU DirectML)"),
        ]:
            row = tk.Frame(thresh, bg=CARD)
            row.pack(fill="x", padx=14, pady=2)
            tk.Label(row, text=label, font=F_SMALL, bg=CARD, fg=GRAY,
                     anchor="w", width=38).pack(side="left")
            tk.Label(row, text=val, font=("Courier New", 9, "bold"),
                     bg=CARD, fg=ACCENT).pack(side="left")

        # Firma
        tk.Label(thresh,
                 text="NOT AGAIN  •  v1.0 Beta  •  Motor ViT FP32  •  DirectML GPU",
                 font=F_SMALL, bg=CARD, fg=GRAY).pack(padx=14, pady=(8, 14))

    # ─────────────────────────────────────────────────────────────────────────
    def _restart_guardian(self):
        bat = os.path.join(BASE, "restart_guardian.bat")
        if os.path.exists(bat):
            subprocess.Popen(
                ["cmd", "/c", bat],
                creationflags=subprocess.CREATE_NO_WINDOW)
            messagebox.showinfo("Not Again",
                                "Guardián reiniciando…\nComprueba el estado en unos segundos.")
        else:
            messagebox.showerror("Error", f"No encontrado:\n{bat}")

    def _schedule_refresh(self):
        """Refresca el home cada 5 segundos automáticamente."""
        if self.current_page == "home":
            self._page_home()
        self.root.after(5000, self._schedule_refresh)


# ─── Lanzador ─────────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    root.configure(bg=BG)
    app = NotAgainApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
