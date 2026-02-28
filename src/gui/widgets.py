import customtkinter as ctk

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        ctk.CTkLabel(self, text="MASW CONTROL", font=("Arial", 16, "bold")).pack(pady=10)

        # Создаем вкладки внутри сайдбара
        self.tabs = ctk.CTkTabview(self, height=700)
        self.tabs.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.tab_data = self.tabs.add("Данные")
        self.tab_proc = self.tabs.add("Расчет")
        self.tab_view = self.tabs.add("Вид")

        # --- Вкладка "Данные" ---
        self.load_btn = ctk.CTkButton(self.tab_data, text="Открыть файл")
        self.load_btn.pack(pady=10, padx=10, fill="x")

        self.create_label(self.tab_data, "Окно анализа (T, с):")
        self.t_min = self.create_entry(self.tab_data, "0.0")
        self.t_max = self.create_entry(self.tab_data, "1.0")

        self.create_label(self.tab_data, "Окно анализа (X, м):")
        self.d_min = self.create_entry(self.tab_data, "0.0")
        self.d_max = self.create_entry(self.tab_data, "100.0")

        # --- Вкладка "Расчет" ---
        self.create_label(self.tab_proc, "Шаги (dt мс / dr м):")
        self.dt_ent = self.create_entry(self.tab_proc, "1.0")
        self.dr_ent = self.create_entry(self.tab_proc, "2.0")

        self.create_label(self.tab_proc, "Частоты (Fmin/Fmax Гц):")
        self.f_min = self.create_entry(self.tab_proc, "5.0")
        self.f_max = self.create_entry(self.tab_proc, "80.0")

        self.create_label(self.tab_proc, "Макс. Скорость (м/с):")
        self.v_max = self.create_entry(self.tab_proc, "500.0")

        self.process_btn = ctk.CTkButton(self.tab_proc, text="РАССЧИТАТЬ", fg_color="#28a745", hover_color="#218838")
        self.process_btn.pack(pady=20, padx=10, fill="x")

        # --- Вкладка "Вид" ---
        self.create_label(self.tab_view, "Усиление (Gain):")
        self.gain_slider = ctk.CTkSlider(self.tab_view, from_=0.1, to=10.0)
        self.gain_slider.set(1.0)
        self.gain_slider.pack(padx=10, pady=5, fill="x")

        self.norm_check = ctk.CTkCheckBox(self.tab_view, text="Нормировка спектров")
        self.norm_check.select() # по умолчанию включена
        self.norm_check.pack(padx=10, pady=10, anchor="w")

        self.view_mode = ctk.CTkOptionMenu(self.tab_view, values=["Wiggle", "Image"])
        self.view_mode.pack(padx=10, pady=10, fill="x")

    def create_label(self, master, text):
        lbl = ctk.CTkLabel(master, text=text, anchor="w", font=("Arial", 12, "bold"))
        lbl.pack(padx=10, pady=(10, 0), fill="x")
        
    def create_entry(self, master, default):
        ent = ctk.CTkEntry(master)
        ent.insert(0, default)
        ent.pack(padx=10, pady=2, fill="x")
        return ent
    