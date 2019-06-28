# !/usr/bin/env python
# -*- coding: utf-8 -*-

#------------------------------------------------------------------------
# Application :    Projet XPY, atelier de développement
# Auteurs:          Jacques BRUNEL,
# Copyright:       (c) 2019-04     Cerfrance Provence, Matthania
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import os
import sys
import xpy.xUTILS_RapportBugs
import xpy.xUTILS_Config

def CrashReport(dictAppli):
    # Crash report
    fichierLog = dictAppli['NOM_FICHIER_LOG']
    appli = dictAppli['NOM_APPLICATION']
    if 'VERSION_APPLICATION' in dictAppli.keys():
        version = dictAppli['VERSION_APPLICATION']
    else: version = appli
    xpy.xUTILS_RapportBugs.Activer_rapport_erreurs(version=version, appli = appli)
    print('CrashReport ok')

    # Supprime le journal.log si supérieur à 10 Mo
    if os.path.isfile(fichierLog):
        taille = os.path.getsize(fichierLog)
        if taille > 5000000:
            os.remove(fichierLog)

class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super().__init__(*args, name="general", style=wx.DEFAULT_FRAME_STYLE, **kw)
        # Vérifie le path xpy
        self.pathXpy = os.path.dirname(os.path.abspath(__file__))
        if not self.pathXpy in sys.path:
            sys.path = [self.pathXpy] + sys.path
        # le dictionnaire config contiendra  toutes les configurations de l'utilisateur,
        #       enregistrées dans des fichiers  soit dans profilUser ou dans Data selon xUTILS_Config
        self.config = {}

    def xInit(self):
        print("Lancement %s"%self.dictAppli["NOM_APPLICATION"])

        os.chdir(self.pathXpy)
        os.chdir('..')
        pathCourant = os.getcwd()
        self.pathTemp = pathCourant +"\\%s"%self.dictAppli['REP_TEMP']
        self.pathData = pathCourant +"\\%s"%self.dictAppli['REP_DATA']
        self.pathSrcAppli = pathCourant +"\\%s"%self.dictAppli['REP_SOURCES']
        # teste la présence de sources
        lstFiles = os.listdir(self.pathSrcAppli)
        nbModules = 0
        for nom in lstFiles:
            if nom[-3:] == '.py':
                nbModules += 1
        if not nbModules > 0:
            wx.MessageBox("Aucun module présent dans %s"%self.pathSrcAppli, 'Lancement impossible', wx.OK | wx.ICON_STOP)
            return None
        else:
            # Ajoute le path des modules spécifiques pour les imports
            if not self.pathSrcAppli in sys.path:
                sys.path = [self.pathSrcAppli] + sys.path
            # Vérifie l'existence des répertoires Data et Temp et les crées
            for rep in (self.pathData, self.pathTemp):
                xpy.xUTILS_Config.CreePath(rep)
            for rep in ('pathData', 'pathTemp','pathSrcAppli','pathXpy'):
                self.dictAppli[rep] = eval('self.'+rep)
            cfg = xpy.xUTILS_Config.ParamUser()
            self.config= cfg.SetDict(self.dictAppli, groupe='APPLI')
            return wx.OK

    def MakeHello(self,message):
        self.topPanel = wx.Panel(self)
        self.topContenu = wx.StaticText(self.topPanel, label=message, pos=(25, 25))
        font = self.topContenu.GetFont()
        font.PointSize += 5
        font = font.Bold()
        self.topContenu.SetFont(font)

    def MakeMenuBar(self):
        # Construction de la barre de menu à partir du fichier menu.py présent dans les sources de l'appli
        self.dictMenu = {}
        try:
            import menu
            self.menuClass = menu.MENU(self)
            self.dictMenu = menu.MENU.ParamMenu(self)
        except:
            wx.MessageBox("Echec de l'ouverture de l'objet : 'MENU.ParamMenu'\ndans %s"%self.pathSrcAppli+"\menu.py", 'Lancement impossible', wx.OK | wx.ICON_STOP)

        # Création du menu dernière branche
        def CreationItem(menuParent, item):

            # Lance l'action dans l'appli ou dans xAppli par défaut
            def OnAction(event):
                id = event.GetId()
                if id in self.dictMenuActions:
                    if self.dictMenuActions[id] in dir(self.menuClass):
                        action='self.menuClass.'+self.dictMenuActions[id]+'(self)'
                    else:
                        mess1 = 'Fonction \'%s\' non présente dans le fichier menu.py de l\'appli'%self.dictMenuActions[id]
                        if self.dictMenuActions[id] in dir(self):
                            action = 'self.' + self.dictMenuActions[id] + '(self)'
                        else:
                            wx.MessageBox(mess1,'Non Programmé', wx.OK | wx.ICON_STOP)
                eval(action)

            id = wx.NewId()
            if "genre" in item.keys():
                genre = item["genre"]
            else :
                genre = wx.ITEM_NORMAL
            itemMenu = wx.MenuItem(parentMenu=menuParent, id = id, text = item["label"], helpString=item["infobulle"], kind = genre)
            if "actif" in item.keys() :
                itemMenu.Enable(item["actif"])
            if "image" in item.keys() :
                ptImage = (str(self.pathXpy) + "/" + str(item["image"])).replace("\\","/")
                itemMenu.SetBitmap(wx.Bitmap(ptImage, wx.BITMAP_TYPE_PNG))
            ctrl = menuParent.Append(itemMenu)
            self.Bind(wx.EVT_MENU, OnAction, id=id)

            self.dictInfosMenu[item["code"]] = {"id" : id, "ctrl" : ctrl}
            self.dictMenuActions[id] = item["action"]

        # Déroulé des branches du menu
        def CreationMenu(menuParent, item, sousmenu=False):
            menu = wx.Menu()
            id = wx.NewId()
            for sousitem in item["items"]:
                if sousitem == "-":
                    menu.AppendSeparator()
                elif "items" in sousitem.keys():
                    CreationMenu(menu, sousitem, sousmenu=True)
                else:
                    CreationItem(menu, sousitem)
            if sousmenu == True:
                ctrl = menuParent.AppendSubMenu( menu, item["label"])
            else:
                ctrl = menuParent.Append(menu, item["label"])
            self.dictInfosMenu[item["code"]] = {"id": id, "ctrl": ctrl}

        # Racine du menu
        self.menu = wx.MenuBar()
        self.dictInfosMenu = {}
        self.dictMenuActions = {}

        # Pour chaque colonne
        for colonne in self.dictMenu:
            CreationMenu(self.menu, colonne)

        # Give the menu bar to the frame
        self.SetMenuBar(self.menu)

    def Final(self, videRepertoiresTemp=True):
        """ Fin de l'application
        # Mémorise l'action dans l'historique
        if self.userConfig["nomFichier"] != "":
            try:
                UTILS_Historique.InsertActions([{
                    "IDcategorie": 1,
                    "action": _(u"Fermeture du fichier"),
                }, ])
            except:
                pass

        # Mémorisation du paramètre de la taille d'écran
        if self.IsMaximized() == True:
            taille_fenetre = (0, 0)
        else:
            taille_fenetre = tuple(self.GetSize())
        self.userConfig["taille_fenetre"] = taille_fenetre

        # Mémorisation des perspectives
        self.SauvegardePerspectiveActive()
        self.userConfig["perspectives"] = self.perspectives
        self.userConfig["perspective_active"] = self.perspective_active

        if hasattr(self, "ctrl_remplissage"):
            self.userConfig["perspective_ctrl_effectifs"] = self.ctrl_remplissage.SavePerspective()
            self.userConfig["page_ctrl_effectifs"] = self.ctrl_remplissage.GetPageActive()

            # Sauvegarde du fichier de configuration
        self.SaveFichierConfig(nomFichier=self.nomFichierConfig)

        # Vidage des répertoires Temp
        if videRepertoiresTemp == True:
            FonctionsPerso.VideRepertoireTemp()
            FonctionsPerso.VideRepertoireUpdates()

        # Arrête le timer Autodeconnect
        if self.autodeconnect_timer.IsRunning():
            self.autodeconnect_timer.Stop()

        # Affiche les connexions restées ouvertes
        GestionDB.AfficheConnexionOuvertes()
        """
        return True

    def xQuitter(self, event):
        """Close the frame, terminating the application."""
        if self.Final() == False :
            return
        self.Close(True)

    def xInfos(self, event):
        """Display an About Dialog"""
        wx.MessageBox("xAppli : Prochainement une action d'information sera générée par défaut", 'Projet en attente',
                      wx.OK|wx.ICON_INFORMATION)

    def xAide(self, event):
        """Display an About Dialog"""
        wx.MessageBox("xAppli : Prochainement une action d'aide sera générée par défaut", 'Projet en attente',
                      wx.OK|wx.ICON_INFORMATION)

    def SaisieConfig(self):
        import xpy.xGestionConfig as gc
        cfg = gc.DLG_identification(self, style = wx.RESIZE_BORDER )
        cfg.Show()


#************************   Pour Test    *******************************
if __name__ == "__main__":
    # Lancement de l'application
    app = wx.App()
    frm = MainFrame(None, title='xPY morceaux choisis')
    frm.dictAppli = {
        'NOM_APPLICATION': "xAppli",
        'REP_SOURCES': "srcMyAppli",
        'REP_DATA': "srcMyAppli/Data",
        'REP_TEMP': "srcMyAppli/Temp",
        'NOM_FICHIER_LOG':"testLOG",
        'OPTIONSCONFIG': ["db_prim"],
        }
    frm.xInit()
    CrashReport(frm.dictAppli)
    frm.Show()
    #frm.MakeHello("OK test")
    frm.SaisieConfig()
    app.MainLoop()

