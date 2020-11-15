# !/usr/bin/env python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------
# Application :    Projet XPY, atelier de développement
# Auteurs:          Jacques BRUNEL,
# Copyright:       (c) 2020-03    Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
from  srcNoelite import DLG_Km_saisie, DLG_Transposition_ficher, CTRL_Identification, \
    DLG_Reglements_gestion, DLG_Adresses_gestion

""" Paramétrage de la construction de la barre de menus """
class MENU():
    def __init__(self,parent):
        self.parent = parent

    def ParamMenu(self):
        """ appelé pour Construire la barre de menus """
        menu = [
        # Première colonne
        {"code": "&params\tCtrl-P", "label": ("Paramètres_et_outils"), "items": [
            {"code": "config", "label": ("&Accès aux Bases de données\tCtrl-A"),
             "infobulle": (u"Reconfigurer l'accès à la base de données principale"),
             "image": "Images/16x16/Utilisateur_reseau.png",
             "action": "On_config", "genre": wx.ITEM_NORMAL},
            "-",
        {"code": "utilisateurs", "label": (u"Utilisateurs"), "infobulle": (u"Paramétrage des utilisateurs"),
         "image": "Images/16x16/Personnes.png", "action": "On_utilisateurs"},
        "-",
        {"code": "transpose", "label": (u"Transposition fichier"),
                "infobulle": (u"Outil de reformatage d'un fichier pour la compta"),
        "image": "Images/16x16/Conversion.png", "action": "On_transpose"},
        {"code": "kmSaisie", "label": (u"Saisie-import des km véhicules"),
                "infobulle": (u"Outil d'import et de saisie pour refacturer les km pour la compta analytique"),
        "image": "Images/16x16/Conversion.png", "action": "On_kmSaisie"},
        "-",
        {"code": "quitter", "label": (u"Quitter"), "infobulle": (u"Fin de travail Noelite"),
         "image": "Images/16x16/Quitter.png", "action": "xQuitter"},
        ]},
        # deuxième colonne
        {"code": "&params\tCtrl-P", "label": ("Actions_Noethys"), "items": [
            {"code": "modifAdresses", "label": ("&Modification d'adresses Individus\tCtrl-I"),
             "infobulle": (u"Gestion de l'adresses de rattachement des personnes (soit la leur soit celle de leur hébergeur"),
             "image": "Images/16x16/Editeur_email.png",
             "action": "On_Adresses_individus", "genre": wx.ITEM_NORMAL},
            {"code": "modifAdressesF", "label": ("&Modification d'adresses Familles\tCtrl-F"),
             "infobulle": (u"Gestion des adresses des familles, mais pas de tous les individus de la famille"),
             "image": "Images/16x16/Editeur_email.png",
             "action": "On_Adresses_familles", "genre": wx.ITEM_NORMAL},
            "-",
            {"code": "gestionReglements", "label": ("&Gestion des règlements\tCtrl-R"),
             "infobulle": (u"Gestion de bordereau de règlements : remise de chèques, arrivée de virements, de dons..."),
             "image": "Images/16x16/Impayes.png",
             "action": "On_reglements_bordereau", "genre": wx.ITEM_NORMAL},
        ]}
        ]
        return menu

    def CouleurFondBureau(self):
        return wx.Colour(96,73,123)

    def ParamBureau(self):
        #appelé pour construire une page d'accueil, même structure que les items du menu pour gérer des boutons
        lstItems = [
            {"code": "inStock", "label": ("&Entrée en stock"),
             "infobulle": (u"Saisie d'une entrée en stock (livraison, achat direct, retour camp, correctifs...)"),
             "image": "Images/80x80/Entree.png",
             "action": self.menuClass.On_utilisateurs, "genre": wx.ITEM_NORMAL},

            {"code": "outStocks", "label": ("&Sortie du stock"),
             "infobulle": (u"Saisie d'une sortie de stock, (repas en cuisine, extérieur, autre camp, correctifs)"),
             "image": "Images/80x80/Sortie.png",
             "action": self.menuClass.On_utilisateurs, "genre": wx.ITEM_NORMAL},

            {"code": "effectifs", "label": ("&Effectifs présents"),
             "infobulle": (u"Gestion des effectifs journaliers des couverts"),
             "image": "Images/80x80/Famille.png",
             "action": self.menuClass.On_utilisateurs, "genre": wx.ITEM_NORMAL},

            {"code": "inventaires", "label": ("&Inventaires"),
             "infobulle": (u"Etat du stock, contrôle, correction pour l'inventaire"),
             "image": "Images/80x80/Inventaire.png",
             "action": self.menuClass.On_utilisateurs, "genre": wx.ITEM_NORMAL},

            {"code": "prixJournee", "label": ("&Prix journée"),
             "infobulle": (u"Calcul du prix de journée après saisie des sorties et de l'effectif"),
             "image": "Images/80x80/Loupe.png",
             "action": self.menuClass.On_utilisateurs, "genre": wx.ITEM_NORMAL},
        ]
        return lstItems

    def On_config(self,event):
        #lance la configuration initiale à la base de donnée pincipale
        ret = self.parent.SaisieConfig()

    def On_utilisateurs(self,event):
        CTRL_Identification.AfficheUsers()


if __name__ == "__main__":
    """ Affichage du menu"""
    menu = MENU(None).ParamMenu()
    for dictColonne in menu:
        print(dictColonne['code'], dictColonne['label'])
        for ligne in dictColonne['items']:
            print('\t',end='')
            if isinstance(ligne,str):
                print(ligne)
            elif isinstance(ligne,dict):
                print(ligne['code'],"\t", ligne['label'],"\n\t\t",ligne.keys())
            else: print("problème!!!!!!!!!!!")
    for dictColonne in menu:
        for dictligne in dictColonne['items']:
            if 'action' in dictligne:
                if dictligne['action'][:1] != 'x':
                    act = "MENU."+dictligne['action']+"(None)"
                    print(act + "\t action >>\t")
