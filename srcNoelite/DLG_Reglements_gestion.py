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
            ColumnDefn("ID", 'centre', 0, 'IDregl',isEditable=False),
            ColumnDefn("date", 'center', 80, 'dateregl', valueSetter=wx.DateTime.Today(),isSpaceFilling=False,
                                stringConverter=xformat.FmtDate),
            ColumnDefn("famille", 'centre', 50, 'IDfamille', valueSetter=0,isSpaceFilling=False,
                                stringConverter=xformat.FmtIntNoSpce),
            ColumnDefn("désignation famille", 'left', 180, 'designation',valueSetter='',isSpaceFilling=True,
                            isEditable=False),
            ColumnDefn("émetteur", 'left', 80, "emetteur", valueSetter='', isSpaceFilling=True,
                                cellEditorCreator=CellEditor.ComboEditor),
            ColumnDefn("mode", 'centre', 50, 'mode', valueSetter='CHQ',choices=['CHQ','VRT','ESP'], isSpaceFilling=False,
                       cellEditorCreator=CellEditor.ChoiceEditor),
            ColumnDefn("n°ref", 'left', 50, 'numero', isSpaceFilling=False),
            ColumnDefn("nat", 'centre', 50, 'nature',valueSetter='Regl',choices=['Regl','Acpte','Don','Debour','X'], isSpaceFilling=False,
                                cellEditorCreator=CellEditor.ChoiceEditor),
            ColumnDefn("IDart", 'centre', 40, 'IDarticle'),
            ColumnDefn("libelle", 'left', 200, 'libelle', valueSetter='à saisir', isSpaceFilling=True),
            ColumnDefn("montant", 'right',70, "montant", isSpaceFilling=False, valueSetter=0.0,
                               stringConverter=xformat.FmtDecimal),
            ColumnDefn("créer", 'centre', 38, 'creation', valueSetter=False,
                                cellEditorCreator=CellEditor.CheckEditor,
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

def GetOlvInfos(dlg):
    return {'IDfamille':"<F4> Choix d'une famille",'emetteur':"<F4> Gestion des émetteurs"}
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
        sz_banque.Add(boxBanque,1,wx.EXPAND|wx.ALL|wx.ALIGN_CENTRE_HORIZONTAL,3)
        sz_banque.Add(self.ctrlSsDepot,1,wx.ALL|wx.ALIGN_CENTRE_HORIZONTAL,3)

        sz_bordereau = wx.StaticBoxSizer(wx.VERTICAL, self, " Bordereau ")
        sz_bordereau.Add(boxBordereau,1,wx.ALL|wx.ALIGN_CENTRE_HORIZONTAL,3)

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
            print(ret)
            if ret == wx.OK:
                self.ctrlBanque.SetFocusFromKbd()
            else: self.Parent.OnClose(None)

class PNL_corpsReglements(xgte.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xgte.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)
        self.matriceFamilles = nur.GetMatriceFamilles()
        self.ctrlOlv.Choices={}

    def OnSt_IDfamille(self):
        mess = GetOlvInfos('IDfamille')
        self.parent.pnlPied.lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),"Bonjour la famille"]
        print(self.parent.pnlPied.itemsInfos)
        self.parent.pnlPied.Sizer()
        print(self.parent.pnlPied.itemsInfos)

    def OnKl_IDfamille(self,IDfamille=None,designation=None):
        if not IDfamille : return
        IDfamille = int(IDfamille)
        if not designation:
            designation = nur.GetDesignationFamille(IDfamille)
        self.ctrlOlv.lastGetObject.designation = designation
        payeurs = nur.GetPayeurs(IDfamille)
        if len(payeurs)==0: payeurs.append(designation)
        payeur = payeurs[0]
        self.ctrlOlv.lastGetObject.emetteur = payeur
        self.ctrlOlv.dicChoices[self.ctrlOlv.lstCodesColonnes.index('emetteur')]=payeurs

    def OnEditorFuctionKeys(self,event):
        row, col = self.ctrlOlv.cellBeingEdited
        if event.GetKeyCode() == wx.WXK_F4 and col == 2:
            # Choix famille
            (IDfamille,designation) = nur.GetFamille(self.matriceFamilles)
            self.OnKl_IDfamille(IDfamille,designation)
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
        dicOlv = {'lstColonnes': GetOlvColonnes(self)}
        dicOlv.update(GetOlvOptions(self))

        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        self.txtInfo =  "Petite info selon contexte"
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),self.txtInfo]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xbandeau.Bandeau(self,TITRE,INTRO,nomImage="xpy/Images/32x32/Matth.png")
        self.pnlParams = PNL_params(self)
        self.pnlOlv = PNL_corpsReglements(self, dicOlv)
        self.pnlPied = PNL_Pied(self, dicPied)
        self.ctrlOlv = self.pnlOlv.ctrlOlv
        self.__Sizer()

    def __Sizer(self):
        sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        sizer_base.Add(self.pnlBandeau, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlParams, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlOlv, 1, wx.TOP | wx.EXPAND, 3)
        sizer_base.Add(self.pnlPied, 0, wx.ALIGN_RIGHT | wx.ALL | wx.EXPAND, 3)
        sizer_base.AddGrowableCol(0)
        sizer_base.AddGrowableRow(1)
        self.CenterOnScreen()
        self.SetSizerAndFit(sizer_base)
        self.CenterOnScreen()

    # ------------------- Gestion des actions -----------------------

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
