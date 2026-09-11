"""Carte KPI : valeur, pastille d'icône colorée et tendance fléchée."""

from __future__ import annotations

import streamlit as st

from core.formats import format_variation

# Couleurs d'accent des pastilles, reprises de la palette du logo (icône, fond).
_ACCENTS: dict[str, tuple[str, str]] = {
    "violet": ("#6F3BFD", "#F1ECFE"),
    "rose": ("#E11D48", "#FFE4EC"),
    "ambre": ("#B45309", "#FEF3D6"),
    "turquoise": ("#0F766E", "#D6F7EF"),
    "neutre": ("#475569", "#F1F5F9"),
}


def _pied(variation: float | None, note: str | None) -> str:
    """Construit le HTML du pied de carte (tendance fléchée, note ou vide)."""
    if variation is not None:
        positif = variation >= 0
        fleche = "trending_up" if positif else "trending_down"
        classe = "kpi-trend-pos" if positif else "kpi-trend-neg"
        return (
            f'<span class="kpi-trend {classe}">'
            f'<span class="material-symbols-outlined">{fleche}</span>'
            f"{format_variation(variation)}</span>"
            '<span class="kpi-foot-note">vs période précédente</span>'
        )
    if note is not None:
        return f'<span class="kpi-foot-note">{note}</span>'
    return '<span class="kpi-foot-note">&nbsp;</span>'


def carte_kpi(
    libelle: str,
    valeur: str,
    icone: str,
    variation: float | None = None,
    note: str | None = None,
    accent: str = "neutre",
) -> None:
    """Affiche une carte KPI (valeur, pastille d'icône, tendance).

    Args:
        libelle: intitulé du KPI.
        valeur: valeur déjà formatée (chaîne).
        icone: nom d'icône Material Symbols (ex. "payments").
        variation: variation en % vs période précédente (None si non pertinent).
        note: texte secondaire affiché à défaut de variation.
        accent: clé de couleur de la pastille (violet, rose, ambre, turquoise, neutre).
    """
    couleur, tint = _ACCENTS.get(accent, _ACCENTS["neutre"])
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-top">'
        f'<div class="kpi-card-value">{valeur}</div>'
        f'<span class="kpi-chip" style="background:{tint};color:{couleur}">'
        f'<span class="material-symbols-outlined">{icone}</span></span>'
        f"</div>"
        f'<div class="kpi-card-label">{libelle}</div>'
        f'<div class="kpi-card-foot">{_pied(variation, note)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )
