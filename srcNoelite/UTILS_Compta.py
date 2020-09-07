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
from xpy.outils             import xexport,xformat

# Paramétrage des accès aux bases de données, les 'select' de _COMPTAS doivent respecter 'lstChamps' de  _COMPTES
MATRICE_COMPTAS = {'quadra': {
                            'fournisseurs':{'select':'Numero,CleDeux,Intitule',
                                            'from'  :'Comptes',
                                            'where' :"Type = 'F'",
                                            'filtre':"AND (Numero like \"%xxx%\" OR CleDeux like \"%xxx%\" OR Intitule like \"%xxx%\")"},
                            'clients':  {'select': 'Numero,CleDeux,Intitule',
                                            'from'  : 'Comptes',
                                            'where' : "Type = 'C'",
                                            'filtre':"AND (Numero like \"%xxx%\" OR CleDeux like \"%xxx%\" OR Intitule like \"%xxx%\")"},
                            'generaux': {'select': 'Numero,CleDeux,Intitule',
                                            'from'  :'Comptes',
                                            'where' : "Type = 'G'",
                                            'filtre':"AND (Numero like \"%xxx%\" OR CleDeux like \"%xxx%\" OR Intitule like \"%xxx%\")"},
                            'journaux': {'select': 'Code,Libelle,CompteContrepartie,TypeJournal',
                                            'from':' Journaux',
                                            'where': "TypeJournal = 'T'",
                                            'filtre':"AND (Code like \"%xxx%\" OR Libelle like \"%xxx%\")"},
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
    'lstValDefColonnes':[1,'','','',''],
    'lstLargeurColonnes':[90,-1,100,60]
    }

#FORMATS_EXPORT
"""les formats d'exports sont décrits plus bas, en dessous de la définition des fonctions d'exports,
    car ils les appellent ces fonctions qui doivent donc êtres déclarées avant dans le module"""

# Transposition des valeurs Export, gérer chaque item FORMAT_xxxx pour les spécificités
def ComposeFuncExp(dicParams,donnees,champsIn,champsOut):
    # 'in' est l'OLV, 'out' est le fichier de sortie
    lstOut = []
    #formatOut = dicParams['fichiers']['formatexp']
    for ligne in donnees:
        ligneOut = []
        typePiece = "B" # cas par défaut B comme carte Bancaire
        for champ in champsOut:
            if champ in champsIn:
                valeur = ligne.donnees[champsIn.index(champ)]
            elif champ in ('debit','credit','sens','valeur','valeur00'):
                valeur = ligne.donnees[champsIn.index('montant')]
            else: valeur = ''
            # composition des champs sortie
            if champ    == 'journal':   valeur = dicParams['compta']['journal']
            elif champ  == 'compte':
                if not valeur or valeur == '' : valeur = '471'
            elif champ  == 'date':
                valeur = xformat.DateStrToWxdate(valeur)
            elif champ  == 'typepiece': valeur = typePiece
            elif champ  == 'contrepartie': valeur = dicParams['compta']['contrepartie']
            elif champ  == 'devise': valeur = 'EUR'
            elif champ  == 'sens':
                mtt = float(valeur.replace(",","."))
                if mtt >=0: valeur = 'C'
                else: valeur = 'D'
            elif champ  == 'valeur': valeur = abs(float(valeur.replace(",",".")))
            elif champ == 'valeur00':valeur = abs(float(valeur.replace(",", "."))*100)
            elif champ  == 'debit':
                montant = float(valeur.replace(",","."))
                if montant < 0.0: valeur = -montant
                else: valeur = 0.0
            elif champ  == 'credit':
                montant = float(valeur.replace(",","."))
                if montant >= 0.0: valeur = montant
                else: valeur = 0.0
            ligneOut.append(valeur)
        lstOut.append(ligneOut)
        # ajout de la contrepartie banque
        ligneBanque = [x for x in ligneOut]
        ligneBanque[champsOut.index('contrepartie')]    = ligneOut[champsOut.index('compte')]
        ligneBanque[champsOut.index('compte')]          = dicParams['compta']['contrepartie']
        if 'debit' in champsOut:
            ligneBanque[champsOut.index('debit')]    = ligneOut[champsOut.index('credit')]
            ligneBanque[champsOut.index('credit')]    = ligneOut[champsOut.index('debit')]
        elif 'sens' in champsOut:
            ix = champsOut.index('sens')
            if ligneOut[ix] == 'D': ligneBanque[ix] = 'C'
            elif ligneOut[ix] == 'C': ligneBanque[ix] = 'D'
        lstOut.append(ligneBanque)
    return lstOut

def ExportExcel(formatExp, lstValeurs):
    matrice = FORMATS_EXPORT[formatExp]['matrice']
    champsOut   = [x['code'] for x in matrice]
    widths      = [x['lg'] for x in matrice]
    lstColonnes = [[x, None, widths[champsOut.index(x)], x] for x in champsOut]
    # envois dans un fichier excel
    xexport.ExportExcel(listeColonnes=lstColonnes,
                        listeValeurs=lstValeurs,
                        titre=formatExp)

def ExportQuadra(formatExp, lstValeurs):
    matrice = FORMATS_EXPORT[formatExp]['matrice']
    # envois dans un fichier texte
    xexport.ExportLgFixe(nomfic=formatExp+".txt",matrice=matrice,valeurs=lstValeurs)


FORMATS_EXPORT = {"Quadra via Excel":{  'compta':'quadra',
                                        'fonction':ComposeFuncExp,
                                        'matrice':[
                                                {'code':'journal',   'lg': 40,},
                                                {'code':'date',      'lg': 80,},
                                                {'code':'compte',    'lg': 60,},
                                                {'code':'typepiece', 'lg': 25,},
                                                {'code':'libelle',   'lg': 240,},
                                                {'code':'debit',     'lg': 60,},
                                                {'code':'credit',    'lg': 60,},
                                                {'code':'piece',     'lg': 60,},
                                                {'code':'contrepartie','lg': 60,},
                                                ],
                                        'genere':ExportExcel},
                  "Quadra qExport ASCII": { 'compta':'quadra',
                                        'fonction':ComposeFuncExp,
                                        'matrice':[
                                                {'code': 'typ',     'cat': str, 'lg': 1, 'align': "<"},
                                                {'code': 'compte',  'cat': str, 'lg': 8, 'align': "<"},
                                                {'code': 'journal',      'cat': str, 'lg': 2, 'align': "<"},
                                                {'code': 'fol',     'cat': str, 'lg': 3, 'align': "<"},
                                                {'code': 'date',    'cat': wx.DateTime, 'lg':6, 'fmt': "%d%m%y"},
                                                {'code': 'fil',    'cat': str, 'lg': 21, 'align': ">"},
                                                {'code': 'sens',    'cat': str, 'lg': 1, 'align': "<"},
                                                {'code': 'valeur00',  'cat': float, 'lg': 13,'fmt':"{0:+013.0f}"},
                                                {'code': 'contrepartie','cat': str, 'lg': 8, 'align': "<"},
                                                {'code': 'fil',    'cat': str, 'lg': 44, 'align': ">"},
                                                {'code': 'devise',  'cat': str, 'lg': 3, 'align': "<"},
                                                {'code': 'journal',     'cat': str, 'lg': 3, 'align': "<"},
                                                {'code': 'fil',    'cat': str, 'lg': 3, 'align': "<"},
                                                {'code': 'libelle','cat': str, 'lg': 30, 'align': "<"},
                                                {'code': 'fil',    'cat': str, 'lg': 2, 'align': "<"},
                                                {'code': 'piece','cat': str, 'lg': 10, 'align': "<"},
                                                {'code': 'fil',    'cat': str, 'lg': 73, 'align': "<"},
                                                ],
                                        'genere':ExportQuadra},
                  }

def GetLstComptas():
    lstCpta = [x for x in MATRICE_COMPTAS.keys()]
    return lstCpta

class Export(object):
    def __init__(self,parent,compta):
        self.parent = parent
        self.nameCpta = compta.nameCpta

    def Exporte(self,params={},donnees=[],olv=None):
        # génération du fichier
        formatExp = params['fichiers']['formatexp']
        champsOut = [x['code'] for x in FORMATS_EXPORT[formatExp]['matrice']]

        # transposition des lignes par l'appel de la fonction 'ComposeFuncExp'
        lstValeurs = FORMATS_EXPORT[formatExp]['fonction'](donnees,
                                                            olv.innerList,
                                                            olv.lstCodesColonnes,
                                                            champsOut)
        # appel de la fonction génération fichier
        FORMATS_EXPORT[formatExp]['genere'](formatExp,lstValeurs)

        # mise à jour du dernier numero de pièce affiché avant d'être sauvegardé
        if 'piece' in champsOut:
            ixp = champsOut.index('piece')
            lastPiece = lstValeurs[-1][ixp]
            box = self.parent.pnlParams.GetBox('compta')
            box.SetOneValue('compta.lastpiece',lastPiece)
        return

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
    def GetOneAuto(self,table='clients',filtre='',lib=None):
        self.table = table
        # la recherche peut se faire sur un filtre qui est un libellé complet
        if lib:
            # on testera la clé d'appel dans le lib d'origine compacté
            filtre = lib
            lib = lib.replace(' ','')
        # formatage du filtre
        filtre = filtre.replace(',','')
        lstMots = filtre.split(' ')

        # fonction recherche un seul items contenant un mot limité à lg caractères puis décroisant
        def testMatch(mot,lg=10,mini=3):
            lstTemp = []
            match = False
            lgrad = 0
            for lgtest in range(lg,mini-1,-1):
                lstTemp = self.GetDonnees(filtre=mot[:lgtest],table=table)
                # élimine les cas où la cle d'appel du compte n'est pas présente dans le libelle complet
                if lib:
                    lstTemp = [x for x in lstTemp if x[1] and len(x[1]) > 2 and x[1] in lib]
                if len(lstTemp) == 0 : continue
                elif len(lstTemp) == 1 :
                    match = True
                    lgrad = lgtest
                    break
                elif len(lstTemp) == 2:
                    # teste l'identité des libellés pos(2) pour comptes en double
                    if lstTemp[0][2] == lstTemp[1][2]:
                        lstTemp = lstTemp[1:2]
                        match = True
                        lgrad = lgtest
                        break
                else:
                    break
            return match, lstTemp,lgrad

        # appel avec 10 caractères du filtre puis réduit jusqu'a trouver au moins un item (cible clé d'apppel)
        lgMotUn = len(lstMots[0])
        match,lstItems,lgtest = testMatch(filtre.replace(' ',''),lg=10,mini=min(4,lgMotUn))
        if not match: lgtest = lgMotUn
        motTest = filtre.replace(' ','')[:lgtest+1]
        # deuxième tentative avec chaque mot du filtre de + de 3 car (cible libellé)
        if not match:
            lstIx = []
            # calcul des longeurs pour traitement par lg décroissante item 'xx0yy' xx = lg yy=ix
            for ix in range(len(lstMots)):
                if len(lstMots[ix]) <= 3: continue
                lstIx.append(1000*len(lstMots[ix])+ix)
            # appel par mot de longeur décroissante
            for pointeur in sorted(lstIx,reverse=True):
                ix = pointeur%1000
                lgMot = len(lstMots[ix])
                match, lstItems, lgtest2 = testMatch(lstMots[ix],lg=min(10,len(lstMots[ix])),mini=max(3,lgMot))
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
    #print(cpt.GetOneAuto('fournisseurs','sncf internet paris'),cpt.filtreTest)
    cpt.ChoisirItem('clients','brunel')
    app.MainLoop()
