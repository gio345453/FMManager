"""
Gestione controlli e filtri dell'interfaccia
"""
import tkinter as tk
from tkinter import ttk


class ControlsManager:
    """Gestisce i controlli di filtro e azioni dell'applicazione"""

    def __init__(self, parent_frame, app):
        self.parent_frame = parent_frame
        self.app = app
        self.setup_controls()

    def setup_controls(self):
        """Configura i controlli di filtro"""
        # Prima riga: filtri principali
        row1_frame = ttk.Frame(self.parent_frame)
        row1_frame.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self._setup_budget_controls(row1_frame)
        self._setup_role_filter(row1_frame)
        self._setup_search_filter(row1_frame)

        # Seconda riga: filtri squadra/tag e pulsanti
        row2_frame = ttk.Frame(self.parent_frame)
        row2_frame.grid(row=1, column=0, sticky=tk.W)

        self._setup_team_filter(row2_frame)
        self._setup_tag_filter(row2_frame)
        self._setup_action_buttons(row2_frame)

    def _setup_budget_controls(self, parent):
        """Configura controlli budget"""
        ttk.Label(parent, text="Budget Asta:").grid(row=0, column=0, padx=5)
        budget_entry = ttk.Entry(parent, textvariable=self.app.budget_var, width=8)
        budget_entry.grid(row=0, column=1, padx=5)
        budget_entry.bind('<Return>', self.app.on_budget_change)
        ttk.Label(parent, text="crediti").grid(row=0, column=2, padx=(0, 15))

        ttk.Button(parent, text="Aggiorna Prezzi",
                  command=self.app.on_budget_change).grid(row=0, column=3, padx=5)

    def _setup_role_filter(self, parent):
        """Configura filtro ruolo"""
        ttk.Label(parent, text="Filtra per Ruolo:").grid(row=0, column=4, padx=5)
        self.app.role_var = tk.StringVar(value="Tutti")
        role_combo = ttk.Combobox(parent, textvariable=self.app.role_var,
                                   values=["Tutti", "P", "D", "C", "A"], state="readonly", width=15)
        role_combo.grid(row=0, column=5, padx=5)
        role_combo.bind("<<ComboboxSelected>>", self.app.filter_data)

    def _setup_search_filter(self, parent):
        """Configura filtro ricerca nome"""
        ttk.Label(parent, text="Cerca Nome:").grid(row=0, column=6, padx=5)
        self.app.search_var = tk.StringVar()
        self.app.search_var.trace('w', self.app.filter_data)
        search_entry = ttk.Entry(parent, textvariable=self.app.search_var, width=20)
        search_entry.grid(row=0, column=7, padx=5)

    def _setup_team_filter(self, parent):
        """Configura filtro squadra"""
        ttk.Label(parent, text="Filtra per Squadra:").grid(row=0, column=0, padx=5)
        self.app.team_var = tk.StringVar(value="Tutte")
        self.app.team_combo = ttk.Combobox(parent, textvariable=self.app.team_var,
                                           state="readonly", width=15)
        self.app.team_combo.grid(row=0, column=1, padx=5)
        self.app.team_combo.bind("<<ComboboxSelected>>", self.app.filter_data)

    def _setup_tag_filter(self, parent):
        """Configura filtro tag"""
        ttk.Label(parent, text="Filtra per Tag:").grid(row=0, column=2, padx=5)
        self.app.tag_var = tk.StringVar(value="Tutti")
        self.app.tag_combo = ttk.Combobox(parent, textvariable=self.app.tag_var,
                                          state="readonly", width=15)
        self.app.tag_combo.grid(row=0, column=3, padx=5)
        self.app.tag_combo.bind("<<ComboboxSelected>>", self.app.filter_data)

    def _setup_action_buttons(self, parent):
        """Configura pulsanti azione"""
        ttk.Button(parent, text="Ricarica Dati",
                  command=self.app.reload_data).grid(row=0, column=4, padx=10)

        ttk.Button(parent, text="📊 Confronta Giocatori",
                  command=self.app.open_player_comparison).grid(row=0, column=5, padx=5)
        ttk.Button(parent, text="🏆 Dashboard Squadre",
                  command=self.app.open_team_dashboard).grid(row=0, column=6, padx=5)
