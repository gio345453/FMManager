"""
Finestra Confronto Giocatori - Design ultra-moderno con 3 slot e popup risultati
"""
import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
import numpy as np
from src.config import STATS_FILES, ROLE_WEIGHTS
from src.data.cache import DataCache
from src.data.favorites_manager import FavoritesManager
from src.data.player_notes import PlayerNotesManager
from src.data.titolarita_loader import get_status
from src.logic.player_comparison_logic import PlayerComparisonLogic
from src.ui.chart_styles import create_comparison_figure, create_advanced_comparison_figure, embed_figure_in_tkinter
from src.ui.window_chrome import configure_application_window
from src.utils.data_utils import extract_base_role


# Palette colori moderna
COLORS = {
    'bg_primary': '#0F0F1E',
    'bg_secondary': '#1E1E2E',
    'bg_tertiary': '#2B2D42',
    'accent_blue': '#3A86FF',
    'accent_purple': '#8338EC',
    'accent_pink': '#FF006E',
    'accent_green': '#06D6A0',
    'accent_yellow': '#FFD60A',
    'spotify_green': '#1DB954',  # Verde Spotify
    'spotify_green_hover': '#1ED760',  # Verde Spotify hover
    'text_primary': '#FFFFFF',
    'text_secondary': '#A0A0B0',
    'border': '#3A3A4A',
    'hover': '#363646',
    'success': '#06D6A0',
    'warning': '#FFB703',
    'error': '#EF476F'
}


class PlayerComparisonWindow:
    """Finestra confronto giocatori con design moderno a 3 slot puliti"""

    def __init__(self, parent, budget=500, preloaded_data=None):
        self.cache = DataCache()
        self.favorites_manager = FavoritesManager()
        self.budget = budget
        self.player_slots = [None, None, None]  # 3 slot per giocatori
        self.search_vars = []
        self.search_entries = []
        self.preview_frames = []
        self.listboxes = []
        self.role_filters = []
        self.team_filters = []
        self.favorites_filters = []  # Nuovi filtri preferiti
        self.all_players = None  # Inizializza subito

        # Usa dati precaricati se disponibili
        self.preloaded_data = preloaded_data

        # Finestra principale - Centrata 1200x650
        self.window = ctk.CTkToplevel(parent)
        configure_application_window(self.window)
        self.window.title("⚡ Confronto Giocatori")
        self.window.configure(fg_color=COLORS['bg_primary'])

        # Nascondi la finestra durante il setup per evitare rendering progressivo
        self.window.withdraw()

        # Apri sopra la finestra principale
        self.window.transient(parent)

        # Responsive grid principale
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

        self._setup_ui()

        # Carica dati in background dopo aver mostrato la UI
        self.window.after(10, self._load_all_players_deferred)

        # Mostra la finestra centrata dopo che tutto è pronto
        self.window.after(10, self._show_centered)

    def _show_centered(self):
        """Mostra la finestra centrata con dimensioni 1200x650"""
        # Imposta dimensioni
        window_width = 1200
        window_height = 650

        # Ottieni dimensioni schermo
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        # Calcola posizione centrata
        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)

        # Imposta geometria e mostra
        self.window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
        self.window.grab_set()

    def _setup_ui(self):
        """Setup interfaccia pulita e perfettamente disposta a 3 colonne"""
        # Main container con padding ridotto per dare spazio al bottone
        main_container = ctk.CTkFrame(self.window, fg_color=COLORS['bg_primary'])
        main_container.grid(row=0, column=0, sticky="nsew", padx=15, pady=10)

        # Configurazione grid
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=0)
        main_container.grid_columnconfigure(0, weight=1)

        # Frame per le 3 card
        slots_container = ctk.CTkFrame(main_container, fg_color="transparent")
        slots_container.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        slots_container.grid_rowconfigure(0, weight=1)
        # Larghezza fissa per ogni colonna con uniform per mantenere dimensioni identiche
        slots_container.grid_columnconfigure(0, weight=1, minsize=360, uniform="slot")
        slots_container.grid_columnconfigure(1, weight=1, minsize=360, uniform="slot")
        slots_container.grid_columnconfigure(2, weight=1, minsize=360, uniform="slot")

        # Crea i 3 slot
        slot_titles = ["🎯 Giocatore 1", "🎯 Giocatore 2", "💡 Giocatori Consigliati"]
        for i in range(3):
            self._create_player_slot(slots_container, i, slot_titles[i])

        # Bottone confronta ancorato in basso con spessore ottimizzato
        self.compare_btn = ctk.CTkButton(
            main_container,
            text="⚡ AVVIA CONFRONTO",
            command=self._launch_comparison,
            height=42,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=COLORS['spotify_green'],
            hover_color=COLORS['spotify_green_hover'],
            corner_radius=10
        )
        self.compare_btn.grid(row=1, column=0, sticky="ew", padx=120, pady=(0, 5))
    def _create_player_slot(self, parent, slot_index, title):
        """Crea una card slot pulita e compatta per selezionare un giocatore"""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS['bg_secondary'],
            corner_radius=12,
            border_width=2,
            border_color=COLORS['border']
        )
        card.grid(row=0, column=slot_index, sticky="nsew", padx=6, pady=2)

        # uniform="card_content" garantisce la stessa altezza verticale costante in tutti gli slot
        card.grid_rowconfigure(0, weight=0)  # Header
        card.grid_rowconfigure(1, weight=1, uniform="card_content")  # Content fissa
        card.grid_columnconfigure(0, weight=1)

        # Header Card (più compatto)
        header = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS['text_primary']
        )
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))

        # Loading indicator placeholder (verrà mostrato solo durante il caricamento)
        loading_frame = ctk.CTkFrame(card, fg_color="transparent")
        loading_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=20)

        loading_label = ctk.CTkLabel(
            loading_frame,
            text="⏳ Caricamento giocatori...",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_secondary']
        )
        loading_label.pack(expand=True)

        # Salva riferimento per nasconderlo dopo
        if not hasattr(self, 'loading_frames'):
            self.loading_frames = []
        self.loading_frames.append(loading_frame)

        # SEARCH CONTROLS CONTAINER
        search_controls = ctk.CTkFrame(card, fg_color="transparent")
        search_controls.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))

        search_controls.grid_rowconfigure(0, weight=0)  # Search field
        search_controls.grid_rowconfigure(1, weight=0)  # Filters
        search_controls.grid_rowconfigure(2, weight=1)  # Listbox
        search_controls.grid_columnconfigure(0, weight=1)

        if not hasattr(self, 'search_controls'):
            self.search_controls = []
        self.search_controls.append(search_controls)

        # Search entry
        search_var = tk.StringVar()
        search_var.trace('w', lambda *args: self._filter_players_list(slot_index))
        self.search_vars.append(search_var)

        search_entry = ctk.CTkEntry(
            search_controls,
            textvariable=search_var,
            placeholder_text="🔍 Cerca per nome...",
            placeholder_text_color=COLORS['text_secondary'],
            text_color=COLORS['text_primary'],
            height=32,
            font=ctk.CTkFont(size=12),
            border_width=1,
            border_color=COLORS['border'],
            fg_color=COLORS['bg_tertiary'],
            corner_radius=6
        )
        search_entry.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.search_entries.append(search_entry)

        # Frame Filtri
        filters_frame = ctk.CTkFrame(search_controls, fg_color="transparent")
        filters_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        filters_frame.grid_columnconfigure(0, weight=1)
        filters_frame.grid_columnconfigure(1, weight=1)

        # Filtro Ruolo
        role_var = tk.StringVar(value="Ruoli")
        role_menu = ctk.CTkOptionMenu(
            filters_frame,
            variable=role_var,
            values=["Ruoli", "P", "D", "C", "A"],
            command=lambda _: self._filter_players_list(slot_index),
            height=28,
            fg_color=COLORS['bg_tertiary'],
            button_color=COLORS['accent_blue'],
            button_hover_color=COLORS['accent_purple'],
            corner_radius=6,
            font=ctk.CTkFont(size=11)
        )
        role_menu.grid(row=0, column=0, sticky="ew", padx=(0, 2), pady=(0, 4))
        self.role_filters.append(role_var)

        # Filtro Squadra
        team_var = tk.StringVar(value="Squadre")
        team_menu = ctk.CTkOptionMenu(
            filters_frame,
            variable=team_var,
            values=["Squadre"],
            command=lambda _: self._filter_players_list(slot_index),
            height=28,
            fg_color=COLORS['bg_tertiary'],
            button_color=COLORS['accent_blue'],
            button_hover_color=COLORS['accent_purple'],
            corner_radius=6,
            font=ctk.CTkFont(size=11)
        )
        team_menu.grid(row=0, column=1, sticky="ew", padx=(2, 0), pady=(0, 4))
        self.team_filters.append((team_var, team_menu))

        # Checkbox Preferiti
        favorites_var = tk.BooleanVar(value=False)
        favorites_check = ctk.CTkCheckBox(
            filters_frame,
            text="⭐ Solo Preferiti",
            variable=favorites_var,
            command=lambda: self._filter_players_list(slot_index),
            fg_color=COLORS['accent_yellow'],
            hover_color=COLORS['warning'],
            text_color=COLORS['text_primary'],
            checkbox_width=18,
            checkbox_height=18,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        favorites_check.grid(row=1, column=0, columnspan=2, sticky="w", padx=2, pady=(2, 0))
        self.favorites_filters.append(favorites_var)

        # Lista giocatori dinamica (Height impostato a 12 righe per contenere l'altezza)
        list_frame = ctk.CTkFrame(
            search_controls, 
            fg_color=COLORS['bg_tertiary'], 
            corner_radius=8,
            border_width=1,
            border_color=COLORS['border']
        )
        list_frame.grid(row=2, column=0, sticky="nsew", pady=(4, 0))

        scrollbar = ctk.CTkScrollbar(list_frame, orientation="vertical", width=12)
        scrollbar.pack(side="right", fill="y", padx=2, pady=2)

        listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            selectbackground=COLORS['accent_purple'],
            selectforeground=COLORS['text_primary'],
            font=("Segoe UI", 9),
            height=12,  # Evita l'espansione eccessiva in verticale
            borderwidth=0,
            highlightthickness=0,
            activestyle='none'
        )
        listbox.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        listbox.bind('<Double-Button-1>', lambda e, idx=slot_index: self._on_listbox_double_click(idx))
        scrollbar.configure(command=listbox.yview)
        self.listboxes.append(listbox)

        # PREVIEW CONTAINER (posizionato nella stessa cella della ricerca e inizialmente nascosto)
        preview_frame = ctk.CTkFrame(
            card,
            fg_color=COLORS['bg_tertiary'],
            corner_radius=10,
            border_width=2,
            border_color=COLORS['accent_green']
        )
        preview_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))
        preview_frame.grid_remove()  # Inizialmente nascosto
        self.preview_frames.append(preview_frame)
    # def _create_player_slot(self, parent, slot_index, title):
    #     """Crea una card slot pulita e compatta per selezionare un giocatore"""
    #     card = ctk.CTkFrame(
    #         parent,
    #         fg_color=COLORS['bg_secondary'],
    #         corner_radius=12,
    #         border_width=2,
    #         border_color=COLORS['border']
    #     )
    #     card.grid(row=0, column=slot_index, sticky="nsew", padx=6, pady=2)

    #     card.grid_rowconfigure(0, weight=0)  # Header
    #     card.grid_rowconfigure(1, weight=1)  # Content
    #     card.grid_columnconfigure(0, weight=1)

    #     # Header Card (più compatto)
    #     header = ctk.CTkLabel(
    #         card,
    #         text=title,
    #         font=ctk.CTkFont(size=15, weight="bold"),
    #         text_color=COLORS['text_primary']
    #     )
    #     header.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))

    #     # Loading indicator placeholder (verrà mostrato solo durante il caricamento)
    #     loading_frame = ctk.CTkFrame(card, fg_color="transparent")
    #     loading_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=20)

    #     loading_label = ctk.CTkLabel(
    #         loading_frame,
    #         text="⏳ Caricamento giocatori...",
    #         font=ctk.CTkFont(size=13),
    #         text_color=COLORS['text_secondary']
    #     )
    #     loading_label.pack(expand=True)

    #     # Salva riferimento per nasconderlo dopo
    #     if not hasattr(self, 'loading_frames'):
    #         self.loading_frames = []
    #     self.loading_frames.append(loading_frame)

    #     # SEARCH CONTROLS CONTAINER
    #     search_controls = ctk.CTkFrame(card, fg_color="transparent")
    #     search_controls.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))

    #     search_controls.grid_rowconfigure(0, weight=0)  # Search field
    #     search_controls.grid_rowconfigure(1, weight=0)  # Filters
    #     search_controls.grid_rowconfigure(2, weight=1)  # Listbox
    #     search_controls.grid_columnconfigure(0, weight=1)

    #     if not hasattr(self, 'search_controls'):
    #         self.search_controls = []
    #     self.search_controls.append(search_controls)

    #     # Search entry
    #     search_var = tk.StringVar()
    #     search_var.trace('w', lambda *args: self._filter_players_list(slot_index))
    #     self.search_vars.append(search_var)

    #     search_entry = ctk.CTkEntry(
    #         search_controls,
    #         textvariable=search_var,
    #         placeholder_text="🔍 Cerca per nome...",
    #         placeholder_text_color=COLORS['text_secondary'],
    #         text_color=COLORS['text_primary'],
    #         height=32,
    #         font=ctk.CTkFont(size=12),
    #         border_width=1,
    #         border_color=COLORS['border'],
    #         fg_color=COLORS['bg_tertiary'],
    #         corner_radius=6
    #     )
    #     search_entry.grid(row=0, column=0, sticky="ew", pady=(0, 6))
    #     self.search_entries.append(search_entry)

    #     # Frame Filtri
    #     filters_frame = ctk.CTkFrame(search_controls, fg_color="transparent")
    #     filters_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
    #     filters_frame.grid_columnconfigure(0, weight=1)
    #     filters_frame.grid_columnconfigure(1, weight=1)

    #     # Filtro Ruolo
    #     role_var = tk.StringVar(value="Ruoli")
    #     role_menu = ctk.CTkOptionMenu(
    #         filters_frame,
    #         variable=role_var,
    #         values=["Ruoli", "P", "D", "C", "A"],
    #         command=lambda _: self._filter_players_list(slot_index),
    #         height=28,
    #         fg_color=COLORS['bg_tertiary'],
    #         button_color=COLORS['accent_blue'],
    #         button_hover_color=COLORS['accent_purple'],
    #         corner_radius=6,
    #         font=ctk.CTkFont(size=11)
    #     )
    #     role_menu.grid(row=0, column=0, sticky="ew", padx=(0, 2), pady=(0, 4))
    #     self.role_filters.append(role_var)

    #     # Filtro Squadra
    #     team_var = tk.StringVar(value="Squadre")
    #     team_menu = ctk.CTkOptionMenu(
    #         filters_frame,
    #         variable=team_var,
    #         values=["Squadre"],
    #         command=lambda _: self._filter_players_list(slot_index),
    #         height=28,
    #         fg_color=COLORS['bg_tertiary'],
    #         button_color=COLORS['accent_blue'],
    #         button_hover_color=COLORS['accent_purple'],
    #         corner_radius=6,
    #         font=ctk.CTkFont(size=11)
    #     )
    #     team_menu.grid(row=0, column=1, sticky="ew", padx=(2, 0), pady=(0, 4))
    #     self.team_filters.append((team_var, team_menu))

    #     # Checkbox Preferiti
    #     favorites_var = tk.BooleanVar(value=False)
    #     favorites_check = ctk.CTkCheckBox(
    #         filters_frame,
    #         text="⭐ Solo Preferiti",
    #         variable=favorites_var,
    #         command=lambda: self._filter_players_list(slot_index),
    #         fg_color=COLORS['accent_yellow'],
    #         hover_color=COLORS['warning'],
    #         text_color=COLORS['text_primary'],
    #         checkbox_width=18,
    #         checkbox_height=18,
    #         font=ctk.CTkFont(size=11, weight="bold")
    #     )
    #     favorites_check.grid(row=1, column=0, columnspan=2, sticky="w", padx=2, pady=(2, 0))
    #     self.favorites_filters.append(favorites_var)

    #     # Lista giocatori dinamica (Height impostato a 12 righe per contenere l'altezza)
    #     list_frame = ctk.CTkFrame(
    #         search_controls, 
    #         fg_color=COLORS['bg_tertiary'], 
    #         corner_radius=8,
    #         border_width=1,
    #         border_color=COLORS['border']
    #     )
    #     list_frame.grid(row=2, column=0, sticky="nsew", pady=(4, 0))

    #     scrollbar = ctk.CTkScrollbar(list_frame, orientation="vertical", width=12)
    #     scrollbar.pack(side="right", fill="y", padx=2, pady=2)

    #     listbox = tk.Listbox(
    #         list_frame,
    #         yscrollcommand=scrollbar.set,
    #         bg=COLORS['bg_tertiary'],
    #         fg=COLORS['text_primary'],
    #         selectbackground=COLORS['accent_purple'],
    #         selectforeground=COLORS['text_primary'],
    #         font=("Segoe UI", 9),
    #         height=12,  # Evita l'espansione eccessiva in verticale
    #         borderwidth=0,
    #         highlightthickness=0,
    #         activestyle='none'
    #     )
    #     listbox.pack(side="left", fill="both", expand=True, padx=4, pady=4)
    #     listbox.bind('<Double-Button-1>', lambda e, idx=slot_index: self._on_listbox_double_click(idx))
    #     scrollbar.configure(command=listbox.yview)
    #     self.listboxes.append(listbox)

    #     # PREVIEW CONTAINER
    #     preview_frame = ctk.CTkFrame(
    #         card,
    #         fg_color=COLORS['bg_tertiary'],
    #         corner_radius=10,
    #         border_width=2,
    #         border_color=COLORS['accent_green']
    #     )
    #     self.preview_frames.append(preview_frame)

    def _load_all_players_deferred(self):
        """Carica tutti i giocatori in modo differito dopo la visualizzazione della UI"""
        # Se abbiamo dati precaricati, usali
        if self.preloaded_data is not None:
            self.all_players = self.preloaded_data
            self._populate_ui_with_data()
        else:
            # Altrimenti carica normalmente
            self._load_all_players()

    def _load_all_players(self):
        """Carica tutti i giocatori"""
        from src.data_processor import FantaCalcioDataProcessor
        from src.data.price_calculator import PriceCalculator

        processor = FantaCalcioDataProcessor()
        price_calculator = PriceCalculator(use_optimized=True)

        weighted_df = processor.calculate_weighted_stats()

        if weighted_df is not None:
            # Calcola Overall scores
            df = processor.calculate_overall_scores(weighted_df)

            # Aggiorna price calculator con i dati
            price_calculator.update_players_data(df)

            # Calcola prezzi per tutti i giocatori con budget di default
            all_player_ids = df['Id'].tolist()
            price_data = price_calculator.calculate_batch_prices(all_player_ids, self.budget)

            # Aggiungi price_percentage al DataFrame
            df['price_percentage'] = df['Id'].apply(
                lambda pid: price_data.get(pid, {}).get('percentage', 0)
            )

            self.all_players = df[['Id', 'Nome', 'Squadra', 'R', 'Fm_weighted', 'Mv_weighted', 'seasons_count', 'Overall', 'price_percentage', 'Pv_recent', 'Pv_weighted']].copy()
            self.all_players['display'] = (
                self.all_players['Nome'] + ' (' +
                self.all_players['Squadra'] + ' - ' +
                self.all_players['R'] + ')'
            )

            self._populate_ui_with_data()
        else:
            self.all_players = None

    def _populate_ui_with_data(self):
        """Popola l'interfaccia con i dati caricati"""
        if self.all_players is None:
            return

        # Nascondi indicatori di caricamento
        if hasattr(self, 'loading_frames'):
            for loading_frame in self.loading_frames:
                loading_frame.grid_remove()

        # Popola filtri squadre
        teams = ["Squadre"] + sorted(self.all_players['Squadra'].unique().tolist())
        for team_var, team_menu in self.team_filters:
            team_menu.configure(values=teams)

        # Popola tutte e 3 le liste
        for i in range(3):
            self._filter_players_list(i)

    def _filter_players_list(self, slot_index):
        """Filtra e popola la lista giocatori per uno slot"""
        if self.all_players is None:
            return

        listbox = self.listboxes[slot_index]
        search_text = self.search_vars[slot_index].get().strip().lower()
        role_filter = self.role_filters[slot_index].get()
        team_var, _ = self.team_filters[slot_index]
        team_filter = team_var.get()
        favorites_only = self.favorites_filters[slot_index].get()

        # SLOT 2 (Giocatori Consigliati): mostra consigliati se nessun filtro attivo
        if slot_index == 2 and not search_text and role_filter == "Ruoli" and team_filter == "Squadre" and not favorites_only:
            self._show_recommended_players(listbox)
            return

        # Filtra
        filtered = self.all_players.copy()

        if search_text:
            filtered = filtered[filtered['Nome'].str.lower().str.contains(search_text, na=False)]

        if role_filter != "Ruoli":
            filtered = filtered[filtered['R'].str.contains(role_filter, na=False)]

        if team_filter != "Squadre":
            filtered = filtered[filtered['Squadra'] == team_filter]

        # Filtro preferiti
        if favorites_only:
            favorite_ids = self.favorites_manager.get_all_favorites()
            filtered = filtered[filtered['Id'].isin(favorite_ids)]

        # Popola listbox
        listbox.delete(0, tk.END)
        for _, row in filtered.iterrows():
            listbox.insert(tk.END, row['display'])

        # Salva dati filtrati per riferimento
        if not hasattr(self, 'filtered_data'):
            self.filtered_data = [None, None, None]
        self.filtered_data[slot_index] = filtered

    def _show_recommended_players(self, listbox):
        """Mostra giocatori consigliati basati sui primi 2 slot"""
        import pandas as pd

        # Verifica che ci siano giocatori selezionati nei primi 2 slot
        selected_players = [self.player_slots[0], self.player_slots[1]]
        selected_players = [p for p in selected_players if p is not None]

        if len(selected_players) == 0:
            # Nessun giocatore selezionato: mostra i top 5 overall
            filtered = self.all_players.copy()
            filtered['_overall_sort'] = pd.to_numeric(filtered['Overall'], errors='coerce')
            filtered = filtered.sort_values('_overall_sort', ascending=False, na_position='last').head(5)
            filtered = filtered.drop(columns='_overall_sort')

            listbox.delete(0, tk.END)
            for _, row in filtered.iterrows():
                listbox.insert(tk.END, row['display'])

            if not hasattr(self, 'filtered_data'):
                self.filtered_data = [None, None, None]
            self.filtered_data[2] = filtered
            return

        # Helper per estrarre valore numerico da colonne weighted
        def safe_float(value):
            if pd.isna(value):
                return 0.0
            if isinstance(value, (int, float)):
                return float(value)
            # Rimuovi simboli trend
            value_str = str(value).replace('↑', '').replace('↓', '').replace('→', '').strip()
            try:
                return float(value_str)
            except:
                return 0.0

        # Estrai caratteristiche dai giocatori selezionati
        roles = []
        roles_with_modifiers = []
        fm_values = []
        price_values = []
        pv_values = []

        for player in selected_players:
            role_full = player.get('R', '')
            role_base = role_full.split('/')[0].split('(')[0].strip()
            roles.append(role_base)

            # Estrai modificatori (E, T, etc.) dalle parentesi
            modifiers = ''
            if '(' in role_full:
                modifiers = role_full.split('(')[1].split(')')[0].strip()
            roles_with_modifiers.append((role_base, modifiers))

            fm_values.append(safe_float(player.get('Fm', 6.0)))
            price_values.append(safe_float(player.get('price_percentage', 5.0)))
            pv_values.append(safe_float(player.get('Pv_recent', player.get('Pv', 20))))

        # Calcola target medio
        target_role = roles[0] if len(set(roles)) == 1 else None  # Stesso ruolo per tutti
        target_modifiers = set()
        for _, mods in roles_with_modifiers:
            if mods:
                target_modifiers.update(list(mods))

        target_fm = sum(fm_values) / len(fm_values)
        target_price = sum(price_values) / len(price_values)
        target_pv = sum(pv_values) / len(pv_values)

        # Filtra candidati
        candidates = self.all_players.copy()

        # Escludi giocatori già selezionati
        selected_ids = [p['Id'] for p in selected_players]
        candidates = candidates[~candidates['Id'].isin(selected_ids)]

        # Calcola score di similarità per ogni candidato
        scores = []

        for idx, row in candidates.iterrows():
            score = 0.0

            # 1. RUOLO (peso massimo)
            role_full = row.get('R', '')
            role_base = role_full.split('/')[0].split('(')[0].strip()

            if target_role and role_base == target_role:
                score += 100  # Match perfetto ruolo
            elif target_role:
                continue  # Skip se ruolo diverso

            # Bonus per modificatori (E, T)
            modifiers = ''
            if '(' in role_full:
                modifiers = role_full.split('(')[1].split(')')[0].strip()

            modifier_match = 0
            if modifiers and target_modifiers:
                common = set(list(modifiers)) & target_modifiers
                modifier_match = len(common) / len(target_modifiers) * 30
            score += modifier_match

            # 2. FM ultima stagione (40%)
            fm = safe_float(row.get('Fm_weighted', 6.0))
            fm_diff = abs(fm - target_fm)
            fm_score = max(0, 40 - (fm_diff * 20))  # -0.05 FM = -1 punto
            score += fm_score

            # 3. Prezzo massimo (30%)
            price = safe_float(row.get('price_percentage', 5.0))
            price_diff = abs(price - target_price)
            price_score = max(0, 30 - (price_diff * 2))  # -0.5% = -1 punto
            score += price_score

            # 4. PV ultima stagione (30%)
            pv = safe_float(row.get('Pv_recent', row.get('Pv_weighted', 20)))
            pv_diff = abs(pv - target_pv)
            pv_score = max(0, 30 - (pv_diff * 1.5))  # -0.67 PV = -1 punto
            score += pv_score

            # 5. Ranking interno al ruolo (bonus)
            overall = safe_float(row.get('Overall', 50))
            ranking_bonus = overall / 10  # Max +10 punti per Overall 99
            score += ranking_bonus

            scores.append((idx, score))

        # Ordina per score e prendi top 5
        scores.sort(key=lambda x: x[1], reverse=True)
        top_indices = [idx for idx, _ in scores[:5]]

        recommended = candidates.loc[top_indices]

        # Popola listbox
        listbox.delete(0, tk.END)
        for _, row in recommended.iterrows():
            listbox.insert(tk.END, row['display'])

        # Salva dati filtrati
        if not hasattr(self, 'filtered_data'):
            self.filtered_data = [None, None, None]
        self.filtered_data[2] = recommended

    def _on_listbox_double_click(self, slot_index):
        """Gestisce doppio click sulla lista"""
        listbox = self.listboxes[slot_index]
        selection = listbox.curselection()

        if not selection:
            return

        idx = selection[0]
        filtered = self.filtered_data[slot_index]

        if filtered is not None and idx < len(filtered):
            player_row = filtered.iloc[idx]
            self._select_player(slot_index, player_row)

    def _select_player(self, slot_index, player_row):
        """Seleziona un giocatore per lo slot"""
        self.player_slots[slot_index] = PlayerComparisonLogic.extract_player_data(player_row)
        self._show_preview(slot_index)

        # Aggiorna consigliati se viene selezionato un giocatore negli slot 0 o 1
        if slot_index in [0, 1]:
            self.window.after(50, lambda: self._filter_players_list(2))

        # Avvia preloading in background quando ci sono almeno 2 giocatori
        selected_count = sum(1 for p in self.player_slots if p is not None)
        if selected_count >= 2:
            # Avvia preloading dopo un breve delay per non bloccare la UI
            self.window.after(100, self._preload_comparison_data_in_background)

    def _show_preview(self, slot_index):
        """Mostra preview con FM e MV ponderata"""
        player = self.player_slots[slot_index]

        if player is None:
            return

        # Nascondi completamente i search controls
        self.search_controls[slot_index].grid_remove()

        # Mostra preview nella row 1 della card
        preview_frame = self.preview_frames[slot_index]
        preview_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Pulisci contenuto precedente
        for widget in preview_frame.winfo_children():
            widget.destroy()

        # Nome giocatore
        ctk.CTkLabel(
            preview_frame,
            text=player['Nome'],
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(pady=(12, 2))

        # Status titolarità sotto al nome
        status = get_status(player['Nome'])
        ctk.CTkLabel(
            preview_frame,
            text=f"Status: {status}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        ).pack(pady=(0, 6))

        # Badge squadra e ruolo
        badges_frame = ctk.CTkFrame(preview_frame, fg_color="transparent")
        badges_frame.pack(pady=(0, 10))

        squad_badge = ctk.CTkFrame(badges_frame, fg_color=COLORS['accent_blue'], corner_radius=6)
        squad_badge.pack(side="left", padx=3)
        ctk.CTkLabel(
            squad_badge,
            text=player['Squadra'],
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(padx=8, pady=3)

        role_badge = ctk.CTkFrame(badges_frame, fg_color=COLORS['accent_purple'], corner_radius=6)
        role_badge.pack(side="left", padx=3)
        ctk.CTkLabel(
            role_badge,
            text=player['R'],
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(padx=8, pady=3)

        # Container statistiche
        stats_container = ctk.CTkFrame(preview_frame, fg_color=COLORS['bg_secondary'], corner_radius=8)
        stats_container.pack(fill="x", padx=10, pady=(0, 10))

        fm_value = player.get('Fm', 0)
        mv_value = player.get('Mv', 0)

        # FM
        fm_row = ctk.CTkFrame(stats_container, fg_color="transparent")
        fm_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            fm_row,
            text="FM:",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        ).pack(side="left")

        fm_display = PlayerComparisonLogic.format_stat_value(fm_value)
        ctk.CTkLabel(
            fm_row,
            text=fm_display,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS['accent_green'] if fm_value and fm_value > 0 else COLORS['text_secondary']
        ).pack(side="right")

        # MV
        mv_row = ctk.CTkFrame(stats_container, fg_color="transparent")
        mv_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            mv_row,
            text="MV:",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        ).pack(side="left")

        mv_display = PlayerComparisonLogic.format_stat_value(mv_value)
        ctk.CTkLabel(
            mv_row,
            text=mv_display,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS['accent_green'] if mv_value and mv_value > 0 else COLORS['text_secondary']
        ).pack(side="right")

        # Bottone rimuovi
        ctk.CTkButton(
            preview_frame,
            text="❌ Rimuovi",
            command=lambda: self._clear_slot(slot_index),
            fg_color=COLORS['error'],
            hover_color="#D62A56",
            corner_radius=8,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(pady=(5, 10), padx=10, fill="x")

    # def _clear_slot(self, slot_index):
    #     """Pulisci slot e mostra di nuovo search controls"""
    #     self.player_slots[slot_index] = None
    #     self.search_vars[slot_index].set("")

    #     # Nascondi preview
    #     preview_frame = self.preview_frames[slot_index]
    #     preview_frame.grid_remove()

    #     # Mostra search controls
    #     self.search_controls[slot_index].grid()

    #     # Resetta filtri
    #     self.role_filters[slot_index].set("Ruoli")
    #     team_var, _ = self.team_filters[slot_index]
    #     team_var.set("Squadre")

    #     # Ricarica lista
    #     self._filter_players_list(slot_index)

    #     # Aggiorna consigliati se viene rimosso un giocatore dagli slot 0 o 1
    #     if slot_index in [0, 1]:
    #         self.window.after(50, lambda: self._filter_players_list(2))
    
    def _clear_slot(self, slot_index):
        """Pulisci slot e mostra di nuovo i controlli di ricerca"""
        self.player_slots[slot_index] = None
        self.search_vars[slot_index].set("")

        # Nascondi la preview
        preview_frame = self.preview_frames[slot_index]
        preview_frame.grid_remove()

        # Ripristina i controlli di ricerca nella stessa posizione
        self.search_controls[slot_index].grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))
        if slot_index in [0, 1]:
                     self.window.after(50, lambda: self._filter_players_list(2))
        

    def _launch_comparison(self):
        """Lancia confronto in finestra popup con dati precaricati"""
        selected_players = [p for p in self.player_slots if p is not None]

        if len(selected_players) < 2:
            messagebox.showwarning(
                "Attenzione",
                "Seleziona almeno 2 giocatori per il confronto"
            )
            return

        # Usa dati precaricati se disponibili
        preloaded_results = None
        if hasattr(self, '_preloaded_comparison_data'):
            preloaded_results = self._preloaded_comparison_data

        ComparisonResultsWindow(
            self.window,
            selected_players,
            self.budget,
            preloaded_data=preloaded_results
        )

    def _preload_comparison_data_in_background(self):
        """Precarica i dati necessari per la finestra di confronto risultati in background"""
        # Questo viene chiamato appena l'utente seleziona giocatori
        # per preparare i dati pesanti in anticipo
        selected_players = [p for p in self.player_slots if p is not None]

        if len(selected_players) < 2:
            return

        try:
            # Precarica statistiche comparative
            comparison_stats = PlayerComparisonLogic.compare_players(selected_players)

            # Precarica dati stagionali per tutti i giocatori
            players_seasonal_data = []
            for player in selected_players:
                seasonal_data = self._get_player_seasonal_data_for_preload(player['Id'])
                if seasonal_data:
                    players_seasonal_data.append({
                        'player': player,
                        'seasons': seasonal_data
                    })

            # Precarica statistiche ponderate
            players_weighted = []
            for player_data in players_seasonal_data:
                weighted = self._get_player_weighted_stats_for_preload(player_data['player']['Id'])
                if weighted:
                    weighted['Nome'] = player_data['player']['Nome']
                    players_weighted.append(weighted)

            # Salva i dati precaricati
            self._preloaded_comparison_data = {
                'comparison_stats': comparison_stats,
                'players_seasonal_data': players_seasonal_data,
                'players_weighted': players_weighted
            }
        except Exception:
            # Se il preload fallisce, non è un problema critico
            # La finestra caricherà i dati normalmente
            pass

    def _get_player_seasonal_data_for_preload(self, player_id):
        """Helper per preload - ottiene dati stagionali giocatore"""
        from src.config import STATS_FILES, get_season_labels

        season_labels = get_season_labels()
        season_names = [season_labels.get('old', 'N/A'), season_labels.get('middle', 'N/A'), season_labels.get('recent', 'N/A')]
        season_keys = ['old', 'middle', 'recent']
        seasonal_data = []

        for season_name, season_key in zip(season_names, season_keys):
            filename, _ = STATS_FILES[season_key]
            df = self.cache.get(filename)

            if df is not None:
                player_data = df[df['Id'] == player_id]

                if not player_data.empty:
                    row = player_data.iloc[0]
                    seasonal_data.append({
                        'season': season_name,
                        'Squadra': row.get('Squadra', 'N/A'),
                        'Pv': int(row.get('Pv', 0)),
                        'Mv': float(str(row.get('Mv', 0)).replace(',', '.')),
                        'Fm': float(str(row.get('Fm', 0)).replace(',', '.')),
                        'Gf': int(row.get('Gf', 0)),
                        'Gs': int(row.get('Gs', 0)),
                        'Rp': int(row.get('Rp', 0)),
                        'Ass': int(row.get('Ass', 0)),
                        'Amm': int(row.get('Amm', 0)),
                        'Esp': int(row.get('Esp', 0))
                    })

        return seasonal_data

    def _get_player_weighted_stats_for_preload(self, player_id):
        """Helper per preload - ottiene statistiche ponderate giocatore"""
        from src.data_processor import FantaCalcioDataProcessor
        processor = FantaCalcioDataProcessor()
        df = processor.calculate_weighted_stats()

        if df is None:
            return None

        player_data = df[df['Id'] == player_id]

        if player_data.empty:
            return None

        row = player_data.iloc[0]
        return {
            'Fm': row['Fm_weighted'],
            'Mv': row['Mv_weighted'],
            'Gf': row['Gf_weighted'],
            'Ass': row['Ass_weighted'],
            'Pv': row['Pv_weighted'],
            'Gs': row['Gs_weighted'],
            'Rp': row['Rp_weighted']
        }

class ComparisonResultsWindow:
    """Finestra popup ottimizzata per i risultati del confronto"""

    def __init__(self, parent, players, budget=500, preloaded_data=None):
        self.players = players
        self.cache = DataCache()
        self.budget = budget
        self.preloaded_data = preloaded_data  # Dati precaricati
        self.notes_manager = PlayerNotesManager()  # Per recuperare i tag
        self.favorites_manager = FavoritesManager()  # Per gestire preferiti

        # Finestra popup
        self.window = ctk.CTkToplevel(parent)
        configure_application_window(self.window)
        self.window.title("📊 Risultati Confronto")
        self.window.geometry("1400x850")
        self.window.configure(fg_color=COLORS['bg_primary'])

        # Transient & focus
        self.window.transient(parent)
        self.window.lift()
        self.window.focus_force()

        # Responsive grid
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

        # Massimizza
        try:
            self.window.state('zoomed')
        except Exception:
            pass

        self._setup_ui()

        # Carica e mostra il confronto (usa preloaded se disponibile)
        if preloaded_data:
            self.window.after(10, self._display_preloaded_comparison)
        else:
            self.window.after(10, self._load_and_display_comparison)

    def _setup_ui(self):
        """Setup UI con contenitore scrollabile e layout pulito"""
        # Main container SCROLLABILE per evitare taglia-fuori
        self.main_container = ctk.CTkScrollableFrame(
            self.window, 
            fg_color=COLORS['bg_primary'],
            scrollbar_button_color=COLORS['accent_purple'],
            scrollbar_button_hover_color=COLORS['accent_blue']
        )
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=15)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            header_frame,
            text="📊 RISULTATI CONFRONTO",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COLORS['accent_purple']
        ).pack(side="left")

        ctk.CTkButton(
            header_frame,
            text="✕ Chiudi",
            command=self.window.destroy,
            fg_color=COLORS['error'],
            hover_color="#D62A56",
            corner_radius=10,
            width=100,
            height=35,
            font=ctk.CTkFont(weight="bold")
        ).pack(side="right")

        # Container sommario
        self.summary_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.summary_container.pack(fill="x", pady=(0, 15))

        # Container Cards giocatori (3 colonne)
        self.cards_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.cards_container.pack(fill="x", pady=(0, 20))

        # Container Grafici
        self.graphs_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=COLORS['bg_secondary'],
            corner_radius=15,
            border_width=2,
            border_color=COLORS['border']
        )
        self.graphs_frame.pack(fill="x", pady=(0, 15))

    def _load_and_display_comparison(self):
        """Carica dati e mostra confronto"""
        comparison_stats = PlayerComparisonLogic.compare_players(self.players)

        players_seasonal_data = []
        for player in self.players:
            seasonal_data = self._get_player_seasonal_data(player['Id'])
            if seasonal_data:
                players_seasonal_data.append({
                    'player': player,
                    'seasons': seasonal_data
                })

        if not players_seasonal_data:
            messagebox.showerror("Errore", "Impossibile caricare i dati stagionali")
            self.window.destroy()
            return

        if comparison_stats:
            self._display_comparison_summary(comparison_stats)

        self._display_player_cards(players_seasonal_data)
        self._display_comparison_charts(players_seasonal_data)

    def _display_preloaded_comparison(self):
        """Mostra confronto usando dati precaricati per ottimizzare i tempi"""
        if not self.preloaded_data:
            # Fallback al caricamento normale
            self._load_and_display_comparison()
            return

        try:
            comparison_stats = self.preloaded_data.get('comparison_stats')
            players_seasonal_data = self.preloaded_data.get('players_seasonal_data')

            if not players_seasonal_data:
                messagebox.showerror("Errore", "Impossibile caricare i dati stagionali")
                self.window.destroy()
                return

            if comparison_stats:
                self._display_comparison_summary(comparison_stats)

            self._display_player_cards(players_seasonal_data)
            self._display_comparison_charts(players_seasonal_data)
        except Exception:
            # Se c'è un errore con i dati precaricati, fallback al caricamento normale
            self._load_and_display_comparison()

    def _display_comparison_summary(self, stats):
        """Sommario compatto senza spazi sprecati"""
        summary_frame = ctk.CTkFrame(
            self.summary_container,
            fg_color=COLORS['bg_secondary'],
            corner_radius=12,
            border_width=1,
            border_color=COLORS['accent_green']
        )
        summary_frame.pack(fill="x")

        stats_text = (
            f"🎯 Giocatori analizzati: {stats['count']}  |  "
            f"⚡ FM Media: {PlayerComparisonLogic.format_stat_value(stats['avg_fm'])}  |  "
            f"📈 MV Media: {PlayerComparisonLogic.format_stat_value(stats['avg_mv'])}"
        )

        ctk.CTkLabel(
            summary_frame,
            text=stats_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['accent_green']
        ).pack(pady=12)

    def _display_player_cards(self, players_data):
        """Mostra le 3 card ben spaziate e riempite con colorazione comparativa"""
        colors = [COLORS['accent_blue'], COLORS['accent_purple'], COLORS['accent_pink']]

        for i in range(len(players_data)):
            self.cards_container.grid_columnconfigure(i, weight=1)

        # Raccolta statistiche per confronto
        all_stats = {
            'fm': [],
            'mv': [],
            'pv': [],
            'overall': [],
            'price': [],
            'amm': [],
            'esp': [],
            'bonus': [],  # Gf o Gs
            'special': [],  # Ass o Rp
            'gs_per_match': [],  # Solo per portieri
            'gf_per_match': [],  # Solo per non portieri
            'ass_per_match': [],  # Solo per non portieri
            'bonus_per_match': [],  # Solo per non portieri (Gf+Ass)/Pv
            'amm_per_match': []  # Solo per difensori
        }

        # Prima passata: raccogli tutte le statistiche
        for player_data in players_data:
            player = player_data['player']
            seasons = player_data['seasons']

            if seasons:
                last_season = seasons[-1]
                is_goalkeeper = player['R'].startswith('P')
                is_defender = player['R'].startswith('D')

                all_stats['fm'].append(float(last_season.get('Fm', 0)))
                all_stats['mv'].append(float(last_season.get('Mv', 0)))
                pv = int(last_season.get('Pv', 0))
                all_stats['pv'].append(pv)

                # Overall potrebbe essere int o float, gestisci entrambi
                try:
                    overall_val = float(player.get('Overall', 0))
                except (ValueError, TypeError):
                    overall_val = 0
                all_stats['overall'].append(overall_val)

                # Price percentage potrebbe non esistere
                try:
                    price_val = float(player.get('price_percentage', 0))
                except (ValueError, TypeError):
                    price_val = 0
                all_stats['price'].append(price_val)

                amm_val = int(last_season.get('Amm', 0))
                esp_val = int(last_season.get('Esp', 0))

                all_stats['amm'].append(amm_val)
                all_stats['esp'].append(esp_val)

                if is_goalkeeper:
                    gs = int(last_season.get('Gs', 0))
                    all_stats['bonus'].append(gs)
                    all_stats['special'].append(int(last_season.get('Rp', 0)))
                    # GS per partita (per portieri)
                    all_stats['gs_per_match'].append(gs / pv if pv > 0 else 0)
                else:
                    gf = int(last_season.get('Gf', 0))
                    ass = int(last_season.get('Ass', 0))
                    all_stats['bonus'].append(gf)
                    all_stats['special'].append(ass)
                    # GF per partita
                    all_stats['gf_per_match'].append(gf / pv if pv > 0 else 0)
                    # Assist per partita
                    all_stats['ass_per_match'].append(ass / pv if pv > 0 else 0)
                    # Bonus per partita (GF + Ass) / Pv
                    all_stats['bonus_per_match'].append((gf + ass) / pv if pv > 0 else 0)

                # Ammonizioni per partita (solo per difensori)
                if is_defender:
                    amm = int(last_season.get('Amm', 0))
                    all_stats['amm_per_match'].append(amm / pv if pv > 0 else 0)

        # Calcola migliori e peggiori per ogni statistica
        def get_best_worst(values, higher_is_better=True):
            if not values or all(v == 0 for v in values):
                return None, None
            if higher_is_better:
                return max(values), min(values)
            else:
                return min(values), max(values)

        best_worst = {
            'fm': get_best_worst(all_stats['fm'], True),
            'mv': get_best_worst(all_stats['mv'], True),
            'pv': get_best_worst(all_stats['pv'], True),
            'overall': get_best_worst(all_stats['overall'], True),
            'price': get_best_worst(all_stats['price'], False),  # Prezzo basso è meglio
            'amm': get_best_worst(all_stats['amm'], False),  # Meno ammonizioni è meglio
            'esp': get_best_worst(all_stats['esp'], False),  # Meno espulsioni è meglio
            'bonus': get_best_worst(all_stats['bonus'], True),
            'special': get_best_worst(all_stats['special'], True),
            'gs_per_match': get_best_worst(all_stats['gs_per_match'], False),  # Meno GS/partita è meglio
            'gf_per_match': get_best_worst(all_stats['gf_per_match'], True),  # Più GF/partita è meglio
            'ass_per_match': get_best_worst(all_stats['ass_per_match'], True),  # Più assist/partita è meglio
            'bonus_per_match': get_best_worst(all_stats['bonus_per_match'], True),  # Più bonus/partita è meglio
            'amm_per_match': get_best_worst(all_stats['amm_per_match'], False)  # Meno ammonizioni/partita è meglio
        }

        # Seconda passata: crea le card con colorazione
        for idx, player_data in enumerate(players_data):
            player = player_data['player']
            seasons = player_data['seasons']

            card = ctk.CTkFrame(
                self.cards_container,
                fg_color=COLORS['bg_secondary'],
                corner_radius=15,
                border_width=2,
                border_color=colors[idx]
            )
            card.grid(row=0, column=idx, sticky="nsew", padx=8, pady=5)

            # Header - Nome e bottone preferiti
            header_frame = ctk.CTkFrame(card, fg_color="transparent")
            header_frame.pack(pady=(15, 2), padx=10, fill="x")

            # Nome cliccabile a sinistra
            name_label = ctk.CTkLabel(
                header_frame,
                text=player['Nome'],
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=COLORS['text_primary'],
                cursor="hand2"
            )
            name_label.pack(side="left", pady=0)
            name_label.bind("<Double-Button-1>", lambda e, p=player: self._open_player_details(p))

            # Bottone preferiti a destra
            is_favorite = self.favorites_manager.is_favorite(player['Id'])
            fav_button = ctk.CTkButton(
                header_frame,
                text="⭐" if is_favorite else "☆",
                command=lambda pid=player['Id'], btn_idx=idx: self._toggle_favorite_in_comparison(pid, btn_idx),
                fg_color=COLORS['accent_yellow'] if is_favorite else COLORS['bg_tertiary'],
                hover_color="#FFB703" if is_favorite else COLORS['hover'],
                text_color=COLORS['bg_primary'] if is_favorite else COLORS['text_primary'],
                corner_radius=8,
                width=35,
                height=35,
                font=ctk.CTkFont(size=16, weight="bold")
            )
            fav_button.pack(side="right", pady=0)

            # Salva riferimento al bottone per aggiornarlo dinamicamente
            if not hasattr(self, 'favorite_buttons'):
                self.favorite_buttons = {}
            self.favorite_buttons[idx] = fav_button

            # Status titolarità sotto al nome
            status = get_status(player['Nome'])
            ctk.CTkLabel(
                card,
                text=f"Status: {status}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS['text_secondary']
            ).pack(pady=(0, 2))

            # Indicatore solo per dati di una sola stagione (non ponderabili)
            if player.get('seasons_count', 1) == 1:
                ctk.CTkLabel(
                    card,
                    text="* Dati disponibili solo per 1 stagione",
                    font=ctk.CTkFont(size=10),
                    text_color=COLORS['warning']
                ).pack(pady=(0, 4))

            ctk.CTkLabel(
                card,
                text=f"{player['Squadra']} • {player['R']}",
                font=ctk.CTkFont(size=12),
                text_color=COLORS['text_secondary']
            ).pack(pady=(0, 12))

            if seasons:
                last_season = seasons[-1]

                # Tabella statistiche
                stats_grid = ctk.CTkFrame(card, fg_color=COLORS['bg_tertiary'], corner_radius=10)
                stats_grid.pack(fill="x", padx=12, pady=(0, 15))

                # Adatta dinamicamente se è un portiere
                is_goalkeeper = player['R'].startswith('P')
                is_defender = player['R'].startswith('D')

                bonus_label = "Goal Subiti (GS)" if is_goalkeeper else "Goal Fatti (GF)"
                bonus_val = last_season.get('Gs', 0) if is_goalkeeper else last_season.get('Gf', 0)
                special_label = "Rigori Parati (RP)" if is_goalkeeper else "Assist (ASS)"
                special_val = last_season.get('Rp', 0) if is_goalkeeper else last_season.get('Ass', 0)

                pv = int(last_season.get('Pv', 0))

                # Funzione per determinare il colore
                def get_stat_color(value, stat_key):
                    best, worst = best_worst.get(stat_key, (None, None))
                    if best is None or worst is None:
                        return colors[idx]
                    if best == worst:
                        # Tutti i valori sono uguali → bianco
                        return COLORS['text_primary']
                    try:
                        val = float(value) if not isinstance(value, (int, float)) else value
                        if val == best:
                            return COLORS['success']
                        elif val == worst:
                            return COLORS['error']
                        else:
                            # Valore intermedio → bianco
                            return COLORS['text_primary']
                    except (ValueError, TypeError):
                        pass
                    return colors[idx]

                # Estrai valori in modo sicuro
                try:
                    overall_val = int(player.get('Overall', 0))
                except (ValueError, TypeError):
                    overall_val = 0

                try:
                    price_val = float(player.get('price_percentage', 0))
                except (ValueError, TypeError):
                    price_val = 0

                # Lista statistiche base
                stats_items = [
                    ("Overall (OVR)", overall_val, 'overall'),
                    ("% Prezzo Max", f"{price_val:.1f}%", 'price'),
                    ("Fantamedia (FM)", PlayerComparisonLogic.format_stat_value(last_season.get('Fm', 0)), 'fm'),
                    ("Media Voto (MV)", PlayerComparisonLogic.format_stat_value(last_season.get('Mv', 0)), 'mv'),
                ]

                # Aggiungi info tiratore (tag rigorista o tiratore piazzati)
                player_tags = self.notes_manager.get_tags(player['Id'])
                tiratore_value = "No"
                if 'rigorista' in player_tags and 'tiratore piazzati' in player_tags:
                    tiratore_value = "Rigorista, Calci Piazzati"
                elif 'rigorista' in player_tags:
                    tiratore_value = "Rigorista"
                elif 'tiratore piazzati' in player_tags:
                    tiratore_value = "Calci Piazzati"

                stats_items.append(("Tiratore:", tiratore_value, None))  # None = nessun confronto colore
                stats_items.append(("Presenze (PV)", pv, 'pv'))
                stats_items.extend([
                    (bonus_label, int(bonus_val), 'bonus'),
                    (special_label, int(special_val), 'special'),
                ])

                # Aggiungi statistiche per partita in base al ruolo
                if is_goalkeeper:
                    # Portieri: GS per partita
                    gs = int(last_season.get('Gs', 0))
                    gs_per_match = gs / pv if pv > 0 else 0
                    stats_items.append(("GS per Partita", f"{gs_per_match:.2f}", 'gs_per_match'))
                else:
                    # Non portieri: GF/partita, Assist/partita, Bonus/partita
                    gf = int(last_season.get('Gf', 0))
                    ass = int(last_season.get('Ass', 0))
                    gf_per_match = gf / pv if pv > 0 else 0
                    ass_per_match = ass / pv if pv > 0 else 0
                    bonus_per_match = (gf + ass) / pv if pv > 0 else 0

                    stats_items.append(("GF per Partita", f"{gf_per_match:.2f}", 'gf_per_match'))
                    stats_items.append(("Assist per Partita", f"{ass_per_match:.2f}", 'ass_per_match'))
                    stats_items.append(("Bonus per Partita", f"{bonus_per_match:.2f}", 'bonus_per_match'))

                # Difensori: Cartellini gialli per partita
                if is_defender:
                    amm = int(last_season.get('Amm', 0))
                    amm_per_match = amm / pv if pv > 0 else 0
                    stats_items.append(("Amm. per Partita", f"{amm_per_match:.2f}", 'amm_per_match'))

                # Aggiungi statistiche finali comuni
                stats_items.extend([
                    ("Ammonizioni", int(last_season.get('Amm', 0)), 'amm'),
                    ("Espulsioni", int(last_season.get('Esp', 0)), 'esp')
                ])

                for label, value, stat_key in stats_items:
                    row = ctk.CTkFrame(stats_grid, fg_color="transparent")
                    row.pack(fill="x", padx=10, pady=6)

                    ctk.CTkLabel(
                        row,
                        text=label,
                        font=ctk.CTkFont(size=11),
                        text_color=COLORS['text_secondary']
                    ).pack(side="left")

                    # Determina colore in base al confronto
                    display_value = str(value)

                    # Se stat_key è None, usa colore base (per righe senza confronto come "Tiratore:")
                    if stat_key is None:
                        stat_color = COLORS['text_primary']
                    else:
                        # Estrai valore numerico per il confronto
                        try:
                            # Rimuovi simboli come % e converti in float
                            if isinstance(value, str):
                                # Rimuovi % se presente
                                clean_value = value.replace('%', '').strip()
                                compare_value = float(clean_value)
                            elif isinstance(value, (int, float)):
                                compare_value = float(value)
                            else:
                                compare_value = 0.0
                        except (ValueError, TypeError):
                            compare_value = 0.0

                        stat_color = get_stat_color(compare_value, stat_key)

                    ctk.CTkLabel(
                        row,
                        text=display_value,
                        font=ctk.CTkFont(size=13, weight="bold"),
                        text_color=stat_color
                    ).pack(side="right")

    def _get_player_seasonal_data(self, player_id):
        """Helper per recuperare i dati stagionali dal DB o cache"""
        if hasattr(self.cache, 'get_player_seasons'):
            return self.cache.get_player_seasons(player_id)
        
        # Fallback se la cache ha struttura diversa
        for p in self.players:
            if p['Id'] == player_id:
                return [{
                    'Fm': p.get('Fm', 0),
                    'Mv': p.get('Mv', 0),
                    'Pv': p.get('Pv', 30),
                    'Gf': p.get('Gf', 0),
                    'Gs': p.get('Gs', 0),
                    'Ass': p.get('Ass', 0),
                    'Rp': p.get('Rp', 0)
                }]
        return []

    def _display_comparison_charts(self, players_data):
        """Mostra grafici comparativi usando modulo centralizzato"""
        # Ruolo di riferimento
        reference_role = extract_base_role(players_data[0]['player']['R'])

        # Ottieni stats da confrontare
        if reference_role not in ROLE_WEIGHTS:
            reference_role = 'C'  # Default

        stats_to_plot = list(ROLE_WEIGHTS[reference_role].keys())

        # Usa dati precaricati se disponibili
        if self.preloaded_data and 'players_weighted' in self.preloaded_data:
            players_weighted = self.preloaded_data['players_weighted']
        else:
            # Altrimenti ottieni dati ponderati normalmente
            players_weighted = []
            for player_data in players_data:
                weighted = self._get_player_weighted_stats(player_data['player']['Id'])
                if weighted:
                    weighted['Nome'] = player_data['player']['Nome']
                    players_weighted.append(weighted)

        if not players_weighted:
            return

        # Prepara dizionario stats per il modulo centralizzato
        stats_dict = {}
        for stat in stats_to_plot:
            # Converti tutti i valori in float/int per evitare errori
            raw_values = [p.get(stat, 0) for p in players_weighted]
            numeric_values = []
            for val in raw_values:
                try:
                    # Converti stringhe con virgole in float
                    if isinstance(val, str):
                        val = float(val.replace(',', '.'))
                    numeric_values.append(float(val) if val else 0.0)
                except (ValueError, TypeError):
                    numeric_values.append(0.0)
            stats_dict[stat] = numeric_values

        player_names = [p['Nome'] for p in players_weighted]

        # Crea figura usando il modulo centralizzato
        figure = create_advanced_comparison_figure(
            player_names=player_names,
            stats_dict=stats_dict,
            role=reference_role
        )

        # Incorpora in Tkinter
        embed_figure_in_tkinter(figure, self.graphs_frame)

    def _get_player_seasonal_data(self, player_id):
        """Ottiene dati stagionali giocatore"""
        from src.config import get_season_labels

        season_labels = get_season_labels()
        season_names = [season_labels.get('old', 'N/A'), season_labels.get('middle', 'N/A'), season_labels.get('recent', 'N/A')]
        season_keys = ['old', 'middle', 'recent']
        seasonal_data = []

        for season_name, season_key in zip(season_names, season_keys):
            filename, _ = STATS_FILES[season_key]
            df = self.cache.get(filename)

            if df is not None:
                player_data = df[df['Id'] == player_id]

                if not player_data.empty:
                    row = player_data.iloc[0]
                    seasonal_data.append({
                        'season': season_name,
                        'Squadra': row.get('Squadra', 'N/A'),
                        'Pv': int(row.get('Pv', 0)),
                        'Mv': float(str(row.get('Mv', 0)).replace(',', '.')),
                        'Fm': float(str(row.get('Fm', 0)).replace(',', '.')),
                        'Gf': int(row.get('Gf', 0)),
                        'Gs': int(row.get('Gs', 0)),
                        'Rp': int(row.get('Rp', 0)),
                        'Ass': int(row.get('Ass', 0)),
                        'Amm': int(row.get('Amm', 0)),
                        'Esp': int(row.get('Esp', 0))
                    })

        return seasonal_data

    def _get_player_weighted_stats(self, player_id):
        """Ottiene statistiche ponderate giocatore"""
        from src.data_processor import FantaCalcioDataProcessor
        processor = FantaCalcioDataProcessor()
        df = processor.calculate_weighted_stats()

        if df is None:
            return None

        player_data = df[df['Id'] == player_id]

        if player_data.empty:
            return None

        row = player_data.iloc[0]
        return {
            'Fm': row['Fm_weighted'],
            'Mv': row['Mv_weighted'],
            'Gf': row['Gf_weighted'],
            'Ass': row['Ass_weighted'],
            'Pv': row['Pv_weighted'],
            'Gs': row['Gs_weighted'],
            'Rp': row['Rp_weighted']
        }

    def _open_player_details(self, player):
        """Apri finestra dettaglio giocatore con doppio click sul nome"""
        from src.ui.player_details import PlayerDetailsWindow

        PlayerDetailsWindow(
            self.window,
            player['Id'],
            player['Nome'],
            player['R'],
            self.budget
        )

    def _toggle_favorite_in_comparison(self, player_id, button_index):
        """Toggle stato preferito del giocatore nel confronto"""
        is_now_favorite = self.favorites_manager.toggle_favorite(player_id)

        # Aggiorna bottone
        if button_index in self.favorite_buttons:
            button = self.favorite_buttons[button_index]
            if is_now_favorite:
                button.configure(
                    text="⭐",
                    fg_color=COLORS['accent_yellow'],
                    hover_color="#FFB703",
                    text_color=COLORS['bg_primary']
                )
            else:
                button.configure(
                    text="☆",
                    fg_color=COLORS['bg_tertiary'],
                    hover_color=COLORS['hover'],
                    text_color=COLORS['text_primary']
                )
