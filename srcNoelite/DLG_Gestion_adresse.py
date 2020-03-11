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
MINSIZE = (1200,650)
WCODE = 150
WLIBELLE = 100
COLONNETRI = 2

import wx
import datetime
import xpy.outils.xbandeau      as xbd
import xpy.xGestion_Tableau     as xgt
import xpy.xUTILS_SaisieParams  as xusp
import xpy.xGestionDB           as xdb
from xpy.outils.ObjectListView import CTRL_Outils

def ComposeLstDonnees(record,lstChamps):
    # retourne les données pour colonnes, extraites d'un record défini par une liste de champs
    lstdonnees=[]
    for ix in range(len(lstChamps)):
        lstdonnees.append(record[ix])
    return lstdonnees

def ValeursDefaut(lstNomsColonnes,lstTypes):
    # Détermine des valeurs par défaut selon le type des variables
    lstValDef = [0,]
    for ix in range(1,len(lstNomsColonnes)):
        tip = lstTypes[ix].lower()
        if tip[:3] == 'int': lstValDef.append(0)
        elif tip[:10] == 'tinyint(1)': lstValDef.append(False)
        elif tip[:5] == 'float': lstValDef.append(0.0)
        elif tip[:4] == 'date': lstValDef.append(datetime.date(1900,1,1))
        else: lstValDef.append('')
    return lstValDef

def LargeursDefaut(lstNomsColonnes,lstTypes):
    # Evaluation de la largeur nécessaire des colonnes selon le type de donnee et la longueur du champ
    lstLargDef = [0,]
    for ix in range(1, len(lstNomsColonnes)):
        tip = lstTypes[ix]
        tip = tip.lower()
        if tip[:3] == 'int': lstLargDef.append(50)
        elif tip[:5] == 'float': lstLargDef.append(60)
        elif tip[:4] == 'date': lstLargDef.append(80)
        elif tip[:7] == 'varchar':
            lg = int(tip[8:-1])*8
            if lg > 150: lg = -1
            lstLargDef.append(lg)
        elif 'blob' in tip:
            lstLargDef.append(250)
        else: lstLargDef.append(40)
    return lstLargDef

def GetIndividus():
    # appel des données à afficher
    lstChamps = ["0","IDindividu", "nom", "prenom","date_naiss", "adresse_auto",
                "rue_resid", "cp_resid", "ville_resid","tel_domicile", "tel_mobile", "mail"]
    lstNomsColonnes = ["null","Individu", "Nom", "Prenom","Naissance","adresse",
                        "rue", "cp", "ville","teldom", "telmob", "mail"]
    lstTypes = ["INTEGER","INTEGER","VARCHAR(100)","VARCHAR(100)","DATE","INTEGER",
                "VARCHAR(100)","VARCHAR(8)","VARCHAR(100)","VARCHAR(11)","VARCHAR(11)","VARCHAR(40)"]
    db = xdb.DB()
    req = """SELECT %s
            FROM individus
            ; """ % (",".join(lstChamps))
    retour = db.ExecuterReq(req, mess='%s.GetIndividus'%NOM_MODULE )
    if retour == "ok":
        recordset = db.ResultatReq()
        if len(recordset) == 0:
            retour = "aucun enregistrement disponible"
    if (not retour == "ok"):
        wx.MessageBox("Erreur : %s" % retour)
        return 'ko'
    db.Close()
    lstCodesColonnes = [xusp.SupprimeAccents(x) for x in lstNomsColonnes]
    lstValDefColonnes = ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = LargeursDefaut(lstNomsColonnes, lstTypes)
    # composition des données du tableau à partir du recordset
    lstDonnees = []
    for record in recordset:
        ligne = ComposeLstDonnees( record, lstChamps)
        lstDonnees.append(ligne)

    # matrice OLV
    lstColonnes = xusp.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
    dicOlv =    {
                'listeColonnes': lstColonnes,
                'listeDonnees': lstDonnees,
                'checkColonne': False,
                'colonneTri': COLONNETRI,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                'dictColFooter': {"nom": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},}
                }
    return dicOlv

class Dialog(wx.Dialog):
    def __init__(self, titre=TITRE, intro=INTRO):
        wx.Dialog.__init__(self, None, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
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

        # Initialisations
        self.__init_olv()
        self.__set_properties()
        self.__do_layout()

    def __init_olv(self):
        dicOlv = GetIndividus()
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
        self.ctrlOlv.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.OnDblClicOk)

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
            print(self.choix.individu)
            event.Skip()

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
