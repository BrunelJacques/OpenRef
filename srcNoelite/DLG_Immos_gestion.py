#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------------
# Application :    Noelite, Getion des immos
# Usage : Grille d'affichage des lignes d'immobilisation et gestion par boutons
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------------------------------

import wx
import xpy.xGestion_TableauEditor       as xgte
import xpy.xGestionConfig               as xgc
import xpy.xUTILS_SaisieParams          as xusp
import srcNoelite.UTILS_Noegest         as nunoegest
import srcNoelite.UTILS_Utilisateurs    as nuutil
from srcNoelite                 import DB_schema
from xpy.outils.ObjectListView  import ColumnDefn
from xpy.outils                 import xformat,xbandeau,ximport,xexport

#---------------------- Paramètres écran affichage ---------------------------------------
MODULE = 'DLG_Immos_gestion'
TITRE = "Gestion des immobilisations"
INTRO = "Gerez les immobilisations, avant de calculer la dotation et exporter les écritures d'amortissements"

# Infos d'aide en pied d'écran
DIC_INFOS = {'date':"Flèche droite pour le mois et l'année, Entrée pour valider.\nC'est la date",
            'tauxlineaire':    "c'est 100 divisé par le nombre d'années d'amortissement",
            'dotation':     "Cette zone est modifiée automatiquement par le calcul,\nune correction est ephémère",
            'valeur':      "Montant en €",
             }

# Info par défaut
INFO_OLV = "Double clic pour modifier, ou gérer les lignes par les boutons à droite"

# Fonctions de transposition entrée à gérer pour chaque item FORMAT_xxxx pour les spécificités
def ComposeFuncImp(dlg,entete,donnees):
    # cf modème dans DLG_Km_saisie
    lst = None
    return lst

# Description des paramètres à définir en haut d'écran pour PNL_params
MATRICE_PARAMS = {}

# description des boutons en pied d'écran et de leurs actions
def GetBoutons(dlg):
    return  [
                {'name': 'btnDot', 'label': "Calcul\ndotations",
                    'toolTip': "Cliquez ici pour lancer l'importation du fichier de km consommés",
                    'size': (120, 35), 'image': wx.ART_UNDO,},
                {'name': 'btnExp', 'label': "Exporter\nfichier",
                    'toolTip': "Cliquez ici pour lancer l'exportation du fichier selon les paramètres que vous avez défini",
                    'size': (120, 35), 'image': wx.ART_REDO,},
                {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'toolTip':"Cliquez ici pour fermer la fenêtre",
                    'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnFermer}
            ]

# description des boutons à droite de l'écran de leurs actions
def GetOlvActions(pnl):
    # les fonctions appellées devront être présente dans PNL_corps qui implémentera les actions
    return  [
                {'name': 'ajouter',
                    'toolTip': "Ajouter une nouvelle ligne",
                    'size': (25, 25), 
                    'image': wx.Bitmap("xpy/Images/16x16/Ajouter.png", wx.BITMAP_TYPE_ANY),
                    'onBtn': pnl.OnAjouter},
                {'name': 'modifier',
                    'toolTip': "Modifier les propriétés de la ligne selectionnée",
                    'size': (25, 25), 
                    'image': wx.Bitmap("xpy/Images/16x16/Modifier.png", wx.BITMAP_TYPE_ANY),
                    'onBtn': pnl.OnModifier},
                {'name': 'supprimer',
                 'toolTip': "Supprimer la ligne selectionnée",
                 'size': (25, 25),
                 'image': wx.Bitmap("xpy/Images/16x16/Supprimer.png", wx.BITMAP_TYPE_ANY),
                 'onBtn': pnl.OnSupprimer},
            ]

# paramètre les options de l'OLV
DICOLV = {
    'lstColonnes': [
                ColumnDefn("IDimmo", 'centre', 0, 'IDimmo'),
                ColumnDefn("IDcomposant", 'centre', 0, 'IDcomposant'),
                ColumnDefn("Cpte Immo", 'centre', 80, 'compteimmo'),
                ColumnDefn("Cpte Dot", 'center', 70, 'cptedot', ),
                ColumnDefn("Section", 'left', 60, 'section'),
                ColumnDefn("Acquisition", 'center', 80, 'acquisition',
                           stringConverter=xformat.FmtDate,),
                ColumnDefn("Ensemble", 'center', 120, 'enemble', isSpaceFilling=True),
                ColumnDefn("Etat", 'left', 30, 'etat'),
                ColumnDefn("Composant", 'center', 120, 'composant', isSpaceFilling=True),
                ColumnDefn("Valeur", 'right', 90, 'valeur', valueSetter=0,
                           stringConverter=xformat.FmtDecimal),
                ColumnDefn("Amo", 'center', 40, 'typeamo'),
                ColumnDefn("Taux", 'right', 50, 'taux', valueSetter=0,
                           stringConverter=xformat.FmtPercent),
                ColumnDefn("Amo Antér.", 'right', 90, 'ante', valueSetter=0,
                           stringConverter=xformat.FmtDecimal),
                ColumnDefn("Dotation", 'right', 90, 'dotation',
                           ),
                ColumnDefn("Cession", 'left', 40, 'cession',),
                ],
    'dictColFooter': {'composant': {"mode": "nombre", "alignement": wx.ALIGN_CENTER,'pluriel':"lignes"},
                      'valeur': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      'ante': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      'dotation': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      },
    'lstChamps': ['immobilisations.compteImmo', 'immosComposants.IDcomposant', 'immobilisations.compteImmo',
                  'immobilisations.compteDotation','immobilisations.IDanalytique', 'immosComposants.dteAcquisition',
                  'immobilisations.libelle','immosComposants.etat', 'immosComposants.libComposant',
                  'immosComposants.valeur','immosComposants.type', 'immosComposants.tauxLineaire',
                  'immosComposants.amortAnterieur','immosComposants.dotation', 'immosComposants.cessionType'],
    'getActions': GetOlvActions,
    'hauteur': 400,
    'largeur': 950,
    'checkColonne': False,
    'recherche': True,
    'autoAddRow': False,
    'editMode': False,
    'msgIfEmpty':"Aucune immobilisation à afficher !",
    }

#---------------------- Paramètres écran gestion ligne ---------------------------------------
lTITRE = "Gestion d'un ensemble immobilisé"
lINTRO = "Gerez les composants d'une immobilisation dans le tableau, ou l'ensemble dans l'écran du haut."

# Info par défaut
lINFO_OLV = "Double clic pour modifier une cellule."

# Description des paramètres à définir en haut d'écran pour PNL_params
lMATRICE_PARAMS = {
    ("comptes","Comptes d'amortissements"): [
            {'name': 'compteimmo', 'label': "Immobilisation", 'genre': 'texte', 'size':(200,30),
             'help': "Compte du plan comptable pour cet ensemble dans la classe 2"},
            {'name': 'comptedotation', 'label': "Dotation", 'genre': 'texte', 'size': (200, 30),
             'help': "Compte du plan comptable pour cet ensemble dans la classe 68"},
            {'name': 'idanalytique', 'label': "Section analytique", 'genre': 'texte', 'size': (400, 30),
             'help': "Section analytique s'insérant dans les deux comptes ci dessus",
             'btnLabel': "...", 'btnHelp': "Cliquez pour choisir une section analytique",
             'btnAction': 'OnBtnSection'},
            ],
    ("ensemble", "Propriétés de l'ensemble"): [
            {'name': 'libelle', 'label': "Libellé", 'genre': 'texte', 'size':(500,30),
             'help': "Libellé désignant cet ensemble"},
            {'name': 'nbreplaces', 'label': "Nombre places", 'genre': 'int', 'size':(200,30),
             'help': "Capacité ou nombre de places en service (dernière connue"},
            {'name': 'noserie', 'label': "No de série", 'genre': 'int', 'size':(200,30),
             'help': "Immatriculation des véhicules ou identification facultative"},
            ]}

# description des boutons en pied d'écran et de leurs actions
def lGetBoutons(dlg):
    return  [
                {'name':'btnAbandon','ID':wx.ID_CANCEL,'label':"Abandon",'toolTip':"Cliquez ici pour fermer sans modifs",
                    'size':(120,36),'image':"xpy/Images/16x16/Abandon.png",'onBtn':dlg.OnAbandon},
                {'name':'btnOK','ID':wx.ID_ANY,'label':"Valider",'toolTip':"Cliquez ici pour enrgistrer les modifs",
                    'size':(120,35),'image':"xpy/Images/32x32/Valider.png",'onBtn':dlg.OnValider},
            ]

# paramètre les options de l'OLV
lcutend = 2
lDICOLV = {
    'lstColonnes': xformat.GetLstColonnes(DB_schema.DB_TABLES['immosComposants'],cutend=lcutend),
    'dictColFooter': {'composant': {"mode": "nombre", "alignement": wx.ALIGN_CENTER,'pluriel':"lignes"},
                      'valeur': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      'amortanterieur': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      'dotation': {"mode": "total","alignement": wx.ALIGN_RIGHT},
                      },
    'lstChamps': xformat.GetLstChamps(DB_schema.DB_TABLES['immosComposants'][:-lcutend]),
    'lstChmpEns': xformat.GetLstChamps(DB_schema.DB_TABLES['immobilisations']),
    'hauteur': 400,
    'largeur': 1350,
    'checkColonne': False,
    'recherche': True,
    'autoAddRow': True,
    'editMode': True,
    'msgIfEmpty':"Aucune ligne d'immobilisation à afficher !",
    }

#----------------------- Parties de l'écran de gestion d'un ensemble ------------------

class Pnl_params(xgc.PNL_paramsLocaux):
    #panel de paramètres de l'application
    def __init__(self, parent, **kwds):
        self.parent = parent
        #('pos','size','style','name','matrice','donnees','lblbox')
        kwds = {
                'name':"Pnl_params",
                'matrice':lMATRICE_PARAMS,
                'lblbox':None,
                'pathdata':"srcNoelite/Data",
                'nomfichier':"params",
                'nomgroupe': MODULE
                }
        super().__init__(parent, **kwds)
        self.Init()

class Pnl_corps(xgte.PNL_corps):
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
            test = self.parent.noegest.ValideLigneComposant(track)
            if test:
                track.valide = True
                self.oldRow = row
            else:
                track.valide = False
        track = self.ctrlOlv.GetObjectAt(row)
        if code == 'comptefrn':
            pass
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
        if code == 'vehicule':
            # vérification de l'unicité du code saisi
            dicVehicule = self.parent.noegest.GetVehicule(filtre=value)
            if dicVehicule:
                track.IDvehicule = dicVehicule['idanalytique']
                track.vehicule = dicVehicule['abrege']
                track.nomvehicule = dicVehicule['nom']
            else:
                track.vehicule = ''
                track.IDvehicule = ''
                track.nomvehicule = ''
            if parent:
                # la modification de la cellule éditée ne doit pas être écrasée par le finish
                parent.valeur = track.vehicule
                parent.event.cellValue = track.vehicule
            track.donnees[col] = track.vehicule
            self.ctrlOlv.Refresh()


        # l'enregistrement de la ligne se fait à chaque saisie pour gérer les montées et descentes
        self.parent.noegest.ValideLigneComposant(track)


        # enlève l'info de bas d'écran
        self.parent.pnlPied.SetItemsInfos( INFO_OLV,wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.flagSkipEdit = False

    def OnDelete(self,noligne,track,parent=None):
        pass

    def OnEditFunctionKeys(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        track = self.ctrlOlv.GetObjectAt(row)
        code = self.ctrlOlv.lstCodesColonnes[col]
        if event.GetKeyCode() == wx.WXK_F4 and code == 'vehicule':
            # F4 Choix
            dict = self.parent.noegest.GetVehicule(filtre=track.vehicule,mode='F4')
            if dict:
                self.OnEditFinishing('vehicule',dict['abrege'])
                track.vehicule = dict['abrege']
                track.nomvehicule = dict['nom']
                track.IDvehicule = dict['idanalytique']

class Pnl_pied(xgte.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xgte.PNL_pied.__init__(self,parent, dicPied, **kwds)

class Dlg_immo(xusp.DLG_vide):
    # ------------------- Composition de l'écran de gestion des composants d'une immo ---
    def __init__(self,IDimmo=None):
        super().__init__(self,name = MODULE)
        self.IDimmo = IDimmo
        self.ctrlOlv = None
        self.dicOlv = lDICOLV
        self.dicOlv['lstColonnes'][1].width = 0
        self.noegest = nunoegest.Noegest(self)
        self.IDutilisateur = nuutil.GetIDutilisateur()
        if (not self.IDutilisateur) or not nuutil.VerificationDroitsUtilisateurActuel('facturation_factures','creer'):
            self.Destroy()
        self.Init()
        self.Sizer()

    # Initialisation des panels
    def Init(self):
        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),lINFO_OLV]
        dicPied = {'lstBtns': lGetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self,lTITRE,lINTRO,nomImage="xpy/Images/32x32/Matth.png")
        self.pnlParams = Pnl_params(self)
        self.pnlOlv = Pnl_corps(self, self.dicOlv)
        self.pnlPied = Pnl_pied(self, dicPied)
        self.ctrlOlv = self.pnlOlv.ctrlOlv
        self.Bind(wx.EVT_CLOSE,self.OnFermer)
        self.noegest.GetEnsemble(self.IDimmo,self.dicOlv['lstChmpEns'],self.pnlParams)
        self.noegest.GetComposants(self.IDimmo,self.dicOlv['lstChamps'])


    def Sizer(self):
        sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        sizer_base.Add(self.pnlBandeau, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlParams, 1, wx.TOP , 3)
        sizer_base.Add(self.pnlOlv, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlPied, 0, wx.ALL | wx.EXPAND, 3)
        sizer_base.AddGrowableCol(0)
        sizer_base.AddGrowableRow(1)
        self.CenterOnScreen()
        self.SetSizerAndFit(sizer_base)
        self.CenterOnScreen()

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

    def OnImporter(self,event):
        """ Open a file"""
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choisissez un fichier à importer", self.dirname)
        nomFichier = None
        if dlg.ShowModal() == wx.ID_OK:
            nomFichier = dlg.GetPath()
        dlg.Destroy()
        if not nomFichier: return
        entete,donnees = self.GetDonneesIn(nomFichier)
        if donnees:
            donExist = [x.donnees for x in self.ctrlOlv.modelObjects]
            if len(donExist)>0:
                ix = self.ctrlOlv.lstCodesColonnes.index('conso')
                if xformat.Nz(donExist[-1][ix]) == 0:
                    del donExist[-1]
                    del self.ctrlOlv.modelObjects[-1]
            donNew = ComposeFuncImp(self,entete,donnees)
            self.ctrlOlv.listeDonnees = donExist + donNew
            # ajout de la ligne dans olv
            self.ctrlOlv.AddTracks(donNew)
            # test de validité pour changer la couleur de la ligne
            for object in self.ctrlOlv.modelObjects:
                self.noegest.ValideLigneComposant(object)
            self.ctrlOlv._FormatAllRows()
            self.ctrlOlv.Refresh()

    def OnBtnSection(self,event):
        wx.MessageBox("On va chercher")

    def OnAbandon(self,event):
        self.OnFermer(event)

    def OnValider(self,event):
        pass

#----------------------- Parties de l'écran d'affichage de la liste--------------------

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
                'nomgroupe': MODULE
                }
        super().__init__(parent, **kwds)
        self.Init()

class PNL_corps(xgte.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xgte.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)

    def OnAjouter(self,evt):
        wx.MessageBox("on va ajouter")
        return

    def OnModifier(self,evt):
        wx.MessageBox("on va modifier")
        return

    def OnSupprimer(self,evt):
        wx.MessageBox("on va supprimer")
        return

class PNL_pied(xgte.PNL_pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xgte.PNL_pied.__init__(self,parent, dicPied, **kwds)

class DLG_immos(xusp.DLG_vide):
    # ------------------- Composition de l'écran de gestion----------
    def __init__(self):
        super().__init__(self,name = MODULE)
        self.ctrlOlv = None
        self.dicOlv = DICOLV
        self.noegest = nunoegest.Noegest(self)
        self.IDutilisateur = nuutil.GetIDutilisateur()
        if (not self.IDutilisateur) or not nuutil.VerificationDroitsUtilisateurActuel('facturation_factures','creer'):
            self.Destroy()
        self.Init()
        self.Sizer()

    # Initialisation des panels
    def Init(self):
        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),INFO_OLV]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self,TITRE,INTRO,nomImage="xpy/Images/32x32/Matth.png")
        self.pnlParams = PNL_params(self)
        self.pnlOlv = PNL_corps(self, self.dicOlv)
        self.pnlPied = PNL_pied(self, dicPied)
        self.ctrlOlv = self.pnlOlv.ctrlOlv
        self.Bind(wx.EVT_CLOSE,self.OnFermer)
        self.noegest.GetImmosComposants(self.dicOlv['lstChamps'])

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

    def OnImporter(self,event):
        """ Open a file"""
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choisissez un fichier à importer", self.dirname)
        nomFichier = None
        if dlg.ShowModal() == wx.ID_OK:
            nomFichier = dlg.GetPath()
        dlg.Destroy()
        if not nomFichier: return
        entete,donnees = self.GetDonneesIn(nomFichier)
        if donnees:
            donExist = [x.donnees for x in self.ctrlOlv.modelObjects]
            if len(donExist)>0:
                ix = self.ctrlOlv.lstCodesColonnes.index('conso')
                if xformat.Nz(donExist[-1][ix]) == 0:
                    del donExist[-1]
                    del self.ctrlOlv.modelObjects[-1]
            donNew = ComposeFuncImp(self,entete,donnees)
            self.ctrlOlv.listeDonnees = donExist + donNew
            # ajout de la ligne dans olv
            self.ctrlOlv.AddTracks(donNew)
            # test de validité pour changer la couleur de la ligne
            for object in self.ctrlOlv.modelObjects:
                self.noegest.ValideLigne(object)
                self.noegest.SauveLigne(object)
            self.ctrlOlv._FormatAllRows()
            self.ctrlOlv.Refresh()

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    import os
    app = wx.App(0)
    os.chdir("..")
    dlg = Dlg_immo(IDimmo = 18)
    #dlg = DLG_immos()
    dlg.ShowModal()
    app.MainLoop()
