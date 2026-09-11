"""Page 4 — Campagnes. État vide tant que kpis_campagnes.csv est absent."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.etat_vide import afficher_etat_vide
from components.mise_en_page import entete_page, titre_carte
from core import config
from data.loaders import charger_resultat


def _kpis_par_canal(kpis: pd.DataFrame) -> pd.DataFrame:
    """Agrège les indicateurs de campagne par canal."""
    return (
        kpis.groupby("Channel")
        .agg(
            Campagnes=("Campaign_ID", "count"),
            Budget=("Budget", "sum"),
            Impressions=("Impressions", "sum"),
            Clics=("Clicks", "sum"),
            Conversions=("Conversions", "sum"),
            ROI_moyen=("ROI", "mean"),
        )
        .reset_index()
        .round(2)
    )


def afficher() -> None:
    """Rend la page Campagnes ou son état vide."""
    entete_page("Campagnes", "Performance des campagnes par canal et par campagne.")
    kpis = charger_resultat(config.RESULTAT_CAMPAGNES.cle)
    if kpis is None:
        afficher_etat_vide(config.RESULTAT_CAMPAGNES)
        return

    with st.container(border=True):
        titre_carte("Indicateurs par canal")
        st.dataframe(_kpis_par_canal(kpis), width="stretch", hide_index=True)
    with st.container(border=True):
        titre_carte("Détail par campagne")
        st.dataframe(kpis, width="stretch", hide_index=True)


afficher()
