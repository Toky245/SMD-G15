# Règles des données (M2)

Responsable : Toky

Ce document fixe les règles de nettoyage appliquées aux données du professeur et décrit les fichiers livrés dans `data/processed/`. Tout le monde s'y réfère avant d'écrire son code. Toute demande de modification (nouvelle colonne, autre règle) passe par Toky.

## Organisation des fichiers

```
data/raw/        -> src/generation.py -> data/generated/          (jeu étendu, même format que raw)
data/generated/  -> src/nettoyage.py  -> data/processed/          (fichiers utilisés par tout le groupe)
data/raw/        -> src/nettoyage.py  -> data/processed/original/ (version 5 lignes, pour le rapport)
```

Personne ne modifie `data/raw/`, `data/generated/` ou `data/processed/` à la main. Si une règle change, on modifie le script et on le relance.

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

Les fichiers de `data/processed/` sont construits à partir du jeu étendu (section 4). Les mêmes fichiers, construits à partir des 5 lignes du professeur, sont dans `data/processed/original/`. Les colonnes sont identiques dans les deux cas.

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

### 4.1 Pourquoi un jeu étendu

Les 5 lignes d'origine ne suffisent pas pour le K-means (M3) ni pour entraîner et tester un modèle de prédiction (M6). Un jeu étendu a donc été généré par `src/generation.py`, avec **exactement les mêmes colonnes** que les fichiers du professeur. Le code écrit sur la version 5 lignes fonctionne sans modification sur le jeu étendu.

### 4.2 Contenu

| Fichier | Lignes | Détail |
|---|---|---|
| customers_data.csv | 805 | les 5 clients d'origine + 800 clients générés |
| products_data.csv | 20 | les 5 produits d'origine + 15 produits (mêmes 4 catégories, marques A à E) |
| sales_data.csv | 5 337 | les 5 ventes d'origine + ventes générées, du 2023-01-01 au 2024-12-31 |
| marketing_data.csv | 50 | les 5 campagnes d'origine + 9 campagnes par canal (Online, In-Store, Social, Email, TV) |

Les lignes d'origine sont conservées telles quelles, y compris l'erreur de la vente 3, qui est corrigée ensuite par `nettoyage.py` comme pour les données brutes.

### 4.3 Méthode de génération

1. **Clients** : chaque client généré se voit attribuer un profil de comportement, qui détermine son âge, son canal d'achat habituel (en ligne ou en magasin), sa fréquence d'achat, sa gamme de prix, ses catégories préférées et sa probabilité d'arrêter d'acheter. Le genre et la ville sont tirés au hasard. Les dates d'inscription vont de 2021 à mi-2024.
2. **Ventes** : pour chaque client, les achats sont tirés jour par jour entre son inscription (ou le 1er janvier 2023) et la fin de la période, selon sa fréquence d'achat. Une variation individuelle est ajoutée pour que deux clients du même profil ne soient pas identiques.
3. **Saisonnalité** : la fréquence d'achat varie selon le mois, avec un creux en février et un pic en novembre-décembre.
4. **Produits achetés** : chaque achat choisit un produit selon les catégories et la gamme de prix préférées du client. La quantité est le plus souvent de 1 ou 2. `Sale_Price = Price × Quantity`.
5. **Churn** : une partie des clients arrête d'acheter à une date aléatoire pendant la période, avec un taux qui varie selon le profil. Certains clients inscrits n'achètent jamais (ils sont traités comme Eva, règle 3).
6. **Total_Spent** : cumul historique = montant des ventes générées + une estimation des achats faits avant 2023, proportionnelle à l'ancienneté du client.
7. **Campagnes** : chaque canal a ses propres caractéristiques (budget, impressions, taux de clic, taux de conversion), avec une variation aléatoire d'une campagne à l'autre. Les contrôles restent respectés : clics inférieurs aux impressions, conversions inférieures aux clics.
8. **Reproductibilité** : la graine aléatoire est fixe (15). Relancer `python src/generation.py` redonne exactement les mêmes données.

Le nombre de profils et leurs caractéristiques ne sont volontairement pas indiqués ici : la segmentation (M3) doit retrouver les groupes à partir des données, sans les connaître à l'avance. Ils seront présentés dans le rapport, pour comparer les segments trouvés aux profils réels.

### 4.4 Valeurs de référence

| Indicateur | Données d'origine | Jeu étendu |
|---|---|---|
| Date de référence (dernière vente) | 2023-01-19 | 2024-12-31 |
| Panier moyen des ventes (ROI de M5) | 76,00 | 90,81 |
| Clients sans achat | 1 | 79 |

### 4.5 Limites à mentionner dans le rapport

Les données générées sont synthétiques : les tendances qu'on y trouve reflètent les hypothèses de génération, pas le comportement de vrais clients. Le jeu étendu sert à démontrer la méthode (segmentation, prédiction, stratégie) ; les conclusions doivent être présentées comme valables sous ces hypothèses.

### 4.6 Commandes

```bash
python src/nettoyage.py --dest data/processed/original
python src/generation.py
python src/nettoyage.py --source data/generated
```
