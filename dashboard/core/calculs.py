"""Calculs métier : fonctions pures pandas, sans dépendance à Streamlit.

Ces fonctions ne modifient jamais leurs entrées et ne touchent pas au disque.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from core import config
from core.config import Filtres


def appliquer_filtres(ventes: pd.DataFrame, filtres: Filtres) -> pd.DataFrame:
    """Applique les filtres globaux aux ventes.

    Args:
        ventes: ventes fusionnées (colonne Date en datetime).
        filtres: sélection courante.

    Returns:
        Une copie filtrée des ventes.
    """
    masque = ventes[config.COL_DATE].between(
        pd.Timestamp(filtres.date_debut), pd.Timestamp(filtres.date_fin)
    )
    for colonne, valeurs in (
        (config.COL_CANAL, filtres.canaux),
        (config.COL_CATEGORIE, filtres.categories),
        (config.COL_VILLE, filtres.villes),
        (config.COL_GENRE, filtres.genres),
    ):
        if valeurs:
            masque &= ventes[colonne].isin(valeurs)
    return ventes.loc[masque].copy()


def periode_precedente(filtres: Filtres) -> Filtres:
    """Retourne les filtres décalés sur la période précédente de même durée."""
    duree = filtres.date_fin - filtres.date_debut
    fin = filtres.date_debut - timedelta(days=1)
    debut = fin - duree
    return Filtres(
        date_debut=debut,
        date_fin=fin,
        canaux=filtres.canaux,
        categories=filtres.categories,
        villes=filtres.villes,
        genres=filtres.genres,
    )


def kpis_principaux(ventes_filtrees: pd.DataFrame) -> dict[str, float]:
    """Calcule les KPI de base sur un sous-ensemble de ventes.

    Returns:
        chiffre_affaires, nb_ventes, panier_moyen, clients_actifs.
    """
    nb_ventes = int(len(ventes_filtrees))
    chiffre_affaires = float(ventes_filtrees[config.COL_MONTANT_VENTE].sum())
    panier_moyen = chiffre_affaires / nb_ventes if nb_ventes else 0.0
    clients_actifs = int(ventes_filtrees[config.COL_CLIENT].nunique())
    return {
        "chiffre_affaires": chiffre_affaires,
        "nb_ventes": nb_ventes,
        "panier_moyen": panier_moyen,
        "clients_actifs": clients_actifs,
    }


def variation_pct(courant: float, precedent: float) -> float | None:
    """Retourne la variation en % entre deux valeurs, ou None si non pertinent."""
    if precedent <= 0:
        return None
    return (courant - precedent) / precedent * 100.0


def part_clients_inactifs(
    clients: pd.DataFrame,
    identifiants: pd.Series | pd.Index,
    seuil_jours: int = config.SEUIL_INACTIF_JOURS,
) -> tuple[float, int, int]:
    """Calcule la part de clients inactifs depuis plus de `seuil_jours`.

    Ne considère que les clients ayant au moins un achat (récence renseignée)
    et présents dans `identifiants`.

    Returns:
        (part en %, nombre d'inactifs, nombre de clients acheteurs considérés).
    """
    acheteurs = clients[
        clients[config.COL_CLIENT].isin(identifiants) & clients[config.COL_RECENCE].notna()
    ]
    total = int(len(acheteurs))
    if total == 0:
        return 0.0, 0, 0
    nb_inactifs = int((acheteurs[config.COL_RECENCE] > seuil_jours).sum())
    return nb_inactifs / total * 100.0, nb_inactifs, total


def ca_mensuel(ventes_filtrees: pd.DataFrame) -> pd.DataFrame:
    """Chiffre d'affaires agrégé par mois.

    Returns:
        DataFrame trié avec les colonnes Mois (datetime) et CA (float).
    """
    if ventes_filtrees.empty:
        return pd.DataFrame({"Mois": pd.Series(dtype="datetime64[ns]"), "CA": []})
    mensuel = (
        ventes_filtrees.groupby(ventes_filtrees[config.COL_DATE].dt.to_period("M"))[
            config.COL_MONTANT_VENTE
        ]
        .sum()
        .reset_index()
    )
    mensuel[config.COL_DATE] = mensuel[config.COL_DATE].dt.to_timestamp()
    return mensuel.rename(columns={config.COL_DATE: "Mois", config.COL_MONTANT_VENTE: "CA"})


def ca_mensuel_compare(ventes: pd.DataFrame, filtres: Filtres) -> pd.DataFrame:
    """Chiffre d'affaires mensuel de la période courante et de la précédente.

    Les deux séries sont alignées par rang de mois (1er mois de chaque période,
    etc.), afin d'être comparées sur un même axe.

    Returns:
        DataFrame avec les colonnes Label (mois courant), Courant et Precedent
        (Precedent vaut NaN si aucune période précédente comparable n'existe).
    """
    courant = ca_mensuel(appliquer_filtres(ventes, filtres)).reset_index(drop=True)
    precedent = ca_mensuel(appliquer_filtres(ventes, periode_precedente(filtres))).reset_index(
        drop=True
    )
    resultat = pd.DataFrame(
        {
            "Label": courant["Mois"].dt.strftime("%m/%Y"),
            "Courant": courant["CA"],
        }
    )
    serie_precedente = precedent["CA"].reindex(range(len(resultat)))
    resultat["Precedent"] = serie_precedente.to_numpy()
    return resultat


def ca_par_dimension(ventes_filtrees: pd.DataFrame, colonne: str) -> pd.DataFrame:
    """Chiffre d'affaires par modalité d'une dimension, trié décroissant.

    Returns:
        DataFrame avec les colonnes `colonne` et CA.
    """
    agrege = (
        ventes_filtrees.groupby(colonne)[config.COL_MONTANT_VENTE]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={config.COL_MONTANT_VENTE: "CA"})
    )
    return agrege


def top_produits(
    ventes_filtrees: pd.DataFrame, nombre: int = config.TOP_PRODUITS_DEFAUT
) -> pd.DataFrame:
    """Top des produits par chiffre d'affaires.

    Returns:
        DataFrame trié croissant (adapté à un graphique en barres horizontales),
        avec les colonnes Product_Name et CA.
    """
    agrege = ca_par_dimension(ventes_filtrees, config.COL_PRODUIT)
    return agrege.head(nombre).sort_values("CA")


def bornes_dates(ventes: pd.DataFrame) -> tuple[date, date]:
    """Retourne la première et la dernière date de vente."""
    return (
        ventes[config.COL_DATE].min().date(),
        ventes[config.COL_DATE].max().date(),
    )


def modalites(ventes: pd.DataFrame, colonne: str) -> list[str]:
    """Retourne les modalités distinctes d'une colonne, triées."""
    return sorted(ventes[colonne].dropna().unique().tolist())


def clients_de_selection(clients: pd.DataFrame, ventes_filtrees: pd.DataFrame) -> pd.DataFrame:
    """Restreint les clients à ceux présents dans les ventes filtrées.

    Les agrégats (RFM, panier, parts) restent ceux précalculés par M2 ; seule la
    liste des clients affichés dépend des filtres. Les clients sans achat, absents
    des ventes, ne figurent donc jamais ici.
    """
    identifiants = ventes_filtrees[config.COL_CLIENT].unique()
    return clients[clients[config.COL_CLIENT].isin(identifiants)].copy()
