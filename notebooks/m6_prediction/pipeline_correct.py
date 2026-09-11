import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
import xgboost as xgb
import warnings
warnings.filterwarnings("ignore")

ventes = pd.read_csv("/mnt/user-data/uploads/ventes_fusionnees.csv", parse_dates=["Date","Join_Date"])

CUTOFF = pd.Timestamp("2024-09-30")
FUTURE_START = pd.Timestamp("2024-10-01")
FUTURE_END = pd.Timestamp("2024-12-31")
FINAL_REF = pd.Timestamp("2024-12-31")

def build_features(sales_subset, reference_date):
    """Construit les variables RFM à partir d'un sous-ensemble de ventes, par rapport à une date de référence."""
    g = sales_subset.groupby("Customer_ID").agg(
        Nb_Achats=("Sale_ID","count"),
        Montant_Total=("Sale_Price","sum"),
        Dernier_Achat=("Date","max"),
        Age=("Age","first"),
    ).reset_index()
    g["Panier_Moyen"] = g["Montant_Total"] / g["Nb_Achats"]
    g["Recence_Jours"] = (reference_date - g["Dernier_Achat"]).dt.days
    online = sales_subset[sales_subset["Channel"]=="Online"].groupby("Customer_ID")["Sale_ID"].count()
    g = g.merge(online.rename("Nb_Online"), on="Customer_ID", how="left")
    g["Nb_Online"] = g["Nb_Online"].fillna(0)
    g["Part_Online"] = (g["Nb_Online"] / g["Nb_Achats"] * 100).round(1)
    return g

# =====================================================================
# JEU D'ENTRAÎNEMENT : features calculées AVANT le cutoff, cible = churn APRÈS
# =====================================================================
ventes_avant = ventes[ventes["Date"] <= CUTOFF]
train_features = build_features(ventes_avant, CUTOFF)
print(f"Clients ayant acheté au moins une fois avant le {CUTOFF.date()} : {len(train_features)}")

clients_actifs_apres = set(ventes[(ventes["Date"] >= FUTURE_START) & (ventes["Date"] <= FUTURE_END)]["Customer_ID"])
train_features["Churn"] = (~train_features["Customer_ID"].isin(clients_actifs_apres)).astype(int)

print(f"Répartition Churn (fenêtre future) :\n{train_features['Churn'].value_counts()}")
print(f"Taux de churn : {train_features['Churn'].mean()*100:.1f}%")

FEATURES = ["Recence_Jours","Nb_Achats","Montant_Total","Age","Part_Online"]
X = train_features[FEATURES]
y = train_features["Churn"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

lr = LogisticRegression(random_state=42, max_iter=1000).fit(X_train_scaled, y_train)
rf = RandomForestClassifier(n_estimators=200, random_state=42, max_depth=6).fit(X_train, y_train)
xg = xgb.XGBClassifier(random_state=42, eval_metric="logloss", max_depth=4).fit(X_train, y_train)

scores = {}
for name, model, Xte in [("Régression logistique", lr, X_test_scaled), ("Random Forest", rf, X_test), ("XGBoost", xg, X_test)]:
    pred = model.predict(Xte)
    scores[name] = {"Accuracy": accuracy_score(y_test, pred), "F1": f1_score(y_test, pred, zero_division=0), "AUC": roc_auc_score(y_test, pred)}

print("\n=== Comparaison des modèles (validation temporelle correcte) ===")
for name, s in scores.items():
    print(f"{name:25s} Accuracy={s['Accuracy']:.3f}  F1={s['F1']:.3f}  AUC={s['AUC']:.3f}")

best_name = max(scores, key=lambda k: scores[k]["F1"])
best_model = {"Random Forest": rf, "XGBoost": xg, "Régression logistique": lr}[best_name]
print(f"\nModèle retenu : {best_name}")

print("\n=== Importance des variables ===")
if best_name == "Régression logistique":
    importances = pd.Series(np.abs(lr.coef_[0]), index=FEATURES).sort_values(ascending=False)
else:
    importances = pd.Series(best_model.feature_importances_, index=FEATURES).sort_values(ascending=False)
print(importances)

# =====================================================================
# LIVRABLE FINAL : recalcul des features avec TOUT l'historique (jusqu'au 31/12/2024)
# puis application du meilleur modèle -> risque de churn ACTUEL
# =====================================================================
final_features = build_features(ventes, FINAL_REF + pd.Timedelta(days=1))
print(f"\nClients avec au moins un achat (population finale) : {len(final_features)}")

X_final = final_features[FEATURES]
if best_name == "Régression logistique":
    X_final_input = scaler.transform(X_final)
else:
    X_final_input = X_final

final_features["Proba_Churn"] = best_model.predict_proba(X_final_input)[:,1].round(3)
final_features["Churn_Predicted"] = best_model.predict(X_final_input)

# --- CLV : panier moyen x fréquence mensuelle x durée de vie (24 mois) ---
observation_months = (FINAL_REF - pd.Timestamp("2023-01-01")).days / 30.44
final_features["Frequence_Mensuelle"] = final_features["Nb_Achats"] / observation_months
final_features["CLV_estimee"] = (final_features["Panier_Moyen"] * final_features["Frequence_Mensuelle"] * 24).round(2)

print(f"\nTaux de churn actuel (population totale) : {final_features['Churn_Predicted'].mean()*100:.1f}%")
print(f"CLV moyenne (non à risque) : {final_features[final_features['Churn_Predicted']==0]['CLV_estimee'].mean():.2f}")
print(f"CLV moyenne (à risque) : {final_features[final_features['Churn_Predicted']==1]['CLV_estimee'].mean():.2f}")

deliverable = final_features[["Customer_ID","Proba_Churn","Churn_Predicted","CLV_estimee"]].sort_values("Proba_Churn", ascending=False)
deliverable.to_csv("/home/claude/m6_v2/predictions_churn.csv", index=False)
final_features.to_csv("/home/claude/m6_v2/clients_complet.csv", index=False)

print("\nTop 10 clients à risque :")
print(deliverable.head(10).to_string(index=False))

with open("/home/claude/m6_v2/resume_resultats.txt","w") as f:
    f.write(f"METHODE: validation temporelle (cutoff {CUTOFF.date()})\n")
    f.write(f"Population entrainement: {len(train_features)} clients ayant achete avant cutoff\n")
    f.write(f"Taux de churn (fenetre future, entrainement): {train_features['Churn'].mean()*100:.1f}%\n\n")
    for name,s in scores.items():
        f.write(f"{name}: Accuracy={s['Accuracy']:.3f} F1={s['F1']:.3f} AUC={s['AUC']:.3f}\n")
    f.write(f"\nModele retenu: {best_name}\n")
    f.write(f"\nImportance variables:\n{importances.to_string()}\n")
    f.write(f"\n--- LIVRABLE FINAL (toutes ventes jusqu'au 31/12/2024) ---\n")
    f.write(f"Population: {len(final_features)} clients avec historique d'achat\n")
    f.write(f"Taux de churn actuel predit: {final_features['Churn_Predicted'].mean()*100:.1f}%\n")
    f.write(f"CLV moyenne non a risque: {final_features[final_features['Churn_Predicted']==0]['CLV_estimee'].mean():.2f}\n")
    f.write(f"CLV moyenne a risque: {final_features[final_features['Churn_Predicted']==1]['CLV_estimee'].mean():.2f}\n")
