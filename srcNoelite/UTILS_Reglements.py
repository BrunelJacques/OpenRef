#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noelite, gestion multi-activités
# Auteur:          Jacques BRUNEL
# Copyright:       (c) 2019-04   Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import xpy.xGestionDB               as xdb
import xpy.xGestion_TableauEditor   as xgte
import xpy.xGestion_TableauRecherche as xgtr
import xpy.xUTILS_SaisieParams      as xusp


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

def GetFamille(self):
    dicOlv = GetMatriceFamilles()
    dlg = xgtr.DLG_tableau(None,dicOlv=dicOlv)
    ret = dlg.ShowModal()
    if ret == wx.OK:
        famille = (dlg.GetSelection().donnees[1],dlg.GetSelection().donnees[2])
    else: famille = None
    dlg.Destroy()
    return famille

def GetBanquesNne(where = 'code_nne IS NOT NULL'):
    db = xdb.DB()
    lstBanques = []
    lstChamps = ['IDcompte','nom','defaut','code_nne','iban','bic']
    req = """   SELECT %s
                FROM comptes_bancaires
                WHERE %s
                """ % (",".join(lstChamps),where)
    retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetBanques' )
    if retour == "ok":
        recordset = db.ResultatReq()
        if len(recordset) == 0:
            wx.MessageBox("Aucun banque n'a de compte destination (code Nne) paramétré")
    db.Close()
    for record in recordset:
        dicBanque = {}
        for ix in range(len(lstChamps)):
            dicBanque[lstChamps[ix]] = record[ix]
        lstBanques.append(dicBanque)
    return lstBanques

def GetDesignationFamille(IDfamille):
    db = xdb.DB()
    req = """   SELECT adresse_intitule
                FROM familles
                WHERE IDfamille = %d
                """ % (IDfamille)
    retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetPayeurs' )
    if retour == "ok":
        recordset = db.ResultatReq()
    designation = ''
    for record in recordset:
        designation = record[0]
    db.Close()
    return designation


def GetPayeurs(IDfamille):
    db = xdb.DB()
    lstPayeurs = []
    req = """   SELECT nom
                FROM payeurs
                WHERE IDcompte_payeur = %d
                """ % (IDfamille)
    retour = db.ExecuterReq(req, mess='UTILS_Reglements.GetPayeurs' )
    if retour == "ok":
        recordset = db.ResultatReq()

    for record in recordset:
        lstPayeurs.append(record[0])
    if len(lstPayeurs) == 0:
        lstPayeurs = [GetDesignationFamille(IDfamille),]
    db.Close()
    return lstPayeurs

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    #print(GetBanquesNne())
    #print(GetFamille(None))
    print(GetPayeurs(1))
    app.MainLoop()
