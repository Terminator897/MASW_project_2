import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import customtkinter as ctk

class SeismicCanvas:
    def __init__(self, master):
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#1e1e1e')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.toolbar = NavigationToolbar2Tk(self.canvas, master)
        self.toolbar.pack(side=ctk.BOTTOM, fill=ctk.X)
        self.widget = self.canvas.get_tk_widget()
        self.widget.pack(fill="both", expand=True)

    def clear(self):
        self.ax.clear()
        self.ax.set_facecolor('#1e1e1e')

    def draw(self):
        self.canvas.draw()