import customtkinter as ctk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from obspy import read
import numpy as np
import sys

from src.processing.sfk_transform import sfk_transform

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MaswApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MASW Processor Pro 2026")
        self.geometry("1300x900")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Состояние данных ---
        self.stream = None
        self.full_data = None  # Оригинальные данные
        self.view_data = None  # Обрезанные данные для расчетов
        
        # --- Layout ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar
        self.sidebar = ctk.CTkScrollableFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="УПРАВЛЕНИЕ", font=("Arial", 16, "bold")).pack(pady=10)

        self.load_btn = ctk.CTkButton(self.sidebar, text="Открыть файл", command=self.load_file)
        self.load_btn.pack(pady=10, padx=20, fill="x")

        # --- Блок границ (Time/Dist) ---
        ctk.CTkLabel(self.sidebar, text="Границы (Time min/max, с):").pack(padx=20, anchor="w")
        self.t_min_ent = ctk.CTkEntry(self.sidebar, placeholder_text="0.0")
        self.t_min_ent.pack(padx=20, pady=2, fill="x")
        self.t_max_ent = ctk.CTkEntry(self.sidebar, placeholder_text="1.0")
        self.t_max_ent.pack(padx=20, pady=2, fill="x")

        ctk.CTkLabel(self.sidebar, text="Границы (Dist min/max, м):").pack(padx=20, anchor="w", pady=(10,0))
        self.d_min_ent = ctk.CTkEntry(self.sidebar, placeholder_text="0.0")
        self.d_min_ent.pack(padx=20, pady=2, fill="x")
        self.d_max_ent = ctk.CTkEntry(self.sidebar, placeholder_text="100.0")
        self.d_max_ent.pack(padx=20, pady=2, fill="x")

                # --- Параметры записи (dt, dr) ---
        ctk.CTkLabel(self.sidebar, text="Параметры записи:").pack(padx=20, anchor="w", pady=(10,0))

        ctk.CTkLabel(self.sidebar, text="dt (мс):").pack(padx=20, anchor="w")
        self.entry_dt = ctk.CTkEntry(self.sidebar)
        self.entry_dt.pack(padx=20, pady=2, fill="x")
        self.entry_dt.insert(0, "1.0") # Значение по умолчанию

        ctk.CTkLabel(self.sidebar, text="dr (м):").pack(padx=20, anchor="w")
        self.entry_dr = ctk.CTkEntry(self.sidebar)
        self.entry_dr.pack(padx=20, pady=2, fill="x")
        self.entry_dr.insert(0, "2.0") # Значение по умолчанию

        # --- Усиление (Gain) ---
        ctk.CTkLabel(self.sidebar, text="Усиление (Gain):").pack(padx=20, anchor="w", pady=(10,0))
        self.gain_slider = ctk.CTkSlider(self.sidebar, from_=0.1, to=20.0, command=lambda x: self.plot_seismogram())
        self.gain_slider.set(1.0)
        self.gain_slider.pack(padx=20, pady=5, fill="x")

        # --- Тип отображения ---
        ctk.CTkLabel(self.sidebar, text="Тип отображения:").pack(padx=20, anchor="w", pady=(10,0))
        self.view_mode = ctk.StringVar(value="Wiggle")
        self.mode_menu = ctk.CTkOptionMenu(self.sidebar, values=["Wiggle", "Image (Grayscale)"], 
                                          variable=self.view_mode, command=lambda x: self.plot_seismogram())
        self.mode_menu.pack(padx=20, pady=5, fill="x")

        self.process_btn = ctk.CTkButton(self.sidebar, text="РАССЧИТАТЬ SFK", fg_color="green", command=self.run_processing)
        self.process_btn.pack(pady=30, padx=20, fill="x")

        # 2. Main Visualization
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.fig.patch.set_facecolor('#2b2b2b')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.main_frame)
        self.toolbar.update()

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Seismic", "*.segy *.su")])
        if not file_path: return

        try:
            self.stream = read(file_path)
            self.full_data = np.array([tr.data for tr in self.stream])
            
            # Авто-заполнение границ
            dt = self.stream[0].stats.delta
            n_samples = self.full_data.shape[1]
            n_traces = self.full_data.shape[0]
            dr = 1.0 # По умолчанию, если нет в заголовке
            # Авто-заполнение параметров записи
            dt_ms = self.stream[0].stats.delta * 1000
            self.entry_dt.delete(0, "end")
            self.entry_dt.insert(0, str(round(dt_ms, 4)))

            # dr обычно в SEGY не хранится в явном виде, 
            # но если ты знаешь его из проекта, можно оставить по умолчанию или вписать вручную
            
            self.t_min_ent.delete(0, "end"); self.t_min_ent.insert(0, "0.0")
            self.t_max_ent.delete(0, "end"); self.t_max_ent.insert(0, str(round((n_samples-1)*dt, 3)))
            self.d_min_ent.delete(0, "end"); self.d_min_ent.insert(0, "0.0")
            self.d_max_ent.delete(0, "end"); self.d_max_ent.insert(0, str(float((n_traces-1)*dr)))

            self.plot_seismogram()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка файла: {e}")

    def get_cropped_data(self):
        """Обрезает данные согласно значениям в полях ввода"""
        if self.full_data is None: return None, None, None

        dt = self.stream[0].stats.delta
        dr = 2.0 # Шаг приемников (можно вынести в Entry)
        
        t_start = float(self.t_min_ent.get())
        t_end = float(self.t_max_ent.get())
        d_start = float(self.d_min_ent.get())
        d_end = float(self.d_max_ent.get())

        # Индексы для обрезки
        it_start, it_end = int(t_start/dt), int(t_end/dt)
        id_start, id_end = int(d_start/dr), int(d_end/dr)

        cropped = self.full_data[id_start:id_end+1, it_start:it_end+1]
        t_axis = np.linspace(t_start, t_end, cropped.shape[1])
        d_axis = np.linspace(d_start, d_end, cropped.shape[0])
        
        return cropped, t_axis, d_axis

    def plot_seismogram(self):
        if self.full_data is None: return
        
        data, t_axis, d_axis = self.get_cropped_data()
        self.view_data = data # Сохраняем для SFK
        gain = self.gain_slider.get()
        
        self.ax.clear()
        
        if self.view_mode.get() == "Wiggle":
            # Отрисовка трассами
            norm = np.max(np.abs(data)) if np.max(np.abs(data)) != 0 else 1
            dr = d_axis[1] - d_axis[0] if len(d_axis) > 1 else 1
            
            for i in range(data.shape[0]):
                trace = (data[i, :] / norm) * dr * gain
                self.ax.plot(d_axis[i] + trace, t_axis, color='cyan', lw=0.5)
                self.ax.fill_betweenx(t_axis, d_axis[i], d_axis[i] + trace, where=(trace>0), color='cyan', alpha=0.3)
        else:
            # Отрисовка изображением (Grayscale)
            # vmin/vmax регулируются ползунком gain
            v_lim = np.max(np.abs(data)) / gain
            self.ax.imshow(data.T, aspect='auto', cmap='gray', 
                           extent=[d_axis[0], d_axis[-1], t_axis[-1], t_axis[0]],
                           vmin=-v_lim, vmax=v_lim)

        self.ax.set_xlabel("Расстояние (м)")
        self.ax.set_ylabel("Время (с)")
        self.ax.set_ylim(t_axis[-1], t_axis[0]) # Время вниз
        self.canvas.draw()

    def run_processing(self):
        if self.view_data is None: return
        
        # Получаем параметры из GUI
        dt = float(self.entry_dt.get()) / 1000.0
        dr = float(self.entry_dr.get())
        f_min = 10 # Можно добавить поля ввода
        f_max = 80
        
        # Запускаем расчет (может занять время, позже вынесем в поток)
        fk2d, vf2d, freq, k, v = sfk_transform(self.view_data, dt, dr, f_min, f_max)
        
        # Визуализируем результат (например, VF спектр)
        self.ax.clear()
        self.ax.imshow(vf2d, aspect='auto', extent=[freq[0], freq[-1], v[0], v[-1]], origin='lower')
        self.ax.set_title("V-F Spectrum (Dispersion Image)")
        self.ax.set_xlabel("Frequency (Hz)")
        self.ax.set_ylabel("Velocity (m/s)")
        self.canvas.draw()

    def on_closing(self):
        self.quit()
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = MaswApp()
    app.mainloop()