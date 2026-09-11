"""
M2 - Nettoyage et préparation des données (responsable : Toky)

Applique les règles de docs/regles_donnees.md et produit dans data/processed/ :
    - ventes_fusionnees.csv  : une ligne par vente (vente + client + produit)
    - clients_agreges.csv    : une ligne par client (indicateurs d'achat, RFM)
    - marketing_nettoye.csv  : campagnes avec dates converties

Utilisation (depuis la racine du dépôt) :
    python src/nettoyage.py
    python src/nettoyage.py --source data/generated   (plus tard, pour le jeu étendu)
"""

import argparse
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Chargement
# ---------------------------------------------------------------------------
def charger(source: Path):
    clients = pd.read_csv(source / "customers_data.csv", parse_dates=["Join_Date"])
    produits = pd.read_csv(source / "products_data.csv")
    ventes = pd.read_csv(source / "sales_data.csv", parse_dates=["Date"])
    marketing = pd.read_csv(source / "marketing_data.csv", parse_dates=["Start_Date", "End_Date"])
    return clients, produits, ventes, marketing


# ---------------------------------------------------------------------------
# Contrôles qualité
# ---------------------------------------------------------------------------
def controler(nom, df, cle):
    print(f"\n--- {nom} : {df.shape[0]} lignes, {df.shape[1]} colonnes")
    manquants = df.isna().sum()
    manquants = manquants[manquants > 0]
    print("Valeurs manquantes :", "aucune" if manquants.empty else manquants.to_dict())
    print("Doublons (lignes entières) :", int(df.duplicated().sum()))
    print(f"Doublons sur {cle} :", int(df[cle].duplicated().sum()))


def controler_references(clients, produits, ventes):
    clients_inconnus = set(ventes["Customer_ID"]) - set(clients["Customer_ID"])
    produits_inconnus = set(ventes["Product_ID"]) - set(produits["Product_ID"])
    print("\n--- Intégrité des références")
    print("Ventes avec un client inconnu :", clients_inconnus or "aucune")
    print("Ventes avec un produit inconnu :", produits_inconnus or "aucune")


# ---------------------------------------------------------------------------
# Règles de nettoyage
# ---------------------------------------------------------------------------
def corriger_sale_price(ventes, produits):
    """Règle 1 : Sale_Price = Price x Quantity."""
    v = ventes.merge(produits[["Product_ID", "Price"]], on="Product_ID", how="left")
    attendu = (v["Price"] * v["Quantity"]).round(2)
    a_corriger = v["Sale_Price"].round(2) != attendu
    print("\n--- Règle 1 : correction de Sale_Price")
    if a_corriger.any():
        print(v.loc[a_corriger, ["Sale_ID", "Price", "Quantity", "Sale_Price"]]
              .assign(Sale_Price_corrige=attendu[a_corriger]).to_string(index=False))
    else:
        print("Aucune correction nécessaire")
    ventes = ventes.copy()
    ventes["Sale_Price"] = attendu.values
    return ventes


def verifier_marketing(marketing):
    print("\n--- Contrôles marketing")
    incoherent = marketing["End_Date"] < marketing["Start_Date"]
    print("Campagnes avec End_Date avant Start_Date :", int(incoherent.sum()))
    trop_clics = marketing["Clicks"] > marketing["Impressions"]
    print("Campagnes avec plus de clics que d'impressions :", int(trop_clics.sum()))
    trop_conv = marketing["Conversions"] > marketing["Clicks"]
    print("Campagnes avec plus de conversions que de clics :", int(trop_conv.sum()))
    return marketing


# ---------------------------------------------------------------------------
# Construction des fichiers de sortie
# ---------------------------------------------------------------------------
def construire_ventes_fusionnees(ventes, clients, produits):
    colonnes_clients = ["Customer_ID", "Age", "Gender", "Location", "Join_Date"]
    df = (ventes
          .merge(clients[colonnes_clients], on="Customer_ID", how="left")
          .merge(produits, on="Product_ID", how="left"))
    ordre = ["Sale_ID", "Date", "Customer_ID", "Age", "Gender", "Location", "Join_Date",
             "Product_ID", "Product_Name", "Category", "Brand", "Price", "Quantity",
             "Sale_Price", "Channel"]
    return df[ordre].sort_values("Date").reset_index(drop=True)


def construire_clients_agreges(ventes_f, clients):
    date_ref = ventes_f["Date"].max()   # dernière date du jeu de données

    achats = ventes_f.groupby("Customer_ID").agg(
        Nb_Achats=("Sale_ID", "count"),
        Montant_Total=("Sale_Price", "sum"),
        Premier_Achat=("Date", "min"),
        Dernier_Achat=("Date", "max"),
    )
    achats["Panier_Moyen"] = achats["Montant_Total"] / achats["Nb_Achats"]
    achats["Recence_Jours"] = (date_ref - achats["Dernier_Achat"]).dt.days

    # Part de chaque catégorie dans le montant dépensé (%)
    parts_cat = (ventes_f.pivot_table(index="Customer_ID", columns="Category",
                                      values="Sale_Price", aggfunc="sum", fill_value=0))
    parts_cat = parts_cat.div(parts_cat.sum(axis=1), axis=0) * 100
    ordre_cat = ["Clothing", "Footwear", "Outerwear", "Accessories"]
    parts_cat = parts_cat[[c for c in ordre_cat if c in parts_cat.columns]
                          + [c for c in parts_cat.columns if c not in ordre_cat]]
    parts_cat.columns = [f"Part_{c}" for c in parts_cat.columns]

    # Canal préféré (en nombre d'achats) et part des achats en ligne (%)
    canaux = ventes_f.groupby("Customer_ID")["Channel"]
    canal = pd.DataFrame({
        "Canal_Prefere": canaux.agg(lambda s: s.value_counts().idxmax()),
        "Part_Online": canaux.agg(lambda s: (s == "Online").mean() * 100),
    })

    df = (clients.drop(columns=["Name"])
          .merge(achats, on="Customer_ID", how="left")
          .merge(parts_cat, on="Customer_ID", how="left")
          .merge(canal, on="Customer_ID", how="left"))

    df["Anciennete_Jours"] = (date_ref - df["Join_Date"]).dt.days

    # Règle 3 : clients sans achat conservés, indicateurs à 0 (dates et récence vides)
    colonnes_zero = ["Nb_Achats", "Montant_Total", "Panier_Moyen", "Part_Online"] + list(parts_cat.columns)
    df[colonnes_zero] = df[colonnes_zero].fillna(0)
    df["Nb_Achats"] = df["Nb_Achats"].astype(int)
    df["Recence_Jours"] = df["Recence_Jours"].astype("Int64")
    numeriques = df.select_dtypes("float").columns
    df[numeriques] = df[numeriques].round(2)

    ordre = (["Customer_ID", "Age", "Gender", "Location", "Join_Date", "Anciennete_Jours",
              "Total_Spent", "Nb_Achats", "Montant_Total", "Panier_Moyen",
              "Premier_Achat", "Dernier_Achat", "Recence_Jours"]
             + list(parts_cat.columns) + ["Canal_Prefere", "Part_Online"])
    return df[ordre], date_ref


# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Nettoyage des données SMD (M2)")
    parser.add_argument("--source", default="data/raw", help="dossier des 4 CSV d'entrée")
    parser.add_argument("--dest", default="data/processed", help="dossier de sortie")
    args = parser.parse_args()

    source, dest = RACINE / args.source, RACINE / args.dest
    dest.mkdir(parents=True, exist_ok=True)

    clients, produits, ventes, marketing = charger(source)

    controler("customers_data", clients, "Customer_ID")
    controler("products_data", produits, "Product_ID")
    controler("sales_data", ventes, "Sale_ID")
    controler("marketing_data", marketing, "Campaign_ID")
    controler_references(clients, produits, ventes)

    ventes = corriger_sale_price(ventes, produits)
    marketing = verifier_marketing(marketing)

    ventes_f = construire_ventes_fusionnees(ventes, clients, produits)
    clients_a, date_ref = construire_clients_agreges(ventes_f, clients)

    sans_achat = clients_a.loc[clients_a["Nb_Achats"] == 0, "Customer_ID"].tolist()
    print("\n--- Règle 3 : clients sans achat :", sans_achat or "aucun")

    ventes_f.to_csv(dest / "ventes_fusionnees.csv", index=False)
    clients_a.to_csv(dest / "clients_agreges.csv", index=False)
    marketing.to_csv(dest / "marketing_nettoye.csv", index=False)

    print("\n=== Fichiers produits dans", dest.relative_to(RACINE))
    print(f"ventes_fusionnees.csv : {len(ventes_f)} lignes")
    print(f"clients_agreges.csv   : {len(clients_a)} lignes")
    print(f"marketing_nettoye.csv : {len(marketing)} lignes")
    print(f"\nDate de référence (dernière vente) : {date_ref.date()}")
    print(f"Panier moyen des ventes (pour le ROI de Manassé) : {ventes_f['Sale_Price'].mean():.2f}")


if __name__ == "__main__":
    main()
