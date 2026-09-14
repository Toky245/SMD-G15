"""Barre latérale des filtres globaux, partagés entre toutes les pages.

L'état est conservé dans st.session_state ; le bouton de réinitialisation
supprime les clés pour revenir aux valeurs par défaut.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from core import calculs, config
from core.config import Filtres

_CLES = ("f_periode", "f_canaux", "f_categories", "f_villes", "f_genres")


def _reinitialiser() -> None:
    """Callback du bouton de réinitialisation : efface les clés de filtres."""
    for cle in _CLES:
        st.session_state.pop(cle, None)


def _selection_periode(bornes: tuple[date, date]) -> tuple[date, date]:
    """Widget de sélection de la période, robuste à une sélection partielle."""
    minimum, maximum = bornes
    selection = st.sidebar.date_input(
        "Période",
        value=bornes,
        min_value=minimum,
        max_value=maximum,
        format="DD/MM/YYYY",
        key="f_periode",
    )
    if isinstance(selection, (list, tuple)):
        if len(selection) == 2:
            return selection[0], selection[1]
        if len(selection) == 1:
            return selection[0], maximum
    return minimum, maximum


def _selection_multiple(
    label: str,
    options: list[str],
    cle: str,
    libelles: dict[str, str] | None = None,
) -> tuple[str, ...]:
    """Widget multiselect renvoyant un tuple (vide = toutes les modalités)."""
    selection = st.sidebar.multiselect(
        label,
        options=options,
        default=None,
        format_func=(lambda v: libelles.get(v, v)) if libelles else str,
        placeholder="Toutes",
        key=cle,
    )
    return tuple(selection)


def construire_filtres(ventes: pd.DataFrame, *, filtres_ventes: bool = True) -> Filtres:
    """Construit la barre latérale de filtres et renvoie la sélection.

    Args:
        ventes: ventes complètes, servant à déterminer bornes et modalités.
        filtres_ventes: si True, affiche période/canal/catégorie (filtres au niveau
            des ventes) ; sinon seuls ville et genre s'appliquent, avec une note.

    Returns:
        Les filtres correspondant à la sélection courante ; les dimensions non
        affichées valent « toutes » (période complète, tuples vides).
    """
    st.sidebar.divider()
    st.sidebar.markdown('<div class="sidebar-section">Filtres</div>', unsafe_allow_html=True)
    bornes = calculs.bornes_dates(ventes)

    if filtres_ventes:
        date_debut, date_fin = _selection_periode(bornes)
        canaux = _selection_multiple(
            "Canal", list(config.CANAUX_VENTES), "f_canaux", config.LIBELLES_CANAUX
        )
        categories = _selection_multiple("Catégorie", list(config.CATEGORIES), "f_categories")
    else:
        date_debut, date_fin = bornes
        canaux = ()
        categories = ()

    villes = _selection_multiple("Ville", calculs.modalites(ventes, config.COL_VILLE), "f_villes")
    genres = _selection_multiple(
        "Genre",
        calculs.modalites(ventes, config.COL_GENRE),
        "f_genres",
        config.LIBELLES_GENRES,
    )

    if not filtres_ventes:
        st.sidebar.caption(
            "Les filtres période, canal et catégorie portent sur les ventes ; "
            "ils ne s'appliquent pas à cette page centrée sur les clients."
        )

    st.sidebar.button(
        "Réinitialiser les filtres",
        icon=":material/restart_alt:",
        on_click=_reinitialiser,
        width="stretch",
    )

    return Filtres(
        date_debut=date_debut,
        date_fin=date_fin,
        canaux=canaux,
        categories=categories,
        villes=villes,
        genres=genres,
    )
