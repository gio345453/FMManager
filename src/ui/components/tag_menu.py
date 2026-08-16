"""
Componente TagMenu - Menu rapido per gestione tag giocatori
"""
import customtkinter as ctk
import tkinter as tk
from .constants import COLORS


class TagMenu:
    """Menu popup per aggiunta/rimozione rapida tag"""

    def __init__(self, root, notes_manager, on_tag_toggle, on_open_details):
        """
        Inizializza menu tag

        Args:
            root: Finestra principale
            notes_manager: Istanza di PlayerNotesManager
            on_tag_toggle: Callback chiamata quando un tag viene aggiunto/rimosso
            on_open_details: Callback per aprire dettagli completi giocatore
        """
        self.root = root
        self.notes_manager = notes_manager
        self.on_tag_toggle_callback = on_tag_toggle
        self.on_open_details_callback = on_open_details

        # Tag predefiniti
        self.common_tags = ["obiettivo", "da evitare", "esca", "riserva", "titolare", "occasione", "rigorista", "tiratore piazzati"]

    def show(self, player_id, player_name, item, event):
        """
        Mostra menu rapido tag per un giocatore

        Args:
            player_id: ID del giocatore
            player_name: Nome del giocatore
            item: Item del treeview
            event: Evento click
        """
        current_tags = self.notes_manager.get_tags(player_id)

        # Crea finestra popup moderna
        popup = tk.Toplevel(self.root)
        popup.wm_overrideredirect(True)
        popup.attributes('-topmost', True)

        # Frame principale con stile moderno
        main_frame = ctk.CTkFrame(
            popup,
            fg_color=COLORS['bg_secondary'],
            border_width=2,
            border_color=COLORS['accent_purple'],
            corner_radius=0
        )
        main_frame.pack(fill="both", expand=True)

        # Header con nome giocatore
        header = ctk.CTkFrame(main_frame, fg_color=COLORS['bg_primary'], corner_radius=0)
        header.pack(fill="x", pady=0)

        ctk.CTkLabel(
            header,
            text=f"🏷️ {player_name}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS['accent_purple']
        ).pack(pady=10, padx=15)

        # Separatore
        separator = ctk.CTkFrame(main_frame, height=1, fg_color=COLORS['bg_tertiary'])
        separator.pack(fill="x", padx=10, pady=5)

        # Tag comuni (2 colonne)
        tags_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        tags_container.pack(fill="x", padx=10, pady=10)

        for i, tag in enumerate(self.common_tags):
            is_active = tag in current_tags

            # Frame per ogni riga (2 tag per riga)
            if i % 2 == 0:
                tag_row = ctk.CTkFrame(tags_container, fg_color="transparent")
                tag_row.pack(fill="x", pady=2)

            tag_btn_frame = ctk.CTkFrame(tag_row, fg_color="transparent")
            tag_btn_frame.pack(side="left", fill="x", expand=True, padx=(0, 5 if i % 2 == 0 else 0))

            tag_btn = ctk.CTkButton(
                tag_btn_frame,
                text=tag,
                command=lambda t=tag, pid=player_id, p=popup: self._toggle_tag(pid, t, p),
                font=ctk.CTkFont(size=12),
                fg_color=COLORS['accent_purple'] if is_active else COLORS['bg_tertiary'],
                hover_color=COLORS['accent_blue'],
                corner_radius=0,
                height=32,
                anchor="w"
            )
            tag_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Separatore
        separator2 = ctk.CTkFrame(main_frame, height=1, fg_color=COLORS['bg_tertiary'])
        separator2.pack(fill="x", padx=10, pady=5)

        # Bottone modifica completa
        edit_btn = ctk.CTkButton(
            main_frame,
            text="✏️ Modifica completa",
            command=lambda: self._open_details(item, popup),
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS['accent_blue'],
            hover_color=COLORS['accent_purple'],
            corner_radius=0,
            height=35
        )
        edit_btn.pack(pady=(5, 10), padx=10, fill="x")

        # Aggiorna per ottenere dimensioni reali
        popup.update_idletasks()

        # Ottieni dimensioni popup
        popup_width = popup.winfo_reqwidth()
        popup_height = popup.winfo_reqheight()

        # Ottieni dimensioni schermo
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()

        # Calcola posizione con offset dal cursore
        x = event.x_root + 10
        y = event.y_root + 10

        # Aggiusta se va fuori dallo schermo a destra
        if x + popup_width > screen_width:
            x = event.x_root - popup_width - 10

        # Aggiusta se va fuori dallo schermo in basso
        if y + popup_height > screen_height:
            y = event.y_root - popup_height - 10

        # Assicurati che non vada fuori a sinistra o in alto
        x = max(10, x)
        y = max(10, y)

        # Posiziona il popup
        popup.geometry(f"+{x}+{y}")

        # Chiudi solo con Escape (non FocusOut che interferisce con i click sui pulsanti)
        def close_popup(event=None):
            try:
                popup.destroy()
            except:
                pass

        popup.bind('<Escape>', close_popup)

        # Focus per ricevere eventi
        popup.focus_set()

    def _toggle_tag(self, player_id, tag, popup):
        """
        Toggle tag (aggiunge se non presente, rimuove se presente)

        Args:
            player_id: ID del giocatore
            tag: Tag da aggiungere/rimuovere
            popup: Finestra popup da chiudere
        """
        current_tags = self.notes_manager.get_tags(player_id)

        if tag in current_tags:
            self.notes_manager.remove_tag(player_id, tag)
        else:
            self.notes_manager.add_tag(player_id, tag)

        # Chiudi popup
        try:
            popup.destroy()
        except:
            pass

        # Notifica cambio tag
        self.on_tag_toggle_callback()

    def _open_details(self, item, popup):
        """
        Apre finestra dettagli giocatore

        Args:
            item: Item del treeview
            popup: Finestra popup da chiudere
        """
        try:
            popup.destroy()
        except:
            pass

        self.on_open_details_callback(item)
