# !/usr/bin/env python
# -*- coding: utf-8 -*-

#----------------------------------------------------------------------------
# Application :    Projet XPY, gestion d'identification
# Auteurs:          Jacques BRUNEL
# Copyright:       (c) 2019-04     Cerfrance Provence, Matthania
# Licence:         Licence GNU GPL
#----------------------------------------------------------------------------

import wx
import os
import xpy.xUTILS_SaisieParams as xusp
import xpy.xUTILS_Shelve as xucfg
import xpy.xGestionDB as xdb

# Constantes de paramétrage des écrans de configuration et identification

MATRICE_IDENT = {
("ident","Votre session"):[
    {'name': 'userdomain', 'genre': 'String', 'label': 'Votre organisation', 'value': "NomDuPC",
                        'help': 'Ce préfixe à votre nom permet de vous identifier'},
    {'name': 'username', 'genre': 'String', 'label': 'Identifiant session', 'value': "NomSession",
                        'help': "Nom d'ouverture de la sesssion sur l'ordi local"},
    {'name': 'utilisateur', 'genre': 'String', 'label': "Nom présenté à l'application", 'value': "Nom pour l'appli",
                        'help': ''},
    ],
}
MATRICE_USER = {
("choix_config","Choisissez votre configuration"):[
    {'name': 'config', 'genre': 'Enum', 'label': 'Config active',
                        'help': "Le bouton de droite vous permet de créer une nouvelle configuration",
                        'ctrlAction':'OnCtrlConfig',
                        'btnLabel':"...", 'btnHelp':"Cliquez pour gérer les configurations BD",
                        'btnAction':"OnBtnConfig",
                        'txtSize': 120},
    {'name': 'mpUserDB', 'genre': 'Mpass', 'label': 'Mot de Passe Serveur',
                        'help': "C\'est le mot de passe de l'utilisateur BD défini dans la configuration active," +
                                "\nce n'est pas celui de votre pseudo, qui vous sera demandé au lancement de l'appli",
                        'txtSize': 120},
    {'name': 'pseudo', 'genre': 'String', 'label': 'Votre pseudo appli',
                        'help': 'Par défaut c\'est votre Identifiant reconnu dans l\'application',
                        'ctrlAction':'OnCtrlPseudo',
                        'txtSize': 120},
    ]
}
# db_prim et db_second pourront être présentes dans dictAPPLI['CODE_CONFIG'] et repris dans xGestionDB
MATRICE_CONFIGS = {
    ('db_prim', "Acccès à la base principale"): [
    {'name': 'ID', 'genre': 'String', 'label': 'Désignation config', 'value': 'config1',
                    'help': "Désignez de manière unique cette configuration"},
    {'name': 'serveur', 'genre': 'String', 'label': 'Path ou Serveur', 'value':'',
                    'help': "Répertoire 'c:\...' si local - Adresse IP ou nom du serveur si réseau"},
    {'name': 'port', 'genre': 'Int', 'label': 'Port', 'value': 3306,
                    'help': "Pour réseau seulement, information disponible aurpès de l'administrateur système"},
    {'name': 'typeDB', 'genre': 'Enum', 'label': 'Type de Base',
                    'help': "Le choix est limité par la programmation", 'value':0,
                    'values':['MySql','SqlServer','Access','SQLite'] },
    {'name': 'nameDB', 'genre': 'String', 'label': 'Nom de la Base',
                     'help': "Base de donnée présente sur le serveur"},
    {'name': 'userDB', 'genre': 'String', 'label': 'Utilisateur BD',
                    'help': "Si nécessaire, utilisateur ayant des droits d'accès à la base de donnée", 'value':'invite'},
    ],
    ('db_simple',"Accès  base locale"): [
        {'name': 'ID', 'genre': 'String', 'label': 'Désignation config', 'value': 'config1',
                        'help': "Désignez de manière unique cette configuration"},
        {'name': 'serveur', 'genre': 'String', 'label': 'Path ou Serveur', 'value': '',
                        'help': "Répertoire 'c:\...' si local - Adresse IP ou nom du serveur si réseau"},
        {'name': 'typeDB', 'genre': 'Enum', 'label': 'Type de Base',
                        'help': "Le choix est limité par la programmation", 'value': 0,
                        'values': ['Access', 'SQLite']},
        {'name': 'nameDB', 'genre': 'String', 'label': 'Nom de la Base',
                         'help': "Base de donnée présente sur le serveur"},
    ],
}

IMPLANTATIONS = {
'quadratus':{
        'LCtraitements':'//srvprint/qappli/quadra/datadouble',
        'La Crau':      '//srvprint/qappli/quadra/database',
        'AlpesMed':     '//srvtse/qappli$/quadra/database',
        'Bastia':     '../qappli/quadra/database',
        'Local (all agc)':        'c:/quadra/database'},}

# la clé des agences est la désignation d'une agc, les valeurs une implantation (implantations propres à cette agc)
AGENCES = {
    'prov':['LCtraitements','La Crau'],
    'alpes':['AlpesMed'],
    'corse':['Bastia'],
    'ANY':['Local (all agc)']}

def AppelLignesMatrice(categ=None, possibles={}):
    # retourne les lignes de la  matrice de l'argument categ
    # ou la première catégorie si not categ
    code = None
    label = ''
    lignes = {}
    if possibles:
        for code, labelCategorie in possibles:
            if isinstance(code, str):
                if categ:
                    if categ == code:
                        label = labelCategorie
                        lignes = possibles[(code, labelCategorie)]
                else:
                    label = labelCategorie
                    lignes = possibles[(code, labelCategorie)]
                    break
    return code, label, lignes

def GetLstCodesMatrice(matrice):
    # retourne une liste des premiers composant des tuples clé d'une matrice
    return [x[0] for x in matrice.keys()]

def GetCleMatrice(code,matrice):
    # retourne la clé complète d'une matrice selon son ID
    cle = None
    for cle in matrice.keys():
        if cle[0] == code:
            break
    return cle

# Ecran d'identification
class DLG_identification(wx.Dialog):
    # Ecran de saisie de paramètres en dialog
    def __init__(self, parent, **kwds):
        style = kwds.pop('style',wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        size = kwds.pop('size',(400,650))
        self.optionsConfig = kwds.pop('optionsConfig',None)
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__

        wx.Dialog.__init__(self, parent, -1,title = titre,
                           style=style,size = size)

        self.parent = parent


        try :
            self.topWindow = wx.GetApp().GetTopWindow()
            nomWindow = self.topWindow.GetName()
            if nomWindow :
                # il y a une frame en top windows on va l'utiliser comme tampon mémoire
                self.topWin = True
        except : self.topWin=False


        cadre_staticbox = wx.StaticBox(self, -1, label='identification')
        topbox = wx.StaticBoxSizer(cadre_staticbox, wx.VERTICAL)
        self.btn = xusp.BTN_fermer(self)
        self.btn.Bind(wx.EVT_BUTTON, self.OnFermer)
        self.btnTest = xusp.BTN_action(self,help='Test de la connexion réseau',image=wx.Bitmap("xpy/Images/100x30/Bouton_tester.png"))
        self.btnTest.Bind(wx.EVT_BUTTON, self.OnTest)

        # Récup du code de la description des champs pour une configuration
        lstcode = GetLstCodesMatrice(MATRICE_CONFIGS)
        if not self.optionsConfig:
            self.optionsConfig = lstcode[0]
        if self.parent and 'CODE_CONFIG' in self.parent.dictAppli:
            self.optionsConfig = self.parent.dictAppli['CODE_CONFIG']
            if not (self.optionsConfig in lstcode):
                wx.MessageBox("L'option '%s' n'est pas dans MATRICECONFIGS " % (self.optionsConfig))

        def AffichID():
            #Affichage de l'identification IDENT partie grisée, et dernière CHOIX_CONFIG (non grisée)
            self.ctrlID = xusp.CTRL_property(self, matrice=MATRICE_IDENT, enable=False)
            # précharge les dernières valeurs de l'utilisateurs de toutes les clé du groupe IDENT
            ddDonnees = {}
            valeurs = {}
            ident = None
            try:
                utilisateur = self.parent.dictUser['utilisateur']
            except : utilisateur = None
            for (code,label), lignes in MATRICE_IDENT.items():
                for ligne in  lignes:
                    if ligne['name'].lower() in ('username', 'user'):
                        valeurs[ligne['name']] = os.environ['USERNAME']
                        ident = code
                    if ligne['name'].lower() in ('userdomain','domaine', 'workgroup'):
                        try:
                            valeurs[ligne['name']] = os.environ['USERDOMAIN']
                        except:
                            import platform
                            valeurs[ligne['name']] = platform.node()
                    if ligne['name'].lower() in ('utilisateur',):
                        valeurs[ligne['name']] = utilisateur
                        ident = code

            if ident:
                ddDonnees[ident] = valeurs
                self.ctrlID.SetValeurs(ddDonnees=ddDonnees)

            code,label,lignes = AppelLignesMatrice(None, MATRICE_USER)
            # le nom de la configuration c'est le premier champ décrit dans la matrice
            self.codeConfig = code + '.' + lignes[0]['name']
            ###self.codeConfig = lignes[0]['name']

            # simple texte
            self.titre =wx.StaticText(self, -1, "Accès à la base de donnée principale")

            # contrôle gérant la saisie des paramètres de config
            self.ctrlConfig = xusp.BoxPanel(self, wx.ID_ANY, lblbox=label, code=code, lignes=lignes, dictDonnees={})
            # adressage dans le fichier par défaut dans profilUser
            cfg = xucfg.ParamUser()
            # lecture des valeurs préalablement utilisées
            self.choix= cfg.GetDict(dictDemande=None, groupe='USER', close=False)
            self.dictAppli= cfg.GetDict(dictDemande=None, groupe='APPLI')
            if self.dictAppli == {}:
                self.dictAppli = self.parent.dictAppli

            # choix de la configuration prise dans paramUser
            cfgF = xucfg.ParamFile()
            self.configs= cfgF.GetDict(dictDemande=None, groupe='CONFIGS')
            self.choix.update(cfgF.GetDict(dictDemande={'config':None}, groupe='CONFIGS', close=False))
            if self.configs and ('lstIDconfigs' in self.configs ) :
                if self.configs['lstIDconfigs']:
                    # pose dans la grille la valeur de la dernière valeur utilisée
                    self.ctrlConfig.SetOneValues(self.codeConfig, self.configs['lstIDconfigs'])
            #pose dans la grille de saisie, les valeurs lues dans profilUser
            self.ctrlConfig.SetValues(self.choix)
            topbox.Add(self.ctrlID, 0,wx.ALL | wx.EXPAND, 5)
            topbox.Add((20,20), 0, wx.ALIGN_TOP, 0)
            topbox.Add(self.titre, 0, wx.LEFT, 60)
            topbox.Add((20,20), 0, wx.ALIGN_TOP, 0)
            topbox.Add(self.ctrlConfig, 0, wx.ALIGN_TOP| wx.EXPAND, 0)
            topbox.Add((40,40), 0, wx.EXPAND, 0)
            piedbox = wx.BoxSizer(wx.HORIZONTAL)
            piedbox.Add(self.btnTest, 0, 0, 0)
            piedbox.Add(self.btn, 0, wx.RIGHT, 11)
            topbox.Add(piedbox, 0, wx.ALIGN_RIGHT, 0)

        AffichID()
        self.SetSizer(topbox)

    def OnTest(self,event):
        self.OnCtrlAction(None)
        DB = xdb.DB(grpConfig=self.optionsConfig)
        style = wx.ICON_WARNING
        try:
            nomBase = DB.nomBase
            if DB.echec == 0: style = wx.ICON_INFORMATION
            retour = ['avec succès', '!!!!!!!! SANS SUCCES !!!!!!!\n'][DB.echec]
            mess = "L'accès à la base '%s' s'est réalisé %s" % (nomBase, retour)
        except: mess = "Désolé "
        wx.MessageBox(mess,style=style)

    def OnCtrlPseudo(self,event):
        cle = GetCleMatrice('utilisateur',MATRICE_IDENT)
        dic = self.ctrlID.GetValeurs()
        utilisateur = dic['ident']['utilisateur']
        pseudo = event.EventObject.Value
        if len(utilisateur) == 0:
            dic['ident']['utilisateur'] = pseudo + " #NA"
            self.ctrlID.SetValeurs(dic)

    def OnCtrlAction(self, event):
        # relais des actions sur les ctrls
        action = 'self.%s(event)' % event.EventObject.actionCtrl
        try:
            eval(action)
        except Exception as err:
            wx.MessageBox(
                "Echec sur lancement action sur ctrl: '%s' \nLe retour d'erreur est : \n%s" % (action, err))

    def OnCtrlConfig(self,event):
        #action evènement Enter sur le contrôle combo, correspond à un changement de choix
        self.SauveParamUser()
        self.SauveConfig()

    def OnBtnAction(self, event):
        # relais des actions sur les boutons associés aux ctrls
        action = 'self.%s(event)' % event.EventObject.actionBtn
        try:
            eval(action)
        except Exception as err:
            wx.MessageBox(
                "Commande: '%s' \n\nErreur: \n%s" % (action, err),
            "Echec sur lancement de l'action bouton")

    def OnBtnConfig(self,event):
        # sur clic du bouton pour élargir le choix de la combo
        sc = DLG_saisieConfigs(self,optionsConfig=self.optionsConfig)
        if sc.ok :
            sc.ShowModal()
            # Fichier config dans Data commun à tous
            cfg = xucfg.ParamFile()
            dicvalues = cfg.GetDict({'lstIDconfigs':None}, 'CONFIGS')
            if dicvalues['lstIDconfigs']:
                self.ctrlConfig.SetOneValues(self.codeConfig, dicvalues['lstIDconfigs'])
            value = sc.GetChoix(idxColonne=0)
            self.ctrlConfig.SetOneValue(self.codeConfig,value)
            # choix de configs user stockées
            self.SauveConfig()
        else: wx.MessageBox('DLG_saisieConfigs : lancement impossible, cf MATRICE_CONFIGS et  CODE_CONFIG')

    def SauveParamUser(self):
        # sauve Config et ID dans le registre de la session
        cfg = xucfg.ParamUser()
        dic = self.ctrlConfig.GetValues()
        # le choix config sera stocké dans File
        del dic['config']
        cfg.SetDict(dic, groupe='USER',close=False)
        dic = self.ctrlID.GetValeurs()
        cfg.SetDict(dic['ident'], groupe='IDENT')

    def SauveConfig(self):
        # sauve les configs sur appli/data local
        cfg = xucfg.ParamFile()
        value = self.ctrlConfig.GetOneValue(self.codeConfig)
        cfg.SetDict({'config': value}, groupe='CONFIGS')

    def OnFermer(self,event):
        # enregistre les valeurs de l'utilisateur
        self.SauveParamUser()
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else: self.Destroy()

class zzDLG_implantation(wx.Dialog):
    # Ecran de saisie de paramètres de bases de données
    def __init__(self, parent, *args, **kwds):
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self, parent, -1,title = titre,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.parent = parent
        cadre_staticbox = wx.StaticBox(self, -1)
        topbox = wx.StaticBoxSizer(cadre_staticbox, wx.VERTICAL)
        self.btn = xusp.BTN_fermer(self)
        self.btn.Bind(wx.EVT_BUTTON, self.OnFermer)
        self.btnTest = xusp.BTN_action(self,help='Test de la connexion réseau',image=wx.Bitmap("xpy/Images/100x30/Bouton_tester.png"))
        self.btnTest.Bind(wx.EVT_BUTTON, self.OnTest)

        def Affiche():
            # récupère le premier groupe de paramètres à afficher dans la grille
            code,label,lignes = AppelLignesMatrice(None, MATRICE_CONFIGS)
            # le nom de la configuration c'est le premier champ décrit dans la matrice
            #self.codeConfig = code + '.' + lignes[0]['name']

            # simple texte
            self.titre =wx.StaticText(self, -1, "Accès aux bases compta")

            # contrôle gérant la saisie des paramètres de config
            self.ctrlConfig = xusp.BoxPanel(self, -1, lblbox=label, code=code, lignes=lignes, dictDonnees={})
            self.choix = self.ctrlConfig.GetValues()

            # adressage dans le fichier par défaut dans profilUser
            cfg = xucfg.ParamUser()
            self.choix= cfg.GetDict(dictDemande=None, groupe='IMPLANTATION', close=False)

            self.ctrlConfig.SetValues(self.choix)

            topbox.Add(self.titre, 0, wx.LEFT, 60)
            topbox.Add((20,20), 0, wx.ALIGN_TOP, 0)
            topbox.Add(self.ctrlConfig, 0, wx.ALIGN_TOP, 0)
            topbox.Add((40,40), 0, wx.ALIGN_TOP, 0)
            piedbox = wx.BoxSizer(wx.HORIZONTAL)
            piedbox.Add(self.btnTest, 0, 0, 0)
            piedbox.Add(self.btn, 0, wx.RIGHT, 11)
            topbox.Add(piedbox, 0, 0, 0)

        Affiche()
        self.SetSizerAndFit(topbox)

    def OnTest(self,event):
        self.OnCtrlAction(None)
        DB = xdb.DB(config = self.choix)
        style = wx.ICON_WARNING
        try:
            #si le constructeur est passé, la variable echec peut être restée à True
            nomBase = DB.nomBase
            if DB.echec == 0: style = wx.ICON_INFORMATION
            retour = ['avec succès','!!!!!!!! SANS SUCCES !!!!!!!\n'][DB.echec]
            mess = "L'accès à la base '%s' s'est réalisé %s"%(nomBase,retour)
        except: mess = "Désolé il y a un problème "
        DB.Close()
        wx.MessageBox(mess,style=style)

    def OnFermer(self,event):
        # enregistre les valeurs de l'utilisateur, puis ferme
        self.OnCtrlAction(None)
        self.Destroy()

    def OnCtrlAction(self,event):
        #action evènement Enter sur le contrôle combo, correspond à un changement de choix
        pass

# Gestion à partir d'une liste des accès aux bases de données en début d'appli
class DLG_saisieConfigs(xusp.DLG_listCtrl):
    # Ecran de saisie de paramètres en dialog
    def __init__(self, parent, *args, **kwds):
        optionsConfig = kwds.pop('optionsConfig',None)
        super().__init__(parent, *args, **kwds)
        self.parent = parent
        self.dlColonnes = {}
        self.lddDonnees = []
        self.exLstConfigs = []
        self.dldMatrice = {}
        # composition des paramètres
        # seuls les paragraphes option choisis par l'appli et présents dans MATRICE_CONFIGS seront appelés.
        self.gestionProperty = False
        self.ok = False
        cle = GetCleMatrice(optionsConfig,MATRICE_CONFIGS)
        self.dldMatrice[cle] = MATRICE_CONFIGS[cle]
        self.dlColonnes[optionsConfig] = [x ['name'] for x in MATRICE_CONFIGS[cle]]
        cfg = xucfg.ParamFile()
        dic= cfg.GetDict(None,'CONFIGS')
        if 'lstConfigs' in dic:
            newlst = []
            if dic['lstConfigs']:
               for dicligne in dic['lstConfigs']:
                   if optionsConfig in dicligne:
                       newlst.append(dicligne)
                   else: self.exLstConfigs.append(dicligne)
               self.lddDonnees = newlst
        # paramètres pour self.pnl contenu principal de l'écran
        self.kwds['lblbox'] = 'Configurations disponibles'
        self.MinSize = (400,300)
        if self.dldMatrice != {}:
            self.Init()
            self.ok = True
            if 'config' in self.parent.choix:
                choix = self.parent.choix['config']
            else: choix = 0
            if 'lstIDconfigs' in dic:
                lst = dic['lstIDconfigs']
                if choix in lst:
                    ix = lst.index(choix)
                    self.pnl.ctrl.Select(ix)
                    self.pnl.ctrl.SetItemState(ix,wx.LIST_STATE_SELECTED,wx.LIST_STATE_SELECTED)

    def OnFermer(self, event):
        configs = []
        #constitution de la liste des noms de configs (première colonne)
        for ligne in self.exLstConfigs + self.lddDonnees:
            for cle, valeurs  in ligne.items():
                if 'ID' in valeurs.keys():
                   conf = valeurs['ID']
            configs.append(conf)

        cfg = xucfg.ParamFile()
        cfg.SetDict({'lstIDconfigs': configs}, 'CONFIGS', close=False )
        cfg.SetDict({'lstConfigs':self.exLstConfigs + self.lddDonnees}, 'CONFIGS')
        return self.Close()

    def GetChoix(self, idxColonne = 0):
        # récupère le choix fait dans le listCtrl par la recherche de son ID
        ctrl = self.pnl.ctrl
        idxLigne = ctrl.GetFirstSelected()
        # en l'absence de choix on prend la première ligne
        if idxLigne == -1:
            if ctrl.GetItemCount() > 0:
                idxLigne = 0
        if idxLigne >= 0:
            # le nom de la config est dans la colonne pointée par l'index fourni
            cell = ctrl.GetItem(idxLigne,idxColonne)
            choix = cell.GetText()
        else: choix=''
        return choix

# Gestion d'un accès config_base de donnée particulier
class DLG_saisieUneConfig(xusp.DLG_vide):
    def __init__(self,nomConfig=None,**kwds):
        super().__init__(self, **kwds)
        # récup de la matrice ayant servi à la gestion des données
        optionsConfig = kwds.pop('optionsConfig',None)
        if not optionsConfig:
            lstcode = GetLstCodesMatrice(MATRICE_CONFIGS)
            optionsConfig = lstcode[0]
        key = (optionsConfig,"Paramètres BD de l'accès à la compta")
        matrice = {key: MATRICE_CONFIGS[GetCleMatrice(optionsConfig,MATRICE_CONFIGS)]}
        # suppose le champ ID en première position
        matrice[key][0]['value'] = nomConfig
        # grise le champ ID
        xusp.SetEnableID(matrice, False)
        self.pnl = xusp.TopBoxPanel(self, matrice=matrice, lblbox='Ajout d\'un accès pour la compta')
        self.Sizer(self.pnl)

    def GetValeurs(self):
        return self.pnl.GetValeurs()

    def GetConfig(self):
        return self.pnl.GetValeurs()['db_prim']

# Gestion de paramètres à partir d'une liste, la matrice est définie après l'init
class DLG_saisieParams(xusp.DLG_listCtrl):
    def __init__(self, parent, *args, **kwds):
        super().__init__(parent, *args, **kwds)
        self.parent = parent
        self.matrice = {}
        self.lddDonnees = []
        self.dldMatrice = {}
        # composition des paramètres
        self.gestionProperty = False
        self.ok = False

    # entre __init__() et init() remplir dldMatrice, lddDonnees et dlColonnes(pour ne pas les afficher toutes)
    def init(self):
        self.dldMatrice = self.matrice
        # paramètres pour self.pnl contenu principal de l'écran
        self.kwds['lblbox'] = 'Choix disponibles'
        self.MinSize = (400,300)
        if self.dldMatrice != {}:
            self.Init()
            self.ok = True
            if self.parent.choisi and len(self.parent.choisi) > 0 :
                choix = self.parent.choisi
            else: choix = 0
        self.dlDonnees = self.GetDonnees()

    def OnFermer(self, event):
        # une ligne a été ajoutée
        self.dlDonneesFin = self.GetDonnees()
        for cle, lstItems in self.dlDonneesFin.items() :
            if not cle in self.dlDonnees:
                self.parent.Ajouter(lstItems)
            elif self.dlDonneesFin[cle] != self.dlDonnees[cle]:
                    self.parent.Modifier(lstItems)
        for cle, lstItems in self.dlDonnees.items() :
            if not cle in self.dlDonneesFin:
                self.parent.Supprimer(lstItems)
        return self.Close()

    def GetChoix(self, idxColonne = 0):
        # récupère le choix fait dans le listCtrl par la recherche de son ID
        ctrl = self.pnl.ctrl
        idxLigne = ctrl.GetFirstSelected()
        # en l'absence de choix on prend la première ligne
        if idxLigne == -1:
            if ctrl.GetItemCount() > 0:
                idxLigne = 0
        if idxLigne >= 0:
            # le nom de la config est dans la colonne pointée par l'index fourni
            cell = ctrl.GetItem(idxLigne,idxColonne)
            choix = cell.GetText()
        else: choix=''
        return choix

    def GetDonnees(self, idxColonneCle = 0):
        # récupère les données du ctrl
        ctrl = self.pnl.ctrl
        dic = {}
        for ix in range(ctrl.ItemCount):
            ligne = []
            for col in range(ctrl.ColumnCount):
                ligne.append(ctrl.GetItem(ix,col).GetText())
            don = ctrl.GetItem(ix,idxColonneCle).GetText()
            dic[don] = ligne
        return dic

# Gestion d'un jeu de paramètres stockés localement, et définis dans kwds
class PNL_paramsLocaux(xusp.TopBoxPanel):
    # Ecran de saisie de paramètres mono écran repris du disque de la station
    def __init__(self, parent, *args, **kwds):
        kwdsTopBox = {}
        for key in ('pos','size','style','name','matrice','donnees','lblbox'):
            if key in kwds.keys(): kwdsTopBox[key] = kwds[key]
        super().__init__(parent, *args, **kwdsTopBox)
        self.pathData = kwds.pop('pathdata',"")
        self.nomFichier = kwds.pop('nomfichier',"params")
        self.nomGroupe = kwds.pop('nomgroupe',"paramLocal")
        self.parent = parent

    # Init doit être lancé après l'initialisation du super() qui alimente les champs par défaut
    def Init(self):
        # choix de la configuration prise dans paramUser
        self.paramsFile = xucfg.ParamFile(nomFichier=self.nomFichier, path=self.pathData)
        self.dicParams = self.paramsFile.GetDict(dictDemande=None, groupe=self.nomGroupe, close=False)
        if self.dicParams:
            # pose dans la grille la valeur de la dernière valeur utilisée
            self.SetValeurs(self.dicParams)

    def SauveParams(self,close=False):
        # peut être lancé avec close forcé du shelve
        dicValeurs = self.GetValeurs()
        self.paramsFile.SetDict(dictEnvoi=dicValeurs,groupe=self.nomGroupe,close=close )

#************************   Pour Test ou modèle  *********************************

class xFrame(wx.Frame):
    # reçoit les controles à gérer sous la forme d'un ensemble de paramètres
    def __init__(self, *args, matrice={}, donnees={}, lblbox="Paramètres xf"):
        listArbo=os.path.abspath(__file__).split("\\")
        self.parent = None
        self.pathData = 'c:\\Temp'
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Frame.__init__(self,*args, title=titre, name = titre)
        self.topPnl = PNL_paramsLocaux(self,wx.ID_ANY, nomfichier='test', matrice=matrice, donnees=donnees, lblbox=lblbox)
        self.topPnl.Init()
        self.btn0 = wx.Button(self, wx.ID_ANY, "Action Frame")
        self.btn0.Bind(wx.EVT_BUTTON,self.OnBoutonAction)
        self.marge = 10
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.topPnl, 0, wx.LEFT|wx.EXPAND,self.marge)
        sizer_1.Add(self.btn0, 0, wx.RIGHT,self.marge)
        self.SetSizerAndFit(sizer_1)
        self.CentreOnScreen()

    def OnBoutonAction(self, event):
        #Bouton Test: sauvegarde les params, pallie l'absence de kill focus
        self.topPnl.SauveParams()
        print('OK pour Sauve Params, relancez pour vérifier')

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    frame_1 = DLG_identification(None,optionsConfig='db_prim')
    #frame_1 = xFrame(None, matrice={('db_prim','Test xframe'): MATRICE_CONFIGS['db_prim']})
    #frame_1 = DLG_implantation(None)
    app.SetTopWindow(frame_1)
    frame_1.Position = (50,50)
    frame_1.Show()
    app.MainLoop()

