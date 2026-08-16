"""
Modulo centralizzato per lo stile dei grafici Matplotlib
Versione modernizzata per CustomTkinter (stile Dashboard Dark UI)
"""
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patheffects as path_effects
from src.utils.data_utils import extract_base_role

# Palette colori UI moderna e pulita
CHART_COLORS = {
    'bg_primary': '#0F0F1E',
    'bg_secondary': '#1A1B26',  # Sfondo della figura
    'bg_tertiary': '#242535',   # Sfondo delle schede/subplot
    'accent_blue': '#4F46E5',
    'accent_purple': '#8B5CF6',
    'accent_pink': '#EC4899',
    'accent_green': '#10B981',
    'accent_yellow': '#F59E0B',
    'text_primary': '#F3F4F6',
    'text_secondary': '#9CA3AF',
    'grid': '#2E3048',
    'spine': '#2E3048'
}

BAR_COLORS = ['#6366F1', '#A855F7', '#EC4899']

LINE_COLORS = {
    'fantamedia': '#38BDF8',
    'media_voto': '#F43F5E',
    'gol': '#10B981',
    'assist': '#F59E0B',
    'primary': '#6366F1',
    'secondary': '#A855F7'
}


def configure_subplot(ax, title=None, ylabel=None, show_grid=True):
    """Configura il subplot rimuovendo i bordi visibili e ammorbidendo la griglia."""
    ax.set_facecolor(CHART_COLORS['bg_tertiary'])

    if title:
        ax.set_title(
            title,
            fontsize=11,
            fontweight='bold',
            color=CHART_COLORS['text_primary'],
            pad=12,
            loc='left'  # Allineato a sinistra per un look più moderno
        )

    if ylabel:
        ax.set_ylabel(
            ylabel,
            fontsize=9,
            fontweight='bold',
            color=CHART_COLORS['text_secondary']
        )

    if show_grid:
        # Griglia tratteggiata molto leggera
        ax.grid(True, linestyle='--', alpha=0.25, color=CHART_COLORS['grid'], zorder=0)

    ax.tick_params(
        colors=CHART_COLORS['text_secondary'],
        labelsize=9,
        length=0  # Rimuove i trattini dei tick per un design minimal
    )

    # Rimuove del tutto le spine/bordi inutili
    for spine in ['top', 'right', 'left', 'bottom']:
        ax.spines[spine].set_visible(False)


def create_figure(nrows=1, ncols=1, figsize=(10, 8), suptitle=None):
    """Crea una figura con spaziatura adeguata e titolo moderno."""
    fig = Figure(figsize=figsize, dpi=100, facecolor=CHART_COLORS['bg_secondary'])

    if nrows == 1 and ncols == 1:
        axes = fig.add_subplot(1, 1, 1)
    else:
        axes = fig.subplots(nrows, ncols)

    if suptitle:
        fig.suptitle(
            suptitle,
            fontsize=15,
            fontweight='bold',
            color=CHART_COLORS['text_primary'],
            x=0.05,
            ha='left'
        )

    return fig, axes


def add_value_labels_on_bars(ax, bars, is_float=False):
    """Aggiunge etichette di testo pulite sopra le barre."""
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            label = f'{height:.2f}' if is_float else str(int(height))
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                label,
                ha='center',
                va='bottom',
                fontweight='bold',
                color=CHART_COLORS['text_primary'],
                fontsize=9,
                zorder=4
            )


def add_value_labels_on_line(ax, x_data, y_data, offset=0.1):
    """Aggiunge etichette sopra i punti di una linea."""
    for i, v in enumerate(y_data):
        ax.text(
            i,
            v + offset,
            f'{v:.2f}',
            ha='center',
            va='bottom',
            fontweight='bold',
            color=CHART_COLORS['text_primary'],
            fontsize=8,
            zorder=4
        )


def create_line_chart(ax, x_data, y_data, label, color=None, marker='o'):
    """Crea una linea spessa con riempimento gradiente/area sfumata sottostante."""
    if color is None:
        color = CHART_COLORS['accent_blue']

    # Disegna la linea principale
    line, = ax.plot(
        x_data,
        y_data,
        marker=marker,
        linewidth=2.5,
        markersize=6,
        color=color,
        label=label,
        zorder=3
    )

    # Sfumatura/riempimento sotto la linea
    ax.fill_between(
        x_data,
        y_data,
        alpha=0.15,
        color=color,
        zorder=2
    )


def create_bar_chart(ax, x_data, y_data, color=None, alpha=0.9):
    """Crea barre con angoli superiori arrotondati senza bordi marcati."""
    if color is None:
        color = CHART_COLORS['accent_green']

    bars = ax.bar(
        x_data,
        y_data,
        color=color,
        alpha=alpha,
        width=0.45,
        zorder=3
    )

    return bars


def create_comparison_bar_chart(ax, x_labels, y_values_list, colors=None, width=0.45):
    """Crea barre di confronto moderne."""
    if colors is None:
        colors = BAR_COLORS[:len(y_values_list)]

    bars = ax.bar(
        x_labels,
        y_values_list,
        color=colors,
        width=width,
        zorder=3
    )

    return bars


def embed_figure_in_tkinter(figure, parent_frame):
    """Incorpora la figura nel frame CustomTkinter."""
    canvas = FigureCanvasTkAgg(figure, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    return canvas


def create_player_trend_figure(seasons, fm_data, mv_data, gf_data, gs_data, rp_data, rc_data, ass_data, player_name, player_role):
    """Crea la figura completa del trend per il giocatore con statistiche specifiche per ruolo."""

    # Determina quali statistiche mostrare in base al ruolo
    if player_role == 'P':  # Portiere
        stats_to_show = [
            ('Fantamedia (Fm)', fm_data, 'line', LINE_COLORS['fantamedia'], 'o'),
            ('Media Voto (Mv)', mv_data, 'line', LINE_COLORS['media_voto'], 's'),
            ('Gol Subiti (Gs)', gs_data, 'bar', LINE_COLORS['media_voto'], None),
            ('Rigori Parati (Rp)', rp_data, 'bar', LINE_COLORS['gol'], None)
        ]
    elif player_role == 'D':  # Difensore
        stats_to_show = [
            ('Fantamedia (Fm)', fm_data, 'line', LINE_COLORS['fantamedia'], 'o'),
            ('Media Voto (Mv)', mv_data, 'line', LINE_COLORS['media_voto'], 's'),
            ('Gol Fatti (Gf)', gf_data, 'bar', LINE_COLORS['gol'], None),
            ('Assist (Ass)', ass_data, 'bar', LINE_COLORS['assist'], None)
        ]
    elif player_role == 'C':  # Centrocampista
        stats_to_show = [
            ('Fantamedia (Fm)', fm_data, 'line', LINE_COLORS['fantamedia'], 'o'),
            ('Media Voto (Mv)', mv_data, 'line', LINE_COLORS['media_voto'], 's'),
            ('Gol Fatti (Gf)', gf_data, 'bar', LINE_COLORS['gol'], None),
            ('Assist (Ass)', ass_data, 'bar', LINE_COLORS['assist'], None)
        ]
    elif player_role == 'A':  # Attaccante
        stats_to_show = [
            ('Fantamedia (Fm)', fm_data, 'line', LINE_COLORS['fantamedia'], 'o'),
            ('Media Voto (Mv)', mv_data, 'line', LINE_COLORS['media_voto'], 's'),
            ('Gol Fatti (Gf)', gf_data, 'bar', LINE_COLORS['gol'], None),
            ('Assist (Ass)', ass_data, 'bar', LINE_COLORS['assist'], None)
        ]
    else:  # Default - mostra tutto
        stats_to_show = [
            ('Fantamedia (Fm)', fm_data, 'line', LINE_COLORS['fantamedia'], 'o'),
            ('Media Voto (Mv)', mv_data, 'line', LINE_COLORS['media_voto'], 's'),
            ('Gol Fatti (Gf)', gf_data, 'bar', LINE_COLORS['gol'], None),
            ('Assist (Ass)', ass_data, 'bar', LINE_COLORS['assist'], None)
        ]

    fig, axes = create_figure(
        nrows=2,
        ncols=2,
        figsize=(10, 7),
        suptitle=f'Evoluzione Stagionale • {player_name}'
    )

    # Popola i subplot con le statistiche appropriate
    for idx, (title, data, chart_type, color, marker) in enumerate(stats_to_show):
        row = idx // 2
        col = idx % 2
        ax = axes[row, col]

        if chart_type == 'line':
            # Estrai titolo base senza parentesi
            base_title = extract_base_role(title) if '(' in title else title.split('(')[0].strip()
            create_line_chart(ax, seasons, data, base_title, color=color, marker=marker)
            configure_subplot(ax, title=title)
            ax.set_ylim(bottom=min(data) * 0.8 if data and min(data) > 0 else 0)
            add_value_labels_on_line(ax, seasons, data, offset=0.08)
        else:  # bar
            bars = create_bar_chart(ax, seasons, data, color=color)
            configure_subplot(ax, title=title)
            add_value_labels_on_bars(ax, bars, is_float=False)

    fig.tight_layout(pad=2.0)
    return fig


def create_comparison_figure(player_names, fm_values, mv_values, pv_values, bonus_values, bonus_title='Gol Fatti'):
    """Crea la figura per il confronto diretto."""
    fig, axes = create_figure(
        nrows=2,
        ncols=2,
        figsize=(11, 6.5)
    )

    metrics = [
        ("Fantamedia", fm_values, axes[0, 0]),
        ("Media Voto", mv_values, axes[0, 1]),
        ("Partite Giocate", pv_values, axes[1, 0]),
        (bonus_title, bonus_values, axes[1, 1])
    ]

    for title, values, ax in metrics:
        bars = create_comparison_bar_chart(ax, player_names, values, width=0.4)
        configure_subplot(ax, title=title)

        for bar in bars:
            h = bar.get_height()
            label = f'{h:.2f}' if isinstance(h, float) and h % 1 != 0 else f'{int(h)}'
            ax.annotate(
                label,
                xy=(bar.get_x() + bar.get_width() / 2, h),
                xytext=(0, 4),
                textcoords="offset points",
                ha='center',
                va='bottom',
                color=CHART_COLORS['text_primary'],
                fontsize=9,
                fontweight='bold'
            )

    fig.subplots_adjust(hspace=0.35, wspace=0.25)
    return fig


def create_advanced_comparison_figure(player_names, stats_dict, role='C'):
    """Crea la figura avanzata con griglia dinamica."""
    stat_names = {
        'Fm': 'Fantamedia',
        'Mv': 'Media Voto',
        'Pv': 'Partite Giocate',
        'Gf': 'Gol Fatti',
        'Gs': 'Gol Subiti',
        'Rp': 'Rigori Parati',
        'Ass': 'Assist'
    }

    num_stats = len(stats_dict)
    if num_stats <= 3:
        rows, cols = 1, num_stats
    elif num_stats <= 6:
        rows, cols = 2, 3
    else:
        rows, cols = 3, 3

    fig, axes = create_figure(
        nrows=rows,
        ncols=cols,
        figsize=(13, 7.5),
        suptitle=f'Confronto Statistico • Ruolo {role}'
    )

    if num_stats == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    for idx, (stat_key, values) in enumerate(stats_dict.items()):
        ax = axes[idx]

        bars = create_comparison_bar_chart(ax, player_names, values, width=0.45)
        stat_display = stat_names.get(stat_key, stat_key)
        configure_subplot(ax, title=stat_display)

        for bar, val in zip(bars, values):
            try:
                numeric_val = float(val) if not isinstance(val, (int, float)) else val
            except (ValueError, TypeError):
                numeric_val = 0

            label = f'{numeric_val:.2f}' if stat_key in ['Mv', 'Fm'] else f'{int(numeric_val)}'
            height = bar.get_height()

            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                label,
                ha='center',
                va='bottom',
                fontweight='bold',
                color=CHART_COLORS['text_primary'],
                fontsize=9,
                zorder=4
            )

    for idx in range(num_stats, len(axes)):
        axes[idx].set_visible(False)

    fig.tight_layout(rect=[0, 0, 1, 0.95], pad=2.0)
    return fig