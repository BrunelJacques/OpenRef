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
import xpy.xUTILS_SaisieParams      as xusp

def GetDicOlvFamilles(filtre = None, limit=40):
    # appel des données à afficher
    where = ""
    if filtre:
        where = """WHERE familles.adresse_intitule LIKE '%%%s%%'
                        OR individus_1.ville_resid LIKE '%%%s%%'
                        OR individus.nom LIKE '%%%s%%'
                        OR individus.prenom LIKE '%%%s%%' """%(filtre,filtre,filtre,filtre,)

    lstChamps = ['0','familles.IDfamille','familles.adresse_intitule','individus_1.cp_resid','individus_1.ville_resid',
                 'rattachements.IDcategorie','individus.nom','individus.prenom']

    lstNomsColonnes = ["0","famille","désignation","cp","ville",
                 "categ","nom","prenom"]

    lstTypes = ['INTEGER','INTEGER','VARCHAR(100)','VARCHAR(3)','VARCHAR(100)',
                'INTEGER','VARCHAR(100)','VARCHAR(80)']
    db = xdb.DB()
    req = """   SELECT %s 
                FROM ((familles 
                LEFT JOIN rattachements ON familles.IDfamille = rattachements.IDfamille) 
                LEFT JOIN individus ON rattachements.IDindividu = individus.IDindividu) 
                LEFT JOIN individus AS individus_1 ON familles.adresse_individu = individus_1.IDindividu
                %s
                LIMIT %d ;""" % (",".join(lstChamps),where,limit)
    retour = db.ExecuterReq(req, mess='GetIndividus' )
    if retour == "ok":
        recordset = db.ResultatReq()
    db.Close()
    lstCodesColonnes = [xusp.SupprimeAccents(x) for x in lstNomsColonnes]
    lstValDefColonnes = xgte.ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = xgte.LargeursDefaut(lstNomsColonnes, lstTypes)

    # composition des données du tableau à partir du recordset, regroupement par famille
    lstDonnees = []
    for record in recordset:
        ligne = xgte.ComposeLstDonnees( record, lstChamps)
        lstDonnees.append(ligne)

    # matrice OLV
    lstColonnes = xusp.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
    dicOlv =    {
                'listeColonnes': lstColonnes,
                'listeDonnees': lstDonnees,
                'checkColonne': False,
                'colonneTri': 1,
                'style': wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                }
    return dicOlv

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


#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    #print(GetBanquesNne())
    import xpy.xGestion_Tableau as xgt
    dlg = xgt.DLG_tableau(None,dicOlv=GetDicOlvFamilles())
    dlg.ShowModal()
    app.MainLoop()
