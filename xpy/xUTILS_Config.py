# !/usr/bin/env python
# -*- coding: utf-8 -*-

#----------------------------------------------------------------------------
# Application :    Projet XPY, gestion des paramètres de configuration
#                  soit dans un fichier user soit dans un repertoire partagé
# Licence:         Licence GNU GPL
#----------------------------------------------------------------------------

import wx
import os
import shelve

def ListToDict(lstCles,lstValeurs):
    dict = {}
    if isinstance(lstCles,list):
        for cle in lstCles:
            idx = lstCles.index(cle)
            dict[cle] = None
            if isinstance(lstValeurs, list) and len(lstValeurs) >= idx:
                dict[cle] = lstValeurs[idx]
    return dict

def DictToList(dic):
    lstCles = []
    lstValeurs = []
    if isinstance(dic,dict):
        for cle,valeur in dic.items():
            lstCles.append(cle)
            lstValeurs.append(valeur)
    return lstCles,lstValeurs

def DumpFile(dic):
        print(len(dic)," groupes")
        print()
        def DumpDic(dic,nbtab):
            nbtab+=2
            for cle, valeur in dic.items():
                if isinstance(valeur, (dict,list)):
                    print(nbtab * '\t',cle,'( %s %d val): '%(type(valeur), len(valeur)))
                else: print(nbtab * '\t', cle, ' : ' , valeur)
                if isinstance(valeur,dict): DumpDic(valeur,nbtab)
                if isinstance(valeur, list): DumpList(valeur, nbtab)
        def DumpList(lst,nbtab):
            nbtab+=2
            for valeur in lst:
                if isinstance(valeur, (dict,list)):
                    print(nbtab * '\t', '( %s %d valeurs ): ' % (type(valeur), len(valeur)))
                else: print(nbtab * '\t',  valeur)
                if isinstance(valeur,dict): DumpDic(valeur,nbtab)
                if isinstance(valeur, list): DumpList(valeur, nbtab)
        DumpDic(dic,-1)

def CreePath(path):
    cree = False
    # normalise la chaîne puis crée les répertoires nécessaires pour le chemin
    if not (path[-1:] in ['/', '\\']): path += '/'
    path = path.replace('\\', '/')
    path = path[0:2] + path[2:].replace('//', '/')
    arboresc = path.split('/')
    rep = ''
    premier = True
    for mot in arboresc:
        rep += mot + '/'
        if mot != '':
            # le premier mot de l'arborescence est sensé exister
            if not premier:
                if not os.path.exists(rep):
                    os.makedirs(rep)
                    cree = True
            premier = False
    if cree:
        print("Creation du repertoire : ", path)
    return path

class ParamFile():
    # Gestion des paramètres dans un fichier via Shelve
    def __init__(self, nomFichier='Config', path='', versus='data',flag='c', close=True):
        # recherche des configs dans la frame de lancement avec clé 'versus', puis dans UserProfile ou Data
        # le fichier est vu comme un quasi-dictionnaire il contient le dictionnaire du groupe de paramètres
        # le versus 'data' ou 'user' sera la clé de stockage en mémoire dictMem
        self.versus = versus
        self.close = close
        self.topWin = False
        self.dictMem= {}

        try :
            topWindow = wx.GetApp().GetTopWindow()
            nomWindow = topWindow.GetName()
            if nomWindow :
                # il y a une frame en top windows on va l'utiliser comme tampon mémoire
                if not 'config' in topWindow.__dir__():
                    topWindow.config = {}
                self.dictMem = topWindow.config[self.versus]
                self.topWin = True
        except : pass

        if path == '':
            if self.topWin and 'pathData' in topWindow.__dir__():
                path = topWindow.pathData
            else :
                # on va chercher dans userConfig
                cfg = ParamUser()
                config = cfg.GetDict(dictDemande={'pathData':''}, groupe='APPLI')
                path = config['pathData']
                del cfg
        if path == '':
            path = '../xpy/Data/'

        # ouvre le fichier et le crée si nécessaire
        # création du chemin et de tous les répertoires nécessaires
        self.dictFic = {}
        if not path: path = '/'
        if flag in ('c','n'):
            path = CreePath(path)
        if not (path[-1:] in ['/','\\'] ): path +='/'
        path = path.replace('\\','/')
        path = path[0:2]+path[2:].replace('//','/')
        chemin = path+nomFichier
        if os.path.isfile(chemin+'.dat') or flag == 'c':
            self.dictFic = shelve.open(chemin, flag)
        else:
            self.dictFic = {}
            self.close = False
        if self.dictMem == {}:
            for cle, valeur in self.dictFic.items():
                self.dictMem[cle] = valeur

    def GetDict(self,dictDemande=None, groupe=None, close=True):
        """ Recupere une copie du dictionnaire demandé ds le fichier de config
            Si dictDemande est None c'est l'ensemble du groupe,
            Si groupe est None : recherché dans l'ensemble des groupes"""
        dictDonnees = {}
        if dictDemande == {} : dictDemande = None
        if groupe and (not (groupe in self.dictMem.keys())):
            if groupe in self.dictFic.keys():
                self.dictMem[groupe] = self.dictFic[groupe]

        def GetListKey(groupe):
            # liste des clés à Synchroniser
            # si présence d'un dictionnaire en entrée, on le met à jour sinon c'est tout le groupe
            if dictDemande:
                for key in dictDemande.keys(): self.dicKeys[key] = 0
            else :
                if groupe in self.dictMem.keys():
                    for key in self.dictMem[groupe].keys(): self.dicKeys[key] = 0
                elif groupe in self.dictFic.keys():
                    for key in self.dictFic[groupe].keys(): self.dicKeys[key] = 0

        def GetDictGroupe(groupe):
            # les données peuvent être à différents endroits : priorité au premier dictionnaire pointé
            for key in self.dicKeys:
                #recherche par priorité inversée
                if self.dicKeys[key]==0:
                    dictDonnees[key] = None
                    # valeur par défaut si non présente
                    if dictDemande:
                        if key in dictDemande.keys():
                            dictDonnees[key] = dictDemande[key]
                    self.dicKeys[key] = 1
                if self.dicKeys[key] < 2:
                    # recherche dans le deuxième dictionnaire
                    if groupe in self.dictFic:
                        #if isinstance(groupe,dict):
                            if key in self.dictFic[groupe]:
                                dictDonnees[key] = self.dictFic[groupe][key]
                                self.dicKeys[key] = 2
                if self.dicKeys[key] < 3:
                    # recherche dans le premier dictionnaire
                    if groupe in self.dictMem.keys():
                        if isinstance(self.dictMem[groupe],dict):
                            if key in self.dictMem[groupe].keys():
                                dictDonnees[key] = self.dictMem[groupe][key]
                                self.dicKeys[key] = 3

        self.dicKeys = {}
        if groupe :
            GetListKey(groupe)
            GetDictGroupe(groupe)
        else :
            for groupe in self.dictMem.keys():
                GetListKey(groupe)
                GetDictGroupe(groupe)

        if self.topWin and close and self.close : self.dictFic.close()
        return dictDonnees

    def SetDict(self,dictEnvoi=None,groupe=None, close=True, memOnly=False):
        """ Ajoute ou met à jour les clés du dictionnaire ds le fichier de config
            par défaut ce sera le groupe param si groupe est None"""
        if groupe and (not (groupe in self.dictMem.keys())):
            self.dictMem[groupe]={}
            if groupe in self.dictFic:
                self.dictMem[groupe] = self.dictFic[groupe]
            else: self.dictFic[groupe] = {}

        if not groupe: groupe = 'param'

        for key in dictEnvoi.keys():
            self.dictMem[groupe][key] = dictEnvoi[key]

        if not memOnly:
            # double enregistrement
            self.dictFic[groupe] = self.dictMem[groupe]

        if close and self.close:
            self.dictFic.close()
        return

    def DelDictConfig(self, groupe=None, close=True):
        """ Supprime le dict du fichier de config présent sur le disque """
        if groupe in self.dictMem:
                del self.dictMem[groupe]
             #double enregistrement
        if groupe in self.dictFic:
            del self.dictFic[groupe]
        if close and self.close:
            self.dictFic.close()
        return

class ParamUser(ParamFile):
    # Gestion des paramètres dans un fichier créé dans USERPROFILE
    def __init__(self, nomFichier='UserConfig', **kwds):
        pathUser = os.environ['USERPROFILE']
        if (not pathUser ) or (len(pathUser)<2): pathUser = '/'
        pathUser = pathUser.replace('\\','/')+'/'
        ParamFile.__init__(self,nomFichier,pathUser,'user',**kwds)

# --------------- TESTS ----------------------------------------------------------
if __name__ == u"__main__":
    app = wx.App(0)
    print('Fichier Data.Config')
    cfg = ParamFile('Config',flag='r')
    DumpFile(cfg.dictFic)
    print('Fichier UserProfile.UserConfig')
    cfg = ParamUser('UserConfig', flag = 'r')
    DumpFile(cfg.dictFic)
    #cfg = ParamUser('UserConfig', flag='c')
    #cfg.DelDictConfig(groupe='IMPLANTATION')

    """
    from random import randrange
    cfg = ParamUser(nomFichier='testConfig', flag = 'r')
    print("GET :", cfg.GetDict(None,groupe='mongroupe'))
    cfg = ParamUser(nomFichier='testConfig', flag = 'c')
    args =({"test1": randrange(0,100), "test2" : 125.77, "test4":{1:10,2:20,3:30}})
    cfg.SetDict(args,groupe='mongroupe')
    print("SET :", args)
    cfg = ParamUser(nomFichier='testConfig', flag = 'r')
    print("GET :", cfg.GetDict({"test1": 'test1 echoué'},groupe='mongroupe'))
    cfg = ParamUser(nomFichier='testConfig', flag = 'r')
    print("GET :", cfg.GetDict(None, None))
    """
    app.MainLoop()
