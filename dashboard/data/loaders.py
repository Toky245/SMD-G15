"""Chargement des CSV en lecture seule, avec mise en cache Streamlit.

Le dashboard ne fait que lire les données : aucune fonction n'écrit sur disque.
Les fichiers de data/results/ peuvent être absents ; le chargeur renvoie alors
None sans lever d'erreur.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core import config


@st.cache_data(show_spinner=False)
def charger_ventes() -> pd.DataFrame:
    """Charge les ventes fusionnées, dates converties en datetime."""
    ventes = pd.read_csv(config.FICHIER_VENTES)
    ventes[config.COL_DATE] = pd.to_datetime(ventes[config.COL_DATE])
    return ventes


@st.cache_data(show_spinner=False)
def charger_clients() -> pd.DataFrame:
    """Charge les clients agrégés (une ligne par client)."""
    clients = pd.read_csv(config.FICHIER_CLIENTS)
    for colonne in ("Join_Date", "Premier_Achat", "Dernier_Achat"):
        if colonne in clients.columns:
            clients[colonne] = pd.to_datetime(clients[colonne], errors="coerce")
    return clients


@st.cache_data(show_spinner=False)
def charger_marketing() -> pd.DataFrame:
    """Charge les campagnes marketing nettoyées."""
    return pd.read_csv(config.FICHIER_MARKETING)


@st.cache_data(show_spinner=False)
def charger_resultat(cle: str) -> pd.DataFrame | None:
    """Charge un fichier de data/results/ s'il existe, sinon None.

    Args:
        cle: clé du fichier (voir config.FichierResultat.cle).

    Returns:
        Le DataFrame chargé, ou None si le fichier est absent.
    """
    specification = _specification_resultat(cle)
    if not specification.chemin.exists():
        return None
    return pd.read_csv(specification.chemin)


def _specification_resultat(cle: str) -> config.FichierResultat:
    """Retourne la spécification du fichier de résultat pour la clé donnée."""
    specifications = {
        config.RESULTAT_SEGMENTS.cle: config.RESULTAT_SEGMENTS,
        config.RESULTAT_CAMPAGNES.cle: config.RESULTAT_CAMPAGNES,
        config.RESULTAT_PREDICTIONS.cle: config.RESULTAT_PREDICTIONS,
    }
    if cle not in specifications:
        raise KeyError(f"Clé de résultat inconnue : {cle}")
    return specifications[cle]
