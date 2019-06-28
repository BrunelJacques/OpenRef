# !/usr/bin/env python
# -*- coding: utf-8 -*-

#---------------------------------------------------------------------------------------------
# Application :    Projet XPY, gestion de paramètres, différentes formes de grilles de saisie
# Auteurs:          Jacques BRUNEL
# Copyright:       (c) 2019-04     Cerfrance Provence, Matthania
# Licence:         Licence GNU GPL
#----------------------------------------------------------------------------------------------

import wx
import os
import wx.propgrid as wxpg
import copy

def Transpose(matrice,dlColonnes,lddDonnees):
    # Transposition des lignes de la matrice pour présentation colonnes dans le format grille listCtrl
    def LtColonnes(dlColonnes, matrice):
        #Ajoute le format aux colonnes
        ltColonnes=[]
        for code in dlColonnes:
            for colonne in dlColonnes[code]:
                cle = None
                for (cat,libel) in matrice.keys():
                    if cat == code : cle = (cat,libel)
                if cle :
                    for ligne in matrice[cle]:
                        if 'name' in ligne:
                            if colonne in ligne['name']:
                                if 'genre' in ligne:
                                    if ligne['genre'] in ['Float','Int']: format = 'RIGHT'
                                    elif ligne['genre'] in ['Check','Bool']: format = 'CENTER'
                                    else: format = 'LEFT'
                                namecol = code + '.' + ligne['name']
                                if not 'label' in ligne:
                                    wx.MessageBox("Pb de matrice : il faut un champ 'label' dans le dictionnaire ci dessous\n%s" % ligne)
                                ltColonnes.append((namecol,ligne['label'],format))
                        else : wx.MessageBox("Pb de matrice : il faut un champ 'name' dans le dictionnaire ci dessous\n%s"%ligne)
        return ltColonnes

    def LlItems(ltColonnes,lddDonnees):
        llItems = []
        for ddDonnees in lddDonnees:
            lItems = []
            for (namecol, label, format) in ltColonnes:
                [code, champ] = namecol.split('.')
                valeur = ''
                for code, dictDonnee in ddDonnees.items():
                    if champ in dictDonnee:
                        valeur = dictDonnee[champ]
                lItems.append(valeur)
            llItems.append(lItems)
        return llItems

    # si pas de liste de colonnes pour une catégorie c'est toutes les colonnes qui sont prises
    for (codm, label) in matrice:
        if not codm in dlColonnes:
            dlColonnes[codm] = []
            for ligne in matrice[(codm, label)]:
                if ('name' in ligne):
                    if not 'pass' in ligne['name'].lower():
                        dlColonnes[codm].append(ligne['name'])
    ltColonnes = LtColonnes(dlColonnes, matrice)
    llItems = LlItems(ltColonnes, lddDonnees)
    return lddDonnees, ltColonnes, llItems

def Normalise(genre, name, label, value):
    #gestion des approximations de cohérence
    genre = genre.lower()
    if not name : name = 'noname'
    if not isinstance(name,str): name = str(name)
    if not label: label = name
    if genre in ('int','wxintproperty'):
        if not isinstance(value, int): value = 0
    elif genre in ('float','wxfloatproperty'):
        if not isinstance(value, float): value = 0.0
    elif genre in ['bool', 'check','wxboolproperty']:
        if not isinstance(value, bool): value = True
    elif genre in ['enum', 'combo','wxenumproperty']:
        if not isinstance(value, int): value = 0
    elif (genre in ['multichoice']):
        if (not isinstance(value, list)): value = []
    else :
        if not isinstance(value,str) :
            if not value: value=''
            value = str(value)
    return genre,name,label,value

#**********************************************************************************
#                   GESTION des CONTROLES UNITES : Grilles ou composition en panel
#**********************************************************************************

class BTN_reinitialisation(wx.BitmapButton):
    # à parfaire
    def __init__(self, parent, ctrl_parametres=None):
        wx.BitmapButton.__init__(self, parent, wx.ID_ANY, wx.Bitmap("xpy/Images/16x16/Actualiser.png", wx.BITMAP_TYPE_ANY))
        self.ctrl_parametres = ctrl_parametres
        self.SetToolTip(("Cliquez ici pour réinitialiser tous les paramètres"))
        self.Bind(wx.EVT_BUTTON, self.OnBouton)
    def OnBouton(self, event):
        self.ctrl_parametres.Reinitialisation()

class BTN_action(wx.BitmapButton):
    def __init__(self, parent, image=None, help='', action=None):
        if not image: image=wx.Bitmap("xpy/Images/16x16/Loupe.png")
        wx.BitmapButton.__init__(self, parent, wx.ID_ANY, bitmap=image, )
        self.SetToolTip(help)
        self.Bind(wx.EVT_BUTTON, action)

class BTN_fermer(wx.BitmapButton):
    def __init__(self, parent):
        wx.BitmapButton.__init__(self, parent, wx.ID_ANY, wx.Bitmap("xpy/Images/100x30/Bouton_ok.png", wx.BITMAP_TYPE_ANY))
        self.SetToolTip(("Cliquez ici pour enregistrer et fermer la fenêtre"))

class BTN_esc(wx.BitmapButton):
    def __init__(self, parent, image=None, action=None):
        if not image: image=wx.Bitmap("xpy/Images/100x30/Bouton_annuler.png",wx.BITMAP_TYPE_ANY)
        wx.BitmapButton.__init__(self, parent, wx.ID_ANY, bitmap=image, )
        self.SetToolTip(("Cliquez ici pour abandonner et fermer la fenêtre"))
        self.Bind(wx.EVT_BUTTON, action)

class CTRL_property(wxpg.PropertyGrid):
    # grille property affiche les paramètres gérés par PNL_property
    def __init__(self, parent, matrice={}, valeursDefaut={}, enable=True, style=wxpg.PG_SPLITTER_AUTO_CENTER):
        wxpg.PropertyGrid.__init__(self, parent, wx.ID_ANY, style=style)
        self.parent = parent
        self.dictValeursDefaut = valeursDefaut
        self.Bind(wxpg.EVT_PG_CHANGED, self.OnPropGridChange)
        if not enable:
            self.Enable(False)
            couleurFond = wx.LIGHT_GREY
            self.SetCaptionBackgroundColour(couleurFond)
            self.SetCellBackgroundColour(couleurFond)
            self.SetMarginColour(couleurFond)
            self.SetEmptySpaceColour(couleurFond)

        # Remplissage de la matrice
        self.InitMatrice(matrice)

        # Remplissage des valeurs
        if len(self.dictValeursDefaut) > 0:
            self.SetValeurs(self.dictValeursDefaut)

    def OnPropGridChange(self, event):
        event.Skip()

    def InitMatrice(self, matrice={}):
        # Compose la grille de saisie des paramètres selon le dictionnaire matrice
        for (code, chapitre) in matrice:
            # Chapitre
            if isinstance(chapitre, str):
                self.Append(wxpg.PropertyCategory(chapitre))
                for ligne in matrice[(code, chapitre)]:
                    if 'name' in ligne and 'genre' in ligne:
                        if not 'label' in ligne : ligne['name'] = None
                        if not 'value' in ligne : ligne['value'] = None
                        codeName = code + '.' + ligne['name']
                        genre, name, label, value = Normalise(ligne['genre'],codeName,ligne['label'],ligne['value'])
                        if not 'labels' in ligne: ligne['labels'] = []
                        if 'values' in ligne and ligne['values']:
                            if ligne['labels']:
                                if len(ligne['values']) > 0 and len(ligne['labels']) == 0:
                                    ligne['labels'] = ligne['values']
                            else: ligne['labels'] = ligne['values']
                        commande = ''
                        try:
                            commande = genre
                            if genre in ['enum','combo']:
                                values = list(range(0,len(ligne['labels'])))
                                choix = wxpg.PGChoices(ligne['labels'], values=[])
                                propriete = wxpg.EnumProperty(label, name,
                                                              choix,
                                                              value)
                            elif genre == 'multichoice':
                                propriete = wxpg.MultiChoiceProperty(label, name, choices=ligne['labels'], value=value)

                            elif genre in ['bool','check']:
                                wxpg.PG_BOOL_USE_CHECKBOX = 1
                                propriete = wxpg.BoolProperty(label= label, name=name, value= value)
                                propriete.PG_BOOL_USE_CHECKBOX = 1


                            elif genre == 'dir':
                                propriete = wxpg.DirProperty(name)

                            else:
                                commande = "wxpg." + genre.upper()[:1] + genre.lower()[1:] + "Property(label= label, name=name, value=value)"
                                propriete = eval(commande)
                            if 'help' in ligne:
                                propriete.SetHelpString(ligne['help'])
                            self.Append(propriete)

                        except Exception as err:
                            wx.MessageBox(
                            "Echec sur Property de name - value: %s - %s (%s)\nLe retour d'erreur est : \n%s\n\nSur commande : %s"
                            %(name,value,type(value),err,commande),
                            'CTRL_property.InitMatrice() : Paramètre ligne indigeste !', wx.OK | wx.ICON_STOP
                            )

    def Reinitialisation(self):
        dlg = wx.MessageDialog(None, ("Souhaitez-vous vraiment réinitialiser tous les paramètres ?"),
                               ("Paramètres par défaut"), wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse == wx.ID_YES:
            self.SetValeurs(self.dictValeursDefaut)

    def SetValeurs(self, ddDonnees={}):
        # Alimente les valeurs dans la grille en composant le nom avec le code
        for code, valeurs in ddDonnees.items():
            for champ, valeur in valeurs.items():
                nom = code + '.' +champ
                #n = self.GetLastItem().GetName()
                propriete = self.GetPropertyByName(nom)
                if propriete:
                    genre = propriete.GetClassName()
                    label = propriete.GetName()
                    genre,nom,label,valeur = Normalise(genre,nom,label,valeur)
                    propriete.SetValue(valeur)
                    #propriete.SetAttribute('TE_PASSWORD',1)
                    # if propriete.GetClassName() = 'wxEnumProperty'
                    # propriete.SetChoices(choix)

    def GetValeurs(self):
        values = self.GetPropertyValues()
        ddDonnees = {}
        for nom, valeur in values.items():
            [code, champ] = nom.split('.')
            if not code in ddDonnees : ddDonnees[code] = {}
            ddDonnees[code][champ] = valeur
        return ddDonnees

class PNL_param_property(wx.Panel):
    #affichage d'une grille property avec boutons sauvegarde réinit
    def __init__(self, parent, topWin, *args, matrice={}, donnees={}, lblbox="Paramètres property", **kwds):
        self.parent = parent
        wx.Panel.__init__(self, parent, *args, **kwds)

        #********************** CTRL PRINCIPAL ***************************************
        self.ctrl = CTRL_property(self,matrice,donnees)
        #***********************************************************************

        self.bouton_action = BTN_action(self,image=wx.Bitmap("xpy/Images/16x16/Ajouter.png"),help="Créer une sauvegarde",action=self.OnSauvegarde )
        self.bouton_reinit = BTN_reinitialisation(self, self.ctrl)
        cadre_staticbox = wx.StaticBox(self,wx.ID_ANY,label=lblbox)
        topbox = wx.StaticBoxSizer(cadre_staticbox,wx.HORIZONTAL)
        topbox.Add(self.ctrl,1,wx.ALL|wx.EXPAND,4)
        droite_flex = wx.FlexGridSizer(2,1,0,0)
        droite_flex.Add(self.bouton_action, 0, wx.ALL|wx.TOP, 4)
        droite_flex.Add(self.bouton_reinit, 0, wx.ALL|wx.TOP, 4)
        topbox.Add(droite_flex,0,wx.ALL|wx.TOP,1)
        topbox.MinSize = (300,400)
        self.SetSizerAndFit(topbox)

    def OnSauvegarde(self, event):
        # Action du clic sur l'icone sauvegarde renvoie au parent
        if self.parent:
            self.parent.OnChildSauvegarde(event)
        else:
            print("Bonjour l'action sauvegarde du parent de PNL_property")

    def GetValeurs(self):
        return self.ctrl.GetValeurs()

    def SetValeurs(self,donnees):
        ret = self.ctrl.SetValeurs(donnees)
        return ret

class PNL_property(wx.Panel):
    #affichage d'une grille property sans autre bouton que sortie
    def __init__(self, parent, topWin, *args, matrice={}, donnees=[], lblbox="Paramètres item_property", **kwds):
        self.parent = parent
        wx.Panel.__init__(self, parent, *args, **kwds)

        #********************** CTRL PRINCIPAL ***************************************
        self.ctrl = CTRL_property(self,matrice,donnees)
        #***********************************************************************

        cadre_staticbox = wx.StaticBox(self,wx.ID_ANY,label=lblbox)
        topbox = wx.StaticBoxSizer(cadre_staticbox)
        topbox.Add(self.ctrl,1,wx.ALL|wx.EXPAND,4)
        #topbox.MinSize = (300,400)
        self.SetSizerAndFit(topbox)

    def GetValeurs(self):
        return self.ctrl.GetValeurs()

    def SetValeurs(self,donnees):
        ret = self.ctrl.SetValeurs(donnees)
        return ret

class PNL_ctrl(wx.Panel):
    # Panel contenant un contrôle ersatz d'une ligne de propertyGrid et en option (code) un bouton d'action permettant de contrôler les saisies
    # GetValue retourne la valeur choisie dans le ctrl avec action possible par bouton à droite
    def __init__(self, parent, *args, genre='string', name=None, label=None, value= None, labels=[], values=[], help=None,
                 btnLabel=None, btnHelp=None, btnAction='', ctrlAction='', **kwds):
        wx.Panel.__init__(self,parent,*args, **kwds)
        self.value = value
        if btnLabel :
            self.avecBouton = True
        else: self.avecBouton = False

        self.MaxSize = (2000, 35)
        self.txt = wx.StaticText(self, wx.ID_ANY, label + " :")
        self.txt.MinSize = (150, 65)

        # seul le PropertyGrid gère le multichoice, pas le comboBox
        if genre == 'multichoice': genre = 'combo'
        lgenre,lname,llabel,lvalue = Normalise(genre, name, label, value)
        if not labels: labels = []
        if not values: values = []
        if len(values) > 0 and len(labels) == 0:
            labels = values

        try:
            commande = 'debut'
            # construction des contrôles selon leur genre
            if lgenre in ['enum','combo','multichoice']:
                self.ctrl = wx.ComboBox(self, wx.ID_ANY)
                if labels:
                    commande = 'Set in combo'
                    self.ctrl.Set(labels)
                    if isinstance(lvalue,list): lvalue=lvalue[0]
                    if isinstance(lvalue,int): lvalue=labels[lvalue]
                    self.ctrl.SetValue(lvalue)
                else: lvalue = None

            elif lgenre in ['bool', 'check']:
                self.ctrl = wx.CheckBox(self, wx.ID_ANY)
                self.UseCheckbox = 1

            else:
                style = wx.TE_PROCESS_ENTER
                if lname:
                    if 'pass' in lgenre:
                        lgenre = 'str'
                        style = wx.TE_PASSWORD | wx.TE_PROCESS_ENTER
                self.ctrl = wx.TextCtrl(self, wx.ID_ANY, style=style)

            if lvalue:
                commande = 'Set Value'
                if lgenre in ['int','float']:
                    lvalue = str(lvalue)
                self.ctrl.SetValue(lvalue)
            if help:
                self.ctrl.SetToolTip(help)
                self.txt.SetToolTip(help)
            if lgenre == 'dir':
                self.avecBouton = True
                if not btnLabel: btnLabel = '...'
                self.btn = wx.Button(self, wx.ID_ANY, btnLabel, size=(30, 20))
                self.btn.Bind(wx.EVT_BUTTON, self.OnDir)
            elif self.avecBouton:
                self.btn = wx.Button(self, wx.ID_ANY, btnLabel, size=(30, 20))
                if btnHelp:
                    self.btn.SetToolTip(btnHelp)
            self.BoxSizer()

        except Exception as err:
            wx.MessageBox(
                "Echec sur PNL_ctrl de genre - name - value: %s - %s - %s (%s)\n\nLe retour d'erreur est : \n%s\n\nSur commande : %s"
                % (lgenre, name, value, type(value), err, commande),
                'PNL_ctrl.__init__() : Paramètre de ligne indigeste !', wx.OK | wx.ICON_STOP
            )

    def BoxSizer(self):
        topbox = wx.BoxSizer(wx.HORIZONTAL)
        topbox.Add(self.txt,0, wx.LEFT|wx.TOP|wx.ALIGN_TOP, 4)
        topbox.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, 4)
        if self.avecBouton:
            topbox.Add(self.btn, 0, wx.ALL|wx.EXPAND, 4)
        self.SetSizer(topbox)

    def GetValue(self):
        return self.ctrl.GetValue()

    def SetValue(self,value):
        if value: self.ctrl.SetValue(value)

    def SetValues(self,values):
        self.ctrl.Set(values)

    def OnDir(self,event):
        """ Open a file"""
        self.dirname = ''
        dlg = wx.DirDialog(self, "Choisissez un emplacement", self.dirname)
        if dlg.ShowModal() == wx.ID_OK:
            self.ctrl.SetValue(dlg.GetPath())
        dlg.Destroy()

#**********************************************************************************
#                   GESTION des COMPOSITIONS DE CONTROLES
#**********************************************************************************

class PNL_listCtrl(wx.Panel):
    #affichage d'une listeCtrl avec les boutons classiques pour gérer les lignes
    def __init__(self, parent, *args, ltColonnes=[], llItems=[], lblbox="Paramètres listCtrl", **kwds):
        self.parent = parent
        self.llItems = llItems
        self.ltColonnes = ltColonnes
        self.colonnes = []
        self.lddDonnees = []

        wx.Panel.__init__(self, parent, wx.ID_ANY, *args, **kwds)


        #********************** Objet principal *******************************
        self.ctrl = wx.ListCtrl(self, wx.ID_ANY, style=wx.LC_REPORT|wx.LC_SINGLE_SEL)
        #**********************************************************************

        # Remplissage de la matrice
        ret = self.InitMatrice(ltColonnes)
        # Remplissage des valeurs
        self.SetValeurs(llItems,ltColonnes)

        self.bouton_ajouter = BTN_action(self,image=wx.Bitmap("xpy/Images/16x16/Ajouter.png"),help="Créer une nouvelle ligne",action=self.OnAjouter )
        self.bouton_modifier = BTN_action(self,image=wx.Bitmap("xpy/Images/16x16/Modifier.png"),help="Modifier la ligne selectionnée",action=self.OnModifier )
        self.bouton_supprimer = BTN_action(self,image=wx.Bitmap("xpy/Images/16x16/Supprimer.png"),help="Supprimer la ligne selectionée",action=self.OnSupprimer )
        self.bouton_dupliquer = BTN_action(self,image=wx.Bitmap("xpy/Images/16x16/Dupliquer.png"),help="Dupliquer la ligne selectionée",action=self.OnDupliquer )
        cadre_staticbox = wx.StaticBox(self,wx.ID_ANY,label=lblbox)
        topbox = wx.StaticBoxSizer(cadre_staticbox,wx.HORIZONTAL)
        topbox.Add(self.ctrl,1,wx.ALL|wx.EXPAND,4)
        droite_flex = wx.FlexGridSizer(4,1,0,0)
        droite_flex.Add(self.bouton_ajouter, 0, wx.ALL|wx.TOP, 4)
        droite_flex.Add(self.bouton_modifier, 0, wx.ALL|wx.TOP, 4)
        droite_flex.Add(self.bouton_supprimer, 0, wx.ALL|wx.TOP, 4)
        droite_flex.Add(self.bouton_dupliquer, 0, wx.ALL|wx.TOP, 4)
        topbox.Add(droite_flex,0,wx.ALL|wx.TOP,1)
        topbox.MinSize = (300,400)
        self.SetSizerAndFit(topbox)

    def InitMatrice(self, ltColonnes=[]):
        # Compose la grille de saisie des paramètres selon la liste colonnes
        for (name, label, format) in ltColonnes:
                format = eval("wx.LIST_FORMAT_%s" % format.upper())
                self.ctrl.AppendColumn( label, format, width=100)
        return 'fin matrice'

    def SetValeurs(self, llItems=[], ltColonnes=[]):
        # Alimente les valeurs dans la grille
        self.ctrl.DeleteAllItems()
        for items in llItems:
            self.ctrl.Append(items)
        i=0
        for colonne in ltColonnes:
            self.ctrl.SetColumnWidth(i,wx.LIST_AUTOSIZE_USEHEADER)
            i+=1

    def OnAjouter(self, event):
        # Action du clic sur l'icone sauvegarde renvoie au parent
        self.parent.OnAjouter(event)

    def OnModifier(self, event):
        # Action du clic sur l'icone sauvegarde renvoie au parent
        if self.ctrl.GetSelectedItemCount() == 0:
            wx.MessageBox("Pas de sélection faite, pas de modification possible !" ,
                                'La vie est faite de choix', wx.OK | wx.ICON_INFORMATION)
            return
        self.parent.OnModifier(event,self.ctrl.GetFirstSelected())

    def OnSupprimer(self, event):
        if self.ctrl.GetSelectedItemCount() == 0:
            wx.MessageBox("Pas de sélection faite, pas de suppression possible !",
                      'La vie est faite de choix', wx.OK | wx.ICON_INFORMATION)
            return
        # Action du clic sur l'icone sauvegarde renvoie au parent
        self.parent.OnSupprimer(event,self.ctrl.GetFirstSelected())

    def OnDupliquer(self, event):
        if self.ctrl.GetSelectedItemCount() == 0:
            wx.MessageBox("Pas de sélection faite, pas de duplication possible !",
                      'La vie est faite de choix', wx.OK | wx.ICON_INFORMATION)
            return
        # Action du clic sur l'icone sauvegarde renvoie au parent
        self.parent.OnDupliquer(event,self.ctrl.GetFirstSelected())

class BoxPanel(wx.Panel):
    # aligne les contrôles définis par la matrice dans une box verticale
    def __init__(self, parent, *args, lblbox="Box", code = '1', lignes=[], dictDonnees={}, **kwds):
        wx.Panel.__init__(self,parent, *args, **kwds)
        self.parent = parent
        self.code = code
        self.lstPanels=[]
        self.champsItem = ('name', 'label', 'ctrlAction', 'btnLabel', 'btnAction', 'value', 'labels', 'values')
        self.dictDonnees = dictDonnees
        self.ssbox = wx.BoxSizer(wx.VERTICAL)
        self.InitMatrice(lignes)

    def InitMatrice(self,lignes):
        for ligne in lignes:
            kwds={}
            for nom,valeur in ligne.items():
               kwds[nom] = valeur
            if 'genre' in ligne:
                panel = PNL_ctrl(self, **kwds)
                if ligne['genre'].lower() in ['bool', 'check']:
                    self.UseCheckbox = 1
                if panel:
                    for cle in self.champsItem:
                        if not cle in ligne:
                            ligne[cle]=None
                    self.ssbox.Add(panel,1,wx.ALL|wx.EXPAND,4)
                    codename = self.code + '.' + ligne['name']
                    panel.ctrl.genreCtrl = ligne['genre']
                    panel.ctrl.nameCtrl = codename
                    panel.ctrl.labelCtrl = ligne['label']
                    panel.ctrl.actionCtrl = ligne['ctrlAction']
                    panel.ctrl.valueCtrl = ligne['value']
                    panel.ctrl.valuesCtrl = ligne['values']
                    panel.ctrl.labelsCtrl = ligne['labels']
                    if panel.avecBouton and ligne['genre'].lower() != 'dir' :
                        panel.btn.nameBtn = codename
                        panel.btn.labelBtn = ligne['btnLabel']
                        panel.btn.actionBtn = ligne['btnAction']
                        command = 'panel.btn.Bind(wx.EVT_BUTTON,self.parent.%s)' % ligne['btnAction']
                        try:
                            eval(command)
                        except Exception as err:
                            wx.MessageBox("\nMatrice, Echec de la ligne : '%s'\n %s\nSur commande : %s\n" %(codename, err, command),
                            'BoxPanel.panel.btn : Paramètre ligne indigeste !', wx.OK | wx.ICON_STOP)
                            if 'btnAction' in ligne:
                                panel.btn.Bind(wx.EVT_BUTTON,self.parent.OnBouton)
                    if 'ctrlAction' in ligne:
                        panel.ctrl.Bind(wx.EVT_TEXT_ENTER,self.parent.OnEnter)
                        panel.ctrl.Bind(wx.EVT_COMBOBOX, self.parent.OnEnter)
                        panel.ctrl.Bind(wx.EVT_CHECKBOX, self.parent.OnEnter)
                    self.lstPanels.append(panel)
        self.SetSizerAndFit(self.ssbox)

    def GetValues(self):
        for panel in self.lstPanels:
            [code, champ] = panel.ctrl.nameCtrl.split('.')
            self.dictDonnees[champ] = panel.GetValue()
        return self.dictDonnees

    def SetValues(self,dictDonnees):
        for panel in self.lstPanels:
            [code, champ] = panel.ctrl.nameCtrl.split('.')
            if champ in dictDonnees:
                panel.SetValue(dictDonnees[champ])
        return

    def GetOneValue(self,name = ''):
        value = None
        self.dictDonnees = self.GetValues()
        if name in self.dictDonnees:
            value = self.dictDonnees[name]
        return value

    def SetOneValue(self,name = '', value=None):
        ctrl = None
        for panel in self.lstPanels:
            if panel.ctrl.nameCtrl == name:
                    panel.SetValue(value)
        return

    def SetOneValues(self,name = '', values=None):
        ctrl = None
        if values:
            for panel in self.lstPanels:
                if panel.ctrl.nameCtrl == name:
                    ctrl = panel.ctrl
                    if panel.ctrl.genreCtrl.lower() in ['enum', 'combo']:
                        panel.SetValues(values)
        return

class TopBoxPanel(wx.Panel):
    #gestion de pluieurs BoxPanel juxtaposées horisontalement
    def __init__(self, parent, topWin, *args, matrice={}, donnees={}, lblbox="Paramètres top", **kwds):
        wx.Panel.__init__(self,parent,*args, **kwds)
        self.parent = parent

        cadre_staticbox = wx.StaticBox(self,wx.ID_ANY,label=lblbox)
        self.topbox = wx.StaticBoxSizer(cadre_staticbox,wx.HORIZONTAL)
        self.ddDonnees = donnees
        self.lstBoxes = []
        for code, label in matrice:
            if isinstance(code,str):
                if not code in self.ddDonnees:
                     self.ddDonnees[code] = {}
                box = BoxPanel(self, wx.ID_ANY, lblbox=label, code = code, lignes=matrice[(code,label)], dictDonnees=self.ddDonnees[code])
                self.lstBoxes.append(box)
                self.topbox.Add(box, 1, wx.EXPAND,0)
        self.SetSizerAndFit(self.topbox)

    def OnEnter(self,event):
        self.parent.OnChildEnter(event)

    def OnBouton(self,event):
        self.parent.OnBouton(event)

    def GetValeurs(self):
        ddDonnees = {}
        for box in self.lstBoxes:
            dic = box.GetValues()
            ddDonnees[box.code] = dic
        return ddDonnees

    def SetValeurs(self, ddDonnees):
        for box in self.lstBoxes:
            if box.code in ddDonnees:
                dic = ddDonnees[box.code]
                box.SetValues(dic)
        return

class DLG_vide(wx.Dialog):
    def __init__(self,parent, *args, **kwds):
        self.parent = parent
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self,parent,*args, title=titre, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, **kwds)
        self.SetBackgroundColour(wx.WHITE)
        self.marge = 10

        #****************Exemple de Chaînage à faire passer au sizer*****************
        #self.pnl = PNL_property(self, parent, *args, matrice = matrice, **kwds )
        #****************************************************************************

    def Bouton(self,parent):
        self.btnLabel = 'OK'
        self.btn = wx.Button(self, wx.ID_ANY, self.btnLabel)
        self.btn.Bind(wx.EVT_BUTTON, parent.OnFermer)

    def Sizer(self,panel,bouton=None):
        self.pnl = panel
        if bouton:
            self.btn = bouton
        else: self.Bouton(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.pnl, 1, wx.EXPAND | wx.ALL, self.marge)
        sizer.Add(self.btn, 0,  wx.ALIGN_RIGHT | wx.RIGHT,40)
        sizer.SetSizeHints(self)
        self.SetSizer(sizer)

    def OnFermer(self, event):
            if self.parent != None:
                self.EndModal(wx.OK)
                #self.parent.OnChildAction(event)
            else:
                print("Bonjour l'Action de DLG_vide")

    def OnChildSauvegarde(self, event):
            if self.parent != None:
                self.parent.OnChildAction(event)
            else:
                print("Bonjour Sauvegarde de DLG_vide")

    def OnChildEnter(self, event):
            if self.parent != None:
                self.EndModal(wx.OK)
                #self.parent.OnChildAction(event)
            else:
                print("Bonjour l'Action de DLG_vide")

class DLG_listCtrl(wx.Dialog):
    #Dialog contenant le PNL_listCtrl qui intégre la gestion ajout,
    # modif par PorpertyGrid ou PanelsCtrl (cf propriété  gestionProperty )...
    """
    dldMatrice contient les lignes de descriptif des champs gérés :
            dict{(code,label): groupe} de liste[champ1, ] de dict{attrib:valeur,}
    dlColonnes contient les listes des champs affichés dans les colonnes de la grille de type ListCtrl:
            dict{code:groupe,}  de liste[champ1, ]
    lddDonnees est une liste de dictionnaires dont les clés sont les champs et les valeurs celle des items de la ligne.

    Par Transpose() ces infos sont restituées dans ltColonnes liste de tuples descritif ordonné des colonnes
            et llItems liste des lignes, listes d'items (autant que de colonnes)
    """
    def __init__(self,parent, *args, dldMatrice={}, dlColonnes={}, lddDonnees=[], **kwds):
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        super().__init__(parent, wx.ID_ANY, *args, title=titre,  style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER , **kwds)

        #pour une gestion simplifiée sans mot de passe caché ni checkbox ni gestion d'action de contrôle : gestionProperty True
        self.gestionProperty = True
        self.SetBackgroundColour(wx.WHITE)
        self.parent = parent
        self.dlColonnes=dlColonnes
        self.dldMatrice = dldMatrice
        self.lddDonnees = lddDonnees
        self.args = args
        self.kwds = kwds
        self.marge = 10
        # bouton bas d'écran
        self.btn = BTN_fermer(self)
        self.btn.Bind(wx.EVT_BUTTON, self.OnFermer)
        self.btnEsc = BTN_esc(self,action=self.OnBtnEsc)
        self.MinSize = (400, 300)

    def Init(self):
        if self.dldMatrice != {}:
            # transposition avant appel du listCtrl
            self.lddDonnees, self.ltColonnes, self.llItems\
                = Transpose(self.dldMatrice, self.dlColonnes, self.lddDonnees)
            #********************** Chaînage *******************************
            self.kwds['ltColonnes'] = self.ltColonnes
            self.kwds['llItems'] = self.llItems
            self.pnl = PNL_listCtrl(self, *self.args, **self.kwds )
            #***************************************************************
        self.Sizer()

    def Sizer(self):
        topbox = wx.BoxSizer(wx.VERTICAL)
        topbox.Add(self.pnl, 1,wx.EXPAND | wx.ALL, self.marge)
        btnbox = wx.BoxSizer(wx.HORIZONTAL)
        btnbox.Add(self.btnEsc, 0,  wx.ALIGN_RIGHT | wx.RIGHT,40)
        btnbox.Add(self.btn, 0,  wx.ALIGN_RIGHT | wx.RIGHT,40)
        topbox.Add(btnbox,0,wx.ALIGN_RIGHT)
        topbox.SetSizeHints(self)
        self.SetSizer(topbox)

    def OnAjouter(self,event):
        # l'ajout d'une config nécessite d'appeler un écran avec les champs en lignes
        dlgGest = DLG_vide(self,)
        if self.gestionProperty:
            dlgGest.pnl = PNL_property(dlgGest, self, matrice=self.dldMatrice, lblbox='Ajout d\'une ligne')
        else:
            dlgGest.pnl = TopBoxPanel(dlgGest, self, matrice=self.dldMatrice, lblbox='Ajout d\'une ligne')
        dlgGest.Sizer(dlgGest.pnl)
        ret = dlgGest.ShowModal()
        if ret == wx.OK:
            #récupération des valeurs saisies
            ddDonnees = dlgGest.pnl.GetValeurs()
            donnees = copy.deepcopy(ddDonnees)
            self.lddDonnees.append(donnees)
            self.lddDonnees, self.ltColonnes, self.llItems = Transpose(self.dldMatrice, self.dlColonnes, self.lddDonnees)
            self.pnl.SetValeurs(self.llItems, self.ltColonnes)
        dlgGest.Destroy()

    def OnModifier(self,event, items):
        # documentation dans dupliquer
        dlgGest = DLG_vide(self, )
        ddDonnees = copy.deepcopy(self.lddDonnees[items])

        if self.gestionProperty:
            dlgGest.pnl = PNL_property(dlgGest, self, matrice=self.dldMatrice)
        else:
            dlgGest.pnl = TopBoxPanel(dlgGest, self, matrice=self.dldMatrice, lblbox='Modification d\'une ligne')
        dlgGest.pnl.SetValeurs(ddDonnees)
        dlgGest.Sizer(dlgGest.pnl)
        ret = dlgGest.ShowModal()
        if ret == wx.OK:
            ddDonnees = dlgGest.pnl.GetValeurs()
            self.lddDonnees[items] = copy.deepcopy(ddDonnees)
            self.lddDonnees, self.ltColonnes, self.llItems = Transpose(self.dldMatrice, self.dlColonnes, self.lddDonnees)
            self.pnl.SetValeurs(self.llItems, self.ltColonnes)
        self.pnl.ctrl.Select(items)
        dlgGest.Destroy()

    def OnSupprimer(self,event,items):
        # documentation dans dupliquer
        del self.lddDonnees[items]
        self.lddDonnees, self.ltColonnes, self.llItems = Transpose(self.dldMatrice,
                                         self.dlColonnes, self.lddDonnees)
        self.pnl.SetValeurs(self.llItems, self.ltColonnes)

    def OnDupliquer(self,event, items):
        dlgGest = DLG_vide(self, )
        ddDonnees = copy.deepcopy(self.lddDonnees[items])
        if self.gestionProperty:
            dlgGest.pnl = PNL_property(dlgGest, self, matrice=self.dldMatrice)
        else:
            dlgGest.pnl = TopBoxPanel(dlgGest, self, matrice=self.dldMatrice, lblbox='Modification d\'une ligne')
        dlgGest.pnl.SetValeurs(ddDonnees)
        dlgGest.Sizer(dlgGest.pnl)
        ret = dlgGest.ShowModal()
        if ret == wx.OK:
            ddDonnees = dlgGest.pnl.GetValeurs()
            donnees = copy.deepcopy(ddDonnees)
            self.lddDonnees.append(donnees)
            self.lddDonnees, self.ltColonnes, self.llItems = Transpose(self.dldMatrice, self.dlColonnes, self.lddDonnees)
            self.pnl.SetValeurs(self.llItems, self.ltColonnes)
        dlgGest.Destroy()

    def OnFermer(self, event):
        return self.Close()

    def OnBtnEsc(self, event):
            self.Destroy()

#************************   Pour Test ou modèle  *********************************

class xFrame(wx.Frame):
    # reçoit les controles à gérer sous la forme d'un ensemble de paramètres
    def __init__(self, *args, matrice={}, donnees={}, btnaction=None, lblbox="Paramètres xf", **kwds):
        listArbo=os.path.abspath(__file__).split("\\")
        self.parent = None
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Frame.__init__(self,*args, title=titre, **kwds)
        self.topPnl = TopBoxPanel(self,wx.ID_ANY, matrice=matrice, donnees=donnees, lblbox=lblbox)
        self.btn0 = wx.Button(self, wx.ID_ANY, "Action Frame")
        self.btn0.Bind(wx.EVT_BUTTON,self.OnBoutonAction)
        self.marge = 10
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.topPnl, 0, wx.LEFT|wx.EXPAND,self.marge)
        sizer_1.Add(self.btn0, 0, wx.RIGHT|wx.ALIGN_TOP,self.marge)
        self.SetSizerAndFit(sizer_1)
        self.CentreOnScreen()

    def OnEnter(self,event):
        print('Bonjour Enter sur le ctrl : ',event.EventObject.Name)
        print(event.EventObject.genreCtrl, event.EventObject.nameCtrl, event.EventObject.labelCtrl,)
        print('Action prévue : ',event.EventObject.actionCtrl)

    def OnBouton(self,event):
        print('Vous avez cliqué sur le bouton')
        print(event.EventObject.Name)
        print( event.EventObject.nameBtn, event.EventObject.labelBtn,)
        print('vous avez donc souhaité : ',event.EventObject.actionBtn)

    def OnSauvegarde(self, event):
        #Bouton Test
        print("Bonjour l'action de sauvegarde dans la frame")

    def OnBoutonAction(self, event):
        #Bouton Test
        print("Bonjour l'action OnBoutonAction de l'appli")
    def OnChildEnter(self, event,*args):
            if self.parent != None:
                self.EndModal(wx.OK)
                #self.parent.OnChildAction(event)
            else:
                print("Bonjour l'Action de xFrame")

class FramePanels(wx.Frame):
    def __init__(self, *args, **kwds):
        # cette frame moins paramétrée ne passe pas par des panels multilignes
        # elle appelle un à un les panels des controles
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Frame.__init__(self,*args, title=titre, **kwds)
        self.Size = (600,400)
        def ComposeDonnees():
            self.combo1 = PNL_ctrl(self,wx.ID_ANY,
                                genre="combo",
                                label="Le nom du choix PEUT être long ",
                                labels=["ceci est parfois plus long, plus long qu'un autre", 'cela', 'ou un autre', 'la vie est faite de choix'],
                                help="Je vais vous expliquer",
                                btnLabel=" ! ",
                                btnHelp="Là vous pouvez lancer une action par clic")

            self.combo2 = PNL_ctrl(self,wx.ID_ANY,genre="combo",label="Le nom2",values=['ceci', 'cela', 'ou un autre', 'la vie LOong fleuve tranquile'],help="Je vais vous expliquer",btnLabel="...", btnHelp="Là vous pouvez lancer une action de gestion des choix possibles")
            self.combo3 = PNL_ctrl(self,wx.ID_ANY,genre="combo",label="Le nom3 plus long",values=['ceci sans bouton', 'cela', 'ou un autre', 'la vie EST COURTE'], btnHelp="Là vous pouvez lancer une action telle que la gestion des choix possibles")
            self.ctrl1 = PNL_ctrl(self,wx.ID_ANY,genre="string",label="Un ctrl à saisir",value='monchoix', help="Je vais vous expliquer",)
            self.ctrl2 = PNL_ctrl(self,wx.ID_ANY,genre="string",label="Avec bouton de ctrl",value='monchoix étendu', help="Je vais vous expliquer", btnLabel="Ctrl", btnHelp="Là vous pouvez lancer une action de validation")
        ComposeDonnees()
        self.combo1.btn.Bind(wx.EVT_BUTTON,self.OnBoutonActionCombo1)
        self.combo2.btn.Bind(wx.EVT_BUTTON,self.OnBoutonActionCombo2)
        self.ctrl2.btn.Bind(wx.EVT_BUTTON,self.OnBoutonActionTexte2)

        self.marge = 10
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add((10,10), 0, wx.LEFT|wx.ALIGN_TOP,self.marge)
        sizer_1.Add(self.combo1, 1, wx.LEFT|wx.ALIGN_TOP,self.marge)
        sizer_1.Add(self.combo2, 1, wx.LEFT|wx.ALIGN_TOP,self.marge)
        sizer_1.Add(self.ctrl1, 1, wx.LEFT|wx.ALIGN_TOP,self.marge)
        sizer_1.Add(self.combo3, 1, wx.LEFT|wx.ALIGN_TOP,self.marge)
        sizer_1.Add(self.ctrl2, 1, wx.LEFT|wx.ALIGN_TOP,self.marge)
        self.SetBackgroundColour(wx.WHITE)
        self.SetSizer(sizer_1)
        self.Layout()
        self.CentreOnScreen()

    def OnBoutonActionCombo1(self, event):
        #Bouton Test
        print("Bonjour l'action OnBoutonActionCombo1 de l'appli")
        self.combo1.btn.SetLabel("Clic")

    def OnBoutonActionCombo2(self, event):
        #Bouton Test
        print("Bonjour l'action OnBoutonActionCombo2 de l'appli")
        self.combo2.ctrl.Set(["Crack","boum","hue"])
        self.combo2.ctrl.SetSelection (0)

    def OnBoutonActionTexte2(self, event):
        #Bouton Test
        print("Bonjour l'action OnBoutonActionCombo2 de l'appli")
        wx.MessageBox("Houston nous avons un problème!",style=wx.OK)
        self.ctrl2.ctrl.SetValue("corrigez")

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dictDonnees = {"bd_reseau": {'serveur': 'mon serveur','bdReseau':False, 'utilisateur' : 'moi-meme','config': 1, 'monTexte': "élève", 'choix': ["choix2", "choix3"],'multi':["choixmulti1", "choimulti2"]},"ident": {'domaine': 'mon domaine'}}
    dictMatrice = {
        ("ident", "Votre session"):
            [
                {'genre': 'String', 'name': 'domaine', 'label': 'Votre organisation', 'value': "NomDuPC",
                                 'help': 'Ce préfixe à votre nom permet de vous identifier'},
                {'genre': 'String', 'name': 'utilisateur', 'label': 'Votre identifiant', 'value': "NomSession",
                                 'help': 'Confirmez le nom de sesssion de l\'utilisateur'},
            ],
        ("choix_config", "Choisissez votre configuration"):
            [
                {'genre': 'Enum', 'name': 'config', 'label': 'Configuration active','labels':['a','b','c'], 'value':2,
                 'help': "Le bouton de droite vous permet de créer une nouvelle configuration"},
                 {'genre': 'MultiChoice', 'name': 'multi', 'label': 'Configurations','labels':['aa','bb','cc'], 'value':['1','2'],
                 'help': "Le bouton de droite vous permet de créer une nouvelle configuration",
                 'btnLabel': "...", 'btnHelp': "Cliquez pour gérer les configurations",
                 'btnAction': 'OnEnter'},
            ],
        ("bd_reseau", "Base de donnée réseau"):
            [
                {'genre': 'Dir', 'name': 'localisation', 'label': 'Répertoire de localisation',
                 'value': True,
                 'help': "Il faudra connaître les identifiants d'accès à cette base"},
                {'genre': 'String', 'name': 'serveur', 'label': 'Nom du serveur', 'value': '',
                 'help': "Il s'agit du serveur de réseau porteur de la base de données"},
            ]
        }

# Lancement des tests

    """
    """

    frame_4 = DLG_listCtrl(None,dldMatrice=dictMatrice, dlColonnes={'bd_reseau':['serveur'],'ident':['utilisateur']},
                lddDonnees=[dictDonnees,dictDonnees,{"bd_reseau":{'serveur': 'serveur3'}}])
    frame_4.Init()
    app.SetTopWindow(frame_4)
    frame_4.Show()

    frame_3 = DLG_vide(None,)
    pnl = PNL_property(frame_3,frame_3,matrice=dictMatrice,donnees=dictDonnees)
    frame_3.Sizer(pnl)
    app.SetTopWindow(frame_3)
    frame_3.Show()

    frame_2 = FramePanels(None, )
    frame_2.Position = (500,300)
    frame_2.Show()

    frame_1 = xFrame(None, matrice=dictMatrice, donnees=dictDonnees)
    app.SetTopWindow(frame_1)
    frame_1.Position = (50,50)
    frame_1.Show()
    """
    """
    app.MainLoop()
