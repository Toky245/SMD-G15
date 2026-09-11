"""Page 1 — Vue d'ensemble : KPI, CA mensuel, ventilations et top produits."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import graphiques
from components.cartes import carte_kpi
from components.mise_en_page import entete_page, titre_carte
from core import calculs, config
from core.config import Filtres
from core.formats import format_entier, format_euro, format_pourcentage
from data.loaders import charger_clients, charger_ventes


def _cartes_kpi(filtres: Filtres, ventes_filtrees: pd.DataFrame, clients: pd.DataFrame) -> None:
    """Affiche la rangée de cartes KPI avec variations vs période précédente."""
    kpis = calculs.kpis_principaux(ventes_filtrees)
    precedents = calculs.kpis_principaux(
        calculs.appliquer_filtres(charger_ventes(), calculs.periode_precedente(filtres))
    )

    def variation(cle: str) -> float | None:
        return calculs.variation_pct(kpis[cle], precedents[cle])

    part, nb_inactifs, total = calculs.part_clients_inactifs(
        clients, ventes_filtrees[config.COL_CLIENT].unique()
    )

    colonnes = st.columns(5)
    with colonnes[0]:
        carte_kpi(
            "Chiffre d'affaires",
            format_euro(kpis["chiffre_affaires"]),
            "payments",
            variation("chiffre_affaires"),
            accent="violet",
        )
    with colonnes[1]:
        carte_kpi(
            "Nombre de ventes",
            format_entier(kpis["nb_ventes"]),
            "receipt_long",
            variation("nb_ventes"),
            accent="turquoise",
        )
    with colonnes[2]:
        carte_kpi(
            "Panier moyen",
            format_euro(kpis["panier_moyen"], decimales=2),
            "shopping_cart",
            variation("panier_moyen"),
            accent="ambre",
        )
    with colonnes[3]:
        carte_kpi(
            "Clients actifs",
            format_entier(kpis["clients_actifs"]),
            "group",
            variation("clients_actifs"),
            accent="rose",
        )
    with colonnes[4]:
        carte_kpi(
            "Clients inactifs (> 90 j)",
            format_pourcentage(part),
            "person_off",
            note=f"{format_entier(nb_inactifs)} sur {format_entier(total)} acheteurs",
            accent="neutre",
        )


def _graphique_ca_mensuel(filtres: Filtres) -> None:
    """Courbe du CA mensuel avec comparaison à la période précédente."""
    with st.container(border=True):
        titre_carte("Chiffre d'affaires mensuel")
        donnees = calculs.ca_mensuel_compare(charger_ventes(), filtres)
        graphiques.afficher(graphiques.graphique_ca_mensuel_compare(donnees))


def _graphiques_ventilations(ventes_filtrees: pd.DataFrame) -> None:
    """Ventilations du CA par catégorie et par canal, côte à côte."""
    gauche, droite = st.columns(2)
    with gauche, st.container(border=True):
        titre_carte("Chiffre d'affaires par catégorie")
        par_categorie = calculs.ca_par_dimension(ventes_filtrees, config.COL_CATEGORIE)
        graphiques.afficher(
            graphiques.graphique_barres_categorie(par_categorie, config.COL_CATEGORIE, "CA")
        )
    with droite, st.container(border=True):
        titre_carte("Chiffre d'affaires par canal")
        par_canal = calculs.ca_par_dimension(ventes_filtrees, config.COL_CANAL)
        par_canal["Canal"] = par_canal[config.COL_CANAL].map(config.LIBELLES_CANAUX)
        graphiques.afficher(graphiques.graphique_barres_categorie(par_canal, "Canal", "CA"))


def _graphique_top_produits(ventes_filtrees: pd.DataFrame) -> None:
    """Top 10 des produits par chiffre d'affaires."""
    with st.container(border=True):
        titre_carte("Top 10 des produits")
        top = calculs.top_produits(ventes_filtrees)
        graphiques.afficher(graphiques.barres_progression(top, config.COL_PRODUIT, "CA"))


def afficher() -> None:
    """Rend la page Vue d'ensemble."""
    entete_page(
        "Vue d'ensemble",
        "Indicateurs clés de l'activité commerciale sur la période sélectionnée.",
    )
    filtres: Filtres = st.session_state["filtres"]
    ventes_filtrees = calculs.appliquer_filtres(charger_ventes(), filtres)

    if ventes_filtrees.empty:
        st.info("Aucune vente ne correspond aux filtres sélectionnés.")
        return

    _cartes_kpi(filtres, ventes_filtrees, charger_clients())
    st.write("")
    _graphique_ca_mensuel(filtres)
    _graphiques_ventilations(ventes_filtrees)
    _graphique_top_produits(ventes_filtrees)


afficher()
