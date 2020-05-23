#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------
# Application :    NoeLITE, gestion des Reglements en lot
# Auteur:           Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------

NOM_MODULE = "DLG_Reglements_gestion"
ACTION = "Gestion\nreglement"
TITRE = "Saisie d'un lot de réglements !"
INTRO = "Définissez la banque et le mode puis saisissez dans le tableau"
MINSIZE = (1200,650)
WCODE = 150
WLIBELLE = 100
COLONNETRI = 2

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
import xpy.outils               as xout
import xpy.outils.xbandeau      as xbd
import xpy.xGestionConfig       as xgc
import xpy.xGestionDB           as xdb
import xpy.xGestion_TableauEditor     as xgte
import xpy.xUTILS_SaisieParams  as xusp
import xpy.xUTILS_Config        as xucfg
import srcNoelite.UTILS_Utilisateurs  as nuu
from xpy.outils.ObjectListView import ColumnDefn, CTRL_Outils, CellEditor

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
    retour = db.ExecuterReq(req, mess='%s.GetIndividus'%NOM_MODULE )
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
                'colonneTri': COLONNETRI,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                'dictColFooter': {"nom": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},}
                }
    return dicOlv

class Dialog(xgte.DLG_tableau):
    def __init__(self):
        liste_Colonnes = [
            ColumnDefn("null", 'centre', 0, "IX", valueSetter=''),
            ColumnDefn("clé", 'centre', 60, "cle", valueSetter=True, isSpaceFilling=False,
                       cellEditorCreator=CellEditor.BooleanEditor),
            ColumnDefn("mot d'ici", 'left', 200, "mot", valueSetter='A saisir', isEditable=True),
            ColumnDefn("nbre", 'right', -1, "nombre", isSpaceFilling=True, valueSetter=0.0,
                       stringConverter=xout.xformat.FmtDecimal),
            ColumnDefn("prix", 'left', 80, "prix", valueSetter=0.0, isSpaceFilling=True,
                       cellEditorCreator=CellEditor.ComboEditor),
            ColumnDefn("datee", 'center', 80, "date", valueSetter=wx.DateTime.FromDMY(1, 0, 1900), isSpaceFilling=True,
                       stringConverter=xout.xformat.FmtDate),
            ColumnDefn("choicee", 'center', 40, "choice", valueSetter="mon item", isSpaceFilling=True,
                       cellEditorCreator=CellEditor.ChoiceEditor, )
        ]
        liste_Donnees = [[1, False, "Bonjour", -1230.05939, -1230.05939, None, "deux"],
                         [2, None, "Bonsoir", 57.5, 208.99, datetime.date.today(), None],
                         [3, '', "Jonbour", 0, 'remisé', datetime.date(2018, 11, 20), "mon item"],
                         [4, 29, "Salut", 57.082, 209, wx.DateTime.FromDMY(28, 1, 2019),
                          "Gérer l'entrée dans la cellule"],
                         [None, None, "Salutation", 57.08, 0, wx.DateTime.FromDMY(1, 7, 1997), '2019-10-24'],
                         [None, 2, "Python", 1557.08, 29, wx.DateTime.FromDMY(7, 1, 1997), '2000-12-25'],
                         [None, 3, "Java", 57.08, 219, wx.DateTime.FromDMY(1, 0, 1900), None],
                         [None, 98, "langage C", 10000, 209, wx.DateTime.FromDMY(1, 0, 1900), ''],
                         ]
        dicOlv = {'lstColonnes': liste_Colonnes,
                  'listeDonnees': liste_Donnees,
                  'hauteur': 450,
                  'largeur': 650,
                  'checkColonne': False,
                  'recherche': True,
                  'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                  'dictColFooter': {"nombre": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                    "mot": {"mode": "nombre", "alignement": wx.ALIGN_CENTER}, }
                  }

        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstBtns = [('BtnPrec', wx.ID_FORWARD, wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_OTHER, (42, 22)),
                    "Cliquez ici pour retourner à l'écran précédent"),
                   ('BtnPrec2', wx.ID_PREVIEW_NEXT, "Ecran\nprécédent", "Retour à l'écran précédent next"),
                   ('BtnOK', wx.ID_OK, wx.Bitmap("xpy/Images/100x30/Bouton_fermer.png", wx.BITMAP_TYPE_ANY),
                    "Cliquez ici pour fermer la fenêtre")
                   ]
        dicOnBtn = {'Action1': lambda evt: wx.MessageBox('ceci active la fonction action1'),
                    'Action2': 'self.parent.Validation()',
                    'BtnPrec': 'self.parent.Close()'}
        lstInfos = ['Première', "Voici", wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),
                    "Autre\nInfo"]
        dicPied = {'lstBtns': lstBtns, 'dicOnBtn': dicOnBtn, "lstInfos": lstInfos}

        # cadre des paramètres
        dicParams = {
            ("ident", "Vos paramètres"): [
                {'name': 'date', 'genre': 'Date', 'label': 'Début de période', 'value': datetime.date.today(),
                 'help': 'Ce préfixe à votre nom permet de vous identifier'},
                {'name': 'utilisateur', 'genre': 'String', 'label': 'Votre identifiant', 'value': "NomSession",
                 'help': 'Confirmez le nom de sesssion de l\'utilisateur'},
            ],
        }

        xgte.DLG_tableau.__init__(self,self,dicParams=dicParams,dicOlv=dicOlv,dicPied=dicPied )
        if nuu.VerificationDroitsUtilisateurActuel("familles_reglements", "modifier") == False:
            if self.IsModal():
                self.EndModal(wx.ID_CANCEL)
            else: self.Destroy()
        self.SetTitle(NOM_MODULE)

#-------------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    dlg = Dialog()
    dlg.ShowModal()
    app.MainLoop()
