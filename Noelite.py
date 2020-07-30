# !/usr/bin/env python
# -*- coding: utf-8 -*-

# Noelite.py : Lanceur d'une application Noethys version lite

import sys
import os
import wx
import xpy.xAppli as xAppli
import xpy.outils.xaccueil as xaccueil
import srcNoelite.CTRL_Identification as nid
import srcNoelite.menu as menu

# Variables incontournables pour xpy
dictAPPLI = {
            'NOM_APPLICATION'       : "noelite",
            'REP_SOURCES'           : "srcNoelite",
            'REP_DATA'              : "srcNoelite/Data",
            'REP_TEMP'              : "srcNoelite/Temp",
            'NOM_FICHIER_LOG'       : "logsNoelite.log",
            'OPTIONSCONFIG'         : ["db_prim"],
}

class MyFrame(xAppli.MainFrame):
    def __init__(self, *args, **kw):
        kw['size'] = (1000,700)
        super().__init__( *args, **kw)

        #dictionnaire propre à l'appli
        self.dictAppli = dictAPPLI
        self.menuClass = menu.MENU(self)
        self.dictMenu = menu.MENU.ParamMenu(self)
        self.dictButtons = menu.MENU.ParamBureau(self)
        if hasattr(menu.MENU,"CouleurFondBureau"):
            self.couleur_fond = menu.MENU.CouleurFondBureau(self)

        # Intialise et Teste la présence de fichiers dans le répertoire sources
        self.xInit()

        # Crée 'topPanel' et 'topContenu' destroyables
        self.MakeBureau(pnlTitre=xaccueil.Panel_Titre(self,texte="NOELITE\n\nCompléments Noethys",
                                                      pos=(0,0),couleurFond=self.couleur_fond),
                        pnlBtnActions=xaccueil.Panel_Buttons(self,self.dictButtons,couleurFond=self.couleur_fond))

        # Activer le menu décrit dans  PATH_SOURCES/menu.py
        test = os.getcwd()
        self.MakeMenuBar()
        # Crée un message initial de bas de fenêtre status bar
        self.CreateStatusBar()
        self.SetStatusText("Noelite est lancé!")
        self.Show()
        dlg = nid.Dialog(self)
        if dlg.echec:
            self.Destroy()
            return
        ret = dlg.ShowModal()
        self.dicUser = dlg.GetDictUtilisateur()
        dlg.Destroy()
        if self.dicUser:
            etat = True
        else: etat = False
        for numMenu in range(1,2):
            self.menu.EnableTop(numMenu, etat)

class MyApp(wx.App):
    def OnInit(self):
        xAppli.CrashReport(dictAPPLI)
        # Création de la frame principale
        myframe = MyFrame(None)
        self.SetTopWindow(myframe)
        return True

if __name__ == "__main__":
    # Lancement de l'application
    app = MyApp(redirect=False)
    app.MainLoop()