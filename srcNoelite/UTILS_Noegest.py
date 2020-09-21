#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    NoeLITE, gestion des contrepassations analytiques
# Usage : Ensemble de fonctions pour km, stocks, retrocessions
# Auteur:          Jacques BRUNEL
# Copyright:       (c) 2020-04   Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import datetime
import srcNoelite.UTILS_Historique  as nuh
from xpy.outils import xformat
from xpy        import xGestionDB
import xpy.xGestion_TableauEditor   as xgte
import xpy.xGestion_TableauRecherche as xgtr
import xpy.xUTILS_SaisieParams       as xusp

def ValideLigne(db,track):
    track.ligneValide = True
    track.messageRefus = "Saisie incomplète\n\n"

    # vérification des éléments saisis

    # montant null
    try:
        track.montant = float(track.montant)
    except:
        track.montant = None
    if not track.montant or track.montant == 0.0:
        track.messageRefus += "Le montant est à zéro\n"

    # IDligne manquant
    if track.IDligne in (None,0) :
        track.messageRefus += "L'ID reglement n'est pas été déterminé à l'entrée du montant\n"

    # Date
    if not track.date or not isinstance(track.date,(wx.DateTime,datetime.date)):
        track.messageRefus += "Vous devez obligatoirement saisir une date d'émission du règlement !\n"

    # Mode
    if not track.mode or len(track.mode) == 0:
        track.messageRefus += "Vous devez obligatoirement sélectionner un mode de règlement !\n"

    # Numero de piece
    if track.mode[:3].upper() == 'CHQ':
        if not track.numero or len(track.numero)<4:
            track.messageRefus += "Vous devez saisir un numéro de chèque 4 chiffres mini!\n"
        # libelle pour chèques
        if track.libelle == '':
            track.messageRefus += "Veuillez saisir la banque émettrice du chèque dans le libellé !\n"

    # Payeur
    if track.payeur == None:
        track.messageRefus += "Vous devez obligatoirement sélectionner un payeur dans la liste !\n"

    # envoi de l'erreur
    if track.messageRefus != "Saisie incomplète\n\n":
        track.ligneValide = False
    else: track.messageRefus = ""
    return

def SauveLigne(db,dlg,track):
    if not track.ligneValide:
        return False
    if not track.montant or not isinstance(track.montant,float):
        return False
    # --- Sauvegarde des différents éléments associés à la ligne ---
    message = ''
    ret = None
    if len(message)>0: wx.MessageBox(message)
    return ret

def DeleteLigne(db,track):
    # --- Supprime les différents éléments associés à la ligne ---
    # si le montant est à zéro il n'y a pas eu d'enregistrements
    if track.montant != 0.0:
        # suppression  du réglement et des ventilations
        ret = db.ReqDEL("reglements", "IDligne", track.IDligne,affichError=False)
        if track.ligneValide:
            # --- Mémorise l'action dans l'historique ---
            if ret == 'ok':
                IDcategorie = 8
                categorie = "Suppression"
                nuh.InsertActions([{
                    "IDfamille": track.IDfamille,
                    "IDcategorie": IDcategorie,
                    "action": "Noelite %s du règlement ID%d"%(categorie, track.IDligne),
                    },],db=db)

        db.ReqDEL("ventilation", "IDligne", track.IDligne)

    return

def GetClotures():
    noegest = Noegest()
    lClotures = [x for y,x in noegest.GetExercices()]
    del noegest
    return lClotures


class Noegest(object):
    def __init__(self,parent=None):
        self.db = xGestionDB.DB()
        self.cloture = None
        self.ltExercices = None

    def GetExercices(self,where='WHERE  actif = 1'):
        if self.ltExercices : return self.ltExercices
        self.ltExercices = []
        lstChamps = ['date_debut', 'date_fin']
        req = """   SELECT %s
                    FROM cpta_exercices
                    %s                   
                    """ % (",".join(lstChamps),where)
        retour = self.db.ExecuterReq(req, mess='UTILS_Noegest.GetExercices')
        if retour == "ok":
            recordset = self.db.ResultatReq()
            if len(recordset) == 0:
                wx.MessageBox("Aucun exercice n'est paramétré")
            for debut,fin in recordset:
                self.ltExercices.append((xformat.DateSqlToIso(debut),xformat.DateSqlToIso(fin)))
        return self.ltExercices

    def GetMatriceAnalytiques(self,axe,lstChamps,lstNomsColonnes,lstTypes,getDonnees):
        dicBandeau = {'titre': "Choix d'un code analytique: %s"%str(axe),
                      'texte': "les mots clés du champ en bas permettent de filtrer les lignes et d'affiner la recherche",
                      'hauteur': 15, 'nomImage': "xpy/Images/32x32/Matth.png"}

        # Composition de la matrice de l'OLV Analytiques, retourne un dictionnaire

        lstCodesColonnes = [xusp.SupprimeAccents(x).lower() for x in lstNomsColonnes]
        lstValDefColonnes = xgte.ValeursDefaut(lstNomsColonnes, lstTypes)
        lstLargeurColonnes = xgte.LargeursDefaut(lstNomsColonnes, lstTypes,IDcache=False)
        lstColonnes = xusp.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
        return {
            'listeColonnes': lstColonnes,
            'listeChamps': lstChamps,
            'listeNomsColonnes': lstNomsColonnes,
            'listeCodesColonnes': lstCodesColonnes,
            'getDonnees': getDonnees,
            'dicBandeau': dicBandeau,
            'colonneTri': 1,
            'sensTri': False,
            'style': wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES,
            'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
        }

    def GetVehicule(self):
        # appel des véhicules existants
        dicVehicule = {}
        axe = 'VEHICULES'
        lstChamps = ['cpta_analytiques.IDanalytique', 'cpta_analytiques.abrege', 'cpta_analytiques.nom',
                     'vehiculesCouts.prixKmVte']
        lstNomsColonnes = ['abrege','IDanalytique','nom','prixKmVte']
        lstTypes = ['varchar(8)','varchar(8)','varchar(32)','float']
        getDonnees = self.GetVehicules
        dicOlv = self.GetMatriceAnalytiques(axe,lstChamps,lstNomsColonnes,lstTypes,getDonnees)
        dicOlv['largeur'] = 400
        dlg = xgtr.DLG_tableau(self,dicOlv=dicOlv, db=self.db)
        ret = dlg.ShowModal()
        if ret == wx.OK:
            donnees = dlg.GetSelection().donnees
            for ix in range(len(donnees)):
                dicVehicule[dicOlv['listeCodesColonnes'][ix]] = donnees[ix]
        dlg.Destroy()
        return dicVehicule

    def GetVehicules(self,matriceOlv=None,lstChamps=None,filtre=None,**kwd):
        ltVehicules = []
        if not lstChamps:
            lstChamps = matriceOlv['listeChamps']
        where = "WHERE (cpta_analytiques.axe = 'VEHICULES')"
        if filtre:
            where = """ AND (cpta_analytiques.IDanalytique LIKE '%%%s%%'
                            OR cpta_analytiques.abrege LIKE '%%%s%%'
                            OR cpta_analytiques.nom '%%%s%%') """ % (filtre, filtre, filtre, )

        where += " AND (vehiculesCouts.cloture = '%s') "%xformat.DateIsoToSql(self.cloture)

        req = """SELECT %s
                FROM cpta_analytiques LEFT JOIN vehiculesCouts ON cpta_analytiques.IDanalytique = vehiculesCouts.IDanalytique
                %s;
                """%(",".join(lstChamps),where)
        retour = self.db.ExecuterReq(req, mess='UTILS_Noegest.GetVehicules')
        if retour == "ok":
            ltVehicules = self.db.ResultatReq()
        return ltVehicules

    def GetActivite(self):
        # appel des activités existantes
        dicActivite = {}
        axe = 'ACTIVITES'
        lstChamps = ['cpta_analytiques.IDanalytique', 'cpta_analytiques.abrege', 'cpta_analytiques.nom']
        lstNomsColonnes = ['abrege','IDanalytique','nom']
        lstTypes = ['varchar(8)','varchar(8)','varchar(32)']
        getDonnees = self.GetActivites
        dicOlv = self.GetMatriceAnalytiques(axe,lstChamps,lstNomsColonnes,lstTypes,getDonnees)
        dicOlv['largeur'] = 400
        dlg = xgtr.DLG_tableau(self,dicOlv=dicOlv, db=self.db)
        ret = dlg.ShowModal()
        if ret == wx.OK:
            donnees = dlg.GetSelection().donnees
            for ix in range(len(donnees)):
                dicActivite[dicOlv['listeCodesColonnes'][ix]] = donnees[ix]
        dlg.Destroy()
        return dicActivite

    def GetActivites(self,db=None,matriceOlv=None,filtre=None):
        # db dans le param est inutile ici, mais il doit être réceptionné car d'autres modules l'utilisent
        ltActivites = []
        lstChamps = matriceOlv['listeChamps']
        where = "WHERE (cpta_analytiques.axe = 'ACTIVITES')"
        if filtre:
            where = """ AND (cpta_analytiques.IDanalytique LIKE '%%%s%%'
                            OR cpta_analytiques.abrege LIKE '%%%s%%'
                            OR cpta_analytiques.nom '%%%s%%') """ % (filtre, filtre, filtre, )

        req = """SELECT %s
                FROM cpta_analytiques
                %s;
                """%(",".join(lstChamps),where)
        retour = self.db.ExecuterReq(req, mess='UTILS_Noegest.GetActivites')
        if retour == "ok":
            ltActivites = self.db.ResultatReq()
        return ltActivites


#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    ngest = Noegest()
    ngest.cloture = '2020-09-30'
    print(ngest.GetVehicules(lstChamps=['abrege']))
    app.MainLoop()