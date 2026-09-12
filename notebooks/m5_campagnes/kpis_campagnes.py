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
with open(DOSSIER_SCRIPT / "resume_resultats.txt", "w", encoding="utf-8") as f:
    f.write(f"M5 - PERFORMANCE DES CAMPAGNES ({len(campagnes)} campagnes)\n\n")
    f.write("Hypothèse de revenu : Revenu = Conversions x panier moyen des ventes\n")
    f.write(f"Panier moyen utilisé : {PANIER_MOYEN}\n\n")
    f.write("Performance par canal (classement par ROI) :\n")
    f.write(canaux.to_string() + "\n\n")
    f.write(f"Canal le plus rentable : {meilleur} (ROI {canaux.loc[meilleur, 'ROI']:.0f} %)\n")
    f.write(f"Canal le moins rentable : {pire} (ROI {canaux.loc[pire, 'ROI']:.0f} %)\n\n")
    f.write("Top 5 des campagnes par ROI :\n")
    f.write(kpis.nlargest(5, "ROI")[["Campaign_ID", "Channel", "Budget", "Conversions", "CPA", "ROI"]]
            .to_string(index=False) + "\n")

print(f"\nFichiers écrits : data/results/kpis_campagnes.csv, figures/m5_*.png, resume_resultats.txt")
