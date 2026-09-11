# Règles des données (M2)

Responsable : Toky

Ce document fixe les règles de nettoyage appliquées aux données du professeur et décrit les fichiers livrés dans `data/processed/`. Tout le monde s'y réfère avant d'écrire son code. Toute demande de modification (nouvelle colonne, autre règle) passe par Toky.

## 1. Données sources

Les fichiers originaux sont dans `data/raw/` et ne doivent jamais être modifiés.

| Fichier | Contenu | Lignes |
|---|---|---|
| `customers_data.csv` | Clients | 5 |
| `products_data.csv` | Produits | 5 |
| `sales_data.csv` | Ventes | 5 |
| `marketing_data.csv` | Campagnes | 5 |

## 2. Règles de nettoyage

Ces règles sont appliquées automatiquement par `src/nettoyage.py`.

1. **Sale_Price** = prix total de la vente (`Price × Quantity`). La vente 3 est corrigée : 3 Sneakers × 30 = 90 (et non 30).
2. **Total_Spent** = dépenses historiques du client depuis son inscription. Cette colonne ne correspond pas aux ventes du fichier (Alice : 500 contre 140 dans les ventes). Les montants réels calculés à partir des ventes sont dans une colonne séparée : `Montant_Total`.
3. **Client sans achat** : Eva (client 2005) est conservée et marquée comme client sans achat (`Nb_Achats = 0`).
4. **Dates** : toutes au format `AAAA-MM-JJ`.
5. **Canaux** : les ventes n'ont que `Online` et `In-Store`, les campagnes ont aussi `Social`, `Email` et `TV`. Il n'y a pas de lien direct entre une campagne et une vente.
6. **Colonne Name** : exclue des fichiers d'analyse, car elle n'apporte rien à la segmentation ni à la prédiction.

## 3. Fichiers livrés dans `data/processed/`

### 3.1 `ventes_fusionnees.csv` (une ligne par vente)

| Colonne | Description |
|---|---|
| Sale_ID | Identifiant de la vente |
| Date | Date de la vente |
| Customer_ID | Identifiant du client |
| Age | Âge du client |
| Gender | Genre du client |
| Location | Ville du client |
| Join_Date | Date d'inscription du client |
| Product_ID | Identifiant du produit |
| Product_Name | Nom du produit |
| Category | Catégorie (Clothing, Footwear, Outerwear, Accessories) |
| Brand | Marque |
| Price | Prix unitaire |
| Quantity | Quantité achetée |
| Sale_Price | Prix total de la vente (Price × Quantity) |
| Channel | Canal de vente (Online, In-Store) |

### 3.2 `clients_agreges.csv` (une ligne par client)

| Colonne | Description |
|---|---|
| Customer_ID | Identifiant du client |
| Age | Âge |
| Gender | Genre |
| Location | Ville |
| Join_Date | Date d'inscription |
| Anciennete_Jours | Nombre de jours depuis l'inscription |
| Total_Spent | Dépenses historiques (donnée d'origine) |
| Nb_Achats | Nombre d'achats (fréquence du RFM) |
| Montant_Total | Somme des Sale_Price du client (montant du RFM) |
| Panier_Moyen | Montant_Total / Nb_Achats |
| Premier_Achat | Date du premier achat |
| Dernier_Achat | Date du dernier achat |
| Recence_Jours | Jours depuis le dernier achat, par rapport à la dernière date du jeu de données (récence du RFM) |
| Part_Clothing | Part du montant dépensé en Clothing (%) |
| Part_Footwear | Part du montant dépensé en Footwear (%) |
| Part_Outerwear | Part du montant dépensé en Outerwear (%) |
| Part_Accessories | Part du montant dépensé en Accessories (%) |
| Canal_Prefere | Canal le plus utilisé, en nombre d'achats (Online ou In-Store) |
| Part_Online | Part des achats faits en ligne, en nombre d'achats (%) |

Les colonnes `Part_` des catégories sont calculées sur le **montant dépensé**, pas sur le nombre d'achats. Exemple : Alice a dépensé 50 en Clothing et 90 en Footwear, donc Part_Clothing = 35,71 % et Part_Footwear = 64,29 %.

Pour un client sans achat, les colonnes d'achats valent 0, et les dates ainsi que Recence_Jours sont vides.

### 3.3 `marketing_nettoye.csv`

Mêmes colonnes que `marketing_data.csv`, avec les dates converties au format `AAAA-MM-JJ`.

## 4. Jeu de données étendu

Les 5 lignes d'origine ne suffisent pas pour le K-means et les modèles de prédiction. Un jeu étendu sera généré avec **exactement les mêmes colonnes** :

- 500 à 1000 clients et plusieurs milliers de ventes ;
- ventes réparties sur 1 à 2 ans, pour permettre le calcul du churn ;
- profils de clients volontairement différents, pour que la segmentation ait du sens ;
- une partie des clients qui arrêtent d'acheter.

La méthode de génération sera décrite dans ce fichier une fois le jeu produit. Le code écrit sur la version 5 lignes fonctionnera sans modification sur le jeu étendu.
