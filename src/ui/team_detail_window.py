"""
Finestra Dettaglio Squadra - Statistiche complete e rosa
"""
import customtkinter as ctk
import tkinter as tk
from src.ui.components.constants import COLORS
from src.ui.window_chrome import configure_application_window
from src.data.team_notes import TeamNotesManager
from src.data.player_notes import PlayerNotesManager
from src.data.favorites_manager import FavoritesManager
from src.data.price_calculator import PriceCalculator
from src.ui.components.player_table import PlayerTable


class TeamDetailWindow:
    """Finestra popup con dettaglio completo squadra"""

    def __init__(self, parent, team_name, team_stats, players_df, processor, price_calculator, player_notes_manager, on_double_click_callback, on_tag_click_callback, budget=500):
        self.team_name = team_name
        self.team_stats = team_stats or {}
        self.players_df = players_df
        self.processor = processor
        self.price_calculator = price_calculator
        self.player_notes_manager = player_notes_manager
        self.on_double_click_callback = on_double_click_callback
        self.on_tag_click_callback = on_tag_click_callback
        self.budget = budget
        self.notes_manager = TeamNotesManager()
        self.favorites_manager = FavoritesManager()

        self.player_table = None
        self._save_timer = None

        # Carica dati tiratori
        self.tiratori_data = self._load_tiratori_data()

        self.window = ctk.CTkToplevel(parent)
        configure_application_window(self.window)
        self.window.title(f"Dettaglio Squadra: {team_name}")
        self.window.configure(fg_color=COLORS['bg_primary'])
        self.window.withdraw()
        self.window.transient(parent)

        self._setup_ui()
        self.window.after(10, self._show_maximized)

    def _show_maximized(self):
        try:
            self.window.state('zoomed')
        except Exception:
            self.window.attributes('-zoomed', True)

        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()

    def _setup_ui(self):
        # Main container fisso (senza scroll generale)
        main_container = ctk.CTkFrame(
            self.window,
            fg_color=COLORS['bg_primary']
        )
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        main_container.grid_rowconfigure(2, weight=1)  # La rosa prende tutto lo spazio disponibile
        main_container.grid_columnconfigure(0, weight=1)

        self._build_header(main_container)
        self._build_stats_section(main_container)
        self._build_roster_section(main_container)

    def _build_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color=COLORS['bg_secondary'], corner_radius=15)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        content = ctk.CTkFrame(header_frame, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=15)  # Ridotto padding
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=2)

        # Colonna Sinistra - Titolo e Azioni
        name_frame = ctk.CTkFrame(content, fg_color="transparent")
        name_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        title_container = ctk.CTkFrame(name_frame, fg_color="transparent")
        title_container.pack(anchor="w")

        ctk.CTkLabel(
            title_container,
            text=f"🏆 {self.team_name}",
            font=ctk.CTkFont(size=24, weight="bold"),  # Ridotto da 28 a 24
            text_color=COLORS['accent_purple']
        ).pack(anchor="w")

        # Modulo squadra sotto al nome
        modulo = self._get_team_modulo()
        if modulo and modulo != '-':
            ctk.CTkLabel(
                title_container,
                text=f"Modulo: {modulo}",
                font=ctk.CTkFont(size=12),
                text_color=COLORS['text_secondary']
            ).pack(anchor="w")

        ctk.CTkButton(
            name_frame,
            text="✕ Chiudi",
            command=self.window.destroy,
            fg_color=COLORS['error'],
            hover_color="#D62A56",
            corner_radius=8,
            width=90,
            height=32,  # Ridotto da 36 a 32
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(10, 0))  # Ridotto padding

        # Colonna Destra - Note con salvataggio automatico
        notes_frame = ctk.CTkFrame(content, fg_color=COLORS['bg_tertiary'], corner_radius=10)
        notes_frame.grid(row=0, column=1, sticky="nsew")

        header_notes = ctk.CTkFrame(notes_frame, fg_color="transparent")
        header_notes.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            header_notes,
            text="📝 Note Squadra",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS['text_secondary']
        ).pack(side="left")

        self.status_label = ctk.CTkLabel(
            header_notes,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['accent_green']
        )
        self.status_label.pack(side="right")

        self.notes_text = ctk.CTkTextbox(
            notes_frame,
            height=60,  # Ridotto da 80 a 60
            fg_color=COLORS['bg_primary'],
            border_color=COLORS['border'],
            corner_radius=8,
            font=ctk.CTkFont(size=11)  # Ridotto da 12 a 11
        )
        self.notes_text.pack(fill="both", expand=True, padx=12, pady=(0, 8))  # Ridotto padding

        note = self.notes_manager.get_note(self.team_name) or ""
        self.notes_text.insert('1.0', note)
        
        # Auto-salvataggio quando l'utente smette di digitare o perde il focus
        self.notes_text.bind("<KeyRelease>", self._on_note_change)
        self.notes_text.bind("<FocusOut>", lambda e: self._save_note())

    def _on_note_change(self, event):
        if self._save_timer:
            self.window.after_cancel(self._save_timer)
        self._save_timer = self.window.after(800, self._save_note)

    def _save_note(self):
        note = self.notes_text.get('1.0', tk.END).strip()
        self.notes_manager.set_note(self.team_name, note)
        self.status_label.configure(text="✓ Salvato")
        self.window.after(2000, lambda: self.status_label.configure(text=""))

    def _build_stats_section(self, parent):
        # Se non ci sono statistiche (neopromossa), mostra solo un messaggio
        if not self.team_stats:
            stats_card = ctk.CTkFrame(parent, fg_color=COLORS['bg_secondary'], corner_radius=15)
            stats_card.grid(row=1, column=0, sticky="ew", pady=(0, 8))

            content = ctk.CTkFrame(stats_card, fg_color="transparent")
            content.pack(fill="x", padx=15, pady=12)

            ctk.CTkLabel(
                content,
                text="📊 STATISTICHE NON DISPONIBILI",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLORS['text_secondary']
            ).pack(anchor="w", pady=(0, 10))

            ctk.CTkLabel(
                content,
                text="Questa è una squadra neopromossa senza statistiche disponibili per la stagione corrente.",
                font=ctk.CTkFont(size=12),
                text_color=COLORS['text_secondary'],
                wraplength=800
            ).pack(anchor="w")
            return

        # Statistiche normali per squadre con dati
        stats_card = ctk.CTkFrame(parent, fg_color=COLORS['bg_secondary'], corner_radius=15)
        stats_card.grid(row=1, column=0, sticky="ew", pady=(0, 8))  # Ridotto padding

        content = ctk.CTkFrame(stats_card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=12)  # Ridotto padding

        ctk.CTkLabel(
            content,
            text="📊 STATISTICHE RIEPILOGATIVE",
            font=ctk.CTkFont(size=14, weight="bold"),  # Ridotto da 16 a 14
            text_color=COLORS['text_primary']
        ).pack(anchor="w", pady=(0, 10))  # Ridotto padding

        # Grid per le Card delle statistiche
        grid_frame = ctk.CTkFrame(content, fg_color="transparent")
        grid_frame.pack(fill="x")
        grid_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat_cards")

        # 1. Card Classifica
        classifica = self.team_stats.get('classifica', {})
        self._create_stat_card(
            grid_frame,
            title="Classifica",
            row=0, col=0,
            metrics=[
                ("Posizione", f"{classifica.get('posizione', '-')}°"),
                ("Punti", str(classifica.get('punti', '-'))),
                ("Gol Fatti/Subiti", f"{classifica.get('gol_fatti', 0)} / {classifica.get('gol_subiti', 0)}"),
                ("Diff. Reti", f"{classifica.get('differenza_reti', 0):+d}")
            ]
        )

        # 2. Card Giocatori Chiave
        key_players = self.team_stats.get('giocatori_chiave', {})
        fm_player = key_players.get('fm', {})
        gol_player = key_players.get('gol', {})
        assist_player = key_players.get('assist', {})

        self._create_stat_card(
            grid_frame,
            title="Giocatori Chiave",
            row=0, col=1,
            metrics=[
                ("Migliore FM", f"{fm_player.get('nome', '-')} ({fm_player.get('fm', 0):.2f})"),
                ("Capocannoniere", f"{gol_player.get('nome', '-')} ({gol_player.get('gol', 0)} gol)"),
                ("Top Assist", f"{assist_player.get('nome', '-')} ({assist_player.get('assist', 0)} assist)")
            ]
        )

        # 3. Card Medie Reparti
        reparti = self.team_stats.get('reparti', {}).get('dettaglio', {})
        top_reparto = self.team_stats.get('reparti', {}).get('reparto_piu_forte', {})

        reparto_metrics = [
            (self._get_reparto_name(code), f"FM: {reparti.get(code, {}).get('fm_media', 0):.2f} ({reparti.get(code, {}).get('giocatori', 0)})")
            for code in ['P', 'D', 'C', 'A']
        ]

        if top_reparto.get('reparto'):
            reparto_metrics.insert(0, ("Top Reparto", f"{self._get_reparto_name(top_reparto['reparto'])} ({top_reparto.get('fm_media', 0):.2f})"))

        self._create_stat_card(
            grid_frame,
            title="FM Reparti (min. 10 pres.)",
            row=0, col=2,
            metrics=reparto_metrics
        )

        # 4. Card Tiratori (Rigori e Piazzati)
        tiratori_team = self._get_tiratori_team()
        if tiratori_team:
            rigoristi = tiratori_team.get('rigoristi', {})
            piazzati = tiratori_team.get('piazzati_e_angoli', {})

            tiratori_metrics = []

            # Rigori
            if rigoristi.get('1_rigorista'):
                tiratori_metrics.append(("1° Rigorista", rigoristi['1_rigorista']))
            if rigoristi.get('2_rigorista'):
                tiratori_metrics.append(("2° Rigorista", rigoristi['2_rigorista']))

            # Piazzati
            if piazzati.get('1_tiratore'):
                tiratori_metrics.append(("1° Piazzati", piazzati['1_tiratore']))
            if piazzati.get('2_tiratore'):
                tiratori_metrics.append(("2° Piazzati", piazzati['2_tiratore']))

            self._create_stat_card(
                grid_frame,
                title="Tiratori",
                row=0, col=3,
                metrics=tiratori_metrics if tiratori_metrics else [("N/A", "Nessun dato")]
            )
        else:
            # Card vuota se non ci sono dati
            self._create_stat_card(
                grid_frame,
                title="Tiratori",
                row=0, col=3,
                metrics=[("N/A", "Nessun dato")]
            )

    def _create_stat_card(self, parent, title, row, col, metrics):
        """Helper per creare card statistiche dall'aspetto moderno"""
        card = ctk.CTkFrame(parent, fg_color=COLORS['bg_tertiary'], corner_radius=10)
        card.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['accent_blue']
        ).pack(anchor="w", padx=12, pady=(10, 8))

        for label, val in metrics:
            row_frame = ctk.CTkFrame(card, fg_color="transparent")
            row_frame.pack(fill="x", padx=12, pady=2)

            ctk.CTkLabel(
                row_frame,
                text=label,
                font=ctk.CTkFont(size=12),
                text_color=COLORS['text_secondary']
            ).pack(side="left")

            ctk.CTkLabel(
                row_frame,
                text=str(val),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS['text_primary']
            ).pack(side="right")

    def _build_roster_section(self, parent):
        """Sezione rosa giocatori - con scroll indipendente"""
        roster_card = ctk.CTkFrame(parent, fg_color=COLORS['bg_secondary'], corner_radius=15)
        roster_card.grid(row=2, column=0, sticky="nsew")  # nsew per espandersi

        content = ctk.CTkFrame(roster_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=12)  # Ridotto padding

        ctk.CTkLabel(
            content,
            text="👥 ROSA COMPLETA",
            font=ctk.CTkFont(size=14, weight="bold"),  # Ridotto da 16 a 14
            text_color=COLORS['text_primary']
        ).pack(anchor="w", pady=(0, 8))  # Ridotto padding

        team_players = self.players_df[self.players_df['Squadra'] == self.team_name].copy()

        self.player_table = PlayerTable(
            content,
            team_players,
            self.price_calculator,
            self.player_notes_manager,
            self.on_double_click_callback,
            self.on_tag_click_callback,
            favorites_manager=self.favorites_manager,
            show_title=False  # Nascondi titolo "Lista Giocatori"
        )

        roster_frame = self.player_table.create()
        roster_frame.pack(fill="both", expand=True)
        self.player_table.populate(team_players, self.budget)

    def _get_reparto_name(self, code):
        names = {'P': 'Portieri', 'D': 'Difensori', 'C': 'Centrocampisti', 'A': 'Attaccanti'}
        return names.get(code, code)

    def _load_tiratori_data(self):
        """Carica i dati dei tiratori dal file JSON"""
        import json
        import os

        tiratori_file = os.path.join('data', 'Tiratori', 'Tiratori.json')

        if not os.path.exists(tiratori_file):
            return []

        try:
            with open(tiratori_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Errore nel caricamento tiratori: {e}")
            return []

    def _get_tiratori_team(self):
        """Restituisce i dati dei tiratori per la squadra corrente"""
        for team_data in self.tiratori_data:
            if team_data.get('squadra') == self.team_name:
                return team_data
        return None

    def _get_team_modulo(self):
        """Restituisce il modulo della squadra dal file modulo.json"""
        import json
        import os

        modulo_file = os.path.join('data', 'Moduli', 'modulo.json')
        if not os.path.exists(modulo_file):
            return '-'

        try:
            with open(modulo_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for team in data:
                    if team.get('squadra') == self.team_name:
                        return team.get('modulo', '-')
                return '-'
        except Exception as e:
            print(f"Errore caricamento modulo: {e}")
            return '-'


class CompactTeamDetailWindow(TeamDetailWindow):
    """Versione compatta della finestra dettaglio squadra (1/4 schermo)"""

    def _setup_ui(self):
        """Setup interfaccia con scroll per versione compatta"""
        # Main container per scrollable frame e tabella separata
        main_container = ctk.CTkFrame(self.window, fg_color=COLORS['bg_primary'])
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_columnconfigure(0, weight=1)

        # Scrollable frame per header e stats (in alto)
        scrollable_frame = ctk.CTkScrollableFrame(
            main_container,
            fg_color=COLORS['bg_primary'],
            scrollbar_button_color=COLORS['accent_purple'],
            scrollbar_button_hover_color=COLORS['accent_blue']
        )
        scrollable_frame.grid(row=0, column=0, sticky="ew")
        scrollable_frame.grid_columnconfigure(0, weight=1)

        self._build_header(scrollable_frame)
        self._build_stats_section(scrollable_frame)

        # Frame separato per la tabella (in basso, con scroll indipendente)
        table_container = ctk.CTkFrame(main_container, fg_color="transparent")
        table_container.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self._build_roster_section(table_container)

    def _build_header(self, parent):
        """Header compatto"""
        header_frame = ctk.CTkFrame(parent, fg_color=COLORS['bg_secondary'], corner_radius=15)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        content = ctk.CTkFrame(header_frame, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=15)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=2)

        # Colonna Sinistra - Titolo e Azioni
        name_frame = ctk.CTkFrame(content, fg_color="transparent")
        name_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        title_container = ctk.CTkFrame(name_frame, fg_color="transparent")
        title_container.pack(anchor="w")

        ctk.CTkLabel(
            title_container,
            text=f"🏆 {self.team_name}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS['accent_purple']
        ).pack(anchor="w")

        # Modulo squadra sotto al nome
        modulo = self._get_team_modulo()
        if modulo and modulo != '-':
            ctk.CTkLabel(
                title_container,
                text=f"Modulo: {modulo}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS['text_secondary']
            ).pack(anchor="w")

        ctk.CTkButton(
            name_frame,
            text="✕ Chiudi",
            command=self.window.destroy,
            fg_color=COLORS['error'],
            hover_color="#D62A56",
            corner_radius=8,
            width=80,
            height=28,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", pady=(8, 0))

        # Colonna Destra - Note compatte
        notes_frame = ctk.CTkFrame(content, fg_color=COLORS['bg_tertiary'], corner_radius=10)
        notes_frame.grid(row=0, column=1, sticky="nsew")

        header_notes = ctk.CTkFrame(notes_frame, fg_color="transparent")
        header_notes.pack(fill="x", padx=12, pady=(8, 3))

        ctk.CTkLabel(
            header_notes,
            text="📝 Note Squadra",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS['text_secondary']
        ).pack(side="left")

        self.status_label = ctk.CTkLabel(
            header_notes,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=COLORS['accent_green']
        )
        self.status_label.pack(side="right")

        self.notes_text = ctk.CTkTextbox(
            notes_frame,
            height=50,
            fg_color=COLORS['bg_primary'],
            border_color=COLORS['border'],
            corner_radius=8,
            font=ctk.CTkFont(size=10)
        )
        self.notes_text.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        note = self.notes_manager.get_note(self.team_name) or ""
        self.notes_text.insert('1.0', note)

        self.notes_text.bind("<KeyRelease>", self._on_note_change)
        self.notes_text.bind("<FocusOut>", lambda e: self._save_note())

    def _build_stats_section(self, parent):
        """Sezione statistiche compatta"""
        stats_card = ctk.CTkFrame(parent, fg_color=COLORS['bg_secondary'], corner_radius=15)
        stats_card.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        content = ctk.CTkFrame(stats_card, fg_color="transparent")
        content.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            content,
            text="📊 STATISTICHE RIEPILOGATIVE",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(anchor="w", pady=(0, 8))

        # Grid compatta per le Card (4 colonne per includere tiratori)
        grid_frame = ctk.CTkFrame(content, fg_color="transparent")
        grid_frame.pack(fill="x")
        grid_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat_cards")

        # Classifica
        classifica = self.team_stats.get('classifica', {})
        self._create_stat_card(
            grid_frame,
            title="Classifica",
            row=0, col=0,
            metrics=[
                ("Posizione", f"{classifica.get('posizione', 'N/A')}°"),
                ("Punti", classifica.get('punti', 'N/A')),
                ("Gol Fatti", classifica.get('gol_fatti', 'N/A')),
                ("Gol Subiti", classifica.get('gol_subiti', 'N/A'))
            ]
        )

        # Giocatori Chiave
        key_players = self.team_stats.get('giocatori_chiave', {})
        fm_player = key_players.get('fm', {})
        gol_player = key_players.get('gol', {})
        assist_player = key_players.get('assist', {})

        self._create_stat_card(
            grid_frame,
            title="Giocatori Chiave",
            row=0, col=1,
            metrics=[
                ("Migliore FM", f"{fm_player.get('nome', '-')} ({fm_player.get('fm', 0):.2f})"),
                ("Capocannoniere", f"{gol_player.get('nome', '-')} ({gol_player.get('gol', 0)} gol)"),
                ("Top Assist", f"{assist_player.get('nome', '-')} ({assist_player.get('assist', 0)} assist)")
            ]
        )

        # Medie Reparti
        reparti = self.team_stats.get('reparti', {}).get('dettaglio', {})
        top_reparto = self.team_stats.get('reparti', {}).get('reparto_piu_forte', {})

        reparto_metrics = [
            (self._get_reparto_name(code), f"FM: {reparti.get(code, {}).get('fm_media', 0):.2f}")
            for code in ['P', 'D', 'C', 'A']
        ]

        if top_reparto.get('reparto'):
            reparto_metrics.insert(0, ("Top Reparto", f"{self._get_reparto_name(top_reparto['reparto'])} ({top_reparto.get('fm_media', 0):.2f})"))

        self._create_stat_card(
            grid_frame,
            title="FM Reparti",
            row=0, col=2,
            metrics=reparto_metrics
        )

        # Tiratori (Rigori e Piazzati)
        tiratori_team = self._get_tiratori_team()
        if tiratori_team:
            rigoristi = tiratori_team.get('rigoristi', {})
            piazzati = tiratori_team.get('piazzati_e_angoli', {})

            tiratori_metrics = []

            if rigoristi.get('1_rigorista'):
                tiratori_metrics.append(("1° Rigorista", rigoristi['1_rigorista']))
            if piazzati.get('1_tiratore'):
                tiratori_metrics.append(("1° Piazzati", piazzati['1_tiratore']))

            self._create_stat_card(
                grid_frame,
                title="Tiratori",
                row=0, col=3,
                metrics=tiratori_metrics if tiratori_metrics else [("N/A", "Nessun dato")]
            )
        else:
            self._create_stat_card(
                grid_frame,
                title="Tiratori",
                row=0, col=3,
                metrics=[("N/A", "Nessun dato")]
            )

    def _create_stat_card(self, parent, title, row, col, metrics):
        """Helper per creare card statistiche compatte"""
        card = ctk.CTkFrame(parent, fg_color=COLORS['bg_tertiary'], corner_radius=10)
        card.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS['accent_blue']
        ).pack(anchor="w", padx=10, pady=(8, 5))

        for label, val in metrics:
            row_frame = ctk.CTkFrame(card, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=1)

            ctk.CTkLabel(
                row_frame,
                text=label,
                font=ctk.CTkFont(size=10),
                text_color=COLORS['text_secondary']
            ).pack(side="left")

            ctk.CTkLabel(
                row_frame,
                text=str(val),
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=COLORS['text_primary']
            ).pack(side="right")

    def _build_roster_section(self, parent):
        """Sezione rosa compatta con scroll orizzontale"""
        roster_card = ctk.CTkFrame(parent, fg_color=COLORS['bg_secondary'], corner_radius=15)
        roster_card.pack(fill="both", expand=True)

        content = ctk.CTkFrame(roster_card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=10)

        ctk.CTkLabel(
            content,
            text="👥 ROSA COMPLETA",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(anchor="w", pady=(0, 6))

        team_players = self.players_df[self.players_df['Squadra'] == self.team_name].copy()

        self.player_table = PlayerTable(
            content,
            team_players,
            self.price_calculator,
            self.player_notes_manager,
            self.on_double_click_callback,
            self.on_tag_click_callback,
            favorites_manager=self.favorites_manager,
            enable_horizontal_scroll=True,  # Abilita scroll orizzontale per versione compatta
            show_title=False  # Nascondi titolo "Lista Giocatori"
        )

        roster_frame = self.player_table.create()
        roster_frame.pack(fill="both", expand=True)
        self.player_table.populate(team_players, self.budget)

    def _show_maximized(self):
        """Mostra la finestra in modalità compatta (1/4 schermo) invece di massimizzata"""
        # Dimensioni 1/4 schermo
        window_width = 600
        window_height = 500

        # Ottieni dimensioni schermo
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        # Posiziona in basso a destra
        pos_x = screen_width - window_width - 50
        pos_y = screen_height - window_height - 100

        # Imposta geometria e mostra
        self.window.geometry(f'{window_width}x{window_height}+{pos_x}+{pos_y}')
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()