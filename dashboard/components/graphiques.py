"""Fabriques de graphiques Plotly appliquant le template commun.

Les figures héritent du template « smd » (fond transparent, grille légère,
Inter, séparateur de milliers), configuré dans core.theme.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.theme import (
    COULEUR_BORDURE,
    COULEUR_DANGER,
    COULEUR_PRIMAIRE,
    COULEUR_TEXTE_SECONDAIRE,
    PALETTE_CATEGORIELLE,
    TINT_NEUTRE,
    TINT_PRIMAIRE,
)

_HAUTEUR_DEFAUT = 330
_CONFIG_PLOTLY = {"displayModeBar": False}
_ETIQUETTE = {"color": COULEUR_TEXTE_SECONDAIRE, "size": 11}
# Couleur de la série de comparaison (période précédente) : corail sobre.
_COMPARAISON = "#FB7185"


def afficher(fig: go.Figure) -> None:
    """Affiche une figure sur toute la largeur, barre d'outils masquée."""
    st.plotly_chart(fig, width="stretch", config=_CONFIG_PLOTLY)


def _finaliser(fig: go.Figure, hauteur: int = _HAUTEUR_DEFAUT) -> go.Figure:
    """Applique la hauteur et masque la légende (souvent inutile)."""
    fig.update_layout(height=hauteur, showlegend=False)
    return fig


def graphique_ligne(donnees: pd.DataFrame, colonne_x: str, colonne_y: str) -> go.Figure:
    """Courbe temporelle lissée à série unique, avec aire douce."""
    fig = px.line(donnees, x=colonne_x, y=colonne_y, markers=True)
    fig.update_traces(
        line={"color": COULEUR_PRIMAIRE, "width": 2.5, "shape": "spline"},
        marker={"color": COULEUR_PRIMAIRE, "size": 7, "line": {"color": "#FFFFFF", "width": 1.5}},
        fill="tozeroy",
        fillcolor=TINT_PRIMAIRE,
        hovertemplate="%{x|%m/%Y} · %{y:,.0f} €<extra></extra>",
    )
    fig.update_xaxes(title_text="", tickformat="%m/%Y")
    fig.update_yaxes(title_text="")
    fig.update_layout(hovermode="x unified")
    return _finaliser(fig)


def graphique_ca_mensuel_compare(donnees: pd.DataFrame) -> go.Figure:
    """Courbe du CA mensuel : période courante (aire) et précédente (pointillé).

    Args:
        donnees: colonnes Label, Courant, Precedent (voir calculs.ca_mensuel_compare).
    """
    labels = donnees["Label"]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=labels,
            y=donnees["Courant"],
            name="Période courante",
            mode="lines",
            line={"color": COULEUR_PRIMAIRE, "width": 2.6, "shape": "spline"},
            fill="tozeroy",
            fillcolor=TINT_PRIMAIRE,
            hovertemplate="%{y:,.0f} €<extra>Courant</extra>",
        )
    )
    if donnees["Precedent"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=labels,
                y=donnees["Precedent"],
                name="Période précédente",
                mode="lines",
                line={"color": _COMPARAISON, "width": 2, "dash": "dash", "shape": "spline"},
                hovertemplate="%{y:,.0f} €<extra>Précédent</extra>",
            )
        )
    fig.update_xaxes(title_text="", type="category", showgrid=True, gridcolor=COULEUR_BORDURE)
    fig.update_yaxes(title_text="", ticksuffix=" €")
    fig.update_layout(height=_HAUTEUR_DEFAUT, showlegend=True, hovermode="x unified")
    return fig


def barres_progression(
    donnees: pd.DataFrame, colonne_categorie: str, colonne_valeur: str
) -> go.Figure:
    """Barres horizontales en pilule posées sur une piste (style « progression »)."""
    maxi = float(donnees[colonne_valeur].max() or 1)
    categories = donnees[colonne_categorie]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=categories,
            x=[maxi] * len(donnees),
            orientation="h",
            marker={"color": TINT_NEUTRE, "cornerradius": 20},
            hoverinfo="skip",
            showlegend=False,
            width=0.6,
        )
    )
    fig.add_trace(
        go.Bar(
            y=categories,
            x=donnees[colonne_valeur],
            orientation="h",
            marker={"color": COULEUR_PRIMAIRE, "cornerradius": 20},
            text=donnees[colonne_valeur],
            texttemplate="%{x:,.0f} €",
            textposition="outside",
            textfont=_ETIQUETTE,
            cliponaxis=False,
            hovertemplate="%{y} · %{x:,.0f} €<extra></extra>",
            width=0.6,
        )
    )
    fig.update_layout(barmode="overlay", margin={"r": 80})
    fig.update_xaxes(showticklabels=False, showgrid=False, range=[0, maxi * 1.16])
    fig.update_yaxes(title_text="", tickfont={"size": 12})
    return _finaliser(fig, hauteur=400)


def graphique_barres_categorie(
    donnees: pd.DataFrame, colonne_dimension: str, colonne_valeur: str
) -> go.Figure:
    """Barres verticales arrondies colorées par modalité, avec étiquettes."""
    fig = px.bar(
        donnees,
        x=colonne_dimension,
        y=colonne_valeur,
        color=colonne_dimension,
        color_discrete_sequence=list(PALETTE_CATEGORIELLE),
        text=colonne_valeur,
    )
    fig.update_traces(
        marker={"cornerradius": 8, "line": {"width": 0}},
        texttemplate="%{text:,.0f} €",
        textposition="outside",
        textfont=_ETIQUETTE,
        cliponaxis=False,
        hovertemplate="%{x} · %{y:,.0f} €<extra></extra>",
        width=0.62,
    )
    fig.update_xaxes(title_text="", tickfont={"size": 12})
    fig.update_yaxes(
        title_text="",
        showticklabels=False,
        showgrid=False,
        range=[0, float(donnees[colonne_valeur].max()) * 1.18],
    )
    fig.update_layout(margin={"t": 26}, uniformtext={"minsize": 9, "mode": "hide"})
    return _finaliser(fig)


def graphique_barres_horizontales(
    donnees: pd.DataFrame, colonne_categorie: str, colonne_valeur: str
) -> go.Figure:
    """Barres horizontales arrondies à série unique, avec étiquettes."""
    fig = px.bar(
        donnees, x=colonne_valeur, y=colonne_categorie, orientation="h", text=colonne_valeur
    )
    fig.update_traces(
        marker={"color": COULEUR_PRIMAIRE, "cornerradius": 8},
        texttemplate="%{x:,.0f} €",
        textposition="outside",
        textfont=_ETIQUETTE,
        cliponaxis=False,
        hovertemplate="%{y} · %{x:,.0f} €<extra></extra>",
        width=0.68,
    )
    fig.update_xaxes(
        title_text="",
        showticklabels=False,
        showgrid=False,
        range=[0, float(donnees[colonne_valeur].max()) * 1.16],
    )
    fig.update_yaxes(title_text="", tickfont={"size": 12})
    fig.update_layout(margin={"r": 80})
    return _finaliser(fig, hauteur=400)


def histogramme(
    donnees: pd.DataFrame,
    colonne: str,
    titre_x: str,
    nbins: int | None = None,
    ligne_seuil: float | None = None,
) -> go.Figure:
    """Histogramme d'une variable numérique, avec une ligne de seuil optionnelle."""
    fig = px.histogram(donnees, x=colonne, nbins=nbins)
    fig.update_traces(
        marker={"color": COULEUR_PRIMAIRE, "line": {"color": "#FFFFFF", "width": 1}},
        hovertemplate=titre_x + " %{x}<br>%{y} clients<extra></extra>",
    )
    if ligne_seuil is not None:
        fig.add_vline(
            x=ligne_seuil,
            line={"color": COULEUR_DANGER, "width": 2, "dash": "dash"},
            annotation_text=f"Seuil {ligne_seuil:.2f}",
            annotation_position="top",
            annotation_font={"color": COULEUR_DANGER, "size": 11},
        )
    fig.update_xaxes(title_text=titre_x)
    fig.update_yaxes(title_text="Nombre de clients")
    return _finaliser(fig)


def barres_valeur(
    donnees: pd.DataFrame,
    categorie: str,
    valeur: str,
    *,
    orientation: str = "v",
    suffixe: str = "",
    couleur: str = COULEUR_PRIMAIRE,
    decimales: int = 0,
    hauteur: int = _HAUTEUR_DEFAUT,
) -> go.Figure:
    """Barres à série unique avec étiquettes, suffixe libre (%, sans devise…)."""
    suffixe_txt = f" {suffixe}" if suffixe else ""
    valeur_fmt = f"%{{{'x' if orientation == 'h' else 'y'}}}:,.{decimales}f}}"
    axe_valeur = "x" if orientation == "h" else "y"
    axe_categorie = "y" if orientation == "h" else "x"
    maxi = float(donnees[valeur].max() or 0) * 1.2
    fig = px.bar(
        donnees,
        x=valeur if orientation == "h" else categorie,
        y=categorie if orientation == "h" else valeur,
        orientation=orientation,
        text=valeur,
    )
    fig.update_traces(
        marker={"color": couleur, "cornerradius": 8},
        texttemplate=valeur_fmt + suffixe_txt,
        textposition="outside",
        textfont=_ETIQUETTE,
        cliponaxis=False,
        hovertemplate=f"%{{{axe_categorie}}} · " + valeur_fmt + suffixe_txt + "<extra></extra>",
    )
    fig.update_layout(**{f"{axe_valeur}axis": {"range": [0, maxi], "showticklabels": False}})
    if orientation == "h":
        fig.update_layout(margin={"r": 76})
    else:
        fig.update_layout(margin={"t": 26})
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="")
    return _finaliser(fig, hauteur)


def barres_groupees(
    donnees: pd.DataFrame,
    categorie: str,
    series: list[tuple[str, str, str]],
    *,
    hauteur: int = _HAUTEUR_DEFAUT,
) -> go.Figure:
    """Barres groupées : chaque série = (libellé, colonne, couleur)."""
    fig = go.Figure()
    for libelle, colonne, couleur in series:
        fig.add_trace(
            go.Bar(
                x=donnees[categorie],
                y=donnees[colonne],
                name=libelle,
                marker={"color": couleur, "cornerradius": 6},
                hovertemplate="%{x} · " + libelle + " %{y:,.0f}<extra></extra>",
            )
        )
    fig.update_layout(
        barmode="group", height=hauteur, showlegend=True, bargap=0.3, bargroupgap=0.12
    )
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="")
    return fig


def barres_empilees(
    donnees_long: pd.DataFrame, categorie: str, valeur: str, couleur: str
) -> go.Figure:
    """Barres empilées (composition en %) par catégorie, colorées par modalité."""
    fig = px.bar(
        donnees_long,
        x=categorie,
        y=valeur,
        color=couleur,
        color_discrete_sequence=list(PALETTE_CATEGORIELLE),
    )
    fig.update_traces(hovertemplate="%{x} · %{fullData.name} : %{y:.1f} %<extra></extra>")
    fig.update_layout(barmode="stack", height=_HAUTEUR_DEFAUT, showlegend=True)
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="", ticksuffix=" %")
    return fig


def nuage(
    donnees: pd.DataFrame,
    colonne_x: str,
    colonne_y: str,
    couleur: str,
    titre_x: str,
    titre_y: str,
    hauteur: int = 380,
) -> go.Figure:
    """Nuage de points coloré par une modalité (ex. segment)."""
    fig = px.scatter(
        donnees,
        x=colonne_x,
        y=colonne_y,
        color=couleur,
        color_discrete_sequence=list(PALETTE_CATEGORIELLE),
    )
    fig.update_traces(marker={"size": 7, "opacity": 0.7, "line": {"width": 0}})
    fig.update_xaxes(title_text=titre_x)
    fig.update_yaxes(title_text=titre_y)
    fig.update_layout(height=hauteur, showlegend=True)
    return fig


def boite_par_categorie(
    donnees: pd.DataFrame, colonne_x: str, colonne_y: str, titre_x: str, titre_y: str
) -> go.Figure:
    """Boîtes à moustaches d'une variable numérique par modalité."""
    fig = px.box(
        donnees,
        x=colonne_x,
        y=colonne_y,
        color=colonne_x,
        color_discrete_sequence=list(PALETTE_CATEGORIELLE),
    )
    fig.update_traces(line={"width": 1.6}, marker={"size": 4, "opacity": 0.5})
    fig.update_xaxes(title_text=titre_x)
    fig.update_yaxes(title_text=titre_y)
    return _finaliser(fig)
