# !/usr/bin/env python
# -*- coding: utf-8 -*-

#----------------------------------------------------------------------------
# Application :    Projet XPY, gestion de paramètres
# Auteurs:          Jacques BRUNEL
# Copyright:       (c) 2019-04     Cerfrance Provence, Matthania
# Licence:         Licence GNU GPL
#----------------------------------------------------------------------------

import wx
import os
import xpy.outils.xtableaux as xtbl

class DLG_saisieConfig(xtbl.DLG_listCtrl):
    # Ecran de saisie de paramètres en dialog
    def __init__(self, parent, *args, **kwds):
        super().__init__(parent, *args, **kwds)
        self.parent = parent
        self.dlColonnes = {}
        self.lddDonnees = []
        self.dldMatrice = {}
        # composition des paramètres
        # seuls les paragraphes option choisis par l'appli et présents dans MATRICE_CONFIGS seront appelés.
        self.gestionProperty = False
        self.ok = False
        if 'OPTIONSCONFIG' in self.parent.dictAppli:
            for option in self.parent.dictAppli['OPTIONSCONFIG']:
                present = False
                liste = ''
                for code,chapitre in MATRICE_CONFIGS:
                    liste += code + ', '
                    if option == code:
                        present = True
                        self.dldMatrice[(code,chapitre)] = MATRICE_CONFIGS[(code,chapitre)]
                        if code in COLONNES_CONFIGS:
                            self.dlColonnes[code] = COLONNES_CONFIGS[code]
                if not present :
                    wx.MessageBox("L'option '%s' n'est pas dans la liste :\n %s "%(option, liste))
            cfg = xucfg.ParamFile()
            dic= cfg.GetDict(None,'CONFIGS')
            if 'lstConfigs' in dic:
               if dic['lstConfigs']:self.lddDonnees += dic['lstConfigs']
            # paramètres pour self.pnl contenu principal de l'écran
            self.kwds['lblbox'] = 'Configuations disponibles'
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
        for ligne in self.lddDonnees:
            for cle, valeurs  in ligne.items():
                if 'ID' in valeurs.keys():
                   conf = valeurs['ID']
            configs.append(conf)
        cfg = xucfg.ParamFile()
        cfg.SetDict({'lstIDconfigs': configs}, 'CONFIGS', close=False )
        cfg.SetDict({'lstConfigs':self.lddDonnees}, 'CONFIGS')
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

#************************   Pour Test ou modèle  *********************************
if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    frame_1 = DLG_identification(None)
    frame_1.Position = (50,50)
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()

