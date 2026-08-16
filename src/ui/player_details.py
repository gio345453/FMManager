import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from src.config import STATS_FILES
from src.ui.components.constants import COLORS
from src.ui.window_chrome import configure_application_window
from src.data.cache import DataCache
from src.data.season_overall import calculate_single_season_overall
from src.data.player_notes import PlayerNotesManager
from src.data.favorites_manager import FavoritesManager
from src.data.price_calculator import PriceCalculator
from src.data.titolarita_loader import get_status
from src.utils.data_utils import extract_base_role


class PlayerDetailsWindow:
    """Finestra popup CustomTkinter con dettagli stagionali di un giocatore"""

    def __init__(self, parent, player_id, player_name, player_role, budget=500, on_close_callback=None):
        self.player_id = player_id
        self.player_name = player_name
        self.player_role = extract_base_role(player_role)
        self.budget = budget
        self.cache = DataCache()
        self.notes_manager = PlayerNotesManager()
        self.favorites_manager = FavoritesManager()
        self.price_calculator = PriceCalculator(use_optimized=True)
        self.on_close_callback = on_close_callback

        # Timer per autosalvataggio
        self._save_timer = None

        # Nome squadra del giocatore (sarà caricato dai dati)
        self.player_team = None

        # Crea finestra popup CustomTkinter
        self.window = ctk.CTkToplevel(parent)
        configure_application_window(self.window)
        self.window.title(f"Dettagli: {player_name}")
        self.window.geometry("800x700")
        self.window.configure(fg_color=COLORS['bg_primary'])
        
        self.window.transient(parent)
        self.window.lift()
        self.window.focus_force()

        # Bind evento chiusura
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)

        self._setup_ui()
        self._load_player_data()

    def _setup_ui(self):
        """Configura l'interfaccia usando CTkScrollableFrame"""
        # Main Scrollable Frame moderno
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.window,
            fg_color=COLORS['bg_primary'],
            scrollbar_button_color=COLORS['accent_purple'],
            scrollbar_button_hover_color=COLORS['accent_blue']
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self._build_content()

    def _build_content(self):
        """Costruisce le sezioni con il design system dell'app"""
        # --- HEADER ---
        header_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_container.pack(side="left")

        title_label = ctk.CTkLabel(
            title_container,
            text=f"👤 {self.player_name}",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS['accent_purple']
        )
        title_label.pack(anchor="w")

        # Status titolarità sotto al nome
        status = get_status(self.player_name)
        ctk.CTkLabel(
            title_container,
            text=f"Status: {status}",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        ).pack(anchor="w")

        # Bottone preferiti - solo icona (tra nome e ruolo)
        is_favorite = self.favorites_manager.is_favorite(self.player_id)
        self.favorite_button = ctk.CTkButton(
            header_frame,
            text="⭐" if is_favorite else "☆",
            command=self._toggle_favorite,
            fg_color=COLORS['accent_yellow'] if is_favorite else COLORS['bg_tertiary'],
            hover_color="#FFB703" if is_favorite else COLORS['hover'],
            text_color=COLORS['bg_primary'] if is_favorite else COLORS['text_primary'],
            corner_radius=10,
            width=40,
            height=40,
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.favorite_button.pack(side="left", padx=10)

        role_badge = ctk.CTkFrame(header_frame, fg_color=COLORS['bg_secondary'], corner_radius=8)
        role_badge.pack(side="left", padx=15)

        
        role_code = str(self.player_role)[0].upper() if self.player_role else ''
        role_colors = {
                        'P': '#FFB000',  # Portieri: Giallo / Arancio
                        'D': '#22C55E',  # Difensori: Verde
                        'C': '#3B82F6',  # Centrocampisti: Blu
                        'A': '#EF4444'   # Attaccanti: Rosso
                        }
        color = role_colors.get(role_code, COLORS['accent_blue'])
        ctk.CTkLabel(
            
            role_badge,
            text=f"Ruolo: {self.player_role}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=color
        ).pack(padx=10, pady=5)
        # ctk.CTkLabel(
        #     role_badge,
        #     text=f"Ruolo: {self.player_role}",
        #     font=ctk.CTkFont(size=13, weight="bold"),
        #     text_color=COLORS['accent_blue']
        # ).pack(padx=10, pady=5)

        # Bottone per aprire dettaglio squadra (da implementare)
        self.team_button = None  # Sarà creato dopo aver caricato i dati
        self.header_frame = header_frame  # Salva riferimento per aggiungere bottone dopo

        ctk.CTkButton(
            header_frame,
            text="✕ Chiudi",
            command=self._on_window_close,
            fg_color=COLORS['error'],
            hover_color="#D62A56",
            corner_radius=10,
            width=90,
            height=32,
            font=ctk.CTkFont(weight="bold")
        ).pack(side="right")

        # --- SEZIONE TABELLA STATISTICHE ---
        stats_card = ctk.CTkFrame(self.scrollable_frame, fg_color=COLORS['bg_secondary'], corner_radius=15)
        stats_card.pack(fill="x", pady=(0, 15), padx=2)

        ctk.CTkLabel(
            stats_card,
            text="📊 Storico Stagioni",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Integrazione Treeview personalizzata per la dark mode
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Custom.Treeview",
            background=COLORS['bg_tertiary'],
            foreground=COLORS['text_primary'],
            fieldbackground=COLORS['bg_tertiary'],
            rowheight=28,
            borderwidth=0
        )
        style.configure(
            "Custom.Treeview.Heading",
            background=COLORS['bg_primary'],
            foreground=COLORS['text_secondary'],
            font=('Arial', 10, 'bold')
        )
        style.map("Custom.Treeview", background=[('selected', COLORS['accent_purple'])])

        table_frame = ctk.CTkFrame(stats_card, fg_color="transparent")
        table_frame.pack(fill="x", padx=15, pady=(0, 15))

        columns = ['Stagione', 'Squadra', 'Pv', 'Mv', 'Fm', 'Gf', 'Gs', 'Rp', 'Rc', 'Ass', 'Amm', 'Esp']
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=4, style="Custom.Treeview")

        column_widths = {
            'Stagione': 90, 'Squadra': 110, 'Pv': 45, 'Mv': 55, 'Fm': 55,
            'Gf': 45, 'Gs': 45, 'Rp': 45, 'Rc': 45, 'Ass': 45, 'Amm': 45, 'Esp': 45
        }

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 50), anchor='center')

        self.tree.pack(fill="x", expand=True)

        # Label stagione migliore
        self.best_season_label = ctk.CTkLabel(
            stats_card,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS['accent_green']
        )
        self.best_season_label.pack(pady=(0, 15))

        # --- SEZIONE VALUTAZIONE PREZZO ---
        self.price_card = ctk.CTkFrame(self.scrollable_frame, fg_color=COLORS['bg_secondary'], corner_radius=15)
        self.price_card.pack(fill="x", pady=(0, 15), padx=2)

        ctk.CTkLabel(
            self.price_card,
            text="💰 Valutazione Prezzo Massimo Consigliato",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(anchor="w", padx=15, pady=(15, 10))

        self.price_info_frame = ctk.CTkFrame(self.price_card, fg_color="transparent")
        self.price_info_frame.pack(fill="x", padx=15, pady=(0, 15))

        # --- SEZIONE NOTE E TAG ---
        notes_card = ctk.CTkFrame(self.scrollable_frame, fg_color=COLORS['bg_secondary'], corner_radius=15)
        notes_card.pack(fill="x", pady=(0, 15), padx=2)

        ctk.CTkLabel(
            notes_card,
            text="📝 Note e Tag Personali",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Tag entry
        tag_frame = ctk.CTkFrame(notes_card, fg_color="transparent")
        tag_frame.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(tag_frame, text="Tag/Etichette:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 10))

        self.tags_entry = ctk.CTkEntry(
            tag_frame,
            placeholder_text="es. obiettivo, titolare",
            fg_color=COLORS['bg_tertiary'],
            border_color=COLORS['border'],
            width=300
        )
        self.tags_entry.pack(side="left", fill="x", expand=True)

        # Autosalvataggio tag
        self.tags_entry.bind("<KeyRelease>", self._on_tags_change)
        self.tags_entry.bind("<FocusOut>", lambda e: self._auto_save_notes_and_tags())

        # Suggerimenti tag rapidi
        tag_buttons_frame = ctk.CTkFrame(notes_card, fg_color="transparent")
        tag_buttons_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(tag_buttons_frame, text="Tag rapidi:", font=ctk.CTkFont(size=11), text_color=COLORS['text_secondary']).pack(side="left", padx=(0, 10))

        common_tags = ["obiettivo", "da evitare", "esca", "riserva", "titolare", "occasione"]
        for tag in common_tags:
            ctk.CTkButton(
                tag_buttons_frame,
                text=tag,
                command=lambda t=tag: self._add_quick_tag(t),
                fg_color=COLORS['bg_tertiary'],
                hover_color=COLORS['accent_purple'],
                height=26,
                corner_radius=6,
                font=ctk.CTkFont(size=11)
            ).pack(side="left", padx=3)

        # Note Textbox
        ctk.CTkLabel(notes_card, text="Note Personali:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15, pady=(5, 5))

        self.notes_text = ctk.CTkTextbox(
            notes_card,
            height=100,
            fg_color=COLORS['bg_tertiary'],
            border_color=COLORS['border'],
            corner_radius=10
        )
        self.notes_text.pack(fill="x", padx=15, pady=(0, 10))

        # Autosalvataggio note
        self.notes_text.bind("<KeyRelease>", self._on_notes_change)
        self.notes_text.bind("<FocusOut>", lambda e: self._auto_save_notes_and_tags())

        # Label status autosalvataggio
        self.save_status_label = ctk.CTkLabel(
            notes_card,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['accent_green']
        )
        self.save_status_label.pack(anchor="e", padx=15, pady=(0, 15))

        self._load_notes_and_tags()

        # --- FOOTER BOTTONI ---
        button_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        button_frame.pack(pady=10)

        ctk.CTkButton(
            button_frame,
            text="📈 Visualizza Trend",
            command=self._show_trend_graph,
            fg_color=COLORS['accent_purple'],
            hover_color="#8E44AD",
            corner_radius=10,
            height=38,
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=8)

    def _on_tags_change(self, event):
        """Gestisce cambiamento tag per autosalvataggio"""
        if self._save_timer:
            self.window.after_cancel(self._save_timer)
        self._save_timer = self.window.after(800, self._auto_save_notes_and_tags)

    def _on_notes_change(self, event):
        """Gestisce cambiamento note per autosalvataggio"""
        if self._save_timer:
            self.window.after_cancel(self._save_timer)
        self._save_timer = self.window.after(800, self._auto_save_notes_and_tags)

    def _auto_save_notes_and_tags(self):
        """Salva automaticamente note e tag"""
        self._save_notes_and_tags(show_message=False)
        self.save_status_label.configure(text="✓ Salvato automaticamente")
        self.window.after(2000, lambda: self.save_status_label.configure(text=""))

    def _on_window_close(self):
        """Gestisce la chiusura e chiama il callback"""
        try:
            if self.on_close_callback:
                self.on_close_callback()
        except Exception as e:
            print(f"Errore nel callback di chiusura: {e}")
        finally:
            try:
                self.window.grab_release()
            except:
                pass
            self.window.destroy()

    def _show_trend_graph(self):
        """Apre la finestra con i grafici di trend"""
        from src.ui.trend_graph import TrendGraphWindow
        TrendGraphWindow(self.window, self.player_id, self.player_name, self.player_role)

    def _load_player_data(self):
        """Carica e visualizza i dati del giocatore per tutte le stagioni"""
        from src.config import get_season_labels

        season_names = get_season_labels()

        seasons_data = []

        for season_key, (filename, _) in STATS_FILES.items():
            df = self.cache.get(filename)
            if df is not None:
                player_data = df[df['Id'] == self.player_id]

                if not player_data.empty:
                    row = player_data.iloc[0]

                    stats = {
                        'Pv': row.get('Pv', 0),
                        'Mv': row.get('Mv', 0),
                        'Fm': row.get('Fm', 0),
                        'Gf': row.get('Gf', 0),
                        'Gs': row.get('Gs', 0),
                        'Rp': row.get('Rp', 0),
                        'Rc': row.get('Rc', 0),
                        'Ass': row.get('Ass', 0),
                        'Amm': row.get('Amm', 0),
                        'Esp': row.get('Esp', 0)
                    }

                    overall = calculate_single_season_overall(stats, self.player_role)

                    season_info = {
                        'season_key': season_key,
                        'season_name': season_names.get(season_key, 'N/A'),
                        'squadra': row.get('Squadra', 'N/A'),
                        'stats': stats,
                        'overall': overall if overall is not None else 0
                    }

                    seasons_data.append(season_info)

                    # Salva squadra più recente (dalla stagione recent o dalla prima disponibile)
                    if season_key == 'recent':
                        self.player_team = row.get('Squadra', 'N/A')
                    elif not self.player_team:  # Se non c'è recent, prendi la prima disponibile
                        self.player_team = row.get('Squadra', 'N/A')

        season_order = {'recent': 0, 'middle': 1, 'old': 2}
        seasons_data.sort(key=lambda x: season_order.get(x['season_key'], 3))

        best_season = None
        if seasons_data:
            best_season = max(seasons_data, key=lambda x: x['overall'])

        for season in seasons_data:
            values = [
                season['season_name'],
                season['squadra'],
                season['stats']['Pv'],
                f"{season['stats']['Mv']:.2f}" if season['stats']['Mv'] else 'N/A',
                f"{season['stats']['Fm']:.2f}" if season['stats']['Fm'] else 'N/A',
                season['stats']['Gf'],
                season['stats']['Gs'],
                season['stats']['Rp'],
                season['stats']['Rc'],
                season['stats']['Ass'],
                season['stats']['Amm'],
                season['stats']['Esp']
            ]

            item_id = self.tree.insert('', tk.END, values=values)

            if season == best_season:
                self.tree.item(item_id, tags=('best',))

        self.tree.tag_configure('best', background='#1E3A2B', foreground='#2ECC71')

        if best_season:
            self.best_season_label.configure(
                text=f"⭐ Stagione migliore: {best_season['season_name']} ({best_season['squadra']})"
            )

        # Crea bottone per aprire dettaglio squadra dopo aver caricato i dati
        self._add_team_button()

        self._load_price_evaluation()

    def _load_price_evaluation(self):
        """Carica e visualizza la valutazione del prezzo consigliato con layout CTk"""
        try:
            from src.data_processor import FantaCalcioDataProcessor
            processor = FantaCalcioDataProcessor()
            all_players_df = processor.calculate_weighted_stats()
            if all_players_df is not None:
                all_players_df = processor.calculate_overall_scores(all_players_df)
                self.price_calculator.update_players_data(all_players_df)
        except Exception:
            pass

        price_data = self.price_calculator.calculate_price_percentage(self.player_id, self.budget)

        for widget in self.price_info_frame.winfo_children():
            widget.destroy()

        # Riga principali
        main_info = ctk.CTkFrame(self.price_info_frame, fg_color=COLORS['bg_tertiary'], corner_radius=10)
        main_info.pack(fill="x", pady=(0, 10))

        # Gestisci entrambi i formati (optimized usa 'price', classico usa 'credits')
        credits = price_data.get('credits') or int(price_data.get('price', 0))
        budget = price_data.get('budget', self.budget)
        percentage = price_data.get('percentage', 0)

        ctk.CTkLabel(
            main_info,
            text=f"{credits} su {budget} crediti",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['accent_blue']
        ).pack(side="left", padx=15, pady=10)

        ctk.CTkLabel(
            main_info,
            text=f"Percentuale Budget: {percentage}%",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS['accent_green']
        ).pack(side="right", padx=15, pady=10)

    def _load_notes_and_tags(self):
        """Carica note e tag dal manager"""
        tags = self.notes_manager.get_tags(self.player_id)
        self.tags_entry.delete(0, tk.END)
        self.tags_entry.insert(0, ', '.join(tags))

        note = self.notes_manager.get_note(self.player_id)
        self.notes_text.delete('1.0', tk.END)
        self.notes_text.insert('1.0', note)

    def _save_notes_and_tags(self, show_message=True):
        """Salva note e tag nel manager"""
        tags_text = self.tags_entry.get().strip()
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        self.notes_manager.set_tags(self.player_id, tags)

        note = self.notes_text.get('1.0', tk.END).strip()
        self.notes_manager.set_note(self.player_id, note)

        if show_message:
            self._on_window_close()

    def _add_quick_tag(self, tag: str):
        """Aggiunge rapidamente un tag predefinito"""
        current_tags = self.tags_entry.get().strip()
        existing_tags = [t.strip() for t in current_tags.split(',') if t.strip()]

        if tag not in existing_tags:
            if current_tags:
                self.tags_entry.insert(tk.END, f", {tag}")
            else:
                self.tags_entry.insert(0, tag)
            # Salva automaticamente dopo aggiunta tag rapido
            self._auto_save_notes_and_tags()

    def _toggle_favorite(self):
        """Toggle stato preferito del giocatore"""
        is_now_favorite = self.favorites_manager.toggle_favorite(self.player_id)

        # Aggiorna bottone - solo icona
        if is_now_favorite:
            self.favorite_button.configure(
                text="⭐",
                fg_color=COLORS['accent_yellow'],
                hover_color="#FFB703",
                text_color=COLORS['bg_primary']
            )
        else:
            self.favorite_button.configure(
                text="☆",
                fg_color=COLORS['bg_tertiary'],
                hover_color=COLORS['hover'],
                text_color=COLORS['text_primary']
            )

        # Chiama il callback per aggiornare la tabella principale
        if self.on_close_callback:
            self.on_close_callback()

    def _add_team_button(self):
        """Aggiunge bottone per aprire dettaglio squadra dopo aver caricato i dati"""
        # Mostra bottone solo se abbiamo una squadra valida (non vuota e non N/A)
        if not self.player_team or self.player_team == 'N/A' or str(self.player_team).strip() == '':
            return

        self.team_button = ctk.CTkButton(
            self.header_frame,
            text="🏟️ Info Squadra",
            command=self._open_team_detail,
            fg_color=COLORS['spotify_green'],
            hover_color=COLORS['spotify_green_hover'],
            corner_radius=8,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        # Inserisci dopo il role_badge
        self.team_button.pack(side="left", padx=5)

    def _open_team_detail(self):
        """Apre finestra dettaglio squadra in modalità compatta (1/4 schermo)"""
        if not self.player_team:
            return

        try:
            from src.data_processor import FantaCalcioDataProcessor
            from src.data.team_stats import TeamStatsManager
            from src.ui.team_detail_window import CompactTeamDetailWindow

            # Usa il processor per ottenere i dati ponderati (come nella lista principale)
            processor = FantaCalcioDataProcessor()
            weighted_df = processor.calculate_weighted_stats()

            if weighted_df is None:
                messagebox.showerror("Errore", "Impossibile caricare i dati")
                return

            df_with_overall = processor.calculate_overall_scores(weighted_df)

            # Trova la squadra ATTUALE del giocatore dai dati ponderati (quella mostrata nella lista)
            player_row = df_with_overall[df_with_overall['Id'] == self.player_id]
            if player_row.empty:
                messagebox.showerror("Errore", "Giocatore non trovato")
                return

            current_team = player_row.iloc[0]['Squadra']

            # Carica statistiche squadra dalla stagione 2025-26
            team_stats_manager = TeamStatsManager()
            team_stats = team_stats_manager.get_team_stats(current_team)

            if not team_stats:
                messagebox.showwarning("Attenzione", f"Statistiche non disponibili per {current_team}")
                return

            # Apri finestra dettaglio squadra compatta
            detail_window = CompactTeamDetailWindow(
                self.window,
                current_team,
                team_stats,
                df_with_overall,
                processor,
                self.price_calculator,
                self.notes_manager,
                self._handle_player_double_click,
                self._handle_tag_click,
                budget=self.budget
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Errore", f"Impossibile aprire dettaglio squadra: {e}")

    def _handle_player_double_click(self, item, df_with_overall):
        """Gestisce doppio click su giocatore nella tabella squadra"""
        # Non fare nulla per ora, evita di aprire altre finestre
        pass

    def _handle_tag_click(self, item, event):
        """Gestisce click su tag nella tabella squadra"""
        # Non fare nulla per ora
        pass