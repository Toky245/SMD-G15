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


def filtrer_clients(clients: pd.DataFrame, filtres: Filtres) -> pd.DataFrame:
    """Filtre les clients par ville et genre (filtres pertinents au niveau client)."""
    resultat = clients
    if filtres.villes:
        resultat = resultat[resultat[config.COL_VILLE].isin(filtres.villes)]
    if filtres.genres:
        resultat = resultat[resultat[config.COL_GENRE].isin(filtres.genres)]
    return resultat.copy()


# --- Campagnes ---------------------------------------------------------------


def kpis_campagnes_par_canal(kpis: pd.DataFrame) -> pd.DataFrame:
    """Recalcule les indicateurs par canal à partir des totaux (pas de moyenne de ratios).

    CTR = Σclics/Σimpressions, Taux_Conversion = Σconversions/Σclics,
    CPC = Σbudget/Σclics, CPA = Σbudget/Σconversions,
    ROI = (Σrevenu − Σbudget)/Σbudget. CTR, Taux_Conversion et ROI sont en %.
    """
    agrege = (
        kpis.groupby(config.COL_CANAL)
        .agg(
            Campagnes=(config.COL_CAMPAGNE, "count"),
            Budget=(config.COL_BUDGET, "sum"),
            Impressions=(config.COL_IMPRESSIONS, "sum"),
            Clics=(config.COL_CLICS, "sum"),
            Conversions=(config.COL_CONVERSIONS, "sum"),
            Revenu=(config.COL_REVENU, "sum"),
        )
        .reset_index()
    )
    agrege["CTR"] = agrege["Clics"] / agrege["Impressions"] * 100
    agrege["Taux_Conversion"] = agrege["Conversions"] / agrege["Clics"] * 100
    agrege["CPC"] = agrege["Budget"] / agrege["Clics"]
    agrege["CPA"] = agrege["Budget"] / agrege["Conversions"]
    agrege["ROI"] = (agrege["Revenu"] - agrege["Budget"]) / agrege["Budget"] * 100
    return agrege


def kpis_campagnes_global(kpis: pd.DataFrame) -> dict[str, float]:
    """Indicateurs globaux recalculés à partir des totaux de toutes les campagnes."""
    budget = float(kpis[config.COL_BUDGET].sum())
    impressions = float(kpis[config.COL_IMPRESSIONS].sum())
    clics = float(kpis[config.COL_CLICS].sum())
    conversions = float(kpis[config.COL_CONVERSIONS].sum())
    revenu = float(kpis[config.COL_REVENU].sum())
    return {
        "budget": budget,
        "impressions": impressions,
        "clics": clics,
        "conversions": conversions,
        "revenu": revenu,
        "ctr": clics / impressions * 100 if impressions else 0.0,
        "taux_conversion": conversions / clics * 100 if clics else 0.0,
        "cpc": budget / clics if clics else 0.0,
        "cpa": budget / conversions if conversions else 0.0,
        "roi": (revenu - budget) / budget * 100 if budget else 0.0,
    }


# --- Segments ----------------------------------------------------------------


def _fusion_segments(segments: pd.DataFrame, clients: pd.DataFrame) -> pd.DataFrame:
    """Joint segments et clients (jointure interne : respecte le filtrage clients)."""
    return segments.merge(clients, on=config.COL_CLIENT, how="inner")


def profil_segments(segments: pd.DataFrame, clients: pd.DataFrame) -> pd.DataFrame:
    """Profil moyen par segment ; comportement masqué pour le segment sans achat.

    Les clients sans achat (Segment_ID = -1) restent comptés, mais leurs moyennes
    de panier, récence et fréquence sont laissées vides (sans signification).
    """
    fusion = _fusion_segments(segments, clients)
    profil = (
        fusion.groupby([config.COL_SEGMENT_ID, config.COL_SEGMENT_NOM])
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
    masque_sans_achat = profil[config.COL_SEGMENT_ID] == config.SEGMENT_SANS_ACHAT
    for colonne in ("Panier_moyen", "Recence_moyenne", "Achats_moyens"):
        profil[colonne] = profil[colonne].astype("object")
        profil.loc[masque_sans_achat, colonne] = None
    return profil.sort_values(config.COL_SEGMENT_ID).drop(columns=config.COL_SEGMENT_ID)


def nombre_segments_reels(segments: pd.DataFrame) -> int:
    """Nombre de segments réels (hors pseudo-segment des clients sans achat)."""
    reels = segments[segments[config.COL_SEGMENT_ID] != config.SEGMENT_SANS_ACHAT]
    return int(reels[config.COL_SEGMENT_ID].nunique())


def repartition_segments(segments: pd.DataFrame, clients: pd.DataFrame) -> pd.DataFrame:
    """Nombre de clients par segment (tous segments, y compris sans achat)."""
    fusion = _fusion_segments(segments, clients)
    return (
        fusion.groupby(config.COL_SEGMENT_NOM)[config.COL_CLIENT]
        .count()
        .reset_index(name="Clients")
        .sort_values("Clients")
    )


def _segments_reels(segments: pd.DataFrame, clients: pd.DataFrame) -> pd.DataFrame:
    """Fusion restreinte aux segments réels (dépense pertinente)."""
    fusion = _fusion_segments(segments, clients)
    return fusion[fusion[config.COL_SEGMENT_ID] != config.SEGMENT_SANS_ACHAT]


def ca_par_segment(segments: pd.DataFrame, clients: pd.DataFrame) -> pd.DataFrame:
    """Chiffre d'affaires (Montant_Total) par segment réel et part en %."""
    reels = _segments_reels(segments, clients)
    resultat = (
        reels.groupby(config.COL_SEGMENT_NOM)[config.COL_MONTANT_TOTAL]
        .sum()
        .reset_index(name="CA")
        .sort_values("CA")
    )
    total = resultat["CA"].sum()
    resultat["Part"] = resultat["CA"] / total * 100 if total else 0.0
    return resultat


def composition_par_segment(segments: pd.DataFrame, clients: pd.DataFrame) -> pd.DataFrame:
    """Composition moyenne des dépenses par catégorie et par segment réel (format long)."""
    reels = _segments_reels(segments, clients)
    colonnes = list(config.PARTS_CATEGORIES.values())
    moyennes = reels.groupby(config.COL_SEGMENT_NOM)[colonnes].mean().reset_index()
    long = moyennes.melt(id_vars=config.COL_SEGMENT_NOM, var_name="ColPart", value_name="Part")
    inverse = {col: cat for cat, col in config.PARTS_CATEGORIES.items()}
    long["Categorie"] = long["ColPart"].map(inverse)
    return long.drop(columns="ColPart")


# --- Prédictions -------------------------------------------------------------


def predictions_avec_segment(
    predictions: pd.DataFrame, segments: pd.DataFrame | None
) -> pd.DataFrame:
    """Ajoute le nom de segment aux prédictions (si la segmentation est disponible)."""
    if segments is None:
        resultat = predictions.copy()
        resultat[config.COL_SEGMENT_NOM] = "Sans segment"
        return resultat
    return predictions.merge(
        segments[[config.COL_CLIENT, config.COL_SEGMENT_NOM]],
        on=config.COL_CLIENT,
        how="left",
    )


def mesures_risque(predictions: pd.DataFrame, seuil: float) -> dict[str, float]:
    """Mesures de churn au seuil donné (sur les seuls clients ayant une prédiction)."""
    total = int(len(predictions))
    a_risque = predictions[predictions[config.COL_PROBA_CHURN] >= seuil]
    nb_risque = int(len(a_risque))
    clv_risque = float(a_risque[config.COL_CLV].sum()) if config.COL_CLV in predictions else 0.0
    return {
        "total": total,
        "nb_risque": nb_risque,
        "part": nb_risque / total * 100 if total else 0.0,
        "clv_risque": clv_risque,
    }


def risque_par_segment(predictions_segment: pd.DataFrame, seuil: float) -> pd.DataFrame:
    """Par segment : nombre de clients à risque et somme de leur CLV, au seuil donné."""
    a_risque = predictions_segment[predictions_segment[config.COL_PROBA_CHURN] >= seuil]
    return (
        a_risque.groupby(config.COL_SEGMENT_NOM)
        .agg(Clients=(config.COL_CLIENT, "count"), CLV=(config.COL_CLV, "sum"))
        .reset_index()
        .sort_values("CLV")
    )
