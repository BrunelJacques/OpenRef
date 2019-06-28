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
import xpy.xGestionDB as xdb
import unicodedata
import srcOpenRef.DATA_Tables as dtt

CHAMPS_TABLES = {
    '_Balances':['IDdossier','Compte','IDligne','Libellé','Quantités1','Unité1','Quantités2','Unité2',
                 'SoldeDeb','DBmvt','CRmvt','SoldeFin','IDplanCompte','Affectation'],
    'produits':[ 'IDMatelier', 'IDMproduit', 'NomProduit', 'MoisRécolte', 'ProdPrincipal', 'UniteSAU', 'coefHa', 'CptProduit', 'MotsCles', 'TypesProduit'],
    'couts': ['IDMatelier','IDMcoût','UnitéQté','CptCoût','MotsCles','TypesCoût']
    }

def PrechargePlanCompte(DBsql):
    # constitue un dictionnaire des modèles de produits à générer
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
        req = """SELECT mProduits.IDMatelier, mProduits.IDMproduit, mProduits.NomProduit, mProduits.MoisRécolte, mProduits.ProdPrincipal, mProduits.UniteSAU, mProduits.coefHa, mProduits.CptProduit, mProduits.MotsCles, mProduits.TypesProduit
            FROM mProduits LEFT JOIN mAteliers ON mProduits.IDMatelier = mAteliers.IDMatelier
            WHERE (((mAteliers.IDagc) In ('ANY','%s'))) OR (((mAteliers.IDagc) Is Null));
            """ %agc
    else:
        req = """SELECT mProduits.IDMatelier, mProduits.IDMproduit, mProduits.NomProduit, mProduits.MoisRécolte, mProduits.ProdPrincipal, mProduits.UniteSAU, mProduits.coefHa, mProduits.CptProduit, mProduits.MotsCles, mProduits.TypesProduit
                FROM mProduits LEFT JOIN mAteliers ON mProduits.IDMatelier = mAteliers.IDMatelier;"""
    retour = DBsql.ExecuterReq(req, mess='accès OpenRef précharge Produits')
    dic = {}
    if retour == "ok":
        recordset = DBsql.ResultatReq()
        if len(recordset)>0:
            dic = orua.ListsToDic(lstChamps, recordset,1)
        else:
            wx.MessageBox("Aucun modèle produit disponible, le traitement n'est pas lancé!")
            return {}
        for produit in dic:
            dic[produit]['clesstring']=GetMotsCles({'x':{'motscles':dic[produit]['motscles']}},avectuple=False)
            dic[produit]['clestuple'] = GetTuplesCles(dic[produit]['motscles'])
    return dic

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
                            lstMots.append(mot.strip())
                    tuple = True
                else:
                    if not mot.strip() in lstMots:
                        lstMots.append(mot.strip())
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
    return lstTuples

def GetProduitsAny(dicProduits):
    dicProduitsAny = {}
    for produit, dic in dicProduits.items():
        if dic['idmatelier'].upper() == 'ANY':
            dicProduitsAny[produit] = dic
    return dicProduitsAny

class Traitements():
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

        #préchargement de la table des Produits et des coûts
        self.dicProduits = PrechargeProduits(agc,self.DBsql)
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
        messBasEcran = ''
        nbreOK = 0
        for tplIdent in lstDossiers:
            messBasEcran += "%s "%tplIdent[1]
            retour = 'ko'
            self.mess = ''
            retour = self.TraiteClient(tplIdent)
            if retour == 'ok':
                    nbreOK += 1
            if self.topwin and len(self.mess) > 0:
                messBasEcran += retour + ', '
                messBasEcran = messBasEcran[-230:]
                self.topWindow.SetStatusText(messBasEcran)
            del retour
        wx.MessageBox("%d dossiers traités"%nbreOK)

    def GetMotsVentes(self,tplIdent):
        # récupère les mots clés des comptes de vente, de la production et des filières
        req = """SELECT _Ident.IDdossier, _Ident.Filières, _Ident.AnalyseProduction, _Balances.Libellé
            FROM _Ident INNER JOIN _Balances ON _Ident.IDdossier = _Balances.IDdossier
            WHERE (_Balances.Compte Like '70%%') 
                AND (_Ident.IDagc = '%s') 
                AND (_Ident.IDexploitation = '%s') 
                AND (_Ident.Clôture = '%s');
            """ % tplIdent
        retour = self.DBsql.ExecuterReq(req, mess='accès OpenRef GetVentes')

        def Decoupe(texte):
            # isole les mots du texte afin de les comparer aux mots clés
            lstMots = []
            texte = str(texte)
            lstCar = [',','#','__','%',';','-','\\n']
            for lettre in lstCar:
                texte = texte.replace(lettre, ' ')
            #suppression des accents et forcé en minuscule
            texte = ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')
            texte = texte.lower()
            ltxt = texte.split(' ')
            for mot in ltxt:
                mot = mot.strip()
                if len(mot)>2:
                    if mot not in lstMots:
                        lstMots.append(mot)
            return lstMots

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
        return IDdossier,lstVentes,lstFilieres,lstProduction

    def GetAtelierValide(self,IDdossier,table,cle,dossiervalide):
        # rédupère l'atelier de l'affectation pour savoir s'il est validé ou si on peut purger
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
        lstCoûtsValid = []
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
            for IDMatelier,IDMproduit, IDMcoût in self.DBsql.ResultatReq():
                if IDMatelier not in lstAteliersValid : lstAteliersValid.append(IDMatelier)
                if IDMproduit not in lstProduitsValid: lstProduitsValid.append(IDMproduit)
                if IDMcoût not in lstCoûtsValid: lstCoûtsValid.append(IDMcoût)
        return lstAteliersValid, lstProduitsValid,lstProduitsValid

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

    def GenereDicProduit(self, produit, lstMots, lstComptesRetenus, dicProduit=None):
        # affectation des comptes de la balance à un produit, création ou MAJ de dicProduit, et MAJ de self.Balance
        if not dicProduit:
            dicProduit = self.Init_dic_produit(produit)
        lstRadicaux = self.dicProduits[produit]['cptproduit'].split(',')
        compteencours = ''
        atelier = dicProduit['IDMatelier']
        # on récupère les comptes ds balance, on les traite ou pas
        for IDdossier, Compte, IDligne, Libelle, Quantites1, Unite1, Quantites2, Unite2, SoldeDeb, DBmvt, \
            CRmvt, SoldeFin, IDplanCompte, Affectation in self.balance:
            #'AutreProduit sera au niveau de l'atelier, alors que AutrProd est au niveau du produit
            autreProd = 'AutreProduit'
            affectationAtelier = 'A_' + atelier
            affectationProduit = 'P_' + produit
            #if Compte == '70361020': (pour débug)
            # test sur liste de mot, on garde ceux qui contiennent un mot clé du produit
            if lstMots:
                # teste la présence du mot clé dans le compte
                ok = False
                for mot in lstMots:
                    if mot in Libelle.lower():
                        ok = True
                        break
                if not ok: continue
                else:
                    autreProd = 'AutreProd'
                    affectationAtelier = 'P_' + produit
            if Compte in lstComptesRetenus and Compte != compteencours: continue
            # si plusieurs lignes successives d'un même compte (quand plusieurs unités de qté) => compteencours cumule
            compteencours = Compte
            # teste si le compte rentre dans les radicaux possibles pour le modèle de produit
            for radical in lstRadicaux:
                if radical == Compte[:len(radical)]:
                    # le compte rentre dans le produit : calcul du produit
                    lstComptesRetenus.append(Compte)
                    dicProduit['Comptes'].append(Compte)
                    if self.dicProduits[produit]['typesproduit']:
                        dicProduit['TypesProduit'] += (self.dicProduits[produit]['typesproduit'] + ',')
                    dicProduit['Quantité1'] += Quantites1
                    dicProduit['Quantité2'] += Quantites2
                    # inversion des signes de balance pour retrouver du positif dans les produits ou stock
                    if Compte[:2] == '70':
                        dicProduit['Ventes'] -= SoldeFin
                    elif Compte[:2] == '71':
                        dicProduit['DeltaStock'] -= SoldeFin
                    elif Compte[:2] == '72':
                        dicProduit[autreProd] -= SoldeFin
                        dicProduit[autreProd+"CPT"].append(Compte)
                    elif Compte[:2] == '74':
                        dicProduit['Subventions'] -= SoldeFin
                        dicProduit['CalculSubvention'].append(Compte)
                    elif Compte[:2] == '75':
                        dicProduit[autreProd] -= SoldeFin
                        dicProduit[autreProd+"CPT"].append(Compte)
                    elif Compte[:2] == '76':
                        dicProduit[autreProd] -= SoldeFin
                        dicProduit[autreProd+"CPT"].append(Compte)
                    elif Compte[:3] == '603':
                        dicProduit['DeltaStock'] -= SoldeFin
                    elif Compte[:3] == '604':
                        dicProduit['AchatAnmx'] -= SoldeFin
                    # le paramétrage ne doit pas contenir à la fois des ((603 ou 71) et 3) dans les radicaux
                    elif Compte[:1] == '3':
                        dicProduit['DeltaStock'] -= SoldeFin - SoldeDeb
                        dicProduit['StockFin'] -= SoldeFin
                    else:
                        dicProduit['AutreProd'] -= SoldeFin
                    production = 0.0
                    for poste in ('Ventes', 'DeltaStock', 'AchatAnmx', 'AutreProd'):
                        production += dicProduit[poste]
                    dicProduit['Production'] = production
                    # MAJ _Balances, recherche dans le plan comptable standard pour enrichir les types de produit
                    for cptstd in self.dicPlanComp.keys():
                        if not cptstd == Compte[:len(cptstd)]:
                            continue
                        else:
                            for mot in self.dicPlanComp[cptstd]['type'].split(','):
                                if not (mot in dicProduit['TypesProduit']):
                                    dicProduit['TypesProduit'] += mot + ','
                            # enregistrement du compte std et marque d'affectation
                            if cptstd[:2] in ('72','74','75','76'):
                                affectation = affectationAtelier
                            else:
                                affectation = affectationProduit
                            lstCouples = [('IDplanCompte', cptstd), ('Affectation', affectation)]
                            condition = "IDligne = %d" % IDligne
                            self.DBsql.ReqMAJ('_Balances', couples=lstCouples, condition=condition, mess= "GenereDicProduit MAJ _Balances")
        return dicProduit

    def Genere_Atelier(self,dicProduit):
        # création ou MAJ d'un atelier par son produit et les modèles
        IDMatelier = dicProduit['IDMatelier']
        lstChamps = ['IDdossier','IDMatelier','AutreProduit','CalculAutreProduit','Subventions','CalculSubvention']
        lstDonnees=[]
        lstChampsTable = dtt.GetChamps('_Ateliers')
        for champ in lstChamps:
            if champ in lstChampsTable:
                lstDonnees.append(dicProduit[champ])
        self.DBsql.ReqInsert('_Ateliers',lstChamps,lstDonnees,mess= 'Genere_Atelier Atelier : %s'%IDMatelier)
        return 'ok'

    def Genere_Produit(self, dicProduit):
        # création ou MAJ d'un produits par son produit et les modèles
        IDMproduit = dicProduit['IDMproduit']
        lstChampsTable = dtt.GetChamps('_Produits')
        lstChamps = []
        lstDonnees = []
        for champ in dicProduit.keys():
            if champ in lstChampsTable:
                lstChamps.append(champ)
                lstDonnees.append(dicProduit[champ])
        self.DBsql.ReqInsert('_Produits', lstChamps, lstDonnees, mess='GenereProduits Produit : %s' % IDMproduit)
        return 'ok'

    def TraiteClient(self,tplIdent):
        # traitement effectué sur un dossier  pointé
        (IDagc, IDexploitation, Cloture) = tplIdent
        dic_Produits={}
        dic_Ateliers={}
        dic_Couts={}

        #premier accès sur les comptes de vente
        IDdossier, lstVentes,lstFilieres,lstProduction = self.GetMotsVentes(tplIdent)
        #les pointeurs d'affectation non validés doivent être mis à blanc
        self.PurgeNonValide(IDdossier)
        self.balance = self.GetBalance(IDdossier)
        lstAteliersValid, lstProduitsValid, lstProduitsValid = self.GetValide(IDdossier)

        #matche les produits potentiels par les mots clés
        def ChercheProduits():
            lstProduits = []
            #recherches successives dans les listes
            def Matche(mot,lstProduits):
                lstMots = []
                #comparaison des motcle des produits modèles avec le mot testé venant du dossier
                for motcle in self.lstMotsClesProduits:
                    if motcle in mot :
                        #le mot contient un radical pouvant déterminer un produit, on recherche quel produit
                        for produit, dic in self.dicProduits.items():
                            if motcle in dic['clesstring']:
                                if not (produit,motcle) in lstProduits:
                                    lstProduits.append((produit,motcle))
                                return
                            for tup in dic['clestuple']:
                                if motcle == tup[0]:
                                    if not (produit,tup) in lstProduits:
                                        lstProduits.append((produit,tup))
                                    return
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
        dicMotsProduit = {}
        for produit, trouve in lstProduits:
            #on vérifie si le produit n'est pas déjà validé (les non validés ont été purgés)
            ix +=1
            if produit in lstProduitsValid :
                del lstProduits[ix]
                ix -= 1
                continue
            #les mots isolés s'imposent
            if not produit in dicMotsProduit:
                dicMotsProduit[produit]=[]
            if isinstance(trouve, str):
                dicMotsProduit[produit].append(trouve)
                continue
            #les tuples sont des conditions cumulatives
            if isinstance(trouve, tuple):
                ok = True
                dicMotsProduit[produit].append(trouve[0])
                for mot in trouve[1:]:
                    if mot[:1] == '!' :
                        sens = False
                        mot = mot[1:]
                    else : sens = True
                    present = (mot in lstMotsDossier)
                    if not sens : present = not present
                    ok = present
            if not ok :
                del lstProduits[ix]
                ix -= 1

        #chaque produit retenu est calculé, on associe IDplanCompte et on marque le compte affecté
        lstComptesRetenus = []
        lstDicProduits = []
        lstIxDicProduits = []

        # Un premier passage pour n'affecter que les comptes ayant le mot clé dans le libellé
        for produit, trouve in lstProduits:
            dicProduit = self.GenereDicProduit(produit,dicMotsProduit[produit],lstComptesRetenus)
            dicProduit['IDdossier'] = IDdossier
            lstDicProduits.append(dicProduit)

        produitLeader = ''
        production = 0.0
        # on détermine le produit retenu au plus gros CA
        for dicProduit in lstDicProduits:
            # Création d'un index pour pointer les dicProduits
            lstIxDicProduits.append(dicProduit['IDMproduit'])
            if dicProduit['Production'] > production:
                production = dicProduit['Production']
                produitLeader = dicProduit['IDMproduit']

        # il y a des produit calculés
        if produitLeader != '':
            #le plus gros produit , récupère des comptes sans mot clé dans le libellé
            dicProduit = lstDicProduits[lstIxDicProduits.index(produitLeader)]
            # on récupère les comptes ds balance qui restent
            lstDicProduits[lstIxDicProduits.index(produitLeader)] = self.GenereDicProduit(produitLeader,None,lstComptesRetenus,dicProduit)

            #Les produits de l'atelier ANY peuvent être rattachés à l'atelier du produit
            dicProduitsAny = GetProduitsAny(self.dicProduits)
            for produit, dic in dicProduitsAny.items():
                dicProduit = self.GenereDicProduit(produit,None,lstComptesRetenus)
                dicProduit['IDMatelier'] = produitLeader
                lstDicProduits.append(dicProduit)
                lstIxDicProduits.append(produit)

        # s'il reste des comptes non affectés on teste si les produits non leader peuvent contenir ces no de compte
        for dicProduit in lstDicProduits:
            produit =  dicProduit['IDMproduit']
            if (produit != produitLeader) and (len(produitLeader)>0):
                lstDicProduits[lstIxDicProduits.index(produit)] = self.GenereDicProduit(produit,None,lstComptesRetenus,dicProduit)

        # stockage de l'info dans  _Produits et _Atelier
        for dicProduit in lstDicProduits:
            if dicProduit['Production'] == 0.0 : continue
            if dicProduit['IDMatelier'] in lstAteliersValid: continue
            self.Genere_Atelier(dicProduit)
            self.Genere_Produit(dicProduit)
            print(dicProduit['IDMproduit'],":",dicProduit)
        
        return 'ok'

#************************   Pour Test ou modèle  *********************************
if __name__ == '__main__':
    app = wx.App(0)
    fn = Traitements(annee='2018',client='001990',agc='ANY')
    print('Retour: ',fn)

    app.MainLoop()

