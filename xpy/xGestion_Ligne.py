# !/usr/bin/env python
# -*- coding: utf-8 -*-

#---------------------------------------------------------------------------------------------
# Application :    Projet XPY, gestion en vertical d'une ligne record de table
# Auteurs:          Jacques BRUNEL
# Copyright:       (c) 2019-10  Cerfrance Provence - Matthania
# Licence:         Licence GNU GPL
#----------------------------------------------------------------------------------------------

import wx
import datetime
import os
import wx.propgrid as wxpg
import unicodedata
import xpy.outils.xformat as xfmt
from xpy.outils.ObjectListView import ColumnDefn

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
    elif genre in ['date','time','datetime']:
        if not isinstance(value,(wx.DateTime)): value = wx.DateTime.Today()
    else :
        if not isinstance(value,str) :
            if not value: value=''
            value = str(value)
    return genre,name,label,value

def SupprimeAccents(texte):
    # met en minuscule sans accents et sans caractères spéciaux
    code = ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')
    #code = str(unicodedata.normalize('NFD', texte).encode('ascii', 'ignore'))
    code = code.lower()
    code = ''.join(car.lower() for car in code if car not in " %)(.[]',;/\n")
    return code

def DefColonnes(lstNoms,lstCodes,lstValDef,lstLargeur):
    # Composition d'une liste de définition de colonnes d'un OLV; remarque faux ami: 'nom, code' == 'label, name'
    ix=0
    for lst in (lstCodes,lstValDef,lstLargeur):
        # complète les listes entrées si nécessaire
        if lst == None : lst = []
        if len(lst)< len(lstNoms):
            lst.extend(['']*(len(lstNoms)-len(lst)))
    lstColonnes = []
    for colonne in lstNoms:
        if isinstance(lstValDef[ix],(str,wx.DateTime)):
            posit = 'left'
        else: posit = 'right'
        # ajoute un converter à partir de la valeur par défaut
        if isinstance(lstValDef[ix], (float,)):
            if '%' in colonne:
                stringConverter = xfmt.FmtPercent
            else:
                stringConverter = xfmt.FmtInt
        elif isinstance(lstValDef[ix], int):
            stringConverter = xfmt.FmtInt
        elif isinstance(lstValDef[ix], (datetime.date,wx.DateTime)):
            stringConverter = xfmt.FmtDate
        else: stringConverter = None
        if lstLargeur[ix] in ('',None,'None',-1):
            lstLargeur[ix] = -1
            isSpaceFilling = True
        else: isSpaceFilling = False
        lstColonnes.append(ColumnDefn(title=colonne,align=posit,width=lstLargeur[ix],valueGetter=lstCodes[ix],valueSetter=lstValDef[ix],
                                      isSpaceFilling=isSpaceFilling,stringConverter=stringConverter))
        ix += 1
    return lstColonnes

def ExtractList(lstin, champDeb=None, champFin=None):
    # Extraction d'une sous liste à partir du contenu des items début et fin
    lstout = []
    if champDeb in lstin:
        ix1 = lstin.index(champDeb)
    else:
        ix1 = 0
    if champFin in lstin:
        ix2 = lstin.index(champFin)
    elif champFin in ('last','dernier','tous'):
        ix2 = len(lstin)-1
    else:
        ix2 = ix1
    for ix in range(ix1, ix2 + 1):
        lstout.append(lstin[ix])
    return lstout

def ComposeMatrice(lstChamps=[],lstTypes=[],lstHelp=[],record=(),dicOptions={},lstCodes=None):
    # Retourne une matrice (liste de dic[param]:valeurParam) et  donnees (dic[codechamp]:valeur)
    options = {}
    for key, dic in dicOptions.items():
        options[SupprimeAccents(key)] = dic
    if lstCodes:
        lstCodesColonnes = lstCodes
    else:
        lstCodesColonnes = [SupprimeAccents(x) for x in lstChamps]
    if len(lstTypes) < len(lstChamps) and len(record) == len(lstChamps):
        lstTypes = []
        for valeur in record:
            if not valeur: valeur = ''
            if isinstance(valeur, bool): tip = 'bool'
            elif isinstance(valeur, int): tip = 'int'
            elif isinstance(valeur, float): tip = 'float'
            elif isinstance(valeur, datetime.date): tip = 'date'
            else: tip = 'str'
            if tip == 'str' and len(valeur)>200: tip = 'longstring'
            lstTypes.append(tip)

    ldmatrice = []
    def Genre(tip):
        if tip[:3] == 'int':
            genre = 'int'
        elif tip == 'tinyint(1)':
            genre = 'bool'
        elif tip[:7] == 'varchar':
            genre = 'string'
            if len(tip) == 12 and tip[8] > '2': genre = 'longstring'
            if len(tip) > 12: genre = 'longstring'
        elif 'blob' in tip:
            genre = 'blob'
        else:
            genre = tip
        return genre

    for nom, code in zip(lstChamps, lstCodesColonnes):
        ix = lstChamps.index(nom)
        dicchamp = {
            'genre': Genre(lstTypes[ix]),
            'name': code,
            'label': nom,
            'help': lstHelp[ix]
        }
        # Présence de la définition d'options ou dérogations au standart
        if code in options:
            for key,item in options[code].items():
                dicchamp[key]=item
        ldmatrice.append(dicchamp)

    # composition des données
    dicdonnees = {}
    for nom, code in zip(lstChamps, lstCodesColonnes):
        ix = lstChamps.index(nom)
        if len(record) > ix:
            dicdonnees[code] = record[ix]
    return ldmatrice, dicdonnees

def ValeursDefaut(lstNomsColonnes,lstChamps,lstTypes):
    # Détermine des valeurs par défaut selon le type des variables
    lstValDef = []
    for colonne in lstNomsColonnes:
        tip = lstTypes[lstChamps.index(colonne)]
        if tip[:3] == 'int': lstValDef.append(0)
        elif tip[:10] == 'tinyint(1)': lstValDef.append(True)
        elif tip[:5] == 'float': lstValDef.append(0.0)
        elif tip[:4] == 'date': lstValDef.append(datetime.date(1900,1,1))
        else: lstValDef.append('')
    return lstValDef

def LargeursDefaut(lstNomsColonnes,lstChamps,lstTypes):
    # Evaluation de la largeur nécessaire des colonnes selon le type de donnee et la longueur du champ
    lstLargDef = []
    for colonne in lstNomsColonnes:
        tip = lstTypes[lstChamps.index(colonne)]
        if tip[:3] == 'int': lstLargDef.append(40)
        elif tip[:5] == 'float': lstLargDef.append(60)
        elif tip[:4] == 'date': lstLargDef.append(60)
        elif tip[:7] == 'varchar':
            lg = int(tip[8:-1])*7
            if lg > 150: lg = 150
            lstLargDef.append(lg)
        elif 'blob' in tip:
            lstLargDef.append(250)
        else: lstLargDef.append(40)
    if len(lstLargDef)>0:
        # La première colonne est masquée
        lstLargDef[0]=0
    return lstLargDef

#**********************************************************************************
#                   CONTROLES de BASE: Grilles ou composition en panel
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
        wx.BitmapButton.__init__(self, parent, wx.OK, wx.Bitmap("xpy/Images/100x30/Bouton_ok.png", wx.BITMAP_TYPE_ANY))
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
                        if not 'enable' in ligne : ligne['enable'] = True
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

                            elif genre in ['date','datetime','time']:
                                wxpg.PG_BOOL_USE_CHECKBOX = 1
                                propriete = wxpg.DateProperty(label= label, name=name, value= value)
                                propriete.SetFormat('%d/%m/%Y')
                                propriete.PG_BOOL_USE_CHECKBOX = 1

                            elif genre in ['blob','longstring']:
                                wxpg.PG_BOOL_USE_CHECKBOX = 1
                                propriete = wxpg.LongStringProperty(label= label, name=name, value= value)
                                propriete.PG_BOOL_USE_CHECKBOX = 1

                            elif genre in ['str','string','texte','txt']:
                                wxpg.PG_BOOL_USE_CHECKBOX = 1
                                propriete = wxpg.StringProperty(label= label, name=name, value= value)
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
                            "Echec sur Property de name: '%s' - value: '%s' (%s)\nLe retour d'erreur est : \n%s\n\nSur commande : %s"
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
    # Panel contenant un contrôle ersatz d'une ligne de propertyGrid
    """ et en option (code) un bouton d'action permettant de contrôler les saisies
        GetValue retourne la valeur choisie dans le ctrl avec action possible par bouton à droite"""
    def __init__(self, parent, *args, genre='string', name=None, label=None, value= None, labels=[], values=[], help=None,
                 btnLabel=None, btnHelp=None, btnAction='', ctrlAction='', enable=True, **kwds):
        wx.Panel.__init__(self,parent,*args, **kwds)
        self.value = value
        if btnLabel :
            self.avecBouton = True
        else: self.avecBouton = False

        self.MaxSize = (2000, 30)
        self.txt = wx.StaticText(self, wx.ID_ANY, label + " :")
        self.txt.MinSize = (110, 25)

        # seul le PropertyGrid gère le multichoice, pas le comboBox
        if genre == 'multichoice': genre = 'combo'
        lgenre,lname,llabel,lvalue = Normalise(genre, name, label, value)
        if not labels: labels = []
        if not values: values = []
        if len(values) > 0 and len(labels) == 0:
            labels = values
        self.genre = lgenre

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
                if lgenre in ['date','time','datetime']:
                    lvalue = xfmt.DatetimeToStr(lvalue,iso=False)
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
                "Echec sur PNL_ctrl de:\ngenre: %s\nname: %s\nvalue: %s (%s)\n\nLe retour d'erreur est : \n%s\n\nSur commande : %s"
                % (lgenre, name, value, type(value), err, commande),
                'PNL_ctrl.__init__() : Paramètre de ligne indigeste !', wx.OK | wx.ICON_STOP
            )

    def BoxSizer(self):
        topbox = wx.BoxSizer(wx.HORIZONTAL)
        topbox.Add(self.txt,0, wx.LEFT|wx.EXPAND|wx.ALIGN_TOP, 4)
        topbox.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, 4)
        if self.avecBouton:
            topbox.Add(self.btn, 0, wx.ALL|wx.EXPAND, 4)
        self.SetSizer(topbox)

    def GetValue(self):
        return self.ctrl.GetValue()

    def SetValue(self,value):
        if self.genre in ('int','float'): value = str(value)
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
#                   COMPOSITIONS DE CONTROLES
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
        for i in range(len(ltColonnes)):
            self.ctrl.SetColumnWidth(i,wx.LIST_AUTOSIZE_USEHEADER)

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
        self.champsItem = ('name', 'label', 'ctrlAction', 'btnLabel', 'btnAction', 'value', 'labels', 'values','enable')
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
                    self.ssbox.Add(panel,1,wx.ALL|wx.EXPAND,0)
                    codename = self.code + '.' + ligne['name']
                    panel.ctrl.genreCtrl = ligne['genre']
                    panel.ctrl.nameCtrl = codename
                    panel.ctrl.labelCtrl = ligne['label']
                    panel.ctrl.actionCtrl = ligne['ctrlAction']
                    panel.ctrl.valueCtrl = ligne['value']
                    panel.ctrl.valOrigine = ligne['value']
                    panel.ctrl.valuesCtrl = ligne['values']
                    panel.ctrl.labelsCtrl = ligne['labels']
                    if ligne['enable'] == False:
                        panel.ctrl.Enable(False)
                        panel.txt.Enable(False)
                    if panel.avecBouton and ligne['genre'].lower() != 'dir' :
                        panel.btn.nameBtn = codename
                        panel.btn.labelBtn = ligne['btnLabel']
                        panel.btn.actionBtn = ligne['btnAction']
                        panel.btn.Bind(wx.EVT_BUTTON,self.parent.OnBtnAction)
                    if panel.ctrl.actionCtrl:
                        if panel.ctrl.genreCtrl in ['enum','combo','multichoice']:
                            panel.ctrl.Bind(wx.EVT_COMBOBOX, self.parent.OnCtrlAction)
                            panel.ctrl.Bind(wx.EVT_CHECKBOX, self.parent.OnCtrlAction)
                        else:
                            panel.ctrl.Bind(wx.EVT_KILL_FOCUS,self.parent.OnCtrlAction)
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

    def SetOneValues(self,dicvalues=None):
        for panel in self.lstPanels:
            [code, champ] = panel.ctrl.nameCtrl.split('.')
            if champ in dicvalues:
                if panel.ctrl.genreCtrl.lower() in ['enum', 'combo']:
                    panel.SetValues(dicvalues[champ])
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

    def OnCtrlAction(self,event):
        self.parent.OnChildCtrlAction(event)

    def OnBtnAction(self,event):
        self.parent.OnChildBtnAction(event)

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

    def SetOneValues(self, ddDonnees):
        for box in self.lstBoxes:
            if box.code in ddDonnees:
                dic = ddDonnees[box.code]
                box.SetOneValues(dic)
        return

class DLG_ligne(wx.Dialog):
    # variante DLG_vide, avec relais possible d'évènements Boutons ou Controles gérés dans matrice
    def __init__(self, parent, *args, dldMatrice={}, ddDonnees={}, **kwds):
        self.gestionProperty = kwds.pop('gestionProperty',False)
        lblbox = kwds.pop('lblbox','Gestion d\'une ligne')
        self.marge = kwds.pop('marge',10)
        self.minSize = kwds.pop('minSize',(800, 500))
        self.couleur = kwds.pop('couleur',wx.WHITE)
        listArbo = os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        super().__init__(None, wx.ID_ANY, *args, title=titre, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                         **kwds)
        self.pos = kwds.pop('pos',(50, 50))
        self.parent = parent
        self.SetBackgroundColour(self.couleur)
        self.parent = parent
        self.dldMatrice = dldMatrice
        self.ddDonnees = ddDonnees
        self.args = args
        self.kwds = kwds
        # bouton bas d'écran
        self.btn = BTN_fermer(self)
        self.btn.Bind(wx.EVT_BUTTON, self.OnFermer)
        self.btnEsc = BTN_esc(self, action=self.OnBtnEsc)
        if self.gestionProperty:
            self.pnl = PNL_property(self, self, matrice=self.dldMatrice, lblbox=lblbox)
        else:
            self.pnl = TopBoxPanel(self, self, matrice=self.dldMatrice, lblbox=lblbox)
        self.pnl.MinSize = self.minSize
        self.Sizer()
        self.pnl.SetValeurs(self.ddDonnees)

    def Sizer(self):
        topbox = wx.BoxSizer(wx.VERTICAL)
        topbox.Add(self.pnl, 1, wx.EXPAND | wx.ALL, self.marge)
        btnbox = wx.BoxSizer(wx.HORIZONTAL)
        btnbox.Add(self.btnEsc, 0, wx.ALIGN_RIGHT | wx.RIGHT, 40)
        btnbox.Add(self.btn, 0, wx.ALIGN_RIGHT | wx.RIGHT, 40)
        topbox.Add(btnbox, 0, wx.ALIGN_RIGHT)
        topbox.SetSizeHints(self)
        self.SetSizer(topbox)

    def OnFermer(self, event):
        if self.parent != None:
            self.EndModal(wx.ID_OK)
        else:
            return self.Close()

    def OnBtnEsc(self, event):
        if self.parent != None:
            self.EndModal(0)
        else:
            self.Destroy()

    def OnChildBtnAction(self, event):
            if self.parent != None:
                self.parent.OnChildBtnAction(event)
            else:
                print("Bonjour BtnAction de DLG_monoligne")

    def OnChildCtrlAction(self, event):
            if self.parent != None:
                self.parent.OnChildCtrlAction(event)
            else:
                print("Bonjour CtrlAction de DLG_monoligne")

    def OnChildEnter(self, event):
            if self.parent != None:
                self.parent.OnChildAction(event)
            else:
                print("Bonjour l'Action de DLG_monoLigne")

class Gestion_ligne(object):
    # gestion de la ligne d'une table appelée dans un OLV en vue de modif, insert, copy ou supprim
    def __init__(self,parent,DBsql,table,datatable,mode='consult',ctrlolv=None,**kwds):
        self.kwds = kwds
        self.parent = parent
        self.DBsql = DBsql
        self.table = table
        self.mode = mode
        if not self.VerifSelection(ctrlolv,mode):
            self.ok = False
            return
        else : self.ok = True
        self.ctrlolv = ctrlolv
        self.selection = ctrlolv.Selection()[0]
        self.ixsel = ctrlolv.innerList.index(self.selection)

        # enrichissement de kwds transmis soit déjà dans kwds ou posés après init par self.mot=valeur
        self.gestionProperty = None
        self.lblbox = mode[:1].upper() + mode[1:] + " d'une ligne de %s"% table
        self.marge = None
        self.minSize = None
        self.couleur = None
        self.pos = None
        self.altkwds = ['gestionProperty','lblbox','marge','minSize','couleur','pos']
        self.altval = [self.gestionProperty,self.lblbox,self.marge,self.minSize,self.couleur,self.pos]

        #liste associées aux champs à gérer
        lstChamps, lstTypes, lstHelp = datatable.GetChampsTypes(table, tous=True)
        self.lstTblHelp = lstHelp
        self.lstTblChamps = lstChamps
        self.lstTblCodes = [SupprimeAccents(x) for x in lstChamps]
        self.lstTblValdef = ValeursDefaut(lstChamps,lstChamps,lstTypes)
        self.lstTblValeurs = []
        self.lstOlvCodes = ctrlolv.lstCodesColonnes
        self.lstOlvNoms = ctrlolv.lstNomsColonnes
        self.lstOlvValeur = [x for x in self.selection.donnees]

        # récup de la clé de l'enregistrement pointé dans OLV
        codescommuns = [code  for code in self.lstTblCodes if code in self.lstOlvCodes]
        Tplcle = lambda x : (self.lstTblChamps[self.lstTblCodes.index(x)],
                             self.lstOlvValeur[self.lstOlvCodes.index(x)])
        self.lstcle = [Tplcle(code) for code in codescommuns]
        def CleWhere(cletable):
            # tranforme cletable liste de tuples(champ,valeur), en clause sql where
            clewhere = ''
            for cle, val in cletable:
                if isinstance(val, (datetime.date, str)):
                    valsql = "'%s'" % str(val)
                else:
                    valsql = str(val)
                clewhere += '(%s = %s) AND ' % (cle, valsql)
            clewhere = clewhere[:-4]
            return clewhere
        self.clewhere = CleWhere(self.lstcle)

        # gestion de la suppression d'une ligne
        if mode == 'suppr':
            # Suppression
            designation = "Ligne : %s %s %s" % tuple([self.selection.donnees[x] for x in [1, 2, 3]])
            if wx.YES == wx.MessageBox("Confirmez-vous la suppresion de la selection?\n\n%s" % designation,
                                       style=wx.YES_NO):
                ret = self.DBsql.ReqDEL(self.table, self.clewhere, mess='DEL affectations.%s.Ecran' % self.table)
                if ret != 'ok': wx.MessageBox(ret, style=wx.ICON_WARNING)
                del self.ctrlolv.donnees[self.ixsel]
                if not self.ixsel > 0: self.ixsel = 0
                self.ctrlolv.MAJ(self.ixsel-1)

        # listes pour la grille de l'écran
        self.dictMatrice = {}
        self.dictDonnees = {}
        self.lstEcrCodes = []

        # préalimentation des valeurs
        if self.DBsql and mode in ('modif','copie','eclat','consult'):
            # Reprise de toutes les valeurs completes de la table
            req = """SELECT *
                    FROM %s
                    WHERE %s;"""%(table,self.clewhere)
            retour = self.DBsql.ExecuterReq(req, mess='xGestionLigne.EcranSaisie : %s'%table)
            if (not retour == "ok"):
                wx.MessageBox("Erreur : %s"%retour)
            else:
                recordset = self.DBsql.ResultatReq()
                if len(recordset) > 0:
                    self.lstTblValeurs = [x for x in recordset[0]]
                    for code in self.lstTblCodes:
                        ixtbl = self.lstTblCodes.index(code)
                        if code in self.lstOlvCodes:
                            # cas ou un traitement du parent peut avoir changé la record[ixtbl] native
                            valolv = self.lstOlvValeur[self.lstOlvCodes.index(code)]
                            if valolv != self.lstTblValeurs[ixtbl]:
                                self.lstTblValeurs[ixtbl] = valolv

        # cas de l'ajout ou de l'échec de la reprise
        if self.lstTblValeurs == []:
            self.lstTblValeurs =  [x for x in self.lstTblValdef]
            # priorité aux valeurs de la selection
            for code in self.lstTblCodes:
                if code in self.lstOlvCodes:
                    ixcol = self.lstOlvCodes.index(code)
                    ixtbl = self.lstTblCodes.index(code)
                    self.lstTblValeurs[ixtbl]= self.lstOlvValeur[ixcol]

    def VerifSelection(self,ctrlolv,mode):
        # contrôle la selection d'une ligne, puis marque le no dossier et eventuellement texte infos à afficher
        if len(ctrlolv.Selection()) == 0 and mode != 'ajout':
            wx.MessageBox("Action Impossible\n\nVous n'avez pas selectionné une ligne!", "Préalable requis")
            return False
        if len(ctrlolv.Selection()) == 0:
            ctrlolv.SelectObject(ctrlolv.innerList[0])
        return True

    def SetBlocGrille(self,lstCodes=[],dicOptions={},nmCateg='Gestion ligne'):
        # initialisation des variables de la table, affichées à l'écran
        donnees, lstNoms, lstValdef, lstHelp = [],[],[],[]
        if not lstCodes  or len(lstCodes) == 0:
            lstCodes = self.lstTblCodes
        for code in lstCodes:
            if code not in self.lstEcrCodes and code in self.lstTblCodes:
                self.lstEcrCodes.append(code)
                ixtbl = self.lstTblCodes.index(code)
                valeur = self.lstTblValeurs[ixtbl]
                if not valeur: valeur = self.lstTblValdef[ixtbl]
                if (self.mode in ('copie','eclat','ajout')) and isinstance(self.lstTblValdef[ixtbl], (int, float))\
                        and code[:2] != 'id':
                    # raz des valeurs numériques copiées, si ce ne sont pas des 'id'
                    valeur = self.lstTblValdef[ixtbl]
                donnees.append(valeur)
                lstNoms.append(self.lstTblChamps[ixtbl])
                lstValdef.append(self.lstTblValdef[ixtbl])
                lstHelp.append(self.lstTblHelp[ixtbl])
        if len(lstCodes)>0:
            (matrice,donnees) = ComposeMatrice(lstNoms, lstHelp=lstHelp,record=donnees,
                                      dicOptions=dicOptions,lstCodes=lstCodes)
            # incrementation d'un bloc dans la grille
            cdCateg = 'cat%d'%len(self.dictMatrice)
            (self.dictMatrice[(cdCateg,nmCateg)],self.dictDonnees[cdCateg]) = (matrice,donnees)

    def InitDlg(self):
        # envoi de l'écran avec transmission des propriétés heritées
        for mot,val in zip(self.altkwds,self.altval):
            if val: self.kwds[mot] = val
        self.dlg = DLG_ligne(self.parent,dldMatrice=self.dictMatrice,ddDonnees=self.dictDonnees,**self.kwds)

        fin = False
        while not fin:
            retdlg = self.dlg.ShowModal()
            if retdlg == wx.ID_OK:
                # Retour par bouton Fermer
                valeurs = self.dlg.pnl.GetValeurs()
                try:
                    fin = self.parent.Validation(valeurs)
                except Exception as err:
                    wx.MessageBox("Erreur Gestion_ligne\n\nAppel fonction 'Validation' :\n%s"%err)
                if fin:
                    self.Final(valeurs)
                del valeurs
            else: fin = True
        self.ctrlolv.SelectObject(self.ctrlolv.innerList[self.ixsel])

    def Final(self,valeurs):
        # mise à jour de l'olv d'origine
        for code in self.lstEcrCodes:
            for categorie, dicDonnees in valeurs.items():
                if code in dicDonnees and code in self.lstOlvCodes:
                    # pour chaque colonne de la selection de l'olv
                    valorigine = self.lstOlvValeur[self.lstOlvCodes.index(code)]
                    if (not valorigine):
                        valorigine = valeurs[categorie][code]
                        flag = True
                    else:
                        flag = False
                    if flag or (valorigine != valeurs[categorie][code]):
                        ix = self.lstOlvCodes.index(code)
                        self.selection.donnees[ix] = valeurs[categorie][code]
                        if isinstance(valorigine, (str, datetime.date)):
                            action = "self.selection.__setattr__('%s','%s')" % (
                                self.lstOlvCodes[ix], str(valeurs[categorie][code]))
                        elif isinstance(valorigine, (int, float)):
                            if valeurs[categorie][code] in (None, ''):
                                valeurs[categorie][code] = '0'
                            action = "self.selection.__setattr__('%s',%d)" % (
                                self.lstOlvCodes[ix], float(valeurs[categorie][code]))
                        else:
                            action = 'pass'
                            wx.MessageBox("UTIL_Affectaions.EcranSaisie\n\n%s, type non géré pour modifs: %s" % (
                            code, type(valorigine)))
                        eval(action)
        # constitution des données à mettre à jour dans la base de donnee
        lstModifs = []
        for categorie, dicdonnees in valeurs.items():
            for code, valeur in dicdonnees.items():
                if code in self.lstTblCodes:
                    if valeur in (None, ''): valeur = self.lstTblValdef[self.lstTblCodes.index(code)]
                    nom = self.lstTblChamps[self.lstTblCodes.index(code)]
                    lstModifs.append((nom, valeur))

        # complément des champs clé si non gérés dans l'écran
        for (champcle, valcle) in self.lstcle:
            if not champcle in [champ for (champ, val) in lstModifs]:
                lstModifs.append((champcle, valcle))

        # mise à jour de la table
        if len(lstModifs) > 0 and self.mode == 'modif':
            ret = self.DBsql.ReqMAJ(self.table, lstModifs, self.clewhere, mess='MAJ affectations.%s.Ecran' % self.table)
            if ret != 'ok':
                wx.MessageBox(ret)

        if len(lstModifs) > 0 and self.mode in ('copie', 'eclat'):
            lstMaj, lstIns = self.Eclater(lstModifs, self.lstTblValeurs)
            if self.mode == 'eclat':
                # la copie est comme éclater mais sans toucher à l'enreg d'origine
                ret = self.DBsql.ReqMAJ(self.table, lstMaj, self.clewhere, mess='MAJ affectations.%s.Ecran' % self.table)
                if ret != 'ok': wx.MessageBox(ret)
            insChamps = [x for x, y in lstIns]
            insDonnees = [y for x, y in lstIns]
            ret = self.DBsql.ReqInsert(self.table, insChamps, insDonnees, mess='Insert affectations.%s.Ecran' % self.table)
            if ret != 'ok': wx.MessageBox(ret)

        if len(lstModifs) > 0 and self.mode == 'ajout':
            insChamps = [x for x, y in lstModifs]
            insDonnees = [y for x, y in lstModifs]
            ret = self.DBsql.ReqInsert(self.table, insChamps, insDonnees, mess='Insert affectations.%s.Ecran' % self.table)
            if ret != 'ok': wx.MessageBox(ret)

    def Eclater(self,lstModifs,recOrigine):
        # le modèle d'origine voit ses nombres diminués du montant de l'éclat
        lstIns, lstMaj = [],[]
        for champ,valeur in lstModifs:
            ix = self.ctrlolv.lstTblChamps.index(champ)
            valorigine = recOrigine[ix]
            valdef = self.ctrlolv.lstTblValdef[ix]
            if not valorigine: valorigine = valdef
            if isinstance(valdef,(int,float)) and champ[:2].lower() != 'id':
                valeur = xfmt.Nz(valeur)
                valreste = xfmt.Nz(valorigine) - valeur
                if valreste < 0.0 : valreste = 0.0
                lstMaj.append((champ,valreste))
                lstIns.append((champ,valeur))
            else:
                lstMaj.append((champ,valorigine))
                lstIns.append((champ,valeur))
        return lstMaj,lstIns


if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    zzdictDonnees = {"bd_reseau": {'serveur': 'my server',
                                 'bdReseau':False,
                                 'utilisateur' : 'moi-meme',
                                 'config': xfmt.DateStrToWxdate('2020-02-28',iso=True),
                                 'localisation': "élevé ailleurs",
                                 'choix': 12,'multi':[12, 13],
                                'nombre': 456.45,
                                 },
                   "ident": {'domaine': 'mon domaine'}}
    zzdictMatrice = {
        ("ident", "Votre session"):
            [
                {'genre': 'String', 'name': 'domaine', 'label': 'Votre organisation', 'value': "NomDuPC",
                                 'help': 'Ce préfixe à votre nom permet de vous identifier','enable':False},
                {'genre': 'String', 'name': 'utilisateur', 'label': 'Votre identifiant', 'value': "NomSession",
                                 'help': 'Confirmez le nom de sesssion de l\'utilisateur'},
            ],
        ("choix_config", "Choisissez votre configuration"):
            [
                {'genre': 'Date', 'name': 'config', 'label': 'DateConfiguration','value':xfmt.DateStrToWxdate('27/02/2019',iso=False),
                      'help': "Le bouton de droite vous permet de créer une nouvelle configuration"},
                {'genre': 'MultiChoice', 'name': 'multi', 'label': 'Configurations','labels':['aa','bb','cc'], 'value':['1','2'],
                         'help': "Le bouton de droite vous permet de créer une nouvelle configuration",
                         'btnLabel': "...", 'btnHelp': "Cliquez pour gérer les configurations",
                        'btnAction': 'OnCtrlAction'},
            ],
        ("bd_reseau", "Base de donnée réseau"):
            [
                {'genre': 'Dir', 'name': 'localisation', 'label': 'Répertoire de localisation',
                        'value': True,
                        'help': "Il faudra connaître les identifiants d'accès à cette base"},
                {'genre': 'String', 'name': 'serveur', 'label': 'Nom du serveur', 'value': 'monServeur',
                        'help': "Il s'agit du serveur de réseau porteur de la base de données"},
                {'genre': 'Float', 'name': 'nombre', 'label': 'float', 'value': 40.12,
                 'help': "test de nombre"},
            ]
        }

# Lancement  test avec un tableau ne correspondant pas à la table affichée

    import xpy.outils.xdatatables as datatable
    import xpy.xGestion_Tableau as xgt

    def actiontest(self):
        dlg = Gestion_ligne(frame_test, None, 'utilisateurs', datatable, 'consult', frame_test.ctrlOlv)
        if dlg.ok:
            dlg.SetBlocGrille(['nom','prenom'])
            dlg.InitDlg()
        del dlg

    dicOnClick = {'Action1': lambda evt: actiontest(frame_test),
                  'Action2': 'self.parent.Validation()',
                  'BtnPrec': 'self.parent.Close()'}

    frame_test = xgt.DLG_tableau(None,dicOlv=xgt.dicOlv,lstBtns={},lstActions=xgt.lstActions,lstInfos={},
                                 dicOnClick=dicOnClick)
    app.SetTopWindow(frame_test)
    #Gestion_ligne(frame_test,None,'utilisateurs',datatable,'consult',frame_test.ctrlOlv)
    frame_test.Show()
    app.MainLoop()
