#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import wx
import xpy.xGestionDB as xdb
import xpy.outils.xchoixListe as xcl
import xpy.xUTILS_Config as xucfg

def GetListeUsers():
    """ Récupère la liste des utilisateurs et de leurs droits """
    DB = xdb.DB()
    if DB.echec:
        return False
    # Droits
    req = """SELECT IDdroit, IDutilisateur, IDmodele, categorie, action, etat
    FROM droits;"""
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    dictDroitsUtilisateurs = {}
    dictDroitsModeles = {}
    for IDdroit, IDutilisateur, IDmodele, categorie, action, etat in listeDonnees:
        key = (categorie, action)
        if IDutilisateur != None:
            if not IDutilisateur in dictDroitsUtilisateurs:
                dictDroitsUtilisateurs[IDutilisateur] = {}
            dictDroitsUtilisateurs[IDutilisateur][key] = etat
        if IDmodele != None:
            if not IDmodele in dictDroitsModeles:
                dictDroitsModeles[IDmodele] = {}
            dictDroitsModeles[IDmodele][key] = etat

    # Utilisateurs
    req = """SELECT IDutilisateur, sexe, nom, prenom, mdp, profil, actif
    FROM utilisateurs
    WHERE actif=1;"""
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    listeUtilisateurs = []

    for IDutilisateur, sexe, nom, prenom, mdp, profil, actif in listeDonnees:
        droits = None
        if profil.startswith("administrateur"):
            droits = None
        if profil.startswith("modele"):
            IDmodele = int(profil.split(":")[1])
            if IDmodele in dictDroitsModeles:
                droits = dictDroitsModeles[IDmodele]
        if profil.startswith("perso"):
            if IDutilisateur in dictDroitsUtilisateurs:
                droits = dictDroitsUtilisateurs[IDutilisateur]

        dictTemp = {"IDutilisateur": IDutilisateur, "nom": nom, "prenom": prenom, "sexe": sexe, "mdp": mdp,
                    "profil": profil, "actif": actif, "droits": droits}
        listeUtilisateurs.append(dictTemp)

    DB.Close()
    return listeUtilisateurs

class AfficheUsers():
    def __init__(self):
        lstUsers = GetListeUsers()
        lstAffiche = [[x['nom'],x['prenom'],x['profil']] for x in lstUsers]
        lstColonnes = ["Nom", "Prénom", "Profil"]
        dlg = xcl.DialogAffiche( titre="Liste des utilisateurs",intro="pour consultation seulement",lstDonnees=lstAffiche,
                                 lstColonnes=lstColonnes )
        dlg.ShowModal()
        dlg.Destroy()

class CTRL_Bouton_image(wx.Button):
    def __init__(self, parent, id=wx.ID_APPLY, texte="", cheminImage=None):
        wx.Button.__init__(self, parent, id=id, label=texte)
        if cheminImage:
            self.SetBitmap(wx.Bitmap(cheminImage))
        self.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.SetInitialSize()

class CTRL_mdp(wx.SearchCtrl):
    def __init__(self, parent, listeUtilisateurs=[], size=(-1, -1), modeDLG=False):
        wx.SearchCtrl.__init__(self, parent, size=size, style=wx.TE_PROCESS_ENTER | wx.TE_PASSWORD)
        self.parent = parent
        self.listeUtilisateurs = listeUtilisateurs
        self.modeDLG = modeDLG
        self.SetDescriptiveText(u"   ")
        
        # Options
        self.ShowSearchButton(True)
        self.SetCancelBitmap(wx.Bitmap("xpy/Images/16x16/Interdit.png", wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap("xpy/Images/16x16/Cadenas.png", wx.BITMAP_TYPE_PNG))
        
        # Binds
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, event):
        self.Recherche()
        event.Skip() 
            
    def OnCancel(self, event):
        self.SetValue("")
        self.Recherche()
        event.Skip() 

    def OnDoSearch(self, event):
        self.Recherche()
        event.Skip() 

    def Recherche(self):
        txtSearch = self.GetValue()
        if self.modeDLG == True :
            listeUtilisateurs = self.listeUtilisateurs
        else:
            listeUtilisateurs = self.GetGrandParent().listeUtilisateurs
        # Recherche de l'utilisateur
        for dictUtilisateur in listeUtilisateurs :
            if txtSearch == dictUtilisateur["mdp"] :
                # Enregistrement du pseudo et mot de passe
                cfg = xucfg.ParamUser()
                self.choix = cfg.GetDict(groupe='USER')
                self.choix['pseudo'] =  dictUtilisateur['prenom'] + " " + dictUtilisateur['nom']
                self.choix['nom'] = self.choix['pseudo']
                self.choix['mpuser'] = dictUtilisateur['mdp']
                self.choix['id'] =  dictUtilisateur['IDutilisateur']
                self.choix['droits'] = dictUtilisateur['droits']
                self.choix['profil'] = dictUtilisateur['profil']
                cfg.SetDict(self.choix, groupe='USER')

                # Version pour la DLG du dessous
                if self.modeDLG == True :
                    self.GetParent().ChargeUtilisateur(dictUtilisateur)
                    self.SetValue("")
                    break
                # Version pour la barre Identification de la page d'accueil
                if self.modeDLG == False :
                    mainFrame = self.GetGrandParent()
                    if mainFrame.GetName() == "general" :
                        mainFrame.ChargeUtilisateur(dictUtilisateur)
                        self.SetValue("")
                        break
        self.Refresh() 

# --------------------------- DLG de saisie de mot de passe ----------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, id=-1, title="Identification"):
        wx.Dialog.__init__(self, parent, id, title, name="DLG_mdp")
        self.parent = parent
        self.dictUtilisateur = {}
        DB = xdb.DB()
        if DB.echec:
            self.parent.SaisieConfig()
            DB = xdb.DB()
            if DB.echec:
                self.echec = True
                return
        self.echec = False
        DB.Close()
        self.listeUtilisateurs = GetListeUsers()


        self.dictUtilisateur = None

        self.staticbox = wx.StaticBox(self, -1, "")
        self.label = wx.StaticText(self, -1, "Veuillez saisir votre code d'identification personnel :")
        self.ctrl_mdp = CTRL_mdp(self, listeUtilisateurs=self.listeUtilisateurs, modeDLG=True)
        
        self.bouton_annuler = CTRL_Bouton_image(self, id=wx.ID_CANCEL, texte="Annuler", cheminImage="xpy/Images/32x32/Annuler.png")
        
        self.__set_properties()
        self.__do_layout()
        self.ctrl_mdp.SetFocus() 
        
    def __set_properties(self):
        self.bouton_annuler.SetToolTip("Cliquez ici pour annuler")
        self.ctrl_mdp.SetMinSize((300, -1))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=0)
        
        # Intro
        grid_sizer_base.Add(self.label, 0, wx.ALL, 10)
        
        # Staticbox
        staticbox = wx.StaticBoxSizer(self.staticbox, wx.HORIZONTAL)
        grid_sizer_contenu = wx.FlexGridSizer(rows=2, cols=1, vgap=2, hgap=2)
        grid_sizer_contenu.Add(self.ctrl_mdp, 1, wx.EXPAND, 0)
        grid_sizer_contenu.AddGrowableCol(0)
        staticbox.Add(grid_sizer_contenu, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        grid_sizer_boutons.Add((20, 20), 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.Fit(self)
        self.Layout()
        self.CentreOnScreen()

    def ChargeUtilisateur(self, dictUtilisateur={}):
        self.dictUtilisateur = dictUtilisateur
        # Fermeture de la fenêtre
        self.EndModal(wx.ID_OK)
    
    def GetDictUtilisateur(self):
        return self.dictUtilisateur
    
# ----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    ret = AfficheUsers()
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    print(dlg.GetDictUtilisateur())
    app.MainLoop()
