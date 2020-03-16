#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import wx
import xpy.xGestionDB       as xdb

def VerificationDroits(dictUtilisateur=None, categorie="", action="", IDactivite=""):
    """ Vérifie si un utilisateur peut accéder à une action """
    if ((dictUtilisateur == None) or ("droits" in dictUtilisateur)) == False :
        return True
    
    dictDroits = dictUtilisateur["droits"]
    key = (categorie, action)
        
    if (dictDroits != None) and (key in dictDroits) :
        etat = dictDroits[key]
        # Autorisation
        if etat.startswith("autorisation") :
            return True
        # Interdiction
        if etat.startswith("interdiction") :
            return False
        # Restriction
        if etat.startswith("restriction") :
            code = etat.replace("restriction_", "")
            mode, listeID = code.split(":")
            listeID = [int(x) for x in listeID.split(";")]
                        
            if mode == "groupes" :
                if len(listeID) == 1 : condition = "IDtype_groupe_activite=%d" % listeID[0]
                if len(listeID) >1 : condition = "IDtype_groupe_activite IN %s" % str(tuple(listeID))
                DB = xdb.DB()
                req = """SELECT IDgroupe_activite, activites 
                FROM groupes_activites
                WHERE %s;""" % condition
                DB.ExecuterReq(req)
                listeDonnees = DB.ResultatReq()
                listeActivites = []
                for IDgroupe_activite, IDactivite_temp in listeDonnees :
                    listeActivites.append(IDactivite_temp)
                DB.Close()
                
            if mode == "activites" :
                listeActivites = listeID
            
            if IDactivite in listeActivites :
                return True
            else :                
                return False

    return True
    
def VerificationDroitsUtilisateurActuel(categorie="", action="", IDactivite="", afficheMessage=True):
    try :
        topWindow = wx.GetApp().GetTopWindow()
        nomWindow = topWindow.GetName()
    except :
        nomWindow = None
        return True
    if nomWindow == "general" : 
        # Si la frame 'General' est chargée, on y récupère le dict de config
        dictUtilisateur = topWindow.dictUtilisateur
        resultat = VerificationDroits(dictUtilisateur, categorie, action, IDactivite)
        if resultat == True or afficheMessage == True :
            wx.MessageBox( "Votre profil utilisateur ne vous permet pas d'accéder à cette fonctionnalité !")
        return resultat
    return True
    

class CTRL_Bouton_image(wx.Button):
    def __init__(self, parent, id=wx.ID_APPLY, texte="", cheminImage=None):
        wx.Button.__init__(self, parent, id=id, label=texte)
        if cheminImage:
            self.SetBitmap(wx.Bitmap(cheminImage))
        self.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.SetInitialSize()


if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    print(VerificationDroits({'IDutilisateur': 2, 'nom': 'LORIOL', 'prenom': 'Isabelle', 'sexe': 'F', 'mdp': 'lor', 'profil': 'administrateur', 'actif': 1, 'droits': None},
                             "parametrage_modes_reglements", "supprimer"))
    print(VerificationDroitsUtilisateurActuel("parametrage_modes_reglements", "supprimer"))