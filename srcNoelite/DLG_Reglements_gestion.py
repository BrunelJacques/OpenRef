#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------
# Application :    NoeLITE, gestion des Reglements en lot
# Auteur:           Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------

TITRE = "Bordereau de réglements: création, modification"
INTRO = "Définissez la banque, choisissez un numéro si c'est pour une reprise, puis saisissez les règlements dans le tableau"

MATRICE_PRINCIPAL = {
        ("choix_config","Choisissez votre configuration"):
            [
                {'name': 'banque', 'genre': 'Enum', 'label': 'Banque récéptrice','value':'','values':['LCL','LBP',],
                        'help': "Choisissez la banque qui reçoit les règlements"},
                {'name': 'mode', 'genre': 'Enum', 'label': 'Type de règlement','value':'Virements',
                        'values':['Virements', 'Chèques', 'Chq mis au coffre'],
                        'help': 'Choisissez le type de règlement lié à cette banque'},]}

import wx
import datetime
import xpy.outils                       as xout
import xpy.xGestionDB                   as xdb
import xpy.xGestion_TableauEditor       as xgte
import xpy.xUTILS_SaisieParams          as xusp
import xpy.outils.xbandeau
import srcNoelite.UTILS_Utilisateurs    as nuu
from xpy.outils.ObjectListView import FastObjectListView,ColumnDefn, CTRL_Outils, CellEditor

dictAPPLI = {
            'NOM_APPLICATION'       : "noelite",
            'REP_SOURCES'           : "srcNoelite",
            'REP_DATA'              : "srcNoelite/Data",
            'REP_TEMP'              : "srcNoelite/Temp",
            'NOM_FICHIER_LOG'       : "logsNoelite.log",
            'OPTIONSCONFIG'         : ["db_prim"],
            }

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

class Dialog(wx.Dialog):
    def __init__(self):
        listArbo = os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self, None,-1,title=titre, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        liste_Colonnes = [
            ColumnDefn("null", 'centre', 0, "IX", valueSetter=''),
            ColumnDefn("clé", 'centre', 60, "cle", valueSetter=True, isSpaceFilling=False,
                       cellEditorCreator=CellEditor.BooleanEditor),
            ColumnDefn("mot d'ici", 'left', 200, "mot", valueSetter='A saisir', isEditable=True),
            ColumnDefn("nbre", 'right', -1, "nombre", isSpaceFilling=True, valueSetter=0.0,
                       stringConverter=xout.xformat.FmtDecimal),
            ColumnDefn("prix", 'left', 80, "prix", valueSetter=0.0, isSpaceFilling=True,
                       cellEditorCreator=CellEditor.ComboEditor),
            ColumnDefn("ddate", 'center', 80, "date", valueSetter=wx.DateTime.FromDMY(1, 0, 1900), isSpaceFilling=True,
                       stringConverter=xout.xformat.FmtDate),
            ColumnDefn("choicee", 'center', 40, "choice", valueSetter="mon item", isSpaceFilling=True,
                       cellEditorCreator=CellEditor.ChoiceEditor, )
        ]
        liste_Donnees = [[1, False, "Bonjour", -1230.05939, -1230.05939, None, "deux"],
                         [2, None, "Bonsoir", 57.5, 208.99, datetime.date.today(), None],
                         [3, '', "Jonbour", 0, 'remisé', datetime.date(2018, 11, 20), "mon item"],
                         ]
        dicOlv = {'lstColonnes': liste_Colonnes,
                  'listeDonnees': liste_Donnees,
                  'hauteur': 400,
                  'largeur': 850,
                  'checkColonne': False,
                  'recherche': True,
                  'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                  'dictColFooter': {"nombre": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                    "mot": {"mode": "nombre", "alignement": wx.ALIGN_CENTER}, }
                  }

        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstBtns = [
                   ('BtnPrec2', wx.ID_PREVIEW_NEXT, "précédent", "Retour à l'écran précédent next"),
                   ('BtnOK', wx.ID_OK, "fermer","Cliquez ici pour fermer la fenêtre")
                   ]
        dicOnBtn = {'Action1': lambda evt: wx.MessageBox('ceci active la fonction action1'),
                    'Action2': 'self.parent.Validation()',
                    'BtnPrec': 'self.parent.Close()'}
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),
                    "Petite info selon contexte"]
        dicPied = {'lstBtns': lstBtns, 'dicOnBtn': dicOnBtn, "lstInfos": lstInfos}

        # lancement de l'écran en blocs principaux
        self.pnlBandeau = xout.xbandeau.Bandeau(self,TITRE,INTRO,nomImage="xpy/Images/32x32/Matth.png")
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

    def Close(self):
        self.EndModal(wx.OK)

#-------------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    dlg = Dialog()
    dlg.ShowModal()
    app.MainLoop()
