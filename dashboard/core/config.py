"""Constantes centralisées du dashboard : chemins, colonnes, seuils, libellés.

Aucune valeur « magique » ne doit apparaître ailleurs dans le code : tout est
défini ici une seule fois.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# --- Chemins (construits avec pathlib depuis la racine du dépôt) -------------
# config.py -> core -> dashboard -> racine du dépôt.
RACINE_DEPOT: Path = Path(__file__).resolve().parents[2]
DOSSIER_DASHBOARD: Path = RACINE_DEPOT / "dashboard"
DOSSIER_PROCESSED: Path = RACINE_DEPOT / "data" / "processed"
DOSSIER_RESULTS: Path = RACINE_DEPOT / "data" / "results"

FICHIER_VENTES: Path = DOSSIER_PROCESSED / "ventes_fusionnees.csv"
FICHIER_CLIENTS: Path = DOSSIER_PROCESSED / "clients_agreges.csv"
FICHIER_MARKETING: Path = DOSSIER_PROCESSED / "marketing_nettoye.csv"

# --- Paramètres métier -------------------------------------------------------
# Date de référence du jeu étendu (dernière vente), utilisée pour la récence.
DATE_REFERENCE: date = date(2024, 12, 31)
SEUIL_INACTIF_JOURS: int = 90

# --- Noms de colonnes --------------------------------------------------------
COL_DATE = "Date"
COL_CLIENT = "Customer_ID"
COL_AGE = "Age"
COL_GENRE = "Gender"
COL_VILLE = "Location"
COL_CATEGORIE = "Category"
COL_PRODUIT = "Product_Name"
COL_CANAL = "Channel"
COL_MONTANT_VENTE = "Sale_Price"
COL_QUANTITE = "Quantity"

COL_NB_ACHATS = "Nb_Achats"
COL_MONTANT_TOTAL = "Montant_Total"
COL_PANIER_MOYEN = "Panier_Moyen"
COL_RECENCE = "Recence_Jours"
COL_CANAL_PREFERE = "Canal_Prefere"
COL_PART_ONLINE = "Part_Online"

# --- Ordres et modalités de référence ---------------------------------------
CANAUX_VENTES: tuple[str, ...] = ("Online", "In-Store")
CATEGORIES: tuple[str, ...] = ("Clothing", "Footwear", "Outerwear", "Accessories")

# Libellés français des modalités pour l'affichage.
LIBELLES_CANAUX: dict[str, str] = {"Online": "En ligne", "In-Store": "En magasin"}
LIBELLES_GENRES: dict[str, str] = {"Female": "Femme", "Male": "Homme"}

TOP_PRODUITS_DEFAUT: int = 10

# Colonnes affichées dans le tableau des clients (dans l'ordre) et leurs libellés.
COLONNES_TABLEAU_CLIENTS: tuple[str, ...] = (
    COL_CLIENT,
    COL_AGE,
    COL_GENRE,
    COL_VILLE,
    COL_NB_ACHATS,
    COL_MONTANT_TOTAL,
    COL_PANIER_MOYEN,
    COL_RECENCE,
    COL_CANAL_PREFERE,
    COL_PART_ONLINE,
)
LIBELLES_COLONNES_CLIENTS: dict[str, str] = {
    COL_CLIENT: "Identifiant",
    COL_AGE: "Âge",
    COL_GENRE: "Genre",
    COL_VILLE: "Ville",
    COL_NB_ACHATS: "Nombre d'achats",
    COL_MONTANT_TOTAL: "Montant total",
    COL_PANIER_MOYEN: "Panier moyen",
    COL_PART_ONLINE: "Achats en ligne",
    COL_RECENCE: "Récence (jours)",
    COL_CANAL_PREFERE: "Canal préféré",
}

# --- Fichiers livrés plus tard (data/results/) -------------------------------


@dataclass(frozen=True)
class FichierResultat:
    """Spécification d'un fichier attendu dans data/results/."""

    cle: str
    chemin: Path
    responsable: str
    description: str
    colonnes: tuple[str, ...]


RESULTAT_SEGMENTS = FichierResultat(
    cle="segments",
    chemin=DOSSIER_RESULTS / "segments.csv",
    responsable="module M3 (segmentation)",
    description="Segments de clients issus du K-means.",
    colonnes=("Customer_ID", "Segment_ID", "Segment_Nom"),
)

RESULTAT_CAMPAGNES = FichierResultat(
    cle="kpis_campagnes",
    chemin=DOSSIER_RESULTS / "kpis_campagnes.csv",
    responsable="module M5 (analyse des campagnes)",
    description="Indicateurs de performance par campagne.",
    colonnes=(
        "Campaign_ID",
        "Channel",
        "Budget",
        "Impressions",
        "Clicks",
        "Conversions",
        "CTR",
        "Taux_Conversion",
        "CPC",
        "CPA",
        "ROI",
    ),
)

RESULTAT_PREDICTIONS = FichierResultat(
    cle="predictions_churn",
    chemin=DOSSIER_RESULTS / "predictions_churn.csv",
    responsable="module M6 (prédiction du churn)",
    description="Probabilité de churn par client (CLV optionnelle).",
    colonnes=("Customer_ID", "Proba_Churn", "CLV"),
)

# --- État des filtres globaux ------------------------------------------------


@dataclass(frozen=True)
class Filtres:
    """Sélection courante des filtres globaux, partagée entre les pages.

    Les bornes de dates sont incluses. Les tuples vides signifient « aucun
    filtre » (toutes les modalités sont conservées).
    """

    date_debut: date
    date_fin: date
    canaux: tuple[str, ...] = field(default_factory=tuple)
    categories: tuple[str, ...] = field(default_factory=tuple)
    villes: tuple[str, ...] = field(default_factory=tuple)
    genres: tuple[str, ...] = field(default_factory=tuple)
