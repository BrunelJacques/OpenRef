#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    xref tables génériques
# Auteur:          Jacques Brunel
# Licence:         Licence GNU GPL
#-----------------------------------------------------------
#        ("nomchamp",  'type', 'complements', "commentaire"),

DB_TABLES =   {
    "utilisateurs": [
            ("IDutilisateur", "INTEGER PRIMARY KEY AUTOINCREMENT", None, u"IDutilisateur"),
            ("login", "VARCHAR(32)","NOT NULL DEFAULT ' '", u"Login de l'utilisateur"),
            ("nom", "VARCHAR(200)", "NOT NULL DEFAULT ' '", u"Nom de l'utilisateur"),
            ("prenom", "VARCHAR(200)", "DEFAULT ' '", u"Prénom de l'utilisateur"),
            ("mdp", "VARCHAR(100)", "DEFAULT ' '", u"Mot de passe si non encore identifié"),
            ("profil", "VARCHAR(100)", "DEFAULT 'user'", u"Profil des droits attribués"),
                    ], # Utilisateurs
            }

def GetChamps(dbtable,tous = True,reel=False,deci=False,dte=False,texte=False):
    lstChamps = []
    # les params d'un type précisé désactivent le param tous
    if reel or deci or dte or texte : tous=False
    for ligne in dbtable:
        champ = ligne[0]
        genre = ligne[1][:3]
        if tous or (reel and genre == 'flo')\
                or (deci and genre == 'int')\
                or (dte and genre == 'dat')\
                or (texte and genre == 'var'):
            lstChamps.append(champ)
    return lstChamps

def GetChampsTypes(dbtable,tous = True,reel=False,deci=False,dte=False,texte=False):
    lstChamps = []
    lstTypes = []
    lstHelp = []
    # les params d'un type précisé désactivent le param tous
    if reel or deci or dte or texte : tous=False
    for ligne in dbtable:
        champ = ligne[0]
        genre = ligne[1][:3]
        tip = ligne[1]
        help = ligne[-1]
        if tous or (reel and genre == 'flo')\
                or (deci and genre == 'int')\
                or (dte and genre == 'dat')\
                or (texte and genre == 'var'):
            lstChamps.append(champ)
            lstTypes.append(tip)
            lstHelp.append(help)
    return lstChamps, lstTypes, lstHelp

if __name__ == '__main__':
    import wx
    app = wx.App(0)
    for dbTable in DB_TABLES.keys():
        print('Table %s :\t'%str(GetChampsTypes(dbTable,True)))
    app.MainLoop()

