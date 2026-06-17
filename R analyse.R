# ============================================================
# ÉTUDE DES ÉQUIPEMENTS SPORTIFS EN FRANCE
# Source : Recensement des Équipements Sportifs (RES) - Ministère des Sports
# Données : data-es-installation.csv, data-es-equipement.csv, data-es-activite.csv
# ============================================================


# ============================================================
# 0. PACKAGES & CHEMINS
# ============================================================

library(tidyverse)
library(scales)

chemin_inst  <- "DATA/data-es-installation.csv"
chemin_equip <- "DATA/data-es-equipement.csv"
chemin_act   <- "DATA/data-es-activite.csv"


# ============================================================
# 1. CHARGEMENT DES DONNÉES
# ============================================================

install <- read.csv(chemin_inst,  sep = ";")
equip   <- read.csv(chemin_equip, sep = ";")
activ   <- read.csv(chemin_act,   sep = ";")

# Vérification rapide des dimensions
cat(sprintf("Installations : %d lignes, %d colonnes\n", nrow(install), ncol(install)))
cat(sprintf("Équipements   : %d lignes, %d colonnes\n", nrow(equip),   ncol(equip)))
cat(sprintf("Activités     : %d lignes, %d colonnes\n", nrow(activ),   ncol(activ)))


# ============================================================
# 2. TAUX DE VALEURS MANQUANTES
# ============================================================
# On calcule le % de NA ou de cellules vides sur les colonnes importantes
# any_of() évite une erreur si une colonne n'existe pas dans le fichier

taux_na <- function(df, cols, nom_fichier) {
  # On garde seulement les colonnes qui existent réellement
  cols_presentes <- intersect(cols, names(df))
  
  # Si aucune colonne trouvée, on retourne un tableau vide
  if (length(cols_presentes) == 0) return(tibble())
  
  df %>%
    select(all_of(cols_presentes)) %>%
    summarise(across(everything(), ~ mean(is.na(.) | . == "") * 100)) %>%
    pivot_longer(everything(), names_to = "variable", values_to = "pct_na") %>%
    mutate(fichier = nom_fichier)
}

na_all <- bind_rows(
  taux_na(install, c("reg_nom","dep_nom","dens_lib","acces_transp_commun"), "Installations"),
  taux_na(equip,   c("type","famille","mise_en_service_periode",
                     "proprietaire_principal_type","acces_libre",
                     "acces_handi_mobilite","gestion_dsp"),             "Équipements"),
  taux_na(activ,   c("aps_discipline","aps_famille",
                     "aps_niveau_pratique","equip_numero"),             "Activités")
) %>%
  filter(pct_na > 0) # On n'affiche que les colonnes avec des données manquantes

# Graphique des valeurs manquantes (affiché seulement s'il y en a)
if (nrow(na_all) > 0) {
  ggplot(na_all, aes(x = pct_na, y = fct_reorder(variable, pct_na), fill = fichier)) +
    geom_col() +
    geom_text(aes(label = sprintf("%.1f%%", pct_na)), hjust = -0.1, size = 3) +
    scale_fill_brewer(palette = "Set2") +
    scale_x_continuous(expand = expansion(mult = c(0, 0.15))) +
    labs(title = "Taux de valeurs manquantes — variables clés",
         x = "% de NA / vides", y = NULL, fill = "Fichier",
         caption = "Source : Ministère des Sports – RES 2025") +
    theme_minimal(base_size = 11)
}


# ============================================================
# 3. NETTOYAGE & PRÉPARATION
# ============================================================

# --- Installations : on garde seulement celles avec une région renseignée ---
install_clean <- install %>%
  filter(!is.na(numero), !is.na(reg_nom), reg_nom != "") %>%
  mutate(reg_nom = str_trim(reg_nom))

# --- Équipements : on regroupe les périodes et les types de propriétaires ---
equip_clean <- equip %>%
  filter(!is.na(numero)) %>%
  mutate(
    # Regroupement des périodes de mise en service en grandes tranches
    periode = case_when(
      str_detect(mise_en_service_periode, "Avant")   ~ "Avant 1945",
      str_detect(mise_en_service_periode, "1945")    ~ "1945-1964",
      str_detect(mise_en_service_periode, "1965")    ~ "1965-1974",
      str_detect(mise_en_service_periode, "1975")    ~ "1975-1984",
      str_detect(mise_en_service_periode, "1985")    ~ "1985-1994",
      str_detect(mise_en_service_periode, "1995")    ~ "1995-2004",
      str_detect(mise_en_service_periode, "2005")    ~ "2005 et après",
      TRUE ~ NA_character_
    ),
    # Regroupement du type de propriétaire
    proprio_type = case_when(
      str_detect(proprietaire_principal_type, "Commune")            ~ "Commune",
      str_detect(proprietaire_principal_type, "Privé|privé|commercial") ~ "Privé",
      str_detect(proprietaire_principal_type, "EPCI")               ~ "EPCI",
      str_detect(proprietaire_principal_type, "Département")        ~ "Département",
      str_detect(proprietaire_principal_type, "Région")             ~ "Région",
      str_detect(proprietaire_principal_type, "Etat|État")          ~ "État",
      str_detect(proprietaire_principal_type, "Association")        ~ "Association",
      !is.na(proprietaire_principal_type) & proprietaire_principal_type != "" ~ "Autre",
      TRUE ~ "Non renseigné"
    ),
    # Accessibilité : TRUE si la colonne est renseignée (non vide)
    handi_mobilite  = !is.na(acces_handi_mobilite)  & acces_handi_mobilite  != "",
    handi_sensoriel = !is.na(acces_handi_sensoriel) & acces_handi_sensoriel != "",
    acces_libre_bin = case_when(
      acces_libre == "True"  ~ TRUE,
      acces_libre == "False" ~ FALSE,
      TRUE ~ NA
    )
  )

# --- Activités : on enlève les lignes sans discipline ni équipement ---
activ_clean <- activ %>%
  filter(!is.na(equip_numero), !is.na(aps_discipline), aps_discipline != "")


# ============================================================
# 4. JOINTURES — Rattachement de la géographie aux équipements et activités
# ============================================================

# On ajoute région/département à chaque équipement via l'installation
equip_geo <- equip_clean %>%
  left_join(
    install_clean %>% select(numero, reg_nom, dep_nom, dep_code, dens_lib),
    by = c("installation_numero" = "numero")
  ) %>%
  filter(!is.na(reg_nom), reg_nom != "")

# On ajoute région/département à chaque activité via l'équipement
activ_geo <- activ_clean %>%
  left_join(
    equip_geo %>% select(numero, reg_nom, dep_nom, dep_code, dens_lib),
    by = c("equip_numero" = "numero")
  ) %>%
  filter(!is.na(reg_nom))

cat(sprintf("Équipements géolocalisés : %d\n", nrow(equip_geo)))


# ============================================================
# 5. AXE 1 — RÉPARTITION GÉOGRAPHIQUE PAR RÉGION
# ============================================================

equip_par_region <- equip_geo %>%
  count(reg_nom, name = "nb_equip") %>%
  arrange(desc(nb_equip))

print(equip_par_region)

ggplot(equip_par_region, aes(x = nb_equip, y = fct_reorder(reg_nom, nb_equip), fill = nb_equip)) +
  geom_col() +
  geom_text(aes(label = comma(nb_equip, big.mark = " ")), hjust = -0.1, size = 3.5) +
  scale_fill_gradient(low = "#C6DBEF", high = "#084594") +
  scale_x_continuous(labels = comma_format(big.mark = " "),
                     expand = expansion(mult = c(0, 0.15))) +
  labs(title = "Nombre d'équipements sportifs par région",
       x = "Nombre d'équipements", y = NULL,
       caption = "Source : Ministère des Sports – RES 2025") +
  theme_minimal(base_size = 12) +
  theme(legend.position = "none")


# ============================================================
# 6. AXE 2 — TYPES D'ÉQUIPEMENTS & DISCIPLINES SPORTIVES
# ============================================================

# Top 20 des types d'équipements
top_types <- equip_clean %>%
  filter(!is.na(type), type != "") %>%
  count(type, name = "n") %>%
  slice_max(n, n = 20)

ggplot(top_types, aes(x = n, y = fct_reorder(type, n), fill = n)) +
  geom_col() +
  geom_text(aes(label = comma(n, big.mark = " ")), hjust = -0.1, size = 3) +
  scale_fill_gradient(low = "#C7E9C0", high = "#006D2C") +
  scale_x_continuous(labels = comma_format(big.mark = " "),
                     expand = expansion(mult = c(0, .15))) +
  labs(title = "Top 20 des types d'équipements sportifs en France",
       x = "Nombre d'équipements", y = NULL,
       caption = "Source : Ministère des Sports – RES 2025") +
  theme_minimal(base_size = 10) +
  theme(legend.position = "none")

# Top 20 des disciplines pratiquées
top_disciplines <- activ_clean %>%
  count(aps_discipline, name = "n") %>%
  slice_max(n, n = 20)

ggplot(top_disciplines, aes(x = n, y = fct_reorder(aps_discipline, n), fill = n)) +
  geom_col() +
  geom_text(aes(label = comma(n, big.mark = " ")), hjust = -0.1, size = 3) +
  scale_fill_gradient(low = "#FCAE91", high = "#CB181D") +
  scale_x_continuous(labels = comma_format(big.mark = " "),
                     expand = expansion(mult = c(0, .18))) +
  labs(title = "Top 20 des disciplines sportives pratiquées",
       subtitle = "Nombre d'équipements déclarant la discipline",
       x = "Nombre d'équipements", y = NULL,
       caption = "Source : Ministère des Sports – RES 2025") +
  theme_minimal(base_size = 10) +
  theme(legend.position = "none")


# ============================================================
# 7. AXE 3 — ACCESSIBILITÉ (HANDICAP)
# ============================================================

# Taux globaux d'accessibilité
taux_handi_glob <- equip_clean %>%
  summarise(
    total     = n(),
    handi_mob = sum(handi_mobilite,  na.rm = TRUE),
    handi_sen = sum(handi_sensoriel, na.rm = TRUE),
    acces_lib = sum(acces_libre_bin, na.rm = TRUE)
  ) %>%
  mutate(
    pct_mob = handi_mob / total * 100,
    pct_sen = handi_sen / total * 100,
    pct_lib = acces_lib / total * 100
  )

cat(sprintf("Accessibilité mobilité    : %.1f%%\n", taux_handi_glob$pct_mob))
cat(sprintf("Accessibilité sensorielle : %.1f%%\n", taux_handi_glob$pct_sen))
cat(sprintf("Accès libre               : %.1f%%\n", taux_handi_glob$pct_lib))

# Taux d'accessibilité PMR par région
handi_region <- equip_geo %>%
  group_by(reg_nom) %>%
  summarise(
    nb_total = n(),
    nb_handi = sum(handi_mobilite, na.rm = TRUE),
    taux_handi = nb_handi / nb_total * 100,
    .groups = "drop"
  ) %>%
  arrange(desc(taux_handi))

ggplot(handi_region, aes(x = taux_handi, y = fct_reorder(reg_nom, taux_handi), fill = taux_handi)) +
  geom_col() +
  geom_text(aes(label = sprintf("%.1f%%", taux_handi)), hjust = -0.2, size = 3.2) +
  scale_fill_gradient(low = "#FEE6CE", high = "#E6550D") +
  scale_x_continuous(expand = expansion(mult = c(0, .12))) +
  labs(title = "Taux d'accessibilité PMR (mobilité) par région",
       subtitle = "Part des équipements avec au moins un aménagement mobilité",
       x = "Taux (%)", y = NULL,
       caption = "Source : Ministère des Sports – RES 2025") +
  theme_minimal(base_size = 11) +
  theme(legend.position = "none")


# ============================================================
# 8. AXE 4 — PROPRIÉTÉ (PUBLIC / PRIVÉ)
# ============================================================

# Répartition globale par type de propriétaire
proprio_glob <- equip_clean %>%
  filter(!is.na(proprio_type), proprio_type != "") %>%
  count(proprio_type, name = "nb") %>%
  mutate(proportion = nb / sum(nb) * 100) %>%
  arrange(desc(nb))

print(proprio_glob)

ggplot(proprio_glob, aes(x = proportion, y = fct_reorder(proprio_type, proportion), fill = proprio_type)) +
  geom_col(show.legend = FALSE) +
  geom_text(aes(label = sprintf("%.1f%%  (%s)", proportion, comma(nb, big.mark = " "))),
            hjust = -0.05, size = 3.2) +
  scale_fill_brewer(palette = "Dark2") +
  scale_x_continuous(expand = expansion(mult = c(0, .35))) +
  labs(title = "Répartition des équipements sportifs par type de propriétaire",
       x = "Part (%)", y = NULL,
       caption = "Source : Ministère des Sports – RES 2025") +
  theme_minimal(base_size = 11)

# Public vs Privé par région
public_prive_region <- equip_geo %>%
  mutate(secteur = case_when(
    proprio_type %in% c("Commune","EPCI","Département","Région","État") ~ "Public",
    proprio_type %in% c("Privé","Association")                          ~ "Privé/Associatif",
    TRUE ~ "Autre"
  )) %>%
  filter(secteur != "Autre") %>%
  count(reg_nom, secteur) %>%
  group_by(reg_nom) %>%
  mutate(pct = n / sum(n) * 100) %>%
  ungroup()

ggplot(public_prive_region, aes(x = reg_nom, y = pct, fill = secteur)) +
  geom_col(position = "fill") +
  coord_flip() +
  scale_y_continuous(labels = percent_format()) +
  scale_fill_manual(values = c("Public" = "#2171B5", "Privé/Associatif" = "#EF6548")) +
  labs(title = "Part public vs privé/associatif par région",
       x = NULL, y = "Part (%)", fill = NULL,
       caption = "Source : Ministère des Sports – RES 2025") +
  theme_minimal(base_size = 11)


# ============================================================
# 9. AXE 5 — ÉVOLUTION TEMPORELLE (MISE EN SERVICE)
# ============================================================

niveaux_periode <- c("Avant 1945","1945-1964","1965-1974",
                     "1975-1984","1985-1994","1995-2004","2005 et après")

periode_dist <- equip_clean %>%
  filter(!is.na(periode)) %>%
  count(periode, name = "nb") %>%
  mutate(
    pct    = nb / sum(nb) * 100,
    periode = factor(periode, levels = niveaux_periode)
  ) %>%
  arrange(periode)

print(periode_dist)

ggplot(periode_dist, aes(x = periode, y = nb, fill = periode)) +
  geom_col() +
  geom_text(aes(label = sprintf("%s\n%.1f%%", comma(nb, big.mark = " "), pct)),
            vjust = -0.4, size = 3) +
  scale_y_continuous(labels = comma_format(big.mark = " "),
                     expand = expansion(mult = c(0, .15))) +
  scale_fill_brewer(palette = "Blues") +
  labs(title = "Évolution temporelle de la mise en service des équipements sportifs",
       x = "Période", y = "Nombre d'équipements",
       caption = "Source : Ministère des Sports – RES 2025") +
  theme_minimal(base_size = 11) +
  theme(legend.position = "none", axis.text.x = element_text(angle = 20, hjust = 1))

# Dynamique de construction par propriétaire
periode_proprio <- equip_clean %>%
  filter(!is.na(periode), proprio_type %in% c("Commune","Privé","EPCI","Département","État")) %>%
  mutate(periode = factor(periode, levels = niveaux_periode)) %>%
  count(periode, proprio_type)

ggplot(periode_proprio, aes(x = periode, y = n, color = proprio_type, group = proprio_type)) +
  geom_line(linewidth = 1.2) +
  geom_point(size = 3) +
  scale_y_continuous(labels = comma_format(big.mark = " ")) +
  scale_color_brewer(palette = "Set1") +
  labs(title = "Dynamique de construction par propriétaire et par période",
       x = "Période", y = "Nombre d'équipements", color = "Propriétaire",
       caption = "Source : Ministère des Sports – RES 2025") +
  theme_minimal(base_size = 11) +
  theme(axis.text.x = element_text(angle = 20, hjust = 1))


# ============================================================
# 10. AXE 6 — DENSITÉ D'ÉQUIPEMENTS PAR DÉPARTEMENT
# ============================================================

equip_par_dep <- equip_geo %>%
  filter(!is.na(dep_nom), dep_nom != "") %>%
  count(dep_code, dep_nom, name = "nb_equip") %>%
  arrange(desc(nb_equip))

cat(sprintf("Moyenne équipements / département : %.0f\n", mean(equip_par_dep$nb_equip)))
cat(sprintf("Médiane                           : %.0f\n", median(equip_par_dep$nb_equip)))
print(head(equip_par_dep, 10))

ggplot(slice_max(equip_par_dep, nb_equip, n = 20),
       aes(x = nb_equip, y = fct_reorder(dep_nom, nb_equip), fill = nb_equip)) +
  geom_col() +
  geom_text(aes(label = comma(nb_equip, big.mark = " ")), hjust = -0.1, size = 3.2) +
  scale_fill_gradient(low = "#C6DBEF", high = "#084594") +
  scale_x_continuous(labels = comma_format(big.mark = " "),
                     expand = expansion(mult = c(0, 0.15))) +
  labs(title = "Top 20 des départements par nombre d'équipements sportifs",
       x = "Nombre d'équipements", y = NULL,
       caption = "Source : Ministère des Sports – RES 2025") +
  theme_minimal(base_size = 11) +
  theme(legend.position = "none")


# ============================================================
# 11. AXE 7 — NIVEAU DE PRATIQUE (COMPÉTITION vs LOISIR)
# ============================================================

if ("aps_niveau_pratique" %in% names(activ_clean)) {
  
  niveau_glob <- activ_clean %>%
    filter(!is.na(aps_niveau_pratique), aps_niveau_pratique != "") %>%
    count(aps_niveau_pratique, name = "n") %>%
    mutate(pct = n / sum(n) * 100) %>%
    arrange(desc(n))
  
  print(niveau_glob)
  
  ggplot(niveau_glob,
         aes(x = n, y = fct_reorder(aps_niveau_pratique, n), fill = n)) +
    geom_col() +
    geom_text(aes(label = sprintf("%s  (%.1f%%)", comma(n, big.mark = " "), pct)),
              hjust = -0.05, size = 3.2) +
    scale_fill_gradient(low = "#DADAEB", high = "#54278F") +
    scale_x_continuous(labels = comma_format(big.mark = " "),
                       expand = expansion(mult = c(0, 0.28))) +
    labs(title = "Répartition des équipements selon le niveau de pratique sportive",
         x = "Nombre d'équipements", y = NULL,
         caption = "Source : Ministère des Sports – RES 2025") +
    theme_minimal(base_size = 11) +
    theme(legend.position = "none")
  
  # Niveau de pratique par région
  niveau_region <- activ_geo %>%
    filter(!is.na(aps_niveau_pratique), aps_niveau_pratique != "") %>%
    count(reg_nom, aps_niveau_pratique) %>%
    group_by(reg_nom) %>%
    mutate(pct = n / sum(n) * 100) %>%
    ungroup()
  
  ggplot(niveau_region, aes(x = reg_nom, y = pct, fill = aps_niveau_pratique)) +
    geom_col(position = "fill") +
    coord_flip() +
    scale_y_continuous(labels = percent_format()) +
    scale_fill_brewer(palette = "Set2") +
    labs(title = "Niveau de pratique sportive par région",
         x = NULL, y = "Part (%)", fill = "Niveau",
         caption = "Source : Ministère des Sports – RES 2025") +
    theme_minimal(base_size = 10) +
    theme(legend.position = "bottom")
  
} else {
  cat("Colonne 'aps_niveau_pratique' absente — graphique non généré.\n")
}


# ============================================================
# 12. AXE 8 — DIVERSITÉ SPORTIVE PAR DÉPARTEMENT
# ============================================================

diversite_dep <- activ_geo %>%
  filter(!is.na(dep_nom), dep_nom != "") %>%
  group_by(dep_code, dep_nom) %>%
  summarise(
    nb_disciplines = n_distinct(aps_discipline),
    nb_equip       = n_distinct(equip_numero),
    .groups = "drop"
  ) %>%
  arrange(desc(nb_disciplines))

cat(sprintf("Moyenne disciplines / département : %.1f\n", mean(diversite_dep$nb_disciplines)))
cat(sprintf("Médiane                           : %.0f\n", median(diversite_dep$nb_disciplines)))
print(head(diversite_dep, 10))

# Top 20 des départements les plus diversifiés
ggplot(slice_max(diversite_dep, nb_disciplines, n = 20),
       aes(x = nb_disciplines, y = fct_reorder(dep_nom, nb_disciplines), fill = nb_disciplines)) +
  geom_col() +
  geom_text(aes(label = nb_disciplines), hjust = -0.2, size = 3.2) +
  scale_fill_gradient(low = "#C7E9C0", high = "#006D2C") +
  scale_x_continuous(expand = expansion(mult = c(0, 0.12))) +
  labs(title = "Top 20 des départements les plus diversifiés sportivement",
       subtitle = "Nombre de disciplines sportives distinctes pratiquées",
       x = "Nb de disciplines distinctes", y = NULL,
       caption = "Source : Ministère des Sports – RES 2025") +
  theme_minimal(base_size = 11) +
  theme(legend.position = "none")

# Relation nb équipements × diversité — nuage de points
ggplot(diversite_dep, aes(x = nb_equip, y = nb_disciplines)) +
  geom_point(color = "#2171B5", alpha = 0.6, size = 2.5) +
  geom_smooth(method = "lm", se = TRUE, color = "#E6550D", linewidth = 1) +
  geom_text(data = slice_max(diversite_dep, nb_disciplines, n = 6),
            aes(label = dep_nom), size = 2.8, vjust = -0.7) +
  scale_x_continuous(labels = comma_format(big.mark = " ")) +
  labs(title = "Relation entre nombre d'équipements et diversité sportive",
       x = "Nombre d'équipements", y = "Nombre de disciplines distinctes",
       caption = "Source : Ministère des Sports – RES 2025") +
  theme_minimal(base_size = 11)


# ============================================================
# 13. SYNTHÈSE — CHIFFRES CLÉS
# ============================================================

cat("\n--- CHIFFRES CLÉS ---\n")
cat(sprintf("Installations              : %s\n",    comma(nrow(install_clean), big.mark = " ")))
cat(sprintf("Équipements                : %s\n",    comma(nrow(equip_clean),   big.mark = " ")))
cat(sprintf("Enregistrements APS        : %s\n",    comma(nrow(activ_clean),   big.mark = " ")))
cat(sprintf("Régions couvertes          : %d\n",    n_distinct(equip_geo$reg_nom)))
cat(sprintf("Départements couverts      : %d\n",    nrow(equip_par_dep)))
cat(sprintf("Moy. équipements / dép.    : %.0f\n",  mean(equip_par_dep$nb_equip)))
cat(sprintf("Méd. équipements / dép.    : %.0f\n",  median(equip_par_dep$nb_equip)))
cat(sprintf("Moy. disciplines / dép.    : %.1f\n",  mean(diversite_dep$nb_disciplines)))
cat(sprintf("Part équip. publics        : %.1f%%\n",
            sum(equip_clean$proprio_type %in% c("Commune","EPCI","Département","Région","État")) /
              nrow(equip_clean) * 100))
cat(sprintf("Taux accessibilité PMR     : %.1f%%\n", taux_handi_glob$pct_mob))
cat(sprintf("1re discipline             : %s\n",    top_disciplines$aps_discipline[1]))
cat(sprintf("1er type d'équip.          : %s\n",    top_types$type[1]))
cat(sprintf("Dép. le plus doté          : %s\n",    equip_par_dep$dep_nom[1]))
cat(sprintf("Dép. le plus diversifié    : %s\n",    diversite_dep$dep_nom[1]))

cat("\n== Terminé.\n")