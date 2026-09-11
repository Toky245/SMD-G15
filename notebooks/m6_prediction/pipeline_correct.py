"""
M6 - Prédiction du churn et de la CLV (responsable : Câline)

Méthode : validation temporelle.
    - Les variables sont calculées uniquement avec les ventes jusqu'à la date de coupure (CUTOFF).
    - La cible Churn = 1 si le client n'a fait aucun achat dans la fenêtre qui suit la coupure.
    - Le meilleur modèle est ensuite appliqué aux variables recalculées sur tout l'historique,
      pour obtenir le risque de churn actuel de chaque client.

Entrée  : data/processed/ventes_fusionnees.csv
Sorties : data/results/predictions_churn.csv
          figures/m6_*.png
          notebooks/m6_prediction/resume_resultats.txt

Utilisation (depuis n'importe quel dossier) :
    python notebooks/m6_prediction/pipeline_correct.py
"""

import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Chemins : construits à partir de la racine du dépôt
# ---------------------------------------------------------------------------
DOSSIER_SCRIPT = Path(__file__).resolve().parent
RACINE = DOSSIER_SCRIPT.parents[1]
FICHIER_VENTES = RACINE / "data" / "processed" / "ventes_fusionnees.csv"
DOSSIER_RESULTS = RACINE / "data" / "results"
DOSSIER_FIGURES = RACINE / "figures"
DOSSIER_RESULTS.mkdir(parents=True, exist_ok=True)
DOSSIER_FIGURES.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Paramètres
# ---------------------------------------------------------------------------
CUTOFF = pd.Timestamp("2024-09-30")
FUTURE_START = pd.Timestamp("2024-10-01")
FUTURE_END = pd.Timestamp("2024-12-31")
FINAL_REF = pd.Timestamp("2024-12-31")
DEBUT_OBSERVATION = pd.Timestamp("2023-01-01")
HORIZON_CLV_MOIS = 24
JOURS_PAR_MOIS = 30.44
FEATURES = ["Recence_Jours", "Nb_Achats", "Montant_Total", "Age", "Part_Online"]

BLEU, ORANGE = "#4C72B0", "#DD8452"
plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold"})


def build_features(sales_subset: pd.DataFrame, reference_date: pd.Timestamp) -> pd.DataFrame:
    """Construit les variables par client à partir des ventes, par rapport à une date de référence."""
    g = sales_subset.groupby("Customer_ID").agg(
        Nb_Achats=("Sale_ID", "count"),
        Montant_Total=("Sale_Price", "sum"),
        Dernier_Achat=("Date", "max"),
        Age=("Age", "first"),
        Join_Date=("Join_Date", "first"),
    ).reset_index()
    g["Panier_Moyen"] = g["Montant_Total"] / g["Nb_Achats"]
    g["Recence_Jours"] = (reference_date - g["Dernier_Achat"]).dt.days
    online = sales_subset[sales_subset["Channel"] == "Online"].groupby("Customer_ID")["Sale_ID"].count()
    g = g.merge(online.rename("Nb_Online"), on="Customer_ID", how="left")
    g["Nb_Online"] = g["Nb_Online"].fillna(0)
    g["Part_Online"] = (g["Nb_Online"] / g["Nb_Achats"] * 100).round(1)
    return g


def sauver(fig, nom: str) -> None:
    fig.savefig(DOSSIER_FIGURES / f"m6_{nom}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ===========================================================================
# 1. JEU D'ENTRAÎNEMENT : variables AVANT la coupure, cible = churn APRÈS
# ===========================================================================
ventes = pd.read_csv(FICHIER_VENTES, parse_dates=["Date", "Join_Date"])

ventes_avant = ventes[ventes["Date"] <= CUTOFF]
train_features = build_features(ventes_avant, CUTOFF)
print(f"Clients ayant acheté au moins une fois avant le {CUTOFF.date()} : {len(train_features)}")

clients_actifs_apres = set(
    ventes[(ventes["Date"] >= FUTURE_START) & (ventes["Date"] <= FUTURE_END)]["Customer_ID"]
)
train_features["Churn"] = (~train_features["Customer_ID"].isin(clients_actifs_apres)).astype(int)
print(f"Taux de churn (fenêtre future) : {train_features['Churn'].mean() * 100:.1f} %")

X = train_features[FEATURES]
y = train_features["Churn"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ===========================================================================
# 2. ENTRAÎNEMENT ET COMPARAISON DES MODÈLES
# ===========================================================================
lr = LogisticRegression(random_state=42, max_iter=1000).fit(X_train_scaled, y_train)
rf = RandomForestClassifier(n_estimators=200, random_state=42, max_depth=6).fit(X_train, y_train)
xg = xgb.XGBClassifier(random_state=42, eval_metric="logloss", max_depth=4).fit(X_train, y_train)

MODELES = {"Régression logistique": (lr, True), "Random Forest": (rf, False), "XGBoost": (xg, False)}

scores = {}
for name, (model, needs_scaling) in MODELES.items():
    Xte = X_test_scaled if needs_scaling else X_test
    pred = model.predict(Xte)
    proba = model.predict_proba(Xte)[:, 1]          # l'AUC se calcule sur les probabilités
    scores[name] = {
        "Accuracy": accuracy_score(y_test, pred),
        "F1": f1_score(y_test, pred, zero_division=0),
        "AUC": roc_auc_score(y_test, proba),
    }

scores_df = pd.DataFrame(scores).T
print("\n=== Comparaison des modèles (validation temporelle) ===")
print(scores_df.round(3))

best_name = scores_df["F1"].idxmax()
best_model, best_needs_scaling = MODELES[best_name]
print(f"\nModèle retenu (meilleur F1) : {best_name}")

if best_name == "Régression logistique":
    importances = pd.Series(np.abs(lr.coef_[0]), index=FEATURES)
else:
    importances = pd.Series(best_model.feature_importances_, index=FEATURES)
importances = importances.sort_values(ascending=False)
print("\n=== Importance des variables ===")
print(importances.round(3))

# ===========================================================================
# 3. LIVRABLE : variables recalculées sur tout l'historique -> risque actuel
# ===========================================================================
final_features = build_features(ventes, FINAL_REF)
print(f"\nClients avec au moins un achat (population finale) : {len(final_features)}")

X_final = final_features[FEATURES]
X_final_input = scaler.transform(X_final) if best_needs_scaling else X_final
final_features["Proba_Churn"] = best_model.predict_proba(X_final_input)[:, 1].round(3)
final_features["Churn_Predicted"] = best_model.predict(X_final_input)

# CLV = panier moyen x fréquence mensuelle x horizon de 24 mois.
# La fréquence est calculée sur la durée d'activité réelle de chaque client :
# depuis son inscription, ou depuis le début de l'observation s'il est inscrit avant.
debut_activite = final_features["Join_Date"].clip(lower=DEBUT_OBSERVATION)
mois_actifs = ((FINAL_REF - debut_activite).dt.days / JOURS_PAR_MOIS).clip(lower=1)
final_features["Frequence_Mensuelle"] = final_features["Nb_Achats"] / mois_actifs
final_features["CLV"] = (
    final_features["Panier_Moyen"] * final_features["Frequence_Mensuelle"] * HORIZON_CLV_MOIS
).round(2)

taux_actuel = final_features["Churn_Predicted"].mean() * 100
clv_ok = final_features.loc[final_features["Churn_Predicted"] == 0, "CLV"].mean()
clv_risque = final_features.loc[final_features["Churn_Predicted"] == 1, "CLV"].mean()
print(f"\nTaux de churn actuel prédit : {taux_actuel:.1f} %")
print(f"CLV moyenne (non à risque) : {clv_ok:.2f}")
print(f"CLV moyenne (à risque)     : {clv_risque:.2f}")

deliverable = (final_features[["Customer_ID", "Proba_Churn", "Churn_Predicted", "CLV"]]
               .sort_values("Proba_Churn", ascending=False))
deliverable.to_csv(DOSSIER_RESULTS / "predictions_churn.csv", index=False)
print("\nTop 10 clients à risque :")
print(deliverable.head(10).to_string(index=False))

# ===========================================================================
# 4. GRAPHIQUES (figures/m6_*.png)
# ===========================================================================
# Répartition du churn dans le jeu d'entraînement
fig, ax = plt.subplots(figsize=(6, 4.5))
comptes = train_features["Churn"].value_counts().reindex([0, 1])
ax.bar(["Actif (0)", "Churn (1)"], comptes.values, color=[BLEU, ORANGE])
for i, v in enumerate(comptes.values):
    ax.text(i, v, f"{v} ({v / comptes.sum() * 100:.0f} %)", ha="center", va="bottom")
ax.set_title("Répartition du churn (entraînement)")
ax.set_ylabel("Clients")
sauver(fig, "repartition_churn")

# Comparaison des modèles
fig, ax = plt.subplots(figsize=(9, 4.5))
scores_df[["Accuracy", "F1", "AUC"]].plot.bar(ax=ax, rot=0, color=[BLEU, ORANGE, "#55A868"])
ax.set_ylim(0, 1)
ax.set_title("Comparaison des modèles sur le jeu de test")
ax.set_ylabel("Score")
ax.legend(loc="lower right")
for c in ax.containers:
    ax.bar_label(c, fmt="%.2f", fontsize=9)
sauver(fig, "comparaison_modeles")

# Importance des variables
fig, ax = plt.subplots(figsize=(8, 4.5))
imp = importances.sort_values()
ax.barh(imp.index, imp.values, color=BLEU)
ax.set_title(f"Importance des variables ({best_name})")
ax.set_xlabel("Importance")
sauver(fig, "importance_variables")

# Distribution des probabilités de churn actuelles
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.hist(final_features["Proba_Churn"], bins=30, color=BLEU, edgecolor="white")
ax.axvline(0.5, color=ORANGE, ls="--", lw=2, label="Seuil 0,5")
ax.set_title("Distribution des probabilités de churn (au 31/12/2024)")
ax.set_xlabel("Probabilité de churn")
ax.set_ylabel("Clients")
ax.legend()
sauver(fig, "distribution_proba")

# CLV selon le statut prédit
fig, ax = plt.subplots(figsize=(6, 4.5))
ax.bar(["Non à risque", "À risque"], [clv_ok, clv_risque], color=[BLEU, ORANGE])
for i, v in enumerate([clv_ok, clv_risque]):
    ax.text(i, v, f"{v:.0f}", ha="center", va="bottom")
ax.set_title("CLV moyenne selon le statut prédit")
ax.set_ylabel("CLV (24 mois)")
sauver(fig, "clv_par_statut")

# ===========================================================================
# 5. RÉSUMÉ
# ===========================================================================
with open(DOSSIER_SCRIPT / "resume_resultats.txt", "w", encoding="utf-8") as f:
    f.write(f"MÉTHODE : validation temporelle (coupure au {CUTOFF.date()})\n")
    f.write(f"Population d'entraînement : {len(train_features)} clients ayant acheté avant la coupure\n")
    f.write(f"Taux de churn (fenêtre future) : {train_features['Churn'].mean() * 100:.1f} %\n\n")
    f.write("Comparaison des modèles (jeu de test) :\n")
    f.write(scores_df.round(3).to_string() + "\n")
    f.write(f"\nModèle retenu : {best_name}\n")
    f.write(f"\nImportance des variables :\n{importances.round(3).to_string()}\n")
    f.write("\n--- LIVRABLE (toutes les ventes jusqu'au 31/12/2024) ---\n")
    f.write(f"Population : {len(final_features)} clients avec historique d'achat\n")
    f.write(f"Taux de churn actuel prédit : {taux_actuel:.1f} %\n")
    f.write(f"CLV moyenne non à risque : {clv_ok:.2f}\n")
    f.write(f"CLV moyenne à risque : {clv_risque:.2f}\n")

print(f"\nFichiers écrits : {DOSSIER_RESULTS / 'predictions_churn.csv'}, figures/m6_*.png, resume_resultats.txt")
