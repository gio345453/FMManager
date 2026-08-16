"""
Componente FiltersPanel - Filtri e ricerca giocatori
"""
import customtkinter as ctk
import tkinter as tk
from .constants import COLORS


class FiltersPanel:
    """Pannello filtri con layout a 2 righe a larghezza intera"""

    def __init__(self, parent, df, on_filter_change, favorites_manager=None, on_favorites_click=None, notes_manager=None):
        self.parent = parent
        self.df = df
        self.on_filter_change = on_filter_change
        self.favorites_manager = favorites_manager
        self.on_favorites_click = on_favorites_click
        self.notes_manager = notes_manager

        # Variabili
        self.role_var = None
        self.team_var = None
        self.search_var = None
        self.price_range_var = None
        self.tag_var = None

        # Widget
        self.controls_card = None
        self.role_menu = None
        self.team_menu = None
        self.search_entry = None
        self.price_range_menu = None
        self.tag_menu = None
        self.fm_min_entry = None
        self.fm_max_entry = None
        self.reset_button = None
        self.favorites_button = None

    def create(self):
        """Crea e mostra il pannello filtri esteso a tutta larghezza"""
        self.controls_card = ctk.CTkFrame(self.parent, fg_color=COLORS['bg_secondary'], corner_radius=15)
        self.controls_card.pack(fill="x", padx=0, pady=(0, 15))

        controls_inner = ctk.CTkFrame(self.controls_card, fg_color="transparent")
        controls_inner.pack(fill="x", padx=20, pady=15)

        # RIGA 1: Barra di Ricerca + Pulsante Preferiti
        top_row = ctk.CTkFrame(controls_inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 12))

        self._create_search_control(top_row)

        if self.favorites_manager and self.on_favorites_click:
            self._create_favorites_button(top_row)

        # RIGA 2: Filtri + Reset
        bottom_row = ctk.CTkFrame(controls_inner, fg_color="transparent")
        bottom_row.pack(fill="x")

        bottom_row.grid_columnconfigure(0, weight=1)  # Ruolo
        bottom_row.grid_columnconfigure(1, weight=1)  # Squadra
        bottom_row.grid_columnconfigure(2, weight=1)  # Tag
        bottom_row.grid_columnconfigure(3, weight=1)  # % Budget
        bottom_row.grid_columnconfigure(4, weight=2)  # FM
        bottom_row.grid_columnconfigure(5, weight=0)  # Reset

        self._create_role_filter_grid(bottom_row, col=0)
        self._create_team_filter_grid(bottom_row, col=1)
        self._create_tag_filter_grid(bottom_row, col=2)
        self._create_price_range_filter_grid(bottom_row, col=3)
        self._create_fm_filter_grid(bottom_row, col=4)
        self._create_reset_button_grid(bottom_row, col=5)

        return self.controls_card

    def _create_search_control(self, parent):
        """Crea controllo ricerca esteso"""
        search_frame = ctk.CTkFrame(parent, fg_color="transparent")
        search_frame.pack(side="left", fill="x", expand=True, padx=(0, 15))

        ctk.CTkLabel(
            search_frame,
            text="Cerca:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['text_secondary']
        ).pack(side="left", padx=(0, 10))

        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Nome giocatore...",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_tertiary'],
            border_width=0,
            height=35
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind('<KeyRelease>', lambda e: self.on_filter_change())

    def _create_favorites_button(self, parent):
        """Crea bottone preferiti in alto a destra"""
        count = self.favorites_manager.get_favorites_count()
        self.favorites_button = ctk.CTkButton(
            parent,
            text=f"⭐ Preferiti ({count})",
            command=self.on_favorites_click,
            fg_color=COLORS['accent_yellow'],
            hover_color="#FFB703",
            text_color=COLORS['bg_primary'],
            corner_radius=10,
            width=130,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.favorites_button.pack(side="right")

    def _create_role_filter_grid(self, parent, col):
        """Crea filtro ruolo in griglia responsive"""
        role_frame = ctk.CTkFrame(parent, fg_color="transparent")
        role_frame.grid(row=0, column=col, sticky="ew", padx=(0, 10))

        ctk.CTkLabel(
            role_frame,
            text="Ruolo:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['text_secondary']
        ).pack(side="left", padx=(0, 8))

        self.role_var = tk.StringVar(value="Tutti")
        self.role_menu = ctk.CTkOptionMenu(
            role_frame,
            variable=self.role_var,
            values=["Tutti", "P", "D", "C", "A"],
            command=lambda _: self.on_filter_change(),
            fg_color=COLORS['bg_tertiary'],
            button_color=COLORS['accent_blue'],
            button_hover_color=COLORS['accent_purple']
        )
        self.role_menu.pack(side="left", fill="x", expand=True)

    def _create_team_filter_grid(self, parent, col):
        """Crea filtro squadra in griglia responsive"""
        team_frame = ctk.CTkFrame(parent, fg_color="transparent")
        team_frame.grid(row=0, column=col, sticky="ew", padx=(0, 10))

        ctk.CTkLabel(
            team_frame,
            text="Squadra:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['text_secondary']
        ).pack(side="left", padx=(0, 8))

        teams = ["Tutte"] + sorted(self.df['Squadra'].unique().tolist()) if self.df is not None else ["Tutte"]
        self.team_var = tk.StringVar(value="Tutte")
        self.team_menu = ctk.CTkOptionMenu(
            team_frame,
            variable=self.team_var,
            values=teams,
            command=lambda _: self.on_filter_change(),
            fg_color=COLORS['bg_tertiary'],
            button_color=COLORS['accent_blue'],
            button_hover_color=COLORS['accent_purple']
        )
        self.team_menu.pack(side="left", fill="x", expand=True)

    def _create_tag_filter_grid(self, parent, col):
        """Crea filtro tag in griglia responsive"""
        tag_frame = ctk.CTkFrame(parent, fg_color="transparent")
        tag_frame.grid(row=0, column=col, sticky="ew", padx=(0, 10))

        ctk.CTkLabel(
            tag_frame,
            text="Tag:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['text_secondary']
        ).pack(side="left", padx=(0, 8))

        tags = ["Tutti"]
        if self.notes_manager:
            all_tags = self.notes_manager.get_all_tags()
            tags.extend(sorted(all_tags))

        self.tag_var = tk.StringVar(value="Tutti")
        self.tag_menu = ctk.CTkOptionMenu(
            tag_frame,
            variable=self.tag_var,
            values=tags,
            command=lambda _: self.on_filter_change(),
            fg_color=COLORS['bg_tertiary'],
            button_color=COLORS['accent_blue'],
            button_hover_color=COLORS['accent_purple']
        )
        self.tag_menu.pack(side="left", fill="x", expand=True)

    def _create_price_range_filter_grid(self, parent, col):
        """Crea filtro fasce percentuale budget in griglia responsive"""
        price_frame = ctk.CTkFrame(parent, fg_color="transparent")
        price_frame.grid(row=0, column=col, sticky="ew", padx=(0, 10))

        ctk.CTkLabel(
            price_frame,
            text="% Budget:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['text_secondary']
        ).pack(side="left", padx=(0, 8))

        price_ranges = ["Tutte", "0-3%", "3-6%", "6-9%", "9-12%", "12-15%", "15-18%", "18-21%", "21-24%", "24-27%", "27-30%", ">30%"]
        self.price_range_var = tk.StringVar(value="Tutte")
        self.price_range_menu = ctk.CTkOptionMenu(
            price_frame,
            variable=self.price_range_var,
            values=price_ranges,
            command=lambda _: self.on_filter_change(),
            fg_color=COLORS['bg_tertiary'],
            button_color=COLORS['accent_blue'],
            button_hover_color=COLORS['accent_purple']
        )
        self.price_range_menu.pack(side="left", fill="x", expand=True)

    def _create_fm_filter_grid(self, parent, col):
        """Crea filtro FM con campi min e max senza textvariable per far funzionare i placeholder"""
        fm_frame = ctk.CTkFrame(parent, fg_color="transparent")
        fm_frame.grid(row=0, column=col, sticky="ew", padx=(0, 10))

        ctk.CTkLabel(
            fm_frame,
            text="FM:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['text_secondary']
        ).pack(side="left", padx=(0, 8))

        inputs_container = ctk.CTkFrame(fm_frame, fg_color="transparent")
        inputs_container.pack(side="left", fill="x", expand=True)

        # Campo Min (senza textvariable!)
        self.fm_min_entry = ctk.CTkEntry(
            inputs_container,
            placeholder_text="Min",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_tertiary'],
            border_width=0,
            height=32,
            width=90
        )
        self.fm_min_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.fm_min_entry.bind('<KeyRelease>', lambda e: self.on_filter_change())

        # Campo Max (senza textvariable!)
        self.fm_max_entry = ctk.CTkEntry(
            inputs_container,
            placeholder_text="Max",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['bg_tertiary'],
            border_width=0,
            height=32,
            width=90
        )
        self.fm_max_entry.pack(side="left", fill="x", expand=True)
        self.fm_max_entry.bind('<KeyRelease>', lambda e: self.on_filter_change())

    def _create_reset_button_grid(self, parent, col):
        """Crea pulsante reset filtri"""
        self.reset_button = ctk.CTkButton(
            parent,
            text="🔄 Reset Filtri",
            command=self._reset_all_filters,
            width=120,
            height=32,
            fg_color=COLORS['accent_purple'],
            hover_color=COLORS['accent_blue'],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.reset_button.grid(row=0, column=col, sticky="e")

    def update_favorites_count(self):
        """Aggiorna il conteggio dei preferiti nel bottone"""
        if hasattr(self, 'favorites_button') and self.favorites_button and self.favorites_manager:
            count = self.favorites_manager.get_favorites_count()
            self.favorites_button.configure(text=f"⭐ Preferiti ({count})")

    def _reset_all_filters(self):
        """Resetta tutti i filtri e richiama il callback"""
        self.reset_filters()
        self.on_filter_change()

    def get_filter_values(self):
        """Restituisce i valori correnti dei filtri leggendo direttamente dagli Entry"""
        return {
            'role': self.role_var.get() if self.role_var else "Tutti",
            'team': self.team_var.get() if self.team_var else "Tutte",
            'search': self.search_var.get() if self.search_var else "",
            'price_range': self.price_range_var.get() if self.price_range_var else "Tutte",
            'tag': self.tag_var.get() if self.tag_var else "Tutti",
            'fm_min': self.fm_min_entry.get().strip() if self.fm_min_entry else "",
            'fm_max': self.fm_max_entry.get().strip() if self.fm_max_entry else ""
        }

    def update_team_list(self, df):
        """Aggiorna la lista delle squadre disponibili"""
        self.df = df
        if self.team_menu and df is not None:
            teams = ["Tutte"] + sorted(df['Squadra'].unique().tolist())
            self.team_menu.configure(values=teams)

    def reset_filters(self):
        """Resetta tutti i filtri ai valori di default"""
        if self.role_var:
            self.role_var.set("Tutti")
        if self.team_var:
            self.team_var.set("Tutte")
        if self.search_var:
            self.search_var.set("")
        if self.price_range_var:
            self.price_range_var.set("Tutte")
        if self.tag_var:
            self.tag_var.set("Tutti")
        
        # Pulizia diretta degli Entry per Min e Max
        if self.fm_min_entry:
            self.fm_min_entry.delete(0, 'end')
        if self.fm_max_entry:
            self.fm_max_entry.delete(0, 'end')

    def update_tag_list(self):
        """Aggiorna la lista dei tag disponibili"""
        if self.tag_menu and self.notes_manager:
            tags = ["Tutti"]
            all_tags = self.notes_manager.get_all_tags()
            tags.extend(sorted(all_tags))
            self.tag_menu.configure(values=tags)

    def destroy(self):
        """Rimuove il pannello filtri"""
        if self.controls_card:
            self.controls_card.destroy()
            self.controls_card = None