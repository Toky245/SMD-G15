"""Page 4 — Campagnes : KPI recalculés par canal, graphiques et détail.

Cette page gère ses propres filtres (période sur Start_Date, canal campagne) :
les filtres globaux ne s'appliquent pas, les canaux campagne n'étant pas les
canaux de vente.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from components import graphiques
from components.cartes import carte_kpi
from components.etat_vide import afficher_etat_vide
from components.mise_en_page import entete_page, titre_carte
from core import calculs, config
from core.formats import format_entier, format_nombre, format_pourcentage
from core.theme import COULEUR_PRIMAIRE, PALETTE_CATEGORIELLE
from data.loaders import charger_resultat

_COULEUR_REVENU = PALETTE_CATEGORIELLE[3]


def _filtres_campagnes(kpis: pd.DataFrame) -> tuple[date, date, tuple[str, ...]]:
    """Filtres propres à la page : période sur Start_Date et canal campagne."""
    debuts = pd.to_datetime(kpis[config.COL_DEBUT_CAMPAGNE])
    mini, maxi = debuts.min().date(), debuts.max().date()
    st.sidebar.divider()
    st.sidebar.markdown(
        '<div class="sidebar-section">Filtres campagnes</div>', unsafe_allow_html=True
    )
    periode = st.sidebar.date_input(
        "Période (début de campagne)",
        value=(mini, maxi),
        min_value=mini,
        max_value=maxi,
        format="DD/MM/YYYY",
        key="c_periode",
    )
    if isinstance(periode, (list, tuple)) and len(periode) == 2:
        debut, fin = periode[0], periode[1]
    else:
        debut, fin = mini, maxi
    canaux = tuple(
        st.sidebar.multiselect(
            "Canal campagne",
            options=list(config.CANAUX_CAMPAGNES),
            placeholder="Tous",
            key="c_canaux",
        )
    )
    return debut, fin, canaux


def _appliquer_filtres(
    kpis: pd.DataFrame, debut: date, fin: date, canaux: tuple[str, ...]
) -> pd.DataFrame:
    """Restreint les campagnes à la période (Start_Date) et aux canaux choisis."""
    debuts = pd.to_datetime(kpis[config.COL_DEBUT_CAMPAGNE])
    masque = debuts.between(pd.Timestamp(debut), pd.Timestamp(fin))
    if canaux:
        masque &= kpis[config.COL_CANAL].isin(canaux)
    return kpis[masque].copy()


def _cartes_kpi(mesures: dict[str, float]) -> None:
    """Cartes KPI globales recalculées depuis les totaux (sans devise)."""
    colonnes = st.columns(4)
    with colonnes[0]:
        carte_kpi(
            "Budget total", format_nombre(mesures["budget"]), "account_balance", accent="violet"
        )
    with colonnes[1]:
        carte_kpi(
            "Revenu estimé", format_nombre(mesures["revenu"]), "trending_up", accent="turquoise"
        )
    with colonnes[2]:
        carte_kpi(
            "Conversions", format_entier(mesures["conversions"]), "shopping_bag", accent="ambre"
        )
    with colonnes[3]:
        carte_kpi("ROI global", format_pourcentage(mesures["roi"]), "percent", accent="rose")


def _config_canal() -> dict[str, object]:
    """Configuration d'affichage du tableau par canal (%, sans devise)."""
    return {
        config.COL_CANAL: st.column_config.TextColumn("Canal"),
        "Campagnes": st.column_config.NumberColumn("Campagnes", format="%d"),
        "Budget": st.column_config.NumberColumn("Budget", format="%d"),
        "Impressions": st.column_config.NumberColumn("Impressions", format="%d"),
        "Clics": st.column_config.NumberColumn("Clics", format="%d"),
        "Conversions": st.column_config.NumberColumn("Conversions", format="%d"),
        "Revenu": st.column_config.NumberColumn("Revenu estimé", format="%d"),
        "CTR": st.column_config.NumberColumn("CTR", format="%.2f %%"),
        "Taux_Conversion": st.column_config.NumberColumn("Taux conversion", format="%.2f %%"),
        "CPC": st.column_config.NumberColumn("CPC", format="%.2f"),
        "CPA": st.column_config.NumberColumn("CPA", format="%.2f"),
        "ROI": st.column_config.NumberColumn("ROI", format="%.2f %%"),
    }


_ORDRE_CANAL = [
    config.COL_CANAL,
    "Campagnes",
    "Budget",
    "Impressions",
    "Clics",
    "Conversions",
    "Revenu",
    "CTR",
    "Taux_Conversion",
    "CPC",
    "CPA",
    "ROI",
]


def _graphiques(par_canal: pd.DataFrame) -> None:
    """Graphiques de performance par canal."""
    with st.container(border=True):
        titre_carte("ROI par canal (du plus rentable au moins rentable)")
        graphiques.afficher(
            graphiques.barres_valeur(
                par_canal.sort_values("ROI"),
                config.COL_CANAL,
                "ROI",
                orientation="h",
                suffixe="%",
                decimales=1,
            )
        )
    gauche, droite = st.columns(2)
    with gauche, st.container(border=True):
        titre_carte("Taux de clic (CTR) par canal")
        graphiques.afficher(
            graphiques.barres_valeur(par_canal, config.COL_CANAL, "CTR", suffixe="%", decimales=2)
        )
    with droite, st.container(border=True):
        titre_carte("Taux de conversion par canal")
        graphiques.afficher(
            graphiques.barres_valeur(
                par_canal, config.COL_CANAL, "Taux_Conversion", suffixe="%", decimales=2
            )
        )
    gauche2, droite2 = st.columns(2)
    with gauche2, st.container(border=True):
        titre_carte("Coût par clic (CPC) par canal")
        graphiques.afficher(
            graphiques.barres_valeur(par_canal, config.COL_CANAL, "CPC", decimales=2)
        )
    with droite2, st.container(border=True):
        titre_carte("Coût par acquisition (CPA) par canal")
        graphiques.afficher(
            graphiques.barres_valeur(par_canal, config.COL_CANAL, "CPA", decimales=2)
        )
    with st.container(border=True):
        titre_carte("Budget investi et revenu estimé par canal")
        graphiques.afficher(
            graphiques.barres_groupees(
                par_canal,
                config.COL_CANAL,
                [
                    ("Budget", "Budget", COULEUR_PRIMAIRE),
                    ("Revenu estimé", "Revenu", _COULEUR_REVENU),
                ],
            )
        )


def afficher() -> None:
    """Rend la page Campagnes ou son état vide."""
    entete_page("Campagnes", "Performance des campagnes par canal et par campagne.")
    kpis = charger_resultat(config.RESULTAT_CAMPAGNES.cle)
    if kpis is None:
        afficher_etat_vide(config.RESULTAT_CAMPAGNES)
        return

    debut, fin, canaux = _filtres_campagnes(kpis)
    selection = _appliquer_filtres(kpis, debut, fin, canaux)
    if selection.empty:
        st.info("Aucune campagne ne correspond aux filtres sélectionnés.")
        return

    st.caption(
        "Le revenu est estimé (Conversions × panier moyen de "
        f"{config.PANIER_MOYEN_REFERENCE:.2f}) ; les données ne contiennent pas le "
        "chiffre d'affaires réel des campagnes. Aucune devise n'est précisée."
    )
    _cartes_kpi(calculs.kpis_campagnes_global(selection))
    st.write("")

    par_canal = calculs.kpis_campagnes_par_canal(selection)
    with st.container(border=True):
        titre_carte("Indicateurs par canal (recalculés depuis les totaux)")
        st.dataframe(
            par_canal,
            width="stretch",
            hide_index=True,
            column_config=_config_canal(),
            column_order=_ORDRE_CANAL,
        )
    _graphiques(par_canal)


afficher()
