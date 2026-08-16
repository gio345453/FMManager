"""
Gestione tooltip per l'interfaccia grafica
"""
import tkinter as tk


class ToolTip:
    """Classe per creare tooltip temporanei"""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind('<Enter>', self.show_tooltip)
        self.widget.bind('<Leave>', self.hide_tooltip)

    def show_tooltip(self, event=None):
        """Mostra il tooltip"""
        if self.tooltip_window or not self.text:
            return

        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("Arial", 9, "normal"), padx=5, pady=2)
        label.pack()

    def hide_tooltip(self, event=None):
        """Nasconde il tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class TooltipWrapper:
    """Wrapper per gestire tooltip temporanei"""

    def __init__(self, window):
        self.window = window

    def hide_tooltip(self):
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
            self.window = None


def create_tooltip_at(parent, x, y, text):
    """Crea un tooltip a coordinate specifiche"""
    tooltip_window = tk.Toplevel(parent)
    tooltip_window.wm_overrideredirect(True)
    tooltip_window.wm_geometry(f"+{x + 10}+{y + 10}")

    label = tk.Label(tooltip_window, text=text, justify=tk.LEFT,
                    background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                    font=("Arial", 9, "normal"), padx=5, pady=2)
    label.pack()

    return TooltipWrapper(tooltip_window)
