"""
Componente PlayerTable - Tabella giocatori con Treeview
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import pandas as pd
from .constants import COLORS
from src.ui.window_chrome import configure_application_window
from src.utils.data_utils import extract_value_and_trend, extract_base_role, extract_values_and_trends_batch


# Dizionario tooltip per le colonne
COLUMN_TOOLTIPS = {
    '⭐': 'Preferiti - Click per aggiungere/rimuovere',
    'OVR': 'Overall - Valutazione complessiva (ponderata)',
    'Prezzo Max': '% Budget prezzo massimo',
    'Tit': 'Titolarità - Percentuale di titolarità',
    'Nome': 'Nome del Giocatore',
    'Tag': 'Tag Personalizzati - Click per modificare',
    'Note': 'Note Personali',
    'Squadra': 'Squadra di appartenenza',
    'R': 'Ruolo - P (Portiere), D (Difensore), C (Centrocampista), A (Attaccante)',
    'Fm': 'Fantamedia (ponderata)',
    'Mv': 'Media Voto (ponderata)',
    'Pv': 'Partite giocate (ponderata)',
    'Gf': 'Goal Fatti (ponderata)',
    'Ass': 'Assist (ponderata)',
    'Rp': 'Rigori Parati (ponderata)',
    'Gs': 'Goal Subiti (ponderata)'
}


class PlayerTable:
    """Componente tabella giocatori con Treeview"""

    def __init__(self, parent, filtered_df, price_calculator, notes_manager, on_double_click, on_tag_click, favorites_manager=None, on_favorite_toggle=None, enable_horizontal_scroll=False, show_title=True):
        """
        Inizializza tabella giocatori

        Args:
            parent: Frame genitore
            filtered_df: DataFrame filtrato con giocatori da mostrare
            price_calculator: Istanza di PriceCalculator
            notes_manager: Istanza di PlayerNotesManager
            on_double_click: Callback per doppio click (apre dettagli)
            on_tag_click: Callback per click su colonna tag (apre menu)
            favorites_manager: Istanza di FavoritesManager (opzionale)
            on_favorite_toggle: Callback chiamato quando si toglie un preferito (opzionale)
            enable_horizontal_scroll: Abilita scroll orizzontale (default False)
            show_title: Mostra titolo "Lista Giocatori" (default True)
        """
        self.parent = parent
        self.filtered_df = filtered_df
        self.price_calculator = price_calculator
        self.notes_manager = notes_manager
        self.favorites_manager = favorites_manager
        self.on_double_click_callback = on_double_click
        self.on_tag_click_callback = on_tag_click
        self.on_favorite_toggle_callback = on_favorite_toggle
        self.enable_horizontal_scroll = enable_horizontal_scroll
        self.show_title = show_title

        # Widget
        self.data_card = None
        self.tree = None
        self.tree_item_map = {}
        self.loading_task = None

        # Gestione ritardo click colonna Tag (per distinguere singolo da doppio click)
        self._tag_click_after_id = None
        self._tag_click_delay_ms = 350

        # Stato ordinamento
        self.sort_column = None
        self.sort_reverse = False

        # Istanza stile condivisa
        self.style = ttk.Style()

        # Carica dati titolarità
        self.titolarita_data = self._load_titolarita_data()

        # Configura stile Treeview una sola volta
        self._setup_treeview_style()

    def _setup_treeview_style(self):
        """Configura lo stile Treeview una sola volta"""
        self.style.theme_use('default')

        self.style.configure(
            "Custom.Treeview",
            background=COLORS['bg_tertiary'],
            foreground=COLORS['text_primary'],
            fieldbackground=COLORS['bg_tertiary'],
            borderwidth=0,
            relief="flat",
            rowheight=42,  # Aumentato da 37 a 42
            font=('Arial', 12)
        )

        self.style.configure(
            "Custom.Treeview.Heading",
            background=COLORS['bg_primary'],
            foreground=COLORS['accent_purple'],
            borderwidth=0,
            relief="flat",
            font=('Arial', 15, 'bold')  # Aumentato da 13 a 15
        )

        # Mantieni i colori originali anche quando selezionato
        self.style.map(
            'Custom.Treeview',
            background=[],
            foreground=[]
        )

        self.style.map(
            'Custom.Treeview.Heading',
            background=[('active', COLORS['bg_primary'])],
            foreground=[('active', COLORS['accent_purple'])]
        )

    def _load_titolarita_data(self):
        """Carica i dati di titolarità dal file JSON (modulo condiviso)"""
        from src.data.titolarita_loader import load_titolarita_map
        return load_titolarita_map()

    def _get_titolarita(self, player_name):
        """Restituisce la percentuale di titolarità per un giocatore"""
        return self.titolarita_data.get(player_name, 'IND')

    def create(self):
        """Crea e mostra la tabella"""
        # Card principale
        self.data_card = ctk.CTkFrame(self.parent, fg_color=COLORS['bg_secondary'], corner_radius=15)
        self.data_card.pack(fill="both", expand=True, padx=0, pady=0)

        # Header con titolo (opzionale)
        if self.show_title:
            header = ctk.CTkFrame(self.data_card, fg_color="transparent")
            header.pack(fill="x", padx=20, pady=(15, 10))

            ctk.CTkLabel(
                header,
                text="📋 Lista Giocatori",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=COLORS['text_primary']
            ).pack(side="left")
            ctk.CTkLabel(
            header,
            text="  I giocatori con * hanno una sola stagione di dati ",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color=COLORS.get('text_secondary', '#A0A0A0')
        ).pack(side="left", padx=(5, 0))

            # Pulsante scarica listone
            ctk.CTkButton(
                header,
                text="📥 Scarica ultimo listone disponibile",
                command=self._download_latest_quotazioni,
                height=32,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=COLORS['button_green'],
                hover_color=COLORS['button_green_hover'],
                corner_radius=8
            ).pack(side="right", padx=(0, 10))

            # Pulsante aggiornamento fine stagione (attivo solo 15 luglio - 18 agosto)
            self._create_season_update_button(header)

        # Frame Treeview con scrollbar
        tree_frame = ctk.CTkFrame(self.data_card, fg_color="transparent")
        padding_top = 0 if not self.show_title else 0
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(padding_top, 15))

        # Colonne: Stella (se favorites_manager) → OVR → Prezzo Massimo → Tit → Nome → Tag → Note → Squadra → R → Stats
        if self.favorites_manager:
            columns = ('⭐', 'OVR', 'Prezzo Max', 'Tit', 'Nome', 'Tag', 'Note', 'Squadra', 'R', 'Fm', 'Mv', 'Pv', 'Gf', 'Ass', 'Rp', 'Gs')
        else:
            columns = ('OVR', 'Prezzo Max', 'Tit', 'Nome', 'Tag', 'Note', 'Squadra', 'R', 'Fm', 'Mv', 'Pv', 'Gf', 'Ass', 'Rp', 'Gs')

        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            style="Custom.Treeview",
            selectmode='browse'
        )

        # Configura colonne
        if self.favorites_manager:
            column_widths = {
                '⭐': 40,
                'OVR': 60,
                'Prezzo Max': 70,
                'Tit': 70,
                'Nome': 180,
                'Tag': 140,
                'Note': 180,
                'Squadra': 100,
                'R': 40,
                'Fm': 50,
                'Mv': 50,
                'Pv': 40,
                'Gf': 40,
                'Ass': 40,
                'Rp': 40,
                'Gs': 40
            }
        else:
            column_widths = {
                'OVR': 60,
                'Prezzo Max': 70,
                'Tit': 70,
                'Nome': 180,
                'Tag': 140,
                'Note': 180,
                'Squadra': 100,
                'R': 40,
                'Fm': 50,
                'Mv': 50,
                'Pv': 40,
                'Gf': 40,
                'Ass': 40,
                'Rp': 40,
                'Gs': 40
            }

        for col in columns:
            self.tree.heading(col, text=col, anchor='center', command=lambda c=col: self._sort_by_column(c))
            self.tree.column(col, width=column_widths.get(col, 80), anchor='center')

        # Aggiungi tooltip alle intestazioni
        self._setup_column_tooltips()

        # Scrollbar verticale
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_y.set)

        # Scrollbar orizzontale (solo se abilitata)
        if self.enable_horizontal_scroll:
            scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
            self.tree.configure(xscrollcommand=scrollbar_x.set)
            scrollbar_x.pack(side="bottom", fill="x")

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")

        # Tag per righe alternate
        self.tree.tag_configure('evenrow', background=COLORS['bg_tertiary'])
        self.tree.tag_configure('oddrow', background='#252535')

        # Event handlers
        self.tree.bind('<Button-1>', self.on_tree_single_click)
        self.tree.bind('<Double-Button-1>', self.on_tree_double_click)

        return self.data_card

    def _setup_column_tooltips(self):
        """Crea tooltip per le intestazioni delle colonne"""
        self.tooltip_label = None
        self.tree.bind('<Motion>', self._on_tree_motion)
        self.tree.bind('<Leave>', self._hide_tooltip)

    def _on_tree_motion(self, event):
        """Mostra tooltip quando il mouse passa sopra un'intestazione"""
        region = self.tree.identify_region(event.x, event.y)

        if region == "heading":
            column = self.tree.identify_column(event.x)
            col_index = int(column.replace('#', '')) - 1

            if self.favorites_manager:
                columns = ('⭐', 'OVR', 'Prezzo Max', 'Tit', 'Nome', 'Tag', 'Note', 'Squadra', 'R', 'Fm', 'Mv', 'Pv', 'Gf', 'Ass', 'Rp', 'Gs')
            else:
                columns = ('OVR', 'Prezzo Max', 'Tit', 'Nome', 'Tag', 'Note', 'Squadra', 'R', 'Fm', 'Mv', 'Pv', 'Gf', 'Ass', 'Rp', 'Gs')

            if 0 <= col_index < len(columns):
                col_name = columns[col_index]
                tooltip_text = COLUMN_TOOLTIPS.get(col_name, col_name)
                self._show_tooltip(event.x_root, event.y_root, tooltip_text)
        else:
            self._hide_tooltip()

    def _show_tooltip(self, x, y, text):
        """Mostra tooltip in posizione specifica"""
        if self.tooltip_label:
            self.tooltip_label.destroy()

        self.tooltip_label = tk.Toplevel(self.tree)
        self.tooltip_label.wm_overrideredirect(True)
        self.tooltip_label.wm_geometry(f"+{x+10}+{y+10}")

        label = tk.Label(
            self.tooltip_label,
            text=text,
            background=COLORS['bg_secondary'],
            foreground=COLORS['text_primary'],
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 10),
            padx=8,
            pady=4
        )
        label.pack()

    def _hide_tooltip(self, event=None):
        """Nasconde tooltip"""
        if self.tooltip_label:
            self.tooltip_label.destroy()
            self.tooltip_label = None

    def populate(self, filtered_df, budget):
        """
        Popola Treeview con frecce trend solo per stats rilevanti per ruolo

        Args:
            filtered_df: DataFrame filtrato con giocatori da mostrare
            budget: Budget corrente per calcolo prezzi
        """
        if self.loading_task:
            self.loading_task = None

        # Ricarica lo stato dei preferiti se disponibile
        if self.favorites_manager:
            self.favorites_manager._load()

        # Riapplica lo stile per sicurezza
        self.style.configure(
            "Custom.Treeview.Heading",
            background=COLORS['bg_primary'],
            foreground=COLORS['accent_purple'],
            borderwidth=0,
            relief="flat",
            font=('Arial', 15, 'bold')  # Aumentato da 13 a 15
        )

        self.style.map(
            'Custom.Treeview.Heading',
            background=[('active', COLORS['bg_primary'])],
            foreground=[('active', COLORS['accent_purple'])]
        )

        # Pulisci treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.tree_item_map = {}

        if filtered_df is None or filtered_df.empty:
            return

        self.filtered_df = filtered_df

        # Calcola prezzi batch
        all_player_ids = filtered_df['Id'].tolist()
        price_data = self.price_calculator.calculate_batch_prices(all_player_ids, budget)

        # PRE-CALCOLA TUTTI I VALORI E TREND IN BATCH (OTTIMIZZAZIONE H1)
        # Invece di 4800+ chiamate individuali, facciamo 7 operazioni vettoriali
        fm_data = extract_values_and_trends_batch(filtered_df['Fm_weighted'])
        mv_data = extract_values_and_trends_batch(filtered_df['Mv_weighted'])
        pv_data = extract_values_and_trends_batch(filtered_df['Pv_weighted'])
        gf_data = extract_values_and_trends_batch(filtered_df['Gf_weighted'])
        ass_data = extract_values_and_trends_batch(filtered_df['Ass_weighted'])
        rp_data = extract_values_and_trends_batch(filtered_df['Rp_weighted'])
        gs_data = extract_values_and_trends_batch(filtered_df['Gs_weighted'])

        for idx, row in filtered_df.iterrows():
            player_id = row['Id']
            price_calc = price_data.get(player_id, {'percentage': 1.0})

            try:
                overall_val = int(float(row['Overall'])) if pd.notna(row['Overall']) else 0
            except:
                overall_val = 0

            # Usa il ruolo completo con (T;E) dalla colonna R
            role_display = row['R']
            # Estrai solo il ruolo base per la logica di visualizzazione trend
            role_str = extract_base_role(row['R'])

            # USA I VALORI PRE-CALCOLATI (accesso diretto, no chiamate funzione)
            fm_val, fm_trend = fm_data.loc[idx, 'value'], fm_data.loc[idx, 'trend']
            mv_val, mv_trend = mv_data.loc[idx, 'value'], mv_data.loc[idx, 'trend']
            pv_val, pv_trend = pv_data.loc[idx, 'value'], pv_data.loc[idx, 'trend']
            gf_val, gf_trend = gf_data.loc[idx, 'value'], gf_data.loc[idx, 'trend']
            ass_val, ass_trend = ass_data.loc[idx, 'value'], ass_data.loc[idx, 'trend']
            rp_val, rp_trend = rp_data.loc[idx, 'value'], rp_data.loc[idx, 'trend']
            gs_val, gs_trend = gs_data.loc[idx, 'value'], gs_data.loc[idx, 'trend']

            # Mostra trend SOLO per stats usate nel calcolo Overall di quel ruolo
            # P: Fm, Mv, Pv, Rp, Gs
            # D: Fm, Mv, Pv, Gf, Ass
            # C: Fm, Mv, Pv, Gf, Ass
            # A: Gf, Ass, Fm, Mv, Pv

            if role_str == 'P':
                fm_display = f"{fm_val:.1f}{fm_trend}"
                mv_display = f"{mv_val:.1f}{mv_trend}"
                pv_display = f"{pv_val:.0f}{pv_trend}"
                gf_display = f"{gf_val:.0f}"
                ass_display = f"{ass_val:.0f}"
                rp_display = f"{rp_val:.0f}{rp_trend}"
                gs_display = f"{gs_val:.0f}{gs_trend}"
            elif role_str == 'D':
                fm_display = f"{fm_val:.1f}{fm_trend}"
                mv_display = f"{mv_val:.1f}{mv_trend}"
                pv_display = f"{pv_val:.0f}{pv_trend}"
                gf_display = f"{gf_val:.0f}{gf_trend}"
                ass_display = f"{ass_val:.0f}{ass_trend}"
                rp_display = f"{rp_val:.0f}"
                gs_display = f"{gs_val:.0f}"
            elif role_str == 'C':
                fm_display = f"{fm_val:.1f}{fm_trend}"
                mv_display = f"{mv_val:.1f}{mv_trend}"
                pv_display = f"{pv_val:.0f}{pv_trend}"
                gf_display = f"{gf_val:.0f}{gf_trend}"
                ass_display = f"{ass_val:.0f}{ass_trend}"
                rp_display = f"{rp_val:.0f}"
                gs_display = f"{gs_val:.0f}"
            elif role_str == 'A':
                fm_display = f"{fm_val:.1f}{fm_trend}"
                mv_display = f"{mv_val:.1f}{mv_trend}"
                pv_display = f"{pv_val:.0f}{pv_trend}"
                gf_display = f"{gf_val:.0f}{gf_trend}"
                ass_display = f"{ass_val:.0f}{ass_trend}"
                rp_display = f"{rp_val:.0f}"
                gs_display = f"{gs_val:.0f}"
            else:
                # Default: mostra tutto senza trend
                fm_display = f"{fm_val:.1f}"
                mv_display = f"{mv_val:.1f}"
                pv_display = f"{pv_val:.0f}"
                gf_display = f"{gf_val:.0f}"
                ass_display = f"{ass_val:.0f}"
                rp_display = f"{rp_val:.0f}"
                gs_display = f"{gs_val:.0f}"

            # Prepara valori riga
            if self.favorites_manager:
                # Con stella
                star = "⭐" if self.favorites_manager.is_favorite(player_id) else "☆"
                values = (
                    star,
                    overall_val,
                    f"{price_calc['percentage']}%",
                    self._get_titolarita(row['Nome']),
                    row['Nome'],
                    self.notes_manager.get_tags_string(player_id),
                    self.notes_manager.get_note_preview(player_id, max_length=40),
                    row['Squadra'],
                    role_display,  # Usa role_display con (T;E)
                    fm_display,
                    mv_display,
                    pv_display,
                    gf_display,
                    ass_display,
                    rp_display,
                    gs_display
                )
            else:
                # Senza stella
                values = (
                    overall_val,
                    f"{price_calc['percentage']}%",
                    self._get_titolarita(row['Nome']),
                    row['Nome'],
                    self.notes_manager.get_tags_string(player_id),
                    self.notes_manager.get_note_preview(player_id, max_length=40),
                    row['Squadra'],
                    role_display,  # Usa role_display con (T;E)
                    fm_display,
                    mv_display,
                    pv_display,
                    gf_display,
                    ass_display,
                    rp_display,
                    gs_display
                )

            # Determina tag per righe alternate
            row_index = len(self.tree.get_children())
            row_tag = 'evenrow' if row_index % 2 == 0 else 'oddrow'

            item_id = self.tree.insert('', 'end', values=values, tags=(row_tag,))

            self.tree_item_map[item_id] = {
                'player_id': player_id,
                'overall_val': overall_val,
                'role_str': role_str
            }

        # Deseleziona tutto per mantenere lo stile pulito
        self.tree.selection_remove(self.tree.selection())

        # Riapplica l'ordinamento corrente se esiste
        if self.sort_column:
            self._sort_by_column(self.sort_column, preserve_direction=True)

    def _extract_value_and_trend(self, raw_val):
        """
        DEPRECATED: Usa extract_value_and_trend da utils invece
        Estrae valore numerico e simbolo trend da una stringa

        Args:
            raw_val: Valore grezzo (può contenere frecce)

        Returns:
            tuple: (valore_float, trend_string)
        """
        value, trend_symbol = extract_value_and_trend(raw_val)
        # Aggiungi spazio al trend per retrocompatibilità
        trend = f' {trend_symbol}' if trend_symbol else ''
        return value if value is not None else 0.0, trend

    def _sort_by_column(self, col, preserve_direction=False):
        """
        Ordina treeview per colonna cliccata

        Args:
            col: Nome della colonna da ordinare
            preserve_direction: Se True, mantiene la direzione corrente invece di invertirla
        """
        # Determina direzione ordinamento
        if self.sort_column == col and not preserve_direction:
            self.sort_reverse = not self.sort_reverse
        elif self.sort_column != col:
            self.sort_column = col
            self.sort_reverse = False

        # Ottieni indice colonna (adatta in base a presenza stella)
        if self.favorites_manager:
            columns = ('⭐', 'OVR', 'Prezzo Max', 'Tit', 'Nome', 'Tag', 'Note', 'Squadra', 'R', 'Fm', 'Mv', 'Pv', 'Gf', 'Ass', 'Rp', 'Gs')
        else:
            columns = ('OVR', 'Prezzo Max', 'Tit', 'Nome', 'Tag', 'Note', 'Squadra', 'R', 'Fm', 'Mv', 'Pv', 'Gf', 'Ass', 'Rp', 'Gs')

        col_index = columns.index(col)

        # Estrai tutti gli item con i loro valori
        items = []
        for item_id in self.tree.get_children(''):
            values = self.tree.item(item_id, 'values')
            items.append((item_id, values))

        # Funzione di sorting personalizzata
        def sort_key(item):
            value = item[1][col_index]

            # Rimuovi simboli trend per ordinamento numerico
            if col in ('Fm', 'Mv', 'Pv', 'Gf', 'Ass', 'Rp', 'Gs'):
                from src.utils.data_utils import clean_numeric_value
                numeric_val = clean_numeric_value(value)
                return numeric_val if numeric_val is not None else 0.0
            elif col in ('OVR',):
                try:
                    return int(value)
                except:
                    return 0
            elif col == 'Prezzo Max':
                # Rimuovi % per ordinamento
                try:
                    return float(str(value).replace('%', ''))
                except:
                    return 0.0
            elif col == 'Tit':
                # Rimuovi % per ordinamento titolarità
                try:
                    val_str = str(value).replace('%', '').strip()
                    if val_str == '-':
                        return -1  # Metti i '-' alla fine
                    return float(val_str)
                except:
                    return -1
            else:
                # Ordinamento alfabetico
                return str(value).lower()

        # Ordina
        items.sort(key=sort_key, reverse=self.sort_reverse)

        # Riposiziona items nell'ordine ordinato e riapplica colori alternati
        for index, (item_id, values) in enumerate(items):
            self.tree.move(item_id, '', index)
            # Riapplica tag per colori alternati
            row_tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.tree.item(item_id, tags=(row_tag,))

        # Aggiorna indicatore direzione nell'header
        for c in columns:
            if c == col:
                arrow = ' ↓' if self.sort_reverse else ' ↑'
                self.tree.heading(c, text=f"{c}{arrow}")
            else:
                self.tree.heading(c, text=c)

        # Scrolla automaticamente in cima dopo l'ordinamento
        if not preserve_direction:
            self.tree.yview_moveto(0)

    def on_tree_single_click(self, event):
        """Gestisce click singolo sulla colonna Tag o Stella"""
        try:
            region = self.tree.identify_region(event.x, event.y)
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)

            if region != "cell" or not item:
                return

            # Se favorites_manager è attivo, la stella è colonna #1
            if self.favorites_manager and column == '#1':
                # Click sulla stella - toggle preferito
                self._toggle_favorite(item)
                return "break"

            # Colonna Tag (varia in base a presenza stella)
            tag_column = '#5' if not self.favorites_manager else '#6'
            if column == tag_column:
                self.tree.selection_set(item)

                # Non aprire subito il menu: attendi per verificare se si tratta
                # di un doppio click (che deve aprire solo il dettaglio giocatore,
                # non il menu rapido tag). Se arriva un doppio click, questo
                # timer viene annullato in on_tree_double_click.
                if self._tag_click_after_id is not None:
                    self.tree.after_cancel(self._tag_click_after_id)

                self._tag_click_after_id = self.tree.after(
                    self._tag_click_delay_ms,
                    lambda: self._open_tag_menu_delayed(item, event)
                )
                return "break"
        except Exception as e:
            print(f"ERROR in on_tree_single_click: {e}")
            import traceback
            traceback.print_exc()

    def _open_tag_menu_delayed(self, item, event):
        """Apre il menu rapido tag dopo il ritardo anti-doppio-click"""
        self._tag_click_after_id = None
        self.on_tag_click_callback(item, event)

    def on_tree_double_click(self, event):
        """Gestisce doppio click - apre SEMPRE e solo i dettagli giocatore,
        anche se il doppio click avviene sulla colonna Tag"""
        # Annulla l'apertura ritardata del menu tag rapido, se in corso
        if self._tag_click_after_id is not None:
            self.tree.after_cancel(self._tag_click_after_id)
            self._tag_click_after_id = None

        item = self.tree.identify_row(event.y)
        if not item:
            return

        metadata = self.tree_item_map.get(item)
        if metadata:
            self.on_double_click_callback(item)
            # Deseleziona immediatamente per mantenere lo stile originale
            self.tree.selection_remove(item)

    def _toggle_favorite(self, item):
        """Toggle preferito per un giocatore"""
        if not self.favorites_manager:
            return

        metadata = self.tree_item_map.get(item)
        if not metadata:
            return

        player_id = metadata['player_id']
        is_now_favorite = self.favorites_manager.toggle_favorite(player_id)

        # Aggiorna la stella nella tabella
        values = list(self.tree.item(item, 'values'))
        values[0] = "⭐" if is_now_favorite else "☆"
        self.tree.item(item, values=values)

        # Chiama il callback se presente
        if self.on_favorite_toggle_callback:
            self.on_favorite_toggle_callback()

    def get_selected_item(self):
        """
        Restituisce l'item selezionato

        Returns:
            str: ID dell'item selezionato o None
        """
        selection = self.tree.selection()
        return selection[0] if selection else None

    def get_item_metadata(self, item_id):
        """
        Restituisce i metadata di un item

        Args:
            item_id: ID dell'item

        Returns:
            dict: Metadata dell'item o None
        """
        return self.tree_item_map.get(item_id)

    def get_item_values(self, item_id):
        """
        Restituisce i valori di un item

        Args:
            item_id: ID dell'item

        Returns:
            tuple: Valori dell'item
        """
        return self.tree.item(item_id, 'values')

    def clear(self):
        """Pulisce la tabella"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree_item_map = {}

    def destroy(self):
        """Rimuove la tabella"""
        if self.data_card:
            self.data_card.destroy()
            self.data_card = None

    def _create_season_update_button(self, header):
        """Crea pulsante aggiornamento fine stagione con controllo temporale"""
        from datetime import datetime

        # Controlla se siamo nel periodo consentito (15 luglio - 18 agosto)
        now = datetime.now()
        current_year = now.year

        # Definisci finestra temporale
        start_date = datetime(current_year, 7, 15)  # 15 luglio
        end_date = datetime(current_year, 8, 18)    # 18 agosto

        is_enabled = start_date <= now <= end_date

        # Testo pulsante
        button_text = "⚙️ Aggiornamento Fine Stagione\n(Prima della 1ª giornata)"

        # Colore in base allo stato
        if is_enabled:
            fg_color = "#DC143C"  # Rosso crimson
            hover_color = "#B22222"  # Rosso scuro
        else:
            fg_color = COLORS['bg_tertiary']  # Grigio disabilitato
            hover_color = COLORS['bg_tertiary']

        button = ctk.CTkButton(
            header,
            text=button_text,
            command=self._open_season_update_folder if is_enabled else self._show_disabled_warning,
            height=40,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=fg_color,
            hover_color=hover_color,
            corner_radius=8,
            text_color="white" if is_enabled else COLORS['text_secondary']
        )
        button.pack(side="right")

    def _show_disabled_warning(self):
        """Mostra messaggio quando pulsante è disabilitato"""
        from tkinter import messagebox
        from datetime import datetime

        now = datetime.now()
        messagebox.showinfo(
            "Funzione Non Disponibile",
            "⚠️ AGGIORNAMENTO FINE STAGIONE NON DISPONIBILE\n\n"
            "Questa funzione è disponibile solo dal 15 luglio al 18 agosto.\n\n"
            "Eseguire gli aggiornamenti durante la stagione potrebbe\n"
            "sovrascrivere o corrompere i dati attuali.\n\n"
            f"Data attuale: {now.strftime('%d/%m/%Y')}\n"
            f"Prossima finestra: 15 luglio - 18 agosto {now.year if now.month < 7 else now.year + 1}"
        )

    def _open_season_update_folder(self):
        """Apre cartella aggiornamento fine stagione con warning"""
        from tkinter import messagebox
        import subprocess
        import os
        from pathlib import Path

        # Mostra warning prima di aprire
        result = messagebox.askokcancel(
            "⚠️ ATTENZIONE - Aggiornamento Fine Stagione",
            "⚠️ QUESTA PROCEDURA È SOLO PER IL CAMBIO DI STAGIONE\n\n"
            "Eseguire questi script durante il campionato potrebbe:\n"
            "• Sovrascrivere dati della stagione corrente\n"
            "• Resettare classifiche e statistiche\n"
            "• Corrompere i calcoli dell'applicazione\n\n"
            "📅 USA SOLO:\n"
            "• Dopo la fine della stagione (38 giornate)\n"
            "• Prima dell'inizio della prima giornata\n"
            "• Nel periodo: 15 luglio - 18 agosto\n\n"
            "📚 Leggi attentamente la guida nella cartella prima di procedere.\n\n"
            "Vuoi continuare e aprire la cartella?",
            icon='warning'
        )

        if not result:
            return

        # Percorso cartella aggiornamento
        update_folder = Path("Aggiornamento_Fine_Stagione")

        if not update_folder.exists():
            messagebox.showerror(
                "Errore",
                "Cartella 'Aggiornamento_Fine_Stagione' non trovata!\n\n"
                "Verifica che la cartella sia presente nella directory principale."
            )
            return

        # Apri cartella nel file explorer
        try:
            abs_path = update_folder.resolve()
            if os.name == 'nt':  # Windows
                os.startfile(abs_path)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', abs_path])

            # Mostra messaggio informativo
            messagebox.showinfo(
                "Cartella Aperta",
                "📁 Cartella aggiornamento aperta!\n\n"
                "📚 Leggi il file 'GUIDA_AGGIORNAMENTO.md' per istruzioni complete.\n\n"
                "🚀 Inizio rapido:\n"
                "1. Apri README.txt\n"
                "2. Segui i passaggi nell'ordine indicato\n"
                "3. Leggi la guida completa per dettagli"
            )

        except Exception as e:
            messagebox.showerror(
                "Errore Apertura Cartella",
                f"Impossibile aprire la cartella:\n{e}\n\n"
                f"Apri manualmente: {update_folder.resolve()}"
            )

    def _download_latest_quotazioni(self):
        """Scarica e converte ultimo listone quotazioni"""
        from tkinter import filedialog, messagebox
        import sys
        from pathlib import Path

        # Mostra istruzioni prima di procedere
        result = messagebox.askokcancel(
            "Scarica Quotazioni",
            "📥 PROCEDURA DOWNLOAD QUOTAZIONI\n\n"
            "1. Vai su: https://www.fantacalcio.it/quotazioni-fantacalcio\n"
            "2. Scarica il file Excel delle quotazioni\n"
            "3. Premi 'OK' per selezionare il file scaricato\n\n"
            "⚠️ Nota: Assicurati di scaricare l'ultima versione disponibile",
            icon='info'
        )

        if not result:
            return  # Utente ha annullato

        # Importa il converter
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        try:
            from scripts.convert_quotazioni import QuotazioniConverter
        except ImportError:
            messagebox.showerror(
                "Errore",
                "Script convert_quotazioni.py non trovato!\n\nVerifica che esista in scripts/"
            )
            return

        # Chiedi file Excel all'utente
        file_path = filedialog.askopenfilename(
            title="Seleziona file Excel quotazioni scaricato",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ],
            initialdir=str(Path.home() / "Downloads")
        )

        if not file_path:
            return  # Utente ha annullato

        # Mostra finestra di attesa
        wait_window = ctk.CTkToplevel(self.parent)
        configure_application_window(wait_window)
        wait_window.title("Conversione in corso...")
        wait_window.geometry("400x150")
        wait_window.configure(fg_color=COLORS['bg_primary'])
        wait_window.transient(self.parent)
        wait_window.grab_set()

        # Centra finestra
        wait_window.update_idletasks()
        x = (wait_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (wait_window.winfo_screenheight() // 2) - (150 // 2)
        wait_window.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            wait_window,
            text="⏳ Conversione in corso...",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(pady=30)

        status_label = ctk.CTkLabel(
            wait_window,
            text="Lettura file Excel...",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        )
        status_label.pack()

        wait_window.update()

        # Esegui conversione in background
        def do_conversion():
            try:
                converter = QuotazioniConverter()
                output_path, message = converter.run_auto(Path(file_path))

                wait_window.after(0, lambda: on_conversion_done(output_path, message))

            except Exception as e:
                wait_window.after(0, lambda: on_conversion_error(str(e)))

        def on_conversion_done(output_path, message):
            wait_window.destroy()

            if output_path:
                # Mostra messaggio con opzione refresh
                result = messagebox.askquestion(
                    "Conversione Completata",
                    f"✅ {message}\n\n"
                    f"File salvato:\n{output_path}\n\n"
                    "📝 PROSSIMI PASSI:\n"
                    "1. Aggiorna src/config.py con il nuovo nome file\n"
                    "2. Ricarica dati (consigliato)\n\n"
                    "Vuoi ricaricare i dati ora?",
                    icon='info'
                )

                if result == 'yes':
                    self._reload_application_data(output_path)
            else:
                messagebox.showerror(
                    "Errore Conversione",
                    f"❌ {message}\n\n"
                    "Verifica che il file Excel contenga le colonne:\n"
                    "Id, R, RM, Nome, Squadra"
                )

        def on_conversion_error(error):
            wait_window.destroy()
            messagebox.showerror(
                "Errore",
                f"Si è verificato un errore durante la conversione:\n\n{error}"
            )

        # Avvia conversione in thread separato per non bloccare UI
        import threading
        thread = threading.Thread(target=do_conversion, daemon=True)
        thread.start()

    def _reload_application_data(self, new_csv_path):
        """Ricarica dati applicazione con nuovo file CSV"""
        from tkinter import messagebox
        from pathlib import Path

        # Mostra finestra di caricamento
        loading_window = ctk.CTkToplevel(self.parent)
        configure_application_window(loading_window)
        loading_window.title("Ricaricamento dati...")
        loading_window.geometry("450x200")
        loading_window.configure(fg_color=COLORS['bg_primary'])
        loading_window.transient(self.parent)
        loading_window.grab_set()

        # Centra finestra
        loading_window.update_idletasks()
        x = (loading_window.winfo_screenwidth() // 2) - (450 // 2)
        y = (loading_window.winfo_screenheight() // 2) - (200 // 2)
        loading_window.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            loading_window,
            text="🔄 Ricaricamento dati in corso...",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['text_primary']
        ).pack(pady=20)

        status_label = ctk.CTkLabel(
            loading_window,
            text="Aggiornamento config.py...",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        )
        status_label.pack()

        progress_label = ctk.CTkLabel(
            loading_window,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        )
        progress_label.pack(pady=10)

        loading_window.update()

        def do_reload():
            try:
                # Step 1: Aggiorna config.py
                status_label.configure(text="📝 Aggiornamento config.py...")
                loading_window.update()

                # Estrai anno stagione dal nome file
                filename = Path(new_csv_path).name
                import re
                match = re.search(r'(\d{4})_(\d{4})', filename)
                if match:
                    new_season_file = filename

                    # Aggiorna config.py
                    from src.config import CURRENT_SEASON_FILE, STATS_FILES
                    import src.config as config_module

                    # Aggiorna in memoria
                    config_module.CURRENT_SEASON_FILE = new_season_file

                    progress_label.configure(text=f"✅ Config aggiornato: {new_season_file}")
                    loading_window.update()

                # Step 2: Ricarica cache
                status_label.configure(text="🔄 Pulizia cache...")
                loading_window.update()

                from src.data.cache import DataCache
                cache = DataCache()
                cache.clear()

                progress_label.configure(text="✅ Cache pulita")
                loading_window.update()

                # Step 3: Ricarica data processor
                status_label.configure(text="📊 Ricalcolo statistiche...")
                loading_window.update()

                from src.data_processor import FantaCalcioDataProcessor
                processor = FantaCalcioDataProcessor()

                weighted_df = processor.calculate_weighted_stats()
                if weighted_df is not None:
                    df = processor.calculate_overall_scores(weighted_df)

                    progress_label.configure(text=f"✅ Processati {len(df)} giocatori")
                    loading_window.update()

                    # Step 4: Aggiorna UI
                    loading_window.after(0, lambda: on_reload_complete(df))
                else:
                    loading_window.after(0, lambda: on_reload_error("Errore calcolo statistiche"))

            except Exception as e:
                loading_window.after(0, lambda: on_reload_error(str(e)))

        def on_reload_complete(new_df):
            loading_window.destroy()

            # Trova l'app principale e aggiorna
            try:
                # Risali alla classe app principale
                parent_widget = self.parent
                while parent_widget:
                    if hasattr(parent_widget, 'df') and hasattr(parent_widget, 'populate_players'):
                        # Trovata l'app principale
                        parent_widget.df = new_df
                        parent_widget.filtered_df = new_df.copy()

                        # Aggiorna price calculator
                        if hasattr(parent_widget, 'price_calculator'):
                            parent_widget.price_calculator.update_players_data(new_df)

                        # Ricarica tabella
                        parent_widget.populate_players()

                        messagebox.showinfo(
                            "Ricaricamento Completato",
                            f"✅ Dati ricaricati con successo!\n\n"
                            f"Giocatori caricati: {len(new_df)}\n\n"
                            "La lista è stata aggiornata automaticamente."
                        )
                        return

                    # Sali al parent
                    if hasattr(parent_widget, 'master'):
                        parent_widget = parent_widget.master
                    else:
                        parent_widget = None

                # Se non trovata app, mostra messaggio manuale
                messagebox.showinfo(
                    "Ricaricamento Completato",
                    "✅ Dati ricaricati!\n\n"
                    "Riavvia l'applicazione per vedere i cambiamenti."
                )

            except Exception as e:
                messagebox.showerror(
                    "Errore Aggiornamento UI",
                    f"Dati ricaricati ma errore aggiornamento UI:\n{e}\n\n"
                    "Riavvia l'applicazione."
                )

        def on_reload_error(error):
            loading_window.destroy()
            messagebox.showerror(
                "Errore Ricaricamento",
                f"Errore durante il ricaricamento:\n\n{error}\n\n"
                "Riavvia manualmente l'applicazione."
            )

        # Avvia reload in thread
        import threading
        thread = threading.Thread(target=do_reload, daemon=True)
        thread.start()
