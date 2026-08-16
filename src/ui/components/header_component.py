"""
Componente Header - Titolo e informazioni principali
"""
import customtkinter as ctk
from .constants import COLORS


class HeaderComponent:
    """Componente header con titolo e logo"""

    def __init__(self, parent):
        """
        Inizializza header component

        Args:
            parent: Frame genitore dove inserire l'header
        """
        self.parent = parent
        self.header_frame = None

    def create(self):
        """Crea e mostra l'header"""
        # Titolo principale
        self.header_frame = ctk.CTkLabel(
            self.parent,
            text="⚽ FANTACALCIO MANAGER",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS['accent_purple']
        )
        self.header_frame.pack(pady=(0, 20))

        return self.header_frame

    def update_title(self, new_title):
        """
        Aggiorna il titolo dell'header

        Args:
            new_title: Nuovo testo del titolo
        """
        if self.header_frame:
            self.header_frame.configure(text=new_title)

    def destroy(self):
        """Rimuove l'header"""
        if self.header_frame:
            self.header_frame.destroy()
            self.header_frame = None
