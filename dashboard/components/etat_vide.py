"""État vide propre pour les pages dont le fichier de résultats est absent."""

from __future__ import annotations

import streamlit as st

from core import config
from core.config import FichierResultat


def afficher_etat_vide(specification: FichierResultat) -> None:
    """Affiche un message clair indiquant le fichier attendu et son responsable.

    Args:
        specification: fichier de data/results/ attendu pour activer la page.
    """
    chemin_relatif = specification.chemin.relative_to(config.RACINE_DEPOT)
    colonnes = ", ".join(f"`{colonne}`" for colonne in specification.colonnes)
    with st.container(border=True):
        st.markdown(
            ':material/schedule: <span class="card-title">Données en attente de livraison</span>',
            unsafe_allow_html=True,
        )
        st.write(
            "Cette page s'activera automatiquement dès que le fichier suivant "
            "sera présent dans le dépôt."
        )
        st.markdown(
            f"**Fichier attendu :** `{chemin_relatif}`  \n"
            f"**Responsable :** {specification.responsable}  \n"
            f"**Contenu :** {specification.description}"
        )
        st.markdown(f"**Colonnes attendues :** {colonnes}")
