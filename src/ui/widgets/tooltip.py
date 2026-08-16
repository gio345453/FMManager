"""
Widget per tooltip su hover
"""
import tkinter as tk


class ToolTip:
    """Classe per creare tooltip temporanei su widget"""

    def __init__(self, widget, text):
        """
        Args:
            widget: Widget Tkinter su cui mostrare il tooltip
            text: Testo da mostrare nel tooltip
        """
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
