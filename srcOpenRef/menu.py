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
import srcOpenRef.GestionModeles as gm

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
    {"code": "&modeles\tCtrl-M", "label": ("Structure donnees"), "items": [
        {"code": "minfos", "label": ("&Gestion des Infos complémentaires "),
                         "infobulle": (u"Permet la gestion des 'infos complémentaires' de la fiche identification"),
                         "image": "Images/16x16/Mecanisme.png",
                         "action": "On_minfos", "genre": wx.ITEM_NORMAL},
        {"code": "mateliers", "label": ("&Gestion des modèles ateliers"),
                         "infobulle": (u"Permet la gestion de la table modèle 'ateliers'"),
                         "image": "Images/16x16/Mecanisme.png",
                         "action": "On_mateliers", "genre": wx.ITEM_NORMAL},
        {"code": "mproduits", "label": ("&Gestion des modèles produits"),
                         "infobulle": (u"Permet la gestion de la table modèle 'produits'"),
                         "image": "Images/16x16/Mecanisme.png",
                         "action": "On_mproduits", "genre": wx.ITEM_NORMAL},
        {"code": "mcouts", "label": ("&Gestion des modèles coûts"),
                         "infobulle": (u"Permet la gestion de la table modèle 'couts'"),
                         "image": "Images/16x16/Mecanisme.png",
                         "action": "On_mcouts", "genre": wx.ITEM_NORMAL},
        "-",
        {"code": "ctypes", "label": ("&Gestion des constantes types"),
                         "infobulle": (u"Permet la gestion de la table 'ctypes'"),
                         "image": "Images/16x16/Mecanisme.png",
                         "action": "On_ctypes", "genre": wx.ITEM_NORMAL},
        {"code": "cplancomptes", "label": ("&Gestion des constantes plancomptes"),
                         "infobulle": (u"Permet la gestion de la table 'cplancomptes'"),
                         "image": "Images/16x16/Mecanisme.png",
                         "action": "On_cplancomptes", "genre": wx.ITEM_NORMAL},
    ]},

    # Troisième colonne
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
        {"code": "affectations\tCtrl-A", "label": ("Affectations manuelles"), "items": [
            {"code": "affect", "label": ("&Choix d'un dossier\tCtrl-D"),
                             "infobulle": (u"Gérer les affectations d'un dossier"),
                             "image": "Images/16x16/Mecanisme.png",
                             "action": "On_affect", "genre": wx.ITEM_NORMAL},
            {"code": "affectgroupe", "label": ("&Choix d'un groupe\tCtrl-G"),
                             "infobulle": (u"Gérer les affectations d'une liste de dossiers"),
                             "image": "Images/16x16/Mecanisme.png",
                             "action": "On_affectGroupe", "genre": wx.ITEM_NORMAL},
            {"code": "affectfilière", "label": ("&Choix d'une filière\tCtrl-F"),
                             "infobulle": (u"Gérer les affectations de dossiers filtrés par une requête"),
                             "image": "Images/16x16/Mecanisme.png",
                             "action": "On_affectFiliere", "genre": wx.ITEM_NORMAL},
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
        ]}]}]
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

    def On_minfos(self, event):
        # appel des gestions de tables modèles et constantes
        gm.Lancement(self.parent, table='mInfos')

    def On_mateliers(self,event):
        #appel des gestions de tables modèles et constantes
        gm.Lancement(self.parent, table='mAteliers')
        

    def On_mproduits(self,event):
        #appel des gestions de tables modèles et constantes
        gm.Lancement(self.parent, table='mProduits')
        

    def On_mcouts(self,event):
        #appel des gestions de tables modèles et constantes
        gm.Lancement(self.parent, table='mCoûts')
        

    def On_ctypes(self,event):
        #appel des gestions de tables modèles et constantes
        gm.Lancement(self.parent, table='cTypes')
        

    def On_cplancomptes(self,event):
        #appel des gestions de tables modèles et constantes
        gm.Lancement(self.parent, table='cPlanComptes')
        

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

    def On_affect(self,event):
        #appel de des affectations d'un dossier
        cfg = gc.DLG_affect(self.parent, style = wx.RESIZE_BORDER )
        cfg.Show()

    def On_affectGroupe(self,event):
        #appel de des affectations de plusieurs dossiers
        cfg = gc.DLG_affect(self.parent, multi='groupe', style = wx.RESIZE_BORDER )
        cfg.Show()

    def On_affectFiliere(self, event):
        # appel de des affectations de plusieurs dossiers
        cfg = gc.DLG_affect(self.parent, multi='filiere', style=wx.RESIZE_BORDER)
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
