"""Page 5 — Prédictions : risque de churn, croisement segment/valeur.

Seuls les filtres ville et genre s'appliquent (via jointure avec les clients).
Les mesures portent sur les clients disposant d'une prédiction (726 au total).
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
from core.formats import format_entier, format_nombre, format_pourcentage
from data.loaders import charger_clients, charger_resultat


def _cartes_kpi(mesures: dict[str, float], seuil: float) -> None:
    """Cartes KPI : clients à risque, part des clients scorés, CLV à risque."""
    colonnes = st.columns(3)
    with colonnes[0]:
        carte_kpi(
            "Clients à risque",
            format_entier(mesures["nb_risque"]),
            "warning",
            note=f"probabilité ≥ {seuil:.2f}",
            accent="rose",
        )
    with colonnes[1]:
        carte_kpi(
            "Part des clients avec prédiction",
            format_pourcentage(mesures["part"]),
            "percent",
            note=f"sur {format_entier(mesures['total'])} clients scorés",
            accent="violet",
        )
    with colonnes[2]:
        carte_kpi(
            "CLV à risque (24 mois)",
            format_nombre(mesures["clv_risque"]),
            "savings",
            accent="turquoise",
        )


def _segment_risque(predictions_segment: pd.DataFrame, seuil: float) -> None:
    """Croisement segment / risque : clients à risque vs valeur (CLV) à risque."""
    with st.container(border=True):
        titre_carte("Segment et risque : où se concentre la valeur à protéger")
        risque = calculs.risque_par_segment(predictions_segment, seuil)
        if risque.empty:
            st.info("Aucun client à risque à ce seuil.")
            return
        seg_clients = risque.loc[risque["Clients"].idxmax(), config.COL_SEGMENT_NOM]
        seg_valeur = risque.loc[risque["CLV"].idxmax(), config.COL_SEGMENT_NOM]
        if seg_clients != seg_valeur:
            st.info(
                f"Le segment comptant le plus de clients à risque est « {seg_clients} », "
                f"mais la valeur (CLV) à risque se concentre sur « {seg_valeur} » : "
                "ce n'est pas le segment le plus nombreux qu'il faut prioriser."
            )
        else:
            st.info(
                f"« {seg_clients} » concentre à la fois le plus de clients à risque "
                "et la plus forte CLV à risque."
            )
        gauche, droite = st.columns(2)
        with gauche:
            titre_carte("Clients à risque par segment")
            graphiques.afficher(
                graphiques.barres_valeur(
                    risque.sort_values("Clients"),
                    config.COL_SEGMENT_NOM,
                    "Clients",
                    orientation="h",
                )
            )
        with droite:
            titre_carte("CLV à risque par segment")
            graphiques.afficher(
                graphiques.barres_valeur(
                    risque.sort_values("CLV"),
                    config.COL_SEGMENT_NOM,
                    "CLV",
                    orientation="h",
                )
            )


def _tableau(predictions_segment: pd.DataFrame) -> None:
    """Tableau des clients trié par probabilité, formaté en français."""
    tri = predictions_segment.sort_values(config.COL_PROBA_CHURN, ascending=False)
    affichage = pd.DataFrame(
        {
            config.COL_CLIENT: tri[config.COL_CLIENT],
            config.COL_SEGMENT_NOM: tri[config.COL_SEGMENT_NOM],
            "Proba": tri[config.COL_PROBA_CHURN] * 100,
            config.COL_CLV: tri[config.COL_CLV],
        }
    )
    with st.container(border=True):
        titre_carte("Clients triés par probabilité de churn")
        st.dataframe(
            affichage,
            width="stretch",
            hide_index=True,
            column_config={
                config.COL_CLIENT: st.column_config.NumberColumn("Identifiant", format="%d"),
                config.COL_SEGMENT_NOM: st.column_config.TextColumn("Segment"),
                "Proba": st.column_config.NumberColumn("Probabilité de churn", format="%.1f %%"),
                config.COL_CLV: st.column_config.NumberColumn("CLV (24 mois)", format="%.2f"),
            },
        )


def afficher() -> None:
    """Rend la page Prédictions ou son état vide."""
    entete_page(
        "Prédictions",
        "Risque de churn et valeur à protéger, par client et par segment.",
    )
    predictions = charger_resultat(config.RESULTAT_PREDICTIONS.cle)
    if predictions is None:
        afficher_etat_vide(config.RESULTAT_PREDICTIONS)
        return

    segments = charger_resultat(config.RESULTAT_SEGMENTS.cle)
    predictions_segment = calculs.predictions_avec_segment(predictions, segments)

    filtres: Filtres = st.session_state["filtres"]
    clients = calculs.filtrer_clients(charger_clients(), filtres)
    predictions_segment = predictions_segment[
        predictions_segment[config.COL_CLIENT].isin(clients[config.COL_CLIENT])
    ]
    if predictions_segment.empty:
        st.info("Aucun client avec prédiction ne correspond aux filtres sélectionnés.")
        return

    seuil = st.slider(
        "Seuil de risque (probabilité de churn)",
        min_value=0.0,
        max_value=1.0,
        value=config.SEUIL_RISQUE_DEFAUT,
        step=0.01,
    )
    _cartes_kpi(calculs.mesures_risque(predictions_segment, seuil), seuil)
    st.write("")

    _segment_risque(predictions_segment, seuil)

    gauche, droite = st.columns(2)
    with gauche, st.container(border=True):
        titre_carte("Distribution des probabilités de churn")
        graphiques.afficher(
            graphiques.histogramme(
                predictions_segment,
                config.COL_PROBA_CHURN,
                "Probabilité de churn",
                nbins=30,
                ligne_seuil=seuil,
            )
        )
    with droite, st.container(border=True):
        titre_carte("CLV selon la probabilité de churn, par segment")
        graphiques.afficher(
            graphiques.nuage(
                predictions_segment,
                config.COL_PROBA_CHURN,
                config.COL_CLV,
                config.COL_SEGMENT_NOM,
                "Probabilité de churn",
                "CLV (24 mois)",
            )
        )

    _tableau(predictions_segment)


afficher()
