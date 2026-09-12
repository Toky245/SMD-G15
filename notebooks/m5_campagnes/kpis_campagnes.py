"""
M5 - Analyse des performances des campagnes marketing (responsable : Manassé)

Calcule les KPIs de chaque campagne (CTR, taux de conversion, CPC, CPA, ROI), compare les
canaux et produit les graphiques utilisés dans le rapport et la présentation.

Hypothèse de calcul du revenu
-----------------------------
Le fichier marketing ne contient pas le chiffre d'affaires généré par les campagnes. Le revenu
est donc estimé : Revenu = Conversions x panier moyen des ventes. Le panier moyen est calculé
directement à partir de data/processed/ventes_fusionnees.csv (90,81 sur le jeu étendu), et non
saisi en dur, pour rester cohérent si les données changent.

Entrées : data/processed/marketing_nettoye.csv, data/processed/ventes_fusionnees.csv
Sorties : data/results/kpis_campagnes.csv
          figures/m5_*.png
          notebooks/m5_campagnes/resume_resultats.txt

Utilisation (depuis n'importe quel dossier) :
    python notebooks/m5_campagnes/kpis_campagnes.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------
DOSSIER_SCRIPT = Path(__file__).resolve().parent
RACINE = DOSSIER_SCRIPT.parents[1]
DOSSIER_PROCESSED = RACINE / "data" / "processed"
DOSSIER_RESULTS = RACINE / "data" / "results"
DOSSIER_FIGURES = RACINE / "figures"
DOSSIER_RESULTS.mkdir(parents=True, exist_ok=True)
DOSSIER_FIGURES.mkdir(parents=True, exist_ok=True)

BLEU, ORANGE, VERT, ROUGE = "#4C72B0", "#DD8452", "#55A868", "#C44E52"
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({"figure.dpi": 110, "axes.titleweight": "bold",
                     "axes.spines.top": False, "axes.spines.right": False})


def sauver(fig, nom: str) -> None:
    fig.savefig(DOSSIER_FIGURES / f"m5_{nom}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 1. Chargement et hypothèse de revenu
# ---------------------------------------------------------------------------
campagnes = pd.read_csv(DOSSIER_PROCESSED / "marketing_nettoye.csv",
                        parse_dates=["Start_Date", "End_Date"])
ventes = pd.read_csv(DOSSIER_PROCESSED / "ventes_fusionnees.csv", parse_dates=["Date"])

PANIER_MOYEN = round(ventes["Sale_Price"].mean(), 2)
print(f"Campagnes analysées : {len(campagnes)}")
print(f"Panier moyen des ventes (hypothèse de revenu) : {PANIER_MOYEN}")

# ---------------------------------------------------------------------------
# 2. Calcul des KPIs
# ---------------------------------------------------------------------------
# CTR              : part des impressions qui donnent un clic
# Taux_Conversion  : part des clics qui donnent un achat
# CPC              : coût moyen d'un clic
# CPA              : coût moyen d'une vente obtenue
# ROI              : rentabilité de la campagne, en pourcentage du budget investi
kpis = campagnes.copy()
kpis["CTR"] = (kpis["Clicks"] / kpis["Impressions"] * 100).round(2)
kpis["Taux_Conversion"] = (kpis["Conversions"] / kpis["Clicks"] * 100).round(2)
kpis["CPC"] = (kpis["Budget"] / kpis["Clicks"]).round(2)
kpis["CPA"] = (kpis["Budget"] / kpis["Conversions"]).round(2)
kpis["Revenu_Estime"] = (kpis["Conversions"] * PANIER_MOYEN).round(2)
kpis["ROI"] = ((kpis["Revenu_Estime"] - kpis["Budget"]) / kpis["Budget"] * 100).round(2)

COLONNES = ["Campaign_ID", "Channel", "Start_Date", "End_Date", "Budget", "Impressions",
            "Clicks", "Conversions", "CTR", "Taux_Conversion", "CPC", "CPA",
            "Revenu_Estime", "ROI"]
kpis = kpis[COLONNES]
kpis.to_csv(DOSSIER_RESULTS / "kpis_campagnes.csv", index=False)

# ---------------------------------------------------------------------------
# 3. Comparaison des canaux
# ---------------------------------------------------------------------------
# Les KPIs par canal sont recalculés sur les totaux du canal, et non en faisant la moyenne
# des KPIs de chaque campagne : une moyenne de ratios donnerait le même poids à une petite
# et à une grosse campagne.
totaux = kpis.groupby("Channel")[["Budget", "Impressions", "Clicks", "Conversions",
                                  "Revenu_Estime"]].sum()
canaux = pd.DataFrame({
    "Campagnes": kpis.groupby("Channel").size(),
    "Budget": totaux["Budget"],
    "Conversions": totaux["Conversions"],
    "CTR": (totaux["Clicks"] / totaux["Impressions"] * 100).round(2),
    "Taux_Conversion": (totaux["Conversions"] / totaux["Clicks"] * 100).round(2),
    "CPC": (totaux["Budget"] / totaux["Clicks"]).round(2),
    "CPA": (totaux["Budget"] / totaux["Conversions"]).round(2),
    "Revenu_Estime": totaux["Revenu_Estime"].round(2),
    "ROI": ((totaux["Revenu_Estime"] - totaux["Budget"]) / totaux["Budget"] * 100).round(2),
}).sort_values("ROI", ascending=False)

print("\n=== Performance par canal (classement par ROI) ===")
print(canaux.to_string())

meilleur = canaux.index[0]
pire = canaux.index[-1]
print(f"\nCanal le plus rentable : {meilleur} (ROI {canaux.loc[meilleur, 'ROI']:.0f} %)")
print(f"Canal le moins rentable : {pire} (ROI {canaux.loc[pire, 'ROI']:.0f} %)")

print("\n=== Top 5 des campagnes par ROI ===")
print(kpis.nlargest(5, "ROI")[["Campaign_ID", "Channel", "Budget", "Conversions", "CPA", "ROI"]]
      .to_string(index=False))

# ---------------------------------------------------------------------------
# 4. Graphiques
# ---------------------------------------------------------------------------
# ROI par canal
fig, ax = plt.subplots(figsize=(8, 4.5))
couleurs = [VERT if v > 0 else ROUGE for v in canaux["ROI"]]
ax.bar(canaux.index, canaux["ROI"], color=couleurs)
ax.axhline(0, color="black", lw=1)
ax.bar_label(ax.containers[0], fmt="%.0f %%", fontsize=9)
ax.set_title("ROI estimé par canal")
ax.set_ylabel("ROI (%)")
sauver(fig, "01_roi_par_canal")

# Entonnoir : CTR puis taux de conversion
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
for ax, col, titre, couleur in [(axes[0], "CTR", "Taux de clic (CTR)", BLEU),
                                (axes[1], "Taux_Conversion", "Taux de conversion", ORANGE)]:
    donnees = canaux[col].sort_values(ascending=False)
    ax.bar(donnees.index, donnees.values, color=couleur)
    ax.bar_label(ax.containers[0], fmt="%.2f %%", fontsize=9)
    ax.set_title(titre)
    ax.set_ylabel("%")
fig.suptitle("Les canaux qui attirent le clic ne sont pas ceux qui convertissent",
             fontweight="bold", y=1.02)
fig.tight_layout()
sauver(fig, "02_ctr_conversion")

# Coûts : CPC et CPA
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
for ax, col, titre in [(axes[0], "CPC", "Coût par clic (CPC)"), (axes[1], "CPA", "Coût par acquisition (CPA)")]:
    donnees = canaux[col].sort_values()
    ax.bar(donnees.index, donnees.values, color=BLEU)
    ax.bar_label(ax.containers[0], fmt="%.2f", fontsize=9)
    ax.set_title(titre)
fig.suptitle("Coûts par canal", fontweight="bold", y=1.02)
fig.tight_layout()
sauver(fig, "03_couts_par_canal")

# Budget investi et revenu estimé
fig, ax = plt.subplots(figsize=(9, 4.5))
x = range(len(canaux))
largeur = 0.38
ax.bar([i - largeur / 2 for i in x], canaux["Budget"], largeur, label="Budget investi", color=BLEU)
ax.bar([i + largeur / 2 for i in x], canaux["Revenu_Estime"], largeur, label="Revenu estimé", color=VERT)
ax.set_xticks(list(x))
ax.set_xticklabels(canaux.index)
ax.set_title("Budget investi et revenu estimé, par canal")
ax.legend()
sauver(fig, "04_budget_revenu")

# Dispersion budget / conversions
fig, ax = plt.subplots(figsize=(9, 5))
for (canal, g), couleur in zip(kpis.groupby("Channel"), [BLEU, ORANGE, VERT, ROUGE, "#8172B3"]):
    ax.scatter(g["Budget"], g["Conversions"], label=canal, color=couleur, s=60, alpha=0.8)
ax.set_title("Budget et conversions des campagnes, par canal")
ax.set_xlabel("Budget")
ax.set_ylabel("Conversions")
ax.legend(title="Canal")
sauver(fig, "05_budget_conversions")

# ---------------------------------------------------------------------------
# 5. Résumé
# ---------------------------------------------------------------------------
budget_total = canaux["Budget"].sum()
revenu_total = canaux["Revenu_Estime"].sum()
roi_global = (revenu_total - budget_total) / budget_total * 100
conv_max = canaux["Taux_Conversion"].idxmax()
cpa_min = canaux["CPA"].idxmin()
cpa_max = canaux["CPA"].idxmax()
ctr_max = canaux["CTR"].idxmax()

lignes = [
    "=" * 78,
    "M5 - PERFORMANCE DES CAMPAGNES MARKETING",
    "Responsable : Manassé",
    "=" * 78,
    "",
    "Ce fichier est généré automatiquement par notebooks/m5_campagnes/kpis_campagnes.py.",
    "Il contient les chiffres et les conclusions à reprendre dans le rapport et les slides.",
    "",
    "-" * 78,
    "1. PERIMETRE ET METHODE",
    "-" * 78,
    "",
    f"Campagnes analysées : {len(campagnes)}, réparties sur 5 canaux "
    f"(Email, In-Store, Online, Social, TV), 10 campagnes par canal.",
    f"Période : du {campagnes['Start_Date'].min().date()} au {campagnes['End_Date'].max().date()}.",
    "",
    "Indicateurs calculés pour chaque campagne :",
    "  CTR             = Clics / Impressions        part des affichages qui donnent un clic",
    "  Taux_Conversion = Conversions / Clics        part des clics qui donnent un achat",
    "  CPC             = Budget / Clics             coût moyen d'un clic",
    "  CPA             = Budget / Conversions       coût moyen d'une vente obtenue",
    "  ROI             = (Revenu - Budget) / Budget rentabilité, en % du budget investi",
    "",
    "HYPOTHESE IMPORTANTE A CITER DANS LE RAPPORT",
    "Le fichier marketing ne contient pas le chiffre d'affaires généré par les campagnes :",
    "le ROI n'est donc pas calculable directement. Le revenu est estimé ainsi :",
    "",
    f"    Revenu = Conversions x panier moyen des ventes = Conversions x {PANIER_MOYEN}",
    "",
    "Le panier moyen est calculé à partir de data/processed/ventes_fusionnees.csv, et non",
    "saisi en dur, pour rester cohérent si les données changent.",
    "",
    "Limite : cette hypothèse suppose que chaque conversion vaut un panier moyen, et que",
    "toutes les ventes se valent quel que soit le canal. Les ROI obtenus sont donc des",
    "ordres de grandeur comparables entre canaux, pas des montants exacts.",
    "",
    "Limite complémentaire : les ventes ne se font que sur Online et In-Store, alors que les",
    "campagnes couvrent aussi Social, Email et TV. Aucun lien direct entre une campagne et une",
    "vente n'est donc possible ; l'analyse compare les canaux entre eux, sans attribution.",
    "",
    "-" * 78,
    "2. RESULTATS PAR CANAL (classement par ROI)",
    "-" * 78,
    "",
    canaux.to_string(),
    "",
    f"Budget total investi : {budget_total:,.0f}".replace(",", " "),
    f"Revenu total estimé  : {revenu_total:,.0f}".replace(",", " "),
    f"ROI global           : {roi_global:.0f} %",
    "",
    "Note de méthode : les KPIs par canal sont recalculés sur les totaux du canal, et non en",
    "moyennant les KPIs de chaque campagne. Une moyenne de ratios donnerait le même poids à",
    "une petite et à une grosse campagne.",
    "",
    "-" * 78,
    "3. CONCLUSIONS A REPRENDRE DANS LE RAPPORT",
    "-" * 78,
    "",
    f"1. {meilleur} est le canal le plus rentable (ROI {canaux.loc[meilleur, 'ROI']:.0f} %), avec le",
    f"   CPA le plus bas ({canaux.loc[cpa_min, 'CPA']:.2f}). Il reçoit pourtant le plus petit budget",
    "   (" + f"{canaux.loc[meilleur, 'Budget']:,.0f}".replace(",", " ")
    + "). C'est le principal levier d'optimisation du budget.",
    "",
    f"2. {pire} est le canal le moins rentable (ROI {canaux.loc[pire, 'ROI']:.0f} %) alors qu'il affiche",
    f"   le meilleur taux de conversion ({canaux.loc[conv_max, 'Taux_Conversion']:.2f} %). Explication : son CTR est le plus",
    f"   faible ({canaux.loc[pire, 'CTR']:.2f} %), donc il faut beaucoup d'impressions pour obtenir un clic,",
    f"   ce qui fait monter le CPC ({canaux.loc[pire, 'CPC']:.2f}) puis le CPA ({canaux.loc[cpa_max, 'CPA']:.2f}).",
    "",
    "3. Le canal qui attire le clic n'est pas celui qui convertit. Les canaux à fort CTR",
    f"   ({ctr_max} en tête) convertissent peu, et inversement. Un seul indicateur ne suffit",
    "   donc pas à juger un canal : c'est le CPA, puis le ROI, qui tranchent.",
    "",
    "4. TV concentre le plus gros budget ("
    + f"{canaux.loc['TV', 'Budget']:,.0f}".replace(",", " ")
    + f", soit {canaux.loc['TV', 'Budget'] / budget_total * 100:.0f} % du total) pour un",
    f"   ROI de {canaux.loc['TV', 'ROI']:.0f} %, inférieur à Email et Online. Une partie de ce budget serait",
    "   plus rentable sur les canaux à faible CPA.",
    "",
    "-" * 78,
    "4. TOP 5 DES CAMPAGNES PAR ROI",
    "-" * 78,
    "",
    kpis.nlargest(5, "ROI")[["Campaign_ID", "Channel", "Budget", "Conversions", "CPA", "ROI"]]
        .to_string(index=False),
    "",
    "-" * 78,
    "5. GRAPHIQUES DISPONIBLES (dossier figures/)",
    "-" * 78,
    "",
    "  m5_01_roi_par_canal.png      ROI estimé par canal",
    "  m5_02_ctr_conversion.png     CTR et taux de conversion par canal",
    "  m5_03_couts_par_canal.png    CPC et CPA par canal",
    "  m5_04_budget_revenu.png      budget investi et revenu estimé par canal",
    "  m5_05_budget_conversions.png dispersion budget / conversions des campagnes",
    "",
    "-" * 78,
    "6. LIVRABLES ET SUITE",
    "-" * 78,
    "",
    "  data/results/kpis_campagnes.csv  -> pour le dashboard de Toky",
    "  figures/m5_*.png                 -> pour le rapport et les slides",
    "",
    "Les chiffres du tableau de la section 2 sont ceux dont Lalatiana a besoin pour la",
    "répartition du budget (M7).",
    "",
    "A faire : rédiger la partie M5 du rapport dans rapport/parties/ et préparer 2 à 4 slides.",
    "",
]

with open(DOSSIER_SCRIPT / "resume_resultats.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lignes))

print(f"\nFichiers écrits : data/results/kpis_campagnes.csv, figures/m5_*.png, resume_resultats.txt")
