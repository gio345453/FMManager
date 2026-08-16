"""
Dashboard Squadre - Design ultra-moderno e professionale
"""
import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from src.data.team_stats import TeamStatsManager
from src.ui.team_detail_window import TeamDetailWindow
from src.ui.window_chrome import configure_application_window


# Palette colori moderna (stessa della main app)
COLORS = {
    'bg_primary': '#0F0F1E',
    'bg_secondary': '#1E1E2E',
    'bg_tertiary': '#2B2D42',
    'accent_blue': '#3A86FF',
    'accent_purple': '#8338EC',
    'accent_pink': '#FF006E',
    'accent_green': '#06D6A0',
    'text_primary': '#FFFFFF',
    'text_secondary': '#A0A0B0',
    'border': '#3A3A4A',
    'hover': '#363646',
    'success': '#06D6A0',
    'warning': '#FFB703',
    'error': '#EF476F'
}


class TeamDashboardWindow:
    """Dashboard squadre con tabella e dettagli"""

    def __init__(self, parent, processor, df_with_overall=None):
        self.processor = processor
        self.df = df_with_overall
        self.team_stats_manager = None
        self.teams_summary = None

        from src.config import get_current_season_label

        self.window = ctk.CTkToplevel(parent)
        configure_application_window(self.window)
        self.window.title(f"Dashboard Squadre - Serie A {get_current_season_label()}")
        self.window.configure(fg_color=COLORS['bg_primary'])

        # Nascondi la finestra durante il setup per evitare rendering progressivo
        self.window.withdraw()

        # Apri sopra la finestra principale
        self.window.transient(parent)

        self._setup_ui()
        self._load_and_display_data()

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
        """Setup interfaccia moderna"""
        # Main container con padding
        main_container = ctk.CTkFrame(self.window, fg_color=COLORS['bg_primary'])
        main_container.pack(fill="both", expand=True, padx=30, pady=30)

        self._build_content(main_container)

    def _build_content(self, parent):
        """Costruisce il contenuto"""
        # Header
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            header,
            text="🏆 DASHBOARD SQUADRE",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(side="left")

        from src.config import get_current_season_label

        ctk.CTkLabel(
            header,
            text=f"Serie A {get_current_season_label()}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['accent_blue']
        ).pack(side="left", padx=15)

        # Card tabella squadre
        self._build_teams_table_card(parent)

    def _build_teams_table_card(self, parent):
        """Card con tabella di tutte le squadre"""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS['bg_secondary'],
            corner_radius=20
        )
        card.pack(fill="both", expand=True)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=25)

        from src.config import get_current_season_label

        ctk.CTkLabel(
            content,
            text=f"📋 CLASSIFICA - {get_current_season_label().replace('/', '')}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(anchor="w", pady=(0, 15))

        # Info rapida
        info_label = ctk.CTkLabel(
            content,
            text="💡 Doppio click su una squadra per vedere i dettagli completi e la rosa",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        )
        info_label.pack(anchor="w", pady=(0, 10))

        # Treeview per squadre (prime 17)
        tree_frame = ctk.CTkFrame(content, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, pady=(0, 15))

        # Configura stile
        style = ttk.Style()
        style.configure(
            "Teams.Treeview",
            background=COLORS['bg_tertiary'],
            foreground=COLORS['text_primary'],
            fieldbackground=COLORS['bg_tertiary'],
            borderwidth=0,
            relief="flat",
            rowheight=40,
            font=('Arial', 12)
        )

        style.configure(
            "Teams.Treeview.Heading",
            background=COLORS['bg_primary'],
            foreground=COLORS['accent_purple'],
            borderwidth=0,
            relief="flat",
            font=('Arial', 15, 'bold')
        )

        style.map('Teams.Treeview', background=[], foreground=[])

        columns = ('Pos', 'Squadra', 'Punti', 'GF', 'GS', 'Diff.Reti')

        self.teams_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            style="Teams.Treeview",
            selectmode='browse'
        )

        column_widths = {
            'Pos': 80,
            'Squadra': 200,
            'Punti': 100,
            'GF': 80,
            'GS': 80,
            'Diff.Reti': 120
        }

        for col in columns:
            self.teams_tree.heading(col, text=col, anchor='center')
            self.teams_tree.column(col, width=column_widths.get(col, 100), anchor='center')

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.teams_tree.yview)
        self.teams_tree.configure(yscrollcommand=scrollbar.set)

        self.teams_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Tag per righe alternate
        self.teams_tree.tag_configure('evenrow', background=COLORS['bg_tertiary'])
        self.teams_tree.tag_configure('oddrow', background='#252535')
        # Tag speciale per neopromosse (evidenziate in verde)
        self.teams_tree.tag_configure('neopromossa', background='#1E3A2B', foreground=COLORS['accent_green'])

        # Bind doppio click
        self.teams_tree.bind('<Double-Button-1>', self._on_team_double_click)

        # --- SEZIONE NEOPROMOSSE ---
        self._build_neopromosse_section(content)

    def _load_and_display_data(self):
        """Carica e visualizza i dati delle squadre"""
        if self.df is None:
            return

        # Inizializza TeamStatsManager
        self.team_stats_manager = TeamStatsManager(self.df)

        # Ottieni riepilogo di tutte le squadre (con statistiche)
        self.teams_summary = self.team_stats_manager.get_all_teams_summary()

        if not self.teams_summary:
            return

        # Identifica neopromosse: squadre nella lista giocatori ma senza statistiche
        all_teams = self._get_all_teams_from_players()
        teams_with_stats = self._get_current_season_teams()
        neopromosse = all_teams - teams_with_stats

        # Popola la tabella con le prime 17 squadre (con statistiche)
        for idx, team in enumerate(self.teams_summary[:17]):
            values = [
                f"{team['posizione']}°",
                team['squadra'],
                team['punti'],
                team['gol_fatti'],
                team['gol_subiti'],
                team['gol_fatti'] - team['gol_subiti']
            ]

            row_tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            item_id = self.teams_tree.insert('', 'end', values=values, tags=(row_tag,))

        # Aggiungi le neopromosse dopo la 17° posizione con "-" per tutti i valori
        for team_name in sorted(neopromosse):
            values = [
                "-",  # Nessuna posizione
                team_name,
                "-",  # Nessun punto
                "-",  # Nessun GF
                "-",  # Nessun GS
                "-"   # Nessuna diff reti
            ]

            # Tag speciale per neopromosse (evidenziato in verde)
            row_tag = 'neopromossa'
            item_id = self.teams_tree.insert('', 'end', values=values, tags=(row_tag,))

        # Popola la sezione neopromosse separata
        self._populate_neopromosse(neopromosse)

    def _build_neopromosse_section(self, parent):
        """Costruisce la sezione per le squadre neopromosse"""
        # Separatore
        separator = ctk.CTkFrame(parent, height=2, fg_color=COLORS['border'])
        separator.pack(fill="x", pady=(10, 15))

        # Titolo sezione
        ctk.CTkLabel(
            parent,
            text="⬆️ NEOPROMOSSE",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['accent_green']
        ).pack(anchor="w", pady=(0, 10))

        # Frame per le neopromosse
        self.neopromosse_frame = ctk.CTkFrame(parent, fg_color=COLORS['bg_tertiary'], corner_radius=10)
        self.neopromosse_frame.pack(fill="x", pady=(0, 10))

    def _populate_neopromosse(self, neopromosse):
        """Popola la sezione neopromosse con le squadre nuove della stagione"""
        if not neopromosse:
            # Nessuna neopromossa trovata
            ctk.CTkLabel(
                self.neopromosse_frame,
                text="Nessuna squadra neopromossa identificata",
                font=ctk.CTkFont(size=12),
                text_color=COLORS['text_secondary']
            ).pack(padx=15, pady=10)
            return

        # Mostra le neopromosse (senza statistiche, solo nome)
        for team_name in sorted(neopromosse):
            team_row = ctk.CTkFrame(self.neopromosse_frame, fg_color="transparent")
            team_row.pack(fill="x", padx=15, pady=5)

            # Nome squadra (cliccabile)
            name_label = ctk.CTkLabel(
                team_row,
                text=f"⬆️ {team_name}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLORS['accent_green'],
                cursor="hand2"
            )
            name_label.pack(side="left")
            name_label.bind("<Button-1>", lambda e, tn=team_name: self._open_team_detail(tn))

            # Info
            ctk.CTkLabel(
                team_row,
                text="(Neopromossa - statistiche non disponibili)",
                font=ctk.CTkFont(size=11),
                text_color=COLORS['text_secondary']
            ).pack(side="left", padx=15)

    def _get_previous_season_teams(self):
        """Restituisce il set di squadre della stagione precedente"""
        from src.config import STATS_FILES
        from src.data.cache import DataCache

        cache = DataCache()

        # Usa la stagione 'middle' come riferimento della stagione precedente
        middle_file, _ = STATS_FILES.get('middle', (None, None))
        if not middle_file:
            return set()

        df_middle = cache.get(middle_file)
        if df_middle is None or df_middle.empty:
            return set()

        # Estrai nomi squadre unici dalla stagione middle
        return set(df_middle['Squadra'].dropna().unique())

    def _get_current_season_teams(self):
        """Restituisce il set di squadre della stagione corrente (recent con statistiche)"""
        from src.config import STATS_FILES
        from src.data.cache import DataCache

        cache = DataCache()

        # Usa la stagione 'recent' come riferimento della stagione corrente
        recent_file, _ = STATS_FILES.get('recent', (None, None))
        if not recent_file:
            return set()

        df_recent = cache.get(recent_file)
        if df_recent is None or df_recent.empty:
            return set()

        # Estrai nomi squadre unici dalla stagione recent
        return set(df_recent['Squadra'].dropna().unique())

    def _get_all_teams_from_players(self):
        """Restituisce il set di tutte le squadre presenti nella lista giocatori (CURRENT_SEASON)"""
        from src.config import CURRENT_SEASON_FILE
        from src.data.cache import DataCache

        cache = DataCache()

        df_current = cache.get(CURRENT_SEASON_FILE)
        if df_current is None or df_current.empty:
            return set()

        # Estrai nomi squadre unici dalla lista giocatori
        return set(df_current['Squadra'].dropna().unique())

    def _open_team_detail(self, team_name):
        """Apre la finestra dettaglio per una squadra specifica"""
        from src.data.player_notes import PlayerNotesManager
        from src.data.price_calculator import PriceCalculator

        # Verifica se è una neopromossa (senza statistiche)
        all_teams = self._get_all_teams_from_players()
        teams_with_stats = self._get_current_season_teams()
        neopromosse = all_teams - teams_with_stats

        if team_name in neopromosse:
            # Neopromossa: mostra solo rosa, senza statistiche
            team_stats = None
        else:
            # Squadra con statistiche complete
            team_stats = self.team_stats_manager.get_team_stats(team_name)
            if not team_stats:
                messagebox.showwarning("Attenzione", f"Statistiche non disponibili per {team_name}")
                return

        price_calculator = PriceCalculator(use_optimized=True)
        player_notes_manager = PlayerNotesManager()

        detail_window = TeamDetailWindow(
            self.window,
            team_name,
            team_stats,
            self.df,
            self.processor,
            price_calculator,
            player_notes_manager,
            self._dummy_double_click,
            self._dummy_tag_click,
            budget=500
        )

    def _dummy_double_click(self, item, df):
        """Callback dummy per doppio click giocatore"""
        pass

    def _dummy_tag_click(self, item, event):
        """Callback dummy per click tag"""
        pass

    def _on_team_double_click(self, event):
        """Gestisce doppio click su una squadra"""
        item = self.teams_tree.identify_row(event.y)
        if not item:
            return

        # Ottieni il nome della squadra
        values = self.teams_tree.item(item, 'values')
        if not values:
            return

        team_name = values[1]  # Colonna Squadra
        self._open_team_detail(team_name)
        player_table_ref = [None]

        # Callback per doppio click su giocatore
        def on_player_double_click(item_id):
            if player_table_ref[0]:
                metadata = player_table_ref[0].get_item_metadata(item_id)
                if metadata:
                    PlayerDetailsWindow(self.window, metadata['player_id'], self.processor, metadata['role_str'])

        # Callback per click su tag
        def on_tag_click(item_id, event):
            # Già gestito internamente da PlayerTable
            pass

        # Apri finestra dettaglio
        detail_window = TeamDetailWindow(
            self.window,
            team_name,
            team_stats,
            self.df,
            self.processor,
            price_calculator,
            player_notes_manager,
            on_player_double_click,
            on_tag_click,
            budget=500
        )

        # Salva riferimento alla player_table dopo creazione
        player_table_ref[0] = detail_window.player_table
