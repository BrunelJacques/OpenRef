#!/usr/bin/env python
# -*- coding: utf8 -*-

#------------------------------------------------------------------------
# Application :    OpenRef, utilitaires pour l'import des comptas
# Auteurs:          Jacques BRUNEL
# Copyright:       (c) 2019-04     Cerfrance Provence
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import os
import wx
import datetime
import xpy.xUTILS_Config as xucfg
import srcOpenRef.UTIL_traitements as orut
import xpy.xGestionDB as xdb


def ListesToDict(listecles, listevaleurs):
    dic = {}
    try:
        for ix in range(len(listecles)):
            dic[listecles[ix]] = listevaleurs[ix]
    except: pass
    return dic

def DictToLists(dic):
    listecles = []
    listevaleurs = []
    try:
        for cle, valeur in dic.items():
            listecles.append(cle)
            listevaleurs.append(valeur)
    except: pass
    return listecles, listevaleurs

def DictToListTpls(dic):
    #usage d'insertion par SQL insertion d'\ devant apostrophe
    liste = []
    try:
        for cle, valeur in dic.items():
            if isinstance(valeur,(list,dict)):
                value = str(valeur).replace('\'','\'\'')
            else:
                value = valeur
            liste.append((cle,value))
    finally: pass
    return liste

class ImportComptas(object):
    def __init__(self,parent, title='',bases=('gi','sql')):
        self.parent = parent
        self.title = title +'[UTIL_import].ImportComptas'
        self.mono, self.topwin = False, False
        self.filieres = ''
        try:
            """
            # enrichissement du titre pour débug
            nameclass = self.parent.__class__.__name__
            title = nameclass + ': ' + title"""
            self.topWindow = wx.GetApp().GetTopWindow()
            if self.topWindow:
                self.topwin = True
            self.topWindow.Size = (1300,300)
            self.topWindow.pos = (200,500)
        except Exception as err:
            pass

        #récup des arguments stockés dans le shelve
        cfg = xucfg.ParamUser()
        implantation= cfg.GetDict(dictDemande=None, groupe='IMPLANTATION', close=False)
        choiximport= cfg.GetDict(dictDemande=None, groupe='IMPORT', close=False)
        user= cfg.GetDict(dictDemande=None, groupe='USER')
        ident= cfg.GetDict(dictDemande=None, groupe='IDENT')
        self.config = {}
        for groupe in [implantation,choiximport,user,ident]:
            for key,value in groupe.items():
                self.config[key] = value

        #ouverture des bases communes GI et OpenRef en s'appuyant sur le  self.config(dict)
        if 'gi' in bases:
            self.DBgi = self.GetGI()
        # ouverture base principale ( ouverture par défaut de db_prim via xGestionDB)
        self.DBsql = xdb.DB()
        self.lstMotsProd = self.GetMotsCle('mProduits')
        self.lstMotsCout = self.GetMotsCle('mCoûts')
        self.dicPlanComp = orut.PrechargePlanCompte(self.DBsql)

    def GetMotsCle(self,table):
        # découpe  tous les motscle de la table et les met dans une liste
        lstMotsCle = []
        # Constitue la liste des mots clé de mProduits 
        req = """SELECT MotsCles
                FROM %s;"""%table
        retour = self.DBsql.ExecuterReq(req, mess='UTIL_import.GetMotsCle')                                        
        if retour == "ok":
            recordset = self.DBsql.ResultatReq()
            lstMotsCle = []
            for record in recordset:
                lst = orut.Decoupe(str(record))
                for mot in lst:
                    mot = mot.strip()
                    mot = mot.lower()
                    if not mot in lstMotsCle:
                        lstMotsCle.append(mot)
        return lstMotsCle

    def GetGI(self):
        # pointer la gestion interne
        DBgi = None
        if self.config['compta'] == 'quadratus':
            configGI = {}
            configGI['typeDB'] = 'access'
            configGI['serveur'] = self.config['serveur']
            configGI['nameDB'] = 'qgi.mdb'
            configGI['serveur'].replace('datadouble', 'database')
            DBgi = xdb.DB(config=configGI)
            if DBgi.echec == 1: DBgi = None
        return DBgi

    def GetClientsNafs(self,lstNafs,annee=None,*args):
        # appelle les clients par naf de la liste
        lstclients = []
        lstNafs = str(lstNafs)[1:-1]
        if not annee:
            annee = datetime.date.today().year
        if self.config['compta'] == 'quadratus':
            req = """SELECT Clients.Code
                    FROM   (Clients 
                                LEFT JOIN Intervenants ON Clients.Code = Intervenants.Code) 
                    WHERE (Intervenants.CodeNAF2008 in (%s)) 
                            AND ((Clients.DateEntree)<#6/30/%s#) 
                            AND ((Clients.DateSortie)>#12/31/%s# 
                                        Or (Clients.DateSortie)<#1/1/1901#)
                    ORDER BY Clients.Code;"""%(lstNafs,annee,annee)
            retour = self.DBgi.ExecuterReq(req, mess='accès GI Clientsnafs', affichError=False)
            if retour == "ok":
                recordset = self.DBgi.ResultatReq()
                for [client,] in recordset:
                    lstclients.append(client)
        return lstclients

    def GetNafs(self,annee=None,*args):
        # appelle les nbre de clients par naf et par production principale dans la gestion interne
        lstNafs = []
        nbDossiers = 0
        if not annee:
            annee = datetime.date.today().year
        if self.config['compta'] == 'quadratus':
            #lstCle = ['code','libelle','nbre']
            req = """SELECT Intervenants.CodeNAF2008, Activites.Libelle, Count(Clients.Code) AS CompteDeCode
                    FROM   (Clients 
                                LEFT JOIN Intervenants ON Clients.Code = Intervenants.Code) 
                            LEFT JOIN Activites ON Clients.CodeActivite = Activites.Code
                    WHERE (((Clients.DateEntree)<#6/30/%s#) AND ((Clients.DateSortie)>#12/31/%s# Or (Clients.DateSortie)<#1/1/1901#))
                    GROUP BY Intervenants.CodeNAF2008, Activites.Libelle
                    ORDER BY Intervenants.CodeNAF2008;"""%(annee,annee)
            retour = self.DBgi.ExecuterReq(req, mess='accès GI nafs', affichError=False)
            if retour == "ok":
                recordset = self.DBgi.ResultatReq()

                #regroupement par code Naf constitution de la liste des activités
                dicNaf = {}
                for code,label,nbre in recordset:
                    if not label: label = '...'
                    if not code : code = " "
                    code=code.upper().strip()
                    if not(code in dicNaf): dicNaf[code] = {'activités':'','nbre':0}
                    dicNaf[code]['activités'] += label.lower()+"; "
                    dicNaf[code]['nbre'] += nbre
                    nbDossiers += nbre
                for code, dic in dicNaf.items():
                    lstNafs.append((code,dic['activités'],dic['nbre']))
        return lstNafs, nbDossiers

    def GetClient(self,code, dicCompta):
        # appelle les infos du client dans la gestion interne
        if not 'ident' in dicCompta : dicCompta['ident']={}
        dicIdent = {}
        dicInfos = {}
        if self.config['compta'] == 'quadratus':

            #infos générales fiche client
            lstCle = ['code', 'juridique', 'production','impot','is','dja','naf']
            req = """SELECT Clients.Code, Intervenants.TypeSociete, Activites.Libelle, Fiscal.CodeImpotDirect, Fiscal.Impot,
                            Intervenants.DateInstallation, Intervenants.CodeNAF2008
                    FROM ((Clients 
                    LEFT JOIN Intervenants ON Clients.Code = Intervenants.Code) 
                    LEFT JOIN Fiscal ON Clients.Code = Fiscal.CodeClient) 
                    LEFT JOIN Activites ON Clients.CodeActivite = Activites.Code
                    WHERE (((Clients.Code) = '%s' ))
                    ;""" % code
            retour = self.DBgi.ExecuterReq(req, mess='accès GI quadra', affichError=False)
            if retour == "ok":
                recordset = self.DBgi.ResultatReq()
                dicGI = ListesToDict(lstCle, recordset[0])
                dicIdent['IDagc'] = self.config['agc']
                dicIdent['IDexploitation'] = code
                dicIdent['IDuser'] = self.config['domaine'] + '.'+self.config['utilisateur']+'/'+self.config['pseudo']
                dicIdent['IDlocalisation'] = self.config['localis']
                dicIdent['IDjuridique'] = dicGI['juridique']
                if dicGI['production']:
                    if len(dicGI['production'])>0:
                        self.filieres = dicGI['production'] + ", "
                dicIdent['Fiscal'] = dicGI['impot']
                dicIdent['ImpSoc'] = dicGI['is']
                if str(dicGI['dja'])[:4] > '1950':
                    dicInfos['DJA'] = str(dicGI['dja'])[:10]
                dicIdent['IDnaf'] = dicGI['naf']

                #nombre d'associés porteurs de parts pleine propriété ou usufruit
                req = """SELECT Annexe.Code2
                        FROM Annexe
                        WHERE (((Annexe.Code1)= '%s') AND ((Annexe.Type)="S") AND ((Annexe.Texte5) In ('P','U')))
                        GROUP BY Annexe.Code2;
                        """ % code
                retour = self.DBgi.ExecuterReq(req, mess='accès GI quadra associés de %s'%code)
                if retour == "ok":
                    recordset = self.DBgi.ResultatReq()
                    dicIdent['NbreAssociés'] = len(recordset)
                else:
                    self.DBgi.Close()
                    self.DBgi = self.GetGI()
            else:
                print('echec accès à la GI pour client : ',code)
        dicCompta['ident'] = dicIdent
        dicCompta['infos'] = dicInfos

    def GetCompta(self,configCPTA,dicCompta):
        nomBase = None
        # vérif du connecteur par recherche du nom de la base
        try:
            DBq = xdb.DB(config = configCPTA)
            nomBase = DBq.nomBase
            if DBq.echec != 0:
                mess = self.title+ ": " + DBq.echec
                nomBase=None
                wx.MessageBox(mess)
        except Exception as err:
            mess = self.title + '.GetCompta:\n%s'%err
            wx.MessageBox(mess, style=wx.ICON_INFORMATION)
        if nomBase:
            # import des infos d'identification et params généraux dans la compta
            if self.config['compta'] == 'quadratus':
                lstCle = ['cloture', 'civilite', 'nomexploitation', 'codepostal', 'siret', 'naf', 'duree']
                req = """SELECT Dossier1.FinExercice, Dossier1.Civilite, Dossier1.RaisonSociale, Dossier1.CodePostal, Dossier1.Siret, Dossier1.CodeNAF, Dossier1.DureeExercice
                        FROM Dossier1;"""
                retour = DBq.ExecuterReq(req, mess='accès Qcompta.dossier quadra')
                if retour == "ok":
                    recordset = DBq.ResultatReq()
                    dicDoss = ListesToDict(lstCle, recordset[0])
                    dicCompta['ident']['Clôture'] = str(dicDoss['cloture'])[:10]
                    civil = ''
                    if len(dicDoss['civilite']) > 1: civil = dicDoss['civilite'] + ' '
                    dicCompta['ident']['NomExploitation'] = civil + dicDoss['nomexploitation']
                    dicCompta['ident']['IDCodePostal'] = dicDoss['codepostal']
                    dicCompta['ident']['Siren'] = dicDoss['siret'][:9]
                    dicCompta['ident']['IDnaf'] = dicDoss['naf']
                    dicCompta['ident']['NbreMois'] = int(dicDoss['duree'])

            # import de la balance de la compta
            lstBalance = []
            if self.config['compta'] == 'quadratus':
                def ChercheMotsCle(compte,lib,uneecr):
                    #découpe le libellé et l'écriture exemple pour trouver les mots clés mis en minuscule qui matchent
                    lstMots = []
                    lstplus=[]
                    if compte[:1] in ('7','6','3'):
                        lstRef = self.lstMotsCout
                        if compte[:1] in ('7','3'): lstRef = self.lstMotsProd
                        if compte[:2] == '30':lstRef = self.lstMotsCout
                        if compte[:3] == '604': lstRef = self.lstMotsProd
                        lstlib = orut.Decoupe(lib)
                        lstecr = orut.Decoupe(uneecr)
                        if len(lstlib+lstecr)==0:
                            req = """
                                SELECT Ecritures.Libelle
                                FROM Ecritures 
                                WHERE Ecritures.Compte = %s;
                                LIMIT 10
                                """%compte
                            retour = DBq.ExecuterReq(req, mess='accès Qcompta.ecritures TOP 10', affichError=False)
                            if retour == "ok":
                                recordset = DBq.ResultatReq()
                                for record in recordset:
                                    lstplus = orut.Decoupe(str(record))
                        for mot in lstlib+lstecr+lstplus:
                            if mot in lstRef:
                                if not mot in lstMots:
                                   lstMots.append(mot)
                    return lstMots
                # appel de la balance clients et fournisseurs
                # lstCle = ['compte', 'libcompte', 'libecriture', 'anouv', 'qte', 'qtenature','qte2','qte2nature','debits','credits']
                req = """
                    SELECT Comptes.Collectif, Comptes.Type, "collectif" AS ecrLibelle, 
                        IIf(Ecritures.CodeJournal = "AN",1,0) AS AN, Sum([Quantite]) AS qte, 
                        Comptes.QuantiteLibelle, Sum([Quantite2]) AS qte2, Comptes.QuantiteLibelle2, 
                        Sum(Ecritures.MontantTenuDebit) AS Debits, Sum(Ecritures.MontantTenuCredit) AS Credits
                    FROM Dossier1, (Ecritures 
                                    INNER JOIN Comptes ON Ecritures.NumeroCompte = Comptes.Numero) 
                    WHERE (((Ecritures.PeriodeEcriture)<=[dossier1].[finexercice]) AND ((Left([NumeroCompte],1))='0'))
                    GROUP BY Comptes.Collectif, Comptes.Type, IIf(Ecritures.CodeJournal = "AN",1,0), 
                            Comptes.QuantiteLibelle, Comptes.QuantiteLibelle2;
                    """
                retour = DBq.ExecuterReq(req, mess='accès Qcompta.ecritures auxiliaires quadra',affichError=False)
                recordsetAux , recordset = [],[]
                if retour == "ok":
                    recordsetAux = DBq.ResultatReq()
                #appel de la balance hors clients et fournisseurs
                #lstCle = ['compte', 'libcompte', 'libecriture', 'anouv', 'qte', 'qtenature','qte2','qte2nature','debits','credits']
                req = """
                    SELECT Ecritures.NumeroCompte, Comptes.Intitule, Max(Ecritures.Libelle) AS ecrLibelle,
                        IIf(Ecritures.CodeJournal = "AN",1,0) AS AN,
                        Sum([Quantite]) AS qte, Comptes.QuantiteLibelle, Sum([Quantite2]) AS qte2, Comptes.QuantiteLibelle2, 
                        Sum(Ecritures.MontantTenuDebit) AS Debits, Sum(Ecritures.MontantTenuCredit) AS Credits
                    FROM Dossier1, (Ecritures 
                                    INNER JOIN Comptes ON Ecritures.NumeroCompte = Comptes.Numero) 
                    WHERE (((Ecritures.PeriodeEcriture)<=[dossier1].[finexercice]) AND ((Left([NumeroCompte],1))<>'0'))
                    GROUP BY Ecritures.NumeroCompte, Comptes.Intitule, IIf(Ecritures.CodeJournal = "AN",1,0), 
                                Comptes.QuantiteLibelle, Comptes.QuantiteLibelle2
                    ORDER BY Ecritures.NumeroCompte;
                    """
                retour = DBq.ExecuterReq(req, mess='accès Qcompta.ecritures quadra')
                if retour == "ok":
                    recordset = DBq.ResultatReq()
                # constitution des lignes a importer sur concaténation des deux recordset
                for compte, libcompte, libmaxecriture, anouv, qte, qtenature,qte2,qte2nature,debits,credits in recordset + recordsetAux :
                    if anouv ==1 :
                        #cumul d'écritures a nouveaux
                        soldedeb = soldefin = round(debits - credits,2)
                        mvtdeb = mvtcre = 0.0
                    else:
                        soldedeb = 0.0
                        mvtdeb = round(debits,2)
                        mvtcre = round(credits,2)
                        soldefin = round(debits - credits,2)
                    if libcompte == None : libcompte = ''
                    if libmaxecriture == None : libmaxecriture = ''
                    if abs(mvtcre) + abs(mvtdeb) + abs(soldedeb) >0:
                        motsclepres = ChercheMotsCle(compte,libcompte,libmaxecriture)
                        IDplanCompte = orut.ChercheIDplanCompte(compte,self.dicPlanComp)
                        lstBalance.append((compte, libcompte.strip(),str(motsclepres)[1:-1], qte, qtenature,
                                       qte2,qte2nature, soldedeb,mvtdeb, mvtcre, soldefin,IDplanCompte))
            dicCompta['balance'] = lstBalance

            dicIdent = {}
            # import des infos dossier de gestion et liasse pour compléter ident
            if self.config['compta'] == 'quadratus':
                dicProd = {}
                def SetDicProd(record):
                    grp = record[0][2:5]
                    elem = record[0][5]
                    ligne = record[0][6:]
                    prod = grp + ligne
                    if ligne in ['A'] : prod += 'b'
                    if int(ligne) > 0 :
                        if not ((prod) in dicProd.keys()) : dicProd[(prod)]={}
                        if elem in ['L'] : dicProd[(prod)]['lib']= record[8]
                        if elem in ['H','M'] : dicProd[(prod)]['surf']= record[3]
                        if elem in ['Q','A','F'] : dicProd[(prod)]['qte']= record[3]
                        if elem in ['A'] :     dicProd[(prod)]['lib']= "\ten chais"
                        if elem in ['F'] :     dicProd[(prod)]['lib']= "Effectif fin"
                # infos liasse agri (AG pour agri)
                req = """SELECT * FROM HISTORIQUE WHERE RUB LIKE 'AGH%' OR RUB LIKE 'AGU%' OR RUB LIKE 'AYP%';"""
                retour = DBq.ExecuterReq(req, mess='accès Qcompta.historique quadra')
                # récup surfaces et main d'oeuvre de la liasse
                if retour == "ok":
                    recordset = DBq.ResultatReq()
                    for record in recordset:
                        if record[0] in ["AGHD", "AGUU"]: dicIdent["SAUfvd"] = record[3]
                        if record[0] in ["AGHE", "AGUW"]: dicIdent["SAUfermage"] = record[3]
                        if record[0] in ["AGHF", "AGUX"]: dicIdent["SAUmétayage"] = record[3]
                        if record[0] in ["AGHB", "AGUV"]: dicIdent["SAUmad"] = record[3]
                        if record[0] in ["AGHC", "AGUT"]: dicIdent["SAU"] = record[3]
                        if record[0] in ["AYP"]: dicIdent["MOpermanents"] = record[3]

                # infos dossier de gestion  agri productions pour constituer un memo préparé dans dicProd
                req = """SELECT * FROM HISTORIQUE
                        WHERE (((HISTORIQUE.RUB) Like 'AGSAU%' Or (HISTORIQUE.RUB) Like 'AGVIT%' 
                                        Or (HISTORIQUE.RUB) Like 'AGPRS%' Or (HISTORIQUE.RUB) Like 'AGPAN%') 
                                AND ((HISTORIQUE.Regle) In ('0','')) 
                                AND ((HISTORIQUE.AnN)<>0));
                    """
                retour = DBq.ExecuterReq(req, mess='accès Qcompta.historique quadra productions nombre')
                # récup des libellés
                if retour == "ok":
                    recordset = DBq.ResultatReq()
                    for record in recordset:
                        SetDicProd(record)
                req = """SELECT * FROM HISTORIQUE
                        WHERE (((HISTORIQUE.RUB) Like 'AGSAU%' Or (HISTORIQUE.RUB) Like 'AGVIT%' 
                                        Or (HISTORIQUE.RUB) Like 'AGPRS%' Or (HISTORIQUE.RUB) Like 'AGPAN%') 
                                AND ((HISTORIQUE.Regle) In ('0','')) 
                                AND ((HISTORIQUE.Alpha)<> ''));
                    """
                retour = DBq.ExecuterReq(req, mess='accès Qcompta.historique quadra productions nombre')
                # récup des quantités
                if retour == "ok":
                    recordset = DBq.ResultatReq()
                    for record in recordset:
                        SetDicProd(record)
                # intégration des productions dans le memo
                dicIdent['Productions'] = "Production__surface__quantite\n"
                dicElem = {}
                for key in sorted(dicProd.keys()):
                    grp = key[:3]
                    if not grp in dicElem : dicElem[grp] = {'surf':0.0,'qte':0.0,'nature':'ha'}
                    for champ in ['lib','surf','qte']:
                        if not champ in dicProd[key].keys(): dicProd[key][champ] = 0
                    texte = str(dicProd[key]['lib'])+'__'+ str(dicProd[key]['surf']) +'__' + str(dicProd[key]['qte'])
                    try:
                        dicIdent['Productions'] += '\n%s'%texte
                        dicElem[grp]['surf']+= float(dicProd[key]['surf'])
                        dicElem[grp]['qte']+= float(dicProd[key]['qte'])
                    except: pass
                #determination du meilleur élément caractéristique
                qte = 0.0
                surf = 0.0
                grpQte = ''
                for key, value in dicElem.items():
                    if value['qte'] > qte :
                        grpQte = key
                        qte = value['qte']
                if qte == 0.0:
                    # aucune saisie de quantités dans dossier de gestion, on prend les surfaces du groupe activité maxi
                    for key, value in dicElem.items():
                        if value['surf'] > surf:
                            surf = value['surf']
                    dicIdent['NbElemCar'] = surf
                    dicIdent['ElemCar'] = 'ha'
                else:
                    #on priviligie les quantités du groupe d'activité maxi
                    dicIdent['NbElemCar'] = qte
                    if grpQte == 'VIT': dicIdent['ElemCar'] = 'hl'
                    elif grpQte == 'PAN': dicIdent['ElemCar'] = 'tête'
                    elif grpQte == 'SAU': dicIdent['ElemCar'] = 'qx'
                    else: dicIdent['ElemCar'] = 'qte'

                # récup surfaces, main d'oeuvre, activité et tableau de financement, dans le dossier de gestion AGRI
                req = """SELECT * FROM HISTORIQUE 
                        WHERE   (RUB LIKE 'AGPF%' OR RUB LIKE 'AGPM%') 
                                AND AnN<>0;"""
                retour = DBq.ExecuterReq(req, mess='accès Qcompta.historique quadra surfaces MO')
                if retour == "ok":
                    recordset = DBq.ResultatReq()
                    dicSAU = {}
                    dicMO = {}
                    lstSAU =    [("AGPF201", "SAUfvd"), ("AGPF202", "SAUfermage"),
                                ("AGPF203", "SAUmétayage"),("AGPF204", "SAUmad"), ("AGPF205", "SAU")]
                    lstMO = [("AGPMO14","MOexploitants"),("AGPMO15","MOpermanents"),("AGPMO16","MOsaisonniers")]
                    for record in recordset:
                        for (champQ,champOR) in lstSAU:
                            if record[0] == champQ:
                                dicSAU[champOR] = record[3]
                        for (champQ,champOR) in lstMO:
                            if record[0] == champQ:
                                dicMO[champOR] = record[3]
                    if len(dicSAU)>0:
                        #la liasse à pu préalimenter différemment, on remet à zéro si dossier de gestion
                        for (champQ,champOR) in lstSAU:
                            if champOR in dicIdent: dicIdent[champOR]= 0.0
                            if champOR in dicSAU: dicIdent[champOR] = dicSAU[champOR]
                    if len(dicMO)>0:
                        for (champQ,champOR) in lstMO:
                            if champOR in dicIdent: dicIdent[champOR]= 0.0
                            if champOR in dicMO: dicIdent[champOR] = dicMO[champOR]

                # récup du tableau de financement dans le dossier de gestion
                req = """SELECT * FROM HISTORIQUE 
                        WHERE   (RUB LIKE 'AGTR%' OR RUB LIKE 'AGTE%') 
                                AND AnN<>0;"""
                retour = DBq.ExecuterReq(req, mess='accès Qcompta.historique quadra TBF')
                if retour == "ok":
                    recordset = DBq.ResultatReq()
                    lstTBF = [("AGTR1","Caf"),(["AGTR2","AGTR3","AGTR4","AGTR5"],"Cessions"),("AGTRA","SubvReçues"),
                            (["AGTRB","AGTRC"],"NvxEmprunts"),(["AGTR9","AGTR8"],"Apports"),(["AGTE1","AGTE9","AGTEA"],"Prélèvements"),
                            (["AGTE2","AGTE3","AGTE4","AGTE5"],"Investissements"),(["AGTEB","AGTEC"],"RbtEmprunts")]
                    for record in recordset:
                        for (champQ,champOR) in lstTBF:
                            if record[0] in champQ:
                                dicIdent[champOR] = record[3]

                # récup de l'activité dans le dossier de gestion
                req = """SELECT * FROM HISTORIQUE 
                        WHERE   (RUB = 'ACTIVITE');"""
                retour = DBq.ExecuterReq(req, mess='accès Qcompta.historique quadra TBF')
                if retour == "ok":
                    recordset = DBq.ResultatReq()
                    dicIdent['Remarques'] = ""
                    for record in recordset:
                        if record[0] == 'ACTIVITE':
                            dicCompta['ident']['Filières']= self.filieres
                            try:
                                for mot in record[8].split(' '):
                                    if not mot in self.filieres:
                                        dicCompta['ident']['Filières'] += mot+' '
                            except : pass
            for key, value in dicIdent.items():
                dicCompta['ident'][key] = dicIdent[key]
            DBq.Close()

    def HorsPeriode(self,configCPTA,annee,nbAnter,lstNafs):
        nomBase = None
        # vérif du connecteur par recherche du nom de la base
        try:
            DBq = xdb.DB(config = configCPTA)
            nomBase = DBq.nomBase
            if DBq.echec != 0:
                mess = self.title+ ": " + DBq.echec
                nomBase=None
                wx.MessageBox(mess)
        except Exception as err:
            DBq.Close()
            return True
        retour = True
        if nomBase:
            # import des infos de l'exercice et naf dans la compta
            if self.config['compta'] == 'quadratus':
                req = """SELECT Dossier1.FinExercice, Dossier1.CodeNAF
                        FROM Dossier1;"""
                retour = DBq.ExecuterReq(req, mess='accès Qcompta.dossier quadra')
                if retour == "ok":
                    recordset = DBq.ResultatReq()
                    exercice,naf = recordset[0]
                    #controle du naf si filtre posé
                    if lstNafs:
                        if not naf.upper().strip() in lstNafs:
                            DBq.Close()
                            return True
                    anex = int(str(exercice)[:4])
                    anchoix = int(annee)
                    for i in range(0,int(nbAnter)+1):
                        if anex == anchoix-i:
                            retour = False
        DBq.Close()
        return retour

    def Stockage(self,dicCompta):
        #test la présence préalable dans mySql
        agc = dicCompta['ident']['IDagc']
        exploitation = dicCompta['ident']['IDexploitation']
        cloture = dicCompta['ident']['Clôture']
        req = """SELECT IDdossier, Validé FROM _Ident
                WHERE (IDagc = '%s'   AND IDexploitation = '%s' AND Clôture = '%s')
                ;""" % (agc,exploitation,cloture)
        retour = self.DBsql.ExecuterReq(req, mess='accès OpenRef test présence')

        #insertion dans mySql
        def InsertOpenRef(IDdossier):
            #insertion table _Ident
            lstChamps,lstDonnees = DictToLists(dicCompta['ident'])
            if IDdossier :
                lstChamps.append('IDdossier')
                lstDonnees.append(IDdossier)
            ret = self.DBsql.ReqInsert('_Ident',lstChamps,lstDonnees,mess = 'Insert OpenRef._Ident')
            if not IDdossier:
                IDdossier = self.DBsql.newID
            dicCompta['ident']['IDdossier'] = IDdossier

            #insertion table _Balance
            lstChamps = "Compte,Libellé,MotsCléPrés,Quantités1,Unité1,Quantités2,Unité2,SoldeDeb,DBmvt,CRmvt,SoldeFin,IDplanCompte,IDdossier".split(',')
            lstDonnees = []
            for ligne in dicCompta['balance']:
                ligne += (IDdossier,)
                lstDonnees.append(ligne)
            ret = self.DBsql.ReqInsert('_Balances',lstChamps,lstDonnees,mess = 'Insert OpenRef._Balances')

            #insertion table _Infos
            if len(lstDonnees) > 0:
                lstChamps = "IDdossier, IDMinfo, Numerique, Bool, Texte".split(',')
                lstDonnees = []
                for cle, valeur in  dicCompta['infos'].items():
                    numerique, vf, texte = 0.0, True, ''
                    if isinstance(valeur, (str,datetime)) : texte = str(valeur)
                    if isinstance(valeur, (bool) ) : vf = valeur
                    if isinstance(valeur, (int,float)) : numerique = valeur
                    IDMinfo = cle
                    lstDonnees.append((IDdossier, IDMinfo,numerique,vf,texte))
                ret = self.DBsql.ReqInsert('_Infos',lstChamps,lstDonnees,mess = 'Insert OpenRef._Infos')

            #def InsertOpenRef, fin

        if retour == "ok":
            recordset = self.DBsql.ResultatReq()
            if len(recordset) == 0 :
                InsertOpenRef(None)
            elif not recordset[0][1] == 1:
                #dossier présent mais non validé, suppression préalable
                exID = recordset[0][0]
                condition = "_Ident.IDdossier = %d"% exID
                for table in ('_Ident','_Balances','_Infos'):
                    condition = "%s.IDdossier = %d" % (table,exID)
                    self.DBsql.ReqDEL(table,condition,mess='Del dans %s'%table)
                InsertOpenRef(exID)
            else:
                #silencieux en mode batch
                if self.mono:
                    valide = 0
                    try:
                        valide = recordset[0][1]
                    except: pass
                    mess = 'Nbre d\'enregistrement en retour : %s'%len(recordset)
                    if valide == 1 : mess = 'Dossier validé non modifiable'
                    wx.MessageBox('Test présence insertion %s\n\n%s'%(exploitation, mess))
        return retour

    def QuadraLstPaths(self,pathCompta,annee,nbAnter):
        #renvoie la liste des répertoires qu'il faut inspecter pour une plage d'exercices
        lstPaths = []
        if not annee : annee = datetime.datetime.now().year -1
        if not nbAnter : nbAnter = 0
        annee = int(annee)
        pathCpta = pathCompta+ '/CPTA/'
        lstPaths.append(pathCpta+'DC')
        # balayage dossiers archives
        for item in sorted(os.listdir(pathCpta),reverse=True):
            if (item[:2].lower() == 'da') and os.path.isdir(pathCpta +item):
                for i in range(0,int(nbAnter)+1):
                    an = 'DA'+str(annee-i)
                    if an in item:
                        lstPaths.append(pathCpta+item)
        return lstPaths

    def Import(self,multi=False, lstNafs=None):
        # import des comptas sur une plage d'exercices
        configCPTA = {}
        self.nbreOK = 0
        if self.config['compta'] == 'quadratus':
            configCPTA['nameDB'] = 'Qcompta.mdb'
            configCPTA['typeDB'] = 'access'
            if multi:
                self.topWindow.SetStatusText("Préparation de la liste : patientez...")
                #alimente un éventuel filtre sur les codes nafs
                lstNafs = None
                if not (self.config['nafs'] in (None,'','tous')):
                    if self.config['nafs'][:4].lower() != 'tous':
                        lstNafs = self.config['lstNafs']
                        lstClientsNafs = self.GetClientsNafs(lstNafs)
                #recherche de la liste des clients  dans dossier courant et archive du millesime
                lstClients = []
                lstPathsAnnee = self.QuadraLstPaths(self.config['pathCompta'], self.config['annee'], self.config['nbAnter'], )
                if len(lstClientsNafs) > 0:
                    lstClients = lstClientsNafs
                else:
                    for path in lstPathsAnnee:
                        for client in os.listdir(path):
                            if not client in lstClients:
                                if os.path.isfile(path + '/' + client + '/QCompta.mdb'):
                                    configCPTA['serveur'] = path + '/' + client
                                self.topWindow.SetStatusText( "%s - %s, Nombre: %d (%s)" % (path, client, len(lstClients),str(lstClients)[-200:]))
                                if path[-2:] == 'DC':
                                    if self.HorsPeriode(configCPTA,self.config['annee'], self.config['nbAnter'],lstNafs):
                                        continue
                                lstClients.append(client)
            else:
                # le client était choisi dans la config
                lstClients = [self.config['client']]
            messBasEcran = ''

            for client in lstClients:
                if self.topwin:
                    messBasEcran += " - Client : %s "%client
                    self.topWindow.SetStatusText(messBasEcran)
                #l'accès à la fiche client ne se fait qu'une fois pour tous les paths
                dicCompta = {}
                self.GetClient(client,dicCompta)
                if len(dicCompta['ident'])==0:
                    #absent dans la GI
                    if self.topwin:
                        messBasEcran += 'GIko '
                        messBasEcran = messBasEcran[-300:]
                        self.topWindow.SetStatusText(messBasEcran)
                    continue
                print(client)
                # présent dans la GI
                # nouveau controle du naf pour les archives déjà testé dans HorsExercice sur DC
                if lstNafs:
                    if not dicCompta['ident']['IDnaf'] in lstNafs:
                        continue
                # balayage de la liste des répertoires utiles pour la compta
                lstPaths = self.QuadraLstPaths(self.config['pathCompta'],self.config['annee'],self.config['nbAnter'],)
                # lancement du balayage des comptas dans la plage d'exerices
                for path in lstPaths:
                    if os.path.isfile(path+'/'+client+'/QCompta.mdb'):
                        configCPTA['serveur'] = path + '/'+client
                        if 'IDdossier' in dicCompta['ident']:
                            # le stockage précédent à alimenté ID dossier
                            del dicCompta['ident']['IDdossier']
                        self.GetCompta(configCPTA,dicCompta)
                        anex = int(str(dicCompta['ident']['Clôture'])[:4])
                        anchoix = int(self.config['annee'])
                        ok = False
                        for i in range(0, int(self.config['nbAnter']) + 1):
                            if anex == anchoix-i:
                                ok = True
                        if not ok : continue
                        retour = self.Stockage(dicCompta)
                        if retour == 'ok':
                            self.nbreOK +=1
                        if self.topwin:
                            messBasEcran += retour+' '
                            messBasEcran = messBasEcran[-230:]
                            self.topWindow.SetStatusText(messBasEcran)
        self.Close()

    def Close(self):
        try:
            self.DBgi.Close()
            self.DBsql.Close()
        except:pass
        wx.MessageBox('%s \n\nFin de l\'import\n%d dossiers importés'%(self.title,self.nbreOK))

#************************   Pour Test ou modèle  *********************************
if __name__ == '__main__':
    app = wx.App(0)
    imp = ImportComptas(None)
    imp.Import()
    app.MainLoop()

