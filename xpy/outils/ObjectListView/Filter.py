# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         Filter.py
# Author:       Phillip Piper, adaptations JB
# Created:      26 August 2008
# Copyright:    (c) 2008 Phillip Piper
# SVN-ID:       $Id$
# License:      wxWindows license
#----------------------------------------------------------------------------

"""
Filters provide a structured mechanism to display only some of the model objects
given to an ObjectListView. Only those model objects which are 'chosen' by
an installed filter will be presented to the user.

Filters are simple callable objects which accept a single parameter, which
is the list of model objects to be filtered, and returns a collection of
those objects which will be presented to the user.

This module provides some standard filters.

Filters almost always impose a performance penalty on the ObjectListView.
The penalty is normally O(n) since the filter normally examines each model
object to see if it should be included. Head() and Tail() are exceptions
to this observation.
"""

import wx
import wx.propgrid as wxpg
import xpy.outils.xformat as xpof

def Predicate(predicate):
    """
    Display only those objects that match the given predicate

    Example::
        self.olv.SetFilter(Filter.Predicate(lambda x: x.IsOverdue()))
    """
    filtred = lambda modelObjects: [x for x in modelObjects if predicate(x)]
    return filtred

def Head(num):
    """
    Display at most the first N of the model objects

    Example::
        self.olv.SetFilter(Filter.Head(1000))
    """
    return lambda modelObjects: modelObjects[:num]

def Tail(num):
    """
    Display at most the last N of the model objects

    Example::
        self.olv.SetFilter(Filter.Tail(1000))
    """
    return lambda modelObjects: modelObjects[-num:]

#**************************  Gestion des filtres à ajouter************************************************************

class CTRL_property(wxpg.PropertyGrid):
    # grille property affiche les paramètres gérés par PNL_property
    def __init__(self, parent, matrice={}, valeursDefaut={}, enable=True, style=wxpg.PG_SPLITTER_AUTO_CENTER):
        wxpg.PropertyGrid.__init__(self, parent, wx.ID_ANY, style=style)
        self.parent = parent
        self.matrice=matrice
        self.MinSize = (300,50)
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
        self.InitMatrice()

    def OnPropGridChange(self, event):
        event.Skip()

    def InitMatrice(self):
        # Compose la grille de saisie des paramètres selon le dictionnaire matrice
        for code,lignes  in self.matrice.items():
            chapitre = self.matrice[code]['nomchapitre']
            if isinstance(chapitre, str):
                self.Append(wxpg.PropertyCategory(chapitre))
                for ligne in self.matrice[code]['lignes']:
                    if 'name' in ligne and 'genre' in ligne:
                        if not 'label' in ligne : ligne['name'] = None
                        if not 'value' in ligne : ligne['value'] = None
                        codeName = code + '.' + ligne['name']
                        genre, name, label, value = (ligne['genre'],codeName,ligne['label'],ligne['value'])
                        genre = genre.lower()
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
                                choix = wxpg.PGChoices(ligne['labels'], values=values)
                                propriete = wxpg.EnumProperty(label=label,name=name,choices=choix,value=0)

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

                            elif genre == 'dir':
                                propriete = wxpg.DirProperty(name)

                            else:
                                commande = "wxpg." + genre.upper()[:1] + genre.lower()[1:] + "Property(label= label, name=name, value=value)"
                                propriete = eval(commande)
                            if 'help' in ligne:
                                propriete.SetHelpString(ligne['help'])
                            self.Append(propriete)
                            self.ptactive = propriete
                        except Exception as err:
                            wx.MessageBox(
                            "Echec sur Property de name - value: %s - %s (%s)\nLe retour d'erreur est : \n%s\n\nSur commande : %s"
                            %(name,value,type(value),err,commande),
                            'CTRL_property.InitMatrice() : Paramètre ligne indigeste !', wx.OK | wx.ICON_STOP
                            )

    def GetValeurs(self):
        values = self.GetPropertyValues()
        ddDonnees = {}
        for nom, valeur in values.items():
            [code, champ] = nom.split('.')
            if not code in ddDonnees : ddDonnees[code] = {}
            # récupération de la valeur choisie pour une combo
            for dicligne in self.matrice[code]['lignes']:
                if champ in dicligne['name']:
                    if dicligne['genre'].lower() in ['enum','combo']:
                        valeur = dicligne['values'][valeur]
            ddDonnees[code][champ] = valeur
        return ddDonnees

class DLG_saisiefiltre(wx.Dialog):
    def __init__(self,parent, *args, **kwds):
        self.parent = parent
        self.listview = kwds.pop('listview',None)
        self.etape=0
        titre = kwds.pop('titre',"Pas d'argument kwd 'listview' pas de choix de colonnes")
        if self.listview:
            self.lstLabelsColonnes = self.listview.lstLabelsColonnes
            self.lstSetterValues = self.listview.lstSetterValues
            titre = kwds.pop('titre',"Saisie d'un filtre élaboré")
        wx.Dialog.__init__(self, parent, *args, title=titre, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                           **kwds)
        self.marge = 10
        self.btnOK = wx.Button(self, id=wx.ID_ANY, label="OK")
        self.btnAbort = wx.Button(self, id=wx.ID_ANY, label="Abandon")
        self.Bind(wx.EVT_BUTTON, self.OnBtnOK, self.btnOK)
        self.Bind(wx.EVT_BUTTON, self.OnBtnAbort, self.btnAbort)
        if self.listview:
            self.Etape1()

    def Sizer(self,ctrl):
        self.ctrl=ctrl
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(ctrl, 1, wx.EXPAND | wx.ALL, self.marge)
        gridsizer = wx.FlexGridSizer(1, 2, 0, 0)
        gridsizer.Add(self.btnOK)
        gridsizer.Add(self.btnAbort)
        sizer.Add(gridsizer, 0, wx.ALL | wx.ALIGN_RIGHT, self.marge)
        sizer.SetSizeHints(self)
        self.SetSizer(sizer)
        self.Layout()
        self.ctrl.SelectProperty(self.ctrl.ptactive,True)

    def OnBtnOK(self,evt):
        values = self.ctrl.GetValeurs()
        self.ctrl.Destroy()
        if self.etape == 1:
            self.colonne = values['colonne']['colonne']
            self.Etape2()
            return
        if self.etape == 2:
            self.action = values['action']['action']
            self.Etape3()
            return
        if self.etape == 3:
            self.valeur = values['valeur']['valeur']
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox(str(values))

    def OnBtnAbort(self,evt):
        self.EndModal(wx.ID_CANCEL)

    def Etape1(self):
        self.etape = 1
        dictMatrice = {
            "colonne":
                {'nomchapitre': "Choix de la colonne à filtrer",
                 'lignes': [{'genre': 'Enum', 'name': 'colonne', 'label': 'Colonne à filtrer :',
                             'value': '', 'help': 'Choisir par le triangle noir'}], }}
        dictMatrice['colonne']['lignes'][0]['values'] = self.lstLabelsColonnes
        ctrlproperty = CTRL_property(self, matrice=dictMatrice)
        self.Sizer(ctrlproperty)

    def Etape2(self):
        self.etape = 2
        dictMatrice = {
            "action":
                {'nomchapitre': "Que faire sur la colonne %s"%self.colonne,
                 'lignes': [{'genre': 'Enum', 'name': 'action', 'label': 'Type de filtre :',
                             'value': '', 'help': 'Choisir par le type de filtre'}], }}
        idx = self.lstLabelsColonnes.index(self.colonne)
        self.tip = type(self.lstSetterValues[idx])
        self.choixactions = xpof.CHOIX_FILTRES[self.tip]
        if not self.tip: self.tip = str
        if not self.tip in xpof.CHOIX_FILTRES:
            wx.MessageBox("Le genre '%s' de la colonne '%' n'est pas connu dans CHOIX_FILTRES")
            self.EndModal(wx.ID_CANCEL)
        values = []
        for (code,label) in self.choixactions:
            values.append(label)
        dictMatrice['action']['lignes'][0]['values'] = values
        ctrlproperty = CTRL_property(self, matrice=dictMatrice)
        self.Sizer(ctrlproperty)

    def Etape3(self):
        self.etape = 3
        dictMatrice = {
            "valeur":
                {'nomchapitre': "Choix de la valeur",
                 'lignes': [{'genre': 'String', 'name': 'valeur', 'label': 'Valeur :',
                             'value': '', 'help': 'Choisir la valeur'}], }}
        ctrlproperty = CTRL_property(self, matrice=dictMatrice)
        self.Sizer(ctrlproperty)

    def GetDonnees(self):
        for (code,label) in xpof.CHOIX_FILTRES[self.tip]:
            if label == self.action:
                codechoix = code
                break

        filtre =  {'typeDonnee': self.tip,
                   'criteres': self.valeur,
                   'choix': codechoix,
                   'code': self.colonne,
                   'titre': self.colonne}
        return filtre

#**************************************************************************************************

class TextSearch(object):
    """
    Return only model objects that match a given string. If columns is not empty,
    only those columns will be considered when searching for the string. Otherwise,
    all columns will be searched.

    Example::
        self.olv.SetFilter(Filter.TextSearch(self.olv, text="findthis"))
        self.olv.RepopulateList()
    """

    def __init__(self, objectListView, columns=(), text=""):
        """
        Create a filter that includes on modelObject that have 'self.text' somewhere in the given columns.
        """
        self.objectListView = objectListView
        self.columns = columns
        self.text = text

    def __call__(self, modelObjects):
        """
        Return the model objects that contain our text in one of the columns to consider
        """
        if not self.text:
            return modelObjects
        
        # In non-report views, we can only search the primary column
        if self.objectListView.InReportView():
            cols = self.columns or self.objectListView.columns
        else:
            cols = [self.objectListView.columns[0]]

        textToFind = self.EnleveAccents(self.text).lower()

        def _containsText(modelObject):
            for col in cols:
                valeur = col.GetStringValue(modelObject)
                if valeur == None : valeur = ""
                textInListe = self.EnleveAccents(valeur).lower()
                # Recherche de la chaine
                if textToFind in textInListe :
                    return True
            return False

        return [x for x in modelObjects if _containsText(x)]
    
    def EnleveAccents(self, texte):
        try :
            return texte.decode("iso-8859-15")
        except : return texte
        


    def SetText(self, text):
        """
        Set the text that this filter will match. Set this to None or "" to disable the filter.
        """
        self.text = text

class Chain(object):
    """
    Return only model objects that match all of the given filters.

    Example::
        # Show at most 100 people whose salary is over 50,000
        salaryFilter = Filter.Predicate(lambda person: person.GetSalary() > 50000)
        self.olv.SetFilter(Filter.Chain(salaryFilter, Filter.Tail(100)))
        self.olv.RepopulateList()
    """

    def __init__(self, *filters):
        #Create a filter that performs all the given filters. The order of the filters is important.
        self.filters = filters

    def __call__(self, modelObjects):
        #Return the model objects that match all of our filters
        for filter in self.filters:
            modelObjects = filter(modelObjects)
        return modelObjects

if __name__ == '__main__':
    app = wx.App(0)

    dictMatrice = {
        "filtre":
            {
            'nomchapitre':"Filtre initial",
            'lignes':
                [
                {'genre': 'Date', 'name': 'contient', 'label': 'Le nom contient', 'value': wx.DateTime.Today(),'help': 'Saisir une partie de mot'},
                {'genre': 'Enum', 'name': 'type', 'label': 'Type de condition', 'values':['égal', 'différent', 'supérieur ou égal', 'inferieur ou égal'], 'help': 'Saisir une action'},
                ],
            }
        }
# Lancement des tests
    frame_3 = DLG_saisiefiltre(None,)
    ctrlproperty = CTRL_property(frame_3,matrice=dictMatrice)
    frame_3.Sizer(ctrlproperty)
    app.SetTopWindow(frame_3)
    frame_3.Show()
    app.MainLoop()
