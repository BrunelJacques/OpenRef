#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------
# Application :    NoeLITE, gestion des Reglements en lot
# Auteur:           Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------

import wx
import os
import xpy.xGestion_TableauEditor       as xgte
import srcNoelite.UTILS_Utilisateurs    as nuu
import srcNoelite.UTILS_Reglements      as nur
from xpy.outils.ObjectListView  import ColumnDefn, CellEditor
from xpy.outils                 import xformat,xbandeau

#---------------------- Matrices de paramétres -------------------------------------

TITRE = "Bordereau de réglements: création, modification"
INTRO = "Définissez la banque, choisissez un numéro si c'est pour une reprise, puis saisissez les règlements dans le tableau"
DIC_INFOS = {'dateregl':"C'est la date de réception du règlement, qui sera la date comptable",
            'IDfamille':    "<F4> Choix d'une famille, ou saisie directe du no famille",
            'emetteur':     "<F4> Gestion des émetteurs, <UP> <DOWN> pour défiler l'existant",
            'mode':         "<UP> <DOWN> pour défiler les possibles ou première lettre, \nChèques, Chèques non déposés, Virements,Espèces",
            'numero':       "Derniers caractères du numéro du moyen de paiement ou référence externe",
            'nature':       "<UP> <DOWN> pour défiler les nature d'affectation du reglement,\n"+
                            "'Ne pas créer' pour une prestation déjà saisie dans Noethys",
            'IDarticle':   "<F4> Choix d'une affectation du réglement selon sa nature ",
            'libelle':     "S'il est connu, précisez l'affectation (objet) du règlement",
            'montant':      "Montant en €",
            'differe':     "Date future pour le dépot du chèque ou la promesse de règlement",
             }

def GetBoutons(dlg):
    return  [
                {'name': 'btnImp', 'label': "Imprimer\nle bordereau",
                    'toolTip': "Cliquez ici pour imprimer et enregistrer le bordereau",
                    'size': (120, 35), 'image': wx.ART_PRINT,'onBtn':dlg.OnImprimer},
                {'name':'btnOK','ID':wx.ID_ANY,'label':"Quitter",'toolTip':"Cliquez ici pour fermer la fenêtre",
                    'size':(120,35),'image':"xpy/Images/32x32/Quitter.png",'onBtn':dlg.OnClose}
            ]

def GetOlvColonnes(dlg):
    # retourne la liste des colonnes de l'écran principal
    return [
            ColumnDefn("ID", 'centre', 0, 'IDregl',
                            isEditable=False),
            ColumnDefn("date", 'center', 80, 'dateregl', valueSetter=wx.DateTime.Today(),isSpaceFilling=False,
                            stringConverter=xformat.FmtDate),
            ColumnDefn("famille", 'centre', 50, 'IDfamille', valueSetter=0,isSpaceFilling=False,
                            stringConverter=xformat.FmtIntNoSpce),
            ColumnDefn("désignation famille", 'left', 180, 'designation',valueSetter='',isSpaceFilling=True,
                            isEditable=False),
            ColumnDefn("émetteur", 'left', 80, "emetteur", valueSetter='', isSpaceFilling=True,
                            cellEditorCreator=CellEditor.ComboEditor),
            ColumnDefn("mode", 'centre', 50, 'mode', valueSetter='',choices=['VRT virement', 'CHQ chèque',
                                                    'ESP espèces'], isSpaceFilling=False,
                            cellEditorCreator=CellEditor.ChoiceEditor),
            ColumnDefn("n°ref", 'left', 50, 'numero', isSpaceFilling=False),
            ColumnDefn("nat", 'centre', 50, 'nature',valueSetter='Règlement',choices=['Règlement','Acompte','Don','Debour','Ne pas créer'], isSpaceFilling=False,
                            cellEditorCreator=CellEditor.ChoiceEditor),
            ColumnDefn("article", 'left', 50, 'article', isSpaceFilling=False,
                            isEditable=False),
            ColumnDefn("libelle", 'left', 200, 'libelle', valueSetter='à saisir', isSpaceFilling=True),
            ColumnDefn("montant", 'right',70, "montant", isSpaceFilling=False, valueSetter=0.0,
                            stringConverter=xformat.FmtDecimal),
            ColumnDefn("créer", 'centre', 38, 'creer', valueSetter=True,
                            isEditable=False,
                            stringConverter=xformat.FmtCheck),
            ColumnDefn("differé", 'center', 80, 'differe', valueSetter=wx.DateTime.Today(), isSpaceFilling=False,
                   stringConverter=xformat.FmtDate,),
            ]

def GetOlvOptions(dlg):
    # retourne les paramètres de l'OLV del'écran général
    return {
            'hauteur': 400,
            'largeur': 850,
            'checkColonne': False,
            'recherche': True,
            }

#----------------------- Parties de l'écrans -----------------------------------------

class PNL_params(wx.Panel):
    #panel de paramètres de l'application
    def __init__(self, parent, **kwds):
        wx.Panel.__init__(self, parent, **kwds)
        self.dicBanques = nur.GetBanquesNne()
        lstBanques = [x['nom'] for x in self.dicBanques if x['code_nne'][:2]!='47']
        self.lblBanque = wx.StaticText(self,-1, label="Banque Noethys:  ",size=(130,20),style=wx.ALIGN_RIGHT)
        self.ctrlBanque = wx.Choice(self,size=(220,20),choices=lstBanques)
        self.ctrlBanque.Bind(wx.EVT_KILL_FOCUS,self.OnKillFocusBanque)
        self.btnBanque = wx.Button(self, label="...",size=(40,22))
        self.btnBanque.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_FIND,size=(16,16)))
        self.ctrlSsDepot = wx.CheckBox(self,-1," _Sans dépôt immédiat, (saisie d'encaissements futurs)")
        self.btnBordereau = wx.Button(self, label="Rechercher \nun borderau")
        self.btnBordereau.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_FIND,size=(22,22)))

        self.lblDate = wx.StaticText(self,-1, label="Date de saisie:  ",size=(85,20),style=wx.ALIGN_RIGHT)
        self.ctrlDate = wx.adv.DatePickerCtrl(self,-1,size=(90,20),style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.lblRef = wx.StaticText(self,-1, label="Réference:  ",size=(90,20),style=wx.ALIGN_RIGHT)
        self.ctrlRef = wx.SpinCtrl(self,-1,size=(70,20))

        self.ToolTip()
        self.Sizer()
        self.ctrlBanque.SetFocusFromKbd()

    def ToolTip(self):
        self.lblBanque.SetToolTip("Il s'agit de la banque réceptrice")
        self.ctrlBanque.SetToolTip("Choisissez le compte banque de notre comptabilité qui constatera les encaissements")
        self.ctrlSsDepot.SetToolTip("Les encaissementes seront constatés plus tard dans la compta, "+
                                    "mais ces règlements vont créditer les clients dans Noethys")
        self.btnBanque.SetToolTip("Amélioration prévue pour consulter les comptes bancaires")
        self.btnBordereau.SetToolTip("Recherche d'un bordereau existant pour consultation ou modification")

        self.lblDate.SetToolTip("Cette date de saisie servira de date de dépôt s'il est généré par validation")
        self.ctrlDate.SetToolTip("Cette date de saisie servira de date de dépôt s'il est généré par validation")
        self.lblRef.SetToolTip("Numérotation automatique en création, c'est l'identification du lot par cette référence")
        self.lblRef.Enable(False)
        self.ctrlRef.Enable(False)

    def Sizer(self):
        #composition de l'écran selon les composants emboités progressivement
        boxBanque = wx.FlexGridSizer(rows=1, cols=3, vgap=0, hgap=0)
        boxBanque.AddMany([(self.lblBanque,0,wx.TOP,3),
                                (self.ctrlBanque,1,wx.EXPAND|wx.LEFT|wx.RIGHT,5),
                                self.btnBanque])
        boxBanque.AddGrowableCol(1)

        boxBordereau = wx.FlexGridSizer(rows=2, cols=2, vgap=8, hgap=0)
        boxBordereau.AddMany([self.lblDate,
                                   self.ctrlDate,
                                  self.lblRef,
                                  self.ctrlRef])

        sz_banque = wx.StaticBoxSizer(wx.VERTICAL, self, " Destinataire ")
        sz_banque.Add(boxBanque,1,wx.EXPAND|wx.ALL,3)
        sz_banque.Add(self.ctrlSsDepot,1,wx.ALL|wx.ALIGN_CENTRE,3)

        sz_bordereau = wx.StaticBoxSizer(wx.VERTICAL, self, " Bordereau ")
        sz_bordereau.Add(boxBordereau,1,wx.ALL|wx.ALIGN_CENTRE,3)

        sizer_base = wx.FlexGridSizer(rows=1, cols=3, vgap=0, hgap=20)
        sizer_base.Add(sz_banque,1,wx.LEFT|wx.BOTTOM|wx.EXPAND,3)
        sizer_base.Add(sz_bordereau,1,wx.LEFT|wx.BOTTOM|wx.EXPAND,3)
        sizer_base.Add(self.btnBordereau,0,wx.ALL|wx.ALIGN_CENTRE,10)
        sizer_base.AddGrowableCol(0)
        self.SetSizer(sizer_base)

    def OnKillFocusBanque(self,event):
        if self.ctrlBanque.GetSelection() == -1:
            mess = "Choix de la banque obligatoire\n\n'OK' pourchoisir, 'Annuler' pour sortir"
            ret = wx.MessageBox(mess,style=wx.OK|wx.CANCEL)
            if ret == wx.OK:
                self.ctrlBanque.SetFocusFromKbd()
            else: self.Parent.OnClose(None)

class PNL_corpsReglements(xgte.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xgte.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)
        self.ctrlOlv.Choices={}
        self.flagSkipEdit = False

    def OnEditStarted(self,code):
        if code in DIC_INFOS.keys():
            self.parent.pnlPied.SetItemsInfos( DIC_INFOS[code],
                                               wx.ArtProvider.GetBitmap(wx.ART_FIND, wx.ART_OTHER, (16, 16)))
        else:
            self.parent.pnlPied.SetItemsInfos( "-",wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))

    def OnEditFinishing(self,code=None,value=None):
        self.parent.pnlPied.SetItemsInfos( "-",wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        if self.flagSkipEdit : return
        self.flagSkipEdit = True
        if code == 'IDfamille':
            try:
                value = int(value)
            except:
                self.flagSkipEdit = False
                return
            designation = nur.GetDesignationFamille(value)
            self.ctrlOlv.lastGetObject.designation = designation
            payeurs = nur.GetPayeurs(value)
            if len(payeurs)==0: payeurs.append(designation)
            payeur = payeurs[0]
            self.ctrlOlv.lastGetObject.emetteur = payeur
            self.ctrlOlv.dicChoices[self.ctrlOlv.lstCodesColonnes.index('emetteur')]=payeurs
        if code == 'nature':
            if value.lower() in ('don','debour') :
                # Seuls les dons et débours vont générer la prestation selon l'article
                self.ctrlOlv.lastGetObject.creer = True
                # Choix article - code comptable
                obj = nur.Article(value)
                compte = obj.GetArticle()
                self.ctrlOlv.lastGetObject.article = compte
            else:
                self.ctrlOlv.lastGetObject.article = ""
                self.ctrlOlv.lastGetObject.creer = False
            if code == 'montant':
                if self.ctrlOlv.lastGetObject.nature in ('Règlement','Ne pas créer'):
                    # appel des ventilations
                    obj = nur.Ventilation(value)
                    self.ctrlOlv.lastGetObject.ventilation = obj.GetVentilation()

        # enlève l'info de bas d'écran
        self.parent.pnlPied.SetItemsInfos( "-",wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        self.flagSkipEdit = False

    def OnEditFunctionKeys(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        code = self.ctrlOlv.lstCodesColonnes[col]
        if event.GetKeyCode() == wx.WXK_F4 and code == 'IDfamille':
            # Choix famille
            IDfamille = nur.GetFamille()
            self.OnEditFinishing('IDfamille',IDfamille)
            self.ctrlOlv.lastGetObject.IDfamille = IDfamille

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

        if not nuu.VerificationDroitsUtilisateurActuel('reglements_depots','creer'):
            self.OnClose(None)

        # définition de l'OLV
        self.dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        self.dicOlv.update(GetOlvOptions(self))

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
        self.pnlParams.ctrlSsDepot.Bind(wx.EVT_KILL_FOCUS,self.OnSsDepot)
        self.choicesNonDiffere = self.ctrlOlv.lstColonnes[self.ctrlOlv.lstCodesColonnes.index('mode')].choices
        self.OnSsDepot(None)
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
    def OnSsDepot(self,event):
        # cas d'une saisie différée, la grille est modifiée
        if event:
            value = event.EventObject.GetValue()
        else:
            value = False
        self.ctrlOlv.lstColonnes = GetOlvColonnes(self)
        self.ctrlOlv.lstCodesColonnes = self.ctrlOlv.formerCodeColonnes()
        ixMode = self.ctrlOlv.lstCodesColonnes.index('mode')
        ixDiffere= self.ctrlOlv.lstCodesColonnes.index('differe')
        if not value:
            del self.ctrlOlv.lstCodesColonnes[ixDiffere]
            del self.ctrlOlv.lstColonnes[ixDiffere]
            self.ctrlOlv.lstColonnes[ixMode].choices = self.choicesNonDiffere
        else:
            self.ctrlOlv.lstColonnes[ixMode].choices = ['ND non déposés']

        self.ctrlOlv.InitObjectListView()
        self.ctrlOlv.Refresh()
        if event:
            event.Skip()

    def OnImprimer(self,event):
        event.Skip()
        return

    def OnClose(self,event):
        self.Destroy()

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dlg = Dialog()
    dlg.ShowModal()
    app.MainLoop()
