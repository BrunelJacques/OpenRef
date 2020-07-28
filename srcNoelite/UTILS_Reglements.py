#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    NoeLITE, gestion des Reglements en lot
# Usage : Ensemble de fonctions acompagnant DLG_Reglements_gestion
# Auteur:          Jacques BRUNEL
# Copyright:       (c) 2020-04   Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import srcNoelite.UTILS_Historique  as nuh
import xpy.xGestionDB               as xdb
import xpy.xGestion_TableauEditor   as xgte
import xpy.xGestion_TableauRecherche as xgtr
import xpy.xUTILS_SaisieParams      as xusp
import xpy.outils.xformat           as xfor
import datetime

SYMBOLE = "€"

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
                'colonneTri': 2,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                }

def GetFamilles(matriceOlv, filtre = None, limit=100):
    # ajoute les données à la matrice pour la recherche d'une famille
    where = ""
    if filtre:
        where = """WHERE familles.adresse_intitule LIKE '%%%s%%'
                        OR individus_1.ville_resid LIKE '%%%s%%'
                        OR individus.nom LIKE '%%%s%%'
                        OR individus.prenom LIKE '%%%s%%' """%(filtre,filtre,filtre,filtre,)

    lstChamps = matriceOlv['listeChamps']
    lstCodesColonnes = matriceOlv['listeCodesColonnes']

    db = xdb.DB()
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
    db.Close()
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

def GetFamille():
    dicOlv = GetMatriceFamilles()
    dlg = xgtr.DLG_tableau(None,dicOlv=dicOlv)
    ret = dlg.ShowModal()
    if ret == wx.OK:
        IDfamille = dlg.GetSelection().donnees[1]
    else: IDfamille = None
    dlg.Destroy()
    return IDfamille

def GetMatriceDepots():
    dicBandeau = {'titre':"Rappel d'un depot existant",
                  'texte':"les mots clés du champ en bas permettent de filtrer d'autres lignes et d'affiner la recherche",
                  'hauteur':15, 'nomImage':"xpy/Images/32x32/Matth.png"}

    # Composition de la matrice de l'OLV depots, retourne un dictionnaire

    lstChamps = ['0','IDdepot', 'depots.date', 'depots.nom',
                    'comptes_bancaires.nom', 'observations']

    lstNomsColonnes = ['0','numéro', 'date', 'nomDépôt', 'banque', 'nbre', 'total', 'détail', 'observations']

    lstTypes = ['INTEGER','INTEGER','VARCHAR(10)','VARCHAR(80)','VARCHAR(130)','VARCHAR(10)','VARCHAR(10)','VARCHAR(170)','VARCHAR(170)']
    lstCodesColonnes = [xusp.SupprimeAccents(x).lower() for x in lstNomsColonnes]
    lstValDefColonnes = xgte.ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = xgte.LargeursDefaut(lstNomsColonnes, lstTypes)
    lstColonnes = xusp.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
    return   {
                'listeColonnes': lstColonnes,
                'listeChamps':lstChamps,
                'listeNomsColonnes':lstNomsColonnes,
                'listeCodesColonnes':lstCodesColonnes,
                'getDonnees': GetDepots,
                'dicBandeau': dicBandeau,
                'colonneTri': 2,
                'sensTri' : False,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                }

def GetDepots(matriceOlv, filtre = None, limit=100):
    # ajoute les données à la matrice pour la recherche d'un depot
    where = ""
    if filtre:
        where = """WHERE IDdepot LIKE '%%%s%%'
                        OR depots.date LIKE '%%%s%%'
                        OR depots.nom LIKE '%%%s%%'
                        OR comptes_bancaires.nom LIKE '%%%s%%'
                        OR observations LIKE '%%%s%%' """%(filtre,filtre,filtre,filtre,filtre)

    lstChamps = matriceOlv['listeChamps']
    lstCodesColonnes = matriceOlv['listeCodesColonnes']

    db = xdb.DB()
    req = """   SELECT %s
                FROM depots
                LEFT JOIN comptes_bancaires ON comptes_bancaires.IDcompte = depots.IDcompte
                %s 
                ORDER BY depots.date DESC
                LIMIT %d ;""" % (",".join(lstChamps),where,limit)
    retour = db.ExecuterReq(req, mess='GetDepots' )
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()

    # composition des données du tableau à partir du recordset
    dicDepots = {}
    ixID = lstCodesColonnes.index('numero')
    for record in recordset:
        dicDepots[record[ixID]] = {}
        for ix in range(len(lstChamps)-1):
            dicDepots[record[ixID]][lstCodesColonnes[ix]] = record[ix]
        # champ observation relégué en fin
        dicDepots[record[ixID]][lstCodesColonnes[-1]] = record[-1]
        dicDepots[record[ixID]]['lstModes'] = []

    # appel des compléments d'informations sur les règlements associés au dépôt
    lstIDdepot = [x for x in dicDepots.keys()]
    req = """SELECT reglements.IDdepot, reglements.IDmode, modes_reglements.label,
                SUM(reglements.montant), COUNT(reglements.IDreglement)
                FROM reglements 
                LEFT JOIN modes_reglements ON modes_reglements.IDmode = reglements.IDmode
                WHERE reglements.IDdepot IN (%s)
                GROUP BY reglements.IDdepot, reglements.IDmode, modes_reglements.label
                ;"""% str(lstIDdepot)[1:-1]
    retour = db.ExecuterReq(req, mess='GetDepots' )
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()
    db.Close()

    # Ajout des compléments au dictionnaire
    for IDdepot, IDmode, label, somme, nombre in recordset:
        if not 'nbre' in dicDepots[IDdepot]:
            dicDepots[IDdepot]['nbre'] = 0
            dicDepots[IDdepot]['total'] = 0.0
        dicDepots[IDdepot]['nbre'] += nombre
        dicDepots[IDdepot]['total'] += somme
        dicDepots[IDdepot][IDmode] = {}
        dicDepots[IDdepot][IDmode]['nbre'] = nombre
        dicDepots[IDdepot][IDmode]['label'] = label
        dicDepots[IDdepot]['lstModes'].append(IDmode)

    # composition des données
    lstDonnees = []
    for IDdepot, dic in dicDepots.items():
        if not 'nbre' in dic.keys(): continue
        ligne = []
        dic['detail'] = ""
        for IDmode in dic['lstModes']:
            dic['detail'] += "%d %s, "%(dic[IDmode]["nbre"], dic[IDmode]["label"])
        for code in lstCodesColonnes:
            ligne.append(dic[code])
        lstDonnees.append(ligne)
    dicOlv =  matriceOlv
    dicOlv['listeDonnees']=lstDonnees
    return lstDonnees

def GetBanquesNne(where = 'code_nne IS NOT NULL'):
    db = xdb.DB()
    ldBanques = []
    lstChamps = ['IDcompte','nom','defaut','code_nne','iban','bic']
    req = """   SELECT %s
                FROM comptes_bancaires
                WHERE %s
                """ % (",".join(lstChamps),where)
    retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetBanquesNne' )
    if retour == "ok":
        recordset = db.ResultatReq()
        if len(recordset) == 0:
            wx.MessageBox("Aucun banque n'a de compte destination (code Nne) paramétré")
    db.Close()
    for record in recordset:
        dicBanque = {}
        for ix in range(len(lstChamps)):
            dicBanque[lstChamps[ix]] = record[ix]
        ldBanques.append(dicBanque)
    return ldBanques

def GetModesReglements():
    db = xdb.DB()
    ldModesRegls = []
    lstChamps = ['IDmode','label','numero_piece','nbre_chiffres','type_comptable','code_compta']
    req = """   SELECT %s
                FROM modes_reglements
                ;"""%",".join(lstChamps)
    retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetModesReglements' )
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()
        if len(recordset) == 0:
            wx.MessageBox("Aucun mode de règlements")
    db.Close()
    for record in recordset:
        dicModeRegl = {}
        for ix in range(len(lstChamps)):
            dicModeRegl[lstChamps[ix]] = record[ix]
        ldModesRegls.append(dicModeRegl)
    return ldModesRegls

def GetDesignationFamille(IDfamille):
    if not isinstance(IDfamille,int): return ""
    db = xdb.DB()
    req = """   SELECT adresse_intitule
                FROM familles
                WHERE IDfamille = %d
                """ % (IDfamille)
    retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetDesignationFamille' )
    if retour == "ok":
        recordset = db.ResultatReq()
    designation = ''
    for record in recordset:
        designation = record[0]
    db.Close()
    return designation

def GetPayeurs(IDfamille):
    db = xdb.DB()
    ldPayeurs = []
    lstChamps = ['IDpayeur','IDcompte_payeur','nom']
    req = """   SELECT %s
                FROM payeurs
                WHERE IDcompte_payeur = %d
                """ % (",".join(lstChamps),IDfamille)
    retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetPayeurs')
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()
    for record in recordset:
        dicPayeur = {}
        for ix in range(len(lstChamps)):
            dicPayeur[lstChamps[ix]] = record[ix]
        ldPayeurs.append(dicPayeur)
    db.Close()
    return ldPayeurs

def SetPayeur(IDcompte_payeur,nom):
    listeDonnees = [('IDcompte_payeur',IDcompte_payeur),
                    ('nom',nom)]
    DB = xdb.DB()
    DB.ReqInsert("payeurs", lstDonnees=listeDonnees,mess="UTILS_Reglements.SetPayeur")
    ID = DB.newID
    DB.Close()
    return ID

def GetReglements(IDdepot):
    listeDonnees = []
    db = xdb.DB()
    #            IDreglement,date,IDfamille,designation,payeur,labelmode,numero,libelle,montant,IDpiece in recordset
    lstChamps = ['reglements.IDreglement', 'reglements.date', 'reglements.IDcompte_payeur', 'familles.adresse_intitule',
                 'payeurs.nom', 'modes_reglements.label', 'reglements.numero_piece', 'reglements.observations', 
                 'reglements.montant', 'reglements.IDpiece','reglements.compta']

    req = """   SELECT %s
                FROM (( reglements 
                        LEFT JOIN modes_reglements ON reglements.IDmode = modes_reglements.IDmode) 
                        LEFT JOIN payeurs ON reglements.IDpayeur = payeurs.IDpayeur) 
                        LEFT JOIN familles ON reglements.IDcompte_payeur = familles.IDfamille
                WHERE ((reglements.IDdepot = %d))
                ;""" % (",".join(lstChamps),IDdepot)

    retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetReglements')
    recordset = ()
    if retour == "ok":
        recordset = db.ResultatReq()

    for IDreglement,date,IDfamille,designation,payeur,labelmode,numero,libelle,montant,IDpiece,compta in recordset:
        creer = "N"
        # la reprise force la non création car déjà potentiellement fait. IDpiece contient l'ID de la prestation créée
        lstDonneesTrack = [IDreglement, date, IDfamille, designation,payeur, labelmode, numero, "", "", libelle,
                           montant, creer, compta]
        listeDonnees.append(lstDonneesTrack)
    db.Close()
    return listeDonnees

def GetNewIDreglement(lstID):
    # Recherche le prochain ID reglement après ceux de la base et éventuellement déjà dans la liste ID préaffectés
    db = xdb.DB()
    req = """SELECT MAX(IDreglement) 
            FROM reglements;"""
    db.ExecuterReq(req)
    recordset = db.ResultatReq()
    ID = recordset[0][0] + 1
    while ID in lstID:
        ID += 1
    return ID

def ValideLigne(track):
    track.ligneValide = True
    track.messageRefus = "Saisie incomplète\n\n"

    # vérification des éléments saisis
    if not len(GetDesignationFamille(track.IDfamille)) > 0:
        track.messageRefus += "La famille n'est pas identifiée\n"

    # montant null
    if track.montant == 0.0:
        track.messageRefus += "Le montant est à zéro\n"

    # IDreglement manquant
    if track.IDreglement in (None,0) :
        track.messageRefus += "L'ID reglement n'est pas été déterminé à l'entrée du montant\n"

    # Date
    if track.date == None or not isinstance(track.date,wx.DateTime):
        track.messageRefus += "Vous devez obligatoirement saisir une date d'émission du règlement !\n"

    # Mode
    if track.mode == None or len(track.mode) == 0:
        track.messageRefus += "Vous devez obligatoirement sélectionner un mode de règlement !\n"

    # Numero de piece
    if track.mode[:3].upper() == 'CHQ':
        if not track.numero or len(track.numero)<4:
            track.messageRefus += "Vous devez saisir un numéro de chèque !\n"
        # libelle pour chèques
        if track.libelle == '':
            track.messageRefus += "Veuillez saisir la banque émettrice du chèque dans les observations !\n"

    # Payeur
    if track.payeur == None:
        track.messageRefus += "Vous devez obligatoirement sélectionner un payeur dans la liste !\n"

    # envoi de l'erreur
    if track.messageRefus != "Saisie incomplète\n\n":
        track.ligneValide = False
    else: track.messageRefus = ""
    return

def SetReglement(dlg,track):
    if not track.ligneValide:
        return False
    # --- Sauvegarde du règlement ---
    IDmode = dlg.dicModesRegl[track.mode]['IDmode']
    IDpayeur = None
    for dicPayeur in dlg.pnlOlv.ldPayeurs:
        if track.payeur in dicPayeur['nom']:
            IDpayeur = dicPayeur['IDpayeur']
            break
    if not IDpayeur:
        IDpayeur = SetPayeur(track.IDfamille,track.payeur)

    listeDonnees = [
        ("IDreglement", track.IDreglement),
        ("IDcompte_payeur", IDpayeur),
        ("date", xfor.DatetimeToStr(track.date,iso=True)),
        ("IDmode", IDmode),
        ("numero_piece", track.numero),
        ("montant", track.montant),
        ("IDpayeur", IDpayeur),
        ("observations", track.libelle),
        ("IDcompte", dlg.GetIDbanque()),
        ("date_saisie", xfor.DatetimeToStr(datetime.date.today(),iso=True)),
        ("IDutilisateur", dlg.IDutilisateur),
    ]
    attente = 0
    if hasattr(track,'differe'):
        listeDonnees.append(("date_differe", xfor.DatetimeToStr(track.differe,iso=True)))
        if len(track.differe) > 0:
            attente = 1
    listeDonnees.append(("encaissement_attente",attente))

    db = xdb.DB()
    if track.IDreglement in dlg.pnlOlv.lstNewReglements:
        nouveauReglement = True
        ret = db.ReqInsert("reglements",lstDonnees= listeDonnees, mess="UTILS_Reglements.SetReglement")
        dlg.pnlOlv.lstNewReglements.remove(track.IDreglement)
    else:
        nouveauReglement = False
        db.ReqMAJ("reglements", listeDonnees, "IDreglement", track.IDreglement)
    db.Close()

    # --- Mémorise l'action dans l'historique ---
    if nouveauReglement == True:
        IDcategorie = 6
        categorie = ("Saisie")
    else:
        IDcategorie = 7
        categorie = "Modification"
    texteMode = track.mode
    if track.numero != "":
        texteNumpiece = u" n°%s" % track.numero
    else:
        texteNumpiece = u""
    if texteNumpiece == "":
        texteDetail = u""
    else:
        texteDetail = u"- %s - " % (texteNumpiece)
    montant = u"%.2f %s" % (track.montant, SYMBOLE)
    textePayeur = track.payeur
    nuh.InsertActions([{
        "IDfamille": track.IDfamille,
        "IDcategorie": IDcategorie,
        "action": ("Noelite %s du règlement ID%d : %s en %s %spayé par %s") % (
        categorie, track.IDreglement, montant, texteMode, texteDetail, textePayeur),
    }, ])
    return True

class Article(object):
    def __init__(self,nature):
        self.nature = nature

    def GetMatriceArticles(self):
        dicBandeau = {'titre':"Recherche d'un article prestation",
                      'texte':"l'article choisi détermine le code du plan comptable de la prestation générée",
                      'hauteur':15, 'nomImage':"xpy/Images/32x32/Matth.png"}

        # Composition de la matrice de l'OLV articles, retourne un dictionnaire

        lstChamps = ['0','matPlanComptable.pctCompte','matPlanComptable.pctCodeComptable','matPlanComptable.pctLibelle',]

        lstNomsColonnes = ["0","compte","code","libellé"]

        lstTypes = ['INTEGER','VARCHAR(8)','VARCHAR(16)','VARCHAR(100)']
        lstCodesColonnes = [xusp.SupprimeAccents(x) for x in lstNomsColonnes]
        lstValDefColonnes = xgte.ValeursDefaut(lstNomsColonnes, lstTypes)
        lstLargeurColonnes = xgte.LargeursDefaut(lstNomsColonnes, lstTypes)
        lstColonnes = xusp.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
        return   {
                    'listeColonnes': lstColonnes,
                    'listeChamps':lstChamps,
                    'listeNomsColonnes':lstNomsColonnes,
                    'listeCodesColonnes':lstCodesColonnes,
                    'getDonnees': self.GetArticles,
                    'dicBandeau': dicBandeau,
                    'colonneTri': 2,
                    'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                    'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                    }

    def GetArticles(self,matriceOlv,filtre = None):
        # le pointeur de cette fonction est dans le dic généré par GetMatriceArticles,
        nature = self.nature
        if nature: nature = nature.lower()
        if nature == 'don':
            rad1 = 'DON'
            rad2 = 'PRET'
        else:
            rad1 = 'RBT'
            rad2 = 'DEB'

        where = """ ((pctLibelle Like '%s%%')
                        OR (pctLibelle Like '%s%%')
                        OR (pctCodeComptable Like '%s%%')
                        OR (pctCodeComptable Like '%s%%'))
                """%(rad1,rad2,rad1,rad2)
        if filtre:
            where += """AND (pctLibelle LIKE '%%%s%%'
                            OR pctCodeComptable LIKE '%%%s%%'
                            OR pctCompte LIKE '%%%s%%')"""%(filtre,filtre,filtre)

        db = xdb.DB()
        lstChamps = matriceOlv['listeChamps']
        lstCodesColonnes = matriceOlv['listeCodesColonnes']
        req = """SELECT %s
                FROM matPlanComptable
                WHERE %s;
                """ % (",".join(lstChamps),where)
        retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetArticles' )
        recordset = ()
        if retour == "ok":
            recordset = db.ResultatReq()
            if len(recordset) == 0:
                wx.MessageBox("Aucun article paramétré contenant '%s' ou '%s' dans le code ou le libellé"%(rad1,rad2))
        db.Close()

        # composition des données du tableau à partir du recordset, regroupement par article
        dicArticles = {}
        ixID = lstCodesColonnes.index('code')
        for record in recordset:
            if not record[ixID] in dicArticles.keys():
                dicArticles[record[ixID]] = {}
                for ix in range(len(lstCodesColonnes)):
                    dicArticles[record[ixID]][lstCodesColonnes[ix]] = record[ix]
            else:
                # ajout de noms et prénoms si non encore présents
                if not record[-2] in dicArticles[record[ixID]]['noms']:
                    dicArticles[record[ixID]]['noms'] += "," + record[-2]
                if not record[-1] in dicArticles[record[ixID]]['prenoms']:
                    dicArticles[record[ixID]]['prenoms'] += "," + record[-1]

        lstDonnees = []
        for key, dic in dicArticles.items():
            ligne = []
            for code in lstCodesColonnes:
                ligne.append(dic[code])
            lstDonnees.append(ligne)
        dicOlv =  matriceOlv
        dicOlv['listeDonnees']=lstDonnees
        return lstDonnees

    def GetArticle(self):
        dicOlv = self.GetMatriceArticles()
        dlg = xgtr.DLG_tableau(None,dicOlv=dicOlv)
        ret = dlg.ShowModal()
        if ret == wx.OK:
            article = dlg.GetSelection().donnees[1]
        else: article = None
        dlg.Destroy()
        return article

def GetDepot():
    dicDepot = {}
    dicOlv = GetMatriceDepots()
    dlg = xgtr.DLG_tableau(None,dicOlv=dicOlv)
    ret = dlg.ShowModal()
    if ret == wx.OK:
        donnees = dlg.GetSelection().donnees
        for ix in range(len(donnees)):
            dicDepot[dicOlv['listeCodesColonnes'][ix]] = donnees[ix]
    dlg.Destroy()
    return dicDepot

#------------------------ Lanceur de test  -------------------------------------------
def OnClick(event):
    print("on click")
    #mydialog.Close()

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    #print(GetBanquesNne())
    #print(GetFamille(None))
    #print(GetPayeurs(1))
    #art = Article('debour')
    #print(art.GetArticle())
    print(GetDepot())
    app.MainLoop()