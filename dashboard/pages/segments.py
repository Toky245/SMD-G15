"""Page 3 — Segments : profil moyen et analyses par segment.

Seuls les filtres ville et genre s'appliquent (via jointure avec les clients) ;
les 79 clients sans achat (segment -1) sont comptés mais exclus des moyennes de
comportement et des analyses de dépense.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import graphiques
from components.cartes import carte_kpi
from components.etat_vide import afficher_etat_vide
from components.mise_en_page import entete_page, titre_carte
from core import calculs, config
from core.config import Filtres
from core.formats import format_entier
from data.loaders import charger_clients, charger_resultat

_LIBELLES_PROFIL: dict[str, str] = {
    config.COL_SEGMENT_NOM: "Segment",
    "Clients": "Clients",
    "Age_moyen": "Âge moyen",
    "Panier_moyen": "Panier moyen",
    "Montant_moyen": "Montant moyen",
    "Recence_moyenne": "Récence moyenne",
    "Achats_moyens": "Achats moyens",
}


def _graphiques(segments: pd.DataFrame, clients: pd.DataFrame) -> None:
    """Répartition, chiffre d'affaires et composition des dépenses par segment."""
    gauche, droite = st.columns(2)
    with gauche, st.container(border=True):
        titre_carte("Répartition des clients par segment")
        repartition = calculs.repartition_segments(segments, clients)
        graphiques.afficher(
            graphiques.barres_valeur(
                repartition, config.COL_SEGMENT_NOM, "Clients", orientation="h"
            )
        )
    with droite, st.container(border=True):
        titre_carte("Chiffre d'affaires par segment (part du total)")
        ca = calculs.ca_par_segment(segments, clients)
        ca["Label"] = ca[config.COL_SEGMENT_NOM] + " — " + ca["Part"].round(1).astype(str) + " %"
        graphiques.afficher(
            graphiques.barres_valeur(ca, "Label", "CA", orientation="h", suffixe="€")
        )
    with st.container(border=True):
        titre_carte("Composition moyenne des dépenses par catégorie et par segment")
        composition = calculs.composition_par_segment(segments, clients)
        graphiques.afficher(
            graphiques.barres_empilees(composition, config.COL_SEGMENT_NOM, "Part", "Categorie")
        )


def afficher() -> None:
    """Rend la page Segments ou son état vide."""
    entete_page("Segments", "Profil moyen et analyses de chaque segment de clients.")
    segments = charger_resultat(config.RESULTAT_SEGMENTS.cle)
    if segments is None:
        afficher_etat_vide(config.RESULTAT_SEGMENTS)
        return

    filtres: Filtres = st.session_state["filtres"]
    clients = calculs.filtrer_clients(charger_clients(), filtres)
    if clients.empty:
        st.info("Aucun client ne correspond aux filtres sélectionnés.")
        return

    carte_kpi(
        "Nombre de segments",
        format_entier(calculs.nombre_segments_reels(segments)),
        "scatter_plot",
        accent="violet",
    )
    st.caption(
        "Les 79 clients sans achat (segment -1) sont comptés dans la répartition, "
        "mais exclus des moyennes de comportement et des analyses de dépense."
    )
    st.write("")

    profil = calculs.profil_segments(segments, clients).rename(columns=_LIBELLES_PROFIL)
    with st.container(border=True):
        titre_carte("Profil moyen par segment")
        st.dataframe(profil, width="stretch", hide_index=True)

    _graphiques(segments, clients)


afficher()
