"""
Componenti UI modulari per l'applicazione FantaCalcio
"""

from .constants import COLORS, THEME_CONFIG
from .header_component import HeaderComponent
from .filters_panel import FiltersPanel
from .player_table import PlayerTable
from .tag_menu import TagMenu
from .footer_actions import FooterActions

__all__ = [
    'COLORS',
    'THEME_CONFIG',
    'HeaderComponent',
    'FiltersPanel',
    'PlayerTable',
    'TagMenu',
    'FooterActions'
]
