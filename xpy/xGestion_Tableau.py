#!/usr/bin/python3
# -*- coding: utf-8 -*-

#  Jacques Brunel x Sébastien Gouast
#  MATTHANIA - Projet XPY - xTableau.py (implémentation d'une gestion de tableau paramétrable)
#  2019/04/18
# note l'appel des fonctions 2.7 passent par le chargement de la bibliothèque future (vue comme past)
# ce module reprend les fonctions de xUTILS_Tableau sans y faire appel

import wx
import os
import xpy.outils.xformat
from xpy.outils.ObjectListView import FastObjectListView, BarreRecherche, ColumnDefn, Filter, Footer, CTRL_Outils, OLVEvent
from xpy.outils.xconst import *

# ------------------------------------------------------------------------------------------------------------------

class ListView(FastObjectListView):
    """
    Lors de l'instanciation de cette classe vous pouvez y passer plusieurs parametres :

    listeColonnes : censé être une liste d'objets ColumndeFn
    listeDonnees : liste de listes ayant la même longueur que le nombre de colonnes.

    msgIfEmpty : une chaine de caractères à envoyer si le tableau est vide

    colonneTri : Permet d'indiquer le numéro de la colonne selon laquelle on veut trier
    sensTri : True ou False indique le sens de tri

    exportExcel : True par défaut, False permet d'enlever l'option 'Exporter au format Excel'
    exportTexte : idem
    apercuAvantImpression : idem
    imprimer : idem
    toutCocher : idem
    toutDecocher : idem
    menuPersonnel : On peut avoir déjà créé un "pré" menu contextuel auquel viendra s'ajouter le tronc commun

    titreImpression : Le titre qu'on veut donner à la page en cas d'impression par exemple "Titre")
    orientationImpression : L'orientation de l'impression, True pour portrait et False pour paysage

    Pour cette surcouche de OLV j'ai décidé de ne pas laisser la fonction OnItemActivated car ça peut changer selon le tableau
    donc ce sera le role de la classe parent (qui appelle ListView) de définir une fonction OnItemActivated qui sera utilisée
    lors du double clic sur une ligne

    Dictionnaire optionnel ou on indique si on veut faire le bilan (exemple somme des valeurs)
    """

    def __init__(self, *args, **kwds):
        self.ctrl_footer = None
        self.parent = args[0].parent
        self.pnlfooter = kwds.pop("pnlfooter", None)
        # Récupération des paramètres perso
        #self.classeAppelante = kwds.pop("classeAppelante", None)
        self.checkColonne = kwds.pop("checkColonne",True)
        self.listeColonnes = kwds.pop("listeColonnes", [])
        self.msgIfEmpty = kwds.pop("msgIfEmpty", "Tableau vide")
        self.colonneTri = kwds.pop("colonneTri", None)
        self.sensTri = kwds.pop("sensTri", True)
        self.menuPersonnel = kwds.pop("menuPersonnel", None)
        self.listeDonnees = kwds.pop("listeDonnees", None)
        self.lstNomsColonnes = self.formerNomColonnes()
        self.lstLabelsColonnes = self.formerLabelsColonnes()
        self.lstSetterValues = self.formerSetterValues()
        self.dictColFooter = kwds.pop("dictColFooter", {})
        self.formerTracks()

        # Choix des options du 'tronc commun' du menu contextuel
        self.exportExcel = kwds.pop("exportExcel", True)
        self.exportTexte = kwds.pop("exportTexte", True)
        self.apercuAvantImpression = kwds.pop("apercuAvantImpression", True)
        self.imprimer = kwds.pop("imprimer", True)
        self.toutCocher = kwds.pop("toutCocher", True)
        self.toutDecocher = kwds.pop("toutDecocher", True)
        self.inverserSelection = kwds.pop("inverserSelection", True)

        # Choix du mode d'impression
        self.titreImpression = kwds.pop("titreImpression", "Tableau récapitulatif")
        self.orientationImpression = kwds.pop("orientationImpression", True)
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []

        # Initialisation du listCtrl
        #test
        #self.test = kwds.pop("dictColFooter", True)
        FastObjectListView.__init__(self, *args,**kwds)
        # Binds perso
        #self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        #self.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnItemChecked)
        self.Bind(OLVEvent.EVT_ITEM_CHECKED, self.OnItemChecked)
        #self.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnItemChecked)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def SetFooter(self, ctrl=None, dictColFooter={}):
        self.ctrl_footer = ctrl
        self.ctrl_footer.listview = self
        self.ctrl_footer.dictColFooter = dictColFooter

    def MAJ_footer(self):
        if self.ctrl_footer != None:
            self.ctrl_footer.MAJ()
            dc = self.ctrl_footer.dc
            dc.Clear()
            self.ctrl_footer.Paint(dc)

    def formerTracks(self):
        self.tracks = list()

        if self.listeDonnees is None:
            return

        for listeDonnee in self.listeDonnees:
            self.tracks.append(TrackGeneral(donnees=listeDonnee,nomColonnes=self.lstNomsColonnes,
                                            setterValues=self.lstSetterValues))
        return

    def formerNomColonnes(self):
        nomColonnes = list()
        for colonne in self.listeColonnes:
            nom = colonne.valueGetter
            #nom = colonne.title
            nomColonnes.append(nom)
        return nomColonnes

    def formerLabelsColonnes(self):
        nomColonnes = list()
        for colonne in self.listeColonnes:
            nom = colonne.title
            nomColonnes.append(nom)
        return nomColonnes

    def formerSetterValues(self):
        setterValues = list()
        for colonne in self.listeColonnes:
            tip = None
            if colonne.valueSetter:
                tip = colonne.valueSetter
            if not tip:
                tip = ''
                fmt = colonne.stringConverter
                if fmt:
                    fmt = colonne.stringConverter.__name__
                    if fmt[3:] in ('Montant','Solde','Decimal','Entier'):
                        tip = 0.0
                    elif fmt[3:] == 'Date':
                        tip = wx.DateTime.FromDMY(1,0,1900)
            setterValues.append(tip)
        return setterValues

    def InitModel(self):
        self.donnees = self.GetTracks()

    def InitObjectListView(self):
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        # On définit les colonnes
        self.SetColumns(self.listeColonnes)
        if self.checkColonne:
            self.CreateCheckStateColumn(0)
        # On définit le message en cas de tableau vide
        self.SetEmptyListMsg(self.msgIfEmpty)
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT))
        # Si la colonne à trier n'est pas précisée on trie selon la première par défaut
        if self.colonneTri == None:
            self.SortBy(1, self.sensTri)
        else:
            self.SortBy(self.colonneTri, self.sensTri)
        self.SetObjects(self.donnees)

    def MAJ(self, ID=None):
        if ID != None:
            self.selectionID = ID
            self.selectionTrack = None
        else:
            self.selectionID = None
            self.selectionTrack = None
        self.InitModel()
        self.InitObjectListView()
        # Sélection d'un item
        if self.selectionTrack != None:
            self.SelectObject(self.selectionTrack, deselectOthers=True, ensureVisible=True)
        self.selectionID = None
        self.selectionTrack = None
        if ID == None:
            self.DefileDernier()

    def Selection(self):
        return self.GetSelectedObjects()

    def GetTracks(self):
        """ Récupération des données """
        return self.tracks

    def OnItemChecked(self, event):
        if self.pnlfooter:
            self.pnlfooter.SetFooter(reinit=True)

    def OnContextMenu(self, event):
        """
        Ouverture du menu contextuel

        L'idée serait de créer dans ce menu tout le 'tronc commun' c'est à dire Aperçu avant impression, Imprimer,
        Exporter au format texte , Exporter au format Excel, et pourquoi pas ajouter une option copier (la ligne ou tout le tableau)

        Ensuite on pourrait passer en paramètre une partie du menu qui sera simplement ajoutée au début.

        Par exemple les options 'tout cocher' et 'tout décocher' pourraient être activées de base et paramétrables lors de l'initialisation

        """
        if len(self.Selection()):  # equivalent a !=0
            noSelection = False
        else:
            noSelection = True

        # Création du menu contextuel ou alors récupération du menu donné en paramètre
        if self.menuPersonnel:
            menuPop = self.menuPersonnel
            # On ajoute un séparateur ici ou dans la classe parent ?
            menuPop.AppendSeparator()
        else:
            menuPop = wx.Menu()

        # Item Tout cocher
        if self.toutCocher:
            item = wx.MenuItem(menuPop, 70, TOUT_COCHER_TXT)
            bmp = wx.Bitmap(COCHER_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.CocheTout, id=70)

        # Item Tout décocher
        if self.toutDecocher:
            item = wx.MenuItem(menuPop, 80, TOUT_DECOCHER_TXT)
            bmp = wx.Bitmap(DECOCHER_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.CocheRien, id=80)

        if self.inverserSelection and self.GetSelectedObject() is not None:
            item = wx.MenuItem(menuPop, 90, INVERSER_SELECTION_TXT)
            bmp = wx.Bitmap(DECOCHER_16X16_IMG, wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.InverserCocheSelection, id=90)

        # On met le separateur seulement si un des deux menus est present
        if self.toutDecocher or self.toutCocher:
            menuPop.AppendSeparator()

        # Item filtres
        item = wx.MenuItem(menuPop, 81, UN_FILTRE)
        bmp = wx.Bitmap(FILTRE_16X16_IMG, wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.UnFiltre, id=81)

        item = wx.MenuItem(menuPop, 82, AJOUT_FILTRE)
        bmp = wx.Bitmap(FILTRE_16X16_IMG, wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.AjoutFiltre, id=82)

        item = wx.MenuItem(menuPop, 83, SUPPRIMER_FILTRES)
        bmp = wx.Bitmap(FILTREOUT_16X16_IMG, wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.SupprimerFiltres, id=83)

        # On met le separateur
        menuPop.AppendSeparator()

        # Item Apercu avant impression
        if self.apercuAvantImpression:
            item = wx.MenuItem(menuPop, 40, APERCU_IMP_TXT)
            item.SetBitmap(wx.Bitmap(APERCU_16X16_IMG, wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.Apercu, id=40)

        # Item Imprimer
        if self.imprimer:
            item = wx.MenuItem(menuPop, 50, IMPRIMER_TXT)
            item.SetBitmap(wx.Bitmap(IMPRIMANTE_16X16_IMG, wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.Imprimer, id=50)

        # On vérifie la présence d'un des menus précédents pour mettre un séparateur
        if self.imprimer or self.apercuAvantImpression:
            menuPop.AppendSeparator()

        # Item Export Texte
        if self.exportTexte:
            item = wx.MenuItem(menuPop, 600, EXPORT_TEXTE_TXT)
            item.SetBitmap(wx.Bitmap(TEXTE2_16X16_IMG, wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)

        # Item Export Excel
        if self.exportExcel:
            item = wx.MenuItem(menuPop, 700, EXPORT_EXCEL_TXT)
            item.SetBitmap(wx.Bitmap(EXCEL_16X16_IMG, wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        # On vérifie que menuPop n'est pas vide
        if self.MenuNonVide():
            self.PopupMenu(menuPop)
        menuPop.Destroy()

    def MenuNonVide(self):  # Permet de vérifier si le menu créé est vide
        return self.exportExcel or self.exportTexte or self.apercuAvantImpression or self.toutCocher or self.toutDecocher or self.imprimer or self.menuPersonnel

    def GetOrientationImpression(self):
        if self.orientationImpression:
            return wx.PORTRAIT
        return wx.LANDSCAPE

    def Apercu(self, event):
        import xpy.outils.xprinter
        # Je viens de voir dans la fonction concernée, le format n'est pas utilisé et il vaut "A" par défaut donc rien ne change
        prt = xpy.outils.xprinter.ObjectListViewPrinter(self, titre=self.titreImpression,
                                                        orientation=self.GetOrientationImpression())
        prt.Preview()

    def Imprimer(self, event):
        import xpy.outils.xprinter
        prt = xpy.outils.xprinter.ObjectListViewPrinter(self, titre=self.titreImpression,
                                                        orientation=self.GetOrientationImpression())
        prt.Print()

    def ExportTexte(self, event):
        import xpy.outils.xexport
        xpy.outils.xexport.ExportTexte(self, titre=self.titreImpression, autoriseSelections=False)

    def ExportExcel(self, event):
        import xpy.outils.xexport
        xpy.outils.xexport.ExportExcel(self, titre=self.titreImpression, autoriseSelections=False)

    def CocheTout(self, event=None):
        if self.GetFilter() is not None:
            listeObjets = self.GetFilteredObjects()
        else:
            listeObjets = self.GetObjects()
        for track in listeObjets:
            self.Check(track)
            self.RefreshObject(track)
        return

    def CocheRien(self, event=None):
        if self.GetFilter() is not None:
            listeObjets = self.GetFilteredObjects()
        else:
            listeObjets = self.GetObjects()
        for track in listeObjets:
            self.Uncheck(track)
            self.RefreshObject(track)
        return

    def InverserCocheSelection(self, event=None):
        if self.GetFilter() is not None:
            listeObjets = self.GetFilteredObjects()
        else:
            listeObjets = self.GetObjects()

        if self.GetSelectedObject() is not None:
            for track in listeObjets:
                if self.IsChecked(track):
                    self.Uncheck(track)
                else:
                    self.Check(track)
                self.RefreshObject(track)
                if track == self.GetSelectedObject():
                    return

    def GetTracksCoches(self):
        return self.GetCheckedObjects()

    def UnFiltre(self, event=None):
        self.parent.ctrloutils.UnFiltre()

    def AjoutFiltre(self, event=None):
        self.parent.ctrloutils.AjoutFiltre()

    def SupprimerFiltres(self, event=None):
        self.parent.ctrloutils.SupprimerFiltres()

class PanelListView(wx.Panel):
    #def __init__(self, parent, listview=None, kwargs={}, dictColFooter={}, style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL):
    def __init__(self, parent, **kwargs):
        id = -1
        self.parent = parent
        style = wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, parent, id=id, style=style)
        self.dictColFooter = kwargs.pop("dictColFooter", {})
        if not "id" in kwargs: kwargs["id"] = wx.ID_ANY
        if not "style" in kwargs: kwargs["style"] = wx.LC_REPORT|wx.NO_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES
        kwargs["pnlfooter"]=self
        listview = ListView(self,**kwargs)
        #kwargs["parent"] = self

        self.ctrl_listview = listview
        self.ctrl_listview.SetMinSize((10, 10))
        self.ctrl_footer = None
        self.SetFooter(reinit=False)

        # Layout
    def Compose(self):
        sizerbase = wx.BoxSizer(wx.VERTICAL)
        sizerbase.Add(self.ctrl_listview, 1, wx.ALL | wx.EXPAND, 0)
        sizerbase.Add(self.ctrl_footer, 0, wx.ALL | wx.EXPAND, 0)
        self.SetSizer(sizerbase)
        self.Layout()

    def SetFooter(self,reinit=False):
        if reinit:
            del self.ctrl_footer
        self.ctrl_footer = Footer.Footer(self)
        self.ctrl_listview.SetFooter(ctrl=self.ctrl_footer, dictColFooter=self.dictColFooter)
        self.Compose()
        #self.MAJ()

    def MAJ(self):
        self.ctrl_listview.MAJ()
        if self.ctrl_footer:
            self.ctrl_footer.MAJ()

    def GetListview(self):
        return self.ctrl_listview

class TrackGeneral(object):
    #    Cette classe va transformer les listes en objets
    def __init__(self, donnees, nomColonnes, setterValues):
        for (donnee, nomColonne, setterValue) in zip(donnees, nomColonnes, setterValues):
            if setterValue:
                if (donnee is None):
                    donnee = setterValue
                else:
                    if not isinstance(donnee,type(setterValue)):
                        try:
                            if type(setterValue) in (int,float):
                                donnee = float(donnee)
                            elif type(setterValue) == str:
                                donnee = str(donnee)
                        except : pass
            self.__setattr__(nomColonne, donnee)

# ------------------------------------------------------------------------------------------------------------------

class PNL_tableau(wx.Panel):
    def __init__(self, parent, dicOlv,*args, **kwds):
        wx.Panel.__init__(self, parent, *args,  **kwds)
        #ci dessous l'ensemble des paramètres possibles pour OLV
        lstParamsOlv = ['id',
                        'style',
                        'listeColonnes',
                        'listeDonnees',
                        'msgIfEmpty',
                        'sensTri',
                        'exportExcel',
                        'exportTexte',
                        'apercuAvantImpression',
                        'imprimer',
                        'toutCocher',
                        'toutDecocher',
                        'inverserSelection',
                        'titreImpression',
                        'orientationImpression',
                        'dictColFooter']
        avecFooter = "dictColFooter" in dicOlv
        if not avecFooter : lstParamsOlv.remove('dictColFooter')
        if 'recherche' in dicOlv: barreRecherche = dicOlv['recherche']
        else : barreRecherche = True
        self.parent = parent
        #récup des seules clés possibles pour dicOLV
        dicOlvOut = {}
        for key,valeur in dicOlv.items():
            if key in lstParamsOlv:
                 dicOlvOut[key] = valeur

        # choix footer ou pas
        pnlOlv = PanelListView(self,**dicOlvOut)
        if avecFooter:
            self.ctrlOlv = pnlOlv.ctrl_listview
            self.olv = pnlOlv
        else:
            self.ctrlOlv = ListView(self,**dicOlvOut)
            self.olv = self.ctrlOlv
        if barreRecherche:
            self.ctrloutils = CTRL_Outils(self, listview=self.ctrlOlv, afficherCocher=False)
        self.ctrlOlv.MAJ()
        #if self.ctrlOlv.ctrl_footer:
        #    self.ctrlOlv.ctrl_footer.MAJ()

        self.BoutonOK = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap("xpy/Images/100x30/Bouton_ok.png", wx.BITMAP_TYPE_ANY))
        self.BoutonOK.SetToolTip(("Cliquez ici pour enregistrer et fermer la fenêtre"))
        self.BoutonOK.Bind(wx.EVT_BUTTON, self.OnBoutonOK)

        sizerbase = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        #sizerbase = wx.BoxSizer(wx.VERTICAL)
        sizerbase.Add(self.olv, 10, wx.EXPAND, 40)
        if barreRecherche:
            sizerbase.Add(self.ctrloutils, 10, wx.EXPAND, 40)
        sizerbase.Add(self.BoutonOK, 10, wx.ALIGN_RIGHT, 40)
        sizerbase.AddGrowableCol(0,1)
        sizerbase.AddGrowableRow(0,1)

        self.SetSizerAndFit(sizerbase)

    def OnBoutonOK(self,event):
        self.parent.Close()

class DLG_tableau(wx.Dialog):
    def __init__(self,parent,dicOlv={}, **kwds):
        self.parent = parent
        largeur = dicOlv.pop("largeur", 900)
        hauteur = dicOlv.pop("hauteur", 700)
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self,parent, title=titre, size=(largeur,hauteur),style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.SetBackgroundColour(wx.WHITE)
        self.marge = 10
        self.pnl = PNL_tableau(self, dicOlv,  **kwds )
        self.CenterOnScreen()
        self.Layout()
    def Close(self):
        self.EndModal(wx.OK)

# -- pour tests -----------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    liste_Colonnes = [
        ColumnDefn("cle", 'left', 70, "cle",valueSetter=1),
        ColumnDefn("mot", 'left', 200, "mot",valueSetter=''),
        ColumnDefn("nombre", 'right', 80, "nombre",valueSetter=0.0, stringConverter=xpy.outils.xformat.FmtDecimal),
        ColumnDefn("prix", 'right', 80, "prix",valueSetter=0.0, stringConverter=xpy.outils.xformat.FmtMontant),
        ColumnDefn("date", 'center', 80, "date",valueSetter=wx.DateTime.FromDMY(1,0,1900), stringConverter=xpy.outils.xformat.FmtDate)
    ]
    liste_Donnees = [[18, "Bonjour", -1230.05939,-1230.05939,None],
                     [19, "Bonsoir", 57.5, 208.99,wx.DateTime.FromDMY(15,11,2018)],
                     [1, "Jonbour", 0 , 209,wx.DateTime.FromDMY(6,11,2018)],
                     [29, "Salut", 57.082, 209,wx.DateTime.FromDMY(28,1,2019)],
                     [None, "Salutation", 57.08, 0,wx.DateTime.FromDMY(1,7,1997)],
                     [2, "Python", 1557.08, 29,wx.DateTime.FromDMY(7,1,1997)],
                     [3, "Java", 57.08, 219,wx.DateTime.FromDMY(1,0,1900)],
                     [98, "langage C", 10000, 209,wx.DateTime.FromDMY(1,0,1900)],
                     ]
    dicOlv = {'listeColonnes':liste_Colonnes,
                    'listeDonnees':liste_Donnees,
                    'hauteur':650,
                    'largeur':850,
                    'recherche':True,
                    'msgIfEmpty':"Aucune donnée ne correspond à votre recherche",
                    'dictColFooter':{"nombre" : {"mode" : "total",  "alignement" : wx.ALIGN_RIGHT},
                                     "mot" : {"mode" : "nombre",  "alignement" : wx.ALIGN_CENTER},
                                     "prix": {"mode": "total", "alignement": wx.ALIGN_RIGHT},}
    }
    exampleframe = DLG_tableau(None,dicOlv=dicOlv)
    app.SetTopWindow(exampleframe)
    ret = exampleframe.ShowModal()
    app.MainLoop()
    'Exporter au format texte'
