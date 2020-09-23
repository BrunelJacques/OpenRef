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

    def GetAnalytique(self,**kwd):
        # choix d'un code analytique, retourne un dict, mode:'auto' automatisme d'affectation, f4 force écran
        mode = kwd.pop('mode',None)
        axe = kwd.pop('axe',None)
        filtre = kwd.pop('filtre',None)
        getAnalytiques = kwd.pop('getAnalytiques', None)

        lstNomsColonnes = ['IDanalytique', 'abrégé', 'nom']
        lstChamps = ['cpta_analytiques.IDanalytique', 'cpta_analytiques.abrege', 'cpta_analytiques.nom']
        lstTypes = ['varchar(8)', 'varchar(8)', 'varchar(32)']
        lstCodesColonnes = [xusp.SupprimeAccents(x).lower() for x in lstNomsColonnes]

        if not mode: mode = 'normal'
        dicAnalytique = None
        nb = 0
        # Test préalable sur début de clé seulement
        if filtre and len(filtre)>0:
            # déroule les champs progresivement, jusqu'à trouver un item unique
            for ix in range(len(lstChamps)):
                kwd['whereFiltre']  = """
                    AND (%s LIKE '%s%%' )"""%(lstChamps[ix],filtre)

                ltAnalytiques = getAnalytiques(lstChamps=lstChamps,**kwd)
                nb = len(ltAnalytiques)
                if nb == 1:
                    dicAnalytique={}
                    for ix in range(len(ltAnalytiques[0])):
                        dicAnalytique[lstCodesColonnes[ix]] = ltAnalytiques[0][ix]
                    break
                elif nb > 1:
                    break
        if (mode.lower() in ('auto')): return dicAnalytique
        if dicAnalytique and mode.lower() == 'normal':  return dicAnalytique

        # le filtre semble trop sélectif pour un f4 on le supprime
        if nb == 0: filtre = None
        # un item unique n'a pas été trouvé on affiche les choix possibles
        getDonnees = getAnalytiques
        dicOlv = self.GetMatriceAnalytiques(axe,lstChamps,lstNomsColonnes,lstTypes,getDonnees)
        dicOlv['largeur'] = 400
        dlg = xgtr.DLG_tableau(self,dicOlv=dicOlv, db=self.db)
        if filtre and len(filtre)>0:
            dlg.ctrlOlv.Parent.barreRecherche.SetValue(filtre)
            dlg.ctrlOlv.Filtrer(filtre)
        ret = dlg.ShowModal()
        if ret == wx.OK:
            donnees = dlg.GetSelection().donnees
            dicAnalytique = {}
            for ix in range(len(donnees)):
                dicAnalytique[dicOlv['listeCodesColonnes'][ix]] = donnees[ix]
        dlg.Destroy()
        return dicAnalytique

    def GetAnalytiques(self,lstChamps=None,**kwd):
        reqFrom = kwd.pop('reqFrom','')
        reqWhere = kwd.pop('reqWhere','')

        # retourne un recordset de requête (liste de tuples)
        ltAnalytiques = []
        champs = ",".join(lstChamps)
        req = """SELECT %s
                %s
                %s
                GROUP BY %s;
                """%(champs,reqFrom,reqWhere,champs)
        retour = self.db.ExecuterReq(req, mess='UTILS_Noegest.GetAnalytiques')
        if retour == "ok":
            ltAnalytiques = self.db.ResultatReq()
        return ltAnalytiques

    def zzGetVehicule(self,filtre=None,mute=False):
        # choix d'un véhicule et retour de son dict, mute sert pour automatisme d'affectation
        dicVehicule = None
        axe = 'VEHICULES'
        lstChamps = ['cpta_analytiques.IDanalytique', 'cpta_analytiques.abrege', 'cpta_analytiques.nom',
                     'vehiculesCouts.prixKmVte']
        lstNomsColonnes = ['IDanalytique','abrege','nom','prixKmVte']
        lstTypes = ['varchar(8)','varchar(8)','varchar(32)','float']
        lstCodesColonnes = [xusp.SupprimeAccents(x).lower() for x in lstNomsColonnes]
        # Test préalable sur début de clé seulement
        if filtre:
            whereFiltre = """
                            AND ((cpta_analytiques.IDanalytique LIKE '%s%%')
                            OR (cpta_analytiques.abrege LIKE '%s%%')) """ % (filtre, filtre,)

            ltVehicules = self.GetVehicules(lstChamps=lstChamps[:1],whereFiltre=whereFiltre)
            if len(ltVehicules) == 1:
                dicVehicule={}
                for ix in range(len(lstCodesColonnes)):
                    dicVehicule[lstCodesColonnes[ix]] = ltVehicules[0][ix]
            if mute or dicVehicule: return dicVehicule
        # un item unique n'a pas été trouvé on affiche les choix possibles
        getDonnees = self.GetVehicules
        dicOlv = self.GetMatriceAnalytiques(axe,lstChamps,lstNomsColonnes,lstTypes,getDonnees)
        dicOlv['largeur'] = 400
        dlg = xgtr.DLG_tableau(self,dicOlv=dicOlv, db=self.db)
        if len(filtre)>0:
            dlg.ctrlOlv.Parent.barreRecherche.SetValue(filtre)
            dlg.ctrlOlv.Filtrer(filtre)
        ret = dlg.ShowModal()
        if ret == wx.OK:
            donnees = dlg.GetSelection().donnees
            dicVehicule = {}
            for ix in range(len(donnees)):
                dicVehicule[dicOlv['listeCodesColonnes'][ix]] = donnees[ix]
        dlg.Destroy()
        return dicVehicule

    def zzGetVehicules(self,lstChamps=None,filtre=None,**kwd):
        matriceOlv = kwd.pop('matriceOlv',{})
        whereFiltre = kwd.pop('whereFiltre','')
        # retourne un recordset de requête (liste de tuples)
        ltVehicules = []
        # matrice Olv est envoyé par la saisie d'un filtre dans la barre de recherche
        if (not lstChamps) and 'listeChamps' in matriceOlv:
            lstChamps = matriceOlv['listeChamps']
        # where filtre permet de personnaliser la recherche
        if filtre and not whereFiltre:
            whereFiltre = """
                AND ((cpta_analytiques.IDanalytique LIKE '%%%s%%')
                OR (cpta_analytiques.abrege LIKE '%%%s%%')
                OR (cpta_analytiques.nom LIKE '%%%s%%')) """ % (filtre, filtre, filtre, )

        where = """
                WHERE (cpta_analytiques.axe = 'VEHICULES') %s
                AND (vehiculesCouts.cloture = '%s') """%(whereFiltre,xformat.DateIsoToSql(self.cloture))

        champs = ",".join(lstChamps)
        req = """
                SELECT %s
                FROM    cpta_analytiques   
                        LEFT JOIN vehiculesCouts ON cpta_analytiques.IDanalytique = vehiculesCouts.IDanalytique
                %s
                GROUP BY %s;
                """%(champs,where,champs)
        retour = self.db.ExecuterReq(req, mess='UTILS_Noegest.GetVehicules')
        if retour == "ok":
            ltVehicules = self.db.ResultatReq()
        return ltVehicules

    def GetVehicule(self,filtre='', mode=None):
        # choix d'une activité et retour de son dict, mute sert pour automatisme d'affectation
        kwd = {
            'axe': 'VEHICULES',
            'mode' : mode,
            'filtre' : filtre,
            'getAnalytiques': self.GetVehicules}
        dicVehicule = self.GetAnalytique(**kwd)
        return dicVehicule

    def GetVehicules(self,lstChamps=None,**kwd):
        # matriceOlv et filtre résultent d'une saisie en barre de recherche
        matriceOlv = kwd.pop('matriceOlv',{})
        if (not lstChamps) and 'listeChamps' in matriceOlv:
            lstChamps = matriceOlv['listeChamps']
        filtre = kwd.pop('filtre','')
        kwd['filtre'] = filtre
        whereFiltre = kwd.pop('whereFiltre','')
        if len(whereFiltre) == 0 and len(filtre)>0:
            whereFiltre = self.ComposeWhereFiltre(filtre,lstChamps)
        kwd['reqWhere'] = """
                WHERE (cpta_analytiques.axe = 'VEHICULES')
                AND (vehiculesCouts.cloture = '%s') %s"""%(xformat.DateIsoToSql(self.cloture),whereFiltre)
        kwd['reqFrom'] = """
                FROM    cpta_analytiques   
                LEFT JOIN vehiculesCouts ON cpta_analytiques.IDanalytique = vehiculesCouts.IDanalytique"""
        return self.GetAnalytiques(lstChamps,**kwd)

    def GetActivite(self,filtre='', mode=None):
        # choix d'une activité et retour de son dict, mute sert pour automatisme d'affectation
        kwd = {
            'axe': 'ACTIVITES',
            'mode' : mode,
            'filtre' : filtre,
            'getAnalytiques': self.GetActivites}
        dicActivite = self.GetAnalytique(**kwd)
        return dicActivite

    def GetActivites(self,lstChamps=None,**kwd):
        # matriceOlv et filtre résultent d'une saisie en barre de recherche
        matriceOlv = kwd.pop('matriceOlv',{})
        if (not lstChamps) and 'listeChamps' in matriceOlv:
            lstChamps = matriceOlv['listeChamps']
        filtre = kwd.pop('filtre','')
        kwd['filtre'] = filtre
        whereFiltre = kwd.pop('whereFiltre','')
        if len(whereFiltre) == 0 and len(filtre)>0:
            whereFiltre = self.ComposeWhereFiltre(filtre,lstChamps)
        kwd['reqWhere'] = """
            WHERE cpta_analytiques.axe = 'ACTIVITES' %s
            """%(whereFiltre)
        kwd['reqFrom'] = """
            FROM cpta_analytiques"""
        return self.GetAnalytiques(lstChamps,**kwd)

    def ComposeWhereFiltre(self,filtre,lstChamps):
        whereFiltre = ''
        if filtre and len(filtre) > 0:
            texte = ''
            ordeb = """
                    ("""
            for ix in range(len(lstChamps)):
                texte += "%s %s LIKE '%%%s%%' )"%(ordeb,lstChamps[ix],filtre)
                ordeb = """
                    OR ("""
            whereFiltre = """
                AND ( %s )"""%(texte)
        return whereFiltre
    
#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    ngest = Noegest()
    ngest.cloture = '2020-09-30'
    print(ngest.GetVehicules(lstChamps=['abrege']))
    app.MainLoop()