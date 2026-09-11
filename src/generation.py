"""
M2 - Génération du jeu de données étendu (responsable : Toky)

Les fichiers du professeur ne contiennent que 5 lignes, ce qui est insuffisant pour la
segmentation (M3) et la prédiction (M6). Ce script génère un jeu étendu avec EXACTEMENT
les mêmes colonnes que les fichiers de data/raw/.

Principes :
    - Les 5 lignes d'origine de chaque fichier sont conservées telles quelles au début.
    - Les nouveaux clients suivent 4 profils de comportement différents (âge, canal,
      fréquence d'achat, panier, catégories préférées), pour que la segmentation ait du sens.
    - Les ventes couvrent 2 ans (2023-2024), avec une saisonnalité (pic en novembre-décembre).
    - Une partie des clients arrête d'acheter à une date aléatoire (churn), avec un taux
      différent selon le profil.
    - Les campagnes ont des performances différentes selon le canal.
    - La graine aléatoire est fixe : relancer le script donne exactement les mêmes données.

Sorties (data/generated/) :
    customers_data.csv, products_data.csv, sales_data.csv, marketing_data.csv
    profils_caches.csv  -> profil réel de chaque client généré, UNIQUEMENT pour vérifier
                           après coup si la segmentation retrouve les profils.
                           Ne pas le donner aux autres avant qu'ils aient fini M3.

Utilisation (depuis la racine du dépôt) :
    python src/generation.py
    python src/generation.py --clients 1000
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
GRAINE = 15

DEBUT_VENTES = pd.Timestamp("2023-01-01")
FIN_VENTES = pd.Timestamp("2024-12-31")

VILLES = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
          "Philadelphia", "San Antonio", "San Diego", "Dallas", "Miami"]

PRENOMS_F = ["Emma", "Olivia", "Sophia", "Mia", "Chloe", "Grace", "Lily", "Zoe", "Nora", "Ella",
             "Aria", "Hannah", "Laura", "Julia", "Sarah", "Nina", "Clara", "Lucy", "Ruby", "Anna"]
PRENOMS_M = ["Liam", "Noah", "Ethan", "Lucas", "Mason", "Leo", "Jack", "Ryan", "Adam", "Owen",
             "Henry", "Samuel", "Daniel", "Nathan", "Oscar", "Hugo", "David", "Victor", "Paul", "Max"]

# Catalogue : les 5 produits d'origine (101-105) + 15 nouveaux
NOUVEAUX_PRODUITS = [
    (106, "Shirt", "Clothing", 40.0, "Brand A"),
    (107, "Dress", "Clothing", 65.0, "Brand B"),
    (108, "Hoodie", "Clothing", 55.0, "Brand C"),
    (109, "Shorts", "Clothing", 30.0, "Brand E"),
    (110, "Boots", "Footwear", 110.0, "Brand D"),
    (111, "Sandals", "Footwear", 35.0, "Brand E"),
    (112, "Running Shoes", "Footwear", 85.0, "Brand C"),
    (113, "Coat", "Outerwear", 180.0, "Brand D"),
    (114, "Parka", "Outerwear", 150.0, "Brand B"),
    (115, "Blazer", "Outerwear", 130.0, "Brand A"),
    (116, "Belt", "Accessories", 20.0, "Brand A"),
    (117, "Scarf", "Accessories", 18.0, "Brand E"),
    (118, "Bag", "Accessories", 60.0, "Brand B"),
    (119, "Sunglasses", "Accessories", 45.0, "Brand C"),
    (120, "Cap", "Accessories", 15.0, "Brand E"),
]

# Profils de comportement
#   poids        : part des clients dans ce profil
#   age          : (moyenne, écart-type, min, max)
#   online       : probabilité qu'un achat soit fait en ligne
#   achats_mois  : nombre moyen d'achats par mois quand le client est actif
#   categories   : préférence par catégorie (Clothing, Footwear, Outerwear, Accessories)
#   gamme        : préférence pour les produits chers (>0) ou bon marché (<0)
#   quantite     : quantité moyenne par achat
#   churn        : probabilité que le client arrête d'acheter pendant la période
PROFILS = {
    "Jeunes connectés": dict(poids=0.30, age=(23, 3, 18, 30), online=0.85, achats_mois=0.55,
                             categories=[0.40, 0.30, 0.05, 0.25], gamme=-1.0, quantite=1.6, churn=0.40),
    "Actifs premium": dict(poids=0.20, age=(38, 5, 28, 50), online=0.50, achats_mois=0.30,
                           categories=[0.25, 0.20, 0.45, 0.10], gamme=1.5, quantite=1.1, churn=0.20),
    "Fidèles en magasin": dict(poids=0.25, age=(52, 7, 40, 70), online=0.15, achats_mois=0.35,
                               categories=[0.50, 0.20, 0.20, 0.10], gamme=0.3, quantite=1.3, churn=0.12),
    "Occasionnels": dict(poids=0.25, age=(34, 9, 18, 60), online=0.60, achats_mois=0.10,
                         categories=[0.25, 0.20, 0.10, 0.45], gamme=-0.5, quantite=1.2, churn=0.55),
}

# Saisonnalité : coefficient multiplicateur par mois (janvier = indice 0)
SAISON = np.array([0.8, 0.7, 0.9, 1.0, 1.0, 1.1, 1.0, 0.9, 1.0, 1.0, 1.5, 1.8])

# Campagnes : caractéristiques par canal
#   budget (min, max), impressions par unité de budget, CTR, taux de conversion (moyens)
CANAUX_CAMPAGNE = {
    "Online":   dict(budget=(800, 2500), impr_par_ar=45, ctr=0.040, conv=0.070),
    "In-Store": dict(budget=(1000, 3000), impr_par_ar=20, ctr=0.018, conv=0.180),
    "Social":   dict(budget=(1000, 3500), impr_par_ar=25, ctr=0.035, conv=0.120),
    "Email":    dict(budget=(300, 1000), impr_par_ar=40, ctr=0.050, conv=0.050),
    "TV":       dict(budget=(2500, 6000), impr_par_ar=22, ctr=0.050, conv=0.080),
}


# ---------------------------------------------------------------------------
def generer_produits(produits_origine):
    nouveaux = pd.DataFrame(NOUVEAUX_PRODUITS, columns=produits_origine.columns)
    return pd.concat([produits_origine, nouveaux], ignore_index=True)


def generer_clients(rng, clients_origine, n):
    noms_profils = list(PROFILS)
    poids = np.array([PROFILS[p]["poids"] for p in noms_profils])
    profils = rng.choice(noms_profils, size=n, p=poids / poids.sum())

    lignes = []
    premier_id = clients_origine["Customer_ID"].max() + 1
    for i, profil in enumerate(profils):
        moy, et, amin, amax = PROFILS[profil]["age"]
        age = int(np.clip(rng.normal(moy, et), amin, amax))
        genre = rng.choice(["Female", "Male"])
        prenom = rng.choice(PRENOMS_F if genre == "Female" else PRENOMS_M)
        # Inscriptions entre 2021 et mi-2024
        inscription = pd.Timestamp("2021-01-01") + pd.Timedelta(days=int(rng.integers(0, 1277)))
        lignes.append(dict(Customer_ID=premier_id + i, Name=prenom, Age=age, Gender=genre,
                           Location=rng.choice(VILLES), Join_Date=inscription, Profil=profil))
    return pd.DataFrame(lignes)


def choisir_produit(rng, produits, profil):
    p = PROFILS[profil]
    pref_cat = dict(zip(["Clothing", "Footwear", "Outerwear", "Accessories"], p["categories"]))
    prix_norm = (produits["Price"] - produits["Price"].mean()) / produits["Price"].std()
    score = produits["Category"].map(pref_cat) * np.exp(p["gamme"] * prix_norm)
    return produits.iloc[rng.choice(len(produits), p=(score / score.sum()).values)]


def generer_ventes(rng, clients, produits, premier_sale_id):
    ventes = []
    sale_id = premier_sale_id
    for c in clients.itertuples():
        p = PROFILS[c.Profil]
        debut = max(c.Join_Date, DEBUT_VENTES)
        fin = FIN_VENTES
        # Churn : le client arrête d'acheter à une date aléatoire
        if rng.random() < p["churn"]:
            jours_possibles = (FIN_VENTES - debut).days - 90
            if jours_possibles > 60:
                fin = debut + pd.Timedelta(days=int(rng.integers(60, jours_possibles)))

        # Achats jour par jour selon un taux mensuel ajusté par la saison
        jours = pd.date_range(debut, fin, freq="D")
        taux_jour = p["achats_mois"] / 30 * SAISON[jours.month - 1]
        # Hétérogénéité individuelle : chaque client achète un peu plus ou moins que son profil
        taux_jour = taux_jour * rng.lognormal(0, 0.35)
        dates_achat = jours[rng.random(len(jours)) < taux_jour]

        for d in dates_achat:
            prod = choisir_produit(rng, produits, c.Profil)
            quantite = max(1, int(rng.poisson(p["quantite"] - 1) + 1))
            canal = "Online" if rng.random() < p["online"] else "In-Store"
            ventes.append(dict(Sale_ID=sale_id, Product_ID=prod.Product_ID, Customer_ID=c.Customer_ID,
                               Date=d, Quantity=quantite,
                               Sale_Price=round(prod.Price * quantite, 2), Channel=canal))
            sale_id += 1
    return pd.DataFrame(ventes)


def calculer_total_spent(rng, clients, ventes):
    """Total_Spent = cumul historique : achats générés + achats avant 2023 (estimés)."""
    montant = ventes.groupby("Customer_ID")["Sale_Price"].sum()
    total = clients["Customer_ID"].map(montant).fillna(0)
    mois_avant_2023 = ((DEBUT_VENTES - clients["Join_Date"]).dt.days / 30).clip(lower=0)
    historique = mois_avant_2023 * rng.uniform(5, 25, size=len(clients))
    return (total + historique).round(2)


def generer_campagnes(rng, campagnes_origine, n_par_canal):
    lignes = []
    cid = campagnes_origine["Campaign_ID"].max() + 1
    for canal, c in CANAUX_CAMPAGNE.items():
        for _ in range(n_par_canal):
            debut = DEBUT_VENTES + pd.Timedelta(days=int(rng.integers(0, 700)))
            fin = debut + pd.Timedelta(days=int(rng.integers(7, 35)))
            budget = round(float(rng.uniform(*c["budget"])), -1)
            impressions = int(budget * c["impr_par_ar"] * rng.uniform(0.7, 1.3))
            clics = int(impressions * np.clip(rng.normal(c["ctr"], c["ctr"] * 0.25), 0.002, 0.2))
            conversions = int(clics * np.clip(rng.normal(c["conv"], c["conv"] * 0.25), 0.005, 0.5))
            lignes.append(dict(Campaign_ID=cid, Channel=canal, Start_Date=debut.date(),
                               End_Date=min(fin, FIN_VENTES).date(), Budget=budget,
                               Impressions=impressions, Clicks=clics, Conversions=conversions))
            cid += 1
    nouvelles = pd.DataFrame(lignes).sort_values("Start_Date")
    nouvelles["Campaign_ID"] = range(campagnes_origine["Campaign_ID"].max() + 1,
                                     campagnes_origine["Campaign_ID"].max() + 1 + len(nouvelles))
    return pd.concat([campagnes_origine, nouvelles], ignore_index=True)


# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Génération du jeu de données étendu (M2)")
    parser.add_argument("--clients", type=int, default=800, help="nombre de nouveaux clients")
    parser.add_argument("--campagnes", type=int, default=9, help="nouvelles campagnes par canal")
    parser.add_argument("--dest", default="data/generated")
    args = parser.parse_args()

    rng = np.random.default_rng(GRAINE)
    raw = RACINE / "data/raw"
    dest = RACINE / args.dest
    dest.mkdir(parents=True, exist_ok=True)

    clients_o = pd.read_csv(raw / "customers_data.csv", parse_dates=["Join_Date"])
    produits_o = pd.read_csv(raw / "products_data.csv")
    ventes_o = pd.read_csv(raw / "sales_data.csv", parse_dates=["Date"])
    campagnes_o = pd.read_csv(raw / "marketing_data.csv")

    produits = generer_produits(produits_o)
    nouveaux_clients = generer_clients(rng, clients_o, args.clients)
    nouvelles_ventes = generer_ventes(rng, nouveaux_clients, produits,
                                      premier_sale_id=ventes_o["Sale_ID"].max() + 1)
    nouveaux_clients["Total_Spent"] = calculer_total_spent(rng, nouveaux_clients, nouvelles_ventes)

    colonnes_clients = list(clients_o.columns)
    clients = pd.concat([clients_o, nouveaux_clients[colonnes_clients]], ignore_index=True)
    ventes = pd.concat([ventes_o, nouvelles_ventes], ignore_index=True)
    campagnes = generer_campagnes(rng, campagnes_o, args.campagnes)

    clients.to_csv(dest / "customers_data.csv", index=False, date_format="%Y-%m-%d")
    produits.to_csv(dest / "products_data.csv", index=False)
    ventes.to_csv(dest / "sales_data.csv", index=False, date_format="%Y-%m-%d")
    campagnes.to_csv(dest / "marketing_data.csv", index=False)
    nouveaux_clients[["Customer_ID", "Profil"]].to_csv(dest / "profils_caches.csv", index=False)

    print("=== Jeu étendu généré dans", dest.relative_to(RACINE))
    print(f"Clients   : {len(clients)} (dont 5 d'origine)")
    print(f"Produits  : {len(produits)} (dont 5 d'origine)")
    print(f"Ventes    : {len(ventes)} (dont 5 d'origine), du {ventes['Date'].min().date()} au {ventes['Date'].max().date()}")
    print(f"Campagnes : {len(campagnes)} (dont 5 d'origine)")
    print("\nRépartition des profils :")
    print(nouveaux_clients["Profil"].value_counts().to_string())


if __name__ == "__main__":
    main()
