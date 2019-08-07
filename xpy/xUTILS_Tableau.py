#!/usr/bin/python3
# -*- coding: utf-8 -*-

#  Jacques Brunel x Sébastien Gouast x Ivan Lucas
#  MATTHANIA - Projet XPY - xTableau.py (implémentation d'un tableau paramétrable)
#  2019/04/18
# note l'appel des fonctions 2.7 passent par le chargement de la bibliothèque future (vue comme past)

import wx
import os
from xpy.outils.ObjectListView import FastObjectListView, ColumnDefn, Filter

import xpy.outils.xformat
from xpy.outils.xconst import *

# ------------------------------------------------------------------------------------------------------------------

class ListViewTableau(FastObjectListView):
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
        # Récupération des paramètres perso
        self.classeAppelante = kwds.pop("classeAppelante", None)
        self.listeColonnes = kwds.pop("listeColonnes", [])
        self.msgIfEmpty = kwds.pop("msgIfEmpty", "Tableau vide")
        self.colonneTri = kwds.pop("colonneTri", None)
        self.sensTri = kwds.pop("sensTri", True)
        self.menuPersonnel = kwds.pop("menuPersonnel", None)
        self.listeDonnees = kwds.pop("listeDonnees", None)
        self.nomlisteColonnes = self.formerNomColonnes()
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
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        # self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def formerTracks(self):
        self.tracks = list()

        if self.listeDonnees is None:
            return

        for listeDonnee in self.listeDonnees:
            self.tracks.append(self.formerTrack(listeDonnee))
        return

    def formerTrack(self, listeDonnee):
        track = TrackGeneral(donnees=listeDonnee, nomColonnes=self.nomlisteColonnes)
        return track

    def formerNomColonnes(self):
        nomColonnes = list()
        for colonne in self.listeColonnes:
            nomColonnes.append(colonne.valueGetter)
        return nomColonnes

    def InitModel(self):
        self.donnees = self.GetTracks()

    def InitObjectListView(self):
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        # On définit les colonnes
        self.SetColumns(self.listeColonnes)
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

    def OnContextMenu(self, event):
        """
        Ouverture du menu contextuel

        L'idée serait de créer dans ce menu tout le 'tronc commun' c'est à dire Aperçu avant impression, Imprimer,
        Exporter au format texte (il faut demander à Isabelle si cette fonction est vraiment utilisée sinon on peut la
        supprimer), Exporter au format Excel, et pourquoi pas ajouter une option copier (la ligne ou tout le tableau)

        Ensuite on pourrait passer en paramètre une partie du menu qui sera simplement ajoutée au début.

        Par exemple les options 'tout cocher' et 'tout décocher' pourraient être activées de base et paramétrables lors de l'initialisation

        C'est ce que je vais tenter de faire dans l'exemple.
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
        # On ne sait pas encore si on va garder celui la ici
        # # Item Ouverture fiche famille
        # item = wx.MenuItem(menuPop, 10, "Ouvrir la fiche famille"))
        # item.SetBitmap(wx.Bitmap("Images/16x16/Famille.png", wx.BITMAP_TYPE_PNG))
        # menuPop.AppendItem(item)
        # self.Bind(wx.EVT_MENU, self.OuvrirFicheFamille, id=10)
        #
        # menuPop.AppendSeparator()

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

    # def OuvrirFicheFamille(self, event): Cette fonction sera surement recopiée ailleurs donc je la laisse pour le moment
    #     if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_fiche", "consulter") == False: return
    #     if len(self.Selection()) == 0:
    #         dlg = wx.MessageDialog(self, "Vous n'avez sélectionné aucune fiche famille à ouvrir !"),
    #                                "Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
    #         dlg.ShowModal()
    #         dlg.Destroy()
    #         return
    #     IDfamille = self.Selection()[0].IDfamille
    #     import DLG_Famille
    #     dlg = DLG_Famille.Dialog(self, IDfamille)
    #     if dlg.ShowModal() == wx.ID_OK:
    #         pass
    #     dlg.Destroy()
    #     self.MAJ(IDfamille)

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

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent, listview):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False

        self.SetDescriptiveText("Rechercher un texte...")
        self.ShowSearchButton(True)

        self.listView = listview
        self.nbreColonnes = self.listView.GetColumnCount()
        self.listView.SetFilter(Filter.TextSearch(self.listView, self.listView.columns[0:self.nbreColonnes]))

        self.SetCancelBitmap(wx.Bitmap(ACTIVITE_16X16_IMG, wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap(FILTRE_16X16_IMG, wx.BITMAP_TYPE_PNG))

        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, evt):
        self.Recherche()

    def OnCancel(self, evt):
        self.SetValue("")
        self.Recherche()

    def OnDoSearch(self, evt):
        self.Recherche()

    def Recherche(self):
        txtSearch = self.GetValue()
        self.ShowCancelButton(len(txtSearch))
        self.listView.GetFilter().SetText(txtSearch)
        self.listView.RepopulateList()
        self.Refresh()

class TrackGeneral(object):
    """
    Cette classe va transformer les listes en objets
    """

    def __init__(self, donnees, nomColonnes):
        for (donnee, nomColonne) in zip(donnees, nomColonnes):
            self.__setattr__(nomColonne, donnee)


# ------------------------------------------------------------------------------------------------------------------

class PNL_tableau(wx.Panel):
    def __init__(self, parent, dicOlv,*args, **kwds):
        wx.Panel.__init__(self, parent, *args,  **kwds)
        if 'recherche' in dicOlv: barreRecherche = dicOlv['recherche']
        else : barreRecherche = True
        self.parent = parent
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
                        'orientationImpression']
        #récup des seules clés possibles pour dicOLV
        dicOlvOut = {}
        dicOlvOut['id']=-1
        dicOlvOut['style']=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES
        for key,valeur in dicOlv.items():
            if key in lstParamsOlv:
                 dicOlvOut[key] = valeur

        self.myOlv = ListViewTableau(self,**dicOlvOut)

        if barreRecherche:
            self.barreRecherche = BarreRecherche(self, listview=self.myOlv)
        self.myOlv.MAJ()

        self.BoutonOK = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap("xpy/Images/100x30/Bouton_ok.png", wx.BITMAP_TYPE_ANY))
        self.BoutonOK.SetToolTip(("Cliquez ici pour enregistrer et fermer la fenêtre"))
        self.BoutonOK.Bind(wx.EVT_BUTTON, self.OnBoutonOK)

        sizerbase = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        #sizerbase = wx.BoxSizer(wx.VERTICAL)
        sizerbase.Add(self.myOlv, 10, wx.EXPAND, 40)
        if barreRecherche:
            sizerbase.Add(self.barreRecherche, 10, wx.EXPAND, 40)
        sizerbase.Add(self.BoutonOK, 10, wx.ALIGN_RIGHT, 40)
        sizerbase.AddGrowableCol(0,1)
        sizerbase.AddGrowableRow(0,1)

        self.SetSizerAndFit(sizerbase)

    def OnBoutonOK(self,event):
         self.parent.Close()

class DLG_tableau(wx.Dialog):
    def __init__(self,parent,dicOlv={}, **kwds):
        self.parent = parent
        largeur = dicOlv.pop("largeur", 500)
        longueur = dicOlv.pop("longueur", 700)
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self,parent, title=titre, size=(largeur,longueur),style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.SetBackgroundColour(wx.WHITE)
        self.marge = 10
        self.pnl = PNL_tableau(self, dicOlv,  **kwds )
        self.myOlv = self.pnl.myOlv
        self.CenterOnScreen()
        self.Layout()
    def Close(self):
        self.EndModal(wx.OK)

# -- pour tests -----------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    liste_Colonnes = [
        ColumnDefn("cle", 'left', 70, "trackLabel1"),
        ColumnDefn("mot", 'left', 200, "un mot"),
        ColumnDefn("nombre", 'right', 80, "un nombre", stringConverter=xpy.outils.xformat.FormateSolde),
        ColumnDefn("prix", 'right', 80, "un prix", stringConverter=xpy.outils.xformat.FormateMontant)
    ]
    liste_Donnees = [[18, "Bonjour", 57.02, 9],
                     [19, "Bonsoir", 57.05, 208.99],
                     [20, "Jonbour", 57.08, 209],
                     [29, "Salut", 57.08, 209],
                     [78, "Salutation", 57.08, 209],
                     [21, "Python", 57.08, 29],
                     [34, "Java", 57.08, 219],
                     [98, "langage C", 10000, 209],
                     ]
    dicOlv = {'listeColonnes':liste_Colonnes,
                    'listeDonnees':liste_Donnees,
                    'longueur':850,
                    'largeur':1000,
                    'recherche':False,
                    'msgIfEmpty':"Aucune donnée ne correspond à votre recherche"}
    exampleframe = DLG_tableau(None,dicOlv=dicOlv)
    app.SetTopWindow(exampleframe)
    ret = exampleframe.ShowModal()
    print(ret)
    app.MainLoop()
