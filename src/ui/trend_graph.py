"""
Modulo per visualizzare grafici di trend stagionali dei giocatori
"""
import customtkinter as ctk
from src.config import STATS_FILES
from src.data.cache import DataCache
from src.ui.chart_styles import create_player_trend_figure, embed_figure_in_tkinter
from src.ui.components.constants import COLORS
from src.ui.window_chrome import configure_application_window


class TrendGraphWindow:
    """Finestra per visualizzare i trend stagionali di un giocatore"""

    def __init__(self, parent, player_id, player_name, player_role):
        self.player_id = player_id
        self.player_name = player_name
        self.player_role = player_role
        self.cache = DataCache()

        # Finestra popup CustomTkinter
        self.window = ctk.CTkToplevel(parent)
        configure_application_window(self.window)
        self.window.title(f"📈 Trend Stagionale: {player_name}")
        self.window.geometry("1200x800")
        self.window.configure(fg_color=COLORS['bg_primary'])

        # Transient & focus
        self.window.transient(parent)
        self.window.lift()
        self.window.focus_force()

        # Responsive grid
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

        self._setup_ui()
        self._load_and_plot_data()

    def _setup_ui(self):
        """Configura l'interfaccia con design moderno"""
        # Main container scrollabile
        main_container = ctk.CTkScrollableFrame(
            self.window,
            fg_color=COLORS['bg_primary'],
            scrollbar_button_color=COLORS['accent_purple'],
            scrollbar_button_hover_color=COLORS['accent_blue']
        )
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=15)
        main_container.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        # Titolo
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"📈 Evoluzione Statistiche",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COLORS['accent_purple']
        )
        title_label.pack(side="left")

        # Bottone chiudi
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

        # Info Card - Nome e Ruolo
        info_card = ctk.CTkFrame(
            main_container,
            fg_color=COLORS['bg_secondary'],
            corner_radius=15,
            border_width=2,
            border_color=COLORS['accent_blue']
        )
        info_card.pack(fill="x", pady=(0, 20))

        info_content = ctk.CTkFrame(info_card, fg_color="transparent")
        info_content.pack(fill="x", padx=20, pady=15)

        # Nome giocatore
        ctk.CTkLabel(
            info_content,
            text=self.player_name,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(side="left", padx=(0, 20))

        # Badge ruolo
        role_badge = ctk.CTkFrame(info_content, fg_color=COLORS['accent_purple'], corner_radius=8)
        role_badge.pack(side="left")
        ctk.CTkLabel(
            role_badge,
            text=f"Ruolo: {self.player_role}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(padx=12, pady=6)

        # Container grafici
        self.graph_container = ctk.CTkFrame(
            main_container,
            fg_color=COLORS['bg_secondary'],
            corner_radius=15,
            border_width=2,
            border_color=COLORS['border']
        )
        self.graph_container.pack(fill="both", expand=True)

    def _load_and_plot_data(self):
        """Carica i dati e crea i grafici"""
        from src.config import get_season_names_list
        season_names = get_season_names_list()
        season_keys = ['old', 'middle', 'recent']

        data = {
            'seasons': [],
            'Fm': [],
            'Mv': [],
            'Gf': [],
            'Gs': [],
            'Rp': [],
            'Rc': [],
            'Ass': [],
            'Pv': []
        }

        for season_name, season_key in zip(season_names, season_keys):
            filename, _ = STATS_FILES[season_key]
            df = self.cache.get(filename)

            if df is not None:
                player_data = df[df['Id'] == self.player_id]

                if not player_data.empty:
                    row = player_data.iloc[0]
                    data['seasons'].append(season_name)
                    data['Fm'].append(float(str(row.get('Fm', 0)).replace(',', '.')))
                    data['Mv'].append(float(str(row.get('Mv', 0)).replace(',', '.')))
                    data['Gf'].append(int(row.get('Gf', 0)))
                    data['Gs'].append(int(row.get('Gs', 0)))
                    data['Rp'].append(int(row.get('Rp', 0)))
                    data['Rc'].append(int(row.get('Rc', 0)))
                    data['Ass'].append(int(row.get('Ass', 0)))
                    data['Pv'].append(int(row.get('Pv', 0)))

        if not data['seasons']:
            # Nessun dato disponibile - Messaggio stilizzato
            no_data_frame = ctk.CTkFrame(
                self.graph_container,
                fg_color=COLORS['bg_tertiary'],
                corner_radius=12
            )
            no_data_frame.pack(expand=True, fill="both", padx=20, pady=20)

            ctk.CTkLabel(
                no_data_frame,
                text="📊 Nessun dato disponibile",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=COLORS['text_secondary']
            ).pack(expand=True)
            return

        # Crea figura usando il modulo centralizzato con statistiche appropriate per ruolo
        figure = create_player_trend_figure(
            seasons=data['seasons'],
            fm_data=data['Fm'],
            mv_data=data['Mv'],
            gf_data=data['Gf'],
            gs_data=data['Gs'],
            rp_data=data['Rp'],
            rc_data=data['Rc'],
            ass_data=data['Ass'],
            player_name=self.player_name,
            player_role=self.player_role
        )

        # Incorpora in Tkinter
        embed_figure_in_tkinter(figure, self.graph_container)
