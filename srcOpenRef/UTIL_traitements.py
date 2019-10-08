#!/usr/bin/env python
# -*- coding: utf8 -*-

#------------------------------------------------------------------------
# Application :    OpenRef, Génération des traitements pré-analyses
# Auteurs:          Jacques BRUNEL
# Copyright:       (c) 2019-05     Cerfrance Provence
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import srcOpenRef.UTIL_analyses as orua
import srcOpenRef.UTIL_import as orui
import xpy.xGestionDB as xdb
import xpy.xGestion_Ligne as xgl
import unicodedata
import srcOpenRef.DATA_Tables as dtt

CHAMPS_TABLES = {
    '_Balances':['IDdossier','Compte','IDligne','Libellé','MotsCléPrés','Quantités1','Unité1','Quantités2','Unité2',
                 'SoldeDeb','DBmvt','CRmvt','SoldeFin','IDplanCompte','Affectation'],
    'produits':[ 'IDMatelier', 'IDMproduit', 'NomProduit', 'MoisRécolte', 'ProdPrincipal', 'UniteSAU', 'coefHa', 'CptProduit',
                 'Priorité', 'MotsCles', 'TypesProduit','UnitéQté1','UnitéQté2'],
    'couts': ['IDMatelier','IDMcoût','UnitéQté','CptCoût','MotsCles','TypesCoût']
    }

def SupprimeAccents(texte):
    # met en minuscule sans accents et sans caractères spéciaux le none est blanc
    if not texte: texte = ''
    if not isinstance(texte,str): texte = ''
    code = ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')
    #code = str(unicodedata.normalize('NFD', texte).encode('ascii', 'ignore'))
    code = code.lower()
    code = ''.join(car.lower() for car in code if car not in " %)(.[]',;/\n")
    return code.strip()

def Affectation(iddossier,affectation,DBsql):
    # l'affectation d'une ligne de la balance va être imputée dans les tables de synthèse
    genre,atelier,option = None,None,None
    mess = 'ok'
    if affectation :
        if len(affectation.strip()) > 0 :
            elements = affectation.split('.')
            if len(elements) > 0: genre = SupprimeAccents(elements[0]).upper()
            if len(elements) > 1: atelier = SupprimeAccents(elements[1]).upper()
            if len(elements) > 2: option = elements[2]
    # impasse sur les remises à blanc
    if not genre: return 'ok'
    # autre liminaires
    if not isinstance(iddossier,int): "le IDdossier %s n'est pas valable"%str(iddossier)
    if not genre in ('P','C','A','I'): return "L'affectation '%s', ne commence pas par 'P','C','A','I'"%affectation
    if genre == 'P':
        mess = AffectProduit(iddossier,atelier,option,DBsql)
    if genre == 'A':
        mess = AffectAtelier(iddossier,atelier,option,DBsql)
    return mess

def AffectAtelier(iddossier, atelier,poste,DBsql):

    dicAtelier = Get_Atelier(iddossier,atelier,DBsql)

    # récupère les comptes à affectés à cet atelier ou a un produit de cet atelier( 74 ou 76 vont dans l'atelier)
    affectation = '//%.%s.//%'%(atelier)
    req = """SELECT _balances.IDdossier, _balances.Compte, _balances.IDplanCompte, Sum(_balances.Quantités1), 
                _balances.Unité1, Sum(_balances.Quantités2), _balances.Unité2, Sum(_balances.SoldeDeb), Sum(_balances.SoldeFin)
            FROM _balances
            WHERE ((_balances.IDdossier = %d) 
                AND((_balances.Affectation) LIKE '%s') 
                AND ((Left(IDplanCompte,1)) In ('3','6','7')))
            GROUP BY _balances.IDdossier, _balances.Compte, _balances.IDplanCompte, _balances.Unité1, _balances.Unité2
        ;""" % (iddossier,affectation)
    ret = DBsql.ExecuterReq(req, mess='UTIL_traitements.AffectAtelier')
    if ret == "ok":
        recordset = DBsql.ResultatReq()
    else : return ret
    dicAtelier = {}
    for cle in ('AutreProduit','Subvention','Comm','Conditionnement','AutresAppros','AutresServices','AmosSpecif') :
        dicAtelier[cle] = 0.0
        dicAtelier['CPT%s'%cle.replace('Autres','')] = ''
    for iddossier, compte, idplancompte, quantites1, unite1, quantites2, unite2, soldedeb, soldefin in recordset:
        dicAtelier = VentileValeurAtelier(dicAtelier,idplancompte,quantites1,unite1,quantites2,unite2,soldedeb,soldefin)
    ret = Set_Atelier(dicAtelier,DBsql)
    return ret

def VentileValeurAtelier(dicAtelier,IDplanCompte,SoldeFin):
    # ventilation des valeurs du compte dans le atelier auquel il se rattache
    # inversion des signes de balance pour retrouver du positif dans les ateliers ou stock
    if IDplanCompte[:2] == '70':
        dicAtelier['Comptes'].append(IDplanCompte)
        dicAtelier['Ventes'] -= SoldeFin
    elif IDplanCompte[:2] == '71':
        dicAtelier['DeltaStock'] -= SoldeFin
    elif IDplanCompte[:2] == '72':
        dicAtelier['AutreProd'] -= SoldeFin
    elif IDplanCompte[:2] == '75':
        dicAtelier['AutreProd'] -= SoldeFin
    elif IDplanCompte[:3] == '603':
        dicAtelier['DeltaStock'] -= SoldeFin
    elif IDplanCompte[:3] == '604':
        dicAtelier['AchatAnmx'] -= SoldeFin
    # le paramétrage ne doit pas contenir à la fois des ((603 ou 71) et 3) dans les radicaux
    elif IDplanCompte[:1] == '3':
        dicAtelier['DeltaStock'] -= SoldeFin
        dicAtelier['StockFin'] -= SoldeFin
    else:
        dicAtelier['AutreProd'] -= SoldeFin
    return dicAtelier

def AffectProduit(iddossier, atelier, produit,DBsql):

    dicProduit = Get_Produit(iddossier,atelier,produit,DBsql)

    # récupère les comptes à affecter à ce produit
    affectation = 'P.%s.%s'%(atelier,produit)
    req = """SELECT _balances.IDdossier, _balances.Compte, _balances.IDplanCompte, Sum(_balances.Quantités1), 
                _balances.Unité1, Sum(_balances.Quantités2), _balances.Unité2, Sum(_balances.SoldeDeb), Sum(_balances.SoldeFin)
            FROM _balances
            WHERE ((_balances.IDdossier = %d) 
                AND((_balances.Affectation) = '%s') 
                AND ((Left(IDplanCompte,1)) In ('3','6','7')))
            GROUP BY _balances.IDdossier, _balances.Compte, _balances.IDplanCompte, _balances.Unité1, _balances.Unité2
        ;""" % (iddossier,affectation)
    ret = DBsql.ExecuterReq(req, mess='UTIL_traitements.AffectPoduit')
    if ret == "ok":
        recordset = DBsql.ResultatReq()
    else : return ret
    dicProduit['Comptes'] = ''
    for cle in ('Quantité1','Quantité2','Ventes','AchatAnms','DeltaStock','AutreProd','StockFin') :
        dicProduit[cle] = 0.0
    for iddossier, compte, idplancompte, quantites1, unite1, quantites2, unite2, soldedeb, soldefin in recordset:
        dicProduit = VentileValeurProduit(dicProduit,idplancompte,quantites1,unite1,quantites2,unite2,soldedeb,soldefin)
    ret = Set_Produit(dicProduit,DBsql)
    return ret

def Get_Produit(iddossier,atelier,produit,DBsql,init=True):
    # constitue un dictionnaire des modèles de produits à générer
    lstChamps = dtt.GetChamps('_Produits')
    lstChamps.extend(['UnitéQté1','UnitéQté2'])

    req = """SELECT _Produits.*,mProduits.'UnitéQté1',mProduits.'UnitéQté2'
            FROM _Produits
            INNER JOIN mProduits ON(_produits.IDMproduit = mProduits.IDMproduit) 
                                    AND(_produits.IDMatelier = mProduits.IDMatelier)
            WHERE (IDdossier = '%d') AND (IDMproduit) = '%s') AND (IDMatelier  = '%s') 
            ; """ % (iddossier,atelier,produit)
    retour = DBsql.ExecuterReq(req, mess='accès UTIL_traitement.GetProduit')
    dic = {}
    if retour == "ok":
        recordset = DBsql.ResultatReq()
        if len(recordset)>0:
            dic = orua.ListsToDic(lstChamps, recordset,1)
        else:
            dic={}
            if init :
                Set_ProduitVide(iddossier,atelier,produit,DBsql)
                dic = Get_Produit(iddossier,atelier,produit,DBsql,init=False)
    return dic

def Set_ProduitVide(iddossier,atelier,produit,DBsql):
    lstChamps, lstTypes, lstHelp = dtt.GetChampsTypes('_Produits', tous=True)
    lstTblChamps = lstChamps
    lstTblValdef = xgl.ValeursDefaut(lstChamps, lstChamps, lstTypes)
    lstTblValdef[lstTblChamps.index('IDdossier')] = iddossier
    lstTblValdef[lstTblChamps.index('IDMatelier')] = atelier
    lstTblValdef[lstTblChamps.index('IDMproduit')] = produit
    ret = DBsql.ReqInsert('_Produits', lstChamps, lstTblValdef, mess='Insert UTIL_traitement.Set_ProduitVide')
    if ret != 'ok': wx.MessageBox(ret)
    return

def Set_Produit(dicProduit,DBsql):
    # création ou MAJ d'un produits par son produit et les modèles
    IDMproduit = dicProduit['IDMproduit']
    lstTblChamps = dtt.GetChamps('_Produits', tous=True)
    lstChamps = [x for x in lstTblChamps if x in dicProduit]
    lstDonnees = [dicProduit[x] for x in lstChamps]
    orui.TronqueData(None,lstChamps,lstDonnees)
    ok = DBsql.ReqInsert('_Produits', lstChamps, lstDonnees, mess='Set_Produits Produit : %s' % IDMproduit)
    return ok

def Set_Atelier(dicAtelier,DBsql):
    # création ou MAJ d'un atelier par son produit et les modèles
    lstDonnees, lstChamps =[], []
    lstChampsTable = dtt.GetChamps('_Ateliers')
    for champ in dicAtelier.keys():
        if champ in lstChampsTable:
            lstChamps.append(champ)
            lstDonnees.append(dicAtelier[champ])
    orui.TronqueData('_Ateliers',lstChamps,lstDonnees)
    ok = DBsql.ReqInsert('_Ateliers',lstChamps,lstDonnees,mess= 'Set_Atelier Atelier'%dicAtelier['IDMatelier'])
    return ok

def VentileValeurProduit(dicProduit,IDplanCompte,Quantites1,Unite1,Quantites2,Unite2,SoldeDeb,SoldeFin):
    # ventilation des valeurs du compte dans le produit auquel il se rattache
    dicProduit['Comptes'].append(IDplanCompte)
    uniteRetenue = SupprimeAccents(dicProduit['UnitéQté1'])
    uniteBalance = SupprimeAccents(Unite1)
    if uniteBalance == uniteRetenue or len(uniteRetenue) == 0 or len(uniteBalance == 0):
        dicProduit['Quantité1'] += Quantites1
    uniteRetenue = SupprimeAccents(dicProduit['UnitéQté2'])
    uniteBalance = SupprimeAccents(Unite2)
    if uniteBalance == uniteRetenue or len(uniteRetenue) == 0 or len(uniteBalance == 0):
        dicProduit['Quantité2'] += Quantites2

    # inversion des signes de balance pour retrouver du positif dans les produits ou stock
    if IDplanCompte[:2] == '70':
        dicProduit['Ventes'] -= SoldeFin
    elif IDplanCompte[:2] == '71':
        dicProduit['DeltaStock'] -= SoldeFin
    elif IDplanCompte[:2] == '72':
        dicProduit['AutreProd'] -= SoldeFin
    elif IDplanCompte[:2] == '75':
        dicProduit['AutreProd'] -= SoldeFin
    elif IDplanCompte[:3] == '603':
        dicProduit['DeltaStock'] -= SoldeFin
    elif IDplanCompte[:3] == '604':
        dicProduit['AchatAnmx'] -= SoldeFin
    # le paramétrage ne doit pas contenir à la fois des ((603 ou 71) et 3) dans les radicaux
    elif IDplanCompte[:1] == '3':
        dicProduit['DeltaStock'] -= SoldeFin - SoldeDeb
        dicProduit['StockFin'] -= SoldeFin
    else:
        dicProduit['AutreProd'] -= SoldeFin

    # les 74subventions et 76ProdFin seront affectés à l'atelier même avec mot clé de genre produit
    return dicProduit

def ChercheIDplanCompte(compte, dicPlanComp):
    # récupération de la clé du plan comptable standard
    IDplanCompte = ''
    for cptstd in dicPlanComp.keys():
        if not cptstd == compte[:len(cptstd)]:
            continue
        else:
            IDplanCompte = cptstd
            break
    if IDplanCompte == '':
        IDplanCompte = compte[:5]
    return IDplanCompte

def Decoupe(texte):
    # isole les mots du texte afin de les comparer aux mots clés
    lstMots = []
    texte = str(texte)
    lstCar = [',', '[', ']', "'", '#', '__', '%', ';', '-', '\\n','(',')',"'","!"]
    for lettre in lstCar:
        texte = texte.replace(lettre, ' ')
    # suppression des accents et forcé en minuscule
    texte = ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')
    texte = texte.lower()
    ltxt = texte.split(' ')
    for mot in ltxt:
        mot = mot.strip()
        if len(mot) > 2:
            if mot not in lstMots:
                lstMots.append(mot)
    return lstMots

def PrechargePlanCompte(DBsql):
    # constitue un dictionnaire des modèles de comptes à générer
    lstChamps = dtt.GetChamps('cPlanComptes')
    req = """SELECT *
            FROM cPlanComptes;"""
    retour = DBsql.ExecuterReq(req, mess='accès OpenRef précharge PlanComptes ')
    dic = {}
    if retour == "ok":
        recordset = DBsql.ResultatReq()
        if len(recordset)>0:
            dic = orua.ListsToDic(lstChamps, recordset,0)
        else:
            wx.MessageBox("Aucun plan comptable disponible !")
            return {}
    return dic

def PrechargeProduits(agc, DBsql):
    # constitue un dictionnaire des modèles de produits à générer
    lstChamps = CHAMPS_TABLES['produits']
    if agc:
        where = "WHERE (((mAteliers.IDagc) In ('ANY','%s'))) OR (((mAteliers.IDagc) Is Null))"% agc
    else: where = ''
    req = """SELECT mProduits.IDMatelier, mProduits.IDMproduit, mProduits.NomProduit, mProduits.MoisRécolte,
                    mProduits.ProdPrincipal, mProduits.UniteSAU, mProduits.coefHa, mProduits.CptProduit, mProduits.Priorité, 
                    mProduits.MotsCles, mProduits.TypesProduit,mProduits.UnitéQté1,mProduits.UnitéQté2
            FROM mProduits LEFT JOIN mAteliers ON mProduits.IDMatelier = mAteliers.IDMatelier
            %s; """ % where
    retour = DBsql.ExecuterReq(req, mess='accès OpenRef précharge Produits')
    dic = {}
    if retour == "ok":
        recordset = DBsql.ResultatReq()
        if len(recordset)>0:
            dic = orua.ListsToDic(lstChamps, recordset,1)
        else:
            wx.MessageBox("Aucun modèle produit disponible, le traitement n'est pas lancé!")
            return {}
        dicPriorites={}
        for idmproduit in dic:
            dic[idmproduit]['clesstring']=GetMotsCles({'x':{'motscles':dic[idmproduit]['motscles']}},avectuple=False)
            dic[idmproduit]['clestuple'] = GetTuplesCles(dic[idmproduit]['motscles'])
            dic[idmproduit]['lstmots'] = GetMotsCles({'x': {'motscles': dic[idmproduit]['motscles']}}, avectuple=True)
            dicPriorites[(dic[idmproduit]['priorité'],idmproduit)]=idmproduit
        lstPrioritesProduits = []
        for ordre in sorted(dicPriorites.keys()):
            lstPrioritesProduits.append(dicPriorites[ordre])
    return dic,lstPrioritesProduits

def PrechargeCouts(agc, DBsql):
    # constitue un dictionnaire des modèles de Couts à générer
    lstChamps = CHAMPS_TABLES['couts']
    if agc:
        req = """SELECT mCoûts.IDMatelier, mCoûts.IDMcoût, mCoûts.UnitéQté, mCoûts.CptCoût, mCoûts.MotsCles, mCoûts.TypesCoût
                FROM mCoûts LEFT JOIN mAteliers ON mCoûts.IDMatelier = mAteliers.IDMatelier
                WHERE (((mAteliers.IDagc) In ('ANY','%s'))) OR (((mAteliers.IDagc) Is Null));
                """ %agc
    else:
        req = """SELECT mCoûts.IDMatelier, mCoûts.IDMcoût, mCoûts.UnitéQté, mCoûts.CptCoût, mCoûts.MotsCles, mCoûts.TypesCoût
                FROM mCoûts LEFT JOIN mAteliers ON mCoûts.IDMatelier = mAteliers.IDMatelier;"""
    retour = DBsql.ExecuterReq(req, mess='accès OpenRef précharge Coûts')
    dic = {}
    if retour == "ok":
        recordset = DBsql.ResultatReq()
        if len(recordset)>0:
            dic = orua.ListsToDic(lstChamps, recordset,1)
        else:
            return {}
    for cout in dic:
        dic[cout]['clesstring'] = GetMotsCles({'x': {'motscles': dic[cout]['motscles']}}, avectuple=False)
        dic[cout]['clestuple'] = GetTuplesCles(dic[cout]['motscles'])
    return dic

def GetMotsCles(dic, avectuple = True):
    # le dictionnaire contient la clé d'une liste de string ou str(tuples) dont on recherche seulement le premier mot
    lstMots = []
    for key in dic.keys():
        mots = dic[key]['motscles']
        #pour les binaires passés string
        if mots[:2] == "b'" : mots = mots[2:-1]
        mots = mots.replace(';',',')
        mots = mots.replace('[','(')
        mots = mots.replace(']',')')
        mots = mots.lower()
        mots = ''.join(c for c in unicodedata.normalize('NFD', mots) if unicodedata.category(c) != 'Mn')
        lmots = mots.split(',')
        tuple = False
        for mot in lmots:
            if tuple and not (')' in mot): continue
            elif tuple and (')' in mot):
                tuple = False
                continue
            elif (not tuple) and (')' in mot): wx.MessageBox("Impossible d'isoler les mots clés dans l'item '%s'"%dic[key])
            else:
                if '(' in mot:
                    # il s'agit du premier mot du tuple
                    mot = mot.replace('(','')
                    if not mot.strip() in lstMots:
                        if avectuple:
                            if len(mot.strip()) > 0:
                                lstMots.append(mot.strip())
                    tuple = True
                else:
                    if not mot.strip() in lstMots:
                        if len(mot.strip()) > 0:
                            lstMots.append(mot.strip())
    lstMots.sort(key=len,reverse=True)
    return lstMots

def GetTuplesCles(mots):
    # le texte est une liste de string ou psudos tuples. On recherche seulement les tuples
    lstTuples = []
    mots = mots.replace(';',',')
    mots = mots.replace('[','(')
    mots = mots.replace(']',')')
    mots = mots.lower()
    mots = ''.join(c for c in unicodedata.normalize('NFD', mots) if unicodedata.category(c) != 'Mn')
    lmots = mots.split(',')
    tuple = False
    tup = ()
    for mot in lmots:
        if tuple and not (')' in mot):
            tup += (mot.strip(),)
        elif tuple and (')' in mot):
            mot = mot.replace(')','')
            tup += (mot.strip(),)
            lstTuples.append(tup)
            tup = ()
            tuple=False
        elif (not tuple) and (')' in mot): wx.MessageBox("Impossible d'isoler les mots clés dans le texte '%s'"%mots)
        else:
            if '(' in mot:
                mot = mot.replace('(','')
                tup += (mot.strip(),)
                tuple = True
            else: continue
    lstTuples.sort(key=lambda v: len(v[0]), reverse=True)
    return lstTuples

def GetProduitsAny(dicProduits):
    # extrait les produits utilisables par toutes les structures agc
    dicProduitsAny = {}
    for produit, dic in dicProduits.items():
        if dic['idmatelier'].upper() == 'ANY':
            dicProduitsAny[produit] = dic
    return dicProduitsAny

class Traitements():
    # pour chaque dossier, le traitement génére des ateliers, produits et couts en affectant les comptes
    def __init__(self,annee=None, client=None, groupe=None, filiere=None, agc=None):
        self.title = '[UTIL_traitements].Traitements'
        self.mess = ''
        # recherche pour affichage bas d'écran
        self.topwin = False
        self.topWindow = wx.GetApp().GetTopWindow()
        if self.topWindow:
            self.topwin = True

        # pointeur de la base principale ( ouverture par défaut de db_prim via xGestionDB)
        self.DBsql = xdb.DB()

        self.dic_Ateliers = {}
        #préchargement de la table des Produits et des coûts
        self.dicProduits, self.lstPrioritesProduits = PrechargeProduits(agc,self.DBsql)


        self.dicCouts = PrechargeCouts(agc,self.DBsql)
        self.dicPlanComp = PrechargePlanCompte(self.DBsql)
        self.lstMotsClesProduits = GetMotsCles(self.dicProduits, avectuple=True)
        self.lstMotsClesCouts = GetMotsCles(self.dicCouts, avectuple=True)
        # détermination des clients à traiter
        if client:
            lstDossiers = orua.GetExercicesClient(agc,client,annee,0,self.DBsql,saufvalide=True)
        elif groupe:
            lstDossiers=orua.GetClientsGroupes(agc, groupe, annee, 0, self.DBsql,saufvalide=True)
        elif filiere:
            lstDossiers = orua.GetClientsFilieres(agc, filiere, annee, 0, self.DBsql,saufvalide=True)
        else :
            wx.MessageBox("Analyse : Aucun paramètre de lancement ne concerne un dossier")
            return

        # déroulé du traitement
        messBasEcran = 'Client : '
        nbreOK = 0
        for tplIdent in lstDossiers:
            messBasEcran += "%s "%tplIdent[1]
            if self.topwin:
                self.topWindow.SetStatusText(messBasEcran)
            self.mess = ''
            retour = self.TraiteClient(tplIdent)
            if retour == 'ok':
                    nbreOK += 1
            if self.topwin:
                messBasEcran += retour + ', '
                messBasEcran = messBasEcran[-230:]
                self.topWindow.SetStatusText(messBasEcran)
            self.DBsql.Close()
            self.DBsql = xdb.DB()
        wx.MessageBox("%d dossiers traités"%nbreOK)

    def GetMotsCleDossier(self,tplIdent):
        # récupère les mots clés des comptes de vente, de la production et des filières
        req = """SELECT _Ident.IDdossier, _Ident.Filières, _Ident.Productions, _Balances.MotsCléPrés
            FROM _Ident INNER JOIN _Balances ON _Ident.IDdossier = _Balances.IDdossier
            WHERE (_Balances.Compte Like '70%%') 
                AND (_Ident.IDagc = '%s') 
                AND (_Ident.IDexploitation = '%s') 
                AND (_Ident.Clôture = '%s');
            """ % tplIdent
        retour = self.DBsql.ExecuterReq(req, mess='accès OpenRef GetVentes')

        IDdossier = None
        lstVentes = []
        lstFilieres =[]
        lstProduction = []
        if retour == "ok":
            recordset = self.DBsql.ResultatReq()
            if len(recordset) > 0:
                for dossier, filieres,prod,libelle in recordset:
                    if not IDdossier:
                        IDdossier = dossier
                        lstFilieres = Decoupe(filieres)
                        lstProduction = Decoupe(prod)
                    lstVentes.extend(Decoupe(libelle))
        #compactage des répétitions
        def Compacte(oldliste):
            newliste=[]
            for item in oldliste:
                if not item in newliste:
                    newliste.append(item)
            return newliste
        return IDdossier,Compacte(lstVentes),Compacte(lstFilieres),Compacte(lstProduction)

    def GetAtelierValide(self,IDdossier,table,cle,dossiervalide):
        # Validé : récupère l'atelier de l'affectation pour savoir s'il est validé ou si on peut purger
        if table == '_Produits':
            req = """SELECT _Ateliers.IDMatelier, _Ateliers.Validation
                FROM _Produits 
                    INNER JOIN _Ateliers ON (_Produits.IDMatelier = _Ateliers.IDMatelier) 
                                            AND (_Produits.IDdossier = _Ateliers.IDdossier)
                WHERE ((_Produits.IDMproduit='%s') 
                        AND (_Produits.IDdossier=%d))
                GROUP BY _Ateliers.Validation;
                    """ %(cle,IDdossier)
        elif table == '_Coûts':
            req = """SELECT _Ateliers.IDMatelier, _Ateliers.Validation
                FROM _Coûts 
                    INNER JOIN _Ateliers ON (_Coûts.IDMatelier = _Ateliers.IDMatelier) 
                                            AND (_Coûts.IDdossier = _Ateliers.IDdossier)
                WHERE ((_Coûts.IDMcoût='%s') 
                        AND (_Coûts.IDdossier=%d))
                GROUP BY _Ateliers.Validation;
                    """ % (cle, IDdossier)
        elif table == '_Ateliers':
            req = """SELECT _Ateliers.IDMatelier, _Ateliers.Validation
                FROM _Ateliers 
                WHERE (_Ateliers.IDdossier=%d))
                GROUP BY _Ateliers.Validation;
                    """ %(cle,IDdossier)
        else: req = None

        ateliervalide = None
        if req:
            retour = self.DBsql.ExecuterReq(req, mess='accès OpenRef.UTIL_traitements.PurgeNonValide %s'%table)
            if retour == 'ok':
                recordset = self.DBsql.ResultatReq()
                for atelier,valide in recordset:
                    if (valide == 1) or (dossiervalide == 1):
                        ateliervalide = atelier
        return ateliervalide

    def GetValide(self,IDdossier):
        # récupère les ateliers produits et coûts validés qui ne devront pas être écrasés
        lstAteliersValid = []
        lstProduitsValid = []
        lstCoutsValid = []
        req = """SELECT _Ateliers.IDMatelier, _Produits.IDMproduit, _Coûts.IDMcoût
            FROM (((((_Ident 
                        INNER JOIN _Ateliers ON _Ident.IDdossier = _Ateliers.IDdossier) 
                       INNER JOIN mAteliers ON _Ateliers.IDMatelier = mAteliers.IDMatelier) 
                      INNER JOIN mProduits ON mAteliers.IDMatelier = mProduits.IDMatelier) 
                     INNER JOIN mCoûts ON mAteliers.IDMatelier = mCoûts.IDMatelier) 
                INNER JOIN _Produits ON (_Ateliers.IDdossier = _Produits.IDdossier) 
                                    AND (mProduits.IDMatelier = _Produits.IDMatelier) 
                                    AND (mProduits.IDMproduit = _Produits.IDMproduit)) 
                INNER JOIN _Coûts ON (_Ateliers.IDdossier = _Coûts.IDdossier) 
                                AND (mCoûts.IDMcoût = _Coûts.IDMcoût) 
                                AND (mCoûts.IDMatelier = _Coûts.IDMatelier)                
            WHERE ((_Ident.Validé=1) OR (_Ateliers.Validation=1))
                    AND _Ident.IDdossier = %d
            GROUP BY _Ateliers.IDMatelier, _Produits.IDMproduit, _Coûts.IDMcoût;
                ;""" %(IDdossier)
        retour = self.DBsql.ExecuterReq(req, mess='accès OpenRef.UTIL_traitements.GetValide')
        if retour == 'ok':
            for IDMatelier,IDMproduit, IDMcout in self.DBsql.ResultatReq():
                if IDMatelier not in lstAteliersValid : lstAteliersValid.append(IDMatelier)
                if IDMproduit not in lstProduitsValid: lstProduitsValid.append(IDMproduit)
                if IDMcout not in lstCoutsValid: lstCoutsValid.append(IDMcout)
        return lstAteliersValid, lstProduitsValid,lstCoutsValid

    def PurgeNonValide(self,IDdossier):
        # récupère les affectations précédentes dans _Balances, pour les purger
        req = """SELECT _Balances.Affectation, _Ident.Validé
                FROM _Balances INNER JOIN _Ident ON _Balances.IDdossier = _Ident.IDdossier
                WHERE _Balances.IDdossier=%d
                GROUP BY _Balances.Affectation, _Ident.Validé;
                """ %(IDdossier)
        retour = self.DBsql.ExecuterReq(req, mess='accès OpenRef.UTIL_traitements.PurgeNonValide1')
        if retour == 'ok':
            recordset = self.DBsql.ResultatReq()
            lstAffectations = []
            dossiervalide = 0
            for Affectation, DossierValide in recordset:
                lstAffectations.append(Affectation)
                dossiervalide = DossierValide

            lstAteliers = []
            lstProduits = []
            lstCouts = []
            # détermine quelles affectations il faut garder avec listes par type d'affectation, purge des balances
            for Affectation  in lstAffectations:
                ateliervalide = None
                #vérifie la structure, cherche ce qui a été validé
                if Affectation[1:2]== '_':
                    #constitue les listes à vérifier, une affectation pointe l'une des trois tables
                    if Affectation[:1] == "P" :
                        ateliervalide = self.GetAtelierValide(IDdossier, '_Produits', Affectation[2:], dossiervalide)
                        if ateliervalide:
                            lstProduits.append(Affectation[2:])
                    elif Affectation[:1] == "C" :
                        ateliervalide = self.GetAtelierValide(IDdossier, '_Coûts', Affectation[2:], dossiervalide)
                        if ateliervalide:
                            lstCouts.append(Affectation[2:])
                    elif Affectation[:1] == "A" :
                        ateliervalide = self.GetAtelierValide(IDdossier, '_Ateliers', Affectation[2:], dossiervalide)

                # Efface l'affectation dans _Balances
                if not ateliervalide:
                    condition = "IDdossier = %d AND Affectation = '%s'" % (IDdossier, Affectation)
                    self.DBsql.ReqMAJ('_Balances', (('Affectation', ''),), condition,
                                      mess="PurgeDuNonValidé dossier %d, cout %s" % (IDdossier, Affectation))
                else:
                    # l'atelier qui a déterminé la validation devra être conservé
                    lstAteliers.append(Affectation[2:])

            # purge des autres tables que _Balance
            if len(lstProduits)>0:
                condition = "IDdossier = %d AND IDMproduit not in (%s)"%(IDdossier,str(lstProduits[1:-1]))
            else: condition = "IDdossier = %d"%IDdossier
            self.DBsql.ReqDEL('_Produits',condition,mess="PurgeDuNonValidé dossier %d"%(IDdossier))

            if len(lstCouts)>0:
                condition = "IDdossier = %d AND IDMcoût not in (%s)"%(IDdossier,str(lstCouts[1:-1]))
            else: condition = "IDdossier = %d"%IDdossier
            self.DBsql.ReqDEL('_Coûts',condition,mess="PurgeDuNonValidé dossier %d"%(IDdossier))

            if len(lstAteliers)>0:
                condition = "IDdossier = %d AND IDMatelier not in (%s)"%(IDdossier,str(lstAteliers[1:-1]))
            else: condition = "IDdossier = %d"%IDdossier
            self.DBsql.ReqDEL('_Ateliers',condition,mess="PurgeDuNonValidé dossier %d"%(IDdossier))
        return

    def GetBalance(self,IDdossier):
        # récupère la balance du comptes de résultat et des stocks
        balance = []
        self.champsBalance = str(CHAMPS_TABLES['_Balances'])[1:-1]
        self.champsBalance = self.champsBalance.replace("'","")
        req = """SELECT %s
            FROM _Balances
            WHERE ((Compte Like '7%%') 
                        OR (Compte Like '6%%')
                        OR (Compte Like '3%%'))
                AND (IDdossier = %s)
                AND (Affectation in ('',' '));
            """ %(self.champsBalance,IDdossier)
        retour = self.DBsql.ExecuterReq(req, mess='accès OpenRef GetBalance')
        if retour == 'ok':
            balance = self.DBsql.ResultatReq()
        return balance

    def Init_dic_produit(self,produit):
        #prépare un dictionnaire vide pour les champs nombre réels
        dic = {'IDMproduit':produit}
        for champ in dtt.GetChamps('_Produits',reel=True):
            dic[champ] = 0.0
        dic['IDMatelier'] = self.dicProduits[produit]['idmatelier']
        dic['UnitéQté1'] = self.dicProduits[produit]['unitéqté1']
        dic['UnitéQté2'] = self.dicProduits[produit]['unitéqté2']
        dic['Comptes'] = []
        dic['AutreProduit'] = 0.0
        dic['CalculAutreProduit'] = []
        dic['Subventions'] = 0.0
        dic['CalculSubvention'] = []
        dic['AutreProd'] = 0.0
        dic['ProdPrincipal'] = 1
        dic['TypesProduit'] = ''
        dic['Production'] = 0.0
        return dic

    def Init_dic_atelier(self,atelier,IDdossier):
        #prépare un dictionnaire vide pour les champs nombre réels et texte provisoirement en liste
        dic = {'IDMatelier':atelier}
        for champ in dtt.GetChamps('_Ateliers',reel=True):
            dic[champ] = 0.0
        for champ in dtt.GetChamps('_Ateliers',texte=True):
            dic[champ] = []
        dic['IDMatelier'] = atelier
        dic['IDdossier'] = IDdossier
        return dic

    def AffecteAtelier(self, IDdossier,atelier,lstComptesRetenus):
        # Balaye la balance  pour affecter à l'atelier tout les comptes non affectés aux produits
        # on récupère les comptes ds balance, on les traite sur le IDplanCompte
        compteencours = ''
        for IDdossier, Compte, IDligne, Libelle, MotsClePres,Quantites1, Unite1, Quantites2, Unite2, SoldeDeb, DBmvt, \
            CRmvt, SoldeFin, IDplanCompte, Affectation in self.balanceCeg:
            if Compte in lstComptesRetenus and Compte != compteencours: continue
            if not IDplanCompte : 
                IDplanCompte = ChercheIDplanCompte(Compte,self.dicPlanComp)
            if  not (IDplanCompte in self.dicPlanComp) : 
                IDplanCompte = ChercheIDplanCompte(Compte,self.dicPlanComp)
            if len(IDplanCompte.strip())==0: continue
            ok = False            


            # ce compte sera affecté à l'atelier
            post = 'cout'
            # si plusieurs lignes successives d'un même compte (quand plusieurs unités de qté) => compteencours cumule
            compteencours = Compte
            lstComptesRetenus.append(Compte)

            def AppendCompte(lstComptes,compte):
                if not compte in lstComptes:
                    lstComptes.append(compte)
                return
            # inversion des signes de balance pour retrouver du positif dans les produits ou stock
            if IDplanCompte[:2] == '74':
                # subventions seront affectées à l'atelier
                self.dic_Ateliers[atelier]['Subventions'] += SoldeFin
                AppendCompte(self.dic_Ateliers[atelier]['CPTSubventions'],Compte)
                post='Subventions'
            elif IDplanCompte[:2] in ('70','71','75','33','34','35','36','37'):
                self.dic_Ateliers[atelier]['AutreProduit'] += SoldeFin
                AppendCompte(self.dic_Ateliers[atelier]['CPTAutreProduit'],Compte)
                post='AutreProduit'
            elif IDplanCompte[:3] in ('307','604'):
                self.dic_Ateliers[atelier]['AutreProduit'] += SoldeFin
                AppendCompte(self.dic_Ateliers[atelier]['CPTAutreProduit'],Compte)
                post = 'AutreProduit'

            #TODO inserer les comptes de charges selon type


            # MAJ _Balances
            affectation = 'A.' + atelier + "." + post
            lstCouples = [('IDplanCompte', IDplanCompte), ('Affectation', affectation)]
            condition = "IDligne = %d" % IDligne
            self.DBsql.ReqMAJ('_Balances', couples=lstCouples, condition=condition, mess= "GeneredicAtelier MAJ _Balances")

        return

    def GenereDicProduit(self, IDdossier, produit, lstMots, lstComptesRetenus, dicProduit=None):
        # Balaye la balance  pour affecter à ce produit, création ou MAJ de dicProduit, et MAJ de self.balanceCeg
        if not dicProduit:
            dicProduit = self.Init_dic_produit(produit)
            dicProduit['IDdossier'] = IDdossier
        lstRadicaux = self.dicProduits[produit]['cptproduit'].split(',')
        compteencours = ''
        atelier = dicProduit['IDMatelier']
        if(not atelier in self.dic_Ateliers) and atelier != 'ANY':
            dicAtelier = self.Init_dic_atelier(atelier,dicProduit['IDdossier'])
            self.dic_Ateliers[atelier] = dicAtelier
        if self.dicProduits[produit]['typesproduit']:
            for tip in self.dicProduits[produit]['typesproduit'].split(','):
                if not tip.lower() in dicProduit['TypesProduit'].lower():
                    dicProduit['TypesProduit'] += (tip + ',')
        # on récupère les comptes ds balance, on les traite sur le IDplanCompte
        for IDdossier, Compte, IDligne, Libelle, MotsClePres,Quantites1, Unite1, Quantites2, Unite2, SoldeDeb, DBmvt, \
            CRmvt, SoldeFin, IDplanCompte, Affectation in self.balanceCeg:
            if not IDplanCompte : 
                IDplanCompte = ChercheIDplanCompte(Compte,self.dicPlanComp)
            if  not (IDplanCompte in self.dicPlanComp) : 
                IDplanCompte = ChercheIDplanCompte(Compte,self.dicPlanComp)
            if len(IDplanCompte.strip())==0: continue
            # test sur liste de mot, on garde ceux qui contiennent un mot clé du produit
            ok = False
            if lstMots:
                # teste la présence du mot clé dans le compte
                for mot in lstMots:
                    if mot in MotsClePres.lower():
                        ok = True
                        #un mot présent suffit pour matcher
                        break
            if not ok: continue
            # ce compte a matché il sera affecté au produit
            affectation = ''
            if Compte in lstComptesRetenus and Compte != compteencours:
                # le compte à déjà été affecté par un autre produit et ce n'est pas une deuxième ligne d'un même compte
                continue
            # si plusieurs lignes successives d'un même compte (quand plusieurs unités de qté) => compteencours cumule
            compteencours = Compte
            # teste si le compte rentre dans les radicaux possibles pour le modèle de produit
            for radical in lstRadicaux :
                if radical == IDplanCompte[:len(radical)]:
                    # le compte rentre dans le produit : calcul du produit
                    if IDplanCompte[:2] == '74':
                        # les subventions et ProdFin seront affectés à l'atelier même avec mot clé de genre produit
                        lstComptesRetenus.append(IDplanCompte)
                        self.dic_Ateliers[atelier]['Subventions'] += SoldeFin
                        self.dic_Ateliers[atelier]['CPTSubventions'].append(Compte)
                        affectation = 'A.' + atelier + "." + 'Subventions'
                    elif IDplanCompte[:2] == '76':
                        self.dic_Ateliers[atelier]['AutreProduit'] += SoldeFin
                        self.dic_Ateliers[atelier]['CPTAutreProduit'].append(Compte)
                        affectation = 'A.' + atelier + "." + 'AutreProduit'

                    dicProduit = VentileValeurProduit(dicProduit,radical,Quantites1,Quantites2,SoldeDeb,SoldeFin)
                    production = 0.0
                    for poste in ('Ventes', 'DeltaStock', 'AchatAnmx', 'AutreProd'):
                        production += dicProduit[poste]
                    dicProduit['Production'] = production
                    # MAJ _Balances
                    # enregistrement du compte std et marque d'affectation
                    if affectation == '':
                        affectation = 'P.'+atelier+'.'+produit
                    lstCouples = [('IDplanCompte', IDplanCompte), ('Affectation', affectation)]
                    condition = "IDligne = %d" % IDligne
                    self.DBsql.ReqMAJ('_Balances', couples=lstCouples, condition=condition, mess= "GenereDicProduit MAJ _Balances")
                    break
        return dicProduit

    def TraiteClient(self,tplIdent):
        # traitement effectué sur un dossier  pointé
        #(IDagc, IDexploitation, Cloture) = tplIdent
        self.dic_Ateliers = {}
        #premier accès sur les comptes de vente
        IDdossier, lstVentes,lstFilieres,lstProduction = self.GetMotsCleDossier(tplIdent)
        #les pointeurs d'affectation non validés doivent être mis à blanc
        if not IDdossier:
            return 'Incomplet'
        self.PurgeNonValide(IDdossier)
        self.balanceCeg = self.GetBalance(IDdossier)
        lstAteliersValid, lstProduitsValid,lstCoutsValid = self.GetValide(IDdossier)

        #matche les produits potentiels par les mots clés simples ou première position tuple
        def ChercheProduits():
            lstProduits = []
            #recherches successives dans les listes
            def Matche(mot,lstProduits):
                #comparaison des motcle des produits modèles avec le mot testé venant du dossier
                for motcle in self.lstMotsClesProduits:
                    if motcle in mot :
                        #le mot contient un radical pouvant déterminer un produit, on recherche quel produit
                        for produit in self.lstPrioritesProduits:
                            dic = self.dicProduits[produit]
                            if motcle in dic['clesstring']:
                                if not (produit,motcle) in lstProduits:
                                    lstProduits.append((produit,motcle))
                                continue
                            for tup in dic['clestuple']:
                                if motcle == tup[0]:
                                    if not (produit,tup) in lstProduits:
                                        lstProduits.append((produit,tup))
            # d'abord sur les libelles des comptes de vente
            for mot in lstVentes:
                Matche(mot,lstProduits)
            if lstProduits == []:
                #puis recherche dans les productions
                for mot in lstProduction:
                    Matche(mot,lstProduits)
            if lstProduits == []:
                #puis recherche dans les filières
                for mot in lstFilieres:
                    Matche(mot,lstProduits)
            return lstProduits
        lstProduits = ChercheProduits()
        lstMotsDossier = lstVentes + lstProduction +lstFilieres
        # on vérifie les conditions de traitement pour les produits potentiels trouvés
        ix = -1
        lstDel =[]
        # élimination des produits ne vérifiant pas les conditions cumulatives
        for produit, trouve in lstProduits:
            #on vérifie si le produit n'est pas déjà validé (les non validés ont été purgés)
            ix +=1
            if produit in lstProduitsValid :
                del lstProduits[ix]
                ix -= 1
                continue
            #les mots isolés s'imposent
            if isinstance(trouve, str):
                continue
            #les tuples sont des conditions cumulatives
            if isinstance(trouve, tuple):
                ok = True
                for mot in trouve[1:]:
                    present = (mot in lstMotsDossier)
                    if mot[:1] == '!' : present = not present
                    if not present : ok = False
            if not ok :
                lstDel.append(ix)
                ix -= 1
        # abandon des produits ne correspondant pas aux conditions
        for ix in lstDel:
            del lstProduits[ix]
        #chaque produit retenu est calculé, on associe IDplanCompte et on marque le compte affecté
        lstComptesRetenus = []
        lstDicProduits = []
        lstIxDicProduits = []

        # Un premier passage pour n'affecter que les comptes ayant le mot clé dans le libellé
        for produit, trouve in lstProduits:
            dicProduit = self.GenereDicProduit(IDdossier,produit,self.dicProduits[produit]['lstmots'],lstComptesRetenus)
            lstDicProduits.append(dicProduit)

        produitLeader = ''
        atelierLeader = ''
        production = 0.0
        # on détermine le produitLeader par le plus gros CA
        for dicProduit in lstDicProduits:
            # Création d'un index pour pointer les dicProduits
            lstIxDicProduits.append(dicProduit['IDMproduit'])
            if (dicProduit['Production'] > production) and (dicProduit['IDMatelier'] != 'ANY'):
                production = dicProduit['Production']
                produitLeader = dicProduit['IDMproduit']
                atelierLeader = dicProduit['IDMatelier']

        # il y a des produit calculés
        if produitLeader != '':
            #le plus gros produit , récupère des comptes sans mot clé dans le libellé
            dicProduitLeader = lstDicProduits[lstIxDicProduits.index(produitLeader)]
            # on récupère les comptes ds balance qui restent
            lstDicProduits[lstIxDicProduits.index(produitLeader)] = self.GenereDicProduit(IDdossier,produitLeader,None,
                                                                                          lstComptesRetenus,dicProduitLeader)

            #Les produits de l'atelier ANY peuvent être rattachés à l'atelier du produit
            dicProduitsAny = GetProduitsAny(self.dicProduits)
            for produit, dic in dicProduitsAny.items():
                dicProduit = self.GenereDicProduit(IDdossier,produit,None,lstComptesRetenus)
                dicProduit['IDMatelier'] = dicProduitLeader['IDMatelier']
                lstDicProduits.append(dicProduit)
                lstIxDicProduits.append(produit)

        # s'il reste des comptes non affectés on teste si les produits non leader peuvent contenir ces no de compte
        for dicProduit in lstDicProduits:
            produit =  dicProduit['IDMproduit']
            if (produit != produitLeader) and (len(produitLeader)>0):
                lstDicProduits[lstIxDicProduits.index(produit)] = self.GenereDicProduit(IDdossier,produit,None,lstComptesRetenus,dicProduit)

        # s'il reste des comptes non affectés on les rattache à l'atelier principal
        if atelierLeader != '':
            self.AffecteAtelier(IDdossier, atelierLeader, lstComptesRetenus)
        ok = 'ok'
        # stockage de l'info dans  _Produits et _Atelier
        lstAteliersCrees = []
        for dicProduit in lstDicProduits:
            if dicProduit['Production'] == 0.0 : continue
            atelier = dicProduit['IDMatelier']
            if atelier in lstAteliersValid: continue
            if not atelier in lstAteliersCrees:
                dicAtelier = self.dic_Ateliers[atelier]
                ret = self.Set_Atelier(dicAtelier,self.DBsql)
                if ret != 'ok': ok = ret
                lstAteliersCrees.append(atelier)
            ret = Set_Produit(dicProduit,self.DBsql)
            if ret != 'ok': ok += '; '+ret
        return ok

#************************   Pour Test ou modèle  *********************************
if __name__ == '__main__':
    app = wx.App(0)
    fn = Traitements(annee='2018',client='041058',agc='ANY')
    #fn = Traitements(annee='2018',groupe='LOT1',agc='prov')
    print('Retour: ',fn)

    app.MainLoop()

