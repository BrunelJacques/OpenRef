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
                                            'filtre':"AND (CleDeux like \"%xxx%\" OR Intitule like \"%xxx%\")"},
                            'clients':  {'select': 'Numero,CleDeux,Intitule',
                                            'from'  : 'Comptes',
                                            'where' : "Type = 'C'",
                                            'filtre':"AND (CleDeux like \"%xxx%\" OR Intitule like \"%xxx%\")"},
                            'generaux': {'select': 'Numero,CleDeux,Intitule',
                                            'from'  :'Comptes',
                                            'where' : "Type = 'G'",
                                            'filtre':"AND (CleDeux like \"%xxx%\" OR Intitule like \"%xxx%\")"},
                            'journaux': {'select': 'Code,Libelle,TypeJournal,CompteContrepartie',
                                            'from':' Journaux',
                                            'filtre':"WHERE (Code like \"%xxx%\" OR Intitule like \"%xxx%\")"},
                            }}

MATRICE_COMPTES = {
    'lstChamps': ['ID','cle','libelle'],
    'lstNomsColonnes': ["numero","cle","libelle"],
    'lstTypes': ['VARCHAR(10)','VARCHAR(30)','VARCHAR(130)'],
    'lstValDefColonnes':['','',''],
    'lstLargeurColonnes':[90,100,-1]
    }

MATRICE_JOURNAUX = {
    'lstChamps': ['ID','libelle','type','contrepartie'],
    'lstNomsColonnes': ["code","libelle",'type','contrepartie'],
    'lstTypes': ['INTEGER','VARCHAR(130)','VARCHAR(10)','VARCHAR(60)',],
    }

def GetLstComptas():
    lstCpta = [x for x in MATRICE_COMPTAS.keys()]
    return lstCpta

# ouvre la base de donnée compta et interagit
class Compta(object):
    def __init__(self,parent,compta='quadra'):
        self.db = self.DB(parent,compta)
        self.dicTables = MATRICE_COMPTAS[compta]
        self.table = None

        if self.db and self.db.echec:
            self.db = None

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

    # Appel d'une liste extraite de la base de donnée
    def GetDonnees(self,**kwds):
        filtre = kwds.pop('filtre','')
        donnees = []
        dicTable = self.dicTables[self.table]
        req = ''
        for segment in ('select','from','where'):
            if segment in dicTable.keys():
                req += segment.upper() + " %s"%dicTable[segment] +"\n"
        if len(filtre) > 0 and 'filtre' in dicTable.keys():
            txtfiltre = dicTable['filtre'].replace("xxx","%s"%filtre)
            # ajout du filtre dans la requête
            req += "%s\n"%txtfiltre
        req += ";"
        ret = self.db.ExecuterReq(req,mess="UTILS_Compta.GetDonnees %s"%self.table)
        if ret == "ok":
            donnees = self.db.ResultatReq()
        return donnees

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
                    'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                    }

    # Choix d'un enregistrement dans une liste
    def GetOneItem(self,table='generaux'):
        self.table = table
        dicOlv = self.GetDicOlv(table)
        dlg = xgtr.DLG_tableau(None, dicOlv=dicOlv)
        ret = dlg.ShowModal()
        if ret == wx.OK:
            IDitem = dlg.GetSelection().donnees[0]
        else:
            IDitem = None
        dlg.Destroy()
        return IDitem

# --------------- TESTS ----------------------------------------------------------
if __name__ == u"__main__":
    import os
    os.chdir("..")
    app = wx.App(0)
    cpt = Compta(None,compta='quadra')
    print(cpt.GetOneItem('clients'))
    app.MainLoop()
