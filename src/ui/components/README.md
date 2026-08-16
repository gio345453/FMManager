# Componenti UI Modulari

Questa cartella contiene i componenti UI modulari dell'applicazione FantaCalcio Manager.

## Struttura File

```
src/ui/components/
├── __init__.py              # Esporta tutti i componenti
├── constants.py             # Costanti UI (colori, tema)
├── header_component.py      # Componente header/titolo
├── filters_panel.py         # Pannello filtri (budget, ruolo, squadra, ricerca)
├── player_table.py          # Tabella giocatori con Treeview
├── tag_menu.py              # Menu popup per gestione tag rapida
└── footer_actions.py        # Pulsanti azioni e status bar
```

## Componenti

### 1. **constants.py** (~50 righe)
Definisce le costanti condivise:
- `COLORS`: Palette colori moderna
- `THEME_CONFIG`: Configurazioni tema (dimensioni, bordi, ecc.)

### 2. **HeaderComponent** (~50 righe)
Header con titolo dell'applicazione.
```python
header = HeaderComponent(parent)
header.create()
header.update_title("Nuovo Titolo")
```

### 3. **FiltersPanel** (~200 righe)
Pannello filtri completo con:
- Budget input
- Filtro ruolo (P, D, C, A)
- Filtro squadra
- Barra ricerca
```python
filters = FiltersPanel(parent, df, on_filter_change=callback)
filters.create(budget_var)
filter_values = filters.get_filter_values()  # {'role': 'P', 'team': 'Milan', 'search': ''}
```

### 4. **PlayerTable** (~300 righe)
Tabella giocatori con Treeview:
- Configurazione colonne
- Popolamento dati con trend
- Gestione eventi (click, doppio click)
- Righe alternate colorate
```python
table = PlayerTable(parent, filtered_df, price_calculator, notes_manager, 
                   on_double_click=callback, on_tag_click=callback)
table.create()
table.populate(filtered_df, budget)
```

### 5. **TagMenu** (~180 righe)
Menu popup per gestione tag:
- Tag predefiniti (obiettivo, da evitare, esca, riserva, titolare, occasione)
- Indicazione tag attivi
- Bottone modifica completa
```python
tag_menu = TagMenu(root, notes_manager, on_tag_toggle=callback, on_open_details=callback)
tag_menu.show(player_id, player_name, item, event)
```

### 6. **FooterActions** (~100 righe)
Footer con pulsanti azioni e status bar:
- Pulsante "Confronta Giocatori"
- Pulsante "Dashboard Squadre"
- Status bar con messaggi
```python
footer = FooterActions(parent, on_comparison=callback, on_dashboard=callback)
footer.create()
footer.create_status_bar()
footer.set_success("Dati caricati!")
```

## Utilizzo nell'App Principale

```python
from src.ui.components import (
    COLORS,
    HeaderComponent,
    FiltersPanel,
    PlayerTable,
    TagMenu,
    FooterActions
)

class UltraModernFantaCalcioApp:
    def setup_ui(self):
        # Header
        self.header = HeaderComponent(main_container)
        self.header.create()
        
        # Filters
        self.filters = FiltersPanel(main_container, self.df, on_filter_change=self.apply_filters)
        self.filters.create(self.budget_var)
        
        # Footer Actions
        self.footer = FooterActions(main_container, on_comparison=self.open_comparison, 
                                   on_dashboard=self.open_team_dashboard)
        self.footer.create()
        
        # Player Table
        self.player_table = PlayerTable(main_container, self.filtered_df, 
                                       self.price_calculator, self.notes_manager,
                                       on_double_click=self._open_details, 
                                       on_tag_click=self.show_tag_menu)
        self.player_table.create()
        
        # Tag Menu
        self.tag_menu = TagMenu(self.root, self.notes_manager, 
                               on_tag_toggle=self.populate_players, 
                               on_open_details=self._open_details)
        
        # Status bar
        self.footer.create_status_bar()
```

## Vantaggi della Struttura Modulare

✅ **Manutenibilità**: Ogni componente ha una responsabilità chiara  
✅ **Testing**: Facile testare componenti in isolamento  
✅ **Riuso**: Componenti riutilizzabili in altre parti dell'app  
✅ **Chiarezza**: Codice più leggibile e organizzato  
✅ **Scalabilità**: Facile aggiungere nuovi componenti  

## File Originale

Il file originale `app_modern.py` (~900 righe) è stato salvato come backup in:
- `src/ui/app_modern_backup.py`

La nuova versione modulare ha solo ~180 righe!
