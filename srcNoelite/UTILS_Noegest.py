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
import xpy.xGestionDB               as xdb
import srcNoelite.UTILS_Historique  as nuh
import xpy.xGestion_TableauRecherche as xgtr
import xpy.outils.xformat           as xfor
import datetime


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

    # IDreglement manquant
    if track.IDreglement in (None,0) :
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
        ret = db.ReqDEL("reglements", "IDreglement", track.IDreglement,affichError=False)
        if track.ligneValide:
            # --- Mémorise l'action dans l'historique ---
            if ret == 'ok':
                IDcategorie = 8
                categorie = "Suppression"
                nuh.InsertActions([{
                    "IDfamille": track.IDfamille,
                    "IDcategorie": IDcategorie,
                    "action": "Noelite %s du règlement ID%d"%(categorie, track.IDreglement),
                    },],db=db)

        db.ReqDEL("ventilation", "IDreglement", track.IDreglement)

    return

class Noegest(object):
    def __init__(self,parent=None):
        self.db = xdb.DB()

    def GetExercices(self):
        return []

#------------------------ Lanceur de test  -------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    app.MainLoop()