import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re
import os
import sys

APP_TITLE = "Generador de Zócalos Pipatí"
APP_VERSION = "1.0"
W, H = 1920, 1080

DEFAULTS = {
    "top_x": 960,
    "top_y": 909,
    "bottom_x": 960,
    "bottom_y": 975,
    "top_size": 39,
    "bottom_size": 43,
    "top_max_width": 780,
    "bottom_max_width": 1300,
    "top_min_size": 22,
    "bottom_min_size": 24,
}

# Colores definidos por el diseño actual.
TOP_FILL = (145, 0, 28, 255)
BOTTOM_FILL = (255, 255, 255, 255)


def app_base():
    # En PyInstaller --onefile, los archivos incluidos se extraen
    # temporalmente en sys._MEIPASS. No están junto al .exe.
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


BASE = app_base()
ASSETS = BASE / "assets"


class GeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} — v{APP_VERSION}")
        self.root.geometry("760x560")
        self.root.resizable(False, False)
        self.params = DEFAULTS.copy()
        self.template_path = ASSETS / "plantilla_vacia.png"
        self.txt_var = tk.StringVar(value="")
        self.output_var = tk.StringVar(value=str(Path.home() / "Desktop" / "Zocalos generados"))
        self.status_var = tk.StringVar(value="Arrastrá un archivo TXT para comenzar.")
        self.count_var = tk.StringVar(value="Ningún TXT seleccionado")
        self.dnd_enabled = False
        self.build_ui()
        self.setup_drag_drop()
        self.root.after(100, self.handle_command_line_file)

    def build_ui(self):
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="GENERADOR DE ZÓCALOS", font=("Segoe UI", 20, "bold")).pack()
        ttk.Label(outer, text="Pipatí  •  TXT → PNG  •  1920×1080", font=("Segoe UI", 10)).pack(pady=(2, 16))

        drop = tk.Frame(outer, bd=2, relief="groove", height=145)
        drop.pack(fill="x", pady=(0, 14))
        drop.pack_propagate(False)
        self.drop_frame = drop
        self.drop_title = tk.Label(drop, text="ARRASTRÁ TU ARCHIVO TXT AQUÍ", font=("Segoe UI", 16, "bold"))
        self.drop_title.pack(pady=(28, 5))
        self.drop_hint = tk.Label(drop, text="o hacé clic para elegirlo", font=("Segoe UI", 10))
        self.drop_hint.pack()
        for w in (drop, self.drop_title, self.drop_hint):
            w.bind("<Button-1>", lambda e: self.choose_txt())

        info = ttk.LabelFrame(outer, text="Archivo seleccionado", padding=10)
        info.pack(fill="x", pady=(0, 12))
        ttk.Label(info, textvariable=self.txt_var, wraplength=690).pack(anchor="w")
        ttk.Label(info, textvariable=self.count_var, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(6, 0))

        out = ttk.LabelFrame(outer, text="Carpeta de salida", padding=10)
        out.pack(fill="x", pady=(0, 12))
        ttk.Entry(out, textvariable=self.output_var, width=68).pack(side="left", fill="x", expand=True)
        ttk.Button(out, text="Elegir…", command=self.choose_output).pack(side="left", padx=(8, 0))

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(2, 8))
        ttk.Button(actions, text="Vista previa", command=self.preview).pack(side="left")
        ttk.Button(actions, text="Abrir carpeta", command=self.open_output).pack(side="left", padx=8)
        self.generate_btn = ttk.Button(actions, text="GENERAR ZÓCALOS", command=self.generate)
        self.generate_btn.pack(side="right", ipadx=24, ipady=8)

        self.progress = ttk.Progressbar(outer, orient="horizontal", length=700, mode="determinate")
        self.progress.pack(fill="x", pady=(5, 4))
        ttk.Label(outer, textvariable=self.status_var).pack(anchor="w")
        ttk.Label(outer, text="La gráfica Pipatí y la configuración tipográfica están integradas y protegidas.", font=("Segoe UI", 9)).pack(pady=(16, 0))

    def setup_drag_drop(self):
        try:
            from tkinterdnd2 import DND_FILES, TkinterDnD
            # La ventana ya fue creada con Tk; TkinterDnD no puede convertirla
            # de forma segura después de creada. El soporte real se activa en
            # main() cuando el paquete está disponible.
        except Exception:
            self.drop_hint.config(text="o hacé clic para elegirlo")
            return
        self.drop_hint.config(text="o hacé clic para elegirlo")

    def handle_drop(self, event):
        try:
            from tkinterdnd2 import TkinterDnD
            paths = self.root.tk.splitlist(event.data)
            if not paths:
                return
            p = Path(paths[0])
            if p.suffix.lower() != ".txt":
                raise ValueError("Soltá un archivo .TXT")
            self.set_txt(p)
        except Exception as e:
            messagebox.showerror(APP_TITLE, str(e))

    def handle_command_line_file(self):
        if len(sys.argv) > 1:
            p = Path(sys.argv[1].strip('"'))
            if p.exists() and p.suffix.lower() == ".txt":
                self.set_txt(p)

    def set_txt(self, path):
        self.txt_var.set(str(path))
        self.refresh_count()
        self.status_var.set("TXT listo para generar.")

    def add_row(self, parent, row, label, variable, command):
        ttk.Label(parent, text=label, width=15).grid(row=row, column=0, sticky="w", pady=7)
        ttk.Entry(parent, textvariable=variable, width=72).grid(row=row, column=1, padx=7, sticky="ew")
        ttk.Button(parent, text="Elegir…", command=command).grid(row=row, column=2)
        parent.columnconfigure(1, weight=1)

    def choose_txt(self):
        p = filedialog.askopenfilename(title="Seleccionar TXT", filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")])
        if p:
            self.set_txt(Path(p))

    def choose_output(self):
        p = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if p:
            self.output_var.set(p)

    def parse_txt(self):
        p = Path(self.txt_var.get())
        if not p.exists():
            raise FileNotFoundError("Primero seleccioná o arrastrá un archivo TXT.")
        raw = p.read_text(encoding="utf-8-sig")
        lines = [x.strip() for x in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
        lines = [x for x in lines if x]
        if len(lines) % 2:
            raise ValueError("El TXT debe contener una cantidad par de líneas no vacías: línea 01 + línea 02.")
        return list(zip(lines[0::2], lines[1::2]))

    def refresh_count(self):
        try:
            pairs = self.parse_txt()
            self.count_var.set(f"✓ {len(pairs)} zócalos detectados")
        except Exception:
            self.count_var.set("No se pudo leer el TXT todavía")

    def font_paths(self):
        top = ASSETS / "FiraSansExtraCondensed-ExtraBold.ttf"
        bottom = ASSETS / "FiraSansCondensed-Black.ttf"
        if not top.exists() or not bottom.exists():
            raise FileNotFoundError("Faltan las fuentes dentro de la carpeta assets.")
        return top, bottom

    def fit_font(self, draw, text, max_width, start_size, min_size, font_path):
        for size in range(int(start_size), int(min_size) - 1, -1):
            font = ImageFont.truetype(str(font_path), size)
            box = draw.textbbox((0, 0), text, font=font)
            if box[2] - box[0] <= max_width:
                return font
        return ImageFont.truetype(str(font_path), int(min_size))

    @staticmethod
    def draw_centered(draw, text, center_x, center_y, font, fill, stable_vertical=False):
        box = draw.textbbox((0, 0), text, font=font)
        cx = (box[0] + box[2]) / 2
        if stable_vertical:
            y = center_y - box[3]
        else:
            cy = (box[1] + box[3]) / 2
            y = center_y - cy
        draw.text((center_x - cx, y), text, font=font, fill=fill)

    def render(self, top, bottom):
        if not self.template_path.exists():
            raise FileNotFoundError("No se encontró la gráfica integrada de Pipatí.")
        im = Image.open(self.template_path).convert("RGBA")
        if im.size != (W, H):
            raise ValueError(f"La plantilla debe ser 1920×1080. La seleccionada es {im.width}×{im.height}.")
        top_font_path, bottom_font_path = self.font_paths()
        draw = ImageDraw.Draw(im)
        p = self.params
        f1 = self.fit_font(draw, top, p["top_max_width"], p["top_size"], p["top_min_size"], top_font_path)
        f2 = self.fit_font(draw, bottom, p["bottom_max_width"], p["bottom_size"], p["bottom_min_size"], bottom_font_path)
        self.draw_centered(draw, top, p["top_x"], 928.5, f1, TOP_FILL, stable_vertical=True)
        self.draw_centered(draw, bottom, p["bottom_x"], p["bottom_y"], f2, BOTTOM_FILL)
        return im

    @staticmethod
    def safe_name(text):
        text = re.sub(r'[\\/:*?"<>|]', "", text).strip()
        return text[:80] or "zocalo"

    def generate(self):
        try:
            pairs = self.parse_txt()
            if not pairs:
                raise ValueError("No se encontraron pares de líneas en el TXT.")
            out = Path(self.output_var.get())
            out.mkdir(parents=True, exist_ok=True)
            self.progress["maximum"] = len(pairs)
            self.progress["value"] = 0
            self.generate_btn.config(state="disabled")
            for idx, (top, bottom) in enumerate(pairs, 1):
                self.status_var.set(f"Generando zócalo {idx}/{len(pairs)}…")
                self.root.update_idletasks()
                self.render(top, bottom).save(out / f"{idx:02d} - {self.safe_name(top)}.png", "PNG")
                self.progress["value"] = idx
            self.status_var.set(f"✓ Proceso terminado: {len(pairs)} PNG generados.")
            messagebox.showinfo(APP_TITLE, f"Proceso terminado.\n\nGenerados: {len(pairs)} PNG\n\nCarpeta:\n{out}")
            self.open_output()
        except Exception as e:
            self.status_var.set("Se produjo un error.")
            messagebox.showerror(APP_TITLE, str(e))
        finally:
            self.generate_btn.config(state="normal")

    def preview(self):
        try:
            pairs = self.parse_txt()
            if not pairs:
                raise ValueError("No hay textos para previsualizar.")
            im = self.render(*pairs[0])
            preview = Path(self.output_var.get()) / "PREVIEW_primer_zocalo.png"
            preview.parent.mkdir(parents=True, exist_ok=True)
            im.save(preview, "PNG")
            try:
                os.startfile(str(preview))
            except Exception:
                messagebox.showinfo(APP_TITLE, f"Vista previa creada en:\n{preview}")
        except Exception as e:
            messagebox.showerror(APP_TITLE, str(e))

    def open_output(self):
        p = Path(self.output_var.get())
        p.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(p))
        except Exception:
            pass


if __name__ == "__main__":
    try:
        from tkinterdnd2 import TkinterDnD, DND_FILES
        root = TkinterDnD.Tk()
        dnd_ok = True
    except Exception:
        root = tk.Tk()
        dnd_ok = False
    try:
        ttk.Style().theme_use("vista")
    except Exception:
        pass
    app = GeneratorApp(root)
    if dnd_ok:
        app.drop_frame.drop_target_register(DND_FILES)
        app.drop_frame.dnd_bind("<<Drop>>", app.handle_drop)
        app.drop_title.drop_target_register(DND_FILES)
        app.drop_title.dnd_bind("<<Drop>>", app.handle_drop)
        app.drop_hint.drop_target_register(DND_FILES)
        app.drop_hint.dnd_bind("<<Drop>>", app.handle_drop)
    root.mainloop()
