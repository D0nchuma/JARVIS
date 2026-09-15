"""Burbuja flotante en la esquina de la pantalla que muestra el estado de
Jarvis en tiempo real: escuchando, pensando, o la respuesta.

Es una ventana de Tkinter sin bordes, siempre-arriba, semi-transparente.
Corre en su propio hilo así no bloquea el resto del programa (el hotkey
de voz, el servidor web, etc.). La comunicación entre hilos se hace con
una queue.Queue, que es segura para eso; solo el hilo de Tkinter toca los
widgets directamente.
"""
import queue
import threading
import tkinter as tk

AUTO_HIDE_MS = 7000  # tiempo que queda visible tras el último update


class Overlay:
    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._root = None
        self._label = None
        self._hide_job = None
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    # --- API pública, segura para llamar desde cualquier hilo ---
    def show(self, text: str):
        self._queue.put(("show", text))

    def update(self, text: str):
        self._queue.put(("show", text))

    def hide(self):
        self._queue.put(("hide", None))

    # --- Implementación interna (solo corre en el hilo de Tkinter) ---
    def _run(self):
        self._root = tk.Tk()
        self._root.withdraw()
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        try:
            self._root.attributes("-alpha", 0.94)
        except tk.TclError:
            pass
        self._root.configure(bg="#12151c")

        width, height = 320, 64
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        x = screen_w - width - 20
        y = screen_h - height - 60  # deja lugar para la barra de tareas
        self._root.geometry(f"{width}x{height}+{x}+{y}")

        border = tk.Frame(
            self._root, bg="#12151c",
            highlightbackground="#3b82f6", highlightthickness=2,
        )
        border.pack(fill="both", expand=True)

        self._label = tk.Label(
            border, text="", fg="#e6e9ef", bg="#12151c",
            font=("Segoe UI", 11), wraplength=280, justify="left",
        )
        self._label.pack(expand=True, padx=14, pady=8)

        self._poll()
        self._root.mainloop()

    def _poll(self):
        try:
            while True:
                action, payload = self._queue.get_nowait()
                if action == "show":
                    self._label.config(text=payload)
                    self._root.deiconify()
                    if self._hide_job is not None:
                        self._root.after_cancel(self._hide_job)
                    self._hide_job = self._root.after(AUTO_HIDE_MS, self._root.withdraw)
                elif action == "hide":
                    if self._hide_job is not None:
                        self._root.after_cancel(self._hide_job)
                        self._hide_job = None
                    self._root.withdraw()
        except queue.Empty:
            pass
        self._root.after(50, self._poll)


overlay = Overlay()
