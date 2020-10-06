#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# Application :    Noelite, Gestion des immobilisations
# Usage :     Aficher une liste des immos permettant de gérer les lignes
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# -------------------------------------------------------------------------

import wx
import os
import datetime
import xpy.xGestion_TableauEditor    as xgte
import xpy.xGestion_TableauRecherche as xgtr
import xpy.xUTILS_SaisieParams       as xusp
from xpy.outils.ObjectListView  import ColumnDefn
from xpy.outils                 import xformat

# Fonctions de transposition entrée à gérer lors de l'import des données
def ComposeFuncImp(dlg,entete,donnees):
    # Fonction import pour composition
    colonnesIn =    ["Code Véhicule       ","Date Début     ","Membre        ","Partenaire  ","Activité ",
                     "KM Début       ","KM Fin   "]
    champsIn =      ['vehicule','dtkmdeb','membre','partenaire','activite','kmdeb','kmfin']
    lstOut = [] # sera composé selon champs out
    champsOut = dlg.ctrlOlv.lstCodesColonnes
    # teste la cohérence de la première ligne importée
    mess = "Vérification des champs trouvés,\n\n"
    mess += '{:_<22} '.format('ATTENDU') + 'TROUVÉ\n\n'
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
            value = ligneIn[champsIn.index(champ)]
            if isinstance(value,datetime.datetime):
                value = datetime.date(value.year,value.month,value.day)
            ligneOut[champsOut.index(champ)] = value
        # calcul auto d'une date fin de mois
        findemois = xformat.FinDeMois(ligneIn[champsIn.index('dtkmdeb')])
        ligneOut[champsOut.index('dtkmfin')] = findemois
        # recherche champ libellé véhicule
        dicVehicule = dlg.noegest.GetVehicule(mode='auto',filtre=ligneIn[champsIn.index('vehicule')])
        if dicVehicule:
            ligneOut[champsOut.index('IDvehicule')] = dicVehicule['idanalytique']
            ligneOut[champsOut.index('vehicule')] =  dicVehicule['abrege']
            ligneOut[champsOut.index('nomvehicule')] = dicVehicule['nom']
        # détermine le type de tiers
        if ligneIn[champsIn.index('activite')]:
            ligneOut[champsOut.index('typetiers')] = 'A'
            ligneOut[champsOut.index('IDtiers')] =  ligneIn[champsIn.index('activite')]
            dicActivite = dlg.noegest.GetActivite(mode='auto', filtre=ligneIn[champsIn.index('activite')])
            if dicActivite:
                ligneOut[champsOut.index('IDtiers')] = dicActivite['idanalytique']
                ligneOut[champsOut.index('nomtiers')] = dicActivite['nom']
        elif ligneIn[champsIn.index('partenaire')]:
            ligneOut[champsOut.index('typetiers')] = 'P'
            ligneOut[champsOut.index('nomtiers')] = ligneIn[champsIn.index('partenaire')]
        elif ligneIn[champsIn.index('membre')]:
            ligneOut[champsOut.index('typetiers')] = 'C'
            ligneOut[champsOut.index('nomtiers')] = ligneIn[champsIn.index('membre')]
        # calcul conso
        kmdeb = xformat.Nz(ligneOut[champsOut.index('kmdeb')])
        kmfin = xformat.Nz(ligneOut[champsOut.index('kmfin')])
        if kmdeb <= kmfin and kmdeb > 0:
            ligneOut[champsOut.index('conso')] = kmfin - kmdeb
        lstOut.append(ligneOut)
    return lstOut

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
            ColumnDefn("IDconso", 'centre', 0, 'IDconso',
                       isEditable=False),
            ColumnDefn("IDvehicule", 'centre', 0, 'IDvehicule',
                       isEditable=False),
            ColumnDefn("Véhicule", 'center', 70, 'vehicule', isSpaceFilling=False,),
            ColumnDefn("Nom Véhicule", 'left', 120, 'nomvehicule',
                       isSpaceFilling=True, isEditable=False),
            ColumnDefn("Type Tiers", 'center', 40, 'typetiers', isSpaceFilling=False,valueSetter='A',
                       choices=['A analytique','C client','P partenaire' ] ),
            ColumnDefn("Activité", 'center', 60, 'IDtiers', isSpaceFilling=False),
            ColumnDefn("Nom tiers/activité", 'left', 130, 'nomtiers',
                       isSpaceFilling=True, isEditable=False),
            ColumnDefn("Date Début", 'center', 85, 'dtkmdeb',
                       stringConverter=xformat.FmtDate, isSpaceFilling=False),
            ColumnDefn("KM début", 'right', 90, 'kmdeb', isSpaceFilling=False,valueSetter=0,
                       stringConverter=xformat.FmtInt),
            ColumnDefn("Date Fin", 'center', 85, 'dtkmfin',
                       stringConverter=xformat.FmtDate, isSpaceFilling=False),
            ColumnDefn("KM fin", 'right', 90, 'kmfin', isSpaceFilling=False,valueSetter=0,
                       stringConverter=xformat.FmtInt),
            ColumnDefn("KM conso", 'right', 80, 'conso', isSpaceFilling=False,valueSetter=0,
                       stringConverter=xformat.FmtInt, isEditable=False),
            ColumnDefn("Observation", 'left', 150, 'observation',
                       isSpaceFilling=True),
            ]

# paramètre les options de l'OLV
def GetOlvOptions(dlg):
    return {
            'hauteur': 400,
            'largeur': 950,
            'checkColonne': False,
            'recherche': True,
            'autoAddRow':True,
            'msgIfEmpty':"Saisir ou importer un fichier !",
            'dictColFooter': {'tiers': {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                              'observation': {"mode": "texte", "alignement": wx.ALIGN_LEFT, "texte": 'km imputés'},
                              'conso': {"mode": "total"}, }
    }


# ----------------------------------------------------------------------------------
def GetFamilles(db,matriceOlv={}, filtre = None, limit=100):
    # ajoute les données à la matrice pour la recherche d'une famille
    where = ""
    if filtre:
        where = """WHERE familles.adresse_intitule LIKE '%%%s%%'
                        OR individus_1.ville_resid LIKE '%%%s%%'
                        OR individus.nom LIKE '%%%s%%'
                        OR individus.prenom LIKE '%%%s%%' """%(filtre,filtre,filtre,filtre,)

    lstChamps = matriceOlv['listeChamps']
    lstCodesColonnes = matriceOlv['listeCodesColonnes']

    req = """   SELECT %s 
                FROM ((familles 
                LEFT JOIN rattachements ON familles.IDfamille = rattachements.IDfamille) 
                LEFT JOIN individus ON rattachements.IDindividu = individus.IDindividu) 
                LEFT JOIN individus AS individus_1 ON familles.adresse_individu = individus_1.IDindividu
                %s
                LIMIT %d ;""" % (",".join(lstChamps),where,limit)
    retour = db.ExecuterReq(req, mess='GetFamilles' )
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()
    # composition des données du tableau à partir du recordset, regroupement par famille
    dicFamilles = {}
    # zero,IDfamille,designation,cp,ville,categ,nom,prenom
    ixID = lstCodesColonnes.index('idfam')
    for record in recordset:
        if not record[ixID] in dicFamilles.keys():
            dicFamilles[record[ixID]] = {}
            for ix in range(len(lstCodesColonnes)):
                dicFamilles[record[ixID]][lstCodesColonnes[ix]] = record[ix]
        else:
            # ajout de noms et prénoms si non encore présents
            if not record[-2] in dicFamilles[record[ixID]]['noms']:
                dicFamilles[record[ixID]]['noms'] += "," + record[-2]
            if not record[-1] in dicFamilles[record[ixID]]['prenoms']:
                dicFamilles[record[ixID]]['prenoms'] += "," + record[-1]

    lstDonnees = []
    for key, dic in dicFamilles.items():
        ligne = []
        for code in lstCodesColonnes:
            ligne.append(dic[code])
        lstDonnees.append(ligne)
    dicOlv =  matriceOlv
    dicOlv['listeDonnees']=lstDonnees
    return lstDonnees

def GetMatriceFamilles():
    dicBandeau = {'titre':"Recherche d'une famille",
                  'texte':"les mots clés du champ en bas permettent de filtrer d'autres lignes et d'affiner la recherche",
                  'hauteur':15, 'nomImage':"xpy/Images/32x32/Matth.png"}

    # Composition de la matrice de l'OLV familles, retourne un dictionnaire

    lstChamps = ['0','familles.IDfamille','familles.adresse_intitule','individus_1.cp_resid','individus_1.ville_resid',
                 'individus.nom','individus.prenom']

    lstNomsColonnes = ["0","IDfam","désignation","cp","ville","noms","prénoms"]

    lstTypes = ['INTEGER','INTEGER','VARCHAR(80)','VARCHAR(30)','VARCHAR(100)',
                'VARCHAR(90)','VARCHAR(120)']
    lstCodesColonnes = [xusp.SupprimeAccents(x) for x in lstNomsColonnes]
    lstValDefColonnes = xgte.ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = xgte.LargeursDefaut(lstNomsColonnes, lstTypes)
    lstColonnes = xusp.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
    return   {
                'listeColonnes': lstColonnes,
                'listeChamps':lstChamps,
                'listeNomsColonnes':lstNomsColonnes,
                'listeCodesColonnes':lstCodesColonnes,
                'getDonnees': GetFamilles,
                'dicBandeau': dicBandeau,
                'autoSizer': False,
                'colonneTri': 2,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                }

def ComposeLstDonnees(record,lstChamps):
    # retourne les données pour colonnes, extraites d'un record défini par une liste de champs
    lstdonnees=[]
    for ix in range(len(lstChamps)):
        lstdonnees.append(record[ix])
    return lstdonnees

class PNL_Pied(xgte.PNL_Pied):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        xgte.PNL_Pied.__init__(self,parent, dicPied, **kwds)

class Dialog(xgtr.DLG_tableau):
    def __init__(self):
        # params d'actions: ce sont des boutons placés à droite et non en bas
        lstActions = [('Action1', wx.ID_COPY, 'Choix un', "Cliquez pour l'action 1"),
                      ('Action2', wx.ID_CUT, 'Choix deux', "Cliquez pour l'action 2")]
        # params des actions ou boutons: name de l'objet, fonction ou texte à passer par eval()
        dicOnClick = {'Action1': lambda evt: wx.MessageBox('ceci active la fonction action1'),
                      'Action2': 'self.parent.Close()', }
        self.txtInfo =  "connection à la base de donnée en cours"

        dicOlv = GetMatriceFamilles()
        super().__init__(self,dicOlv = dicOlv, lstActions = lstActions, lstBtns = None, dicOnClick = dicOnClick )
        dicOlv['largeur'] = 400
        self.dicOlv = dicOlv
        # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = [ wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),self.txtInfo]
        dicPied = {'lstBtns': GetBoutons(self), "lstInfos": lstInfos}
        self.pnl.pnlPied = PNL_Pied(self, dicPied)
        self.pnl.ProprietesOlv()
        self.pnl.do_layout()


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

    def OnExporter(self,event):
       # affichage résultat
        wx.MessageBox("Fin de transfert")

    def OnFermer(self, event):
        # si présence d'un Final et pas de sortie par fermeture de la fenêtre
        if not event.EventObject.ClassName == 'wxDialog' and hasattr(self,'Final'):
            self.Final()

        if self.IsModal():
            self.EndModal(wx.OK)
        else:
            self.Close()

    def Final(self):
        # sauvegarde des params
        self.pnlParams.SauveParams(close=True)


if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    exempleframe = Dialog()
    app.SetTopWindow(exempleframe)
    ret = exempleframe.ShowModal()
    if exempleframe.GetSelection():
        print(exempleframe.GetSelection().donnees)
    else: print(None)
    app.MainLoop()
