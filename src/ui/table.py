"""
Gestione tabella giocatori e ordinamento
"""
import tkinter as tk
from tkinter import ttk
import pandas as pd
from src.ui.tooltips import create_tooltip_at


class TableManager:
    """Gestisce la tabella dei giocatori e l'ordinamento"""

    def __init__(self, parent_frame, app):
        self.parent_frame = parent_frame
        self.app = app
        self.tree = None
        self.current_tooltip = None
        self.sort_col = None
        self.sort_reverse = False
        self.setup_tree()

    def setup_tree(self):
        """Configura la tabella dei dati"""
        scrollbar_y = ttk.Scrollbar(self.parent_frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(self.parent_frame, orient=tk.HORIZONTAL)

        self.tree = ttk.Treeview(self.parent_frame,
                                yscrollcommand=scrollbar_y.set,
                                xscrollcommand=scrollbar_x.set,
                                selectmode='browse')

        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=1, column=0, sticky=(tk.W, tk.E))

        columns = ['Overall', 'Prezzo Max %', 'Id', 'Nome', 'Squadra', 'R', 'Tag', 'Note', 'Pv', 'Mv', 'Fm',
                  'Gf', 'Gs', 'Rp', 'Rc', 'R+', 'R-', 'Ass', 'Amm', 'Esp', 'Au']
        self.tree['columns'] = columns
        self.tree['show'] = 'headings'

        column_widths = {
            'Overall': 60, 'Prezzo Max %': 70, 'Id': 60, 'Nome': 150, 'Squadra': 100, 'R': 50,
            'Tag': 120, 'Note': 150,
            'Pv': 40, 'Mv': 50, 'Fm': 50, 'Gf': 40, 'Gs': 40,
            'Rp': 40, 'Rc': 40, 'R+': 40, 'R-': 40, 'Ass': 40,
            'Amm': 40, 'Esp': 40, 'Au': 40
        }

        column_tooltips = {
            'Overall': 'Valutazione Complessiva',
            'Prezzo Max %': '% Budget massimo consigliato (basato su Overall, statistiche e trend)',
            'Id': 'Identificativo Giocatore',
            'Nome': 'Nome Giocatore',
            'Squadra': 'Squadra di Appartenenza',
            'R': 'Ruolo',
            'Tag': 'Tag/Etichette Personali (click per modificare)',
            'Note': 'Note Personali (anteprima)',
            'Pv': 'Partite Giocate (ponderato)',
            'Mv': 'Media Voto (ponderato)',
            'Fm': 'Fantamedia (ponderato)',
            'Gf': 'Goal Fatti (ponderato)',
            'Gs': 'Goal Subiti (ponderato)',
            'Rp': 'Rigori Parati (ponderato)',
            'Rc': 'Rigori Calciati (ponderato)',
            'R+': 'Rigori Segnati (ponderato)',
            'R-': 'Rigori Sbagliati (ponderato)',
            'Ass': 'Assist (ponderato)',
            'Amm': 'Ammonizioni (ponderato)',
            'Esp': 'Espulsioni (ponderato)',
            'Au': 'Autogol (ponderato)'
        }

        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_column(c))
            width = column_widths.get(col, 80)
            self.tree.column(col, width=width, anchor='center')

        self.setup_column_tooltips(column_tooltips)

    def setup_column_tooltips(self, tooltips_dict):
        """Configura i tooltip per le intestazioni delle colonne"""
        self.tree.bind('<Motion>', lambda e: self.show_column_tooltip(e, tooltips_dict))

    def show_column_tooltip(self, event, tooltips_dict):
        """Mostra tooltip quando il mouse passa sopra un'intestazione"""
        region = self.tree.identify_region(event.x, event.y)

        if region != "heading":
            if self.current_tooltip:
                self.current_tooltip.hide_tooltip()
                self.current_tooltip = None
            return

        column = self.tree.identify_column(event.x)
        if not column:
            return

        col_index = int(column.replace('#', '')) - 1
        columns = self.tree['columns']

        if col_index < len(columns):
            col_name = columns[col_index]
            tooltip_text = tooltips_dict.get(col_name, '')

            if tooltip_text:
                if self.current_tooltip:
                    self.current_tooltip.hide_tooltip()

                x = self.tree.winfo_rootx() + event.x
                y = self.tree.winfo_rooty() + event.y

                self.current_tooltip = create_tooltip_at(self.tree, x, y, tooltip_text)

    def populate_tree(self):
        """Popola la tabella con i dati filtrati"""
        self.tree.delete(*self.tree.get_children())

        if self.app.filtered_df is None or self.app.filtered_df.empty:
            return

        total_rows = len(self.app.filtered_df)
        show_progress = total_rows > 100

        if show_progress:
            self.app.status_label.config(text="Caricamento righe...")
            self.app.root.update_idletasks()

        budget = self.app.budget_var.get()

        # Calcola tutti i prezzi in batch
        all_player_ids = self.app.filtered_df['Id'].tolist()
        price_data = self.app.price_calculator.calculate_batch_prices(all_player_ids, budget)

        batch_size = 50
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            batch_df = self.app.filtered_df.iloc[batch_start:batch_end]

            items = []
            for _, row in batch_df.iterrows():
                player_id = row['Id']
                tags_str = self.app.notes_manager.get_tags_string(player_id)
                note_preview = self.app.notes_manager.get_note_preview(player_id, max_length=30)

                price_calc = price_data.get(player_id, {'percentage': 0.0})
                price_percentage = f"{price_calc['percentage']}%"

                values = (
                    row['Overall'],
                    price_percentage,
                    player_id,
                    row['Nome'],
                    row['Squadra'],
                    row['R'],
                    tags_str,
                    note_preview,
                    row['Pv_weighted'],
                    row['Mv_weighted'],
                    row['Fm_weighted'],
                    row['Gf_weighted'],
                    row['Gs_weighted'],
                    row['Rp_weighted'],
                    row['Rc_weighted'],
                    row['R+_weighted'],
                    row['R-_weighted'],
                    row['Ass_weighted'],
                    row['Amm_weighted'],
                    row['Esp_weighted'],
                    row['Au_weighted']
                )
                items.append(values)

            for values in items:
                self.tree.insert('', tk.END, values=values)

            if show_progress:
                progress = int((batch_end / total_rows) * 100)
                self.app.status_label.config(text=f"Caricamento righe... {progress}%")
                self.app.root.update_idletasks()

        self.app.status_label.config(text=f"Caricati {total_rows} giocatori")

    def sort_column(self, col):
        """Ordina la tabella per la colonna specificata"""
        if self.app.filtered_df is None or self.app.filtered_df.empty:
            return

        col_map = {
            'Overall': 'Overall', 'Prezzo Max %': 'Prezzo Max %', 'Id': 'Id', 'Nome': 'Nome', 'Squadra': 'Squadra', 'R': 'R',
            'Tag': 'Tag', 'Note': 'Note',
            'Pv': 'Pv_weighted', 'Mv': 'Mv_weighted', 'Fm': 'Fm_weighted',
            'Gf': 'Gf_weighted', 'Gs': 'Gs_weighted', 'Rp': 'Rp_weighted',
            'Rc': 'Rc_weighted', 'R+': 'R+_weighted', 'R-': 'R-_weighted',
            'Ass': 'Ass_weighted', 'Amm': 'Amm_weighted', 'Esp': 'Esp_weighted',
            'Au': 'Au_weighted'
        }

        actual_col = col_map.get(col, col)

        if col in ['Tag', 'Note']:
            return

        if self.sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col
            self.sort_reverse = False

        temp_df = self.app.filtered_df.copy()

        if col == 'Prezzo Max %':
            budget = self.app.budget_var.get()
            price_percentages = []

            for _, row in temp_df.iterrows():
                player_id = row['Id']
                price_data = self.app.price_calculator.calculate_price_percentage(player_id, budget)
                price_percentages.append(price_data['percentage'])

            temp_df['_temp_price'] = price_percentages
            temp_df = temp_df.sort_values(by='_temp_price', ascending=self.sort_reverse, na_position='last')
            temp_df = temp_df.drop('_temp_price', axis=1)
        elif actual_col in ['Overall', 'Pv_weighted', 'Mv_weighted', 'Fm_weighted', 'Gf_weighted',
                          'Gs_weighted', 'Rp_weighted', 'Rc_weighted', 'R+_weighted',
                          'R-_weighted', 'Ass_weighted', 'Amm_weighted', 'Esp_weighted',
                          'Au_weighted']:
            temp_df['sort_key'] = pd.to_numeric(temp_df[actual_col], errors='coerce')
            temp_df = temp_df.sort_values(by='sort_key', ascending=self.sort_reverse, na_position='last')
            temp_df = temp_df.drop('sort_key', axis=1)
        else:
            temp_df = temp_df.sort_values(by=actual_col, ascending=self.sort_reverse)

        self.app.filtered_df = temp_df
        self.populate_tree()
