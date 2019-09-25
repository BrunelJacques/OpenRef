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
    return lambda modelObjects: [x for x in modelObjects if predicate(x)]

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
        self.MinSize = (300,100)
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

    def OnPropGridChange(self, event):
        event.Skip()
        self.parent.OnBtnOK(False)

    def InitMatrice(self, matrice):
        # Compose la grille de saisie des paramètres selon le dictionnaire matrice
        self.matrice=matrice
        self.dicProperties = {}
        chapitre = self.matrice['nomchapitre']
        if isinstance(chapitre, str):
            self.Append(wxpg.PropertyCategory(chapitre))
        for ligne in self.matrice['lignes']:
            if 'name' in ligne and 'genre' in ligne:
                if not 'label' in ligne : ligne['name'] = None
                if not 'value' in ligne : ligne['value'] = None
                genre, name, label, value = (ligne['genre'],ligne['name'],ligne['label'],ligne['value'])
                genre = genre.lower()
                if not 'labels' in ligne: ligne['labels'] = []
                """
                if 'values' in ligne and ligne['values']:
                    if ligne['labels']:
                        if len(ligne['values']) > 0 and len(ligne['labels']) == 0:
                            ligne['labels'] = ligne['values']
                    else: ligne['labels'] = ligne['values']
                """
                commande = ''
                try:
                    commande = genre
                    if genre in ['enum','combo']:
                        values = list(range(0,len(ligne['labels'])))
                        if not isinstance(value,int): value = 0
                        choix = wxpg.PGChoices(ligne['labels'], values=values)
                        propriete = wxpg.EnumProperty(label=label,name=name,choices=choix, value = value)

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

                    else:
                        commande = "wxpg."  + genre.upper()[:1] + genre.lower()[1:] \
                                            + "Property(label= label, name=name, value=value)"
                        propriete = eval(commande)
                    if 'help' in ligne:
                        propriete.SetHelpString(ligne['help'])
                    self.Append(propriete)
                    self.dicProperties[propriete] = name
                    self.dicProperties[name] = propriete
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
            label = self.dicProperties[nom].GetValueString()
            ddDonnees[nom] = label
        return ddDonnees

class DLG_saisiefiltre(wx.Dialog):
    def __init__(self,parent, *args, **kwds):
        self.parent = parent
        self.listview = kwds.pop('listview',None)
        self.etape=0
        self.idxdefault = 1
        titre = kwds.pop('titre',"Pas d'argument kwd 'listview' pas de choix de colonnes")
        if self.listview:
            self.lstNomsColonnes = self.listview.lstNomsColonnes
            self.lstCodesColonnes = self.listview.lstCodesColonnes
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
            self.dictMatrice = {'nomchapitre': "Choix du filtre",
                                'lignes': [{'genre': 'Enum', 'name': 'colonne', 'label': 'Colonne à filtrer :',
                                            'value': self.idxdefault, 'help': 'Choisir par le triangle noir',
                                            'labels': self.lstNomsColonnes}], }

            self.tip = type(self.lstSetterValues[self.idxdefault])
            self.choixactions = xpof.CHOIX_FILTRES[self.tip]
            values = []
            for (code, label) in self.choixactions:
                values.append(label)
            self.dictMatrice['lignes'].append({'genre': 'Enum', 'name': 'action', 'label': 'Type de filtre :',
                                               'labels': values})

            self.dictMatrice['lignes'].append({'genre': 'String', 'name': 'valeur', 'label': 'Valeur :',
                                                      'value': '', 'help': 'Choisir la valeur'})

            self.ctrl = CTRL_property(self, matrice=self.dictMatrice)
            self.Sizer()
            self.ctrl.SelectProperty('colonne',True)

    def Sizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.EXPAND | wx.ALL, self.marge)
        gridsizer = wx.FlexGridSizer(1, 2, 0, 0)
        gridsizer.Add(self.btnOK)
        gridsizer.Add(self.btnAbort)
        sizer.Add(gridsizer, 0, wx.ALL | wx.ALIGN_RIGHT, self.marge)
        sizer.SetSizeHints(self)
        self.SetSizer(sizer)
        self.Layout()

    def OnBtnOK(self,evt):
        values = self.ctrl.GetValeurs()
        self.colonne = values['colonne']
        self.codeColonne = self.lstCodesColonnes[self.lstNomsColonnes.index(self.colonne)]
        self.action = values['action']
        self.valeur = values['valeur']
        self.etape = ['colonne','action','valeur'].index(self.ctrl.dicProperties[self.ctrl.GetSelection()])+1

        if self.etape == 1:
            self.Etape2()
        elif self.etape == 2:
            pass
        elif self.etape == 3:
            if self.valeur and evt:
                self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox('Quelle étape ?', str(values))

    def OnBtnAbort(self,evt):
        self.EndModal(wx.ID_CANCEL)

    def Etape2(self):
        idx = self.lstNomsColonnes.index(self.colonne)
        self.tip = type(self.lstSetterValues[idx])
        self.choixactions = xpof.CHOIX_FILTRES[self.tip]
        if not self.tip: self.tip = str
        if not self.tip in xpof.CHOIX_FILTRES:
            wx.MessageBox("Le genre '%s' de la colonne '%' n'est pas connu dans CHOIX_FILTRES")
            self.EndModal(wx.ID_CANCEL)
        #recomposition des choix d'action
        labels = []
        for (code,label) in self.choixactions:
            labels.append(label)
        values = list(range(0, len(labels)))
        choix = wxpg.PGChoices(labels, values=values)
        self.ctrl.dicProperties['action'].SetChoices(choix)
        self.Layout()


    def GetDonnees(self):
        codechoix = 'None'
        for (code,label) in xpof.CHOIX_FILTRES[self.tip]:
            if label == self.action:
                codechoix = code
                break

        filtre =  {'typeDonnee': self.tip,
                   'criteres': self.valeur,
                   'choix': codechoix,
                   'code': self. codeColonne,
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
