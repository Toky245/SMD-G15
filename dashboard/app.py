"""Point d'entrée du dashboard M8 (marketing digital).

Lancement : streamlit run dashboard/app.py

Configure le thème, construit les filtres globaux dans la barre latérale et
orchestre la navigation multipage (st.navigation / st.Page).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Garantit que le dossier `dashboard/` est prioritaire dans sys.path afin que
# les paquets core/, data/, components/ soient importables sans ambiguïté.
_DOSSIER_DASHBOARD = Path(__file__).resolve().parent
if str(_DOSSIER_DASHBOARD) not in sys.path:
    sys.path.insert(0, str(_DOSSIER_DASHBOARD))

import streamlit as st  # noqa: E402

from components.filtres import construire_filtres  # noqa: E402
from core import config  # noqa: E402
from core.theme import appliquer_theme  # noqa: E402
from data.loaders import charger_ventes  # noqa: E402

_PAGES_DIR = config.DOSSIER_DASHBOARD / "pages"
_LOGO = config.DOSSIER_DASHBOARD / "assets" / "logo.svg"


def _construire_pages() -> list[st.Page]:
    """Déclare les pages de l'application avec leurs icônes Material."""
    return [
        st.Page(
            _PAGES_DIR / "vue_ensemble.py",
            title="Vue d'ensemble",
            icon=":material/dashboard:",
            default=True,
        ),
        st.Page(_PAGES_DIR / "clients.py", title="Clients", icon=":material/group:"),
        st.Page(_PAGES_DIR / "segments.py", title="Segments", icon=":material/scatter_plot:"),
        st.Page(_PAGES_DIR / "campagnes.py", title="Campagnes", icon=":material/campaign:"),
        st.Page(
            _PAGES_DIR / "predictions.py",
            title="Prédictions",
            icon=":material/online_prediction:",
        ),
    ]


def main() -> None:
    """Configure la page, la navigation et les filtres, puis exécute la page."""
    st.set_page_config(
        page_title="Dashboard M8 — Marketing digital",
        page_icon=":material/insights:",
        layout="wide",
    )
    appliquer_theme()

    # Logo affiché en haut de la barre latérale (au-dessus du menu).
    st.logo(str(_LOGO), size="large")
    page = st.navigation(_construire_pages(), position="sidebar")

    # Les filtres sont construits sous le menu et partagés via session_state.
    st.session_state["filtres"] = construire_filtres(charger_ventes())

    page.run()


main()
