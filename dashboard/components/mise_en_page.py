"""Éléments de mise en page communs : en-têtes de page et titres de carte."""

from __future__ import annotations

import streamlit as st


def entete_page(titre: str, sous_titre: str) -> None:
    """Affiche l'en-tête d'une page (titre + sous-titre)."""
    st.markdown(f'<p class="page-titre">{titre}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="page-sous-titre">{sous_titre}</p>', unsafe_allow_html=True)
    st.write("")


def titre_carte(texte: str) -> None:
    """Affiche le titre d'une carte (graphique ou tableau)."""
    st.markdown(f'<div class="card-title">{texte}</div>', unsafe_allow_html=True)
