# !/usr/bin/env python
# -*- coding: utf-8 -*-

#----------------------------------------------------------------------------
# Application :    Projet OpenRef, gestion d'identification
# Auteurs:          Jacques BRUNEL
# Copyright:       (c) 2019-05     Cerfrance Provence
# Licence:         Licence GNU GPL
#----------------------------------------------------------------------------

import wx
import os
import xpy.xGestionConfig as xgc
import xpy.xUTILS_SaisieParams as xusp
import xpy.xUTILS_Config as xucfg
import xpy.xGestionDB as xdb
import srcOpenRef.UTIL_import as orui
import srcOpenRef.UTIL_analyses as orua
import srcOpenRef.UTIL_traitements as orut
import srcOpenRef.UTIL_affectations as oruaf
import xpy.xGestion_Tableau as tbl
from xpy.outils.ObjectListView import ColumnDefn

MATRICE_COMPTA = {
("choix_config","Choisissez votre configuration"):[
    {'name': 'localis', 'genre': 'Enum', 'label': 'Localisation','value':'LCtraitements', 'values':['LCtraitements','La Crau','AlpesMed','Bastia','Local (all agc)'],
                        'help': "Choisissez votre localisation dans la liste proposée"},
    {'name': 'compta', 'genre': 'Enum', 'label': 'logiciel compta','value':'quadratus', 'values':['quadratus'],
                        'help': 'Type de comptabilité'},
    ]}

MATRICE_IMPORT = {
("choix_config","Choisissez votre configuration"):[
    {'name': 'client', 'genre': 'String', 'label': 'Code client', 'help': "Choisir le code du client"},
    {'name': 'annee', 'genre': 'Int', 'label': 'Année de clôture','help': 'Année de la fin de l\'exercice'},
    {'name': 'nbAnter', 'genre': 'Int', 'label': 'Nbre d\'années d\'archives','value':0,'help': 'Nombre d\'exercices antérieurs à importer'},
    ]}

MATRICE_IMPORTMULTI = {
("choix_config","Choisissez votre configuration"):[
    {'name': 'annee', 'genre': 'Int', 'label': 'Année des clôtures','help': 'Année de la fin de l\'exercice'},
    {'name': 'nbAnter', 'genre': 'Int', 'label': 'Nbre d\'années d\'archives','value':0,'help': 'Nombre d\'exercices antérieurs à importer'},
    {'name': 'nafs', 'genre': 'Str', 'label': 'Filtre sur NAF','value':'tous','help': 'Saisie d\'une liste de codes NAF, servant de filtre',
                'btnLabel':"...", 'btnHelp': "Cliquez pour gérer la liste des codes Naf à retenir",'btnAction': 'OnBtnChoixNafs'},
    ]}

MATRICE_EXPORT = {
("choix_config","Choisissez votre analyse à exporter"):[
    {'name': 'client', 'genre': 'String', 'label': 'Code client', 'help': "Choisir le code du client"},
    {'name': 'annee', 'genre': 'Int', 'label': 'Année de clôture','help': 'Année de la fin de l\'exercice'},
    {'name': 'nbAnter', 'genre': 'Int', 'label': 'Nbre d\'années d\'archives','value':0,'help': 'Nombre d\'exercices antérieurs à analyser'},
    {'name': 'analyse', 'genre': 'str', 'label': 'Analyse à exporter','value':0,'help': 'Une analyse est un ensemble de variables',
             'btnLabel':"...", 'btnHelp': "Cliquez pour choisir une analyse", 'btnAction': 'OnBtnChoixAnalyse'},
    {'name': 'gestiontable', 'genre': 'enum', 'label': 'Gestion de la sortie', 'value': 0,
     'help': 'Traitement à appliquer à la table exportée',
     'values': ['Ajouter à l\'existant','Purger et recréer la table','Créer une nouvelle table']}
    ]}

MATRICE_EXPORTGROUPE = {
("choix_config","Choisissez votre groupe à analyser"):[
    {'name': 'groupe', 'genre': 'String', 'label': 'Code du groupe', 'help': "Choisir le code du groupe de clients",
            'btnLabel':"...", 'btnHelp': "Cliquez pour choisir un groupe", 'btnAction': 'OnBtnChoixGroupe'},
    {'name': 'annee', 'genre': 'Int', 'label': 'Année de clôture','help': 'Année de la fin de l\'exercice'},
    {'name': 'nbAnter', 'genre': 'Int', 'label': 'Nbre d\'années d\'archives','value':0,
            'help': 'Nombre d\'exercices antérieurs à analyser'},
    {'name': 'analyse', 'genre': 'str', 'label': 'Analyse à exporter','value':0,'help': 'Une analyse est un ensemble de variables',
            'btnLabel':"...", 'btnHelp': "Cliquez pour choisir une analyse", 'btnAction': 'OnBtnChoixAnalyse'},
    {'name': 'gestiontable', 'genre': 'enum', 'label': 'Gestion de la sortie', 'value': 0,
            'help': 'Traitement à appliquer à la table exportée',
            'values': ['Ajouter à l\'existant','Purger et recréer la table','Créer une nouvelle table']}
    ]}

MATRICE_EXPORTFILIERE = {
("choix_config","Choisissez votre filière à analyser"):[
    {'name': 'filiere', 'genre': 'String', 'label': 'Code de la filière', 'help': "Choisir le code de la filière à analyser",
            'btnLabel':"...", 'btnHelp': "Cliquez pour choisir une filière", 'btnAction': 'OnBtnChoixFiliere'},
    {'name': 'annee', 'genre': 'Int', 'label': 'Année de clôture','help': 'Année de la fin de l\'exercice'},
    {'name': 'nbAnter', 'genre': 'Int', 'label': 'Nbre d\'années d\'archives','value':0,'help': 'Nombre d\'exercices antérieurs à analyser'},
    {'name': 'analyse', 'genre': 'str', 'label': 'Analyse à exporter','value':0,'help': 'Une analyse est un ensemble de variables',
            'btnLabel':"...", 'btnHelp': "Cliquez pour choisir une analyse", 'btnAction': 'OnBtnChoixAnalyse'},
    {'name': 'gestiontable', 'genre': 'enum', 'label': 'Gestion de la sortie', 'value': 0,
            'help': 'Traitement à appliquer à la table exportée',
            'values': ['Ajouter à l\'existant','Purger et recréer la table','Créer une nouvelle table']}
    ]}

MATRICE_CHOIXANALYSE = {
("analyses","Analyses existantes"): [
    {'name': 'ID', 'genre': 'String', 'label': 'Code','value':'CodeAnalyse',
                    'help': "Désignez de manière unique cet élément"},
    {'name': 'libelle', 'genre': 'String', 'label': 'Nom', 'value':'Mon analyse',
                    'help': "Nom descriptif de l'analyse"},
    {'name': 'etendue', 'genre': 'str', 'label': "Etendue de l'analyse", 'value': '*',
                    'help': "* rend l'analyse accessible à tout agc, sinon préciser l'agc"},
    {'name': 'info', 'genre': 'texte', 'label': "Descriptif",
                    'help': "pour plus d'info sur cette analyse", },
    ],}

MATRICE_CHOIXGROUPE = {
("groupe","Groupes constitués"): [
    {'name': 'ID', 'genre': 'String', 'label': 'Code','value':'CodeGroupe',
                    'help': "Désignez de manière unique cet élément"},
    {'name': 'libelle', 'genre': 'String', 'label': 'Nom', 'value':'MonGroupe',
                    'help': "Nom descriptif du groupe"},
    {'name': 'etendue', 'genre': 'str', 'label': 'Etendue du groupe', 'value': '*',
                    'help': "* rend le groupe accessible à tout agc, sinon préciser l'agc"},
    {'name': 'liste', 'genre': 'texte', 'label': 'Liste membres',
                    'help': "Copier la liste des membres séparés par tab, virgule ou pointvirgule", },
    ],}

MATRICE_CHOIXFILIERE = {
("filiere","Filières constituées"): [
    {'name': 'ID', 'genre': 'String', 'label': 'Code','value':'CodeFilère',
                    'help': "Désignez de manière unique cet élément"},
    {'name': 'libelle', 'genre': 'String', 'label': 'Nom', 'value':'MaFilière',
                    'help': "Nom descriptif de la filière"},
    {'name': 'etendue', 'genre': 'str', 'label': 'Etendue de la filière', 'value': '*',
                    'help': "* rend la filière accessible à tout agc, sinon préciser l'agc"},
    {'name': 'requete', 'genre': 'texte', 'label': 'Requête',
                    'help': "Copier la requête façon access", },
    ],}

IMPLANTATION = {
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

#************************   Gestion de l'identification initiale *****************

def TplsToLDDic(recordset,lstChamps,categorie):
    if len(lstChamps) != len(recordset[0]):
        wx.MessageBox("GestionConfig.TplToDDic : problème de nombre de champs \n%s champs:%s\n%s valeurs:%s"%(len(lstChamps),lstChamps,len(recordset[0]),str(recordset[0])))
        return []
    lst = []
    for record in recordset:
        dic = {categorie: {}}
        for ix in range(len(lstChamps)):
            dic[categorie][lstChamps[ix]] = record[ix]
        lst.append(dic)
    return lst

class DLG_import(wx.Dialog):
    # Ecran de saisie de paramètres en dialog
    def __init__(self, parent,multi = False, *args, **kwds):
        self.multi = multi
        self.lstIDnafs = []
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self, parent, -1,pos=(400,50),title = titre,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.parent = parent
        cadre_staticbox = wx.StaticBox(self, -1)
        topbox = wx.StaticBoxSizer(cadre_staticbox, wx.VERTICAL)
        self.btn = xusp.BTN_action(self,help='Lancement de l\'import',image=wx.Bitmap("xpy/Images/100x30/Bouton_action.png"))
        self.btn.Bind(wx.EVT_BUTTON, self.OnAction)
        self.btnTest = xusp.BTN_action(self,help='Test de l\'accès compta',image=wx.Bitmap("xpy/Images/100x30/Bouton_tester.png"))
        self.btnTest.Bind(wx.EVT_BUTTON, self.OnTestImport)

        def Affiche():

            if self.multi:
                # récupère le premier groupe de paramètres à afficher dans la grille
                code, label, lignes = xgc.AppelLignesMatrice(None, MATRICE_IMPORTMULTI)
                # simple texte d'intro dans la grille
                self.titre = wx.StaticText(self, -1, "Import d\'un groupe de dossiers compta")
            else:
                code,label,lignes = xgc.AppelLignesMatrice(None, MATRICE_IMPORT)
                self.titre =wx.StaticText(self, -1, "Import d'un dossier compta")

            # contrôle gérant la saisie des paramètres de config
            self.ctrlImport = xusp.BoxPanel(self, -1, lblbox=label, code=code, lignes=lignes, dictDonnees={})

            # recherche dans le groupe implantation géré dans la configuration initiale
            cfg = xucfg.ParamUser()
            self.implantation= cfg.GetDict(dictDemande=None, groupe='IMPLANTATION', close=False)
            self.pathCompta = self.implantation['pathCompta']
            #récup de choix antérieurs de cette grille
            self.choix= cfg.GetDict(dictDemande=None, groupe='IMPORT', close=False)
            #pose les valeurs lues dans la grille de saisie
            if 'lstIDnafs' in self.choix:
                self.lstIDnafs = self.choix['lstIDnafs']

            self.ctrlImport.SetValues(self.choix)

            topbox.Add(self.titre, 0, wx.LEFT, 60)
            topbox.Add((20,20), 0, wx.ALIGN_TOP, 0)
            topbox.Add(self.ctrlImport, 0, wx.ALIGN_TOP| wx.EXPAND, 0)
            topbox.Add((40,40), 0, wx.ALIGN_TOP, 0)
            piedbox = wx.BoxSizer(wx.HORIZONTAL)
            piedbox.Add(self.btnTest, 0, wx.ALIGN_RIGHT, 0)
            piedbox.Add(self.btn, 0, wx.RIGHT|wx.ALIGN_RIGHT, 11)
            topbox.Add(piedbox, 0, wx.ALIGN_RIGHT, 0)
        Affiche()
        self.SetSizerAndFit(topbox)

    def CodeClient(self,codeclient):
        if int(codeclient)>0:
            codeclient = "000000"+str(codeclient)
            codeclient = codeclient[-6:]
        return codeclient

    def OnTestImport(self,event):
        self.OnCtrlAction(None)
        if self.implantation['compta'] == 'quadratus':
            ok = False
            if self.multi:
                path = self.pathCompta + '/CPTA/DC/'
                lstDossiers = os.listdir(path)
                nbreDossiers, chemin = 0,''
                for item in lstDossiers:
                    chemin = path+'/'+item+'/Qcompta.mdb'
                    if os.path.exists(chemin) :
                        nbreDossiers += 1
                if nbreDossiers > 0:
                    self.codeclient = chemin.split('/')[-2]
            config = {'typeDB': 'access', 'nameDB': 'Qcompta.mdb'}
            path = self.pathCompta+ '/CPTA/DC/'+self.codeclient
            config['serveur'] = path[:2]+path[2:].replace("//","/")
            DB = xdb.DB(config = config)
            style = wx.ICON_WARNING
            try:
                nomBase = DB.nomBase
                if DB.echec == 0: style = wx.ICON_INFORMATION
                retour = ['avec','sans'][DB.echec]
                if self.multi:
                    mess = "L'accès à l'un des %d dossiers présents s'est réalisé %s succès"%(nbreDossiers,retour)
                else:
                    mess = "L'accès à la base '%s' s'est réalisé %s succès"%(nomBase,retour)
                ok = True
            except: mess = "Désolé "
            if event or not ok:
                wx.MessageBox(mess,style=style)
            DB.Close()
        if not event:
            return ok

    def OnAction(self,event):
        try:
            self.topWindow = wx.GetApp().GetTopWindow()
            if self.topWindow:
                self.topWindow.SetStatusText("Lancement de l'import : patientez...")
        except: pass
        # enregistre les valeurs de l'utilisateur
        cfg = xucfg.ParamUser()
        dic = self.ctrlImport.GetValues()
        cfg.SetDict(dic, groupe='IMPORT')
        # test avant l'import du dossier
        ok = self.OnTestImport(None)
        if ok:
            # lancement proprement dit
            if self.multi:
                imp = orui.ImportComptas(self)
                imp.Import(multi=True,lstNafs=self.lstIDnafs)
                del imp
            else:
                imp = orui.ImportComptas(self)
                imp.Import(multi=False,)
                del imp
        self.Destroy()

    def OnCtrlAction(self,event):
        #action evènement Enter sur le contrôle combo, correspond à un changement de choix
        self.choix = self.ctrlImport.GetValues()
        if self.multi:
            pass
        else:
            self.codeclient = self.CodeClient(self.choix['client'])
            self.choix['client'] = self.codeclient
        cfg = xucfg.ParamUser()
        cfg.SetDict(self.choix, groupe='IMPORT')

    def OnBtnAction(self, event):
        action = 'self.%s(event)'%event.EventObject.actionBtn
        eval(action)

    def OnBtnChoixNafs(self,event):
        # sur clic du bouton pour élargir le choix de la combo
        imp = orui.ImportComptas(self, bases=('gi'))
        # appel des nafs
        annee = self.ctrlImport.GetOneValue('annee')
        lstNafs, nbDossiers = imp.GetNafs(annee)
        # affichage de la liste des nafs
        liste_Colonnes = [
            ColumnDefn("Code Naf", 'left', 80, "code"),
            ColumnDefn("Productions", 'left', 700, "productions"),
            ColumnDefn("Nbre dossiers", 'right', 80, "nbDossiers")]
        dicOlv = {'listeColonnes': liste_Colonnes,
                  'listeDonnees': lstNafs,
                  'longueur': 850,
                  'largeur': 1000,
                  'recherche': True,
                  'msgIfEmpty': "Aucun Naf ne correspond à votre recherche"}
        dlg_olv =  tbl.DLG_tableau(None, dicOlv=dicOlv)
        # cocher les lignes retenues précédement
        if ('lstNafs' in self.choix) and (self.choix['lstNafs'] != []):
            for obj in dlg_olv.ctrlOlv.GetObjects():
                if obj.code in self.choix['lstNafs']:
                    dlg_olv.ctrlOlv.SetCheckState(obj, True)
        ret = dlg_olv.ShowModal()
        if ret == wx.OK:
            # récup des codes nafs checked
            self.lstIDnafs = []
            nbd = 0
            for ligne in dlg_olv.ctrlOlv.GetCheckedObjects() :
                self.lstIDnafs.append(ligne.code)
                nbd +=ligne.nbDossiers
            if nbd>0 : nbDossiers = nbd
            txtNafs = self.GetTexteNafs(self.lstIDnafs,nbDossiers)
            self.ctrlImport.SetOneValue('choix_config.nafs',txtNafs)
            self.choix['lstNafs']=self.lstIDnafs
            cfg = xucfg.ParamUser()
            cfg.SetDict(self.choix, groupe='IMPORT')

    def GetTexteNafs(self,lstIDnafs,nbDossiers):
        if  len(lstIDnafs) > 0:
            txtNafs = '%d codesNaf, %d dossiers'%(len(lstIDnafs),nbDossiers)
        else:
            txtNafs = 'Tous (%d dossiers potentiels)'%nbDossiers
        return txtNafs

class DLG_trait(wx.Dialog):
    # Ecran de saisie de paramètres en dialog
    def __init__(self, parent,multi = None, *args, **kwds):
        self.multi = multi
        self.codeclient = None
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self, parent, -1,pos=(400,50),title = titre,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.parent = parent
        def TakeTwo(matrice):
            # récupère les deux premieres lignes de la matrice
            matretour = {('choix_config','-'):[]}
            for key,valeur in matrice.items():
                for i in range(2):
                    matretour[('choix_config','-')].append(matrice[key][i])
                break
            return matretour

        if self.multi == 'groupe':
            self.client = None
            self.matrice = TakeTwo(MATRICE_EXPORTGROUPE)
            self.titre = wx.StaticText(self, -1, "Génération Produits et Coûts d\'un groupe de dossiers (liste)")
        elif self.multi == 'filiere':
            self.matrice = TakeTwo(MATRICE_EXPORTFILIERE)
            self.titre = wx.StaticText(self, -1, "Génération Produits et Coûts des dossiers d'une filière")
        else:
            self.matrice = TakeTwo(MATRICE_EXPORT)
            self.titre = wx.StaticText(self, -1, "Génération Produits et Coûts d'un dossier")
        cadre_staticbox = wx.StaticBox(self, -1)
        topbox = wx.StaticBoxSizer(cadre_staticbox, wx.VERTICAL)
        self.btn = xusp.BTN_action(self,help='Lancement du traitement',image=wx.Bitmap("xpy/Images/100x30/Bouton_action.png"))
        self.btn.Bind(wx.EVT_BUTTON, self.OnAction)

        def Affiche():
            # récupère les paramètres à afficher dans la grille
            code, label, lignes = xgc.AppelLignesMatrice(None, self.matrice)

            # contrôle gérant la saisie des paramètres
            self.ctrlExport = xusp.BoxPanel(self, -1, lblbox=label, code=code, lignes=lignes, dictDonnees={})

            # recherche dans le groupe implantation géré dans la configuration initiale
            cfg = xucfg.ParamUser()
            self.implantation= cfg.GetDict(dictDemande=None, groupe='IMPLANTATION', close=False)
            self.agc = self.implantation['agc']
            #récup de choix antérieurs de cette grille
            self.choix= cfg.GetDict(dictDemande=None, groupe='EXPORT')
            #pose les valeurs lues dans la grille de saisie
            self.ctrlExport.SetValues(self.choix)

            topbox.Add(self.titre, 0, wx.LEFT, 60)
            topbox.Add((20,20), 0, wx.ALIGN_TOP, 0)
            topbox.Add(self.ctrlExport, 0, wx.ALIGN_TOP| wx.EXPAND, 0)
            topbox.Add((40,40), 0, wx.ALIGN_TOP, 0)
            piedbox = wx.BoxSizer(wx.HORIZONTAL)
            piedbox.Add(self.btn, 0, wx.RIGHT|wx.ALIGN_RIGHT, 11)
            topbox.Add(piedbox, 0, wx.ALIGN_RIGHT, 0)
        Affiche()
        self.SetSizerAndFit(topbox)

    def CodeClient(self,codeclient):
        if codeclient and int(codeclient)>0:
            codeclient = "000000"+str(codeclient)
            codeclient = codeclient[-6:]
        return codeclient

    def OnAction(self,event):
        # enregistre les valeurs de l'utilisateur
        self.OnCtrlAction(None)
        if self.multi == None:
            if not (self.codeclient and self.choix['annee'])  :
                wx.MessageBox('Les champs client et année et sont obligatoires à minima')
        else:
            if not self.choix['annee']:
                wx.MessageBox('Le champ année est obligatoire à minima')
        client = groupe = filiere = None
        if self.multi == 'filiere' : filiere = self.choix['filiere']
        elif self.multi == 'groupe' : groupe = self.choix['groupe']
        else: client = self.choix['client']
        imp = orut.Traitements(annee=self.choix['annee'], client=client, groupe=groupe,
                           filiere= filiere, agc=self.agc)
        self.Destroy()

    def OnCtrlAction(self,event):
        #action evènement Enter sur le contrôle combo, correspond à un changement de choix
        self.choix = self.ctrlExport.GetValues()
        if not self.multi:
            self.codeclient = self.CodeClient(self.choix['client'])
            self.choix['client'] = self.codeclient
        cfg = xucfg.ParamUser()
        cfg.SetDict(self.choix, groupe='EXPORT')
        self.ctrlExport.SetValues(self.choix)

    # paramétrage des boutons d'aide à droite des contrôles
    def OnBtnAction(self, event):
        action = 'self.%s(event)'%event.EventObject.actionBtn
        eval(action)

    def OnBtnChoixAnalyse(self,event):
        # l'agence local étant non liée à une agc elle donne accès à toutes les agc c'est l'agc '*'
        # sur clic du bouton pour élargir le choix de la combo
        self.lstChamps = ['IDanalyse', 'NomAnalyse', 'IDagc', 'Description']
        self.nomTable = "cAnalyses"
        if self.agc == '*':
            self.req = """SELECT cAnalyses.IDanalyse, cAnalyses.NomAnalyse, cAnalyses.IDagc, cAnalyses.Description
                FROM cAnalyses;"""
        else:
            self.req = """SELECT cAnalyses.IDanalyse, cAnalyses.NomAnalyse, cAnalyses.IDagc, cAnalyses.Description
                FROM cAnalyses
                WHERE (cAnalyses.IDagc In ('%s','*')); """%self.agc
        self.matriceParam = MATRICE_CHOIXANALYSE
        self.nameCtrl = 'analyse'
        self.choisi = self.ctrlExport.GetOneValue(self.nameCtrl)
        self.LanceSaisieParams()

    def OnBtnChoixGroupe(self, event):
        self.lstChamps = ['IDgroupe', 'NomGroupe', 'IDagc', 'Membres']
        self.nomTable = "cGroupes"
        if self.agc == '*':
            self.req = """SELECT cGroupes.IDgroupe, cGroupes.NomGroupe, cGroupes.IDagc, cGroupes.Membres
                        FROM cGroupes;"""
        else:
            self.req = """SELECT cGroupes.IDgroupe, cGroupes.NomGroupe, cGroupes.IDagc, cGroupes.Membres
                        FROM cGroupes
                        WHERE (cGroupes.IDagc In ('%s','*')); """%self.agc
        self.matriceParam = MATRICE_CHOIXGROUPE
        self.nameCtrl = 'groupe'
        self.choisi = self.ctrlExport.GetOneValue(self.nameCtrl)
        self.LanceSaisieParams()

    def OnBtnChoixFiliere(self, event):
        self.lstChamps = ['IDfilière', 'NomFilière', 'IDagc', 'Requête']
        self.nomTable = "cFilières"
        if self.agc == '*':
            self.req = """SELECT cFilières.IDfilière, cFilières.NomFilière, cFilières.IDagc, cFilières.Requête
                        FROM cFilières;"""
        else:
            self.req = """SELECT cFilières.IDfilière, cFilières.NomFilière, cFilières.IDagc, cFilières.Requête
                        FROM cFilières
                        WHERE (cFilières.IDagc In ('%s','*')); """%self.agc
        self.matriceParam = MATRICE_CHOIXFILIERE
        self.nameCtrl = 'filiere'
        self.choisi = self.ctrlExport.GetOneValue(self.nameCtrl)
        self.LanceSaisieParams()

    # le lancement de SaisieParams, permet la gestion des lignes affichées gérée au retour ci dessous
    def LanceSaisieParams(self):
        lstcol = []
        categorie = ''
        for bloc in self.matriceParam.keys():
            categorie = bloc[0]
            for ligne in self.matriceParam[bloc]:
                lstcol.append(ligne['name'])
        self.DBsql = xdb.DB()
        gp = xgc.DLG_saisieParams(self)
        retour = self.DBsql.ExecuterReq(self.req, mess='accès OpenRef précharge param')
        dic = {}
        if retour == "ok":
            recordset = self.DBsql.ResultatReq()
            gp.matrice = self.matriceParam
            lddDonnees=TplsToLDDic(recordset,lstcol,categorie)
            gp.lddDonnees = lddDonnees
            gp.init()
            gp.ShowModal()
            value = gp.GetChoix(idxColonne=0)
            nomctrl = 'choix_config.'+self.nameCtrl
            self.ctrlExport.SetOneValue(nomctrl, value)
        del gp

    def Ajouter(self,lstItems):
        self.DBsql.ReqInsert(nomTable=self.nomTable,lstChamps=self.lstChamps,lstlstDonnees=lstItems)

    def Supprimer(self,lstItems):
        condition = "%s = '%s'"%(self.lstChamps[0],lstItems[0])
        self.DBsql.ReqDEL(nomTable=self.nomTable,condition=condition)

    def Modifier(self,lstItems):
        condition = "%s = '%s'"%(self.lstChamps[0],lstItems[0])
        self.DBsql.ReqMAJ(nomTable=self.nomTable,condition= condition, lstChamps=self.lstChamps,lstDonnees=lstItems)

class DLG_affect(wx.Dialog):
    # Ecran de saisie de paramètres en dialog
    def __init__(self, parent,multi = None, *args, **kwds):
        self.multi = multi
        self.codeclient = None
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self, parent, -1,pos=(400,50),title = titre,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.parent = parent
        def TakeTwo(matrice):
            # récupère les deux premieres lignes de la matrice
            matretour = {('choix_config','-'):[]}
            for key,valeur in matrice.items():
                for i in range(2):
                    matretour[('choix_config','-')].append(matrice[key][i])
                break
            return matretour

        if self.multi == 'groupe':
            self.client = None
            self.matrice = TakeTwo(MATRICE_EXPORTGROUPE)
            self.titre = wx.StaticText(self, -1, "Affectation Produits, Coûts, Balances d\'un groupe de dossiers (liste)")
        elif self.multi == 'filiere':
            self.matrice = TakeTwo(MATRICE_EXPORTFILIERE)
            self.titre = wx.StaticText(self, -1, "Affectation Produits, Coûts, Balances des dossiers d'une filière")
        else:
            self.matrice = TakeTwo(MATRICE_EXPORT)
            self.titre = wx.StaticText(self, -1, "Affectation Produits, Coûts, Balances d'un dossier")
        cadre_staticbox = wx.StaticBox(self, -1)
        topbox = wx.StaticBoxSizer(cadre_staticbox, wx.VERTICAL)
        self.btn = xusp.BTN_action(self,help="Lancement de l'écran choix",image=wx.Bitmap("xpy/Images/100x30/Bouton_action.png"))
        self.btn.Bind(wx.EVT_BUTTON, self.OnAction)

        def Affiche():
            # récupère les paramètres à afficher dans la grille
            code, label, lignes = xgc.AppelLignesMatrice(None, self.matrice)

            # contrôle gérant la saisie des paramètres
            self.ctrlExport = xusp.BoxPanel(self, -1, lblbox=label, code=code, lignes=lignes, dictDonnees={})

            # recherche dans le groupe implantation géré dans la configuration initiale
            cfg = xucfg.ParamUser()
            self.implantation= cfg.GetDict(dictDemande=None, groupe='IMPLANTATION', close=False)
            self.agc = self.implantation['agc']
            #récup de choix antérieurs de cette grille
            self.choix= cfg.GetDict(dictDemande=None, groupe='EXPORT')
            #pose les valeurs lues dans la grille de saisie
            self.ctrlExport.SetValues(self.choix)

            topbox.Add(self.titre, 0, wx.LEFT, 60)
            topbox.Add((20,20), 0, wx.ALIGN_TOP, 0)
            topbox.Add(self.ctrlExport, 0, wx.ALIGN_TOP| wx.EXPAND, 0)
            topbox.Add((40,40), 0, wx.ALIGN_TOP, 0)
            piedbox = wx.BoxSizer(wx.HORIZONTAL)
            piedbox.Add(self.btn, 0, wx.RIGHT|wx.ALIGN_RIGHT, 11)
            topbox.Add(piedbox, 0, wx.ALIGN_RIGHT, 0)
        Affiche()
        self.SetSizerAndFit(topbox)

    def CodeClient(self,codeclient):
        if codeclient and int(codeclient)>0:
            codeclient = "000000"+str(codeclient)
            codeclient = codeclient[-6:]
        return codeclient

    def OnAction(self,event):
        # enregistre les valeurs de l'utilisateur
        self.OnCtrlAction(None)
        if self.multi == None:
            if not (self.codeclient and self.choix['annee'])  :
                wx.MessageBox('Les champs client et année et sont obligatoires à minima')
        else:
            if not self.choix['annee']:
                wx.MessageBox('Le champ année est obligatoire à minima')
        client = groupe = filiere = None
        if self.multi == 'filiere' : filiere = self.choix['filiere']
        elif self.multi == 'groupe' : groupe = self.choix['groupe']
        else: client = self.choix['client']
        imp = oruaf.Affectations(annee=self.choix['annee'], client=client, groupe=groupe,
                           filiere= filiere, agc=self.agc)
        self.Destroy()

    def OnCtrlAction(self,event):
        #action evènement Enter sur le contrôle combo, correspond à un changement de choix
        self.choix = self.ctrlExport.GetValues()
        if not self.multi:
            self.codeclient = self.CodeClient(self.choix['client'])
            self.choix['client'] = self.codeclient
        cfg = xucfg.ParamUser()
        cfg.SetDict(self.choix, groupe='EXPORT')
        self.ctrlExport.SetValues(self.choix)

    # paramétrage des boutons d'aide à droite des contrôles
    def OnBtnAction(self, event):
        action = 'self.%s(event)'%event.EventObject.actionBtn
        eval(action)

    def OnBtnChoixAnalyse(self,event):
        # l'agence local étant non liée à une agc elle donne accès à toutes les agc c'est l'agc '*'
        # sur clic du bouton pour élargir le choix de la combo
        self.lstChamps = ['IDanalyse', 'NomAnalyse', 'IDagc', 'Description']
        self.nomTable = "cAnalyses"
        if self.agc == '*':
            self.req = """SELECT cAnalyses.IDanalyse, cAnalyses.NomAnalyse, cAnalyses.IDagc, cAnalyses.Description
                FROM cAnalyses;"""
        else:
            self.req = """SELECT cAnalyses.IDanalyse, cAnalyses.NomAnalyse, cAnalyses.IDagc, cAnalyses.Description
                FROM cAnalyses
                WHERE (cAnalyses.IDagc In ('%s','*')); """%self.agc
        self.matriceParam = MATRICE_CHOIXANALYSE
        self.nameCtrl = 'analyse'
        self.choisi = self.ctrlExport.GetOneValue(self.nameCtrl)
        self.LanceSaisieParams()

    def OnBtnChoixGroupe(self, event):
        self.lstChamps = ['IDgroupe', 'NomGroupe', 'IDagc', 'Membres']
        self.nomTable = "cGroupes"
        if self.agc == '*':
            self.req = """SELECT cGroupes.IDgroupe, cGroupes.NomGroupe, cGroupes.IDagc, cGroupes.Membres
                        FROM cGroupes;"""
        else:
            self.req = """SELECT cGroupes.IDgroupe, cGroupes.NomGroupe, cGroupes.IDagc, cGroupes.Membres
                        FROM cGroupes
                        WHERE (cGroupes.IDagc In ('%s','*')); """%self.agc
        self.matriceParam = MATRICE_CHOIXGROUPE
        self.nameCtrl = 'groupe'
        self.choisi = self.ctrlExport.GetOneValue(self.nameCtrl)
        self.LanceSaisieParams()

    def OnBtnChoixFiliere(self, event):
        self.lstChamps = ['IDfilière', 'NomFilière', 'IDagc', 'Requête']
        self.nomTable = "cFilières"
        if self.agc == '*':
            self.req = """SELECT cFilières.IDfilière, cFilières.NomFilière, cFilières.IDagc, cFilières.Requête
                        FROM cFilières;"""
        else:
            self.req = """SELECT cFilières.IDfilière, cFilières.NomFilière, cFilières.IDagc, cFilières.Requête
                        FROM cFilières
                        WHERE (cFilières.IDagc In ('%s','*')); """%self.agc
        self.matriceParam = MATRICE_CHOIXFILIERE
        self.nameCtrl = 'filiere'
        self.choisi = self.ctrlExport.GetOneValue(self.nameCtrl)
        self.LanceSaisieParams()

    # le lancement de SaisieParams, permet la gestion des lignes affichées gérée au retour ci dessous
    def LanceSaisieParams(self):
        lstcol = []
        categorie = ''
        for bloc in self.matriceParam.keys():
            categorie = bloc[0]
            for ligne in self.matriceParam[bloc]:
                lstcol.append(ligne['name'])
        self.DBsql = xdb.DB()
        gp = xgc.DLG_saisieParams(self)
        retour = self.DBsql.ExecuterReq(self.req, mess='accès OpenRef précharge param')
        dic = {}
        if retour == "ok":
            recordset = self.DBsql.ResultatReq()
            gp.matrice = self.matriceParam
            lddDonnees=TplsToLDDic(recordset,lstcol,categorie)
            gp.lddDonnees = lddDonnees
            gp.init()
            gp.ShowModal()
            value = gp.GetChoix(idxColonne=0)
            nomctrl = 'choix_config.'+self.nameCtrl
            self.ctrlExport.SetOneValue(nomctrl, value)
        del gp

    def Ajouter(self,lstItems):
        self.DBsql.ReqInsert(nomTable=self.nomTable,lstChamps=self.lstChamps,lstlstDonnees=lstItems)

    def Supprimer(self,lstItems):
        condition = "%s = '%s'"%(self.lstChamps[0],lstItems[0])
        self.DBsql.ReqDEL(nomTable=self.nomTable,condition=condition)

    def Modifier(self,lstItems):
        condition = "%s = '%s'"%(self.lstChamps[0],lstItems[0])
        self.DBsql.ReqMAJ(nomTable=self.nomTable,condition= condition, lstChamps=self.lstChamps,lstDonnees=lstItems)

class DLG_export(wx.Dialog):
    # Ecran de saisie de paramètres en dialog
    def __init__(self, parent,multi = None, *args, **kwds):
        self.multi = multi
        self.codeclient = None
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self, parent, -1,pos=(400,50),title = titre,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.parent = parent
        if self.multi == 'groupe':
            self.client = None
            self.matrice = MATRICE_EXPORTGROUPE
            self.titre = wx.StaticText(self, -1, "Export de l\'analyse d\'un groupe de dossiers (liste)")
        elif self.multi == 'filiere':
            self.matrice = MATRICE_EXPORTFILIERE
            self.titre = wx.StaticText(self, -1, "Export de l\'analyse des dossiers d'une filière")
        else:
            self.matrice = MATRICE_EXPORT
            self.titre = wx.StaticText(self, -1, "Export de l\'analyse d'un dossier")

        cadre_staticbox = wx.StaticBox(self, -1)
        topbox = wx.StaticBoxSizer(cadre_staticbox, wx.VERTICAL)
        self.btn = xusp.BTN_action(self,help='Lancement de l\'export',image=wx.Bitmap("xpy/Images/100x30/Bouton_action.png"))
        self.btn.Bind(wx.EVT_BUTTON, self.OnAction)

        def Affiche():
            # récupère les paramètres à afficher dans la grille
            code, label, lignes = xgc.AppelLignesMatrice(None, self.matrice)

            # contrôle gérant la saisie des paramètres
            self.ctrlExport = xusp.BoxPanel(self, -1, lblbox=label, code=code, lignes=lignes, dictDonnees={})

            # recherche dans le groupe implantation géré dans la configuration initiale
            cfg = xucfg.ParamUser()
            self.implantation= cfg.GetDict(dictDemande=None, groupe='IMPLANTATION', close=False)
            self.agc = self.implantation['agc']
            #récup de choix antérieurs de cette grille
            self.choix= cfg.GetDict(dictDemande=None, groupe='EXPORT')
            #pose les valeurs lues dans la grille de saisie
            self.ctrlExport.SetValues(self.choix)

            topbox.Add(self.titre, 0, wx.LEFT, 60)
            topbox.Add((20,20), 0, wx.ALIGN_TOP, 0)
            topbox.Add(self.ctrlExport, 0, wx.ALIGN_TOP| wx.EXPAND, 0)
            topbox.Add((40,40), 0, wx.ALIGN_TOP, 0)
            piedbox = wx.BoxSizer(wx.HORIZONTAL)
            piedbox.Add(self.btn, 0, wx.RIGHT|wx.ALIGN_RIGHT, 11)
            topbox.Add(piedbox, 0, wx.ALIGN_RIGHT, 0)
        Affiche()
        self.SetSizerAndFit(topbox)

    def CodeClient(self,codeclient):
        if codeclient and int(codeclient)>0:
            codeclient = "000000"+str(codeclient)
            codeclient = codeclient[-6:]
        return codeclient

    def OnAction(self,event):
        # enregistre les valeurs de l'utilisateur
        self.OnCtrlAction(None)
        if self.multi == None:
            if not (self.codeclient and self.choix['annee'])  :
                wx.MessageBox('Les champs client et année et sont obligatoires à minima')
        else:
            if not self.choix['annee']:
                wx.MessageBox('Le champ année est obligatoire à minima')
        client = groupe = filiere = None
        if self.multi == 'filiere' : filiere = self.choix['filiere']
        elif self.multi == 'groupe' : groupe = self.choix['groupe']
        else: client = self.choix['client']
        imp = orua.Analyse(analyse=self.choix['analyse'], annee=self.choix['annee'], nbanter=self.choix['nbAnter'], client=client, groupe=groupe,
                           filiere= filiere, gestable=self.choix['gestiontable'], agc=self.agc)
        if len(imp.mess)>0:
            wx.MessageBox("Trace du traitement\n\n%s"%imp.mess)

    def OnCtrlAction(self,event):
        #action evènement Enter sur le contrôle combo, correspond à un changement de choix
        self.choix = self.ctrlExport.GetValues()
        if not self.multi:
            self.codeclient = self.CodeClient(self.choix['client'])
            self.choix['client'] = self.codeclient
        cfg = xucfg.ParamUser()
        cfg.SetDict(self.choix, groupe='EXPORT')
        self.ctrlExport.SetValues(self.choix)

    # paramétrage des boutons d'aide à droite des contrôles
    def OnBtnAction(self, event):
        action = 'self.%s(event)'%event.EventObject.actionBtn
        eval(action)

    def OnBtnChoixAnalyse(self,event):
        # l'agence local étant non liée à une agc elle donne accès à toutes les agc c'est l'agc '*'
        # sur clic du bouton pour élargir le choix de la combo
        self.lstChamps = ['IDanalyse', 'NomAnalyse', 'IDagc', 'Description']
        self.nomTable = "cAnalyses"
        if self.agc == '*':
            self.req = """SELECT cAnalyses.IDanalyse, cAnalyses.NomAnalyse, cAnalyses.IDagc, cAnalyses.Description
                FROM cAnalyses;"""
        else:
            self.req = """SELECT cAnalyses.IDanalyse, cAnalyses.NomAnalyse, cAnalyses.IDagc, cAnalyses.Description
                FROM cAnalyses
                WHERE (cAnalyses.IDagc In ('%s','*')); """%self.agc
        self.matriceParam = MATRICE_CHOIXANALYSE
        self.nameCtrl = 'analyse'
        self.choisi = self.ctrlExport.GetOneValue(self.nameCtrl)
        self.LanceSaisieParams()

    def OnBtnChoixGroupe(self, event):
        self.lstChamps = ['IDgroupe', 'NomGroupe', 'IDagc', 'Membres']
        self.nomTable = "cGroupes"
        if self.agc == '*':
            self.req = """SELECT cGroupes.IDgroupe, cGroupes.NomGroupe, cGroupes.IDagc, cGroupes.Membres
                        FROM cGroupes;"""
        else:
            self.req = """SELECT cGroupes.IDgroupe, cGroupes.NomGroupe, cGroupes.IDagc, cGroupes.Membres
                        FROM cGroupes
                        WHERE (cGroupes.IDagc In ('%s','*')); """%self.agc
        self.matriceParam = MATRICE_CHOIXGROUPE
        self.nameCtrl = 'groupe'
        self.choisi = self.ctrlExport.GetOneValue(self.nameCtrl)
        self.LanceSaisieParams()

    def OnBtnChoixFiliere(self, event):
        self.lstChamps = ['IDfilière', 'NomFilière', 'IDagc', 'Requête']
        self.nomTable = "cFilières"
        if self.agc == '*':
            self.req = """SELECT cFilières.IDfilière, cFilières.NomFilière, cFilières.IDagc, cFilières.Requête
                        FROM cFilières;"""
        else:
            self.req = """SELECT cFilières.IDfilière, cFilières.NomFilière, cFilières.IDagc, cFilières.Requête
                        FROM cFilières
                        WHERE (cFilières.IDagc In ('%s','*')); """%self.agc
        self.matriceParam = MATRICE_CHOIXFILIERE
        self.nameCtrl = 'filiere'
        self.choisi = self.ctrlExport.GetOneValue(self.nameCtrl)
        self.LanceSaisieParams()

    # le lancement de SaisieParams, permet la gestion des lignes affichées gérée au retour ci dessous
    def LanceSaisieParams(self):
        lstcol = []
        categorie = ''
        for bloc in self.matriceParam.keys():
            categorie = bloc[0]
            for ligne in self.matriceParam[bloc]:
                lstcol.append(ligne['name'])
        self.DBsql = xdb.DB()
        gp = xgc.DLG_saisieParams(self)
        retour = self.DBsql.ExecuterReq(self.req, mess='accès OpenRef précharge param')
        dic = {}
        if retour == "ok":
            recordset = self.DBsql.ResultatReq()
            gp.matrice = self.matriceParam
            lddDonnees=TplsToLDDic(recordset,lstcol,categorie)
            gp.lddDonnees = lddDonnees
            gp.init()
            gp.ShowModal()
            value = gp.GetChoix(idxColonne=0)
            nomctrl = 'choix_config.'+self.nameCtrl
            self.ctrlExport.SetOneValue(nomctrl, value)
            #self.ctrlExport.Refresh()
        del gp

    def Ajouter(self,lstItems):
        self.DBsql.ReqInsert(nomTable=self.nomTable,lstChamps=self.lstChamps,lstlstDonnees=lstItems)

    def Supprimer(self,lstItems):
        condition = "%s = '%s'"%(self.lstChamps[0],lstItems[0])
        self.DBsql.ReqDEL(nomTable=self.nomTable,condition=condition)

    def Modifier(self,lstItems):
        condition = "%s = '%s'"%(self.lstChamps[0],lstItems[0])
        self.DBsql.ReqMAJ(nomTable=self.nomTable,condition= condition, lstChamps=self.lstChamps,lstDonnees=lstItems)

class DLG_gestionTables(wx.Dialog):
    # Ecran de saisie de paramètres en dialog
    def __init__(self, parent,multi = False, *args, **kwds):

        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        cfg = xucfg.ParamUser()
        self.implantation = cfg.GetDict(dictDemande=None, groupe='IMPLANTATION', close=False)
        agc = self.implantation['agc']
        wx.Dialog.__init__(self, parent, -1,pos=(550,350),title = titre,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        # recherche de la liste des tables de l'agc
        lstTables = []
        self.DBsql = xdb.DB()
        req = "SHOW TABLES LIKE 'xExp_%s%%';"%(agc)
        ret = self.DBsql.ExecuterReq(req)
        recordset = self.DBsql.ResultatReq()
        if agc != 'ANY':
            req2 = "SHOW TABLES LIKE 'xExp_ANY%%';"
            ret2 = self.DBsql.ExecuterReq(req2)
            recordset.extend(self.DBsql.ResultatReq())
        if len(recordset)>0:
            for table in recordset:
                lstTables.append(table)

        liste_Colonnes = [ColumnDefn("Tables à supprimer", 'left', 240, "table"),]
        dicOlv = {'listeColonnes': liste_Colonnes,
                  'listeDonnees': lstTables,
                  'longueur': 550,
                  'largeur': 350,
                  'recherche': False,
                  'msgIfEmpty': "Aucune Table d'export ne peut être supprimée"}

        self.pnl =  tbl.PNL_tableau(self, dicOlv, **kwds)
        self.myOlv = self.pnl.ctrlOlv
        self.CenterOnScreen()
        self.Layout()

    def Close(self):
        #clic sur le bouton validation
        # récup des noms de tables checked
        tables = []
        for ligne in self.myOlv.GetCheckedObjects() :
            tables.append(ligne.table)
        if len(tables) >0:
            rep = wx.MessageBox("Suppression de %s tables sans retour possible"%len(tables),style=wx.YES_NO)
            if rep == wx.YES:
                for table in tables:
                    req ="""DROP TABLE %s;"""%table
                    ret = self.DBsql.ExecuterReq(req)
                    if ret=='ok':
                        self.DBsql.Commit()
                    else : wx.MessageBox("Echec sur DROP TABLE %s :\n\n%s"%(table,ret))
        self.Destroy()

class DLG_implantation(wx.Dialog):
    # Ecran de saisie de paramètres en dialog
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
            code,label,lignes = xgc.AppelLignesMatrice(None, MATRICE_COMPTA)
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
            piedbox.Add(self.btnTest, 0, wx.ALIGN_RIGHT, 0)
            piedbox.Add(self.btn, 0, wx.RIGHT|wx.ALIGN_RIGHT, 11)
            topbox.Add(piedbox, 0, wx.ALIGN_RIGHT, 0)

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
        #le dictionnaire choix contiendra tous les choix utiles saisis ou dérivés
        self.choix = self.ctrlConfig.GetValues()
        agc = None
        # détermination de l'agc selon la localisation
        for cle, value in AGENCES.items():
            if self.choix['localis'] in value:
                agc = cle
        self.choix['agc'] = agc
        # calcul de l'implantation
        pathCompta = IMPLANTATION[self.choix['compta']][self.choix['localis']]
        self.choix['pathCompta'] = pathCompta
        if self.choix['compta'] == 'quadratus':
            self.choix['typeDB']='access'
            self.choix['nameDB']='qgi.mdb'
            pathGI = IMPLANTATION['quadratus'][self.choix['localis']]+ '/gi/0000/'
            self.choix['serveur'] = pathGI.replace('datadouble','database')
        cfg = xucfg.ParamUser()
        cfg.SetDict(self.choix, groupe='IMPLANTATION')

#************************   Pour Test ou modèle  *********************************
if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    frame_1 = DLG_import(None,multi=True)
    frame_1.Position = (50,50)
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()

