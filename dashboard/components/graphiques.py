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
    donnees: pd.DataFrame, colonne: str, titre_x: str, nbins: int | None = None
) -> go.Figure:
    """Histogramme d'une variable numérique (couleur principale)."""
    fig = px.histogram(donnees, x=colonne, nbins=nbins)
    fig.update_traces(
        marker={"color": COULEUR_PRIMAIRE, "line": {"color": "#FFFFFF", "width": 1}},
        hovertemplate=titre_x + " %{x}<br>%{y} clients<extra></extra>",
    )
    fig.update_xaxes(title_text=titre_x)
    fig.update_yaxes(title_text="Nombre de clients")
    return _finaliser(fig)


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
