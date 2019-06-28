# !/usr/bin/env python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------
# Application :    Projet XPY, atelier de développement
# Auteurs:          Jacques BRUNEL,
# Copyright:       (c) 2019-04     Cerfrance Provence
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import srcOpenRef.GestionConfig as gc

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
    {"code": "implant", "label": ("&Implantation Compta\tCtrl-I"),
                     "infobulle": (u"Définir le répertoire d'accès aux dossiers comptables"),
                     "image": "Images/16x16/Outils.png",
                     "action": "On_implant", "genre": wx.ITEM_NORMAL},
    {"code": "gestables", "label": ("&Gestion des tables Export\tCtrl-G"),
                     "infobulle": (u"Permet de supprimer d'anciennes tables"),
                     "image": "Images/16x16/Supprimer.png",
                     "action": "On_gestables", "genre": wx.ITEM_NORMAL},
    ]},
# Deuxième colonne
{"code": "&Actions\tCtrl-A", "label": ("Actions"), "items": [
    {"code": "imports\tCtrl-A", "label": ("Imports comptas"), "items": [
        {"code": "import", "label": ("&Import d'une compta\tCtrl-I"),
                         "infobulle": (u"Importer les données d'un dossier"),
                         "image": "Images/16x16/Inbox.png",
                         "action": "On_import", "genre": wx.ITEM_NORMAL},
        {"code": "importMulti", "label": ("&Import de comptas\tCtrl-J"),
                         "infobulle": (u"Importer les données de dossiers présents"),
                         "image": "Images/16x16/Fleche_double_bas.png",
                         "action": "On_importMulti", "genre": wx.ITEM_NORMAL},
        ]},
    {"code": "traitements\tCtrl-A", "label": ("Traitement préAnalyses"), "items": [
        {"code": "trait", "label": ("&Traitement d'un dossier\tCtrl-D"),
                         "infobulle": (u"Prétraiter les analyses d'un dossier"),
                         "image": "Images/16x16/Mecanisme.png",
                         "action": "On_trait", "genre": wx.ITEM_NORMAL},
        {"code": "traitgroupe", "label": ("&Traitement d'un groupe\tCtrl-G"),
                         "infobulle": (u"Prétraiter les analyses d'une liste de dossiers"),
                         "image": "Images/16x16/Mecanisme.png",
                         "action": "On_traitGroupe", "genre": wx.ITEM_NORMAL},
        {"code": "traitfilière", "label": ("&Traitement d'une filière\tCtrl-F"),
                         "infobulle": (u"Prétraiter les analyses de dossiers filtrés par une requête"),
                         "image": "Images/16x16/Mecanisme.png",
                         "action": "On_traitFiliere", "genre": wx.ITEM_NORMAL},
        ]},
    {"code": "&Exports\tCtrl-X", "label": ("Export d'Analyses"), "items": [
        {"code": "export", "label": ("&Analyse d'un dossier\tCtrl-D"),
                         "infobulle": (u"Exporter l'analyse d'un dossier"),
                         "image": "Images/16x16/Magique.png",
                         "action": "On_export", "genre": wx.ITEM_NORMAL},
        {"code": "exportgroupe", "label": ("&Analyse d'un groupe\tCtrl-G"),
                         "infobulle": (u"Exporter l'analyse d'une liste de dossiers"),
                         "image": "Images/16x16/Magique.png",
                         "action": "On_exportGroupe", "genre": wx.ITEM_NORMAL},
        {"code": "exportfilière", "label": ("&Analyse d'une filière\tCtrl-F"),
                         "infobulle": (u"Exporter l'analyse de dossiers filtrés par une requête"),
                         "image": "Images/16x16/Magique.png",
                         "action": "On_exportFiliere", "genre": wx.ITEM_NORMAL},
    ]}

]}]
        return menu

    def On_config(self,event):
        #lance la configuration initiale à la base de donnée pincipale
        self.parent.SaisieConfig()

    def On_implant(self,event):
        #appel de l'implantation compta
        cfg = gc.DLG_implantation(self.parent, style = wx.RESIZE_BORDER )
        cfg.Show()

    def On_gestables(self,event):
        #appel de l'implantation compta
        cfg = gc.DLG_gestionTables(self.parent, style = wx.RESIZE_BORDER )
        cfg.Show()

    def On_import(self,event):
        #appel de l'import d'un dossier compta
        cfg = gc.DLG_import(self.parent, style = wx.RESIZE_BORDER )
        cfg.Show()

    def On_importMulti(self,event):
        #appel de l'import de plusieurs dossiers compta
        cfg = gc.DLG_import(self.parent, multi=True, style = wx.RESIZE_BORDER )
        cfg.Show()


    def On_trait(self,event):
        #appel de l'trait d'un dossier
        cfg = gc.DLG_trait(self.parent, style = wx.RESIZE_BORDER )
        cfg.Show()

    def On_traitGroupe(self,event):
        #appel de l'trait de plusieurs dossiers
        cfg = gc.DLG_trait(self.parent, multi='groupe', style = wx.RESIZE_BORDER )
        cfg.Show()

    def On_traitFiliere(self, event):
        # appel de l'trait de plusieurs dossiers
        cfg = gc.DLG_trait(self.parent, multi='filiere', style=wx.RESIZE_BORDER)
        cfg.Show()

    def On_export(self,event):
        #appel de l'export d'un dossier
        cfg = gc.DLG_export(self.parent, style = wx.RESIZE_BORDER )
        cfg.Show()

    def On_exportGroupe(self,event):
        #appel de l'export de plusieurs dossiers
        cfg = gc.DLG_export(self.parent, multi='groupe', style = wx.RESIZE_BORDER )
        cfg.Show()

    def On_exportFiliere(self, event):
        # appel de l'export de plusieurs dossiers
        cfg = gc.DLG_export(self.parent, multi='filiere', style=wx.RESIZE_BORDER)
        cfg.Show()

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
                #print("action", dictligne['code'])
                act = "MENU."+dictligne['action']+"(None,None)"
                print(act + "\t action >>\t", end='')
                eval(act)
