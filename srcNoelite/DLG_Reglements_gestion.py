#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------
# Application :    NoeLITE, gestion des Reglements en lot
# Auteur:           Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------

import wx
import datetime
import xpy.xGestionDB                   as xdb
import xpy.xGestion_TableauEditor       as xgte
import xpy.xUTILS_SaisieParams          as xusp
import srcNoelite.UTILS_Utilisateurs    as nuu
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
            ColumnDefn("mode", 'centre', 50, 'mode', valueSetter='CHQ', isSpaceFilling=False),
            ColumnDefn("n°ref", 'left', 50, 'numero', isSpaceFilling=False),
            ColumnDefn("nat", 'centre', 40, 'nature', isSpaceFilling=False,
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
    return {
            'hauteur': 400,
            'largeur': 850,
            'checkColonne': False,
            'recherche': True,
            'dictColFooter': {"nombre": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                              "mot": {"mode": "nombre", "alignement": wx.ALIGN_CENTER}, }
            }

#---------------------- Fonctions liées aux appels de données -----------------------

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

def GetFamilles():
    # laissé tel quel depuis DLG_Adresses_gestion
    # appel des données à afficher
    lstChamps = ["0","familles.IDfamille","individus.IDindividu","familles.reglement_intitule","individus.nom",
                 "individus.prenom","individus.reglement_auto","individus.rue_resid","individus.cp_resid","individus.ville_resid"]

    lstNomsColonnes = ["0","famille","individu","intitule famille","nom corresp.",
                        "prenomcorresp.","reglement_auto","rue","cp","ville"]

    lstTypes = ["INTEGER","INTEGER","INTEGER","VARCHAR(100)","VARCHAR(100)",
                "VARCHAR(100)","INTEGER","VARCHAR(100)","VARCHAR(11)","VARCHAR(80)"]
    db = xdb.DB()
    req = """   SELECT %s
                FROM familles 
                LEFT JOIN individus ON familles.reglement_individu = individus.IDindividu;
                """ % (",".join(lstChamps))
    retour = db.ExecuterReq(req, mess='GetIndividus' )
    if retour == "ok":
        recordset = db.ResultatReq()
        if len(recordset) == 0:
            retour = "aucun enregistrement disponible"
    else:
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
                'colonneTri': 1,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                'dictColFooter': {"nom": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},}
                }
    return dicOlv

#----------------------- Parties de l'écrans -----------------------------------------

class PNL_params(wx.Panel):
    #panel de paramètres de l'application
    def __init__(self, parent, **kwds):
        wx.Panel.__init__(self, parent, **kwds)

        self.lblBanque = wx.StaticText(self,-1, label="Banque Noethys:  ",size=(130,20),style=wx.ALIGN_RIGHT)
        self.ctrlBanque = wx.Choice(self,size=(220,20),choices=["un", "deux"])
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

class PNL_corps(xgte.PNL_corps):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        xgte.PNL_corps.__init__(self,parent,dicOlv,*args,**kwds)

class PNL_Pied(xgte.PNL_Pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xgte.PNL_Pied.__init__(self,parent, dicPied, **kwds)

class DLG_ReglementsGestion(wx.Dialog):

    # ------------------- Composition de l'acceuil ------------------

    def __init__(self):
        listArbo = os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self, None,-1,title=titre, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

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
        self.pnlOlv = PNL_corps(self, dicOlv)
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
    import os
    os.chdir("..")
    dlg = DLG_ReglementsGestion()
    dlg.ShowModal()
    app.MainLoop()
