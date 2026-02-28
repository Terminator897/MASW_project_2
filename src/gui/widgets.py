import customtkinter as ctk

class Sidebar(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        ctk.CTkLabel(self, text="УПРАВЛЕНИЕ", font=("Arial", 16, "bold")).pack(pady=10)

        self.load_btn = ctk.CTkButton(self, text="Открыть файл")
        self.load_btn.pack(pady=10, padx=20, fill="x")

        # Границы
        self.create_label("Границы Time (min/max, с):")
        self.t_min = self.create_entry("0.0")
        self.t_max = self.create_entry("1.0")

        self.create_label("Границы Dist (min/max, м):")
        self.d_min = self.create_entry("0.0")
        self.d_max = self.create_entry("100.0")

        # Параметры записи
        self.create_label("Параметры записи:")
        self.dt_ent = self.create_entry("1.0", "dt (мс)")
        self.dr_ent = self.create_entry("2.0", "dr (м)")

        # Визуализация
        self.create_label("Усиление (Gain):")
        self.gain_slider = ctk.CTkSlider(self, from_=0.1, to=20.0)
        self.gain_slider.set(1.0)
        self.gain_slider.pack(padx=20, pady=5, fill="x")

        self.view_mode = ctk.CTkOptionMenu(self, values=["Wiggle", "Image (Grayscale)"])
        self.view_mode.pack(padx=20, pady=10, fill="x")

        self.process_btn = ctk.CTkButton(self, text="РАССЧИТАТЬ SFK", fg_color="green")
        self.process_btn.pack(pady=30, padx=20, fill="x")

    def create_label(self, text):
        lbl = ctk.CTkLabel(self, text=text, anchor="w")
        lbl.pack(padx=20, pady=(10, 0), fill="x")
        
    def create_entry(self, default, placeholder=""):
        ent = ctk.CTkEntry(self, placeholder_text=placeholder)
        ent.insert(0, default)
        ent.pack(padx=20, pady=2, fill="x")
        return ent