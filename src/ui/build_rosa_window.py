"""
Finestra Build Rosa - Costruzione guidata della rosa
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import json
from pathlib import Path
from src.ui.components.constants import COLORS
from src.ui.window_chrome import configure_application_window
from src.logic.knapsack_optimizer import KnapsackOptimizer


class BuildRosaWindow:
    """Finestra per costruire una rosa personalizzata"""

    def __init__(self, parent, df, budget, price_calculator, favorites_manager=None, on_favorites_update=None):
        """
        Inizializza finestra Build Rosa

        Args:
            parent: Finestra genitore
            df: DataFrame con tutti i giocatori
            budget: Budget totale disponibile
            price_calculator: Calcolatore prezzi
            favorites_manager: Manager dei preferiti
            on_favorites_update: Callback per aggiornare conteggio preferiti
        """
        self.parent = parent
        self.df = df
        self.budget = budget
        self.price_calculator = price_calculator
        self.favorites_manager = favorites_manager
        self.on_favorites_update = on_favorites_update

        # Inizializza ottimizzatore
        self.optimizer = KnapsackOptimizer(df, price_calculator, budget)

        # Stato della rosa
        self.rosa_composition = {
            'P': 3,
            'D': 8,
            'C': 8,
            'A': 6
        }

        self.selected_players = {}  # {position_index: player_id}
        self.price_range = "90%-100%"
        self.value_priority = "FM"

        # Budget per reparto (%)
        self.budget_per_role = self._load_budget_preferences()

        # Crediti iniziali personalizzati per giocatore
        self.custom_credits = {}  # {position_index: crediti}

        # Traccia giocatori aggiunti dall'algoritmo
        self.auto_generated_positions = set()

        # Blacklist squadre
        self.blacklisted_teams = set()

        # Finestra
        self.window = ctk.CTkToplevel(parent)
        configure_application_window(self.window)
        self.window.title("🏗️ Build Rosa")
        self.window.configure(fg_color=COLORS['bg_primary'])

        # Nascondi durante setup
        self.window.withdraw()

        # Apri sopra la finestra principale
        self.window.transient(parent)

        # Widget
        self.composition_widgets = {}
        self.budget_role_widgets = {}
        self.budget_sum_label = None
        self.initial_budget_var = None
        self.player_combos = []
        self.stats_labels = {}

        self.setup_ui()

        # Mostra centrata dopo setup (stessa dimensione e posizione di confronto giocatori)
        self.window.after(10, self._show_centered)

    def _show_centered(self):
        """Mostra la finestra centrata con stesse dimensioni di confronto giocatori"""
        # Imposta dimensioni (stesse di player_comparison)
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

    def _load_budget_preferences(self) -> dict:
        """Carica preferenze budget da file"""
        preferences_path = Path('data/budget_preferences.json')

        # Valori di default
        default_budget = {
            'P': 15.0,
            'D': 30.0,
            'C': 30.0,
            'A': 25.0
        }

        if preferences_path.exists():
            try:
                with open(preferences_path, 'r', encoding='utf-8') as f:
                    saved_prefs = json.load(f)
                    return saved_prefs.get('budget_per_role', default_budget)
            except Exception:
                pass

        return default_budget

    def _save_budget_preferences(self):
        """Salva preferenze budget su file"""
        preferences_path = Path('data/budget_preferences.json')

        try:
            preferences_path.parent.mkdir(parents=True, exist_ok=True)

            with open(preferences_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'budget_per_role': self.budget_per_role
                }, f, indent=2)
        except Exception as e:
            print(f"Errore salvataggio preferenze: {e}")
        self.window.grab_set()

    def setup_ui(self):
        """Configura interfaccia utente"""
        # Container principale scrollabile
        main_scroll = ctk.CTkScrollableFrame(
            self.window,
            fg_color="transparent"
        )
        main_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header_frame = ctk.CTkFrame(main_scroll, fg_color=COLORS['bg_secondary'], corner_radius=15)
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = ctk.CTkLabel(
            header_frame,
            text="🏗️ Costruisci la tua Rosa",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS['accent_purple']
        )
        title_label.pack(pady=15)

        # Composizione Rosa (filtri)
        self.create_composition_section(main_scroll)

        # Budget per Reparto
        self.create_budget_section(main_scroll)

        # Statistiche Rosa
        self.create_stats_section(main_scroll)

        # Lista giocatori
        self.create_players_list_section(main_scroll)

        # Filtri generazione e bottone
        self.create_generation_section(main_scroll)

    def create_composition_section(self, parent):
        """Crea sezione composizione rosa"""
        comp_frame = ctk.CTkFrame(parent, fg_color=COLORS['bg_secondary'], corner_radius=15)
        comp_frame.pack(fill="x", pady=(0, 15))

        title = ctk.CTkLabel(
            comp_frame,
            text="⚙️ Composizione Rosa",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text_primary']
        )
        title.pack(pady=(15, 10))

        # Grid per i filtri
        filters_grid = ctk.CTkFrame(comp_frame, fg_color="transparent")
        filters_grid.pack(pady=(0, 15), padx=20)

        roles = [
            ('Portieri', 'P', [1, 2, 3, 4]),
            ('Difensori', 'D', [6, 7, 8, 9, 10]),
            ('Centrocampisti', 'C', [6, 7, 8, 9, 10]),
            ('Attaccanti', 'A', [4, 5, 6, 7, 8])
        ]

        for i, (label, role_key, options) in enumerate(roles):
            role_frame = ctk.CTkFrame(filters_grid, fg_color="transparent")
            role_frame.grid(row=0, column=i, padx=10, pady=5)

            role_label = ctk.CTkLabel(
                role_frame,
                text=label,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLORS['text_secondary']
            )
            role_label.pack()

            combo = ctk.CTkComboBox(
                role_frame,
                values=[str(x) for x in options],
                width=120,
                height=35,
                fg_color=COLORS['bg_tertiary'],
                button_color=COLORS['accent_purple'],
                button_hover_color=COLORS['accent_blue'],
                border_color=COLORS['border'],
                command=lambda v, r=role_key: self.on_composition_change(r, v)
            )
            combo.set(str(self.rosa_composition[role_key]))
            combo.pack(pady=(5, 0))

            self.composition_widgets[role_key] = combo

    def create_budget_section(self, parent):
        """Crea sezione budget per reparto"""
        budget_frame = ctk.CTkFrame(parent, fg_color=COLORS['bg_secondary'], corner_radius=15)
        budget_frame.pack(fill="x", pady=(0, 15))

        title = ctk.CTkLabel(
            budget_frame,
            text="💰 Budget per Reparto (%)",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text_primary']
        )
        title.pack(pady=(15, 10))

        # Grid per i filtri budget
        budget_grid = ctk.CTkFrame(budget_frame, fg_color="transparent")
        budget_grid.pack(pady=(0, 10), padx=20)

        roles = [
            ('Portieri', 'P'),
            ('Difensori', 'D'),
            ('Centrocampisti', 'C'),
            ('Attaccanti', 'A'),
            ('Crediti Iniziali', 'CREDITS')
        ]

        for i, (label, role_key) in enumerate(roles):
            role_frame = ctk.CTkFrame(budget_grid, fg_color="transparent")
            role_frame.grid(row=0, column=i, padx=10, pady=5)

            role_label = ctk.CTkLabel(
                role_frame,
                text=label,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLORS['text_secondary']
            )
            role_label.pack()

            if role_key == 'CREDITS':
                # Campo crediti iniziali
                self.initial_budget_var = tk.StringVar(value=str(self.budget))
                credits_entry = ctk.CTkEntry(
                    role_frame,
                    textvariable=self.initial_budget_var,
                    width=100,
                    height=35,
                    fg_color=COLORS['bg_tertiary'],
                    border_color=COLORS['border'],
                    font=ctk.CTkFont(size=14)
                )
                credits_entry.pack(pady=(5, 0))
                credits_entry.bind('<KeyRelease>', lambda e: self.on_initial_budget_change())
            else:
                # Entry per budget percentuale
                budget_var = tk.StringVar(value=str(self.budget_per_role[role_key]))
                budget_entry = ctk.CTkEntry(
                    role_frame,
                    textvariable=budget_var,
                    width=100,
                    height=35,
                    fg_color=COLORS['bg_tertiary'],
                    border_color=COLORS['border'],
                    font=ctk.CTkFont(size=14)
                )
                budget_entry.pack(pady=(5, 0))
                budget_entry.bind('<KeyRelease>', lambda e, r=role_key: self.on_budget_change(r))

                self.budget_role_widgets[role_key] = budget_var

        # Label somma totale
        sum_frame = ctk.CTkFrame(budget_frame, fg_color=COLORS['bg_tertiary'], corner_radius=10)
        sum_frame.pack(pady=(10, 15), padx=20)

        sum_label_text = ctk.CTkLabel(
            sum_frame,
            text="Totale Budget Allocato:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_secondary']
        )
        sum_label_text.pack(side="left", padx=15, pady=10)

        self.budget_sum_label = ctk.CTkLabel(
            sum_frame,
            text="100.0%",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['accent_green']
        )
        self.budget_sum_label.pack(side="right", padx=15, pady=10)

        self.update_budget_sum()

    def on_initial_budget_change(self):
        """Callback quando cambiano i crediti iniziali"""
        try:
            new_budget = float(self.initial_budget_var.get())
            self.budget = new_budget
            self.optimizer = KnapsackOptimizer(self.df, self.price_calculator, new_budget)
            self.update_statistics()
        except ValueError:
            pass

    def on_budget_change(self, role_key):
        """Callback quando cambia budget di un reparto"""
        self.update_budget_sum()

    def update_budget_sum(self):
        """Aggiorna visualizzazione somma budget"""
        total = 0.0
        for role_key in ['P', 'D', 'C', 'A']:
            try:
                value = float(self.budget_role_widgets[role_key].get())
                self.budget_per_role[role_key] = value
                total += value
            except ValueError:
                pass

        # Salva preferenze ogni volta che cambiano
        self._save_budget_preferences()

        # Aggiorna label con colore in base al totale
        self.budget_sum_label.configure(text=f"{total:.1f}%")

        if abs(total - 100.0) < 0.1:
            # Perfetto
            self.budget_sum_label.configure(text_color=COLORS['accent_green'])
        elif total > 100:
            # Troppo
            self.budget_sum_label.configure(text_color="#FF4444")
        else:
            # Sotto
            self.budget_sum_label.configure(text_color=COLORS['accent_yellow'])

    def create_stats_section(self, parent):
        """Crea sezione statistiche rosa"""
        stats_frame = ctk.CTkFrame(parent, fg_color=COLORS['bg_secondary'], corner_radius=15)
        stats_frame.pack(fill="x", pady=(0, 15))

        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(pady=15, padx=20)

        # % Prezzo Max
        price_frame = ctk.CTkFrame(stats_grid, fg_color=COLORS['bg_tertiary'], corner_radius=10)
        price_frame.grid(row=0, column=0, padx=20, pady=5, sticky="ew")

        price_label = ctk.CTkLabel(
            price_frame,
            text="💰 % Prezzo Max Totale:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_secondary']
        )
        price_label.pack(side="left", padx=15, pady=10)

        self.stats_labels['price_pct'] = ctk.CTkLabel(
            price_frame,
            text="0.0%",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['accent_green']
        )
        self.stats_labels['price_pct'].pack(side="right", padx=15, pady=10)

        # Overall Medio
        overall_frame = ctk.CTkFrame(stats_grid, fg_color=COLORS['bg_tertiary'], corner_radius=10)
        overall_frame.grid(row=0, column=1, padx=20, pady=5, sticky="ew")

        overall_label = ctk.CTkLabel(
            overall_frame,
            text="⭐ Overall Medio:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_secondary']
        )
        overall_label.pack(side="left", padx=15, pady=10)

        self.stats_labels['overall_avg'] = ctk.CTkLabel(
            overall_frame,
            text="0.0",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['accent_yellow']
        )
        self.stats_labels['overall_avg'].pack(side="right", padx=15, pady=10)

        stats_grid.columnconfigure(0, weight=1)
        stats_grid.columnconfigure(1, weight=1)

    def create_players_list_section(self, parent):
        """Crea sezione lista giocatori"""
        list_frame = ctk.CTkFrame(parent, fg_color=COLORS['bg_secondary'], corner_radius=15)
        list_frame.pack(fill="x", pady=(0, 15))

        title = ctk.CTkLabel(
            list_frame,
            text="👥 Rosa",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text_primary']
        )
        title.pack(pady=(15, 10))

        # Container non scrollabile (la scrollbar è sul main_scroll)
        players_inner = ctk.CTkFrame(
            list_frame,
            fg_color=COLORS['bg_tertiary'],
            corner_radius=10
        )
        players_inner.pack(fill="x", padx=15, pady=(0, 15))

        self.players_container = players_inner
        self.rebuild_player_list()

    def create_generation_section(self, parent):
        """Crea sezione generazione rosa"""
        gen_frame = ctk.CTkFrame(parent, fg_color=COLORS['bg_secondary'], corner_radius=15)
        gen_frame.pack(fill="x", pady=(0, 15))

        title = ctk.CTkLabel(
            gen_frame,
            text="⚙️ Generazione Automatica",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text_primary']
        )
        title.pack(pady=(15, 10))

        controls_frame = ctk.CTkFrame(gen_frame, fg_color="transparent")
        controls_frame.pack(pady=(0, 15), padx=20)

        # Filtro Valore Principale
        value_filter_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        value_filter_frame.grid(row=0, column=0, padx=10, sticky="ew")

        value_label = ctk.CTkLabel(
            value_filter_frame,
            text="📊 Valore Prioritario:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS['text_secondary']
        )
        value_label.pack()

        self.value_priority_combo = ctk.CTkComboBox(
            value_filter_frame,
            values=["FM", "MV", "PV"],
            width=140,
            fg_color=COLORS['bg_tertiary'],
            button_color=COLORS['accent_green'],
            border_color=COLORS['border']
        )
        self.value_priority_combo.set("FM")
        self.value_priority_combo.pack(pady=(5, 0))

        # Filtro Blacklist Squadre
        blacklist_filter_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        blacklist_filter_frame.grid(row=0, column=1, padx=10, sticky="ew")

        blacklist_label = ctk.CTkLabel(
            blacklist_filter_frame,
            text="🚫 Escludi Squadre:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS['text_secondary']
        )
        blacklist_label.pack()

        # Ottieni lista squadre
        teams = ["Nessuna"] + sorted(self.df['Squadra'].unique().tolist()) if self.df is not None else ["Nessuna"]

        self.blacklist_combo = ctk.CTkComboBox(
            blacklist_filter_frame,
            values=teams,
            width=140,
            fg_color=COLORS['bg_tertiary'],
            button_color=COLORS['error'],
            border_color=COLORS['border'],
            command=self.on_blacklist_change
        )
        self.blacklist_combo.set("Nessuna")
        self.blacklist_combo.pack(pady=(5, 0))

        # Bottone Genera Rosa allineato
        generate_btn_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        generate_btn_frame.grid(row=0, column=2, padx=10, sticky="ew")

        # Spacer per allineare verticalmente
        ctk.CTkLabel(generate_btn_frame, text="", height=20).pack()

        generate_btn = ctk.CTkButton(
            generate_btn_frame,
            text="✨ Genera Rosa",
            command=self.generate_rosa,
            height=40,
            width=160,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=COLORS['accent_green'],
            hover_color=COLORS['success'],
            corner_radius=10
        )
        generate_btn.pack()

        # Label squadre escluse sotto i controlli
        self.blacklist_label = ctk.CTkLabel(
            gen_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['warning']
        )
        self.blacklist_label.pack(pady=(0, 10))

        # Espandi colonne uniformemente
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=1)
        controls_frame.grid_columnconfigure(2, weight=1)

    def on_blacklist_change(self, team):
        """Gestisce aggiunta/rimozione squadre dalla blacklist"""
        if team == "Nessuna":
            return

        if team in self.blacklisted_teams:
            self.blacklisted_teams.remove(team)
        else:
            self.blacklisted_teams.add(team)

        # Aggiorna label
        if self.blacklisted_teams:
            teams_text = ", ".join(sorted(self.blacklisted_teams))
            self.blacklist_label.configure(text=f"Escluse: {teams_text}")
        else:
            self.blacklist_label.configure(text="")

    def on_composition_change(self, role, value):
        """Gestisce cambio composizione rosa"""
        self.rosa_composition[role] = int(value)
        self.rebuild_player_list()
        self.update_statistics()

    def on_custom_cost_change(self, position_index):
        """Callback quando l'utente modifica il costo di un giocatore"""
        try:
            combo_info = self.player_combos[position_index]
            cost_value = combo_info['cost_entry'].get()

            if cost_value:  # Se c'è un valore
                custom_cost = float(cost_value)
                self.custom_credits[position_index] = custom_cost
            else:  # Se è vuoto, rimuovi il costo personalizzato
                if position_index in self.custom_credits:
                    del self.custom_credits[position_index]

            self.update_statistics()
        except ValueError:
            # Valore non valido, ignora
            if position_index in self.custom_credits:
                del self.custom_credits[position_index]

    def toggle_favorite(self, position_index):
        """Aggiungi/rimuovi giocatore dai preferiti"""
        if position_index not in self.selected_players:
            messagebox.showinfo("Nessun Giocatore", "Seleziona prima un giocatore per questa posizione")
            return

        player_id = self.selected_players[position_index]['id']

        # Usa il manager dei preferiti passato o creane uno nuovo
        if self.favorites_manager:
            fav_manager = self.favorites_manager
        else:
            from src.data.favorites_manager import FavoritesManager
            fav_manager = FavoritesManager()

        # Toggle (usa il metodo corretto)
        was_favorite = fav_manager.is_favorite(player_id)
        fav_manager.toggle_favorite(player_id)

        # Aggiorna UI
        if was_favorite:
            # Era preferito, ora non lo è più
            self.player_combos[position_index]['fav_btn'].configure(
                fg_color=COLORS['bg_tertiary']
            )
        else:
            # Non era preferito, ora lo è
            self.player_combos[position_index]['fav_btn'].configure(
                fg_color=COLORS['accent_yellow']
            )

        # Chiama callback per aggiornare conteggio nella finestra principale
        if self.on_favorites_update:
            self.on_favorites_update()

    def rebuild_player_list(self):
        """Ricostruisce lista giocatori in base alla composizione"""
        # Pulisci container
        for widget in self.players_container.winfo_children():
            widget.destroy()

        self.player_combos = []
        position_index = 0

        roles_order = [
            ('PORTIERI', 'P'),
            ('DIFENSORI', 'D'),
            ('CENTROCAMPISTI', 'C'),
            ('ATTACCANTI', 'A')
        ]

        for role_name, role_key in roles_order:
            count = self.rosa_composition[role_key]

            # Separatore
            separator = ctk.CTkFrame(
                self.players_container,
                fg_color=COLORS['accent_purple'],
                height=3
            )
            separator.pack(fill="x", pady=(10, 5))

            # Titolo reparto
            role_title = ctk.CTkLabel(
                self.players_container,
                text=f"📌 {role_name}",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=COLORS['accent_purple']
            )
            role_title.pack(pady=(5, 10))

            # Giocatori del reparto
            for i in range(count):
                self.create_player_row(position_index, role_key)
                position_index += 1

    def create_player_row(self, position_index, role):
        """Crea riga per selezione giocatore"""
        row_frame = ctk.CTkFrame(
            self.players_container,
            fg_color=COLORS['bg_primary'],
            corner_radius=8
        )
        row_frame.pack(fill="x", pady=3, padx=5)

        # Numero posizione
        pos_label = ctk.CTkLabel(
            row_frame,
            text=f"{position_index + 1}.",
            width=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['text_secondary']
        )
        pos_label.pack(side="left", padx=(10, 5))

        # Info giocatore (o placeholder) - clickabile
        info_label = ctk.CTkButton(
            row_frame,
            text="Clicca per selezionare giocatore...",
            width=450,
            height=32,
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary'],
            fg_color=COLORS['bg_secondary'],
            hover_color=COLORS['bg_tertiary'],
            corner_radius=6,
            anchor="w",
            command=lambda idx=position_index, r=role: self.open_player_selector_popup(idx, r)
        )
        info_label.pack(side="left", padx=5, pady=8)

        # Campo costo in crediti (senza textvariable per mostrare placeholder)
        cost_entry = ctk.CTkEntry(
            row_frame,
            placeholder_text="Prezzo",
            width=80,
            height=32,
            fg_color=COLORS['bg_tertiary'],
            border_width=1,
            border_color=COLORS['border'],
            font=ctk.CTkFont(size=11)
        )
        cost_entry.pack(side="left", padx=5)
        cost_entry.bind('<KeyRelease>', lambda e, idx=position_index: self.on_custom_cost_change(idx))

        # Bottone Preferiti (controlla se già preferito)
        fav_btn_color = COLORS['bg_tertiary']
        if position_index in self.selected_players:
            player_id = self.selected_players[position_index]['id']
            if self.favorites_manager and self.favorites_manager.is_favorite(player_id):
                fav_btn_color = COLORS['accent_yellow']

        fav_btn = ctk.CTkButton(
            row_frame,
            text="⭐",
            width=40,
            height=32,
            fg_color=fav_btn_color,
            hover_color=COLORS['accent_yellow'],
            command=lambda idx=position_index: self.toggle_favorite(idx)
        )
        fav_btn.pack(side="left", padx=5)

        # Bottone rimuovi
        remove_btn = ctk.CTkButton(
            row_frame,
            text="🗑️",
            width=40,
            height=32,
            fg_color=COLORS['error'],
            hover_color=COLORS['accent_pink'],
            command=lambda idx=position_index: self.remove_player(idx)
        )
        remove_btn.pack(side="right", padx=10)

        self.player_combos.append({
            'info_label': info_label,
            'cost_entry': cost_entry,
            'fav_btn': fav_btn,
            'role': role,
            'position': position_index,
            'row_frame': row_frame
        })

    def get_players_by_role(self, role):
        """Ottiene lista giocatori per ruolo"""
        if self.df is None or self.df.empty:
            return []

        # Filtra giocatori per ruolo
        # role può essere 'P', 'D', 'C', 'A'
        players = self.df[self.df['R'].str.startswith(role, na=False)].copy()

        # Ordina per Overall decrescente
        if 'Overall' in players.columns and not players.empty:
            # Converti Overall a numeric, gestendo eventuali valori non numerici
            players['Overall'] = pd.to_numeric(players['Overall'], errors='coerce')
            players = players.sort_values('Overall', ascending=False)

        return players.to_dict('records')

    def format_player_display(self, player):
        """Formatta display giocatore per combobox"""
        nome = player.get('Nome', 'N/A')
        role = player.get('R', 'N/A')
        squadra = player.get('Squadra', 'N/A')
        overall = player.get('Overall', 0)

        # Calcola prezzo max
        player_id = player.get('Id')
        price_data = self.price_calculator.calculate_price(player_id, self.budget)
        price_max = price_data.get('price_max', 0) if price_data else 0

        return f"{nome} | {role} | {squadra} | OVR: {overall:.1f} | €{price_max}"

    def open_player_selector_popup(self, position_index, role):
        """Apre popup per selezionare giocatore con ricerca e filtri"""
        # Ottieni giocatori del ruolo
        players_list = self.get_players_by_role(role)

        if not players_list:
            messagebox.showwarning(
                "Nessun Giocatore",
                f"Nessun giocatore disponibile per il ruolo {role}"
            )
            return

        # Crea popup
        popup = ctk.CTkToplevel(self.window)
        configure_application_window(popup)
        popup.title(f"Seleziona Giocatore - Posizione {position_index + 1}")
        popup.geometry("700x600")
        popup.configure(fg_color=COLORS['bg_primary'])

        # Centra popup
        popup.update_idletasks()
        x = popup.winfo_screenwidth() // 2 - 350
        y = popup.winfo_screenheight() // 2 - 300
        popup.geometry(f"700x600+{x}+{y}")

        popup.transient(self.window)
        popup.grab_set()

        # Container principale
        main_frame = ctk.CTkFrame(popup, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = ctk.CTkLabel(
            main_frame,
            text=f"📍 Posizione {position_index + 1} - Ruolo {role}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['accent_purple']
        )
        header.pack(pady=(0, 15))

        # Barra di ricerca
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            main_frame,
            textvariable=search_var,
            placeholder_text="🔍 Cerca giocatore...",
            height=35,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_secondary'],
            border_color=COLORS['border']
        )
        search_entry.pack(fill="x", pady=(0, 10))

        # Filtri
        filters_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        filters_frame.pack(fill="x", pady=(0, 10))

        # Checkbox preferiti
        favorites_var = tk.BooleanVar(value=False)
        favorites_check = ctk.CTkCheckBox(
            filters_frame,
            text="⭐ Solo Preferiti",
            variable=favorites_var,
            fg_color=COLORS['accent_yellow'],
            hover_color=COLORS['warning'],
            text_color=COLORS['text_primary'],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        favorites_check.pack(side="left", padx=5)

        # Ordinamento
        sort_label = ctk.CTkLabel(
            filters_frame,
            text="Ordina per:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        )
        sort_label.pack(side="left", padx=(20, 5))

        sort_var = tk.StringVar(value="Overall")
        sort_combo = ctk.CTkComboBox(
            filters_frame,
            variable=sort_var,
            values=["Overall", "Nome", "Squadra", "FM", "MV"],
            width=120,
            height=30,
            fg_color=COLORS['bg_secondary'],
            button_color=COLORS['accent_blue'],
            border_color=COLORS['border']
        )
        sort_combo.pack(side="left", padx=5)

        # Lista giocatori con Treeview (come nella lista principale)
        list_frame = ctk.CTkFrame(
            main_frame,
            fg_color=COLORS['bg_secondary'],
            corner_radius=10,
            border_width=1,
            border_color=COLORS['border']
        )
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Colonne: Nome, R, Squadra, Overall, PrezzoMax
        columns = ('Nome', 'R', 'Squadra', 'Overall', 'PrezzoMax')

        from tkinter import ttk
        tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            selectmode='browse',
            height=15
        )

        # Configura colonne
        tree.heading('Nome', text='Nome', command=lambda: self._sort_tree(tree, 'Nome', False))
        tree.heading('R', text='R', command=lambda: self._sort_tree(tree, 'R', False))
        tree.heading('Squadra', text='Squadra', command=lambda: self._sort_tree(tree, 'Squadra', False))
        tree.heading('Overall', text='Overall', command=lambda: self._sort_tree(tree, 'Overall', True))
        tree.heading('PrezzoMax', text='Prezzo Max %', command=lambda: self._sort_tree(tree, 'PrezzoMax', True))

        tree.column('Nome', width=180, anchor='w')
        tree.column('R', width=50, anchor='center')
        tree.column('Squadra', width=120, anchor='w')
        tree.column('Overall', width=80, anchor='center')
        tree.column('PrezzoMax', width=100, anchor='center')

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Style
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Treeview",
            background=COLORS['bg_tertiary'],
            foreground=COLORS['text_primary'],
            fieldbackground=COLORS['bg_tertiary'],
            borderwidth=0,
            font=('Segoe UI', 10)
        )
        style.configure("Treeview.Heading", background=COLORS['bg_secondary'], foreground=COLORS['text_primary'], font=('Segoe UI', 10, 'bold'))
        style.map('Treeview', background=[('selected', COLORS['accent_purple'])])

        tree.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scrollbar.pack(side="right", fill="y", padx=2, pady=2)

        # Converte lista in DataFrame per facile filtraggio
        players_df = pd.DataFrame(players_list)

        def update_list(*args):
            """Aggiorna lista in base a filtri"""
            # Pulisci tree
            for item in tree.get_children():
                tree.delete(item)

            # Filtra per ricerca
            filtered = players_df.copy()

            # Escludi giocatori già selezionati
            selected_ids = [p['id'] for p in self.selected_players.values()]
            filtered = filtered[~filtered['Id'].isin(selected_ids)]

            search_text = search_var.get().lower()
            if search_text:
                filtered = filtered[filtered['Nome'].str.lower().str.contains(search_text, na=False)]

            # Filtra per preferiti
            if favorites_var.get():
                from src.data.favorites_manager import FavoritesManager
                fav_manager = FavoritesManager()
                fav_ids = fav_manager.get_all_favorites()
                filtered = filtered[filtered['Id'].isin(fav_ids)]

            # Ordina
            sort_by = sort_var.get()
            if sort_by == "Overall":
                filtered = filtered.sort_values('Overall', ascending=False, na_position='last')
            elif sort_by == "Nome":
                filtered = filtered.sort_values('Nome', ascending=True)
            elif sort_by == "Squadra":
                filtered = filtered.sort_values('Squadra', ascending=True)
            elif sort_by == "FM":
                # Converti a numeric prima di ordinare
                filtered['Fm_weighted_num'] = pd.to_numeric(filtered['Fm_weighted'], errors='coerce')
                filtered = filtered.sort_values('Fm_weighted_num', ascending=False, na_position='last')
            elif sort_by == "MV":
                # Converti a numeric prima di ordinare
                filtered['Mv_weighted_num'] = pd.to_numeric(filtered['Mv_weighted'], errors='coerce')
                filtered = filtered.sort_values('Mv_weighted_num', ascending=False, na_position='last')

            # Popola tree
            for _, player in filtered.iterrows():
                # Usa price_percentage se disponibile, altrimenti calcola
                if 'price_percentage' in player.index and pd.notna(player['price_percentage']):
                    price_pct = player['price_percentage']
                else:
                    price_data = self.price_calculator.calculate_price_percentage(player['Id'], self.budget)
                    price_pct = price_data.get('percentage', 0) if price_data else 0

                values = (
                    player['Nome'],
                    player['R'],
                    player['Squadra'],
                    f"{player.get('Overall', 0):.1f}",
                    f"{price_pct:.1f}%"
                )
                tree.insert('', 'end', values=values, tags=(str(player['Id']),))

        # Bind eventi
        search_var.trace('w', update_list)
        favorites_var.trace('w', update_list)
        sort_var.trace('w', update_list)

        # Doppio click per selezionare
        def on_double_click(event):
            selection = tree.selection()
            if selection:
                item = selection[0]
                item_values = tree.item(item, 'values')
                player_name = item_values[0]

                # Trova il giocatore
                player = players_df[players_df['Nome'] == player_name].iloc[0]

                # Salva selezione
                self.selected_players[position_index] = {
                    'id': player['Id'],
                    'name': player['Nome'],
                    'role': player['R'],
                    'squadra': player['Squadra'],
                    'overall': player.get('Overall', 0)
                }

                # Aggiorna UI
                # Usa price_percentage se disponibile
                if 'price_percentage' in player.index and pd.notna(player['price_percentage']):
                    price_pct = player['price_percentage']
                    price_data = self.price_calculator.calculate_price_percentage(player['Id'], self.budget)
                    price_credits = price_data.get('credits', 0) if price_data else 0
                else:
                    price_data = self.price_calculator.calculate_price_percentage(player['Id'], self.budget)
                    price_pct = price_data.get('percentage', 0) if price_data else 0
                    price_credits = price_data.get('credits', 0) if price_data else 0

                info_text = f"{player['Nome']} | {player['R']} | {player['Squadra']} | OVR:{player.get('Overall', 0):.1f} | {price_pct:.1f}%"

                combo_info = self.player_combos[position_index]
                combo_info['info_label'].configure(
                    text=info_text,
                    text_color=COLORS['text_primary']
                )

                # Imposta placeholder con prezzo Max
                combo_info['cost_entry'].delete(0, 'end')
                combo_info['cost_entry'].configure(placeholder_text=f"{int(price_credits)}")

                # Aggiorna colore sfondo
                combo_info['row_frame'].configure(fg_color=COLORS['bg_tertiary'])

                # Aggiorna stato preferiti
                if self.favorites_manager and self.favorites_manager.is_favorite(player['Id']):
                    combo_info['fav_btn'].configure(fg_color=COLORS['accent_yellow'])
                else:
                    combo_info['fav_btn'].configure(fg_color=COLORS['bg_tertiary'])

                self.update_statistics()
                popup.destroy()

        tree.bind('<Double-Button-1>', on_double_click)

        # Popola inizialmente
        update_list()

        # Bottone chiudi
        close_btn = ctk.CTkButton(
            main_frame,
            text="Chiudi",
            command=popup.destroy,
            height=40,
            fg_color=COLORS['error'],
            hover_color=COLORS['accent_pink']
        )
        close_btn.pack()

    def remove_player(self, position_index):
        """Rimuove giocatore selezionato"""
        if position_index in self.selected_players:
            del self.selected_players[position_index]

        # Rimuovi costo personalizzato se presente
        if position_index in self.custom_credits:
            del self.custom_credits[position_index]

        # Rimuovi da auto-generati se presente
        if position_index in self.auto_generated_positions:
            self.auto_generated_positions.discard(position_index)

        # Reset UI
        combo_info = self.player_combos[position_index]
        combo_info['info_label'].configure(
            text="Clicca per selezionare giocatore...",
            text_color=COLORS['text_secondary']
        )
        combo_info['cost_entry'].delete(0, 'end')
        combo_info['cost_entry'].configure(placeholder_text="Prezzo")
        combo_info['fav_btn'].configure(fg_color=COLORS['bg_tertiary'])
        combo_info['row_frame'].configure(fg_color=COLORS['bg_primary'])

        self.update_statistics()

    def update_statistics(self):
        """Aggiorna statistiche rosa"""
        if not self.selected_players:
            self.stats_labels['price_pct'].configure(text="0.0%")
            self.stats_labels['overall_avg'].configure(text="0.0")
            return

        # Calcola % prezzo totale
        total_price_pct = 0
        total_overall = 0
        valid_overall_count = 0

        for pos_idx, player_data in self.selected_players.items():
            player_id = player_data['id']

            # Usa costo personalizzato se presente
            if pos_idx in self.custom_credits:
                custom_cost = self.custom_credits[pos_idx]
                custom_pct = (custom_cost / self.budget) * 100
                total_price_pct += custom_pct
            else:
                # Usa calcolo standard
                price_data = self.price_calculator.calculate_price_percentage(player_id, self.budget)
                if price_data:
                    price_pct = price_data.get('percentage', 0)
                    # Forza prezzo minimo di 1 credito
                    min_price_pct = (1.0 / self.budget) * 100
                    price_pct = max(price_pct, min_price_pct)
                    total_price_pct += price_pct

            # Converti overall a float gestendo N/A
            try:
                overall_val = float(player_data['overall'])
                total_overall += overall_val
                valid_overall_count += 1
            except (ValueError, TypeError):
                pass  # Ignora giocatori con overall non valido

        avg_overall = total_overall / valid_overall_count if valid_overall_count > 0 else 0.0

        # Aggiorna label
        price_color = COLORS['accent_green'] if total_price_pct <= 100 else COLORS['warning']
        self.stats_labels['price_pct'].configure(
            text=f"{total_price_pct:.1f}%",
            text_color=price_color
        )
        self.stats_labels['overall_avg'].configure(text=f"{avg_overall:.1f}")

    def generate_rosa(self):
        """Genera rosa automaticamente - dinamico, rigenera ad ogni click"""
        self.value_priority = self.value_priority_combo.get()

        # Rimuovi giocatori aggiunti dall'algoritmo precedente
        positions_to_remove = list(self.auto_generated_positions)
        for pos_idx in positions_to_remove:
            if pos_idx in self.selected_players:
                del self.selected_players[pos_idx]

                # Rimuovi anche costo personalizzato se presente
                if pos_idx in self.custom_credits:
                    del self.custom_credits[pos_idx]

                # Reset UI
                combo_info = self.player_combos[pos_idx]
                combo_info['info_label'].configure(
                    text="Clicca per selezionare giocatore...",
                    text_color=COLORS['text_secondary']
                )
                combo_info['cost_entry'].delete(0, 'end')
                combo_info['cost_entry'].configure(placeholder_text="Prezzo")
                combo_info['row_frame'].configure(fg_color=COLORS['bg_primary'])

        # Resetta set giocatori auto-generati
        self.auto_generated_positions.clear()

        # Trova posizioni vuote
        total_positions = sum(self.rosa_composition.values())
        empty_positions = [i for i in range(total_positions) if i not in self.selected_players]

        if not empty_positions:
            messagebox.showinfo("Rosa Completa", "La rosa è già completa!")
            return

        # Calcola budget disponibile (somma budget allocato per ruoli vuoti)
        available_budget_pct = self._calculate_available_budget(empty_positions)

        # Riempi posizioni vuote
        self.fill_empty_positions(empty_positions, available_budget_pct, None)

    def _calculate_available_budget(self, empty_positions):
        """Calcola budget disponibile in base ai ruoli vuoti"""
        # Mappa posizioni a ruoli
        position_roles = []
        pos_idx = 0
        for role_key in ['P', 'D', 'C', 'A']:
            for _ in range(self.rosa_composition[role_key]):
                position_roles.append(role_key)
                pos_idx += 1

        # Conta slot vuoti per ruolo
        empty_by_role = {'P': 0, 'D': 0, 'C': 0, 'A': 0}
        for pos in empty_positions:
            role = position_roles[pos]
            empty_by_role[role] += 1

        # Calcola budget totale disponibile
        total_budget_pct = 0.0
        for role in ['P', 'D', 'C', 'A']:
            if empty_by_role[role] > 0:
                # Usa il budget allocato per questo ruolo
                total_budget_pct += self.budget_per_role[role]

        return total_budget_pct / 100.0

    def fill_empty_positions(self, empty_positions, available_budget_pct, target_price_pct):
        """Riempie posizioni vuote con algoritmo zaino multidimensionale"""
        # Valida budget per reparto
        total_budget_allocated = sum(self.budget_per_role.values())
        if abs(total_budget_allocated - 100.0) > 0.1:
            messagebox.showwarning(
                "Budget Non Valido",
                f"Il budget totale allocato è {total_budget_allocated:.1f}%.\nDeve essere esattamente 100%."
            )
            return

        # Mappa posizioni a ruoli
        position_roles = []
        pos_idx = 0
        for role_key in ['P', 'D', 'C', 'A']:
            for _ in range(self.rosa_composition[role_key]):
                position_roles.append(role_key)
                pos_idx += 1

        # Usa ottimizzatore
        try:
            optimized_players = self.optimizer.optimize_positions(
                empty_positions,
                position_roles,
                self.budget_per_role,
                self.selected_players,
                value_priority=self.value_priority,
                blacklisted_teams=self.blacklisted_teams,
                custom_credits=self.custom_credits
            )

            # Applica risultati
            filled_count = 0
            for pos_idx, player_data in optimized_players.items():
                self.selected_players[pos_idx] = player_data

                # Traccia come auto-generato
                self.auto_generated_positions.add(pos_idx)

                # Calcola prezzo al 100%
                price_data = self.price_calculator.calculate_price_percentage(
                    player_data['id'], self.budget
                )
                price_pct = price_data.get('percentage', 0) if price_data else 0
                price_credits = price_data.get('credits', 0) if price_data else 0

                # Aggiorna label (converti a float gestendo N/A)
                try:
                    overall_val = float(player_data['overall'])
                except (ValueError, TypeError):
                    overall_val = 0.0

                try:
                    price_pct_val = float(price_pct)
                except (ValueError, TypeError):
                    price_pct_val = 0.0

                display_value = f"{player_data['name']} | {player_data['role']} | {player_data['squadra']} | OVR:{overall_val:.1f} | {price_pct_val:.1f}%"
                combo_info = self.player_combos[pos_idx]
                combo_info['info_label'].configure(
                    text=display_value,
                    text_color=COLORS['text_primary']
                )

                # Imposta placeholder con prezzo Max (non il valore)
                combo_info['cost_entry'].delete(0, 'end')
                combo_info['cost_entry'].configure(placeholder_text=f"{int(price_credits)}")

                # Usa verde scuro per evidenziare
                combo_info['row_frame'].configure(fg_color="#1a4d2e")

                # Aggiorna stato preferiti
                if self.favorites_manager and self.favorites_manager.is_favorite(player_data['id']):
                    combo_info['fav_btn'].configure(fg_color=COLORS['accent_yellow'])
                else:
                    combo_info['fav_btn'].configure(fg_color=COLORS['bg_tertiary'])

                filled_count += 1

            self.update_statistics()

            # Calcola totale raggiunto (con prezzi personalizzati se presenti)
            final_total = 0
            final_by_role = {'P': 0, 'D': 0, 'C': 0, 'A': 0}
            for pos, player_data in self.selected_players.items():
                role = position_roles[pos]

                if pos in self.custom_credits:
                    pct = (self.custom_credits[pos] / self.budget) * 100
                    final_total += pct
                    final_by_role[role] += pct
                else:
                    price_data = self.price_calculator.calculate_price_percentage(
                        player_data['id'], self.budget
                    )
                    if price_data:
                        pct = price_data.get('percentage', 0)
                        final_total += pct
                        final_by_role[role] += pct

            # Verifica rispetto vincoli per ruolo
            violations = []
            for role in ['P', 'D', 'C', 'A']:
                allocated = self.budget_per_role[role]
                used = final_by_role[role]
                diff = abs(used - allocated)
                if diff > 2.0:  # Scarto > 2%
                    violations.append(f"{role}: {used:.1f}% (target {allocated:.1f}%)")

            msg = f"Rosa generata con algoritmo ottimizzato!\n\n"
            msg += f"Aggiunti: {filled_count} giocatori\n"
            msg += f"Budget totale: {final_total:.1f}%\n\n"
            msg += f"Per ruolo:\n"
            for role in ['P', 'D', 'C', 'A']:
                msg += f"  {role}: {final_by_role[role]:.1f}% / {float(self.budget_per_role[role]):.1f}%\n"

            if violations:
                msg += f"\n⚠️ Scarto >2% su: {', '.join(violations)}"

            msg += f"\n\n💡 Puoi modificare i prezzi nei campi se li ritieni troppo alti o bassi."

            messagebox.showinfo("Generazione Completata", msg)

        except Exception as e:
            import traceback
            messagebox.showerror(
                "Errore Ottimizzazione",
                f"Errore durante l'ottimizzazione:\n{str(e)}\n\n{traceback.format_exc()}"
            )
