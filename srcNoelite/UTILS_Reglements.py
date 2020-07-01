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

def GetNewIDreglement(lstID):
    # Recherche le prochain ID reglement après ceux de la base et éventuellement déjà dans la liste ID préaffectés
    DB = xdb.DB()
    req = """SELECT MAX(IDreglement) 
            FROM reglements;"""
    DB.ExecuterReq(req)
    recordset = DB.ResultatReq()
    ID = recordset[0][0] + 1
    while ID in lstID:
        ID += 1
    return ID

def ValideLigne(self,track):
    # vérification des éléments saisis
    if not len(GetDesignationFamille(track.IDfamille)) > 0:
        wx.MessageBox("Ligne incomplète\n\nLa famille n'est pas identifiée")
        return False
    if track.montant == 0.0:
        wx.MessageBox("Ligne incomplète\n\nLe montant est à zéro")
        return False
    if track.IDreglement in (None,0) :
        wx.MessageBox("Ligne incomplète\n\nL'ID reglement n'est pas été déterminé à l'entrée du montant")
        return False

    # Date
    if track.date == None or not isinstance(track.date,wx.DateTime):
        dlg = wx.MessageBox( ("Erreur de saisie\n\nVous devez obligatoirement saisir une date d'émission du règlement !"),
                               wx.OK | wx.ICON_EXCLAMATION)
        return False

    # Mode
    if track.mode == None or len(track.mode) == 0:
        dlg = wx.MessageBox( ("Erreur de saisie\n\nVous devez obligatoirement sélectionner un mode de règlement !"),
                               wx.OK | wx.ICON_EXCLAMATION)
        return False

    # Numero de piece
    if track.mode[:3].upper() == 'CHQ':
        if not track.numero or len(track.numero)<4:
            dlg = wx.MessageBox( ("Erreur de saisie\n\nVous devez saisir un numéro de chèque !"),
                               wx.OK | wx.ICON_EXCLAMATION)
        return False

    # Payeur
    if track.payeur == None:
        dlg = wx.MessageBox( ("Erreur de saisie\n\nVous devez obligatoirement sélectionner un payeur dans la liste !"),
                               wx.OK | wx.ICON_EXCLAMATION)
        return False

    # libelle pour chèques
    if track.libelle == '':
        pass
    return True

def SetReglement(dlg,track):
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
    if hasattr(track,'differe'):
        attente = 0
        listeDonnees.append(("date_differe", xfor.DatetimeToStr(track.differe,iso=True)))
        if len(track.differe) > 0:
            attente = 1
        listeDonnees.append(("encaissement_attente",attente))

    DB = xdb.DB()
    if track.IDreglement in dlg.pnlOlv.lstNewReglements:
        nouveauReglement = True
        ret = DB.ReqInsert("reglements",lstDonnees= listeDonnees, mess="UTILS_Reglements.SetReglement")
        dlg.pnlOlv.lstNewReglements.remove(track.IDreglement)
    else:
        nouveauReglement = False
        DB.ReqMAJ("reglements", listeDonnees, "IDreglement", track.IDreglement)
    DB.Close()

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

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    #print(GetBanquesNne())
    #print(GetFamille(None))
    #print(GetPayeurs(1))
    art = Article('debour')
    print(art.GetArticle())
    app.MainLoop()
