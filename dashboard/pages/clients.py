"""Page 2 — Clients : démographie, comportement, tableau filtrable et export."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import graphiques
from components.cartes import carte_kpi
from components.mise_en_page import entete_page, titre_carte
from core import calculs, config
from core.config import Filtres
from core.formats import format_entier, format_euro
from data.loaders import charger_clients, charger_ventes

_FORMATS_NUMERIQUES: dict[str, str] = {
    config.COL_CLIENT: "%d",
    config.COL_AGE: "%d",
    config.COL_NB_ACHATS: "%d",
    config.COL_MONTANT_TOTAL: "%.0f €",
    config.COL_PANIER_MOYEN: "%.2f €",
    config.COL_RECENCE: "%d",
}


def _cartes_kpi(clients_selection: pd.DataFrame) -> None:
    """Affiche les indicateurs synthétiques de la sélection de clients."""
    age_moyen = clients_selection[config.COL_AGE].mean()
    montant_moyen = clients_selection[config.COL_MONTANT_TOTAL].mean()
    recence_mediane = clients_selection[config.COL_RECENCE].median()

    colonnes = st.columns(4)
    with colonnes[0]:
        carte_kpi("Clients", format_entier(len(clients_selection)), "group", accent="violet")
    with colonnes[1]:
        carte_kpi("Âge moyen", f"{age_moyen:.0f} ans", "person", accent="turquoise")
    with colonnes[2]:
        carte_kpi("Montant moyen par client", format_euro(montant_moyen), "euro", accent="ambre")
    with colonnes[3]:
        carte_kpi("Récence médiane", f"{recence_mediane:.0f} j", "history", accent="rose")


def _graphiques_demographie(clients_selection: pd.DataFrame) -> None:
    """Répartition par âge et lien entre âge et canal d'achat préféré."""
    gauche, droite = st.columns(2)
    with gauche, st.container(border=True):
        titre_carte("Répartition par âge")
        graphiques.afficher(
            graphiques.histogramme(clients_selection, config.COL_AGE, "Âge", nbins=20)
        )
    with droite, st.container(border=True):
        titre_carte("Âge selon le canal d'achat préféré")
        demo = clients_selection.dropna(subset=[config.COL_CANAL_PREFERE]).copy()
        demo["Canal"] = demo[config.COL_CANAL_PREFERE].map(config.LIBELLES_CANAUX)
        graphiques.afficher(
            graphiques.boite_par_categorie(demo, "Canal", config.COL_AGE, "Canal préféré", "Âge")
        )


def _graphiques_distributions(clients_selection: pd.DataFrame) -> None:
    """Distributions des montants dépensés et de la récence."""
    gauche, droite = st.columns(2)
    with gauche, st.container(border=True):
        titre_carte("Distribution des montants dépensés")
        graphiques.afficher(
            graphiques.histogramme(
                clients_selection, config.COL_MONTANT_TOTAL, "Montant total (€)", nbins=30
            )
        )
    with droite, st.container(border=True):
        titre_carte("Distribution de la récence")
        recence = clients_selection.dropna(subset=[config.COL_RECENCE])
        graphiques.afficher(
            graphiques.histogramme(recence, config.COL_RECENCE, "Récence (jours)", nbins=30)
        )


def _preparer_tableau(clients_selection: pd.DataFrame) -> pd.DataFrame:
    """Construit le tableau des clients avec les modalités en français."""
    tableau = clients_selection[list(config.COLONNES_TABLEAU_CLIENTS)].copy()
    tableau[config.COL_GENRE] = tableau[config.COL_GENRE].map(config.LIBELLES_GENRES)
    tableau[config.COL_CANAL_PREFERE] = tableau[config.COL_CANAL_PREFERE].map(
        config.LIBELLES_CANAUX
    )
    return tableau


def _config_colonnes() -> dict[str, object]:
    """Configuration d'affichage (libellés et formats) du tableau."""
    configuration: dict[str, object] = {}
    for colonne in config.COLONNES_TABLEAU_CLIENTS:
        libelle = config.LIBELLES_COLONNES_CLIENTS[colonne]
        if colonne == config.COL_PART_ONLINE:
            configuration[colonne] = st.column_config.ProgressColumn(
                libelle, format="%.0f %%", min_value=0, max_value=100
            )
        elif colonne in _FORMATS_NUMERIQUES:
            configuration[colonne] = st.column_config.NumberColumn(
                libelle, format=_FORMATS_NUMERIQUES[colonne]
            )
        else:
            configuration[colonne] = st.column_config.TextColumn(libelle)
    return configuration


def _filtrer_recherche(tableau: pd.DataFrame, recherche: str) -> pd.DataFrame:
    """Filtre le tableau par ville ou identifiant (recherche libre)."""
    if not recherche:
        return tableau
    par_ville = tableau[config.COL_VILLE].str.contains(recherche, case=False, na=False)
    par_id = tableau[config.COL_CLIENT].astype(str).str.contains(recherche, na=False)
    return tableau[par_ville | par_id]


def _tableau_clients(clients_selection: pd.DataFrame) -> None:
    """Tableau filtrable des clients, avec recherche et export CSV."""
    with st.container(border=True):
        titre_carte("Détail des clients")
        recherche = st.text_input(
            "Rechercher",
            placeholder="Ville ou identifiant",
            label_visibility="collapsed",
        )
        tableau = _filtrer_recherche(_preparer_tableau(clients_selection), recherche)
        st.caption(f"{format_entier(len(tableau))} clients affichés")
        st.dataframe(
            tableau,
            width="stretch",
            hide_index=True,
            column_config=_config_colonnes(),
        )
        export = tableau.rename(columns=config.LIBELLES_COLONNES_CLIENTS)
        st.download_button(
            "Exporter en CSV",
            data=export.to_csv(index=False).encode("utf-8-sig"),
            file_name="clients_selection.csv",
            mime="text/csv",
            icon=":material/download:",
            type="primary",
        )


def afficher() -> None:
    """Rend la page Clients."""
    entete_page(
        "Clients",
        "Analyse de la base clients sur la sélection : démographie, comportement et export.",
    )
    filtres: Filtres = st.session_state["filtres"]
    ventes_filtrees = calculs.appliquer_filtres(charger_ventes(), filtres)
    clients_selection = calculs.clients_de_selection(charger_clients(), ventes_filtrees)

    if clients_selection.empty:
        st.info("Aucun client ne correspond aux filtres sélectionnés.")
        return

    _cartes_kpi(clients_selection)
    st.write("")
    _graphiques_demographie(clients_selection)
    _graphiques_distributions(clients_selection)
    _tableau_clients(clients_selection)


afficher()
