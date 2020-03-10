# !/usr/bin/env python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------
# Application :    Projet XPY, atelier de développement
# Auteurs:          Jacques BRUNEL,
# Copyright:       (c) 2020-03    Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import srcNoelite.DLG_Gestion_adresse as dga

MATRICE_CONFIG = {
    # Chapitre  = categorie ou box verticale
    ("Mémorisation","Chapitre de mémorisation"): [
        # Alinea 11 = ligne dans la box
        {'genre': 'Enum', 'name': 'memoriser', 'label': 'Mémoriser les paramètres', 'value': 3,
         'labels': ["Non", "Oui", "Peut-être"], 'values': [0, 1, 3],
         'help': 'Faut-il mémoriser les paramètres?'},
        # Alinea 12
        {'genre': 'Dir', 'name': 'repertoire', 'label': 'Choix du répertoire', 'value': '',
         'help': 'Veuillez choisir le répertoire'},
    ],
    # Chapitre 2
        ("Autres éléments","Chapitre des autes éléments"): [
        # Alinea 21 et suivants
        {'genre': 'Bool', 'name': 'ouiNon', 'label': 'Etes-vous oui ou non', 'value': True,
         'help': 'Cochez pour le oui'},
        {'genre': 'String', 'name': 'monTexte', 'label': 'Saisir un ctrl', 'value': '',
         'help': 'Saisir votre ctrl'},
        {'genre': 'Int', 'name': 'entier', 'label': 'Saisir un entier', 'value': 0,
         'help': 'Saisir votre nombre entier'},
        {'genre': 'Float', 'name': 'saisieNbre', 'label': 'Saisir un nombre réel', 'value': 0.0,
         'help': 'Saisir votre nombre réel', 'btnLabel': ' ! ', 'btnHelp': 'Là vous pouvez lancer une action par clic',
         'btnAction': 'OnClicFloat', 'ctrlAction': 'OnEnterFloat'},
        {'genre': 'Colour', 'name': 'couleur', 'label': 'Choisir votre couleur', 'value': wx.Colour(255, 0, 0),
         'help': 'Saisir votre couleur préférée', 'btnLabel': None, 'btnHelp': None},
        {'genre': 'MultiChoice', 'name': 'choix', 'label': 'Choix multiples', 'value': [],
         'labels': ["choix 1", "choix 2", "choix3"]},
    ]
}

""" Paramétrage de la construction de la barre de menus """
class MENU():
    def __init__(self,parent):
        self.parent = parent

    def ParamMenu(self):
        """ appelé pour Construire la barre de menus """
        # The "\t..." syntax defines an accelerator key that also triggers
        menu = [
            # Première colonne
                {"code": "&params\tCtrl-P", "label": ("Paramètres"), "items": [
                    {"code": "config", "label": ("&Accès Base de données\tCtrl-A"),
                     "infobulle": (u"Reconfigurer l'accès à la base de données principale"),
                     "image": "Images/16x16/Utilisateur_reseau.png",
                     "action": "On_config", "genre": wx.ITEM_NORMAL},
                    "-",
                {"code": "utilisateurs", "label": (u"Utilisateurs"), "infobulle": (u"Paramétrage des utilisateurs"),
                 "image": "Images/16x16/Personnes.png", "action": "On_param_utilisateurs"},
                "-",
                ]},
        {"code": "&params\tCtrl-P", "label": ("Actions"), "items": [
            {"code": "modifAdresses", "label": ("&Modification des adresses\tCtrl-M"),
             "infobulle": (u"Gestion des adresses des personnes"),
             "image": "Images/16x16/Editeur_email.png",
             "action": "On_gestion_adresses", "genre": wx.ITEM_NORMAL},
            "-",
        ]}
        ]
        return menu

    def On_gestion_adresses(self, event):
        # lance la configuration initiale à la base de donnée pincipale
        dlg = dga.Dialog()
        dlg.ShowModal()
        dlg.Destroy()

    def On_config(self,event):
        #lance la configuration initiale à la base de donnée pincipale
        self.parent.SaisieConfig()

    def On_param_utilisateurs(self,event):
        print('Bonjour On_param_utilisateurs')

if __name__ == "__main__":
    """ Affichage du menu"""
    menu = MENU().ParamMenu()
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
                    #print("action", dictligne['code'])
                    act = "MENU."+dictligne['action']+"(None)"
                    print(act + "\t action >>\t", end='')
                    eval(act)
