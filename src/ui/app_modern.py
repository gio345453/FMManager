"""
Interfaccia grafica ultra-moderna con componenti modulari
Lista completa con tutti i dati per calcolo Overall
"""
import os
import sys
import ctypes
import pandas as pd
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

# Fix per registrare l'app su Windows e mostrare l'icona personalizzata sulla Taskbar
if sys.platform.startswith("win"):
    try:
        myappid = "mycompany.fantacalcio.manager.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

from src.data_processor import FantaCalcioDataProcessor
from src.data.player_notes import PlayerNotesManager
from src.data.favorites_manager import FavoritesManager
from src.data.price_calculator import PriceCalculator
from src.data.auto_tags import AutoTagsManager
from src.data.auto_downloader import AutoDownloader
from src.config import DEFAULT_AUCTION_BUDGET
from src.ui.player_details import PlayerDetailsWindow
from src.ui.player_comparison import PlayerComparisonWindow
from src.ui.team_dashboard import TeamDashboardWindow
from src.ui.favorites_window import FavoritesWindow
from src.ui.build_rosa_window import BuildRosaWindow
from src.ui.window_chrome import configure_application_window, enable_windows_dark_mode
from src.ui.components import (
    COLORS,
    HeaderComponent,
    FiltersPanel,
    PlayerTable,
    TagMenu,
    FooterActions
)


# Tema ultra-moderno
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class UltraModernFantaCalcioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FantaCalcio Manager")
        self.root.configure(fg_color=COLORS['bg_primary'])
        configure_application_window(self.root)

        # Esegui download automatico e assegnazione tag PRIMA di mostrare l'interfaccia
        self._auto_download_and_assign()

        # Avvia a schermo intero
        self.root.after(100, self._maximize_window)

        # Data processor
        self.processor = FantaCalcioDataProcessor()
        self.notes_manager = PlayerNotesManager()
        self.favorites_manager = FavoritesManager()
        self.price_calculator = PriceCalculator(use_optimized=True)
        self.auto_tags_manager = AutoTagsManager()

        # State
        self.df = None
        self.filtered_df = None

        # Budget variable
        self.budget_var = tk.IntVar(value=DEFAULT_AUCTION_BUDGET)

        # Componenti UI
        self.header = None
        self.filters = None
        self.player_table = None
        self.tag_menu = None
        self.footer = None

        # Load data
        self.load_data()

        # Setup UI
        self.setup_ui()

        # Initial population
        self.apply_filters()

    def _maximize_window(self):
        """Massimizza la finestra dopo l'inizializzazione"""
        try:
            self.root.state('zoomed')
        except Exception:
            try:
                self.root.attributes('-zoomed', True)
            except Exception:
                pass

    def _auto_download_and_assign(self):
        """
        Scarica automaticamente i dati e assegna tag/note prima di mostrare l'UI
        Viene eseguito massimo 1 volta ogni ora
        """
        print("\n" + "="*60)
        print("🚀 Avvio automatico: download e assegnazione dati")
        print("="*60)

        try:
            # Crea downloader
            downloader = AutoDownloader()

            # Scarica i dati (controlla automaticamente se è passata 1 ora)
            results = downloader.download_all()

            # Se almeno uno dei download è stato effettuato, assegna i dati
            if any(results.values()):
                print("\n📊 Caricamento dati giocatori per assegnazione...")

                # Carica temporaneamente i dati per l'assegnazione
                temp_processor = FantaCalcioDataProcessor()
                weighted_df = temp_processor.calculate_weighted_stats()

                if weighted_df is not None:
                    df_with_overall = temp_processor.calculate_overall_scores(weighted_df)

                    # Assegna tag e note
                    temp_auto_tags = AutoTagsManager()
                    temp_auto_tags.assign_all_auto_data(df_with_overall)
                else:
                    print("⚠️ Impossibile caricare i dati dei giocatori per l'assegnazione")
            else:
                print("\n✅ Nessun download necessario (dati già aggiornati)")

        except Exception as e:
            print(f"\n❌ Errore durante il processo automatico: {e}")
            import traceback
            traceback.print_exc()

        print("="*60 + "\n")

    def load_data(self):
        """Carica dati"""
        weighted_df = self.processor.calculate_weighted_stats()
        if weighted_df is not None:
            self.df = self.processor.calculate_overall_scores(weighted_df)
            self.filtered_df = self.df.copy()
            # Aggiorna PriceCalculator con i dati caricati
            self.price_calculator.update_players_data(self.df)
        else:
            self.df = None
            self.filtered_df = None

    def setup_ui(self):
        """Setup interfaccia con componenti modulari"""
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=15)

        # Header
        self.header = HeaderComponent(main_container)
        self.header.create()

        # Filters
        self.filters = FiltersPanel(
            main_container,
            self.df,
            on_filter_change=self.apply_filters,
            favorites_manager=self.favorites_manager,
            on_favorites_click=self.open_favorites,
            notes_manager=self.notes_manager
        )
        self.filters.create()

        # Footer Actions (pulsanti)
        self.footer = FooterActions(
            main_container,
            on_comparison=self.open_comparison,
            on_dashboard=self.open_team_dashboard,
            on_build_rosa=self.open_build_rosa
        )
        self.footer.create()

        # Player Table
        self.player_table = PlayerTable(
            main_container,
            self.filtered_df,
            self.price_calculator,
            self.notes_manager,
            on_double_click=self._open_player_details_from_item,
            on_tag_click=self.show_tag_quick_menu,
            favorites_manager=self.favorites_manager,
            on_favorite_toggle=self._on_favorite_changed
        )
        self.player_table.create()

        # Tag Menu
        self.tag_menu = TagMenu(
            self.root,
            self.notes_manager,
            on_tag_toggle=self.populate_players,
            on_open_details=self._open_player_details_from_item
        )

        # Status bar
        self.footer.create_status_bar()

    def apply_filters(self):
        """Applica filtri e aggiorna tabella"""
        if self.df is None:
            return

        # Ottieni valori filtri
        filter_values = self.filters.get_filter_values()
        role = filter_values['role']
        team = filter_values['team']
        search = filter_values['search']
        price_range = filter_values['price_range']
        tag = filter_values['tag']
        fm_min = filter_values['fm_min']
        fm_max = filter_values['fm_max']

        # Applica filtri
        filtered = self.df.copy()

        if role != "Tutti":
            filtered = filtered[filtered['R'].str.startswith(role)]

        if team != "Tutte":
            filtered = filtered[filtered['Squadra'] == team]

        if search:
            filtered = filtered[filtered['Nome'].str.contains(search, case=False, na=False)]

        # Filtro tag
        if tag != "Tutti":
            player_ids_with_tag = self.notes_manager.search_by_tag(tag)
            filtered = filtered[filtered['Id'].isin(player_ids_with_tag)]

        # Filtro percentuale budget
        if price_range != "Tutte":
            player_ids = filtered['Id'].tolist()
            budget = self.budget_var.get()
            price_data = self.price_calculator.calculate_batch_prices(player_ids, budget)

            filtered['price_percentage'] = filtered['Id'].apply(
                lambda pid: price_data.get(pid, {}).get('percentage', 0)
            )

            if price_range == ">30%":
                filtered = filtered[filtered['price_percentage'] > 30]
            else:
                range_parts = price_range.replace('%', '').split('-')
                if len(range_parts) == 2:
                    min_pct = float(range_parts[0])
                    max_pct = float(range_parts[1])
                    filtered = filtered[
                        (filtered['price_percentage'] >= min_pct) &
                        (filtered['price_percentage'] < max_pct)
                    ]

        # Filtro FM
        if fm_min or fm_max:
            fm_values = pd.to_numeric(filtered['Fm_weighted'], errors='coerce')
            if fm_min:
                try:
                    filtered = filtered[fm_values >= float(fm_min)]
                    fm_values = fm_values.loc[filtered.index]
                except ValueError:
                    pass
            if fm_max:
                try:
                    filtered = filtered[fm_values <= float(fm_max)]
                except ValueError:
                    pass

        self.filtered_df = filtered
        self.populate_players()

    def populate_players(self):
        """Popola tabella giocatori"""
        if self.player_table:
            self.favorites_manager._load()
            self.player_table.populate(self.filtered_df, self.budget_var.get())
            self.footer.set_success()

        if self.filters:
            self.filters.update_favorites_count()

    def open_favorites(self):
        """Apri finestra preferiti"""
        FavoritesWindow(
            self.root,
            self.df,
            self.favorites_manager,
            self.price_calculator,
            self.notes_manager,
            self.budget_var.get()
        )

    def _on_favorite_changed(self):
        """Callback chiamato quando cambia lo stato di un preferito"""
        self.favorites_manager._load()
        if self.filters:
            self.filters.update_favorites_count()

    def show_tag_quick_menu(self, item, event):
        """Mostra menu rapido tag per un giocatore"""
        metadata = self.player_table.get_item_metadata(item)
        if not metadata:
            return

        player_id = metadata['player_id']
        values = self.player_table.get_item_values(item)
        name_index = 4 if self.favorites_manager else 3
        player_name = values[name_index]

        self.tag_menu.show(player_id, player_name, item, event)

    def _open_player_details_from_item(self, item):
        """Apre dettagli giocatore da item treeview"""
        metadata = self.player_table.get_item_metadata(item)
        if not metadata:
            return

        player_id = metadata['player_id']
        values = self.player_table.get_item_values(item)
        name_index = 4 if self.favorites_manager else 3
        player_name = values[name_index]
        player_role = metadata['role_str']

        PlayerDetailsWindow(
            self.root,
            player_id,
            player_name,
            player_role,
            self.budget_var.get(),
            on_close_callback=self.populate_players
        )

    def open_comparison(self):
        """Apri confronto giocatori con preloading ottimizzato"""
        if self.df is not None:
            preloaded_data = self.df[['Id', 'Nome', 'Squadra', 'R', 'Fm_weighted', 'Mv_weighted', 'seasons_count', 'Overall']].copy()

            all_player_ids = preloaded_data['Id'].tolist()
            price_data = self.price_calculator.calculate_batch_prices(all_player_ids, self.budget_var.get())

            preloaded_data['price_percentage'] = preloaded_data['Id'].apply(
                lambda pid: price_data.get(pid, {}).get('percentage', 0)
            )

            preloaded_data['display'] = (
                preloaded_data['Nome'] + ' (' +
                preloaded_data['Squadra'] + ' - ' +
                preloaded_data['R'] + ')'
            )

            PlayerComparisonWindow(self.root, self.budget_var.get(), preloaded_data=preloaded_data)
        else:
            PlayerComparisonWindow(self.root, self.budget_var.get())

    def open_team_dashboard(self):
        """Apri dashboard squadre"""
        if hasattr(self, 'filtered_df') and self.filtered_df is not None:
            TeamDashboardWindow(self.root, self.processor, self.filtered_df)
        else:
            TeamDashboardWindow(self.root, self.processor)

    def open_build_rosa(self):
        """Apri finestra Build Rosa"""
        if self.df is not None:
            BuildRosaWindow(
                self.root,
                self.df,
                self.budget_var.get(),
                self.price_calculator,
                self.favorites_manager,
                self.filters.update_favorites_count
            )
        else:
            messagebox.showerror("Errore", "Impossibile caricare i dati dei giocatori")


def main():
    enable_windows_dark_mode()
    root = ctk.CTk()
    app = UltraModernFantaCalcioApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()