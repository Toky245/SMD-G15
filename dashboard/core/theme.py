"""Thème visuel : tokens de couleurs, CSS (police Inter, cartes), template Plotly.

Les couleurs sont définies ici une seule fois et réutilisées partout (interface
et graphiques), en cohérence avec .streamlit/config.toml.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# --- Tokens de couleurs ------------------------------------------------------
COULEUR_FOND = "#F8FAFC"
COULEUR_SURFACE = "#FFFFFF"
COULEUR_BORDURE = "#E2E8F0"
COULEUR_TEXTE = "#0F172A"
COULEUR_TEXTE_SECONDAIRE = "#64748B"
# Couleur principale reprise du logo (violet). Utilisée avec parcimonie.
COULEUR_PRIMAIRE = "#6F3BFD"
COULEUR_PRIMAIRE_FONCE = "#5A28E0"

# Palette catégorielle reprise des couleurs du logo (+ gris neutre).
PALETTE_CATEGORIELLE: tuple[str, ...] = (
    "#6F3BFD",
    "#FB315D",
    "#FFC228",
    "#07E0B0",
    "#64748B",
)

COULEUR_SUCCES = "#16A34A"
COULEUR_ALERTE = "#D97706"
COULEUR_DANGER = "#DC2626"

# Teintes claires (couleurs unies) pour puces, badges et aires de graphiques.
TINT_PRIMAIRE = "#F1ECFE"
TINT_SUCCES = "#DCFCE7"
TINT_DANGER = "#FEE2E2"
TINT_NEUTRE = "#F1F5F9"

POLICE = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

_NOM_TEMPLATE_PLOTLY = "smd"

# --- CSS ---------------------------------------------------------------------
_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

html, body, [class*="css"], .stApp, button, input, select, textarea {{
    font-family: {POLICE};
}}
.stApp {{ background-color: {COULEUR_FOND}; }}

/* Icônes Material Symbols pour les composants sur mesure (cartes, marque). */
.material-symbols-outlined {{
    font-family: 'Material Symbols Outlined';
    font-weight: normal;
    font-style: normal;
    line-height: 1;
    display: inline-block;
    white-space: nowrap;
    direction: ltr;
    -webkit-font-feature-settings: 'liga';
    -webkit-font-smoothing: antialiased;
}}

/* Largeur de contenu et respiration. */
.block-container {{ padding-top: 2.4rem; padding-bottom: 3rem; max-width: 1320px; }}

/* ---------------------------------------------------------------- Cartes -- */
/* La carte bordée : le testid varie selon la version de Streamlit, on cible
   les deux formes connues (stContainer dans cette version). */
div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stContainer"] {{
    background-color: {COULEUR_SURFACE};
    border: 1px solid {COULEUR_BORDURE};
    border-radius: 12px;
    padding: 10px 14px;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}}
.card-title {{
    color: {COULEUR_TEXTE};
    font-size: 0.95rem;
    font-weight: 600;
    margin: 4px 4px 10px 4px;
    letter-spacing: -0.01em;
}}

/* ------------------------------------------------------------ Cartes KPI -- */
.kpi-card {{
    background: {COULEUR_SURFACE};
    border: 1px solid {COULEUR_BORDURE};
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-height: 138px;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}}
.kpi-card:hover {{
    border-color: #CBD5E1;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.06);
}}
.kpi-top {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }}
.kpi-chip {{
    width: 40px; height: 40px;
    border-radius: 12px;
    display: inline-flex; align-items: center; justify-content: center;
    flex: 0 0 auto;
}}
.kpi-chip .material-symbols-outlined {{ font-size: 22px; }}
.kpi-card-label {{
    color: {COULEUR_TEXTE_SECONDAIRE};
    font-size: 0.82rem;
    font-weight: 500;
}}
.kpi-card-value {{
    color: {COULEUR_TEXTE};
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.05;
    letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums;
}}
.kpi-card-foot {{ display: flex; align-items: center; gap: 8px; min-height: 22px; }}
.kpi-trend {{
    display: inline-flex; align-items: center; gap: 2px;
    font-size: 0.82rem; font-weight: 600;
    font-variant-numeric: tabular-nums;
}}
.kpi-trend .material-symbols-outlined {{ font-size: 17px; }}
.kpi-trend-pos {{ color: {COULEUR_SUCCES}; }}
.kpi-trend-neg {{ color: {COULEUR_DANGER}; }}
.kpi-foot-note {{ color: {COULEUR_TEXTE_SECONDAIRE}; font-size: 0.8rem; }}

/* --------------------------------------------------------- En-tête page -- */
.page-titre {{
    color: {COULEUR_TEXTE};
    font-size: 1.7rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 2px;
}}
.page-sous-titre {{
    color: {COULEUR_TEXTE_SECONDAIRE};
    font-size: 0.95rem;
    margin-top: 0;
}}

/* ------------------------------------------------------------- Sidebar --- */
section[data-testid="stSidebar"] {{
    background: {COULEUR_SURFACE};
    border-right: 1px solid {COULEUR_BORDURE};
}}
section[data-testid="stSidebar"] .block-container {{ padding-top: 1.2rem; }}

/* Marque / logo */
.marque {{ display: flex; align-items: center; gap: 11px; padding: 2px 4px 14px 4px; }}
.marque-logo {{ flex: 0 0 auto; display: inline-flex; }}
.marque-nom {{
    color: {COULEUR_TEXTE};
    font-size: 1.02rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.15;
}}
.marque-sous {{ color: {COULEUR_TEXTE_SECONDAIRE}; font-size: 0.74rem; font-weight: 500; }}
.sidebar-section {{
    color: {COULEUR_TEXTE_SECONDAIRE};
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin: 6px 4px 2px 4px;
}}

/* Liens de navigation (st.navigation) */
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {{
    border-radius: 9px;
    margin: 2px 0;
    padding-top: 7px; padding-bottom: 7px;
    color: {COULEUR_TEXTE_SECONDAIRE};
    transition: background 0.12s ease, color 0.12s ease;
}}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover {{
    background: {TINT_NEUTRE};
    color: {COULEUR_TEXTE};
}}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"] {{
    background: {TINT_NEUTRE};
    color: {COULEUR_TEXTE};
    font-weight: 600;
}}

/* ------------------------------------------------- Champs de formulaire -- */
div[data-baseweb="select"] > div {{
    border-radius: 9px;
    border-color: {COULEUR_BORDURE};
    min-height: 40px;
    background: {COULEUR_SURFACE};
    transition: border-color 0.12s ease, box-shadow 0.12s ease;
}}
div[data-baseweb="select"] > div:hover {{ border-color: #CBD5E1; }}
div[data-baseweb="select"] > div:focus-within {{
    border-color: {COULEUR_PRIMAIRE};
    box-shadow: 0 0 0 3px {TINT_PRIMAIRE};
}}
div[data-baseweb="tag"] {{
    background: {TINT_NEUTRE} !important;
    color: {COULEUR_TEXTE} !important;
    border-radius: 7px !important;
    font-weight: 500;
    border: 1px solid {COULEUR_BORDURE} !important;
}}
div[data-baseweb="tag"] span {{ color: {COULEUR_TEXTE} !important; }}
div[data-baseweb="tag"] svg {{ fill: {COULEUR_TEXTE_SECONDAIRE} !important; }}

/* Menu déroulant (popover) — carte arrondie à l'ombre douce, façon Material. */
ul[data-baseweb="menu"] {{
    border-radius: 12px;
    border: 1px solid {COULEUR_BORDURE};
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12);
    padding: 6px;
    background: {COULEUR_SURFACE};
}}
ul[data-baseweb="menu"] li {{
    border-radius: 8px;
    margin: 1px 2px;
    transition: background 0.1s ease;
}}
ul[data-baseweb="menu"] li:hover {{ background: {TINT_NEUTRE}; }}
ul[data-baseweb="menu"] li[aria-selected="true"] {{
    background: {TINT_PRIMAIRE};
    color: {COULEUR_PRIMAIRE};
}}

.stTextInput input, .stDateInput input {{
    border-radius: 9px;
}}
.stTextInput div[data-baseweb="input"], .stDateInput div[data-baseweb="input"] {{
    border-radius: 9px;
    border-color: {COULEUR_BORDURE};
}}
.stTextInput div[data-baseweb="input"]:focus-within,
.stDateInput div[data-baseweb="input"]:focus-within {{
    border-color: {COULEUR_PRIMAIRE};
    box-shadow: 0 0 0 3px {TINT_PRIMAIRE};
}}

/* ------------------------------------------------------------- Boutons --- */
.stButton > button, .stDownloadButton > button {{
    border-radius: 9px;
    font-weight: 500;
    padding: 0.42rem 0.9rem;
    transition: background 0.12s ease, border-color 0.12s ease, color 0.12s ease;
}}
.stButton > button[kind="secondary"], .stDownloadButton > button[kind="secondary"] {{
    background: {COULEUR_SURFACE};
    border: 1px solid {COULEUR_BORDURE};
    color: {COULEUR_TEXTE};
}}
.stButton > button[kind="secondary"]:hover, .stDownloadButton > button[kind="secondary"]:hover {{
    background: {TINT_NEUTRE};
    border-color: #CBD5E1;
    color: {COULEUR_TEXTE};
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
    background: {COULEUR_PRIMAIRE};
    border: 1px solid {COULEUR_PRIMAIRE};
    color: #FFFFFF;
}}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {{
    background: {COULEUR_PRIMAIRE_FONCE};
    border-color: {COULEUR_PRIMAIRE_FONCE};
    box-shadow: 0 2px 6px rgba(111, 59, 253, 0.28);
}}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {{
    outline: none;
    box-shadow: 0 0 0 3px {TINT_PRIMAIRE};
}}

/* ------------------------------------------------------------- Tableau --- */
div[data-testid="stDataFrame"] {{ border-radius: 10px; border: 1px solid {COULEUR_BORDURE}; }}
</style>
"""


def _axe() -> dict:
    """Style commun des axes du template Plotly."""
    return {
        "showgrid": False,
        "zeroline": False,
        "showline": False,
        "ticks": "",
        "tickfont": {"color": COULEUR_TEXTE_SECONDAIRE, "size": 12},
        "title": {"font": {"color": COULEUR_TEXTE_SECONDAIRE, "size": 12}},
        "automargin": True,
    }


def _construire_template_plotly() -> go.layout.Template:
    """Construit le template Plotly commun (épuré, grille horizontale légère)."""
    axe_x = _axe()
    axe_y = {**_axe(), "showgrid": True, "gridcolor": COULEUR_BORDURE, "gridwidth": 1}
    return go.layout.Template(
        layout=go.Layout(
            font={"family": POLICE, "color": COULEUR_TEXTE, "size": 13},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            colorway=list(PALETTE_CATEGORIELLE),
            separators=", ",
            margin={"l": 8, "r": 16, "t": 12, "b": 8},
            xaxis=axe_x,
            yaxis=axe_y,
            bargap=0.32,
            hoverlabel={
                "bgcolor": COULEUR_SURFACE,
                "bordercolor": COULEUR_BORDURE,
                "font": {"family": POLICE, "color": COULEUR_TEXTE, "size": 12},
            },
            hovermode="closest",
            legend={
                "title": {"text": ""},
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "x": 0,
                "font": {"color": COULEUR_TEXTE_SECONDAIRE, "size": 12},
            },
        )
    )


def configurer_plotly() -> None:
    """Enregistre le template Plotly commun et le définit par défaut."""
    pio.templates[_NOM_TEMPLATE_PLOTLY] = _construire_template_plotly()
    pio.templates.default = _NOM_TEMPLATE_PLOTLY


def appliquer_theme() -> None:
    """Injecte le CSS (police, cartes) et configure Plotly. À appeler une fois."""
    st.markdown(_CSS, unsafe_allow_html=True)
    configurer_plotly()
