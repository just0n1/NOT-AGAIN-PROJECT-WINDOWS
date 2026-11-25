import os
import sys
import json
import random
import tkinter as tk

def get_random_verse():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    verses_path = os.path.join(script_dir, "verses.json")
    if os.path.exists(verses_path):
        try:
            with open(verses_path, "r", encoding="utf-8") as f:
                verses = json.load(f)
                if verses:
                    return random.choice(verses)
        except Exception:
            pass
    return {
        "reference": "1 Corintios 6:18",
        "text": "Huid de la fornicación. Cualquier otro pecado que el hombre cometa, está fuera del cuerpo; mas el que fornica, contra su propio cuerpo peca."
    }

class LockScreen:
    def __init__(self, root, duration=60):
        self.root = root
        self.remaining_seconds = duration
        self.verse = get_random_verse()

        # Window settings
        self.root.title("Not Again - Alto en el Nombre del Señor")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#0B0E14")
        
        # Override close button and Alt+F4
        self.root.protocol("WM_DELETE_WINDOW", self.prevent_close)
        self.root.bind("<Alt-F4>", lambda e: "break")
        self.root.bind("<Escape>", lambda e: "break")

        # Container
        self.frame = tk.Frame(self.root, bg="#0B0E14", padx=60, pady=40)
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        # Warning Header
        self.header_label = tk.Label(
            self.frame,
            text="⚠️  NOT AGAIN — IMPULSO INTERCEPTADO  ⚠️",
            font=("Segoe UI", 26, "bold"),
            fg="#E63946",
            bg="#0B0E14"
        )
        self.header_label.pack(pady=(0, 25))

        # Subtitle
        self.sub_label = tk.Label(
            self.frame,
            text="El navegador ha sido cerrado para proteger tu mente y tu comunión con Dios.\nRespira, detente y examina tu corazón.",
            font=("Segoe UI", 14),
            fg="#A0AAB8",
            bg="#0B0E14",
            justify="center"
        )
        self.sub_label.pack(pady=(0, 35))

        # Divider
        self.divider = tk.Frame(self.frame, height=2, width=600, bg="#1E2638")
        self.divider.pack(pady=10)

        # Scripture Container
        self.verse_text_label = tk.Label(
            self.frame,
            text=f"«{self.verse['text']}»",
            font=("Georgia", 16, "italic"),
            fg="#F1FAEE",
            bg="#0B0E14",
            wraplength=900,
            justify="center"
        )
        self.verse_text_label.pack(pady=(25, 15))

        self.verse_ref_label = tk.Label(
            self.frame,
            text=f"— {self.verse['reference']}",
            font=("Segoe UI", 15, "bold"),
            fg="#457B9D",
            bg="#0B0E14"
        )
        self.verse_ref_label.pack(pady=(0, 30))

        # Timer Display
        self.timer_label = tk.Label(
            self.frame,
            text=f"Tiempo de enfriamiento y oración: {self.remaining_seconds}s",
            font=("Segoe UI", 20, "bold"),
            fg="#A8DADC",
            bg="#0B0E14"
        )
        self.timer_label.pack(pady=(10, 30))

        # Close button (starts disabled)
        self.close_btn = tk.Button(
            self.frame,
            text="Bloqueo activo...",
            font=("Segoe UI", 13, "bold"),
            bg="#1E2638",
            fg="#5C677D",
            state="disabled",
            padx=25,
            pady=10,
            relief="flat",
            command=self.finish_lock
        )
        self.close_btn.pack()

        self.update_timer()

    def prevent_close(self):
        pass  # Do nothing while locked

    def update_timer(self):
        if self.remaining_seconds > 0:
            self.timer_label.configure(
                text=f"Tiempo de enfriamiento y oración: {self.remaining_seconds}s"
            )
            self.remaining_seconds -= 1
            self.root.after(1000, self.update_timer)
        else:
            self.timer_label.configure(
                text="Tiempo cumplido. Que la gracia de Dios te sostenga hoy.",
                fg="#2A9D8F"
            )
            self.close_btn.configure(
                text="He recuperado el dominio propio (Continuar)",
                bg="#2A9D8F",
                fg="#FFFFFF",
                state="normal",
                cursor="hand2"
            )

    def finish_lock(self):
        self.root.destroy()
        sys.exit(0)

def show_lockscreen(duration=60):
    root = tk.Tk()
    app = LockScreen(root, duration=duration)
    root.mainloop()

if __name__ == "__main__":
    duration = 60
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            pass
    show_lockscreen(duration)
