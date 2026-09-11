# Dashboard M8 — Marketing digital

Tableau de bord Streamlit du projet. Il lit les données produites par les autres
modules et ne les modifie jamais.

## Lancement

Depuis la racine du dépôt, avec l'environnement virtuel activé :

```bash
streamlit run dashboard/app.py
```

Dépendances : voir `requirements.txt` (`pip install -r requirements.txt`).

## Structure

```
dashboard/
  app.py              Point d'entrée : thème, logo, filtres globaux, navigation
  assets/
    logo.svg          Logo de marque (affiché via st.logo)
  core/
    config.py         Constantes : chemins (pathlib), colonnes, seuils, libellés
    theme.py          Tokens de couleurs, CSS (police Inter), template Plotly
    formats.py        Formatage des nombres en français
    calculs.py        Calculs métier (fonctions pures, sans Streamlit)
  data/
    loaders.py        Chargement des CSV en lecture seule (cache Streamlit)
  components/
    filtres.py        Barre latérale de filtres globaux
    cartes.py         Cartes KPI
    graphiques.py     Fabriques de graphiques Plotly
    etat_vide.py      État vide propre pour les fichiers non encore livrés
    mise_en_page.py   En-têtes de page
  pages/
    vue_ensemble.py   Vue d'ensemble (KPI, CA mensuel, ventilations, top produits)
    clients.py        Clients (démographie, comportement, export)
    segments.py       Segments (activée par data/results/segments.csv)
    campagnes.py      Campagnes (activée par data/results/kpis_campagnes.csv)
    predictions.py    Prédictions (activée par data/results/predictions_churn.csv)
```

## Sources de données

Lues dans `data/processed/` (produites par le module M2) :

- `ventes_fusionnees.csv` — une ligne par vente ;
- `clients_agreges.csv` — une ligne par client (RFM, panier, parts par catégorie) ;
- `marketing_nettoye.csv` — les campagnes.

Le dashboard n'utilise jamais `data/generated/`.

## Fichiers attendus dans `data/results/`

Ces fichiers sont livrés par les autres modules. Tant qu'un fichier est absent, la
page correspondante affiche un état vide ; dès qu'il est présent, la page s'active
automatiquement (relancer l'application ou vider le cache si nécessaire).

| Fichier | Livré par | Colonnes attendues |
|---|---|---|
| `segments.csv` | module M3 | `Customer_ID`, `Segment_ID`, `Segment_Nom` |
| `kpis_campagnes.csv` | module M5 | `Campaign_ID`, `Channel`, `Budget`, `Impressions`, `Clicks`, `Conversions`, `CTR`, `Taux_Conversion`, `CPC`, `CPA`, `ROI` |
| `predictions_churn.csv` | module M6 | `Customer_ID`, `Proba_Churn`, `CLV` (optionnelle) |

## Conventions

- Interface entièrement en français.
- Thème défini une seule fois (tokens dans `core/theme.py` et `.streamlit/config.toml`).
- Police Inter, icônes Google Material Symbols (`:material/nom:`).
- Code formaté et vérifié avec `ruff` (`ruff check dashboard`, `ruff format dashboard`).
