import customtkinter as ctk
from tkinter import filedialog, messagebox
import numpy as np
import sys

from .widgets import Sidebar
from .canvas import SeismicCanvas
from ..io import load_seismic_file
from ..processing.sfk_transform import sfk_transform

class MaswApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MASW Processor Pro (Modular)")
        self.geometry("1400x900")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Состояние
        self.full_data = None
        self.stream = None

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Компоненты
        self.sidebar = Sidebar(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Настройка вкладок
        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.tab_seis = self.tabs.add("Сейсмограмма")
        self.tab_disp = self.tabs.add("Дисперсия (V-F)")
        self.tab_fk = self.tabs.add("F-K Спектр")
        
        
        self.canvas_seis = SeismicCanvas(self.tab_seis)
        self.canvas_disp = SeismicCanvas(self.tab_disp)
        self.canvas_fk = SeismicCanvas(self.tab_fk)

        # Привязка событий к кнопкам из Sidebar
        self.sidebar.load_btn.configure(command=self.on_load)
        self.sidebar.process_btn.configure(command=self.on_process)
        self.sidebar.gain_slider.configure(command=lambda x: self.draw_seismogram())
        self.sidebar.view_mode.configure(command=lambda x: self.draw_seismogram())

    def on_load(self):
        path = filedialog.askopenfilename(
            filetypes=[("Seismic Data", "*.segy *.sgy *.su"), ("All files", "*.*")]
        )
        if path:
            try:
                # Получаем расширенный набор данных
                self.stream, self.full_data, dt, dr, x0 = load_seismic_file(path)
                
                # Авто-заполнение полей в Sidebar
                self.sidebar.dt_ent.delete(0, "end")
                self.sidebar.dt_ent.insert(0, str(round(dt * 1000, 4)))
                
                self.sidebar.dr_ent.delete(0, "end")
                self.sidebar.dr_ent.insert(0, str(dr))
                
                self.sidebar.x0_ent.delete(0, "end")
                self.sidebar.x0_ent.insert(0, str(x0))
                
                # Сброс границ обрезки по умолчанию под новый файл
                self.sidebar.t_max.delete(0, "end")
                self.sidebar.t_max.insert(0, str(round(self.full_data.shape[1] * dt, 2)))
                
                self.draw_seismogram()
                messagebox.showinfo("Готово", f"Файл загружен.\nШаг dr: {dr}м\nСмещение x0: {x0}м")
                
            except Exception as e:
                messagebox.showerror("Ошибка чтения", f"Не удалось открыть файл: {e}")

    def draw_seismogram(self):
        if self.full_data is None:
            return

        # 1. Получаем обрезанные данные и оси
        data, t_axis, d_axis = self.get_cropped_data()
        self.view_data = data  # Сохраняем для расчета SFK
        
        gain = self.sidebar.gain_slider.get()
        mode = self.sidebar.view_mode.get()

        # 2. Очищаем холст
        self.canvas_seis.clear()
        ax = self.canvas_seis.ax

        if mode == "Wiggle":
            # Нормировка
            norm = np.max(np.abs(data)) if np.max(np.abs(data)) != 0 else 1
            # Шаг между трассами для масштаба
            dr = d_axis[1] - d_axis[0] if len(d_axis) > 1 else 1
            
            for i in range(data.shape[0]):
                # Масштабируем амплитуду
                trace = (data[i, :] / norm) * dr * gain
                ax.plot(d_axis[i] + trace, t_axis, color='cyan', lw=0.5)
                ax.fill_betweenx(t_axis, d_axis[i], d_axis[i] + trace, 
                                 where=(trace > 0), color='cyan', alpha=0.3)
        else:
            # Режим Grayscale (Image)
            v_lim = np.max(np.abs(data)) / gain if np.max(np.abs(data)) != 0 else 1
            ax.imshow(data.T, aspect='auto', cmap='gray', 
                      extent=[d_axis[0], d_axis[-1], t_axis[-1], t_axis[0]],
                      vmin=-v_lim, vmax=v_lim)

        # 3. Настройка осей
        ax.set_xlabel("Расстояние (м)")
        ax.set_ylabel("Время (с)")
        ax.set_ylim(t_axis[-1], t_axis[0])  # Время вниз
        
        # 4. Обновляем UI
        self.canvas_seis.draw()

    def get_cropped_data(self):
        dt = self.stream[0].stats.delta
        # Шаг dr берем из интерфейса
        try:
            dr = float(self.sidebar.dr_ent.get())
        except:
            dr = 2.0
        
        # Читаем границы из GUI
        x0 = float(self.sidebar.x0_ent.get())
        t_start = float(self.sidebar.t_min.get())
        t_end = float(self.sidebar.t_max.get())
        d_start = float(self.sidebar.d_min.get())
        d_end = float(self.sidebar.d_max.get())

        # Пересчитываем в индексы
        it_start, it_end = int(t_start/dt), int(t_end/dt)
        id_start, id_end = int(d_start/dr), int(d_end/dr)

        # Обрезаем матрицу
        cropped = self.full_data[id_start:id_end+1, it_start:it_end+1]
        t_axis = np.linspace(t_start, t_end, cropped.shape[1])
        d_axis = np.linspace(x0 + d_start, x0 + d_end, cropped.shape[0])
        return cropped, t_axis, d_axis

    def on_process(self):
        if self.full_data is None: return
        try:
            # Считываем ВСЕ параметры из GUI
            dt = float(self.sidebar.dt_ent.get()) / 1000.0
            dr = float(self.sidebar.dr_ent.get())
            v_min = float(self.sidebar.v_min.get())
            v_max = float(self.sidebar.v_max.get())
            f_min = float(self.sidebar.f_min.get())
            f_max = float(self.sidebar.f_max.get())
            m_nt = int(self.sidebar.multi_nt.get())
            m_nr = int(self.sidebar.multi_nr.get())
            s_w = float(self.sidebar.s_width.get())
            
            data, _, _ = self.get_cropped_data()
            
            # Запуск с полным набором параметров
            fk2d, vf2d, freq, k_axis, v_axis = sfk_transform(
                data, dt, dr, f_min, f_max, v_min, v_max, m_nt, m_nr, s_w
            )

            self.update_plots(fk2d, vf2d, freq, k_axis, v_axis)
            self.tabs.set("Дисперсия (V-F)")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Проверьте параметры: {e}")

    def update_plots(self, fk2d, vf2d, freq, k_axis, v_axis):
        cmap = self.sidebar.cmap_menu.get()
        do_norm = self.sidebar.norm_check.get()
        show_grid = self.sidebar.grid_check.get()
        
        # Получаем dr из интерфейса для расчета алиасинга
        dr = float(self.sidebar.dr_ent.get())

        # --- Отрисовка V-F ---
        self.canvas_disp.clear()
        ax_vf = self.canvas_disp.ax
        img_vf = vf2d / np.max(vf2d, axis=0) if do_norm else vf2d
        ax_vf.imshow(img_vf, aspect='auto', origin='lower', cmap=cmap,
                      extent=[freq[0], freq[-1], v_axis[0], v_axis[-1]])
        
        
        if show_grid: ax_vf.grid(True, alpha=0.3)
        self.canvas_disp.draw()

        # --- Отрисовка F-K ---
        self.canvas_fk.clear()
        ax_fk = self.canvas_fk.ax
        fk_data = fk2d.T
        if do_norm: fk_data = fk_data / np.max(fk_data, axis=0)
        
        ax_fk.imshow(fk_data, aspect='auto', origin='lower', cmap=cmap,
                      extent=[freq[0], freq[-1], k_axis[0], k_axis[-1]])

        
        if show_grid: ax_fk.grid(True, alpha=0.3)
        self.canvas_fk.draw()

    def on_closing(self):
        self.quit()
        self.destroy()
        sys.exit()