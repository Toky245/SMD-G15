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

clients = pd.read_csv("/mnt/user-data/uploads/clients_agreges.csv", parse_dates=["Join_Date","Premier_Achat","Dernier_Achat"])

# --- Recence pour les clients sans achat : ancienneté depuis inscription (comme pour Eva précédemment) ---
clients["Recence_Jours_Final"] = clients["Recence_Jours"]
no_purchase = clients["Recence_Jours"].isna()
clients.loc[no_purchase, "Recence_Jours_Final"] = clients.loc[no_purchase, "Anciennete_Jours"]
print(f"Clients sans achat : {no_purchase.sum()} (Récence = ancienneté depuis inscription)")

# --- Règle de churn ---
CHURN_THRESHOLD_DAYS = 90
clients["Churn"] = (clients["Recence_Jours_Final"] > CHURN_THRESHOLD_DAYS).astype(int)
print(f"\nRépartition Churn :\n{clients['Churn'].value_counts()}")
print(f"Taux de churn : {clients['Churn'].mean()*100:.1f}%")

# --- CLV : panier moyen x fréquence mensuelle réelle x durée de vie (24 mois) ---
reference_date = pd.to_datetime("2024-12-31") + pd.Timedelta(days=1)
observation_start = pd.to_datetime("2023-01-01")
observation_months = (reference_date - observation_start).days / 30.44

clients["Frequence_Mensuelle"] = clients["Nb_Achats"] / observation_months
LIFESPAN_MONTHS = 24
clients["CLV_estimee"] = (clients["Panier_Moyen"].fillna(0) * clients["Frequence_Mensuelle"] * LIFESPAN_MONTHS).round(2)

# --- Modèles ---
FEATURES = ["Recence_Jours_Final", "Nb_Achats", "Montant_Total", "Age"]
X = clients[FEATURES].fillna(0)
y = clients["Churn"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

lr = LogisticRegression(random_state=42, max_iter=1000).fit(X_train_scaled, y_train)
rf = RandomForestClassifier(n_estimators=200, random_state=42).fit(X_train, y_train)
xg = xgb.XGBClassifier(random_state=42, eval_metric="logloss").fit(X_train, y_train)

scores = {}
for name, model, Xte in [("Régression logistique", lr, X_test_scaled), ("Random Forest", rf, X_test), ("XGBoost", xg, X_test)]:
    pred = model.predict(Xte)
    scores[name] = {"Accuracy": accuracy_score(y_test, pred), "F1": f1_score(y_test, pred, zero_division=0), "AUC": roc_auc_score(y_test, pred)}

print("\n=== Comparaison des modèles (vraies données, 805 clients) ===")
for name, s in scores.items():
    print(f"{name:25s} Accuracy={s['Accuracy']:.3f}  F1={s['F1']:.3f}  AUC={s['AUC']:.3f}")

best_name = max(scores, key=lambda k: scores[k]["F1"])
best_model = {"Random Forest": rf, "XGBoost": xg, "Régression logistique": lr}[best_name]
print(f"\nModèle retenu : {best_name}")

print("\n=== Importance des variables (Random Forest) ===")
importances = pd.Series(rf.feature_importances_, index=FEATURES).sort_values(ascending=False)
print(importances)

# --- Prédictions finales ---
X_all_scaled = scaler.transform(X) if best_name == "Régression logistique" else X
clients["Proba_Churn"] = best_model.predict_proba(X_all_scaled)[:,1].round(3)
clients["Churn_Predicted"] = best_model.predict(X_all_scaled)

print(f"\nCLV moyenne (clients actifs) : {clients[clients['Churn']==0]['CLV_estimee'].mean():.2f}")
print(f"CLV moyenne (clients churnés) : {clients[clients['Churn']==1]['CLV_estimee'].mean():.2f}")

# --- Livrable exact demandé par Toky : Customer_ID, Proba_Churn (+ bonus CLV) ---
deliverable = clients[["Customer_ID","Proba_Churn","Churn_Predicted","CLV_estimee"]].sort_values("Proba_Churn", ascending=False)
deliverable.to_csv("/home/claude/m6_final/predictions_churn.csv", index=False)
clients.to_csv("/home/claude/m6_final/clients_avec_predictions_complet.csv", index=False)

print("\nTop 10 clients à risque :")
print(deliverable.head(10).to_string(index=False))

with open("/home/claude/m6_final/resultats_resume.txt","w") as f:
    f.write(f"MODELE RETENU: {best_name}\n")
    for name,s in scores.items():
        f.write(f"{name}: Accuracy={s['Accuracy']:.3f} F1={s['F1']:.3f} AUC={s['AUC']:.3f}\n")
    f.write(f"\nImportance variables (RF):\n{importances.to_string()}\n")
    f.write(f"\nTaux de churn global: {clients['Churn'].mean()*100:.1f}%\n")
    f.write(f"CLV moyenne actifs: {clients[clients['Churn']==0]['CLV_estimee'].mean():.2f}\n")
    f.write(f"CLV moyenne churnes: {clients[clients['Churn']==1]['CLV_estimee'].mean():.2f}\n")
    f.write(f"Nb clients: {len(clients)}, Nb churnes: {clients['Churn'].sum()}\n")
