# !/usr/bin/env python
# -*- coding: utf-8 -*-

# openRef : Les références gestion partagées

import sys
import os
import wx
import xpy.xAppli as xAppli

# Variables incontournables pour xpy
dictAPPLI = {
            'NOM_APPLICATION'       : "openRef",
            'REP_SOURCES'           : "srcOpenRef",
            'REP_DATA'              : "srcOpenRef/Data",
            'REP_TEMP'              : "srcOpenRef/Temp",
            'NOM_FICHIER_LOG'       : "logsOpenRef.log",
            'OPTIONSCONFIG'         : 'db_prim',
            }

class MyFrame(xAppli.MainFrame):
    def __init__(self, *args, **kw):
        super().__init__( *args, **kw)

        #dictionnaire propre à l'appli
        self.dictAppli = dictAPPLI

        # Intialise et Teste la présence de fichiers dans le répertoire sources
        self.xInit()
        # Crée 'topPanel' et 'topContenu' destroyables
        self.MakeHello("Application de gestion : " + self.dictAppli['NOM_APPLICATION'])

        # Activer le menu décrit dans  PATH_SOURCES/menu.py
        self.MakeMenuBar()
        # Crée un message initial de bas de fenêtre status bar
        self.CreateStatusBar()
        self.SetStatusText("OpenRef sur %s"%self.dictAppli['REP_SOURCES'])
        self.Show()
        #self.SaisieConfig()

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

