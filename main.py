import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import serial
import serial.tools.list_ports
import time
from player_solo import SoloPlayer
from player_arpej import ChiptunePlayer

# --- RENK PALETİ ---
COLORS = {
    "bg": "#1a1a1a",
    "panel_bg": "#2d2d2d",
    "panel_header": "#00bcd4",
    "accent": "#00bcd4",
    "accent_hover": "#26c6da",
    "text": "#ecf0f1",
    "text_dim": "#95a5a6",
    "danger": "#ff5252",
    "danger_hover": "#ff7979",
    "success": "#4caf50",
    "success_hover": "#66bb6a",
    "lcd_bg": "#0a0a0a",
    "lcd_text": "#00ff41",
    "border": "#3d3d3d",
    "text_black": "#1a1a1a"
}

class ModernButton(tk.Button):
    """Hover efektli modern buton"""
    def __init__(self, master, **kwargs):
        self.default_bg = kwargs.get("bg", COLORS["panel_bg"])
        self.hover_bg = kwargs.pop("hover_bg", self.default_bg)
        super().__init__(master, **kwargs)
        self.configure(
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=kwargs.get("font", ("Segoe UI", 10, "bold")),
            padx=15,
            pady=8
        )
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, e):
        if self['state'] != 'disabled':
            self['bg'] = self.hover_bg
    
    def on_leave(self, e):
        if self['state'] != 'disabled':
            self['bg'] = self.default_bg

class CustomRadioButton(tk.Canvas):
    """Özel radio button"""
    def __init__(self, parent, text, variable, value, **kwargs):
        super().__init__(parent, bg=COLORS["panel_bg"], height=30, highlightthickness=0)
        self.variable = variable
        self.value = value
        self.text = text
        
        # Circle ve text çiz
        self.circle = self.create_oval(5, 8, 20, 23, outline=COLORS["text_dim"], width=2)
        self.inner_circle = None
        self.text_id = self.create_text(28, 15, text=text, anchor="w", 
                                        fill=COLORS["text"], font=("Segoe UI", 10))
        
        self.bind("<Button-1>", self.on_click)
        self.bind("<Enter>", lambda e: self.config(cursor="hand2"))
        
        # İlk durumu ayarla
        self.update_display()
        
        # Variable değişikliklerini dinle
        self.variable.trace('w', lambda *args: self.update_display())
    
    def on_click(self, event):
        self.variable.set(self.value)
    
    def update_display(self):
        if self.variable.get() == self.value:
            # Seçili
            if self.inner_circle:
                self.delete(self.inner_circle)
            self.inner_circle = self.create_oval(9, 12, 16, 19, fill=COLORS["accent"], outline="")
            self.itemconfig(self.circle, outline=COLORS["accent"])
            self.itemconfig(self.text_id, fill=COLORS["accent"])
        else:
            # Seçili değil
            if self.inner_circle:
                self.delete(self.inner_circle)
            self.itemconfig(self.circle, outline=COLORS["text_dim"])
            self.itemconfig(self.text_id, fill=COLORS["text"])

class ArduinoBuzzer:
    """Arduino iletişim sınıfı"""
    def __init__(self):
        self.ser = None
        self.last_freq = -1
        self.is_connected = False
    
    def connect(self, port):
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.ser = serial.Serial(port, 115200, timeout=0.05)
            time.sleep(2)
            self.is_connected = True
            return True, "Başarıyla bağlandı"
        except Exception as e:
            self.is_connected = False
            return False, f"Bağlantı hatası: {str(e)}"
    
    def send_freq(self, freq):
        if not self.is_connected:
            return
        try:
            if freq != self.last_freq:
                self.ser.write(f"{freq},0\n".encode())
                self.last_freq = freq
        except:
            pass
    
    def get_stats(self):
        if not self.is_connected:
            return None
        try:
            self.ser.reset_input_buffer()
            self.ser.write(b"?\n")
            time.sleep(0.05)
            if self.ser.in_waiting:
                line = self.ser.readline().decode('utf-8').strip()
                if line.startswith("STATS:"):
                    parts = line.split(":")[1].split(",")
                    return {
                        'temp': parts[0],
                        'ram': parts[1],
                        'uptime': int(parts[2]) // 1000
                    }
        except:
            return None
        return None
    
    def stop(self):
        self.send_freq(0)
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.is_connected = False
    
    @staticmethod
    def midi_to_freq(note):
        return int(440 * (2 ** ((note - 69) / 12))) if note > 0 else 0
    
    @staticmethod
    def get_note_name(note):
        if note <= 0:
            return "Sus"
        names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        return f"{names[note % 12]}{(note // 12) - 1}"

class MidiPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Arduino MIDI Studio Pro")
        self.root.geometry("900x750")
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(False, False)
        
        self.buzzer = ArduinoBuzzer()
        self.current_thread = None
        self.midi_path = None
        
        self.setup_ui()
        self.refresh_ports()
        self.update_telemetry()
    
    def setup_ui(self):
        # === HEADER ===
        self.create_header()
        
        # === MAIN CONTENT ===
        main_container = tk.Frame(self.root, bg=COLORS["bg"])
        main_container.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        
        # Sol panel
        left_panel = tk.Frame(main_container, bg=COLORS["bg"], width=420)
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False)
        
        self.create_connection_panel(left_panel)
        self.create_file_panel(left_panel)
        self.create_mixer_panel(left_panel)
        self.create_mode_panel(left_panel)
        
        # Sağ panel
        right_panel = tk.Frame(main_container, bg=COLORS["bg"])
        right_panel.pack(side="right", fill="both", expand=True)
        
        self.create_lcd_display(right_panel)
        self.create_telemetry_panel(right_panel)
        self.create_controls(right_panel)  # Butonları sağ panele taşıdık
    
    def create_header(self):
        """Üst başlık"""
        header = tk.Frame(self.root, bg=COLORS["bg"], height=60)
        header.pack(fill="x", padx=20, pady=(20, 10))
        header.pack_propagate(False)
        
        title_frame = tk.Frame(header, bg=COLORS["bg"])
        title_frame.pack(side="left")
        
        tk.Label(
            title_frame,
            text="ARDUINO MIDI STUDIO",
            bg=COLORS["bg"],
            fg=COLORS["accent"],
            font=("Montserrat", 24, "bold")
        ).pack(anchor="w")
        
        tk.Label(
            title_frame,
            text="MIDI Oynatıcısı ve Telemetri İzleyici",
            bg=COLORS["bg"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(2, 0))
        
        tk.Label(
            header,
            text="v4.5",
            bg=COLORS["bg"],
            fg=COLORS["text_dim"],
            font=("Consolas", 10)
        ).pack(side="right", anchor="ne")
    
    def create_panel(self, parent, title):
        """Panel container oluştur"""
        container = tk.Frame(parent, bg=COLORS["bg"])
        container.pack(fill="x", pady=(0, 12))
        
        # Header
        header = tk.Frame(container, bg=COLORS["panel_header"], height=28)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=title,
            bg=COLORS["panel_header"],
            fg="white",
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=10)
        
        # Content
        content = tk.Frame(container, bg=COLORS["panel_bg"])
        content.pack(fill="both", expand=True)
        
        return content
    
    def create_connection_panel(self, parent):
        """Bağlantı paneli"""
        content = self.create_panel(parent, "BAĞLANTI")
        
        inner = tk.Frame(content, bg=COLORS["panel_bg"])
        inner.pack(fill="x", padx=12, pady=12)
        
        tk.Label(
            inner,
            text="Seri Port:",
            bg=COLORS["panel_bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(0, 5))
        
        port_frame = tk.Frame(inner, bg=COLORS["panel_bg"])
        port_frame.pack(fill="x")
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox",
            fieldbackground=COLORS["panel_bg"],
            background=COLORS["bg"],
            foreground=COLORS["text_black"],
            arrowcolor=COLORS["accent"],
            borderwidth=0
        )
        
        self.combo_port = ttk.Combobox(
            port_frame,
            state="readonly",
            width=25,
            font=("Consolas", 9)
        )
        self.combo_port.pack(side="left", fill="x", expand=True)
        
        ModernButton(
            port_frame,
            text="⟳",
            command=self.refresh_ports,
            bg=COLORS["accent"],
            fg="white",
            hover_bg=COLORS["accent_hover"],
            width=3
        ).pack(side="right", padx=(5, 0))
    
    def create_file_panel(self, parent):
        """Dosya seçim paneli"""
        content = self.create_panel(parent, "MIDI DOSYASI")
        
        inner = tk.Frame(content, bg=COLORS["panel_bg"])
        inner.pack(fill="both", padx=12, pady=12)
        
        ModernButton(
            inner,
            text="DOSYA SEÇ",
            command=self.select_file,
            bg="#424242",
            fg=COLORS["text"],
            hover_bg="#525252",
            font=("Segoe UI", 9, "bold")
        ).pack(fill="x")
        
        self.lbl_file = tk.Label(
            inner,
            text="Henüz dosya seçilmedi",
            bg=COLORS["panel_bg"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "italic"),
            anchor="w",
            wraplength=380,
            justify="left"
        )
        self.lbl_file.pack(fill="x", pady=(8, 0))
    
    def create_mixer_panel(self, parent):
        """Mikser ayarları paneli"""
        content = self.create_panel(parent, "MİKSER AYARLARI")
        
        inner = tk.Frame(content, bg=COLORS["panel_bg"])
        inner.pack(fill="both", padx=12, pady=12)
        
        # Oynatma hızı
        self.var_speed = tk.DoubleVar(value=1.0)
        self.create_slider(inner, "Oynatma Hızı (Tempo)", 0.5, 2.0, self.var_speed, 0.1, "x")
        
        # Transpoze
        self.var_transpose = tk.IntVar(value=0)
        self.create_slider(inner, "Transpoze (Pitch)", -12, 12, self.var_transpose, 1)
        
        # Arpej hızı
        self.var_arp = tk.IntVar(value=40)
        self.create_slider(inner, "Arpej Gecikmesi", 10, 100, self.var_arp, 1, "ms")
    
    def create_mode_panel(self, parent):
        """Çalma modu paneli"""
        content = self.create_panel(parent, "ÇALMA MODU")
        
        inner = tk.Frame(content, bg=COLORS["panel_bg"])
        inner.pack(fill="both", padx=12, pady=12)
        
        self.mode = tk.StringVar(value="solo")
        
        # SOLO modu
        solo_btn = CustomRadioButton(
            inner,
            "SOLO (Net Ses)",
            self.mode,
            "solo"
        )
        solo_btn.pack(fill="x", pady=5)
        
        # CHIPTUNE modu
        chip_btn = CustomRadioButton(
            inner,
            "CHIPTUNE (Retro 8-bit)",
            self.mode,
            "arpej"
        )
        chip_btn.pack(fill="x", pady=5)
    
    def create_lcd_display(self, parent):
        """LCD ekran"""
        lcd_container = tk.Frame(parent, bg=COLORS["bg"])
        lcd_container.pack(fill="x", pady=(0, 12))
        
        tk.Label(
            lcd_container,
            text="STATUS MONITOR",
            bg=COLORS["bg"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", pady=(0, 5))
        
        lcd_frame = tk.Frame(lcd_container, bg="#000", padx=3, pady=3)
        lcd_frame.pack(fill="x")
        
        self.lbl_status = tk.Label(
            lcd_frame,
            text="READY",
            font=("Consolas", 28, "bold"),
            bg=COLORS["lcd_bg"],
            fg=COLORS["text_dim"],
            height=2
        )
        self.lbl_status.pack(fill="both")
    
    def create_telemetry_panel(self, parent):
        """Telemetri paneli"""
        content = self.create_panel(parent, "DONANIM DURUMU")
        
        inner = tk.Frame(content, bg=COLORS["panel_bg"])
        inner.pack(fill="both", padx=15, pady=15)
        
        # Grid ayarları
        inner.columnconfigure(1, weight=1)
        
        # Sıcaklık
        self.lbl_temp = self.create_stat_row(
            inner, 0, "Chip Sıcaklığı:", "-- °C", "#ff6b6b"
        )
        
        # RAM
        self.lbl_ram = self.create_stat_row(
            inner, 1, "Boş RAM:", "-- Bytes", "#4ecdc4"
        )
        
        # Uptime
        self.lbl_uptime = self.create_stat_row(
            inner, 2, "Çalışma Süresi:", "-- s", "#95e1d3"
        )
        
        # Ayırıcı
        tk.Frame(inner, bg=COLORS["border"], height=1).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=12
        )
        
        # Alt bilgi
        tk.Label(
            inner,
            text="ARDUINO UNO/NANO\nATmega328P Live Monitor",
            bg=COLORS["panel_bg"],
            fg=COLORS["text_dim"],
            font=("Consolas", 7),
            justify="center"
        ).grid(row=4, column=0, columnspan=2)
    
    def create_controls(self, parent):
        """Kontrol butonları - Sağ panelde"""
        controls = tk.Frame(parent, bg=COLORS["bg"])
        controls.pack(fill="x", pady=(15, 0))
        
        # OYNAT butonu
        self.btn_play = ModernButton(
            controls,
            text="▶ OYNAT",
            command=self.start,
            bg=COLORS["success"],
            fg="white",
            hover_bg=COLORS["success_hover"],
            font=("Segoe UI", 12, "bold"),
            pady=12
        )
        self.btn_play.pack(fill="x", pady=(0, 10))
        
        # DURDUR butonu
        self.btn_stop = ModernButton(
            controls,
            text="⏹ DURDUR",
            command=self.stop,
            bg=COLORS["danger"],
            fg="white",
            hover_bg=COLORS["danger_hover"],
            font=("Segoe UI", 12, "bold"),
            pady=12
        )
        self.btn_stop.pack(fill="x")
        self.btn_stop.config(state="disabled", bg="#3a3a3a")
    
    def create_slider(self, parent, label, from_, to_, var, res=1, suffix=""):
        """Slider oluştur"""
        frame = tk.Frame(parent, bg=COLORS["panel_bg"])
        frame.pack(fill="x", pady=(0, 10))
        
        # Label ve değer
        label_frame = tk.Frame(frame, bg=COLORS["panel_bg"])
        label_frame.pack(fill="x")
        
        tk.Label(
            label_frame,
            text=label,
            bg=COLORS["panel_bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 9)
        ).pack(side="left")
        
        value_label = tk.Label(
            label_frame,
            text=f"{var.get()}{suffix}",
            bg=COLORS["panel_bg"],
            fg=COLORS["accent"],
            font=("Consolas", 9, "bold")
        )
        value_label.pack(side="right")
        
        # Slider
        scale = tk.Scale(
            frame,
            from_=from_,
            to=to_,
            resolution=res,
            orient="horizontal",
            variable=var,
            bg=COLORS["panel_bg"],
            fg=COLORS["accent"],
            highlightthickness=0,
            troughcolor="#1a1a1a",
            activebackground=COLORS["accent"],
            borderwidth=0,
            showvalue=0,
            command=lambda v: value_label.config(
                text=f"{float(v):.1f}{suffix}" if res < 1 else f"{int(float(v))}{suffix}"
            )
        )
        scale.pack(fill="x", pady=(3, 0))
    
    def create_stat_row(self, parent, row, label, value, color):
        """İstatistik satırı oluştur"""
        tk.Label(
            parent,
            text=label,
            bg=COLORS["panel_bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 10)
        ).grid(row=row, column=0, sticky="w", pady=8)
        
        value_label = tk.Label(
            parent,
            text=value,
            bg=COLORS["panel_bg"],
            fg=color,
            font=("Consolas", 10, "bold")
        )
        value_label.grid(row=row, column=1, sticky="e", pady=8)
        
        return value_label
    
    def get_settings(self):
        """Ayarları al"""
        return {
            'transpose': self.var_transpose.get(),
            'playback_speed': self.var_speed.get(),
            'arp_speed': self.var_arp.get()
        }
    
    def update_telemetry(self):
        """Telemetri güncelle"""
        if self.buzzer.is_connected:
            stats = self.buzzer.get_stats()
            if stats:
                self.lbl_temp.config(text=f"{stats['temp']} °C")
                self.lbl_ram.config(text=f"{stats['ram']} Bytes")
                self.lbl_uptime.config(text=f"{stats['uptime']} s")
        
        self.root.after(2000, self.update_telemetry)
    
    def refresh_ports(self):
        """Portları tazele"""
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.combo_port['values'] = ports
        if ports:
            self.combo_port.current(0)
    
    def select_file(self):
        """MIDI dosyası seç"""
        path = filedialog.askopenfilename(
            title="MIDI Dosyası Seçin",
            filetypes=[("MIDI Files", "*.mid"), ("All Files", "*.*")]
        )
        if path:
            self.midi_path = path
            filename = path.split("/")[-1]
            display_name = filename if len(filename) <= 45 else filename[:42] + "..."
            self.lbl_file.config(
                text=f"✓ {display_name}",
                fg=COLORS["success"],
                font=("Segoe UI", 8, "bold")
            )
    
    def update_ui_status(self, text, active):
        """UI durumunu güncelle"""
        if text == "READY":
            color = COLORS["text_dim"]
        elif active:
            color = COLORS["lcd_text"]
        else:
            color = COLORS["danger"]
        
        self.lbl_status.config(text=text, fg=color)
    
    def start(self):
        """Oynatmayı başlat"""
        if not self.midi_path:
            messagebox.showwarning("Eksik Bilgi", "Lütfen bir MIDI dosyası seçin.")
            return
        
        if not self.combo_port.get():
            messagebox.showwarning("Eksik Bilgi", "Lütfen bir seri port seçin.")
            return
        
        if not self.buzzer.is_connected:
            ok, msg = self.buzzer.connect(self.combo_port.get())
            if not ok:
                messagebox.showerror("Bağlantı Hatası", msg)
                return
        
        self.btn_play.config(state="disabled", bg="#3a3a3a")
        self.btn_stop.config(state="normal", bg=COLORS["danger"])
        
        # Seçilen moda göre player seç
        player_class = SoloPlayer if self.mode.get() == "solo" else ChiptunePlayer
        
        print(f"Seçilen Mod: {self.mode.get()}")
        print(f"Player Sınıfı: {player_class.__name__}")
        
        self.current_thread = player_class(
            self.midi_path,
            self.buzzer,
            self.update_ui_status,
            self.get_settings
        )
        self.current_thread.start()
        self.root.after(100, self.check_thread)
    
    def stop(self):
        """Oynatmayı durdur"""
        if self.current_thread:
            self.current_thread.stop()
        
        self.buzzer.stop()
        self.btn_play.config(state="normal", bg=COLORS["success"])
        self.btn_stop.config(state="disabled", bg="#3a3a3a")
        self.update_ui_status("STOPPED", False)
    
    def check_thread(self):
        """Thread kontrolü"""
        if self.current_thread and self.current_thread.is_alive():
            self.root.after(100, self.check_thread)
        else:
            self.stop()

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiPlayerApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop(), root.destroy()))
    root.mainloop()
