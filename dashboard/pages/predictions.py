"""Page 5 — Prédictions. État vide tant que predictions_churn.csv est absent."""

from __future__ import annotations

import streamlit as st

from components.cartes import carte_kpi
from components.etat_vide import afficher_etat_vide
from components.mise_en_page import entete_page, titre_carte
from core import config
from core.formats import format_entier, format_pourcentage
from data.loaders import charger_resultat

_SEUIL_RISQUE = 0.5


def afficher() -> None:
    """Rend la page Prédictions ou son état vide."""
    entete_page(
        "Prédictions",
        "Clients à risque de churn, triés par probabilité décroissante.",
    )
    predictions = charger_resultat(config.RESULTAT_PREDICTIONS.cle)
    if predictions is None:
        afficher_etat_vide(config.RESULTAT_PREDICTIONS)
        return

    tri = predictions.sort_values("Proba_Churn", ascending=False)
    nb_risque = int((predictions["Proba_Churn"] >= _SEUIL_RISQUE).sum())
    part = nb_risque / len(predictions) * 100 if len(predictions) else 0.0

    gauche, droite = st.columns(2)
    with gauche:
        carte_kpi(
            "Clients à risque",
            format_entier(nb_risque),
            "warning",
            note=f"probabilité ≥ {_SEUIL_RISQUE:.0%}".replace("%", " %"),
            accent="rose",
        )
    with droite:
        carte_kpi("Part de la base", format_pourcentage(part), "percent", accent="violet")

    st.write("")
    with st.container(border=True):
        titre_carte("Clients triés par probabilité de churn")
        st.dataframe(tri, width="stretch", hide_index=True)


afficher()
