#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------
# Application :    Noelite, transposition de fichier comptable
# Usage : Reécrire dans un formatage différent avec fonctions de transposition
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------

import wx
import xpy.xGestion_TableauEditor       as xgte
import xpy.xGestionConfig               as xgc
import xpy.xUTILS_SaisieParams          as xusp
from srcNoelite                 import UTILS_Compta
from xpy.outils.ObjectListView  import ColumnDefn
from xpy.outils                 import xformat,xbandeau,xfichiers,xexport

#---------------------- Paramètres du programme -------------------------------------

TITRE = "Transposition de ficher avec intervention possible"
INTRO = "Importez un fichier, puis complétez l'information dans le tableau avant de l'exporter dans un autre format"
# Infos d'aide en pied d'écran
DIC_INFOS = {'date':"Flèche droite pour le mois et l'année, Entrée pour valider.\nC'est la date de réception du règlement, qui sera la date comptable",
            'compte':    "<F4> Choix d'un compte fournisseur, ou saisie directe du compte",
            'libelle':     "S'il est connu, précisez l'affectation (objet) du règlement",
            'montant':      "Montant en €",
             }

# Info par défaut
INFO_OLV = "<Suppr> <Inser> <Ctrl C> <Ctrl V>"

# Fonctions de transposition entrée et sortie à gérer pour chaque item FORMAT_xxxx pour les spécificités
def ComposeFuncImp(dicParams,donnees,champsOut,compta,table):
    # accès aux comptes
    # 'in' est le fichier entrée, 'out' est l'OLV
    lstOut = []
    formatIn = dicParams['fichiers']['formatin']
    noPiece = dicParams['compta']['lastpiece']
    champsIn = FORMATS_IMPORT[formatIn]['champs']
    nblent = FORMATS_IMPORT[formatIn]['lignesentete']
    # teste la cohérence de la première ligne importée
    if len(champsIn) != len(donnees[nblent]):
        wx.MessageBox("Problème de fichier d'origine\n\nLe paramétrage attend les colonnes suivantes:\n\t%s"%str(champsIn) \
                        + "\mais la ligne %d comporte %d champs :\n%s"%(nblent,len(donnees[nblent]),donnees[nblent]))
        return []

    ixLibelle = champsOut.index('libelle')
    ixCompte = champsOut.index('compte')
    ixAppel = champsOut.index('appel')
    ixLibCpt = champsOut.index('libcpt')

    def enrichiLigne(ligne):
        if len(ligne) != len(champsOut): return
        # composition des champs en liens avec la compta
        record = compta.GetOneAuto(table,filtre=ligne[ixLibelle][lgPref:])
        # la recherche de compte a matché
        if record:
            ligne[ixCompte] = record[0]
            ligne[ixAppel]  = record[1]
            ligne[ixLibCpt] = record[2]
        else:
            ligne[ixAppel] = compta.filtreTest

    # déroulé du fichier entrée
    lgPref = 6
    for ligne in donnees[nblent:]:
        if len(champsIn) != len(ligne):
            # ligne batarde ignorée
            continue
        noPiece = xformat.IncrementeRef(noPiece)
        ligneOut = []
        for champ in champsOut:
            valeur = None
            if champ    == 'date':
                if 'date' in champsIn:
                    valeur = xformat.FinDeMois(ligne[champsIn.index(champ)])
            elif champ == 'piece':
                    valeur = noPiece
            elif champ  == 'libelle':
                # ajout du début de date dans le libellé
                if 'date' in champsIn and 'libelle' in champsIn:
                    prefixe = ligne[champsIn.index('date')].strip()[:lgPref-1]+' '
                    valeur = prefixe + ligne[champsIn.index('libelle')]
            # récupération des champs homonymes
            elif champ in champsIn:
                valeur = ligne[champsIn.index(champ)]
            ligneOut.append(valeur)
        if compta:
            enrichiLigne(ligneOut)
        lstOut.append(ligneOut)
    return lstOut

def ComposeFuncExp(dicParams,donnees,champsIn):
    # 'in' est l'OLV, 'out' est le fichier de sortie
    lstOut = []
    formatOut = dicParams['fichiers']['formatexp']
    champsOut = FORMATS_EXPORT[formatOut]['champs']
    for ligne in donnees:
        ligneOut = []
        typePiece = "B" # cas par défaut B comme carte Bancaire
        for champ in champsOut:
            valeur = None
            # composition des champs sortie
            if champ    == 'journal':   valeur = dicParams['compta']['journal']
            elif champ  == 'typepiece': valeur = typePiece
            elif champ  == 'contrepartie': valeur = dicParams['compta']['contrepartie']
            elif champ  == 'debit':
                montant = float(ligne.donnees[champsIn.index("montant")].replace(",","."))
                if montant < 0.0: valeur = -montant
                else: valeur = 0.0
            elif champ  == 'credit':
                montant = float(ligne.donnees[champsIn.index("montant")].replace(",","."))
                if montant >= 0.0: valeur = montant
                else: valeur = 0.0
            # récupération des champs homonymes (date, compte, libelle, piece...)
            elif champ in champsIn:
                valeur = ligne.donnees[champsIn.index(champ)]
            ligneOut.append(valeur)
        lstOut.append(ligneOut)
        # ajout de la contrepartie banque
        ligneBanque = [x for x in ligneOut]
        ligneBanque[champsOut.index('contrepartie')]    = ligneOut[champsOut.index('compte')]
        ligneBanque[champsOut.index('compte')]          = dicParams['compta']['contrepartie']
        ligneBanque[champsOut.index('debit')]    = ligneOut[champsOut.index('credit')]
        ligneBanque[champsOut.index('credit')]    = ligneOut[champsOut.index('debit')]
        lstOut.append(ligneBanque)
    return lstOut

# formats possibles des fichiers en entrées et sortie, utiliser les mêmes codes des champs pour les 'ComposeFunc'
FORMATS_IMPORT = {"LCL carte":{ 'champs':['date','montant','mode',None,'libelle',None,None,'codenat','nature',],
                                'lignesentete':3,
                                'fonction':ComposeFuncImp,
                                'table':'fournisseurs'}}

FORMATS_EXPORT = {"Quadra via Excel":{  'champs':['journal','date','compte','typepiece','libelle','debit','credit',
                                                'piece','contrepartie'],
                                        'widths':[40, 80, 60, 25, 240, 60, 60, 60, 60],
                                        'fonction':ComposeFuncExp,
                                        'compta':'quadra'}}

# Description des paramètres à choisir en haut d'écran
MATRICE_PARAMS = {
("fichiers","Paramètres fichiers"): [
    {'genre': 'dirfile', 'name': 'path', 'label': "Fichier d'origine",'value': "*.csv",
     'help': "Pointez le fichier contenant les valeurs à transposer"},
    {'name': 'formatin', 'genre': 'Enum', 'label': 'Format import',
                    'help': "Le choix est limité par la programmation", 'value':0,
                    'values':[x for x in FORMATS_IMPORT.keys()],
                    'size':(250,30)},
    {'name': 'formatexp', 'genre': 'Enum', 'label': 'Format export',
                    'help': "Le choix est limité par la programmation", 'value':0,
                    'values':[x for x in FORMATS_EXPORT.keys()],
                    'ctrlAction':'OnChoixExport',
                    'size':(250,30)},
    ],
("compta", "Paramètres comptables"): [
    {'name': 'journal', 'genre': 'Combo', 'label': 'Journal','ctrlAction':'OnCtrlJournal',
                    'help': "Code journal utilisé dans la compta",'size':(250,30),
                    'values':['BQ','LCL','LBP','CCP'],
                    'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un journal",
                    'btnAction': 'OnBtnJournal'},
    {'name': 'contrepartie', 'genre': 'String', 'label': 'Contrepartie',
                    'help': "Code comptable du compte de contrepartie de la banque",'size':(250,30)},
    {'name': 'lastpiece', 'genre': 'String', 'label': 'Dernier no de pièce',
                    'help': "Préciser avant l'import le dernier numéro de pièce à incrémenter",'size':(250,30)},
    ]
}

# description des boutons en pied d'écran et de leurs actions
def GetBoutons(dlg):
    return  [
                {'name': 'btnImp', 'label': "Importer\nfichier",
                    'toolTip': "Cliquez ici pour lancer l'importation du fichier selon les paramètres que vous avez défini",
                    'size': (120, 35), 'image': wx.ART_UNDO,'onBtn':dlg.OnImporter},
                {'name': 'btnExp', 'label': "Exporter\nfichier",
                    'toolTip': "Cliquez ici pour lancer l'exportation du fichier selon les paramètres que vous avez défini",
                    'size': (120, 35), 'image': wx.ART_REDO,'onBtn':dlg.OnExporter},
                {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'toolTip':"Cliquez ici pour fermer la fenêtre",
                    'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnFermer}
            ]

# description des colonnes de l'OLV (données affichées)
def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal
    return [
            ColumnDefn("Date", 'center', 80, 'date', valueSetter=wx.DateTime.Today(),isSpaceFilling=False,
                            stringConverter=xformat.FmtDate),
            ColumnDefn("Cpt No", 'left', 70, 'compte',valueSetter='',isSpaceFilling=False,
                            isEditable=True),
            ColumnDefn("Cpt Appel", 'left', 70, 'appel',valueSetter='',isSpaceFilling=False,
                            isEditable=False),
            ColumnDefn("Cpt Libellé ", 'left', 150, 'libcpt',valueSetter='',isSpaceFilling=False,
                            isEditable=False),
            ColumnDefn("Mode", 'centre', 60, 'mode', valueSetter='', isSpaceFilling=False,),
            ColumnDefn("NoPièce", 'left', 70, 'piece', isSpaceFilling=False),
            ColumnDefn("Libelle", 'left', 220, 'libelle', valueSetter='', isSpaceFilling=True),
            ColumnDefn("Montant", 'right',70, "montant", isSpaceFilling=False, valueSetter=0.0,
                            stringConverter=xformat.FmtDecimal),
            ColumnDefn("Nature", 'left', 100, 'nature', valueSetter='', isSpaceFilling=False,
                            isEditable=False)
            ]

# paramètre les options de l'OLV
def GetOlvOptions(dlg):
    return {
            'hauteur': 400,
            'largeur': 900,
            'checkColonne': False,
            'recherche': True,
            'autoAddRow':False,
            'msgIfEmpty':"Fichier non encore importé!",
            'dictColFooter': {"libelle": {"mode": "nombre", "alignement": wx.ALIGN_CENTER}, }
    }

# fonction d'enrichissement des champs


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

class PNL_corpsOlv(xgte.PNL_corps):
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

    def OnEditFinishing(self,code=None,value=None,parent=None):
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        # flagSkipEdit permet d'occulter les évènements redondants. True durant la durée du traitement
        row, col = self.ctrlOlv.cellBeingEdited
        if self.flagSkipEdit : return
        self.flagSkipEdit = True
        track = self.ctrlOlv.lastGetObject

        # si pas de saisie on passe
        if (not value) or track.oldValue == value:
            self.flagSkipEdit = False
            return

        # l'enregistrement de la ligne se fait à chaque saisie pour gérer les montées et descentes
        okSauve = False

        # Traitement des spécificités selon les zones
        if code == 'compte':
            table = self.parent.table
            record = self.parent.compta.GetOneAuto(table,value)
            newfiltre = self.parent.compta.filtreTest
            # tentative de recherche mannuelle
            if not record:
                record = self.parent.compta.ChoisirItem('fournisseurs',newfiltre)
            # alimente les champs ('compte','appel','libelle'), puis répand l'info
            if record:
                track.compte = record[0].upper()
                track.exappel = track.appel
                track.appel = record[1].upper()
                track.libcpt = record[2]
                # la valeur d'origine va être strockée par parent  pour cellEditor
                if parent:
                    #parent n'est pas self.parent!!!
                    parent.valeur = track.compte
                # RepandreCompte sur les autres lignes similaires
                self.RepandreCompte(track)
                self.ctrlOlv.Refresh()

        # enlève l'info de bas d'écran
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.flagSkipEdit = False

    def OnEditFunctionKeys(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        code = self.ctrlOlv.lstCodesColonnes[col]
        if event.GetKeyCode() == wx.WXK_F4 and code == 'compte':
            # F4 Choix compte
            item = self.parent.compta.ChoisirItem(table=self.parent.table,filtre='')
            if item:
                self.OnEditFinishing('compte',item[0])
                self.ctrlOlv.lastGetObject.compte = item[0]

    def RepandreCompte(self,track=None):
        for object in self.ctrlOlv.innerList:
            if object.appel == track.exappel:
                object.compte = track.compte
                object.appel  = track.appel
                object.libcpt = track.libcpt

class PNL_Pied(xgte.PNL_Pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xgte.PNL_Pied.__init__(self,parent, dicPied, **kwds)

class Dialog(xusp.DLG_vide):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self):
        super().__init__(None,name='DLG_Transposition_fichier')
        self.ctrlOlv = None
        self.txtInfo =  "Non connecté à une compta"
        self.dicOlv = self.GetParamsOlv()
        self.Init()
        self.Sizer()

    # Récup des paramètrages pour composer l'écran
    def GetParamsOlv(self):
        # définition de l'OLV
        dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        dicOlv.update(GetOlvOptions(self))
        return dicOlv

    # Initialisation des panels
    def Init(self):
        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),self.txtInfo]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self,TITRE,INTRO,nomImage="xpy/Images/32x32/Matth.png")
        self.pnlParams = PNL_params(self)
        self.pnlOlv = PNL_corpsOlv(self, self.dicOlv)
        self.pnlPied = PNL_Pied(self, dicPied)
        self.ctrlOlv = self.pnlOlv.ctrlOlv
        # connextion compta et affichage bas d'écran
        self.compta = self.GetCompta()
        self.table = self.GetTable()

        self.Bind(wx.EVT_CLOSE,self.OnFermer)

    def Sizer(self):
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

    def OnCtrlJournal(self,evt):
        # tronque pour ne garder que le code journal sur trois caractères maxi
        box = self.pnlParams.GetBox('compta')
        valeur = self.pnlParams.lstBoxes[1].GetOneValue('journal')
        valeur = valeur[:3].strip()
        box.SetOneValue('journal', valeur)
        if self.compta:
            item = self.compta.GetOneAuto(table='journaux',filtre=valeur)
            if item:
                box = self.pnlParams.GetBox('compta')
                box.SetOneValue('journal',valeur)
                box.SetOneValue('contrepartie',item[2])

    def OnBtnJournal(self,evt):
        if self.compta:
            item = self.compta.ChoisirItem(table='journaux')
            if item:
                box = self.pnlParams.GetBox('compta')
                box.SetOneValue('journal',item[0])
                box.SetOneValue('contrepartie',item[2])

    def OnChoixExport(self,evt):
        self.compta = self.GetCompta()
        self.table = self.GetTable()

    def InitOlv(self):
        self.pnlParams.GetValeurs()
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.formerCodeColonnes()
        self.ctrlOlv.InitObjectListView()
        self.Refresh()

    def GetDonneesIn(self):
        # importation des donnéees du fichier entrée
        dic = self.pnlParams.GetValeurs()
        nomFichier = dic['fichiers']['path']
        entrees = xfichiers.GetFichierCsv(nomFichier)
        return entrees

    def GetCompta(self):
        dic = self.pnlParams.GetValeurs()
        formatExp = dic['fichiers']['formatexp']
        compta = None
        if formatExp in FORMATS_EXPORT.keys() :
            nomCompta = FORMATS_EXPORT[formatExp]['compta']
            compta = UTILS_Compta.Compta(self, compta=nomCompta)
            if not compta.db: compta = None
        if not compta:
            txtInfo = "Echec d'accès à la compta associée à %s!!!"%formatExp
            image = wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_OTHER, (16, 16))
        else:
            txtInfo = "Connecté à la compta %s..."%nomCompta
            image = wx.ArtProvider.GetBitmap(wx.ART_TIP, wx.ART_OTHER, (16, 16))
        self.pnlPied.SetItemsInfos(txtInfo,image)
        # appel des journaux
        if compta:
            lstJournaux = compta.GetJournaux()
            lstLibJournaux = [(x[0]+"   ")[:3]+' - '+x[1] for x in lstJournaux]
            box = self.pnlParams.GetBox('compta')
            valeur = self.pnlParams.lstBoxes[1].GetOneValue('journal')
            box.SetOneValues('journal',lstLibJournaux)
            box.SetOneValue('journal',valeur)
        return compta

    def GetTable(self):
        dicParams = self.pnlParams.GetValeurs()
        formatIn = dicParams['fichiers']['formatin']
        return FORMATS_IMPORT[formatIn]['table']

    def EnrichiTrack(self,ligne,lstCodesColonnes):
        # composition des champs en liens avec la compta
        ixLibelle = lstCodesColonnes.index('libelle')
        ixCompte = lstCodesColonnes.index('compte')
        ixAppel = lstCodesColonnes.index('appel')
        ixLibCpt = lstCodesColonnes.index('libcpt')
        record = self.compta.GetOneAuto(self.table,filtre=ligne[ixLibelle])
        # la recherche de compte a matché
        if record:
            ligne[ixCompte] = record[0]
            ligne[ixAppel]  = record[1]
            ligne[ixLibCpt] = record[2]
        else:
            ligne[ixCompte] = self.compta.filtreTest

    def OnImporter(self,event):
        dicParams = self.pnlParams.GetValeurs()
        formatIn = dicParams['fichiers']['formatin']
        self.table = FORMATS_IMPORT[formatIn]['table']
        self.ctrlOlv.listeDonnees = FORMATS_IMPORT[formatIn]['fonction'](dicParams,
                                                           self.GetDonneesIn(),
                                                           self.ctrlOlv.lstCodesColonnes,self.compta,self.table)
        if self.compta and False:
            for ligne in self.ctrlOlv.listeDonnees:
                self.EnrichiTrack(ligne,self.ctrlOlv.lstCodesColonnes,self.table)
        self.InitOlv()

    def OnExporter(self,event):
        dic = self.pnlParams.GetValeurs()
        formatExp = dic['fichiers']['formatexp']
        champs = FORMATS_EXPORT[formatExp]['champs']
        widths = FORMATS_EXPORT[formatExp]['widths']
        lstColonnes = [[x,None,widths[champs.index(x)],x] for x in champs]
        # calcul des débit et crédit des pièces
        totDebits, totCredits = 0.0, 0.0
        for ligne in self.ctrlOlv.innerList:
            montant = float(ligne.montant.replace(',','.'))
            if montant > 0.0:
                totCredits += montant
            else:
                totDebits -= montant

        # transposition des lignes par l'appel de la fonction 'ComposeFuncExp'
        lstValeurs = FORMATS_EXPORT[formatExp]['fonction'](self.pnlParams.GetValeurs(),
                                                           self.ctrlOlv.innerList,
                                                           self.ctrlOlv.lstCodesColonnes)
        # envois dans un fichier excel
        xexport.ExportExcel(listeColonnes=lstColonnes,
                            listeValeurs=lstValeurs,
                            titre=formatExp)
        # mise à jour du dernier numero de pièce affiché avant d'être sauvegardé
        if 'piece' in champs:
            ixp = champs.index('piece')
            lastPiece = lstValeurs[-1][ixp]
            self.pnlParams.lstBoxes[1].SetOneValue('compta.lastpiece',lastPiece)

        # affichage résultat
        solde = xformat.FmtMontant(totDebits - totCredits,lg=12)
        wx.MessageBox("Fin de transfert\n\nDébits: %s\nCrédits:%s"%(xformat.FmtMontant(totDebits,lg=12),
                                                                     xformat.FmtMontant(totCredits,lg=12))+
                      "\nSolde:   %s"%solde)

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    import os
    app = wx.App(0)
    os.chdir("..")
    dlg = Dialog()
    dlg.ShowModal()
    app.MainLoop()
