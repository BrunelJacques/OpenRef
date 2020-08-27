# !/usr/bin/env python
# -*- coding: utf-8 -*-

#----------------------------------------------------------------------------
# Application :    Projet Noelite, outils pour compta
# Licence:         Licence GNU GPL
#----------------------------------------------------------------------------

import wx
import xpy.xUTILS_Config    as xucfg
import xpy.xGestionConfig   as xgc
import xpy.xGestionDB       as xdb
import xpy.xUTILS_SaisieParams          as xusp
import xpy.xGestion_TableauRecherche    as xgtr
import xpy.xGestion_TableauEditor       as xgte
from xpy.outils.ObjectListView import ColumnDefn

# Constantes de paramétrage des accès aux bases de données
MATRICE_COMPTAS = {'quadra': {
                            'fournisseurs':{'select':'Numero,CleDeux,Intitule',
                                            'from'  :'Comptes',
                                            'where' :"Type = 'F'",
                                            'filtre':"AND (Numero like \"%xxx%\" OR CleDeux like \"%xxx%\" OR Intitule like \"%xxx%\")"},
                            'clients':  {'select': 'Numero,CleDeux,Intitule',
                                            'from'  : 'Comptes',
                                            'where' : "Type = 'C'",
                                            'filtre':"AND (CleDeux like \"%xxx%\" OR Intitule like \"%xxx%\")"},
                            'generaux': {'select': 'Numero,CleDeux,Intitule',
                                            'from'  :'Comptes',
                                            'where' : "Type = 'G'",
                                            'filtre':"AND (CleDeux like \"%xxx%\" OR Intitule like \"%xxx%\")"},
                            'journaux': {'select': 'Code,Libelle,CompteContrepartie,TypeJournal',
                                            'from':' Journaux',
                                            'where': "TypeJournal = 'T'",
                                            'filtre':"AND (Code like \"%xxx%\" OR Intitule like \"%xxx%\")"},
                            }}

MATRICE_COMPTES = {
    'lstChamps': ['ID','cle','libelle'],
    'lstNomsColonnes': ["numero","cle","libelle"],
    'lstTypes': ['VARCHAR(10)','VARCHAR(30)','VARCHAR(130)'],
    'lstValDefColonnes':['','',''],
    'lstLargeurColonnes':[90,100,-1]
    }

MATRICE_JOURNAUX = {
    'lstChamps': ['ID','libelle','contrepartie','type'],
    'lstNomsColonnes': ["code","libelle",'contrepartie','type'],
    'lstTypes': ['INTEGER','VARCHAR(130)','VARCHAR(60)','VARCHAR(10)'],
    }

def GetLstComptas():
    lstCpta = [x for x in MATRICE_COMPTAS.keys()]
    return lstCpta

# ouvre la base de donnée compta et interagit
class Compta(object):
    def __init__(self,parent,compta='quadra'):
        self.db = self.DB(parent,compta)
        if compta in MATRICE_COMPTAS:
            self.dicTables = MATRICE_COMPTAS[compta]
        else: wx.MessageBox("Les formats de la compta %s , ne sont pas  paramétrés dans le programme"%compta)
        self.table = None
        if self.db and self.db.echec:
            self.db = None
        self.nameCpta = compta

    # connecteur à la base compta
    def DB(self,parent,compta):
        # recherche des configuration d'accès aux base de données clé 'db_prim'
        paramFile = xucfg.ParamFile(nomFichier="Config")
        dicConfig = paramFile.GetDict(None, 'CONFIGS')
        if not 'lstConfigs' in dicConfig.keys(): dicConfig['lstConfigs'] = []
        if not 'lstIDconfigs' in dicConfig.keys(): dicConfig['lstIDconfigs'] = []
        lddDonnees = dicConfig['lstConfigs']
        configCpta = None
        for config in lddDonnees:
            if 'db_prim' in config.keys():
                if config['db_prim']['ID'] == compta:
                    configCpta = config['db_prim']
        ret = wx.ID_OK
        while (ret == wx.ID_OK) and (not configCpta):
            # gestion d'une configuration nouvelle
            dlgGest = xgc.DLG_saisieUneConfig(compta)
            ret = dlgGest.ShowModal()
            if ret == wx.OK:
                ddDonnees = dlgGest.GetValeurs()
                configCpta = dlgGest.GetConfig()
                # test de l'accès
                db = xdb.DB(config=configCpta)
                db.AfficheTestOuverture()
                echec = db.echec
                db.Close()
                if not echec:
                    # sauve
                    lddDonnees.append(ddDonnees)
                    dicConfig['lstIDconfigs'].append(ddDonnees['ID'])
                    cfg = xucfg.ParamFile()
                    cfg.SetDict({'lstIDconfigs': dicConfig['lstIDconfigs']}, 'CONFIGS', close=False)
                    cfg.SetDict({'lstConfigs': lddDonnees}, 'CONFIGS')

        if configCpta:
            return xdb.DB(config=configCpta)

    # Appel d'une liste extraite de la base de donnée pour table préalablement renseignée
    def GetDonnees(self,**kwds):
        filtre = kwds.pop('filtre','')
        table = kwds.pop('table','')
        if table == '': table = self.table
        if not table:
            wx.MessageBox("UTILS_Compta: Manque l'info de la table à interroger...")
            return []
        donnees = []
        dicTable = self.dicTables[table]
        firstChamp = dicTable['select'].split(',')[0]
        req = ''
        for segment in ('select','from','where'):
            if segment in dicTable.keys():
                req += segment.upper() + " %s"%dicTable[segment] +"\n"
        if len(filtre) > 0 and 'filtre' in dicTable.keys():
            txtfiltre = dicTable['filtre'].replace("xxx","%s"%filtre)
            # ajout du filtre dans la requête
            req += "%s\n"%txtfiltre
        req += "ORDER BY %s;"%firstChamp
        ret = self.db.ExecuterReq(req,mess="UTILS_Compta.GetDonnees %s"%table)
        if ret == "ok":
            donnees = self.db.ResultatReq()
        return donnees

    # Constitue la liste des journaux si la compta est en ligne
    def GetJournaux(self):
        if not self.db: return []
        return self.GetDonnees(table='journaux')

    # Composition du dic de tous les paramètres à fournir pour l'OLV
    def GetDicOlv(self,table):
        nature = None
        matrice = None
        if table in ('fournisseurs','clients','generaux'):
            nature = 'compte'
            matrice = MATRICE_COMPTES
        elif table == 'journaux':
            nature = 'journal'
            matrice = MATRICE_JOURNAUX
        dicBandeau = {'titre':"Choix d'un %s"%nature,
                      'texte':"les mots clés du champ en bas permettent de filtrer d'autres lignes et d'affiner la recherche",
                      'hauteur':15, 'nomImage':"xpy/Images/32x32/Matth.png"}
        # Composition de la matrice de l'OLV familles, retourne un dictionnaire    
        lstChamps =         matrice['lstChamps']
        lstNomsColonnes =   matrice['lstNomsColonnes']
        lstCodesColonnes =  [xusp.SupprimeAccents(x) for x in lstNomsColonnes]
        lstValDefColonnes =   matrice['lstValDefColonnes']
        lstLargeurColonnes = matrice['lstLargeurColonnes']
        lstColonnes = xusp.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
        return   {
                    'listeColonnes': lstColonnes,
                    'listeChamps':lstChamps,
                    'listeNomsColonnes':lstNomsColonnes,
                    'listeCodesColonnes':lstCodesColonnes,
                    'getDonnees': self.GetDonnees,
                    'dicBandeau': dicBandeau,
                    'colonneTri': 2,
                    'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                    'largeur' : 500,
                    'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                    }

    # Lance un DLG pour le choix d'un enregistrement dans une liste
    def ChoisirItem(self,table='generaux',filtre=''):
        self.table = table
        dicOlv = self.GetDicOlv(table)
        dlg = xgtr.DLG_tableau(None, dicOlv=dicOlv)
        if len(filtre)>0:
            dlg.ctrlOlv.Parent.barreRecherche.SetValue(filtre)
            dlg.ctrlOlv.Filtrer(filtre)
        ret = dlg.ShowModal()
        if ret == wx.OK:
            item = dlg.GetSelection().donnees
        else:
            item = None
        dlg.Destroy()
        return item

    # Recherche automatique d'un item
    def GetOneAuto(self,table='clients',filtre=''):
        self.table = table

        # fonction recherche un seul items contenant un mot limité à lg caractères puis décroisant
        def testMatch(mot,lg=10):
            lstTemp = []
            match = False
            for lgtest in range(lg,2,-1):
                lstTemp = self.GetDonnees(filtre=mot[:lgtest+1])
                if len(lstTemp) == 0 : continue
                elif len(lstTemp) == 1 :
                    match = True
                    break
                elif len(lstTemp) == 2:
                    # teste l'identité des libellés pos(2) pour comptes en double
                    if lstTemp[0][2] == lstTemp[1][2]:
                        lstTemp = lstTemp[1:2]
                        match = True
                        break
                else:
                    break
            return match, lstTemp,lgtest

        # appel avec 10 caractères du filtre puis réduit jusqu'a trouver au moins un item (cible clé d'apppel)
        match,lstItems,lgtest = testMatch(filtre.replace(' ',''),lg=10)
        motTest = filtre.replace(' ','')[:lgtest+1]
        # deuxième tentative avec chaque mot du filtre de + de 3 car (cible libellé)
        if not match:
            lstMots = filtre.split(' ')
            lstIx = []
            # calcul des longeurs pour traitement par lg décroissante item 'xx0yy' xx = lg yy=ix
            for ix in range(len(lstMots)):
                if len(lstMots[ix]) <= 3: continue
                lstIx.append(1000*len(lstMots[ix])+ix)
            # appel par mot de longeur décroissante
            for pointeur in sorted(lstIx,reverse=True):
                ix = pointeur%1000
                match, lstItems, lgtest2 = testMatch(lstMots[ix],lg=min(10,len(lstMots[ix])))
                if len(lstItems)>0 and lgtest2 + 1 > len(motTest):
                    motTest = lstMots[ix][:lgtest2 + 1]
                if match: break
        # proposition de filtre pour recherche manuelle (le radical le plus long donnant plusieurs items)
        self.filtreTest = motTest
        item = None
        if match: item = lstItems[0]
        return item

# --------------- TESTS ----------------------------------------------------------
if __name__ == u"__main__":
    import os
    os.chdir("..")
    app = wx.App(0)
    cpt = Compta(None,compta='quadra')
    print(cpt.GetOneAuto('fournisseurs','sncf internet paris'),cpt.filtreTest)
    cpt.ChoisirItem('fournisseurs','sncfi')
    app.MainLoop()
