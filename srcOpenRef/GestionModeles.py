#!/usr/bin/env python
# -*- coding: utf8 -*-

#------------------------------------------------------------------------
# Application :    OpenRef, Gestion des tables modèlel, variables etc
# Auteurs:          Jacques BRUNEL
# Copyright:       (c) 2019-10     Cerfrance Provence
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import datetime
import srcOpenRef.DATA_Tables as dtt
import xpy.xGestionDB as xdb
import xpy.xUTILS_SaisieParams as xusp
import xpy.xGestion_Tableau as xgt
import xpy.xGestion_Ligne as xgl
import xpy.outils.xdatatables as xdtt
from xpy.outils     import xformat

class EcranOlv(object):
    def __init__(self, parent,nomtable='',dbtable=None,title=None):
        self.table = nomtable
        self.echec = True
        if not title:
            listArbo = os.path.abspath(__file__).split("\\")
            title = '%s.%s'%(listArbo[-1:][0], self.__class__.__name__)
        self.title = title
        self.ixsel = 0
        # initialisation des propriétés de la table
        self.lstTblChamps, self.lstTblTypes, self.lstTblHelp = [],[],[]
        if dbtable:
            self.lstTblChamps, self.lstTblTypes, self.lstTblHelp = xdtt.GetChampsTypes(dbtable, tous=True)
            self.lstTblValdef = xformat.ValeursDefaut(self.lstTblChamps, self.lstTblTypes)
            self.lstLargeurColonnes = xformat.LargeursDefaut(self.lstTblChamps, self.lstTblTypes)
        else:
            self.lstTblChamps = ['*']
            self.lstTblValdef = []
        self.lstTblCodes = [xformat.SupprimeAccents(x) for x in self.lstTblChamps]
 
        self.req = "SELECT * FROM %s;"%(self.table)
        ret = self.InitSql()
        if ret == "ok": self.echec = False

    def InitSql(self):
        self.lstReqChamps = self.lstTblChamps
        self.lstReqCodes = [xformat.SupprimeAccents(x) for x in self.lstReqChamps]
        self.DBsql = xdb.DB()
        retour = "ko"
        if self.DBsql.echec == 0:
            self.recordset = ()
            retour = self.DBsql.ExecuterReq(self.req, mess='GestionModeles.EcranOlv\n\n%s'%self.req)
            if retour == "ok":
                self.recordset = self.DBsql.ResultatReq()
                if len(self.recordset) == 0:
                    retour = "aucun enregistrement disponible"
            if (not retour == "ok"):
                wx.MessageBox("Erreur : %s" % retour)
                return 'ko'
        if retour == 'ok':
            self.InitMatrice(largeurs=self.lstLargeurColonnes)
        return retour

    def InitMatrice(self,champsCol=[],valdef=[],largeurs=[],hauteur=650,largeur=1300,footer=None):
        if len(self.lstTblChamps) == 0: self.lstTblChamps = self.lstReqChamps
        
        # les champs col sont les noms de colonne transposés en valeur éventuelle de champs de requête à mettre à jour
        self.lstColChamps = champsCol
        if len(champsCol) == 0: self.lstColChamps = self.lstReqChamps

        self.lstColCodes = [xformat.SupprimeAccents(x) for x in self.lstTblChamps]
        self.lstColValDef = valdef
        if len(valdef) < len(self.lstColChamps):
            self.lstColValDef.extend([''* (len(self.lstColChamps)-len(valdef))])
        self.lstColLargeurs = largeurs
        if not footer:
            footer = {self.lstColCodes[1]: {"mode": "nombre", "alignement": wx.ALIGN_CENTER},}

        lstDonnees = []
        ix = 0
        # composition des données du tableau à partir du recordset
        for record in self.recordset:
            ligne = []
            for champ in self.lstColChamps:
                val = None
                if champ in self.lstReqChamps:
                    val = record[self.lstReqChamps.index(champ)]
                else:
                    if champ == 'ix':
                        val = ix
                    else: 
                        wx.MessageBox("Impossible de trouver la valeur du champ '%s'"%champ)
                ligne.append(val)
            lstDonnees.append(ligne)
            ix += 1
        # matrice OLV
        lstColonnes = xformat.DefColonnes(self.lstTblChamps, self.lstColCodes, self.lstColValDef, self.lstColLargeurs)
        self.dicOlv = {
            'lanceur': self,
            'listeColonnes': lstColonnes,
            'listeDonnees': lstDonnees,
            'checkColonne': False,
            'hauteur': hauteur,
            'largeur': largeur,
            'recherche': True,
            'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
            'dictColFooter': footer
            }
        self.lstDonnees = lstDonnees

        # options d'enrichissement de l'écran DLG
        self.lstBtns = [('BtnOK', wx.ID_OK, wx.Bitmap("xpy/Images/100x30/Bouton_fermer.png", wx.BITMAP_TYPE_ANY),
                    "Cliquez ici pour fermer la fenêtre")]
        # params d'actions: idem boutons, ce sont des boutons placés à droite et non en bas
        self.lstActions = [('ajout', wx.ID_APPLY, 'Ajouter', "Ajouter une nouvelle ligne"),
                      ('modif', wx.ID_APPLY, 'Modifier', "Modifier les propriétés de la ligne pour le dossier"),
                      ('suppr', wx.ID_APPLY, 'Supprimer', "Supprimer la ligne dans le dossier"),
                      ]
        # un param par info: texte ou objet window.  Les infos sont  placées en bas à gauche
        self.lstInfos = [self.title]
        # params des actions ou boutons: name de l'objet, fonction ou texte à passer par eval()
        self.dicOnClick = {
            'ajout': 'self.lanceur.OnAjouter()',
            'modif': 'self.lanceur.OnModif()',
            'suppr': 'self.lanceur.OnSupprimer()'}


    def InitEcran(self):
        self.dlgolv = xgt.DLG_tableau(self, dicOlv=self.dicOlv, lstBtns=self.lstBtns, lstActions=self.lstActions,
                                      lstInfos=self.lstInfos,dicOnClick=self.dicOnClick)
        # l'objet ctrlolv pourra être appelé, il sert de véhicule à params globaux de l'original
        self.ctrlolv = self.dlgolv.ctrlOlv
        self.ctrlolv.lstTblHelp = self.lstTblHelp
        self.ctrlolv.lstTblChamps = self.lstTblChamps
        self.ctrlolv.lstTblCodes = [xformat.SupprimeAccents(x) for x in self.lstTblChamps]
        self.ctrlolv.lstTblValdef = self.lstTblValdef
        self.ctrlolv.recordset = self.recordset
        if len(self.lstDonnees) > 0 and len(self.lstDonnees)> self.ixsel:
            # selection de la ligne
            self.ctrlolv.SelectObject(self.ctrlolv.listeDonnees[self.ixsel+1])
        ret = self.dlgolv.ShowModal()
        return ret

    def OnModif(self):
        self.AppelSaisie('modif')
        self.Reinit()

    def OnAjouter(self):
        self.AppelSaisie('ajout')
        self.Reinit()

    def OnSupprimer(self):
        self.AppelSaisie('suppr')
        self.Reinit()

    def Reinit(self):
        self.dlgolv.Close()
        del self.ctrlolv
        self.InitSql()
        self.InitEcran()

    def AppelSaisie(self, mode):
        ctrlolv = self.ctrlolv

        # personnalisation de la grille de saisie : champs à visualiser, position
        if mode == 'ajout':
            ix = 0
        else: ix = 1
        champdeb = self.lstColChamps[ix]
        champfin = self.lstColChamps[-1]
        lstEcrChamps = xusp.ExtractList(self.lstTblChamps,champdeb,champfin)
        lstEcrCodes = [xformat.SupprimeAccents(x) for x in lstEcrChamps]

        kwds = {'pos': (350, 20)}
        kwds['minSize'] = (350, 600)
        all = ctrlolv.innerList
        sel = ctrlolv.Selection()
        if len(sel)>0:
            selection = ctrlolv.Selection()[0]
            self.ixsel = all.index(selection)
        else:
            self.ixsel = 0

        # personnalisation des actions
        dicOptions = {}
        # disable de tous les champs de synthèse

        # lancement de l'écran de saisie
        self.saisie = xgl.Gestion_ligne(self, self.DBsql, self.table, dtt, mode, ctrlolv,**kwds)
        if self.saisie.ok and mode != 'suppr':
            self.saisie.SetBlocGrille(lstEcrCodes,dicOptions,'Gestion des ateliers ouverts')
            if mode == 'ajout':
                # RAZ de toutes les données
                self.saisie.dictDonnees = {}
            self.saisie.InitDlg()
            self.saisie.ShowDlg()
        del self.saisie

    def Validation(self,valeurs):
        return True
    
class Lancement():
    def __init__(self,parent,table):
        if table in dtt.DB_TABLES.keys():
            ecran = EcranOlv(self,nomtable=table,dbtable=dtt.DB_TABLES[table],title='[GestionModeles].Lancement')
            if not ecran.echec:
                ecran.InitEcran()
        else:
            wx.MessageBox("GestionModeles.Lancement:\n\nLa table %s n'est pas décrite dans DB_TABLES, pb programmation"%table)
            return 'ko'

#************************   Pour Test ou modèle  *********************************
if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    ret = Lancement(None,table = 'mProduits')
    print('Retour appli: ',ret)

    app.MainLoop()

