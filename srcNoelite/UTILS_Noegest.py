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

def GetClotures():
    noegest = Noegest()
    lClotures = [x for y,x in noegest.GetExercices()]
    del noegest
    return lClotures

class Noegest(object):
    def __init__(self,parent=None):
        self.parent = parent
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

    def GetMatriceAnalytiques(self,axe,lstChamps,lstNomsCol,lstTypes,getDonnees):
        dicBandeau = {'titre': "Choix d'un code analytique: %s"%str(axe),
                      'texte': "les mots clés du champ en bas permettent de filtrer les lignes et d'affiner la recherche",
                      'hauteur': 15, 'nomImage': "xpy/Images/32x32/Matth.png"}

        # Composition de la matrice de l'OLV Analytiques, retourne un dictionnaire

        lstCodesColonnes = [xusp.SupprimeAccents(x).lower() for x in lstNomsCol]
        lstValDefColonnes = xgte.ValeursDefaut(lstNomsCol, lstTypes)
        lstLargeurColonnes = xgte.LargeursDefaut(lstNomsCol, lstTypes,IDcache=False)
        lstColonnes = xusp.DefColonnes(lstNomsCol, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
        return {
            'listeColonnes': lstColonnes,
            'listeChamps': lstChamps,
            'listeNomsColonnes': lstNomsCol,
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
        lstNomsCol = kwd.pop('lstNomsCol',['IDanalytique', 'abrégé', 'nom'])
        lstChamps = kwd.pop('lstChamps',['cpta_analytiques.IDanalytique', 'cpta_analytiques.abrege', 'cpta_analytiques.nom'])
        lstTypes = kwd.pop('lstTypes',['varchar(8)', 'varchar(8)', 'varchar(32)'])
        lstCodesColonnes = [xusp.SupprimeAccents(x).lower() for x in lstNomsCol]

        if not mode: mode = 'normal'
        dicAnalytique = None
        nb = 0
        # Test préalable sur début de clé seulement
        if filtre and len(str(filtre))>0:
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
        dicOlv = self.GetMatriceAnalytiques(axe,lstChamps,lstNomsCol,lstTypes,getDonnees)
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

    def GetVehicule(self,filtre='', mode=None):
        # choix d'une activité et retour de son dict, mute sert pour automatisme d'affectation
        kwd = {
            'axe': 'VEHICULES',
            'mode' : mode,
            'filtre' : filtre,
            'getAnalytiques': self.GetVehicules,
            'lstNomsCol': ['IDanalytique', 'abrégé', 'nom','prix'],
            'lstChamps': ['cpta_analytiques.IDanalytique', 'cpta_analytiques.abrege', 'cpta_analytiques.nom',
                          'vehiculesCouts.prixKmVte'],
            'lstTypes': ['varchar(8)', 'varchar(8)', 'varchar(32)','float'],
            }
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

    def SetConso(self,track):
        dlg = self.parent
        # --- Sauvegarde de la ligne consommation ---
        dteFacturation = self.GetParam('filtre','datefact')
        listeDonnees = [
            ("IDconso", track.IDconso),
            ("IDanalytique", track.IDvehicule),
            ("cloture", xformat.DateIsoToSql(self.cloture)),
            ("typeTiers", track.typetiers),
            ("IDtiers", track.IDtiers),
            ("dteKmDeb", xformat.DatetimeToStr(track.dtkmdeb,iso=True)),
            ("kmDeb", track.kmdeb),
            ("dteKmFin", xformat.DatetimeToStr(track.dtkmfin,iso=True)),
            ("kmFin", track.kmfin),
            ("observation", track.observation),
            ("dtFact", xformat.DateIsoToSql(dteFacturation)),
            ("dtMaj", xformat.DatetimeToStr(datetime.date.today(),iso=True)),
            ("user", dlg.IDutilisateur),
            ]

        if not track.IDconso or track.IDconso == 0:
            ret = self.db.ReqInsert("vehiculesConsos",lstDonnees= listeDonnees, mess="UTILS_Noegest.SetConso")
            track.IDconso = self.db.newID
            IDcategorie = 6
            categorie = ("Saisie")
        else:
            ret = self.db.ReqMAJ("vehiculesConsos", listeDonnees, "IDconso", track.IDconso)
            IDcategorie = 7
            categorie = "Modification"

        # --- Mémorise l'action dans l'historique ---
        if ret == 'ok':
            nuh.InsertActions([{
                                "IDcategorie": IDcategorie,
                                "action": "Noelite %s de la conso ID%d : %s %s %s" % (
                                categorie, track.IDconso, track.nomvehicule,track.nomtiers,track.observation,),
                                }, ],db=self.db)
        return True

    def ValideLigne(self, track):
        track.ligneValide = True
        track.messageRefus = "Saisie incomplète\n\n"
        # vérification des éléments saisis
        try:
            track.conso = int(track.conso)
        except:
            track.conso = None
        if not track.conso or track.conso == 0:
            track.messageRefus += "Le nombre de km consommés est à zéro\n"

        # DateKmDeb
        if not xformat.DateIsoToSql(track.dtkmdeb) :
            track.messageRefus += "Vous devez obligatoirement saisir une date de début !\n"

        # véhicule
        if track.IDvehicule == None:
            track.messageRefus += "Vous devez obligatoirement sélectionner un véhicle reconnu !\n"

        # activité
        if track.typetiers == 'A' and (not track.IDtiers or len(str(track.IDtiers))==0):
            track.messageRefus += "Vous devez obligatoirement sélectionner une activité !\n"
        if (not track.nomtiers or len(str(track.nomtiers))==0):
            track.messageRefus += "Vous devez obligatoirement sélectionner un nom de tiers ou d'activité !\n"

        # envoi de l'erreur
        if track.messageRefus != "Saisie incomplète\n\n":
            track.ligneValide = False
        else:
            track.messageRefus = ""
        return

    def SauveLigne(self,track):
        if not track.ligneValide:
            return False
        if not track.montant or not isinstance(track.montant,float):
            return False
        # gestion de la consommation
        ret = self.SetConso(track)
        if ret != 'ok':
            wx.MessageBox(ret)
        return ret

    def DeleteLigne(self,track):
        db = self.db
        # si la vameir conso est à zéro il n'y a pas eu d'enregistrements
        if track.montant != 0.0:
            # suppression  de la consommation et des ventilations
            ret = db.ReqDEL("vehiculesConsos", "IDconso", track.IDligne,affichError=False)
            if track.ligneValide:
                # --- Mémorise l'action dans l'historique ---
                if ret == 'ok':
                    IDcategorie = 8
                    categorie = "Suppression"
                    nuh.InsertActions([{
                        "IDcategorie": IDcategorie,
                        "action": "Noelite %s de conso km véhicule ID%d"%(categorie, track.IDligne),
                        },],db=db)
        return

    def GetParam(self,cat,name):
        valeur = None
        dicParams = self.parent.pnlParams.GetValeurs()
        if cat in dicParams:
            if name in dicParams[cat]:
                valeur = dicParams[cat][name]
        return valeur

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    ngest = Noegest()
    ngest.cloture = '2020-09-30'
    print(ngest.GetVehicules(lstChamps=['abrege']))
    app.MainLoop()