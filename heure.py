import tkinter as tk
from tkinter import filedialog, colorchooser, ttk
import json
import os
import sys
from time import strftime
from PIL import Image, ImageTk
import ctypes

# Tenter d'importer screeninfo, sinon on gère l'erreur
try:
    from screeninfo import get_monitors
except ImportError:
    print("Erreur : Vous devez installer screeninfo (pip install screeninfo)")
    sys.exit(1)

# --- FIX DPI AGRESSIF POUR WINDOWS ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(base_path, "config_horloge.json")

class HorlogePleinEcran:
    def __init__(self, root):
        self.root = root
        self.root.title("Config Horloge Pro")
        self.root.geometry("450x750")

        self.config = self.charger_config()
        
        # Récupération des moniteurs
        try:
            self.monitors = get_monitors()
        except Exception:
            # Fallback si screeninfo échoue
            class MockMonitor:
                def __init__(self):
                    self.x=0; self.y=0; self.width=1920; self.height=1080
            self.monitors = [MockMonitor()]
        
        # --- Interface ---
        tk.Label(root, text="Paramètres de l'Horloge", font=("Arial", 14, "bold")).pack(pady=10)

        # Sélection de l'écran
        tk.Label(root, text="Choisir l'écran :", font=("Arial", 10, "bold")).pack()
        ecrans_liste = [f"Écran {i+1} ({m.width}x{m.height})" for i, m in enumerate(self.monitors)]
        self.combo_ecran = ttk.Combobox(root, state="readonly", values=ecrans_liste)
        self.combo_ecran.current(0)
        self.combo_ecran.pack(pady=5)

        # Boutons et Scales
        tk.Button(root, text="Choisir l'Image de fond", command=self.choisir_image).pack(pady=10)
        self.lbl_img = tk.Label(root, text=os.path.basename(self.config['image_path']) if self.config['image_path'] else "Aucune image", fg="blue")
        self.lbl_img.pack()

        tk.Label(root, text="Couleur du texte :").pack(pady=(10,0))
        self.btn_color = tk.Button(root, text="Couleur", command=self.choisir_couleur, width=15)
        self.btn_color.pack(pady=5)
        self.update_color_button_preview()

        tk.Label(root, text="Taille de la police :").pack()
        self.size_scale = tk.Scale(root, from_=10, to_=1200, orient="horizontal")
        self.size_scale.set(self.config['font_size'])
        self.size_scale.pack(fill="x", padx=40)

        tk.Label(root, text="Position Horizontale (%) :").pack()
        self.pos_x = tk.Scale(root, from_=0, to_=100, orient="horizontal")
        self.pos_x.set(self.config['pos_x'])
        self.pos_x.pack(fill="x", padx=40)

        tk.Label(root, text="Position Verticale (%) :").pack()
        self.pos_y = tk.Scale(root, from_=0, to_=100, orient="horizontal")
        self.pos_y.set(self.config['pos_y'])
        self.pos_y.pack(fill="x", padx=40)

        tk.Button(root, text="LANCER L'HORLOGE", bg="#2ecc71", fg="white", 
                  command=self.lancer_affichage, font=("Arial", 11, "bold"), height=2).pack(pady=30)
        
        tk.Label(root, text="ESC pour quitter", font=("Arial", 8, "italic")).pack()

    def charger_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f: return json.load(f)
            except: pass
        return {"image_path": "", "font_color": "#FFFFFF", "font_size": 150, "pos_x": 50, "pos_y": 50}

    def sauver_config(self):
        self.config.update({
            "font_size": self.size_scale.get(), 
            "pos_x": self.pos_x.get(), 
            "pos_y": self.pos_y.get()
        })
        with open(CONFIG_FILE, "w") as f: json.dump(self.config, f, indent=4)

    def choisir_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.config['image_path'] = path
            self.lbl_img.config(text=os.path.basename(path))

    def choisir_couleur(self):
        color = colorchooser.askcolor(initialcolor=self.config['font_color'])
        if color[1]:
            self.config['font_color'] = color[1]
            self.update_color_button_preview()

    def update_color_button_preview(self):
        self.btn_color.config(bg=self.config['font_color'])

    def lancer_affichage(self):
        if not self.config['image_path'] or not os.path.exists(self.config['image_path']):
            return
        
        self.sauver_config()
        
        idx = self.combo_ecran.current()
        m = self.monitors[idx]

        self.top = tk.Toplevel(self.root)
        self.top.overrideredirect(True)
        self.top.geometry(f"{m.width}x{m.height}+{m.x}+{m.y}")
        
        self.top.config(cursor="none", bg="black")
        self.top.bind("<Escape>", lambda e: self.top.destroy())

        img = Image.open(self.config['image_path'])
        img = img.resize((m.width, m.height), Image.Resampling.LANCZOS)
        self.bg_img = ImageTk.PhotoImage(img)

        self.canvas = tk.Canvas(self.top, width=m.width, height=m.height, highlightthickness=0, bg="black")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_img, anchor="nw")

        rx = (self.config['pos_x'] / 100) * m.width
        ry = (self.config['pos_y'] / 100) * m.height

        self.text_id = self.canvas.create_text(
            rx, ry, text="", fill=self.config['font_color'],
            font=("Arial", self.config['font_size'], "bold"), anchor="center"
        )
        self.actualiser_heure()

    def actualiser_heure(self):
        if not hasattr(self, 'top') or not self.top.winfo_exists(): return
        self.canvas.itemconfig(self.text_id, text=strftime('%H:%M:%S'))
        self.top.after(1000, self.actualiser_heure)

if __name__ == "__main__":
    root = tk.Tk()
    app = HorlogePleinEcran(root)
    root.mainloop()