"""
Componente FooterActions - Pulsanti azioni e status bar
"""
import customtkinter as ctk
from .constants import COLORS


class FooterActions:
    """Componente footer con pulsanti azioni principali e status bar"""

    def __init__(self, parent, on_comparison, on_dashboard, on_build_rosa=None, on_auto_tags=None):
        """
        Inizializza footer actions

        Args:
            parent: Frame genitore
            on_comparison: Callback per aprire confronto giocatori
            on_dashboard: Callback per aprire dashboard squadre
            on_build_rosa: Callback per aprire build rosa (opzionale)
            on_auto_tags: Callback per assegnare tag automatici (opzionale)
        """
        self.parent = parent
        self.on_comparison_callback = on_comparison
        self.on_dashboard_callback = on_dashboard
        self.on_build_rosa_callback = on_build_rosa
        self.on_auto_tags_callback = on_auto_tags

        # Widget
        self.actions_frame = None
        self.status_label = None

    def create(self):
        """Crea e mostra i pulsanti azioni e status bar"""
        # Frame azioni
        self.actions_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.actions_frame.pack(fill="x", pady=(15, 10))

        # Pulsante confronto giocatori
        comparison_btn = ctk.CTkButton(
            self.actions_frame,
            text="⚖️ Confronta Giocatori",
            command=self.on_comparison_callback,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['accent_blue'],
            hover_color=COLORS['accent_purple'],
            corner_radius=10
        )
        comparison_btn.pack(side="left", padx=(0, 10), fill="x", expand=True)

        # Pulsante build rosa (se callback disponibile)
        if self.on_build_rosa_callback:
            build_rosa_btn = ctk.CTkButton(
                self.actions_frame,
                text="🏗️ Build Rosa",
                command=self.on_build_rosa_callback,
                height=45,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=COLORS['accent_purple'],
                hover_color=COLORS['accent_pink'],
                corner_radius=10
            )
            build_rosa_btn.pack(side="left", padx=(0, 10), fill="x", expand=True)

        # Pulsante dashboard squadre
        dashboard_btn = ctk.CTkButton(
            self.actions_frame,
            text="📊 Dashboard Squadre",
            command=self.on_dashboard_callback,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['accent_green'],
            hover_color=COLORS['success'],
            corner_radius=10
        )
        dashboard_btn.pack(side="left", padx=(0, 10), fill="x", expand=True)

        # Pulsante tag automatici (se callback disponibile)
        if self.on_auto_tags_callback:
            auto_tags_btn = ctk.CTkButton(
                self.actions_frame,
                text="🏷️ Assegna Tag Automatici",
                command=self.on_auto_tags_callback,
                height=45,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=COLORS['accent_purple'],
                hover_color=COLORS['accent_blue'],
                corner_radius=10
            )
            auto_tags_btn.pack(side="left", fill="x", expand=True)

        return self.actions_frame

    def create_status_bar(self):
        """Crea e mostra la status bar"""
        # Status bar
        status_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        status_frame.pack(fill="x", pady=(10, 0))

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="⏳ Caricamento dati...",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        )
        self.status_label.pack()

        return status_frame

    def update_status(self, message, color=None):
        """
        Aggiorna il messaggio della status bar

        Args:
            message: Nuovo messaggio da visualizzare
            color: Colore del testo (opzionale)
        """
        if self.status_label:
            self.status_label.configure(text=message)
            if color:
                self.status_label.configure(text_color=color)

    def set_loading(self):
        """Imposta status come caricamento"""
        self.update_status("⏳ Caricamento dati...", COLORS['text_secondary'])

    def set_success(self, message="✓ Dati caricati correttamente"):
        """Imposta status come successo"""
        self.update_status(message, COLORS['success'])

    def set_error(self, message="✗ Errore nel caricamento"):
        """Imposta status come errore"""
        self.update_status(message, COLORS['error'])

    def destroy(self):
        """Rimuove il footer"""
        if self.actions_frame:
            self.actions_frame.destroy()
            self.actions_frame = None
        if self.status_label and self.status_label.master:
            self.status_label.master.destroy()
            self.status_label = None
