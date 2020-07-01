#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------
# Application :    NoeLITE, ventilation des Reglements
# Usage:           trace les actions dans la table historique
# Auteur:           Ivan LUCAS, traduit python3 Jacques BRUNEL
# Copyright:       (c) 2010-15 Ivan LUCAS
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------------


import datetime
import xpy.xGestionDB               as xdb
import srcNoelite.UTILS_Utilisateurs as nuu

CATEGORIES = {
    0: ("Action Inconnue"),
    1: ("Ouverture d'un fichier"),
    2: ("Fermeture d'un fichier"),
    3: ("Nouvel utilisateur"),
    4: ("Création d'une famille"),
    5: ("Suppression d'une famille"),
    6: ("Saisie d'un règlement"),
    7: ("Modification d'un règlement"),
    8: ("Suppression d'un règlement"),
    9: ("Saisie de consommations"),
    10: ("Suppression de consommations"),
    11: ("Création d'un individu"),
    12: ("Suppression d'un individu"),
    13: ("Rattachement d'un individu"),
    14: ("Détachement d'un individu"),
    15: ("Saisie d'une pièce"),
    16: ("Modification d'une pièce"),
    17: ("Suppression d'une pièce"),
    18: ("Inscription à une activité"),
    19: ("Désinscription d'une activité"),
    20: ("Modification de l'inscription à une activité"),
    21: ("Saisie d'une cotisation"),
    22: ("Modification d'une cotisation"),
    23: ("Suppression d'une cotisation"),
    24: ("Saisie d'un message"),
    25: ("Modification d'un message"),
    26: ("Suppression d'un message"),
    27: ("Edition d'une attestation de présence"),
    28: ("Edition d'un reçu de règlement"),
    29: ("Modification de consommations"),
    30: ("Inscription scolaire"),
    31: ("Modification d'une inscription scolaire"),
    32: ("Suppression d'une inscription scolaire"),
    33: ("Envoi d'un Email"),
    34: ("Edition d'une confirmation d'inscription"),
    35: ("Génération d'un fichier XML SEPA"),
    72: ("Transfert en compta"),
    73: ("Mise en cohérence automatique"),
    74: ("Suppression Facturation"),
    75: ("Modification Facturation"),
    76: ("Facturation"),
    77: ("Suppression Inscription"),
    78: ("Modification Inscription"),
    79: ("Inscription"),
}

DICT_COULEURS = {
    (166, 245, 156): (4, 5),
    (236, 245, 156): (6, 7, 8),
    (245, 208, 156): (9, 10, 29),
    (245, 164, 156): (11, 12, 13, 14),
    (156, 245, 160): (15, 16, 17),
    (156, 245, 223): (18, 19, 20),
    (156, 193, 245): (21, 22, 23),
    (170, 156, 245): (24, 25, 26),
    (231, 156, 245): (27, 28),
}


def InsertActions(listeActions=[], DB=None):
    """ dictAction = { IDutilisateur : None, IDfamille : None, IDindividu : None, IDcategorie : None, action : u"" } """
    date = str(datetime.date.today())
    heure = "%02d:%02d:%02d" % (
    datetime.datetime.now().hour, datetime.datetime.now().minute, datetime.datetime.now().second)

    # Traitement des actions
    listeAjouts = []
    for dictAction in listeActions:
        if "IDutilisateur" in dictAction.keys():
            IDutilisateur = dictAction["IDutilisateur"]
        else:
            IDutilisateur = nuu.GetIDutilisateur()
        if "IDfamille" in dictAction.keys():
            IDfamille = dictAction["IDfamille"]
        else:
            IDfamille = None
        if "IDindividu" in dictAction.keys():
            IDindividu = dictAction["IDindividu"]
        else:
            IDindividu = None
        if "IDcategorie" in dictAction.keys():
            IDcategorie = dictAction["IDcategorie"]
        else:
            IDcategorie = None
        if "action" in dictAction.keys():
            action = dictAction["action"]
        else:
            action = u""
        if len(action) >= 500:
            action = action[:495] + "..."  # Texte limité à 499 caractères

        listeAjouts.append((date, heure, IDutilisateur, IDfamille, IDindividu, IDcategorie, action))

    # Enregistrement dans la base
    if len(listeAjouts) > 0:
        req = u"INSERT INTO historique (date, heure, IDutilisateur, IDfamille, IDindividu, IDcategorie, action) VALUES (?, ?, ?, ?, ?, ?, ?)"
        if DB == None:
            DB = xdb.DB()
            DB.Executermany(req, listeAjouts, commit=False)
            DB.Commit()
            DB.Close()
        else:
            DB.Executermany(req, listeAjouts, commit=False)



