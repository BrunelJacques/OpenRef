# !/usr/bin/env python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------
# Application :    Projet XPY, atelier de développement
# Auteurs:          Jacques BRUNEL,
# Copyright:       (c) 2020-03    Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import srcNoelite.DLG_Gestion_adresses as ndga
import srcNoelite.CTRL_Identification as nident

""" Paramétrage de la construction de la barre de menus """
class MENU():
    def __init__(self,parent):
        self.parent = parent

    def ParamMenu(self):
        """ appelé pour Construire la barre de menus """
        menu = [
            # Première colonne
                {"code": "&params\tCtrl-P", "label": ("Paramètres"), "items": [
                    {"code": "config", "label": ("&Accès Base de données\tCtrl-A"),
                     "infobulle": (u"Reconfigurer l'accès à la base de données principale"),
                     "image": "Images/16x16/Utilisateur_reseau.png",
                     "action": "On_config", "genre": wx.ITEM_NORMAL},
                    "-",
                {"code": "utilisateurs", "label": (u"Utilisateurs"), "infobulle": (u"Paramétrage des utilisateurs"),
                 "image": "Images/16x16/Personnes.png", "action": "On_utilisateurs"},
                "-",
                {"code": "quitter", "label": (u"Quitter"), "infobulle": (u"Fin de travail Noelite"),
                 "image": "Images/16x16/Quitter.png", "action": "xQuitter"},
                ]},
        {"code": "&params\tCtrl-P", "label": ("Actions"), "items": [
            {"code": "modifAdresses", "label": ("&Modification d'adresses Individus\tCtrl-I"),
             "infobulle": (u"Gestion de l'adresses de rattachement des personnes (soit la leur soit celle de leur hébergeur"),
             "image": "Images/16x16/Editeur_email.png",
             "action": "On_gestion_adresses", "genre": wx.ITEM_NORMAL},
            {"code": "modifAdresses", "label": ("&Modification d'adresses Familles\tCtrl-F"),
             "infobulle": (u"Gestion des adresses des familles, mais pas de tous les individus de la famille"),
             "image": "Images/16x16/Editeur_email.png",
             "action": "On_gestion_adresses", "genre": wx.ITEM_NORMAL},
            "-",
        ]}
        ]
        return menu

    def On_gestion_adresses(self, event):
        # lance la configuration initiale à la base de donnée pincipale
        dlg = ndga.Dialog()
        dlg.ShowModal()

    def On_config(self,event):
        #lance la configuration initiale à la base de donnée pincipale
        self.parent.SaisieConfig()

    def On_utilisateurs(self,event):
        nident.AfficheUsers()

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
