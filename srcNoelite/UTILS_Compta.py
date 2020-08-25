# !/usr/bin/env python
# -*- coding: utf-8 -*-

#----------------------------------------------------------------------------
# Application :    Projet Noelite, outils pour compta
# Licence:         Licence GNU GPL
#----------------------------------------------------------------------------

import wx
import xpy.xUTILS_Config    as xucfg
import xpy.xUTILS_SaisieParams    as xusp
import xpy.xGestionConfig   as xgc
import xpy.xGestionDB       as xdb

class Compta(object):
    def __init__(self,parent,compta='quadra'):
        self.DB = self.DB(parent,compta)

        self.dicTables = None
        if self.DB and self.DB.echec:
            self.DB = None
        if self.DB:
            self.dicTables = self.GetTables(compta)

    def DB(self,parent,compta):
        # recherche des configuration d'accès aux base de données clé 'db_prim'
        paramFile = xucfg.ParamFile(nomFichier="Config")
        dicConfig = paramFile.GetDict(None, 'CONFIGS')
        if not 'lstConfigs' in dicConfig.keys(): dicConfig['lstConfigs'] = []
        if not 'lstIDconfigs' in dicConfig.keys(): dicConfig['lstIDconfigs'] = []
        lddDonnees = dicConfig['lstConfigs']
        ixCompta = None
        for config in lddDonnees:
            if 'db_prim' in config.keys():
                if config['db_prim']['ID'] == compta:
                    configCpta = config['db_prim']
                    ixCompta = lddDonnees.index(config)
        ret = wx.ID_OK
        while ret and not ixCompta:
            #todo
            pass

        if not ixCompta:
            # gestion d'une configuration nouvelle
            dlgGest = xusp.DLG_vide(self)
            # récup de la matrice ayant servi à la gestion des données
            key = ("db_prim","Accès Base de donnée")
            matrice = {key:xgc.MATRICE_CONFIGS[key]}
            # suppose le champ ID en première position
            matrice[key][0]['value']=compta
            # grise le champ ID
            xusp.SetEnableID(matrice,False)
            dlgGest.pnl = xusp.TopBoxPanel(dlgGest, matrice=matrice, lblbox='Ajout d\'un accès pour la compta')
            dlgGest.Sizer(dlgGest.pnl)
            ret = dlgGest.ShowModal()
            if ret == wx.OK:
                ddDonnees = dlgGest.pnl.GetValeurs()
                configCpta = ddDonnees['db_prim']
                # test de l'accès
                db = xdb.DB(config=configCpta)
                db.AfficheTestOuverture()
                echec = db.echec
                db.Close()
                if not echec:
                    # sauve
                    lddDonnees.append(ddDonnees)
                    dicConfig['lstIDconfigs'].append(ddDonnees['ID'])
                    cfg = xucfg.ParamFile()
                    cfg.SetDict({'lstIDconfigs': dicConfig['lstIDconfigs']}, 'CONFIGS', close=False)
                    cfg.SetDict({'lstConfigs': lddDonnees}, 'CONFIGS')

        if configCpta:
            return xdb.DB(config=configCpta)


    def GetTables(self,compta):
        self.dicCompta = {}
        cfgCompta = xucfg.ParamFile(nomFichier="Comptas")
        self.dicCompta = cfgCompta.GetDict(None,name='quadra')



# --------------- TESTS ----------------------------------------------------------
if __name__ == u"__main__":
    import os
    os.chdir("..")
    app = wx.App(0)
    cpt = Compta(None,compta='quadra')
    print(cpt.dicTables)
    app.MainLoop()
