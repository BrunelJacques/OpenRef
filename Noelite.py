# !/usr/bin/env python
# -*- coding: utf-8 -*-

# Noelite.py : Lanceur d'une application Noethys version lite

import sys
import os
import wx
import xpy.xAppli as xAppli
import srcNoelite.CTRL_Identification as nid

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
        super().__init__( *args, **kw)

        #dictionnaire propre à l'appli
        self.dictAppli = dictAPPLI

        # Intialise et Teste la présence de fichiers dans le répertoire sources
        self.xInit()
        # Crée 'topPanel' et 'topContenu' destroyables
        self.MakeHello(self.dictAppli['NOM_APPLICATION'].upper()+u"\n\nChoisissez votre option dans le menu")
        # Activer le menu décrit dans  PATH_SOURCES/menu.py
        self.MakeMenuBar()
        # Crée un message initial de bas de fenêtre status bar
        self.CreateStatusBar()
        self.SetStatusText("Noelite est lancé!")
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
        self.Show()

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