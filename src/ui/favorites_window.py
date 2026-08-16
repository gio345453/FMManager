"""
Finestra Lista Preferiti - Mostra tutti i giocatori preferiti
con funzionalità di esportazione (CSV, Excel, PDF)
"""
import os
import webbrowser
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox

from src.ui.components.constants import COLORS
from src.ui.window_chrome import configure_application_window
from src.ui.components.player_table import PlayerTable
from src.ui.components.filters_panel import FiltersPanel
from src.ui.player_details import PlayerDetailsWindow


class FavoritesWindow:
    """Finestra popup con la lista dei giocatori preferiti ed esportazione"""

    def __init__(self, parent, full_df, favorites_manager, price_calculator, notes_manager, budget=500):
        """
        Inizializza finestra preferiti

        Args:
            parent: Finestra genitore
            full_df: DataFrame completo con tutti i giocatori
            favorites_manager: Istanza di FavoritesManager
            price_calculator: Istanza di PriceCalculator
            notes_manager: Istanza di PlayerNotesManager
            budget: Budget per calcolo prezzi
        """
        self.full_df = full_df
        self.favorites_manager = favorites_manager
        self.price_calculator = price_calculator
        self.notes_manager = notes_manager
        self.budget = budget

        # Filtra solo i preferiti iniziali
        favorite_ids = self.favorites_manager.get_all_favorites()
        self.favorites_df = full_df[full_df['Id'].isin(favorite_ids)].copy() if favorite_ids else None
        self.filtered_df = self.favorites_df.copy() if self.favorites_df is not None else None

        # Finestra principale
        self.window = ctk.CTkToplevel(parent)
        configure_application_window(self.window)
        self.window.title(f"⭐ Preferiti ({len(favorite_ids)})")
        self.window.configure(fg_color=COLORS['bg_primary'])

        # Nascondi durante setup
        self.window.withdraw()

        # Transient
        self.window.transient(parent)

        self._setup_ui()

        # Mostra massimizzata
        self.window.after(10, self._show_maximized)

    def _show_maximized(self):
        """Massimizza e mostra la finestra"""
        try:
            self.window.state('zoomed')
        except Exception:
            try:
                self.window.attributes('-zoomed', True)
            except Exception:
                self.window.geometry("1200x700")

        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()

    def _setup_ui(self):
        """Setup interfaccia"""
        # Main container
        main_container = ctk.CTkFrame(self.window, fg_color=COLORS['bg_primary'])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # 1. Header (Titolo + Badge + Tasti Esportazione + Tasto Chiudi)
        header = ctk.CTkFrame(main_container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))

        # Titolo
        ctk.CTkLabel(
            header,
            text="⭐ GIOCATORI PREFERITI",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS['accent_yellow']
        ).pack(side="left")

        # Badge count
        count = self.favorites_manager.get_favorites_count()
        badge = ctk.CTkFrame(header, fg_color=COLORS['bg_secondary'], corner_radius=8)
        badge.pack(side="left", padx=15)

        self.count_label = ctk.CTkLabel(
            badge,
            text=f"{count} giocatori",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS['text_primary']
        )
        self.count_label.pack(padx=10, pady=5)

        # --- SEZIONE AZIONI DESSTRA (Chiudi + Esporta) ---
        actions_frame = ctk.CTkFrame(header, fg_color="transparent")
        actions_frame.pack(side="right")

        # Bottone chiudi
        ctk.CTkButton(
            actions_frame,
            text="✕ Chiudi",
            command=self.window.destroy,
            fg_color=COLORS['error'],
            hover_color="#D62A56",
            corner_radius=10,
            width=90,
            height=32,
            font=ctk.CTkFont(weight="bold")
        ).pack(side="right", padx=(10, 0))

        # Menu o Bottoni Esportazione
        export_bg = COLORS.get('bg_secondary', '#2B2D42')
        
        btn_pdf = ctk.CTkButton(
            actions_frame,
            text="📄 PDF",
            command=self._export_pdf,
            fg_color=export_bg,
            hover_color="#3B3E5B",
            corner_radius=8,
            width=75,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        btn_pdf.pack(side="right", padx=3)

        btn_excel = ctk.CTkButton(
            actions_frame,
            text="📊 Excel",
            command=self._export_excel,
            fg_color=export_bg,
            hover_color="#1D6F42",
            corner_radius=8,
            width=75,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        btn_excel.pack(side="right", padx=3)

        btn_csv = ctk.CTkButton(
            actions_frame,
            text="📝 CSV",
            command=self._export_csv,
            fg_color=export_bg,
            hover_color="#3B3E5B",
            corner_radius=8,
            width=75,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        btn_csv.pack(side="right", padx=3)

        ctk.CTkLabel(
            actions_frame,
            text="Esporta:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS.get('text_secondary', '#8D99AE')
        ).pack(side="right", padx=(0, 5))

        # 2. Pannello Filtri (Inserito tra Header e Lista)
        if self.favorites_df is not None and not self.favorites_df.empty:
            self.filters = FiltersPanel(
                main_container,
                self.favorites_df,
                on_filter_change=self._apply_filters,
                favorites_manager=self.favorites_manager,
                notes_manager=self.notes_manager
            )
            self.filters.create()

        # 3. Tabella giocatori
        if self.favorites_df is not None and not self.favorites_df.empty:
            self.player_table = PlayerTable(
                main_container,
                self.filtered_df,
                self.price_calculator,
                self.notes_manager,
                on_double_click=self._open_player_details,
                on_tag_click=self._dummy_tag_click,
                favorites_manager=self.favorites_manager
            )
            self.player_table.create()
            self.player_table.populate(self.filtered_df, self.budget)
        else:
            # Nessun preferito
            empty_frame = ctk.CTkFrame(
                main_container,
                fg_color=COLORS['bg_secondary'],
                corner_radius=15
            )
            empty_frame.pack(fill="both", expand=True)

            ctk.CTkLabel(
                empty_frame,
                text="📭 Nessun giocatore nei preferiti",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=COLORS['text_secondary']
            ).pack(expand=True, pady=100)

            ctk.CTkLabel(
                empty_frame,
                text="Clicca sulla stella ⭐ nella lista giocatori per aggiungere preferiti",
                font=ctk.CTkFont(size=13),
                text_color=COLORS['text_secondary']
            ).pack(expand=True)

    def _apply_filters(self):
        """Applica i filtri selezionati alla lista dei preferiti"""
        if self.favorites_df is None or not hasattr(self, 'filters'):
            return

        filter_values = self.filters.get_filter_values()
        role = filter_values['role']
        team = filter_values['team']
        search = filter_values['search']
        tag = filter_values['tag']
        fm_min = filter_values['fm_min']
        fm_max = filter_values['fm_max']

        filtered = self.favorites_df.copy()

        if role != "Tutti":
            filtered = filtered[filtered['R'].str.startswith(role)]

        if team != "Tutte":
            filtered = filtered[filtered['Squadra'] == team]

        if search:
            filtered = filtered[filtered['Nome'].str.contains(search, case=False, na=False)]

        if tag != "Tutti":
            player_ids_with_tag = self.notes_manager.search_by_tag(tag)
            filtered = filtered[filtered['Id'].isin(player_ids_with_tag)]

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

        if hasattr(self, 'player_table'):
            self.player_table.populate(self.filtered_df, self.budget)

    def _open_player_details(self, item):
        """Apre dettagli giocatore"""
        if not hasattr(self, 'player_table'):
            return

        metadata = self.player_table.get_item_metadata(item)
        if not metadata:
            return

        player_id = metadata['player_id']
        values = self.player_table.get_item_values(item)
        player_name = values[4]
        player_role = metadata['role_str']

        PlayerDetailsWindow(
            self.window,
            player_id,
            player_name,
            player_role,
            self.budget,
            on_close_callback=self._refresh_table
        )

    def _refresh_table(self):
        """Ricarica la tabella dopo modifiche"""
        favorite_ids = self.favorites_manager.get_all_favorites()
        self.favorites_df = self.full_df[self.full_df['Id'].isin(favorite_ids)].copy() if favorite_ids else None

        # Re-applica i filtri sui dati aggiornati
        self._apply_filters()

        # Aggiorna count badge e titolo
        count = self.favorites_manager.get_favorites_count()
        self.window.title(f"⭐ Preferiti ({count})")
        if hasattr(self, 'count_label'):
            self.count_label.configure(text=f"{count} giocatori")

    def _dummy_tag_click(self, item, event):
        """Placeholder per tag click"""
        pass

    # ==========================================
    # METODI DI ESPORTAZIONE (CSV, EXCEL, PDF)
    # ==========================================
    def _get_export_dataframe(self):
        """Estrae i dati esattamente come visualizzati nell'interfaccia grafica (PlayerTable)"""
        if not hasattr(self, 'player_table') or not hasattr(self.player_table, 'tree'):
            messagebox.showwarning("Attenzione", "Nessuna tabella trovata da esportare.", parent=self.window)
            return None

        tree = self.player_table.tree
        children = tree.get_children()

        if not children:
            messagebox.showwarning("Attenzione", "Nessun giocatore presente in tabella da esportare.", parent=self.window)
            return None

        # 1. Recupera le intestazioni delle colonne visibili
        columns = [tree.heading(col)["text"] for col in tree["columns"]]

        # 2. Raccogli le righe esattamente con i valori mostrati a schermo
        data = []
        for item_id in children:
            values = tree.item(item_id)["values"]
            data.append(values)

        # 3. Crea il DataFrame pulito basato sull'interfaccia
        df_export = pd.DataFrame(data, columns=columns)

        # Rimuove la colonna della stella "⭐" se presente come prima colonna
        if df_export.columns[0] in ['⭐', '', 'Fav']:
            df_export = df_export.iloc[:, 1:]

        return df_export

    def _export_csv(self):
        """Esporta la lista corrente in formato CSV"""
        df = self._get_export_dataframe()
        if df is None:
            return

        file_path = filedialog.asksaveasfilename(
            parent=self.window,
            title="Salva come CSV",
            defaultextension=".csv",
            filetypes=[("File CSV", "*.csv"), ("Tutti i file", "*.*")],
            initialfile="giocatori_preferiti.csv"
        )

        if file_path:
            try:
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                messagebox.showinfo("Successo", f"File CSV salvato con successo:\n{file_path}", parent=self.window)
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile salvare il file CSV:\n{e}", parent=self.window)

    def _export_excel(self):
        """Esporta la lista corrente in formato Excel (.xlsx)"""
        df = self._get_export_dataframe()
        if df is None:
            return

        file_path = filedialog.asksaveasfilename(
            parent=self.window,
            title="Salva come Excel",
            defaultextension=".xlsx",
            filetypes=[("File Excel", "*.xlsx"), ("Tutti i file", "*.*")],
            initialfile="giocatori_preferiti.xlsx"
        )

        if file_path:
            try:
                df.to_excel(file_path, index=False, engine='openpyxl')
                messagebox.showinfo("Successo", f"File Excel salvato con successo:\n{file_path}", parent=self.window)
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile salvare il file Excel:\n{e}\n(Assicurati che 'openpyxl' sia installato)", parent=self.window)

    def _export_pdf(self):
        """Esporta la lista corrente in formato PDF"""
        df = self._get_export_dataframe()
        if df is None:
            return

        file_path = filedialog.asksaveasfilename(
            parent=self.window,
            title="Salva come PDF",
            defaultextension=".pdf",
            filetypes=[("File PDF", "*.pdf"), ("Tutti i file", "*.*")],
            initialfile="giocatori_preferiti.pdf"
        )

        if not file_path:
            return

        # Tentativo 1: Usa ReportLab se presente
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors

            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
            elements = []

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#1E1E2E'), spaceAfter=15)
            elements.append(Paragraph("⭐ Lista Giocatori Preferiti", title_style))

            data = [df.columns.tolist()] + df.values.tolist()
            t = Table(data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2B2D42')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            elements.append(t)
            doc.build(elements)

            messagebox.showinfo("Successo", f"File PDF salvato con successo:\n{file_path}", parent=self.window)
            return
        except ImportError:
            pass # Se reportlab non è installato, usa il fallback HTML

        # Fallback HTML -> PDF / Stampa Browser
        try:
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #1E1E2E; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
                    th {{ background-color: #2B2D42; color: white; }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h1>⭐ Lista Giocatori Preferiti</h1>
                {df.to_html(index=False, classes='table')}
            </body>
            </html>
            """
            html_file = file_path.replace('.pdf', '.html')
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            webbrowser.open('file://' + os.path.realpath(html_file))
            messagebox.showinfo("Info PDF", "La lista è stata aperta nel browser. Puoi salvarla direttamente in PDF premendo CTRL+P -> Salva come PDF.", parent=self.window)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile generare l'esportazione PDF:\n{e}", parent=self.window)