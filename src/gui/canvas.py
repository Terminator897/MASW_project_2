import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import customtkinter as ctk

class SeismicCanvas:
    def __init__(self, master):
        # Создаем фигуру с темным фоном под стиль CustomTkinter
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#1e1e1e')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.widget = self.canvas.get_tk_widget()
        self.widget.pack(fill="both", expand=True)
        
        # Индивидуальный тулбар (лупа, сохранение и т.д.)
        self.toolbar = NavigationToolbar2Tk(self.canvas, master)
        self.toolbar.configure(background='#2b2b2b')
        self.toolbar.update()

    def clear(self):
        self.ax.clear()
        self.ax.set_facecolor('#1e1e1e')

    def draw(self):
        self.canvas.draw()