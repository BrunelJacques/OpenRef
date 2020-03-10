#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------
# Application :    NoeLITE, gestion des adresses des individus
# Auteur:           Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------

NOM_MODULE = "DLG_Gestion_adresse"
ACTION = "Gestion\nadresse"
TITRE = "Choisissez un individu !"
INTRO = "Double clic pour lancer la gestion de l'adresse"
MINSIZE = (900,550)
WCODE = 150
WLIBELLE = 100
COLUMNSORT = 0

import wx
import xpy.outils.xbandeau as xbd
import xpy.xGestion_Tableau as xgt
from xpy.outils.ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils
import xpy.xGestionDB as xdb
import xpy.outils.xformat as xfmt
class Dialog(wx.Dialog):
    def __init__(self, titre=TITRE, intro=INTRO):
        wx.Dialog.__init__(self, None, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.SetTitle(NOM_MODULE)
        self.choix= None
        self.avecFooter = True
        self.barreRecherche = True

        # Bandeau
        self.ctrl_bandeau = xbd.Bandeau(self, titre=titre, texte=intro,  hauteur=18, nomImage="xpy/Images/32x32/Matth.png")

        # Boutons
        bmpok = wx.Bitmap("xpy/Images/32x32/Action.png")
        self.bouton_ok = wx.Button(self, id = wx.ID_APPLY,label=(ACTION))
        self.bouton_ok.SetBitmap(bmpok)
        bmpabort = wx.Bitmap("xpy/Images/32x32/Quitter.png")
        self.bouton_fermer = wx.Button(self, id = wx.ID_CANCEL,label=(u"Fermer"))
        self.bouton_fermer.SetBitmap(bmpabort)


        self.__init_olv()
        self.__set_properties()
        self.__do_layout()

    def __init_olv(self):
        liste_Colonnes = [
            ColumnDefn("clé", 'left', 70, "cle", valueSetter=1, isSpaceFilling=True, ),
            ColumnDefn("mot d'ici", 'left', 200, "mot", valueSetter='', isEditable=False),
            ColumnDefn("nbre", 'right', -1, "nombre", isSpaceFilling=True, valueSetter=0.0,
                       stringConverter= xfmt.FmtDecimal),
            ColumnDefn("prix", 'left', 80, "prix", valueSetter=0.0, isSpaceFilling=True,
                       stringConverter=xfmt.FmtMontant),
            ColumnDefn("date", 'center', 80, "date", valueSetter=wx.DateTime.FromDMY(1, 0, 1900), isSpaceFilling=True,
                       stringConverter=xfmt.FmtDate),
            ColumnDefn("date SQL", 'center', 80, "datesql", valueSetter='2000-01-01', isSpaceFilling=True,
                       stringConverter=xfmt.FmtDate)
        ]
        liste_Donnees = [[18, "Bonjour", -1230.05939, -1230.05939, None, None],
                         [19, "Bonsoir", 57.5, 208.99, wx.DateTime.FromDMY(15, 11, 2018), '2019-03-29'],
                         [1, "Jonbour", 0, 209, wx.DateTime.FromDMY(6, 11, 2018), '2019-03-01'],
                         [29, "Salut", 57.082, 209, wx.DateTime.FromDMY(28, 1, 2019), '2019-11-23'],
                         [None, "Salutation", 57.08, 0, wx.DateTime.FromDMY(1, 7, 1997), '2019-10-24'],
                         [2, "Python", 1557.08, 29, wx.DateTime.FromDMY(7, 1, 1997), '2000-12-25'],
                         [3, "Java", 57.08, 219, wx.DateTime.FromDMY(1, 0, 1900), ''],
                         [98, "langage C", 10000, 209, wx.DateTime.FromDMY(1, 0, 1900), ''],
                         ]
        dicOlv = {'listeColonnes': liste_Colonnes,
                  'listeDonnees': liste_Donnees,
                  'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                  'dictColFooter': {"mot": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},}
                  }
        pnlOlv = xgt.PanelListView(self,**dicOlv)
        if self.avecFooter:
            self.ctrlOlv = pnlOlv.ctrl_listview
            self.olv = pnlOlv
        else:
            self.ctrlOlv = xgt.ListView(self,**dicOlv)
            self.olv = self.ctrlOlv
        if self.barreRecherche:
            self.ctrloutils = CTRL_Outils(self, listview=self.ctrlOlv, afficherCocher=False)
        self.ctrlOlv.MAJ()

    def __set_properties(self):
        self.SetMinSize(MINSIZE)
        self.bouton_fermer.SetToolTip(u"Cliquez ici pour fermer")
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnDblClicOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnDblClicFermer, self.bouton_fermer)
        #self.listview.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.OnDblClic)

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)
        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        sizerolv = wx.BoxSizer(wx.VERTICAL)
        sizerolv.Add(self.olv, 10, wx.EXPAND, 10)
        if self.barreRecherche:
            sizerolv.Add(self.ctrloutils, 0, wx.EXPAND, 10)
        gridsizer_base.Add(sizerolv, 10, wx.EXPAND, 10)
        gridsizer_base.Add(wx.StaticLine(self), 0, wx.TOP| wx.EXPAND, 3)

        # Boutons
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=0, hgap=0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_ok, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_fermer, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(0)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND,5)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnDblClicFermer(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnDblClicOk(self, event):
        self.choix = self.ctrlOlv.GetSelectedObject()
        if self.choix == None:
            dlg = wx.MessageDialog(self, (u"Pas de sélection faite !\nIl faut choisir ou cliquer sur annuler"), (u"Accord Impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.EndModal(wx.ID_OK)

    def OnDblClic(self, event):
        self.choix = self.listview.GetSelectedObject()
        self.EndModal(wx.ID_OK)

    def GetChoix(self):
        self.choix = self.listview.GetSelectedObject()
        return self.choix

#-------------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    f = Dialog()
    app.SetTopWindow(f)
    print(f.ShowModal())
    app.MainLoop()
