import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re
import os
import sys

APP_TITLE = "Generador de Zócalos Pipatí"
APP_VERSION = "0.2"
W, H = 1920, 1080

DEFAULTS = {
    "top_x": 960,
    "top_y": 905,
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
    # Compatible con ejecución normal y con PyInstaller --onefile.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
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

        self.template_var = tk.StringVar(value=str(ASSETS / "plantilla_vacia.png"))
        self.txt_var = tk.StringVar(value=str(BASE / "ejemplo_zocalos.txt"))
        self.output_var = tk.StringVar(value=str(BASE / "salida"))
        self.status_var = tk.StringVar(value="Listo para generar.")
        self.count_var = tk.StringVar(value="")

        self.build_ui()

    def build_ui(self):
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="GENERADOR DE ZÓCALOS", font=("Segoe UI", 19, "bold")).pack()
        ttk.Label(outer, text="TXT → PNG  •  1920×1080  •  sin Photoshop", font=("Segoe UI", 10)).pack(pady=(2, 18))

        files = ttk.LabelFrame(outer, text="Archivos", padding=12)
        files.pack(fill="x")
        self.add_row(files, 0, "Plantilla PNG", self.template_var, self.choose_template)
        self.add_row(files, 1, "Archivo TXT", self.txt_var, self.choose_txt)
        self.add_row(files, 2, "Carpeta salida", self.output_var, self.choose_output)

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(14, 8))
        ttk.Button(actions, text="Ajustes", command=self.settings).pack(side="left")
        ttk.Button(actions, text="Vista previa", command=self.preview).pack(side="left", padx=8)
        ttk.Button(actions, text="Abrir carpeta de salida", command=self.open_output).pack(side="left")

        self.generate_btn = ttk.Button(actions, text="GENERAR ZÓCALOS", command=self.generate)
        self.generate_btn.pack(side="right", ipadx=18, ipady=5)

        info = ttk.LabelFrame(outer, text="Resumen", padding=12)
        info.pack(fill="x", pady=(4, 10))
        ttk.Label(info, textvariable=self.count_var, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(info, text="Cada par de líneas del TXT genera un PNG independiente con fondo transparente.", wraplength=690).pack(anchor="w", pady=(5, 0))

        self.progress = ttk.Progressbar(outer, orient="horizontal", length=700, mode="determinate")
        self.progress.pack(fill="x", pady=(5, 4))
        ttk.Label(outer, textvariable=self.status_var).pack(anchor="w")

        ttk.Label(
            outer,
            text="La plantilla gráfica queda intacta; la aplicación sólo coloca y ajusta automáticamente los textos.",
            font=("Segoe UI", 9)
        ).pack(pady=(18, 0))

        self.refresh_count()

    def add_row(self, parent, row, label, variable, command):
        ttk.Label(parent, text=label, width=15).grid(row=row, column=0, sticky="w", pady=7)
        ttk.Entry(parent, textvariable=variable, width=72).grid(row=row, column=1, padx=7, sticky="ew")
        ttk.Button(parent, text="Elegir…", command=command).grid(row=row, column=2)
        parent.columnconfigure(1, weight=1)

    def choose_template(self):
        p = filedialog.askopenfilename(title="Seleccionar plantilla PNG", filetypes=[("PNG", "*.png"), ("Todos los archivos", "*.*")])
        if p:
            self.template_var.set(p)

    def choose_txt(self):
        p = filedialog.askopenfilename(title="Seleccionar TXT", filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")])
        if p:
            self.txt_var.set(p)
            self.refresh_count()

    def choose_output(self):
        p = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if p:
            self.output_var.set(p)

    def parse_txt(self):
        p = Path(self.txt_var.get())
        if not p.exists():
            raise FileNotFoundError(f"No se encontró el TXT:\n{p}")
        raw = p.read_text(encoding="utf-8-sig")
        lines = [x.strip() for x in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
        lines = [x for x in lines if x]
        if len(lines) % 2:
            raise ValueError("El TXT debe contener una cantidad par de líneas no vacías: línea 01 + línea 02.")
        return list(zip(lines[0::2], lines[1::2]))

    def refresh_count(self):
        try:
            pairs = self.parse_txt()
            self.count_var.set(f"{len(pairs)} zócalos detectados en el TXT")
        except Exception as e:
            self.count_var.set("No se pudo leer el TXT todavía.")

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
    def draw_centered(draw, text, center_x, center_y, font, fill):
        box = draw.textbbox((0, 0), text, font=font)
        cx = (box[0] + box[2]) / 2
        cy = (box[1] + box[3]) / 2
        draw.text((center_x - cx, center_y - cy), text, font=font, fill=fill)

    def render(self, top, bottom):
        template = Path(self.template_var.get())
        if not template.exists():
            raise FileNotFoundError(f"No se encontró la plantilla:\n{template}")
        im = Image.open(template).convert("RGBA")
        if im.size != (W, H):
            raise ValueError(f"La plantilla debe ser 1920×1080. La seleccionada es {im.width}×{im.height}.")

        top_font_path, bottom_font_path = self.font_paths()
        draw = ImageDraw.Draw(im)
        p = self.params
        f1 = self.fit_font(draw, top, p["top_max_width"], p["top_size"], p["top_min_size"], top_font_path)
        f2 = self.fit_font(draw, bottom, p["bottom_max_width"], p["bottom_size"], p["bottom_min_size"], bottom_font_path)
        self.draw_centered(draw, top, p["top_x"], p["top_y"], f1, TOP_FILL)
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
                self.status_var.set(f"Generando {idx}/{len(pairs)}…")
                self.root.update_idletasks()
                im = self.render(top, bottom)
                name = f"{idx:02d} - {self.safe_name(top)}.png"
                im.save(out / name, "PNG")
                self.progress["value"] = idx

            self.status_var.set(f"Proceso terminado: {len(pairs)} PNG generados.")
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

    def settings(self):
        win = tk.Toplevel(self.root)
        win.title("Ajustes del diseño")
        win.geometry("410x455")
        win.resizable(False, False)
        fields = [
            ("X línea 01", "top_x"), ("Y línea 01", "top_y"),
            ("X línea 02", "bottom_x"), ("Y línea 02", "bottom_y"),
            ("Tamaño línea 01", "top_size"), ("Tamaño línea 02", "bottom_size"),
            ("Ancho máximo línea 01", "top_max_width"), ("Ancho máximo línea 02", "bottom_max_width"),
        ]
        vars_ = {}
        for r, (label, key) in enumerate(fields):
            ttk.Label(win, text=label, width=24).grid(row=r, column=0, padx=12, pady=7, sticky="w")
            v = tk.StringVar(value=str(self.params[key]))
            vars_[key] = v
            ttk.Entry(win, textvariable=v, width=15).grid(row=r, column=1, padx=8, pady=7)

        ttk.Label(win, text="Estos parámetros quedan guardados sólo durante esta ejecución.", wraplength=360).grid(row=8, column=0, columnspan=2, padx=15, pady=(8, 4))

        def save():
            try:
                for key, v in vars_.items():
                    self.params[key] = int(float(v.get()))
                win.destroy()
            except ValueError:
                messagebox.showerror("Ajustes", "Todos los valores deben ser numéricos.")

        ttk.Button(win, text="Guardar", command=save).grid(row=9, column=0, columnspan=2, pady=20)


if __name__ == "__main__":
    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista")
    except Exception:
        pass
    GeneratorApp(root)
    root.mainloop()
