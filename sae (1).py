import csv
import os


# ==============================================================================
# 1. CHARGEMENT
# ==============================================================================

def charger_donnees_total(file):
    """Charge le fichier CSV et retourne une liste de dictionnaires."""
    with open(file, "r", encoding="latin-1") as fich:
        data = csv.DictReader(fich, delimiter=";")

        print("")
        return list(data)


def charger_plage_data(file, debut, fin):
    """
    Charge une plage de lignes du fichier CSV.
    La première ligne de données = 1, hors en-tête.
    """
    with open(file, "r", encoding="latin-1") as fich:
        data = csv.DictReader(fich, delimiter=";")
        data = list(data)
    print(f"Plage de données chargée (lignes {debut} à {fin}) :")
    return data[debut - 1:fin]


def charger_donnees_var(file, mode, *args):
    """
    Charge le fichier CSV, filtre les colonnes (keep/drop)
    et affiche directement le résultat en tableau.
    """
    data = charger_donnees_total(file)

    if not data:
        print("Fichier vide.")
        return []

    colonnes = data[0].keys()

    for col in args:
        if col not in colonnes:
            print(f"La variable '{col}' n'existe pas dans le fichier.")
            return []

    if mode == "keep":
        data_filtre = keep_var(data, *args)

    elif mode == "drop":
        data_filtre = drop_var(data, *args)

    else:
        print(f"Mode '{mode}' invalide. Utilisez 'keep' ou 'drop'.")
        return []
  
    return data_filtre


def keep_var(data, *variables):
    """Garde uniquement certaines colonnes."""
    return [{k: v for k, v in row.items() if k in variables} for row in data]


def drop_var(data, *variables):
    """Supprime certaines colonnes."""
    return [{k: v for k, v in row.items() if k not in variables} for row in data]


# ==============================================================================
# 2. AFFICHAGE
# ==============================================================================

def afficher_donnees_installation(data):
    """Affiche les données d'installation  (colonnes principales)."""
    if not data:
        print("Aucune donnée à afficher.")
        return

    # En-têtes
    print(f"{'numero':<15} "
          f"{'nom':<40} "
          f"{'cp':<6} "
          f"{'commune':<15} "
          f"{'install_nb':<12} "
          f"{'acces_handi':<12} "
          f"{'acces_transp_commun':<20} "
          f"{'reg_nom':<20} "
          f"{'dens_niveau':<12} "
          f"{'dens_lib':<15}")
    print("-" * 157)

    # Données
    for ligne in data:
        print(f"{ligne.get('numero', ''):<15} "
              f"{ligne.get('nom', ''):<40} "
              f"{ligne.get('cp', ''):<6} "
              f"{ligne.get('commune', ''):<15} "
              f"{ligne.get('install_nb', ''):<12} "
              f"{ligne.get('acces_handi', ''):<12} "
              f"{ligne.get('acces_transp_commun', ''):<20} "
              f"{ligne.get('reg_nom', ''):<20} "
              f"{ligne.get('dens_niveau', ''):<12} "
              f"{ligne.get('dens_lib', ''):<15}")

    print("-" * 157)
    print(f"  {len(data)} ligne(s) affichée(s).")


# ==============================================================================
# 3. MENU 
# ==============================================================================

def menu_visualisation():
    print("\n--- MENU ---")
    print("1. Afficher les données complètes")
    print("2. Afficher certaines colonnes (KEEP)")
    print("3. Supprimer certaines colonnes (DROP)")
    print("4. Afficher une plage de lignes")
    print("0. Quitter")
    return input("Votre choix : ")


def gestion_visualisation(file):
    data = charger_donnees_total(file)
    choix = ""
    while choix != "0":
        choix = menu_visualisation()

        if choix == "1":
            afficher_donnees_installation(data)

        elif choix == "2":
            cols = input("Colonnes à garder (séparées par des virgules) : ").split(",")
            data_filtre = keep_var(data, *cols)
            afficher_donnees_installation(data_filtre)

        elif choix == "3":
            cols = input("Colonnes à supprimer (séparées par des virgules) : ").split(",")
            data_filtre = drop_var(data, *cols)
            afficher_donnees_installation(data_filtre)

        elif choix == "4":
            debut = int(input("Ligne début (1 = première ligne de données) : "))
            fin = int(input("Ligne fin : "))
            data_plage = data[debut - 1:fin]
            afficher_donnees_installation(data_plage)

        elif choix == "0":
            print("Fin du programme.")

        else:
            print("Choix invalide.")


# ==============================================================================
# 4. ANOMALIES
# ==============================================================================

def verifier_identifiant(data, colonne):
    """Vérifie qu'une colonne est bien un identifiant unique"""
    valeurs = [row.get(colonne, '') for row in data]
    valeurs_non_vides = [v for v in valeurs if v != '']
    uniques = set(valeurs_non_vides)

    if len(valeurs_non_vides) != len(uniques):
        print(f"Doublons détectés dans la colonne '{colonne}'.")
        return False
    else:
        print(f"Identifiant '{colonne}' valide (unique).")
        return True


def verifier_intervalle(data, colonne, min_val, max_val):
    """Retourne les lignes où la valeur est hors de l'intervalle min_val, max_val"""
    erreurs = []
    for index, row in enumerate(data):
        val = row.get(colonne, '')
        if val != '':
            try:
                val_num = float(val)
                if val_num < min_val or val_num > max_val:
                    erreurs.append((index, val))
            except ValueError:
                erreurs.append((index, val))
    return erreurs


def verifier_modalites(data, colonne, liste_valeurs):
    """Retourne le nombre d'erreurs de modalités."""
    erreurs = []
    for index, row in enumerate(data):
        val = row.get(colonne, '')
        if val != '' and val not in liste_valeurs:
            erreurs.append((index, val))
    return print("Les erreurs détectées sont :", erreurs, "\nOn en compte ", len(erreurs))


def verifier_cle_etrangere(data1, colonne1, data2, colonne2):
    """Vérifie que les valeurs de colonne1 (dans data1) existent bien dans colonne2 (dans data2)."""
    valeurs_valides = set(row.get(colonne2, '') for row in data2)
    erreurs = []
    for i, row in enumerate(data1):
        val = row.get(colonne1, '')
        if val not in valeurs_valides:
            erreurs.append((i, val))
    return erreurs


def verifier_numerique(data, colonne):
    """Retourne les lignes où la valeur n'est pas convertible en nombre."""
    erreurs = []
    for i, row in enumerate(data):
        val = row.get(colonne, '')
        if val != '':
            try:
                float(val)
            except ValueError:
                erreurs.append((i, val))
    return print("Les erreurs détectées sont :", erreurs, "\nOn en compte ", len(erreurs))


def verifier_date(data, colonne):
    """
    Vérifie le format de date AAAA/MM/JJ
    Retourne les lignes dont le format ne correspond pas
    """
    erreurs = []
    for i, row in enumerate(data):
        val = row.get(colonne, '')
        if val != '':
            parties = val.split("/")
            if len(parties) != 3:
                erreurs.append((i, val))
    return print(erreurs)


# ==============================================================================
# 5. NETTOYAGE 
# ==============================================================================

def ignorer_anomalies(data):
    """Ignore les anomalies."""
    print("Les anomalies sont ignorées : aucun impact sur l'analyse.")
    return data


def remplacer_anomalies(data, colonne, valeur_remplacement):
    """Remplace les valeurs vides par une valeur de remplacement."""
    data_copie = [dict(row) for row in data]
    nb_remplace = 0
    for row in data_copie:
        if row.get(colonne, '') == '':
            row[colonne] = valeur_remplacement
            nb_remplace += 1
    print(f"{nb_remplace} valeur(s) vide(s) remplacée(s) par '{valeur_remplacement}' dans '{colonne}'.")
    return data_copie


def supprimer_anomalies(data, colonne):
    """
    Supprime les lignes dont la valeur est vide dans la colonne.
    Affiche le nombre de lignes supprimées et le taux de suppression.
    """
    total = len(data)
    new_data = [row for row in data if row.get(colonne, '') != '']
    data_restante = total - len(new_data)
    taux = (data_restante / total * 100) if total > 0 else 0
    print(f"{data_restante} lignes supprimées sur {total}.")
    print(f"Taux de suppression : {round(taux, 2)} %")
    return new_data


def ecarter_anomalies(data, colonne):
    """
    Sépare les données valides (valeur non vide) des données écartées (valeur vide).
    Retourne (valides, rejetes).
    """
    valides = []
    rejetes = []
    for i, row in enumerate(data):
        if row.get(colonne, '') == '':
            rejetes.append((i, row))
        else:
            valides.append(row)
    print(f"Données valides : {len(valides)}")
    print(f"Données écartées (valeur vide) : {len(rejetes)}")
    return valides, rejetes


# ==============================================================================
# 6. STATISTIQUES
# ==============================================================================

def moyenne(data, colonne):
    """Calcule la moyenne d'une colonne."""
    valeurs = []
    for row in data:
        val = row.get(colonne, '')
        if val != '':
            try:
                valeurs.append(float(val))
            except ValueError:
                pass
    if not valeurs:
        return None
    return sum(valeurs) / len(valeurs)


def mode(data, colonne):
    """Retourne la valeur la plus fréquente d'une colonne (hors valeurs vides)."""
    compteur = {}
    for row in data:
        val = row.get(colonne, '')
        if val != '':
            compteur[val] = compteur.get(val, 0) + 1
    if not compteur:
        return None
    return max(compteur, key=compteur.get)


def compter_non_vides(data, colonne):
    """Compte le nombre de valeurs non vides dans une colonne."""
    nb = 0
    for row in data:
        if row.get(colonne, '') != '':
            nb += 1
    return nb


def valeurs_uniques(data, colonne):
    """Retourne le nombre de valeurs distinctes non vides dans une colonne."""
    valeurs = set()
    for row in data:
        val = row.get(colonne, '')
        if val != '':
            valeurs.add(val)
    return len(valeurs)


def min_max(data, colonne):
    """Retourne le min et le max des valeurs numériques d'une colonne."""
    valeurs = []
    for row in data:
        val = row.get(colonne, '')
        if val != '':
            try:
                valeurs.append(float(val))
            except ValueError:
                pass
    if not valeurs:
        return None, None
    return min(valeurs), max(valeurs)


def describe(data, *colonnes):
    """
    Fournit un résumé statistique des colonnes demandées.
    Gère le cas où data est vide.
    Si aucune colonne n'est précisée, toutes sont décrites.
    """
    if not data:
        print("Aucune donnée disponible pour la description.")
        return {}

    if not colonnes:
        colonnes = list(data[0].keys())

    resume = {}
    for col in colonnes:
        if col in data[0]:
            total    = len(data)
            non_vides = compter_non_vides(data, col)
            nb_vides  = total - non_vides
            uniques   = valeurs_uniques(data, col)
            minimum, maximum = min_max(data, col)
            moy = moyenne(data, col)
            mod = mode(data, col)

            resume[col] = {
                "total"    : total,
                "non_vides": non_vides,
                "vides"    : nb_vides,
                "uniques"  : uniques,
                "min"      : minimum,
                "max"      : maximum,
                "moyenne"  : moy,
                "mode"     : mod
            }
        else:
            print(f"Colonne '{col}' inexistante dans les données.")
    return resume


def afficher_tableau(data):
    """Affiche une liste de dictionnaires sous forme de tableau simple."""
    if not data:
        print("Aucune donnée à afficher.")
        return

    colonnes = list(data[0].keys())

    # affichage en-têtes
    for col in colonnes:
        print(f"{col:<20}", end="")
    print()

    print("-" * (20 * len(colonnes)))

    # lignes
    for row in data:
        for col in colonnes:
            print(f"{str(row.get(col, '')):<20}", end="")
        print()

    print("\nL'affichage est terminé !")


# ==============================================================================
# 7. TRANSFORMATIONS ET FILTRES
# ==============================================================================

def filtrer(data, colonne, valeur, ignorer_casse=True):
    """
    Filtre les lignes dont la valeur correspond dans une colonne.
    ignorer_casse=True pour une comparaison insensible à la casse.
    """
    if ignorer_casse:
        resultat = [row for row in data if row.get(colonne, '').strip().lower() == valeur.strip().lower()]
    else:
        resultat = [row for row in data if row.get(colonne, '') == valeur]

    print(f"La fréquence de '{valeur}' est de {len(resultat)}")
    return resultat


def filtrer_multiple(data, col1, val1, col2, val2, ignorer_casse=True):
    """Filtre par deux critères simultanément."""
    resultat = []
    for row in data:
        v1 = row.get(col1, '')
        v2 = row.get(col2, '')
        if ignorer_casse:
            match1 = v1.strip().lower() == val1.strip().lower()
            match2 = v2.strip().lower() == val2.strip().lower()
        else:
            match1 = v1 == val1
            match2 = v2 == val2
        if match1 and match2:
            resultat.append(row)
    return resultat


def extraire_ville(data, ville):
    """Extrait les installations d'une ville donnée (insensible à la casse)."""
    return filtrer(data, "commune", ville)


def extraire_installation(data, id_inst):
    """Extrait les lignes correspondant à un identifiant d'installation."""
    return filtrer(data, "id_installation", id_inst, ignorer_casse=False)


def extraire_equipement(data, id_eq):
    """Extrait les lignes correspondant à un identifiant d'équipement."""
    return filtrer(data, "id_equipement", id_eq, ignorer_casse=False)


def regrouper(data, *colonnes):
    """
    Regroupe les lignes par combinaison de valeurs pour les colonnes données.
    Retourne un dictionnaire : {(val1, val2, ...): [liste de lignes]}.
    """
    groupes = {}
    for row in data:
        cle = tuple(row.get(col, '') for col in colonnes)
        if cle not in groupes:
            groupes[cle] = []
        groupes[cle].append(row)
    return groupes


def afficher_groupes(groupes):
    """Affiche proprement le résultat de regrouper()."""
    for cle, lignes in groupes.items():
        print(f"\nGroupe : {cle} — {len(lignes)} ligne(s)")
        afficher_donnees_installation(lignes)


# ==============================================================================
# 8. EXPORT – TABLEAU STATISTIQUE CSV
# ==============================================================================
def exporter_tableau_csv(lignes, fichier_sortie="DATA/tableau_statistique.csv"):
    """
    Exporte une liste de dictionnaires dans un fichier CSV.

    """
    if not lignes:
        print("Aucune donnée à exporter.")
        return ""

    os.makedirs(os.path.dirname(fichier_sortie) if os.path.dirname(fichier_sortie) else ".",exist_ok=True)
    entete = list(lignes[0].keys())

    with open(fichier_sortie, "w", newline="", encoding="latin-1") as f:
        writer = csv.DictWriter(f, entete, delimiter=";")
        writer.writeheader()
        writer.writerows(lignes)

    print(f"Tableau exporté -> {fichier_sortie}")
    return fichier_sortie


# ==============================================================================
# 10. TABLEAUX STATISTIQUES DÉTAILLÉS
# ==============================================================================
#
#  Ce bloc s'appuie sur les fonctions déjà écrites dans les sections précédentes :
#    - charger_donnees_total()  -> section 1
#    - regrouper()              -> section 7
#    - moyenne()                -> section 6
#    - min_max()                -> section 6
#    - mode()                   -> section 6
#    - exporter_tableau_csv()   -> section 8
#
#  7 tableaux sont produits et exportés en CSV :
#    Tableau 1 : Chiffres clés (national / régional / communes)
#    Tableau 2 : Types d'équipements et caractéristiques
#    Tableau 3 : Habitants par équipement par commune
#    Tableau 4 : Utilisateurs des équipements
#    Tableau 5 : Activités pratiquées vs praticables
#    Tableau 6 : Propriétaires et gestionnaires
#    Tableau 7 : Évolution temporelle du parc sportif
# ==============================================================================

NATIONAL = {
    "territoire"   : "France",
    "installations": 151791,
    "equipements"  : 334325,
    "activites"    : 573113,
    "population"   : 69082000,
    "superficie"   : 547557,
}

DEPARTEMENTS_HDF = [
    {"territoire": "Nord (59)",          "installations": 3559, "equipements": 185, "population": 2615635, "superficie": 5742.8},
    {"territoire": "Pas de Calais (62)", "installations": 212,  "equipements": 0,   "population": 1457905, "superficie": 6671.4},
    {"territoire": "Somme (80)",         "installations": 19,   "equipements": 0,   "population": 565540,  "superficie": 6170.1},
    {"territoire": "Oise (60)",          "installations": 8,    "equipements": 0,   "population": 829899,  "superficie": 5860.2},
    {"territoire": "Aisne (02)",         "installations": 10,   "equipements": 0,   "population": 523342,  "superficie": 7361.7},
]

COMMUNES_REF = {
    "LILLE"            : {"population": 238246, "superficie": 34.83, "installations": 150, "equipements": 415},
    "TOURCOING"        : {"population": 98772,  "superficie": 15.19, "installations": 55,  "equipements": 117},
    "ROUBAIX"          : {"population": 98286,  "superficie": 13.23, "installations": 69,  "equipements": 185},
    "DUNKERQUE"        : {"population": 86263,  "superficie": 37.34, "installations": 97,  "equipements": 227},
    "VILLENEUVE D'ASCQ": {"population": 62868,  "superficie": 27.46, "installations": 80,  "equipements": 275},
    "LESQUIN"          : {"population": 8754,   "superficie": 8.41,  "installations": 10,  "equipements": 41},
}

ORDRE_COMMUNES = ["LILLE", "TOURCOING", "ROUBAIX", "DUNKERQUE", "VILLENEUVE D'ASCQ", "LESQUIN"]

# Ordre chronologique des périodes de mise en service
PERIODES = ["Avant 1945", "1945-1964", "1965-1974", "1975-1984","1985-1994", "1995-2004", "A partir de 2005"]


# ----------------------------------------------------------
# FONCTIONS DE FILTRAGE (jointure entre les 3 fichiers CSV)
# ----------------------------------------------------------

def joint_inst_equip(data_inst, data_equip):
    """
    Retourne uniquement les équipements appartenant aux installations de Lille.
    """
    # On indexe les installations par leur numéro
    index_inst = regrouper(data_inst, "numero")
    numeros_lille = set(index_inst.keys())   # ensemble des clés des numeros de lille

    equip_lille = []
    for row in data_equip:
        cle = (row.get("installation_numero", "").strip(),)
        if cle in numeros_lille:
            equip_lille.append(row)
    return equip_lille


def joint_act_equip(data_equip_lille, data_act):
    """
    Retourne uniquement les activités liées aux équipements de Lille.
    """
    index_equip = regrouper(data_equip_lille, "numero")
    numeros_equip = set(index_equip.keys())  
    act_lille = []
    for row in data_act:
        cle = (row.get("equip_numero", "").strip(),)
        if cle in numeros_equip:
            act_lille.append(row)
    return act_lille


# ----------------------------------------------------------
# FONCTIONS UTILITAIRES SIMPLES
# ----------------------------------------------------------

def trier_desc(dictionnaire):
    """Trie un dictionnaire par valeur décroissante. Retourne une liste de (clé, valeur)."""
    # Transformer le dictionnaire en liste de tuples
    liste = list(dictionnaire.items())
    # Trier la liste par les valeurs
    liste_triee = sorted(liste,key=lambda element: element[1],reverse=True)
    return liste_triee

def taux(partie, total):
    """Calcule un pourcentage """
    return round((partie / total) * 100, 2)


def formatage(valeur, decimales=1):
    """Formate un nombre arrondi, ou retourne '-' si la valeur est None."""
    # Si la valeur n'existe pas
    if valeur is None:
        return "-"
    if type(valeur) == float:
        valeur_arrondie = round(valeur, decimales)
        return valeur_arrondie
    return valeur

# ==============================================================================
# TABLEAU 1 – Chiffres clés : national / régional / communes
# ==============================================================================

def tableau1_chiffres_cles(data_inst, data_equip_lille, data_act_lille):
    """
    Tableau récapitulatif à 3 niveaux géographiques :
      - France (niveau national)
      - Hauts-de-France (5 départements + total)
      - 6 communes du Nord (Lille calculée depuis les CSV, autres via référence)
    """
    lignes = []

    # ---- Niveau national ----
    lignes.append({
        "Section"          : "National",
        "Territoire"       : NATIONAL["territoire"],
        "Nb installations" : NATIONAL["installations"],
        "Nb equipements"   : NATIONAL["equipements"],
        "Nb activites"     : NATIONAL["activites"],
        "Population"       : NATIONAL["population"],
        "Superficie km2"   : NATIONAL["superficie"],
    })

    # ---- Niveau régional (Hauts-de-France) ----
    total_inst  = 0
    total_equip = 0
    total_pop   = 0
    total_sup   = 0

    for dep in DEPARTEMENTS_HDF:
        total_inst  += dep["installations"]
        total_equip += dep["equipements"]
        total_pop   += dep["population"]
        total_sup   += dep["superficie"]

        lignes.append({
            "Section"          : "Regional - Hauts-de-France",
            "Territoire"       : dep["territoire"],
            "Nb installations" : dep["installations"],
            "Nb equipements"   : dep["equipements"],
            "Nb activites"     : "-",
            "Population"       : dep["population"],
            "Superficie km2"   : dep["superficie"],
        })

    # Ligne total régional
    lignes.append({
        "Section"          : "Total Regional",
        "Territoire"       : "Total Hauts-de-France",
        "Nb installations" : total_inst,
        "Nb equipements"   : total_equip,
        "Nb activites"     : "-",
        "Population"       : total_pop,
        "Superficie km2"   : round(total_sup, 1),
    })

    # ---- Niveau communes ----
    # Mise à jour de Lille avec les valeurs réelles des CSV
    COMMUNES_REF["LILLE"]["installations"] = len(data_inst)
    COMMUNES_REF["LILLE"]["equipements"]   = len(data_equip_lille)

    total_inst_c  = 0
    total_equip_c = 0
    total_pop_c   = 0
    total_sup_c   = 0

    for commune in ORDRE_COMMUNES:
        ref  = COMMUNES_REF[commune]
        nb_i = ref["installations"]
        nb_e = ref["equipements"]
        pop  = ref["population"]
        sup  = ref["superficie"]

        # Activités disponibles uniquement pour Lille (seule ville dans nos CSV)
        nb_a = len(data_act_lille) if commune == "LILLE" else "-"

        total_inst_c  += nb_i
        total_equip_c += nb_e
        total_pop_c   += pop
        total_sup_c   += sup

        lignes.append({
            "Section"          : "Communes du Nord",
            "Territoire"       : commune,
            "Nb installations" : nb_i,
            "Nb equipements"   : nb_e,
            "Nb activites"     : nb_a,
            "Population"       : pop,
            "Superficie km2"   : sup,
        })

    # Ligne total communes
    lignes.append({
        "Section"          : "Total Communes",
        "Territoire"       : "Total communes",
        "Nb installations" : total_inst_c,
        "Nb equipements"   : total_equip_c,
        "Nb activites"     : "-",
        "Population"       : total_pop_c,
        "Superficie km2"   : round(total_sup_c, 2),
    })

    return lignes


# ==============================================================================
# TABLEAU 2 – Types d'équipements et caractéristiques
# ==============================================================================

def tableau2_types_equipements(data_equip_lille, top_n=15):
    """
    Pour chaque type d'équipement (les top_n les plus fréquents) :
      - Nombre et part sur le total
      - Surface moyenne (m2)       <- via moyenne() section 6
      - Nombre moyen de vestiaires <- via moyenne() section 6
      - Répartition intérieur / extérieur

    Utilise regrouper() (section 7) et moyenne() (section 6).
    """
    lignes = []
    total = len(data_equip_lille)

    # Regroupement par type via regrouper() (section 7)
    groupes = regrouper(data_equip_lille, "type")

    # Comptage du nombre d'équipements par type
    nb_par_type = {}
    for cle, liste in groupes.items():
        nb_par_type[cle[0]] = len(liste)

    for type_eq, nb in trier_desc(nb_par_type)[:top_n]:
        liste = groupes[(type_eq,)]

        # Surface moyenne via moyenne() (section 6)
        surf_moy = moyenne(liste, "aire_surface")

        # Vestiaires moyens via moyenne() (section 6)
        vest_moy = moyenne(liste, "vestiaires_sportifs_nb")

        # Intérieur vs extérieur
        nb_interieur = 0
        for row in liste:
            if row.get("nature", "").strip().lower() == "interieur":
                nb_interieur += 1

        lignes.append({
            "Type d'equipement"    : type_eq,
            "Nb equipements"       : nb,
            "Part du total (%)"    : taux(nb, total),
            "Surface moyenne (m2)" : formatage(surf_moy, 0),
            "Nb moyen vestiaires"  : formatage(vest_moy, 1),
            "Nb interieurs"        : nb_interieur,
            "Nb exterieurs"        : nb - nb_interieur,
        })

    return lignes


# ==============================================================================
# TABLEAU 3 – Habitants par équipement par commune
# ==============================================================================

def tableau3_habitants_par_equipement():
    """
    Pour chaque commune :
      - Population et superficie
      - Nombre d'installations et d'équipements
      - Habitants pour 1 équipement
      - Équipements pour 10 000 habitants
      - Installations pour 10 000 habitants

    Données issues de COMMUNES_REF (référence nationale RES + INSEE).
    """
    lignes = []

    for commune in ORDRE_COMMUNES:
        ref  = COMMUNES_REF[commune]
        pop  = ref["population"]
        sup  = ref["superficie"]
        nb_e = ref["equipements"]
        nb_i = ref["installations"]

        # Habitants pour 1 équipement
        hab_par_equip = round(pop / nb_e) if nb_e > 0 else "-"

        # Équipements / installations pour 10 000 habitants
        equip_10k = round(nb_e / pop * 10000, 1) if pop > 0 else "-"
        inst_10k  = round(nb_i / pop * 10000, 1) if pop > 0 else "-"

        lignes.append({
            "Commune"                        : commune.title(),
            "Population"                     : pop,
            "Superficie (km2)"               : sup,
            "Nb installations"               : nb_i,
            "Nb equipements"                 : nb_e,
            "Habitants pour 1 equipement"    : hab_par_equip,
            "Equipements pour 10 000 hab."   : equip_10k,
            "Installations pour 10 000 hab." : inst_10k,
        })

    return lignes


# ==============================================================================
# TABLEAU 4 – Utilisateurs des équipements
# ==============================================================================

def tableau4_utilisateurs(data_equip_lille):
    """
    La colonne 'utilisateurs' contient plusieurs valeurs séparées par virgule.
    Ex : "Clubs sportifs,...,Scolaires,universités"

    On découpe chaque valeur pour compter séparément chaque type d'utilisateur.

    Colonnes : Type d'utilisateur | Nb équipements concernés | Part des équipements (%)
    """
    compteur    = {}
    nb_avec_info = 0

    for row in data_equip_lille:
        valeur = row.get("utilisateurs", "").strip()
        if valeur == "":
            continue

        nb_avec_info += 1

        # Découpage : "Clubs,...,Scolaires" -> ["Clubs...", "Scolaires"]
        for type_util in valeur.split(","):
            type_util = type_util.strip()
            if type_util != "":
                if type_util not in compteur:
                    compteur[type_util] = 0
                compteur[type_util] += 1

    lignes = []
    for utilisateur, nb in trier_desc(compteur):
        lignes.append({
            "Type d'utilisateur"       : utilisateur,
            "Nb equipements concernes" : nb,
            "Part des equipements (%)" : taux(nb, nb_avec_info),
        })

    # Ligne récapitulative
    lignes.append({
        "Type d'utilisateur"       : "TOTAL (equipements avec info)",
        "Nb equipements concernes" : nb_avec_info,
        "Part des equipements (%)" : taux(nb_avec_info, len(data_equip_lille)),
    })

    return lignes


# ==============================================================================
# TABLEAU 5 – Activités pratiquées vs praticables
# ==============================================================================
#
#  EXPLICATION DES INDICATEURS :
#
#  Chaque ligne du fichier activités associe une discipline à un équipement.
#  La colonne "aps_pratique" indique le statut de cette activité sur l'équipement :
#
#  • "Activité pratiquée"  : l'activité est RÉELLEMENT organisée sur cet équipement
#                            (club, cours, compétition...).
#
#  • "Activité praticable" : l'équipement est COMPATIBLE avec cette activité
#                            (dimensions, sol, matériel) mais elle n'est pas
#                            nécessairement organisée de façon régulière.
#
#  • "Les deux"            : cas le plus courant — l'équipement accueille
#                            l'activité ET est dimensionné pour la pratiquer.
#
#  Lecture du tableau :
#    - "Nb pratiquee"  = nb d'équipements où la discipline est effectivement pratiquée
#    - "Nb praticable" = nb d'équipements compatibles avec la discipline
#    - "Nb les deux"   = nb d'équipements à la fois pratiqués ET praticables
#    - "Total"         = nb total de mentions de la discipline dans nos données
#    - "Part (%)"      = poids de la discipline parmi toutes les activités recensées
#
# ==============================================================================

def tableau5_activites(data_act_lille, top_n=15):
    """
    Pour chaque discipline sportive (top_n les plus fréquentes) :
      - Nb d'équipements où l'activité est pratiquée
      - Nb d'équipements où l'activité est praticable
      - Nb d'équipements où les deux s'appliquent
      - Total de mentions et part du total

    Utilise regrouper() (section 7) pour grouper par discipline.
    """
    lignes = []
    total_act = len(data_act_lille)

    # Regroupement par discipline via regrouper() (section 7)
    groupes = regrouper(data_act_lille, "aps_discipline")

    # Comptage pour le tri
    nb_par_discipline = {}
    for cle, liste in groupes.items():
        nb_par_discipline[cle[0]] = len(liste)

    for discipline, _ in trier_desc(nb_par_discipline)[:top_n]:
        liste = groupes[(discipline,)]

        nb_pratiquee  = 0
        nb_praticable = 0
        nb_les_deux   = 0

        for row in liste:
            # Nettoyage : certaines valeurs ont des guillemets autour
            pratique_txt = row.get("aps_pratique", "").strip().strip("'")

            est_pratiquee  = "pratiqu"    in pratique_txt and "praticable" not in pratique_txt.lower()
            est_praticable = "praticable" in pratique_txt.lower()
            est_les_deux   = "pratiqu"    in pratique_txt and "praticable" in pratique_txt.lower()

            # Si les deux, ce n'est plus uniquement "pratiquée"
            if est_les_deux:
                est_pratiquee = False

            if est_les_deux:
                nb_les_deux += 1
            elif est_pratiquee:
                nb_pratiquee += 1
            elif est_praticable:
                nb_praticable += 1

        nb_total = nb_pratiquee + nb_praticable + nb_les_deux

        lignes.append({
            "Discipline"        : discipline,
            "Nb pratiquee"      : nb_pratiquee + nb_les_deux,
            "Nb praticable"     : nb_praticable + nb_les_deux,
            "Nb les deux"       : nb_les_deux,
            "Total mentions"    : nb_total,
            "Part du total (%)" : taux(nb_total, total_act),
        })

    return lignes


# ==============================================================================
# TABLEAU 6 – Propriétaires et gestionnaires
# ==============================================================================

def tableau6_proprietaires_gestionnaires(data_equip_lille):
    """
    Deux blocs dans un même tableau :
      1. Répartition par type de propriétaire principal
      2. Répartition par type de gestionnaire
    Avec nombre d'équipements, pourcentage et ligne TOTAL pour chaque bloc.

    Utilise regrouper() (section 7) pour compter par type.
    """
    lignes = []
    total = len(data_equip_lille)

    # ---- Bloc PROPRIÉTAIRES ----
    groupes_prop = regrouper(data_equip_lille, "proprietaire_principal_type")

    nb_par_prop = {}
    for cle, liste in groupes_prop.items():
        nb_par_prop[cle[0]] = len(liste)

    lignes.append({"Role": "=== PROPRIETAIRES ===", "Type": "", "Nb equipements": "", "Part (%)": ""})

    total_prop = 0
    for type_p, nb in trier_desc(nb_par_prop):
        total_prop += nb
        lignes.append({
            "Role"          : "Proprietaire",
            "Type"          : type_p if type_p != "" else "Non renseigne",
            "Nb equipements": nb,
            "Part (%)"      : taux(nb, total),
        })

    lignes.append({"Role": "Total Proprietaires", "Type": "TOTAL", "Nb equipements": total_prop, "Part (%)": 100.0})

    # ---- Bloc GESTIONNAIRES ----
    groupes_gest = regrouper(data_equip_lille, "gestionnaire_type")

    nb_par_gest = {}
    for cle, liste in groupes_gest.items():
        nb_par_gest[cle[0]] = len(liste)

    lignes.append({"Role": "=== GESTIONNAIRES ===", "Type": "", "Nb equipements": "", "Part (%)": ""})

    total_gest = 0
    for type_g, nb in trier_desc(nb_par_gest):
        total_gest += nb
        lignes.append({
            "Role"          : "Gestionnaire",
            "Type"          : type_g if type_g != "" else "Non renseigne",
            "Nb equipements": nb,
            "Part (%)"      : taux(nb, total),
        })

    lignes.append({"Role": "Total Gestionnaires", "Type": "TOTAL", "Nb equipements": total_gest, "Part (%)": 100.0})

    return lignes


# ==============================================================================
# TABLEAU 7 – Évolution temporelle du parc sportif
# ==============================================================================

def tableau7_evolution(data_equip_lille):
    """
    Répartition des équipements par période de mise en service.
    Utilise regrouper() (section 7) pour compter par période.
    """
    lignes = []

    # Regroupement par période via regrouper() (section 7)
    groupes = regrouper(data_equip_lille, "mise_en_service_periode")

    # Comptage par période
    nb_par_periode = {}
    for cle, liste in groupes.items():
        nb_par_periode[cle[0]] = len(liste)

    nb_sans_info    = nb_par_periode.pop("", 0)
    total_avec_info = sum(nb_par_periode.values())

    cumul = 0
    for periode in PERIODES:
        nb = nb_par_periode.get(periode, 0)
        cumul += nb

        lignes.append({
            "Periode de mise en service" : periode,
            "Nb equipements"             : nb,
            "Part (%)"                   : taux(nb, total_avec_info),
            "Cumul equipements"          : cumul,
            "Cumul (%)"                  : taux(cumul, total_avec_info),
        })

    # Ligne non renseigné
    lignes.append({
        "Periode de mise en service" : "Non renseigne",
        "Nb equipements"             : nb_sans_info,
        "Part (%)"                   : taux(nb_sans_info, len(data_equip_lille)),
        "Cumul equipements"          : "-",
        "Cumul (%)"                  : "-",
    })

    # Ligne total
    lignes.append({
        "Periode de mise en service" : "TOTAL",
        "Nb equipements"             : len(data_equip_lille),
        "Part (%)"                   : 100.0,
        "Cumul equipements"          : total_avec_info,
        "Cumul (%)"                  : 100.0,
    })

    return lignes


# ==============================================================================
# FONCTION PRINCIPALE – Génère et exporte les 7 tableaux
# ==============================================================================

def export_tableaux(chemin_inst, chemin_equip, chemin_act,
                          dossier_sortie="DATA"):
    """
    Charge les 3 fichiers CSV, filtre sur Lille, génère et exporte
    les 7 tableaux statistiques dans le dossier indiqué.
    """
    print("\n" + "=" * 60)
    print("  TABLEAUX STATISTIQUES")
    print("=" * 60)

    data_inst  = charger_donnees_total(chemin_inst)
    data_equip = charger_donnees_total(chemin_equip)
    data_act   = charger_donnees_total(chemin_act)
   
    data_equip_lille = joint_inst_equip(data_inst, data_equip)
    data_act_lille   = joint_act_equip(data_equip_lille, data_act)
  
    t1 = tableau1_chiffres_cles(data_inst, data_equip_lille, data_act_lille)
    exporter_tableau_csv(t1, dossier_sortie + "/tableau1_chiffres_cles.csv")

    t2 = tableau2_types_equipements(data_equip_lille, top_n=15)
    exporter_tableau_csv(t2, dossier_sortie + "/tableau2_types_equipements.csv")

    t3 = tableau3_habitants_par_equipement()
    exporter_tableau_csv(t3, dossier_sortie + "/tableau3_habitants_par_equipement.csv")

    t4 = tableau4_utilisateurs(data_equip_lille)
    exporter_tableau_csv(t4, dossier_sortie + "/tableau4_utilisateurs.csv")

    t5 = tableau5_activites(data_act_lille, top_n=15)
    exporter_tableau_csv(t5, dossier_sortie + "/tableau5_activites.csv")

    t6 = tableau6_proprietaires_gestionnaires(data_equip_lille)
    exporter_tableau_csv(t6, dossier_sortie + "/tableau6_proprietaires_gestionnaires.csv")

    t7 = tableau7_evolution(data_equip_lille)
    exporter_tableau_csv(t7, dossier_sortie + "/tableau7_evolution.csv")

# ==============================================================================
# APPELS SECTION 10
# ==============================================================================

export_tableaux(
    chemin_inst    = "DATA/Installation_lille.csv",
    chemin_equip   = "DATA/Equipement_lille.csv",
    chemin_act     = "DATA/Activites_lille.csv",
    dossier_sortie = "DATA"
)



# ==============================================================================
# 9. PROGRAMME PRINCIPAL
# ==============================================================================

chemin_inst_lille  = "DATA/Installation_lille.csv"
chemin_equip_lille = "DATA/Equipement_lille.csv"
chemin_act_lille   = "DATA/Activites_lille.csv"

print("\n" + "-" * 74 + "\n")

# Chargement et affichage des colonnes disponibles
data_inst = charger_donnees_total(chemin_inst_lille)
data_equip = charger_donnees_total(chemin_equip_lille)
data_act = charger_donnees_total(chemin_act_lille)

afficher_donnees_installation(data_inst)
print("Colonnes présentes :")
print(list(data_inst[0].keys()))

print("\n" + "-" * 74 + "\n")

# Plage de données 
plage = charger_plage_data(chemin_equip_lille, 1, 10)
afficher_donnees_installation(plage)


print("\n" + "-" * 74 + "\n")
print("CHARGEMENT FILTRÉ (keep)")
data = charger_donnees_var(chemin_inst_lille, "keep", "cp", "commune")
afficher_donnees_installation(data)

print("\n" + "-" * 74 + "\n")
print("MENU INTERACTIF :")
# gestion_visualisation(chemin_inst_lille)  # décommenter pour activer le menu

print("\n" + "-" * 74 + "\n")
print("TRAITEMENT DES ANOMALIES")

data_remplace  = remplacer_anomalies(data_inst, "acces_handi", "NULL")
afficher_donnees_installation(data_remplace)

data_sans_vides = supprimer_anomalies(data_inst, "acces_handi")
afficher_donnees_installation(data_sans_vides)


valides, rejetes = ecarter_anomalies(data_equip, "mise_en_service_date")


print("\n" + "-" * 74 + "\n")
print("STATISTIQUES")

print("Moyenne  :", moyenne(data_inst, "cp"))
print("Mode  :", mode(data_inst, "cp"))
min_val, max_val = min_max(data_inst, "cp")
print(f"Min cp : {min_val}  |  Max cp : {max_val}")

print("\n" + "-" * 74 + "\n")
print("RÉSUMÉ STATISTIQUES (describe)")
resume_stat = describe(data_inst, "install_nb", "dens_niveau")   
for col, stats in resume_stat.items():
    print(f"\nColonne : {col}")
    for k, v in stats.items():
        print(f"  {k} : {v}")

print("\n" + "-" * 74 + "\n")
print("TRANSFORMATIONS ET FILTRES")

resultat_ville = extraire_ville(data_inst, "Lille")
afficher_donnees_installation(resultat_ville)

regroupe = regrouper(data_inst, "commune")
afficher_groupes(regroupe) 