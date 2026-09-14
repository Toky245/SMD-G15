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
    vue_ensemble.py   Vue d'ensemble (KPI, CA mensuel comparé, ventilations, top produits)
    clients.py        Clients (démographie, comportement, tableau, export)
    segments.py       Segments (profil, répartition, CA, composition des dépenses)
    campagnes.py      Campagnes (KPI par canal recalculés, ROI, CTR, CPC/CPA, budget/revenu)
    predictions.py    Prédictions (seuil de risque, histogramme, segment × valeur, nuage CLV)
```

## Filtres

Barre latérale, adaptée à chaque page :

- **Vue d'ensemble** et **Clients** : filtres au niveau des ventes — période, canal,
  catégorie, ville, genre.
- **Segments** et **Prédictions** : seuls **ville** et **genre** s'appliquent (jointure
  avec les clients) ; période, canal et catégorie sont masqués car ce sont des filtres
  au niveau des ventes.
- **Campagnes** : filtres **propres à la page** (période sur `Start_Date`, canal
  campagne), les canaux campagne n'étant pas les canaux de vente.

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

| Fichier | Livré par | Colonnes utilisées |
|---|---|---|
| `segments.csv` | module M3 | `Customer_ID`, `Segment_ID`, `Segment_Nom` |
| `kpis_campagnes.csv` | module M5 | `Campaign_ID`, `Channel`, `Start_Date`, `Budget`, `Impressions`, `Clicks`, `Conversions`, `Revenu_Estime` (colonnes de ratios `CTR`, `Taux_Conversion`, `CPC`, `CPA`, `ROI` acceptées mais **recalculées** depuis les totaux) |
| `predictions_churn.csv` | module M6 | `Customer_ID`, `Proba_Churn`, `CLV` (`Churn_Predicted` optionnelle) |

Conventions et hypothèses importantes :

- **`segments.csv`** : le `Segment_ID` `-1` (nom « Clients sans achat ») désigne les
  clients sans achat. Ils sont comptés dans les répartitions mais **exclus** des
  moyennes de comportement (panier, récence, fréquence) et des analyses de dépense.
- **`kpis_campagnes.csv`** : les indicateurs par canal sont **recalculés à partir des
  totaux** (ex. `CTR = Σclics / Σimpressions`), jamais en moyennant les ratios des
  campagnes. `CTR`, `Taux_Conversion` et `ROI` sont exprimés en pourcentage. Le revenu
  est **estimé** (`Conversions × panier moyen 90,81`) ; aucune devise n'est précisée.
- **`predictions_churn.csv`** : ne couvre que les 726 clients acheteurs. Les mesures
  (part à risque, CLV) portent sur ces clients scorés, jamais sur les 805 clients.

## Conventions

- Interface entièrement en français.
- Thème défini une seule fois (tokens dans `core/theme.py` et `.streamlit/config.toml`).
- Police Inter, icônes Google Material Symbols (`:material/nom:`).
- Code formaté et vérifié avec `ruff` (`ruff check dashboard`, `ruff format dashboard`).
