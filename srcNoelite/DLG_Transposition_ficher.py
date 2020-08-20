#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------
# Application :    NoeLITE, gestion des Reglements en lot
# Usage : Gestion de réglements créant éventuellement la prestation associée et le dépot des règlements
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------

import wx
import os
import xpy.xGestion_TableauEditor       as xgte
import xpy.xGestionConfig               as xgc
from xpy.outils.ObjectListView  import ColumnDefn, CellEditor
from xpy.outils                 import xformat,xbandeau,xfichiers


#---------------------- Matrices de paramétres -------------------------------------

TITRE = "Transposition de ficher avec intervention possible"
INTRO = "Importez un fichier, puis complétez l'information dans le tableau avant de l'exporter dans un autre format"
# Infos d'aide en pied d'écran
DIC_INFOS = {'date':"Flèche droite pour le mois et l'année, Entrée pour valider.\nC'est la date de réception du règlement, qui sera la date comptable",
            'libelle':     "S'il est connu, précisez l'affectation (objet) du règlement",
            'montant':      "Montant en €",
             }
# Info par défaut
INFO_OLV = "<Suppr> <Inser> <Ctrl C> <Ctrl V>"

MATRICE_PARAMS = {
("fichiers","Paramètres fichiers"): [
    {'genre': 'dirfile', 'name': 'path', 'label': "Fichier d'origine",'value': "*.csv",
     'help': "Pointez le fichier contenant les valeurs à transposer"},
    {'name': 'formatimp', 'genre': 'Enum', 'label': 'Format import',
                    'help': "Le choix est limité par la programmation", 'value':0, 'values':['LCL CB',],
                    'size':(250,30)},
    {'name': 'formatexp', 'genre': 'Enum', 'label': 'Format export',
                    'help': "Le choix est limité par la programmation", 'value':0, 'values':['compta csv',],
                    'size':(250,30)},
    ],
("compta", "Paramètres comptables"): [
    {'name': 'journal', 'genre': 'String', 'label': 'Journal',
                    'help': "Code journal utilisé dans la compta",'size':(180,30)},
    {'name': 'contrepartie', 'genre': 'String', 'label': 'Contrepartie',
                    'help': "Code comptable du compte de contrepartie de la banque",'size':(250,30)},
    ]
}

def GetBoutons(dlg):
    # description des boutons en pied d'écran et de leurs actions
    return  [
                {'name': 'btnImp', 'label': "Importer\nfichier",
                    'toolTip': "Cliquez ici pour lancer l'importation du fichier selon les paramètres que vous avez défini",
                    'size': (120, 35), 'image': wx.ART_UNDO,'onBtn':dlg.OnImporter},
                {'name': 'btnExp', 'label': "Exporter\nfichier",
                    'toolTip': "Cliquez ici pour lancer l'exportation du fichier selon les paramètres que vous avez défini",
                    'size': (120, 35), 'image': wx.ART_REDO,'onBtn':dlg.OnExporter},
                {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'toolTip':"Cliquez ici pour fermer la fenêtre",
                    'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnClose}
            ]

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal
    return [
            ColumnDefn("date", 'center', 80, 'date', valueSetter=wx.DateTime.Today(),isSpaceFilling=False,
                            stringConverter=xformat.FmtDate),
            ColumnDefn("compte", 'left', 80, 'compte',valueSetter='',isSpaceFilling=False,
                            isEditable=True),
            ColumnDefn("mode", 'centre', 50, 'mode', valueSetter='',choices=['CB carte', 'CHQ chèque',
                                                    'ESP espèces'], isSpaceFilling=False,
                            cellEditorCreator=CellEditor.ChoiceEditor),
            ColumnDefn("piece", 'left', 50, 'piece', isSpaceFilling=False),
            ColumnDefn("libelle", 'left', 200, 'libelle', valueSetter='à saisir', isSpaceFilling=True),
            ColumnDefn("montant", 'right',110, "montant", isSpaceFilling=False, valueSetter=0.0,
                            stringConverter=xformat.FmtDecimal),
            ColumnDefn("nature", 'centre', 50, 'Nature', valueSetter='', isSpaceFilling=False,
                            cellEditorCreator=CellEditor.ChoiceEditor),
            ]

def GetOlvOptions(dlg):
    # retourne les paramètres de l'OLV del'écran général
    return {
            'hauteur': 400,
            'largeur': 600,
            'checkColonne': False,
            'recherche': True,
            'autoAddRow':False,
            'msgIfEmpty':"Fichier non encore importé!",
            'dictColFooter': {"libelle": {"mode": "nombre", "alignement": wx.ALIGN_CENTER}, }
    }

#----------------------- Parties de l'écrans -----------------------------------------

class PNL_params(xgc.PNL_paramsLocaux):
    #panel de paramètres de l'application
    def __init__(self, parent, **kwds):
        self.parent = parent
        #('pos','size','style','name','matrice','donnees','lblbox')
        kwds = {
                'name':"PNL_params",
                'matrice':MATRICE_PARAMS,
                'lblbox':"Paramètres à saisir",
                'pathdata':"srcNoelite/Data",
                'nomfichier':"params",
                'nomgroupe':"transpose"
                }
        super().__init__(parent, **kwds)
        self.Init()

class PNL_corpsReglements(xgte.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xgte.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)
        self.ctrlOlv.Choices={}
        self.lstNewReglements = []
        self.flagSkipEdit = False
        self.oldRow = None

    def OnEditStarted(self,code):
        # affichage de l'aide
        if code in DIC_INFOS.keys():
            self.parent.pnlPied.SetItemsInfos( DIC_INFOS[code],
                                               wx.ArtProvider.GetBitmap(wx.ART_FIND, wx.ART_OTHER, (16, 16)))
        else:
            self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        row, col = self.ctrlOlv.cellBeingEdited
        if not self.oldRow: self.oldRow = row
        if row != self.oldRow:
            track = self.ctrlOlv.GetObjectAt(self.oldRow)
            track.valide = True
        track = self.ctrlOlv.GetObjectAt(row)

        # conservation de l'ancienne valeur
        track.oldValue = None
        try:
            eval("track.oldValue = track.%s"%code)
        except: pass

    def OnEditFinishing(self,code=None,value=None):
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        # flagSkipEdit permet d'occulter les évènements redondants. True durant la durée du traitement
        if self.flagSkipEdit : return
        self.flagSkipEdit = True
        track = self.ctrlOlv.lastGetObject

        # si pas de saisie on passe
        if (not value) or track.oldValue == value:
            self.flagSkipEdit = False
            return

        # l'enregistrement de la ligne se fait à chaque saisie pour gérer les montées et descentes
        okSauve = False

        # enlève l'info de bas d'écran
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.flagSkipEdit = False

    def OnEditFunctionKeys(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        code = self.ctrlOlv.lstCodesColonnes[col]

class PNL_Pied(xgte.PNL_Pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xgte.PNL_Pied.__init__(self,parent, dicPied, **kwds)

class Dialog(wx.Dialog):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self):
        listArbo = os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self, None,-1,title=titre, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.Init()

    def Init(self):
        # définition de l'OLV
        self.dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        self.dicOlv.update(GetOlvOptions(self))
        self.depotOrigine = []
        self.ctrlOlv = None
        self.withDepot = True
        # récup des modesReglements nécessaires pour passer du texte à un ID d'un mode ayant un mot en commun
        choices = []
        self.libelleDefaut = ''
        for colonne in self.dicOlv['lstColonnes']:
            if 'mode' in colonne.valueGetter:
                choices = colonne.choices
            if 'libelle' in colonne.valueGetter:
                self.libelleDefaut = colonne.valueSetter
        self.dicModesRegl = {}
        for item in choices:
            # les descriptifs de modes de règlements ne doivent pas avoir des mots en commun
            lstMots = item.split(' ')
            self.dicModesRegl[item]={'lstMots':lstMots}
            ok = False

        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        self.txtInfo =  "Ici de l'info apparaîtra selon le contexte de la grille de saisie"
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),self.txtInfo]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self,TITRE,INTRO,nomImage="xpy/Images/32x32/Matth.png")
        self.pnlParams = PNL_params(self)
        self.pnlOlv = PNL_corpsReglements(self, self.dicOlv)
        self.pnlPied = PNL_Pied(self, dicPied)
        self.ctrlOlv = self.pnlOlv.ctrlOlv

        # la grille est modifiée selon la coche sans dépôt
        self.choicesNonDiffere = self.ctrlOlv.lstColonnes[self.ctrlOlv.lstCodesColonnes.index('mode')].choices
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.__Sizer()

    def __Sizer(self):
        sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        sizer_base.Add(self.pnlBandeau, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlParams, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlOlv, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlPied, 0, wx.ALL | wx.EXPAND, 3)
        sizer_base.AddGrowableCol(0)
        sizer_base.AddGrowableRow(1)
        self.CenterOnScreen()
        self.SetSizerAndFit(sizer_base)
        self.CenterOnScreen()

    # ------------------- Gestion des actions -----------------------
    def InitOlv(self):
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.formerCodeColonnes()
        self.ctrlOlv.InitObjectListView()
        self.Refresh()

    def GetDonnees(self):
        dic = self.pnlParams.GetValeurs()
        nomFichier = dic['fichiers']['path']
        return xfichiers.GetFichierCsv(nomFichier)

    def OnImporter(self,event):
        self.ctrlOlv.listeDonnees = self.GetDonnees()
        self.InitOlv()

    def OnExporter(self,event):
        pass

    def OnClose(self,event):
        self.pnlParams.SauveParams(close=True)
        if self.IsModal():
            self.EndModal(wx.ID_CANCEL)
        else:
            self.Close()

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dlg = Dialog()
    dlg.ShowModal()
    app.MainLoop()
