"""
Gestione azioni sui giocatori (doppio click, menu contestuale, tag)
"""
import tkinter as tk
from tkinter import messagebox
from src.ui.player_details import PlayerDetailsWindow


class PlayerActionsManager:
    """Gestisce le azioni sui giocatori (click, menu, tag)"""

    def __init__(self, tree, app):
        self.tree = tree
        self.app = app
        self.bind_events()

    def bind_events(self):
        """Bind eventi sulla tabella"""
        self.tree.bind('<Double-Button-1>', self.on_player_double_click)
        self.tree.bind('<Button-3>', self.on_right_click)
        self.tree.bind('<Button-1>', self.on_single_click)

    def on_player_double_click(self, event):
        """Gestisce il doppio click su un giocatore per aprire i dettagli"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.tree.item(item, 'values')

        if not values:
            return

        # Estrai ID, Nome e Ruolo dal tree
        player_id = int(values[2])  # Colonna 'Id' (indice 2)
        player_name = values[3]      # Colonna 'Nome' (indice 3)
        player_role = values[5]      # Colonna 'R' (indice 5)

        # Apri finestra dettagli
        PlayerDetailsWindow(self.app.root, player_id, player_name, player_role, self.app.budget_var.get())

    def on_right_click(self, event):
        """Gestisce il click destro per aprire menu contestuale"""
        item = self.tree.identify_row(event.y)
        if not item:
            return

        self.tree.selection_set(item)

        menu = tk.Menu(self.app.root, tearoff=0)
        menu.add_command(label="✏️ Modifica Note/Tag", command=self.edit_notes_from_menu)
        menu.add_command(label="📋 Visualizza Dettagli", command=lambda: self.on_player_double_click(None))
        menu.add_separator()
        menu.add_command(label="🗑️ Cancella Note/Tag", command=self.delete_notes_from_menu)

        menu.post(event.x_root, event.y_root)

    def edit_notes_from_menu(self):
        """Apre la finestra di modifica note dalla selezione"""
        self.on_player_double_click(None)

    def delete_notes_from_menu(self):
        """Cancella le note e i tag del giocatore selezionato"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.tree.item(item, 'values')

        if not values:
            return

        player_id = int(values[2])  # Colonna 'Id' (indice 2)
        player_name = values[3]      # Colonna 'Nome' (indice 3)

        if messagebox.askyesno("Conferma", f"Eliminare note e tag per {player_name}?"):
            self.app.notes_manager.delete_player_data(player_id)
            self.app.table_manager.populate_tree()
            messagebox.showinfo("Successo", "Note e tag eliminati")

    def on_single_click(self, event):
        """Gestisce il click singolo per aprire menu tag se si clicca sulla colonna Tag"""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)

        if not item:
            return

        col_index = int(column.replace('#', '')) - 1
        columns = self.tree['columns']

        # Verifica se è la colonna Tag (indice 6)
        if col_index < len(columns) and columns[col_index] == 'Tag':
            self.tree.selection_set(item)
            self.show_tag_quick_menu(event)

    def show_tag_quick_menu(self, event):
        """Mostra menu rapido per aggiungere tag"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.tree.item(item, 'values')

        if not values:
            return

        player_id = int(values[2])  # Colonna 'Id' (indice 2)
        player_name = values[3]      # Colonna 'Nome' (indice 3)

        menu = tk.Menu(self.app.root, tearoff=0)
        menu.add_command(label=f"Tag rapidi per {player_name}", state="disabled")
        menu.add_separator()

        common_tags = ["obiettivo", "da evitare", "esca", "riserva", "titolare", "occasione"]
        current_tags = self.app.notes_manager.get_tags(player_id)

        for tag in common_tags:
            tag_label = f"✓ {tag}" if tag in current_tags else f"  {tag}"
            menu.add_command(
                label=tag_label,
                command=lambda t=tag, pid=player_id: self.toggle_tag(pid, t)
            )

        menu.add_separator()
        menu.add_command(label="✏️ Modifica completa...", command=self.edit_notes_from_menu)

        menu.post(event.x_root, event.y_root)

    def toggle_tag(self, player_id, tag):
        """Aggiunge o rimuove un tag"""
        current_tags = self.app.notes_manager.get_tags(player_id)

        if tag in current_tags:
            self.app.notes_manager.remove_tag(player_id, tag)
        else:
            self.app.notes_manager.add_tag(player_id, tag)

        # Aggiorna la lista dei tag disponibili nel filtro
        all_tags = ["Tutti"] + self.app.notes_manager.get_all_tags()
        self.app.tag_combo['values'] = all_tags

        self.app.table_manager.populate_tree()
