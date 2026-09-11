"""Page 3 — Segments. État vide tant que segments.csv est absent."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.cartes import carte_kpi
from components.etat_vide import afficher_etat_vide
from components.mise_en_page import entete_page, titre_carte
from core import config
from core.formats import format_entier
from data.loaders import charger_clients, charger_resultat


def _profil_moyen(segments: pd.DataFrame, clients: pd.DataFrame) -> pd.DataFrame:
    """Calcule le profil moyen de chaque segment."""
    fusion = segments.merge(clients, on=config.COL_CLIENT, how="left")
    profil = (
        fusion.groupby("Segment_Nom")
        .agg(
            Clients=(config.COL_CLIENT, "count"),
            Age_moyen=(config.COL_AGE, "mean"),
            Panier_moyen=(config.COL_PANIER_MOYEN, "mean"),
            Montant_moyen=(config.COL_MONTANT_TOTAL, "mean"),
            Recence_moyenne=(config.COL_RECENCE, "mean"),
            Achats_moyens=(config.COL_NB_ACHATS, "mean"),
        )
        .reset_index()
        .round(1)
    )
    return profil


def afficher() -> None:
    """Rend la page Segments ou son état vide."""
    entete_page("Segments", "Profil moyen de chaque segment de clients.")
    segments = charger_resultat(config.RESULTAT_SEGMENTS.cle)
    if segments is None:
        afficher_etat_vide(config.RESULTAT_SEGMENTS)
        return

    profil = _profil_moyen(segments, charger_clients())
    carte_kpi("Nombre de segments", format_entier(len(profil)), "scatter_plot", accent="violet")
    st.write("")
    with st.container(border=True):
        titre_carte("Profil moyen par segment")
        st.dataframe(profil, width="stretch", hide_index=True)


afficher()
