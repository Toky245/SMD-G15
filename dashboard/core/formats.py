"""Formatage des nombres pour l'affichage en français (séparateur d'espace)."""

from __future__ import annotations

_ESPACE_FINE = " "


def _grouper_milliers(nombre: float, decimales: int) -> str:
    """Formate un nombre avec l'espace fine comme séparateur de milliers."""
    texte = f"{nombre:,.{decimales}f}"
    texte = texte.replace(",", " ").replace(".", ",")
    return texte.replace(" ", _ESPACE_FINE)


def format_entier(valeur: float) -> str:
    """Retourne un entier avec séparateur de milliers (ex. 5 337)."""
    return _grouper_milliers(round(valeur), 0)


def format_euro(valeur: float, decimales: int = 0) -> str:
    """Retourne un montant en euros (ex. 484 673 €)."""
    return f"{_grouper_milliers(valeur, decimales)}{_ESPACE_FINE}€"


def format_pourcentage(valeur: float, decimales: int = 1) -> str:
    """Retourne un pourcentage (ex. 12,3 %)."""
    return f"{_grouper_milliers(valeur, decimales)}{_ESPACE_FINE}%"


def format_variation(valeur: float, decimales: int = 1) -> str:
    """Retourne une variation signée en pourcentage (ex. +12,3 %)."""
    signe = "+" if valeur >= 0 else "-"
    return f"{signe}{format_pourcentage(abs(valeur), decimales)}"
