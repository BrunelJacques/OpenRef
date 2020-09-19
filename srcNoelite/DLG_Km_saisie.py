#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------
# Application :    Noelite, transposition de fichier comptable
# Usage : Reécrire dans un formatage différent avec fonctions de transposition
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------

import wx
import datetime
import xpy.xGestion_TableauEditor       as xgte
import xpy.xGestionConfig               as xgc
import xpy.xUTILS_SaisieParams          as xusp
from srcNoelite                 import UTILS_Noegest,UTILS_Compta
from xpy.outils.ObjectListView  import ColumnDefn, CellEditor
from xpy.outils                 import xformat,xbandeau,ximport,xexport

#---------------------- Paramètres du programme -------------------------------------

TITRE = "Saisie des consommations de km"
INTRO = "Importez un fichier ou saisissez les consommations de km, avant de l'exporter dans un autre format"

# Infos d'aide en pied d'écran
DIC_INFOS = {'date':"Flèche droite pour le mois et l'année, Entrée pour valider.\nC'est la date",
            'IDtiers':    "<F4> Choix d'une section ou d'un tiers pour l'affectation du coût",
            'observation':     "S'il y a lieu précisez des circonstances particulières",
            'montant':      "Montant en €",
             }

# Info par défaut
INFO_OLV = "<Suppr> <Inser> <Ctrl C> <Ctrl V>"

# Fonctions de transposition entrée à gérer pour chaque item FORMAT_xxxx pour les spécificités
def ComposeFuncImp(entete,donnees,champsOut):
    # Fonction import pour composition
    colonnesIn =    ["Code Véhicule","Date Début","Membre   ","Partenaire","Camp  ","KM Début  ","KM Fin"]
    champsIn =      ['vehicule','dtkmdeb','membre','partenaire','camp','kmdeb','kmfin']
    lstOut = [] #'vehicule','date','membre','camp','kmdeb','kmfin'
    # teste la cohérence de la première ligne importée
    mess = "Vérification des champs trouvés,\n\n"
    mess += '{:_<26} '.format('ATENDU') + 'TROUVE\n\n'
    for ix in range(len(colonnesIn)):
        mess += '{:_<26} '.format(colonnesIn[ix] ) + str(entete[ix])+'\n'
    ret = wx.MessageBox(mess,"Confirmez le fichier ouvert...",style=wx.YES_NO)
    if ret != wx.YES:
        return lstOut
    # déroulé du fichier entrée, composition des lignes de sortie
    for ligneIn in donnees:
        if len(champsIn) < len(ligneIn):
            # ligneIn batarde ignorée
            continue
        ligneOut = [None,]*len(champsOut)
        #champs communs aux listIn et listOut
        for champ in ('vehicule','dtkmdeb','kmdeb','kmfin'):
            ligneOut[champsOut.index(champ)] = ligneIn[champsIn.index(champ)]
        # calcul auto d'une date fin de mois
        findemois = xformat.FinDeMois(ligneIn[champsIn.index('dtkmdeb')])
        ligneOut[champsOut.index('dtkmfin')] = findemois
        if ligneIn[champsIn.index('camp')]:
            ligneOut[champsOut.index('typetiers')] = 'A'
            ligneOut[champsOut.index('IDtiers')] =  ligneIn[champsIn.index('camp')]
        elif ligneIn[champsIn.index('partenaire')]:
            ligneOut[champsOut.index('typetiers')] = 'T'
            ligneOut[champsOut.index('observation')] = ligneIn[champsIn.index('partenaire')]
        elif ligneIn[champsIn.index('membre')]:
            ligneOut[champsOut.index('typetiers')] = 'T'
            ligneOut[champsOut.index('observation')] = ligneIn[champsIn.index('membre')]
        lstOut.append(ligneOut)
    return lstOut

# Description des paramètres à choisir en haut d'écran
MATRICE_PARAMS = {
("filtres","Filtre des données"): [
    {'name': 'exercice', 'genre': 'Enum', 'label': 'Exercice clôturant',
                    'help': "Choisir un exercice ouvert pour pouvoir saisir, sinon il sera en consultation", 'value':0,
                    'values': ['',],
                    'ctrlAction':'OnExercice',
                    'size':(300,30)},
    {'name': 'datefact', 'genre': 'Enum', 'label': 'Date facturation',
                    'help': "Date de facturation pour l'export ou pour consulter l'antérieur",
                    'value':1, 'values':['toutes dates','{:%d/%m/%Y}'.format(datetime.date.today())],
                    'ctrlAction':'OnDateFact',
                    'size':(300,30)},
    {'name': 'vehicule', 'genre': 'Enum', 'label': "Véhicule",
                    'help': "Pour filtrer les écritures d'un seul véhicule, saisir sa clé d'appel",
                    'value':0, 'values':['',],
                    'ctrlAction':'OnDateFact',
                    'size':(300,30)},
    ],
("compta", "Paramètres export"): [
    {'name': 'formatexp', 'genre': 'Enum', 'label': 'Format export',
                    'help': "Le choix est limité par la programmation", 'value':0,
                    'values':[x for x in UTILS_Compta.FORMATS_EXPORT.keys()],
                    'ctrlAction':'OnChoixExport',
                    'size':(300,30)},
    {'name': 'journal', 'genre': 'Combo', 'label': 'Journal','ctrlAction':'OnCtrlJournal',
                    'help': "Code journal utilisé dans la compta",'size':(350,30),
                    'value':'CI','values':['BQ','LCL','LBP','CCP'],
                    'btnLabel': "...", 'btnHelp': "Cliquez pour choisir un journal",
                    'btnAction': 'OnBtnJournal'},
    {'name': 'forcer', 'genre': 'Bool', 'label': 'Exporter les écritures déjà transférées','value':False,
     'help': "Pour forcer un nouvel export d'écritures déjà transférées!", 'size': (250, 30)},
    ],
("comptes", "Comptes à mouvementer"): [
    {'name': 'revente', 'genre': 'String', 'label': 'Vente interne km',
     'help': "Code comptable du compte crédité de la rétrocession", 'size': (250, 30)},
    {'name': 'achat', 'genre': 'String', 'label': 'Achat interne km',
     'help': "Code comptable du compte débité de la rétrocession interne", 'size': (250, 30)},
    {'name': 'tiers', 'genre': 'String', 'label': 'km faits par tiers',
     'help': "Code comptable du compte crédité de la rétrocession à refacturer aux clients", 'size': (250, 30)},

]}

# description des boutons en pied d'écran et de leurs actions
def GetBoutons(dlg):
    return  [
                {'name': 'btnImp', 'label': "Importer\nfichier",
                    'toolTip': "Cliquez ici pour lancer l'importation du fichier de km consommés",
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
            ColumnDefn("Véhicule", 'center', 50, 'vehicule', isSpaceFilling=False,
                       cellEditorCreator=CellEditor.ComboEditor),
            ColumnDefn("Nom Véhicule", 'left', 120, 'nomvehicule',
                       isSpaceFilling=True, isEditable=False),
            ColumnDefn("Type Tiers", 'center', 40, 'typetiers', isSpaceFilling=False,valueSetter='A',
                       cellEditorCreator=CellEditor.ChoiceEditor,choices=['A analytique', 'T tiers']),
            ColumnDefn("Tiers", 'center', 60, 'IDtiers', isSpaceFilling=False),
            ColumnDefn("Nom Tiers", 'left', 120, 'tiers',
                       isSpaceFilling=True, isEditable=False),
            ColumnDefn("Date Début", 'center', 85, 'dtkmdeb',
                       stringConverter=xformat.FmtDate, isSpaceFilling=False),
            ColumnDefn("KM début", 'right', 90, 'kmdeb', isSpaceFilling=False,
                       stringConverter=xformat.FmtInt),
            ColumnDefn("Date Fin", 'center', 85, 'dtkmfin',
                       stringConverter=xformat.FmtDate, isSpaceFilling=False),
            ColumnDefn("KM fin", 'right', 90, 'kmfin', isSpaceFilling=False,
                       stringConverter=xformat.FmtInt),
            ColumnDefn("KM conso", 'right', 80, 'conso', isSpaceFilling=False,valueSetter=0,
                       isEditable=False),
            ColumnDefn("Observation", 'left', 150, 'observation',
                       isSpaceFilling=True),
            ]

# paramètre les options de l'OLV
def GetOlvOptions(dlg):
    return {
            'hauteur': 400,
            'largeur': 900,
            'checkColonne': False,
            'recherche': True,
            'autoAddRow':True,
            'msgIfEmpty':"Saisir ou importer un fichier !",
            'dictColFooter': {'tiers': {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                              'observation': {"mode": "texte", "alignement": wx.ALIGN_LEFT, "texte": 'km imputés'},
                              'conso': {"mode": "total"}, }
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
                'lblbox':None,
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
        track = self.ctrlOlv.GetObjectAt(row)

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
            """# deuxième essai dans les comptes généraux
            if not record:
                record = self.parent.compta.GetOneAuto('generaux', value)
            # tentative de recherche mannuelle
            newfiltre = self.parent.compta.filtreTest
            if not record:
                record = self.parent.compta.ChoisirItem('fournisseurs',newfiltre)
            """
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
            else:
                track.appel = ''
                track.libcpt = ''


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
                track = self.ctrlOlv.GetObjectAt(row)
                track.compte = item[0]

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

    def GetDonneesIn(self,nomFichier):
        # importation des donnéees du fichier entrée
        entrees = None
        if nomFichier[-4:].lower() == 'xlsx':
            entrees = ximport.GetFichierXlsx(nomFichier,maxcol=7)
        elif nomFichier[-3:].lower() == 'xls':
            entrees = ximport.GetFichierXls(nomFichier,maxcol=7)
        else: wx.MessageBox("Il faut choisir un fichier .xls ou .xlsx",'NomFichier non reconnu')
        # filtrage des premières lignes incomplètes
        entete = None
        if entrees:
            for ix in range(len(entrees)):
                sansNull= [x for x in entrees[ix] if x]
                if len(sansNull)>5:
                    entete = entrees[ix]
                    entrees = entrees[ix + 1:]
                    break
        return entete,entrees

    def GetCompta(self):
        dic = self.pnlParams.GetValeurs()
        formatExp = dic['compta']['formatexp']
        compta = None
        if formatExp in UTILS_Compta.FORMATS_EXPORT.keys() :
            nomCompta = UTILS_Compta.FORMATS_EXPORT[formatExp]['compta']
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
        pnlJournal = self.pnlParams.GetPanel('journal', 'compta')
        x = False
        if compta : x = True
        pnlJournal.btn.Enable(x)
        return compta

    def GetTable(self):
        return None

    def OnImporter(self,event):
        """ Open a file"""
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choisissez un fichier à importer", self.dirname)
        nomFichier = None
        if dlg.ShowModal() == wx.ID_OK:
            nomFichier = dlg.GetPath()
        dlg.Destroy()
        if not nomFichier: return
        dicParams = self.pnlParams.GetValeurs()
        entete,donnees = self.GetDonneesIn(nomFichier)
        if donnees:
            self.ctrlOlv.listeDonnees = ComposeFuncImp(entete,
                                                                            donnees,
                                                                          self.ctrlOlv.lstCodesColonnes,)
            self.InitOlv()

    def OnExporter(self,event):

        # calcul des débit et crédit des pièces
        totDebits, totCredits = 0.0, 0.0
        nonValides = 0
        for ligne in self.ctrlOlv.innerList:
            if not ligne.compte or len(ligne.compte)==0: nonValides +=1
            montant = float(ligne.montant.replace(',','.'))
            if montant > 0.0:
                totCredits += montant
            else:
                totDebits -= montant
        if nonValides > 0:
            ret = wx.MessageBox("%d lignes sans no de compte!\n\nelles seront mises en compte d'attente 471"%nonValides,
                          "Confirmez ou abandonnez",style= wx.YES_NO)
            if not ret == wx.YES:
                return wx.CANCEL


        exp = UTILS_Compta.Export(self,self.compta)
        ret = exp.Exporte(params=self.pnlParams.GetValeurs(),donnees=self.pnlParams.GetValeurs(),olv=self.ctrlOlv)
        if not ret == wx.OK:
            return ret

        # affichage résultat
        solde = xformat.FmtMontant(totDebits - totCredits,lg=12)
        wx.MessageBox("Fin de transfert\n\nDébits: %s\nCrédits:%s"%(xformat.FmtMontant(totDebits,lg=12),
                                                                     xformat.FmtMontant(totCredits,lg=12))+
                      "\nSolde:   %s"%solde)

        # sauvegarde des params
        self.pnlParams.SauveParams(close=True)


#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    import os
    app = wx.App(0)
    os.chdir("..")
    dlg = Dialog()
    dlg.ShowModal()
    app.MainLoop()
