#!/usr/bin/python3
# -*- coding: utf-8 -*-

#  Jacques Brunel x Sébastien Gouast
#  MATTHANIA - Projet XPY - xTableau.py (implémentation d'une saisie directe dans  un tableau paramétrable)
#  2020/05/15
# note l'appel des fonctions 2.7 passent par le chargement de la bibliothèque future (vue comme past)
# ce module reprend les fonctions de xUTILS_Tableau sans y faire appel
# matrice OLV

import wx
import os
import sys
import xpy.outils.xformat
from xpy.outils.ObjectListView import FastObjectListView, ColumnDefn, Filter, Footer, CTRL_Outils, OLVEvent,CellEditor
from xpy.outils.xconst import *
import datetime
import xpy.xUTILS_SaisieParams as xusp

#------------- Fonctions liées aux appels de données pour OLV ------------------------------

def ComposeLstDonnees(record,lstChamps):
    # retourne les données pour colonnes, extraites d'un record défini par une liste de champs
    lstdonnees=[]
    for ix in range(len(lstChamps)):
        lstdonnees.append(record[ix])
    return lstdonnees

def ValeursDefaut(lstNomsColonnes,lstTypes):
    # Détermine des valeurs par défaut selon le type des variables
    lstValDef = [0,]
    for ix in range(1,len(lstNomsColonnes)):
        tip = lstTypes[ix].lower()
        if tip[:3] == 'int': lstValDef.append(0)
        elif tip[:10] == 'tinyint(1)': lstValDef.append(False)
        elif tip[:5] == 'float': lstValDef.append(0.0)
        elif tip[:4] == 'date': lstValDef.append(datetime.date(1900,1,1))
        else: lstValDef.append('')
    return lstValDef

def LargeursDefaut(lstNomsColonnes,lstTypes):
    # Evaluation de la largeur nécessaire des colonnes selon le type de donnee et la longueur du champ
    lstLargDef = [0,]
    for ix in range(1, len(lstNomsColonnes)):
        tip = lstTypes[ix]
        tip = tip.lower()
        if tip[:3] == 'int': lstLargDef.append(50)
        elif tip[:5] == 'float': lstLargDef.append(60)
        elif tip[:4] == 'date': lstLargDef.append(80)
        elif tip[:7] == 'varchar':
            lg = int(tip[8:-1])*8
            if lg > 150: lg = -1
            lstLargDef.append(lg)
        elif 'blob' in tip:
            lstLargDef.append(250)
        else: lstLargDef.append(40)
    return lstLargDef

# ----------- Objets divers ----------------------------------------------------------------

class Button(wx.Button):
    # Enrichissement du wx.Button par l'image, nom, toolTip et Bind
    def __init__(self, parent,**kwds):
        #ID=None,label=None,name=None,image=None,toolTip=None,onBtn=None,...):
        # image en bitmap ou ID de artProvider sont possibles
        ID = kwds.pop('ID',None)
        label = kwds.pop('label',None)
        name = kwds.pop('name',None)
        image = kwds.pop('image',None)
        toolTip = kwds.pop('toolTip',None)
        onBtn = kwds.pop('onBtn',None)
        size = kwds.pop('size',None)
        sizeBmp = None
        sizeFont = 14
        if size:
            kwds['size']=size
            cote = int(size[1]*0.8)
            sizeBmp = (cote,cote)
            sizeFont = int(cote*0.5)
        # récupère un éventuel id en minuscule
        if not ID: ID = kwds.pop('id',None)
        if not ID : ID = wx.ID_ANY

        # récupère le label
        if not label : label = ""
        if "\n" in label: sizeFont = int(sizeFont*0.75)
        # fixe le nom interne du controle
        if not name:
            name = 'btn'
            if len(label)>0:
                name += str(label.split()[0].lower())
        kwds['name'] = name

        wx.Button.__init__(self,parent,ID,label,**kwds)
        font = wx.Font(sizeFont, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,False)
        self.SetFont(font)


        # ajout de l'image. Le code de wx.ART_xxxx est de type bytes et peut être mis en lieu de l'image
        if  isinstance(image,bytes):
            # image ArtProvider
            if sizeBmp:
                self.SetBitmap(wx.ArtProvider.GetBitmap(image,wx.ART_BUTTON,wx.Size(sizeBmp)))
            else:
                self.SetBitmap(wx.ArtProvider.GetBitmap(image,wx.ART_BUTTON))
        elif isinstance(image,wx.Bitmap):
            # image déjà en format wx
            self.SetBitmap(image)
        elif isinstance(image,str):
            # image en bitmap pointée par son adresse
            self.SetBitmap(wx.Bitmap(image))

        # ajustement de la taille si non précisée
        if not size :
            self.SetInitialSize()

        # Compléments d'actions
        self.SetToolTip(toolTip)
        self.name = name

        # implémente les fonctions bind transmises, soit par le pointeur soit par eval du texte
        if onBtn:
            if isinstance(onBtn, str):
                fonction = lambda evt, code=name: eval(onBtn)
            else:
                fonction = onBtn
            self.Bind(wx.EVT_BUTTON, fonction)

# ----------  Objets ObjectListView --------------------------------------------------------

class TrackGeneral(object):
    #    Cette classe va transformer une ligne en objet selon les listes de colonnes et valeurs par défaut(setter)
    def __init__(self, donnees,codesColonnes, nomsColonnes, setterValues):
        self.donnees = donnees
        if not(len(donnees) == len(codesColonnes)== len(nomsColonnes) == len(setterValues)):
            wx.MessageBox("Problème de nombre d'occurences!\n%d donnees, %d codes, %d colonnes et %d valeurs défaut"
                          %(len(donnees), len(codesColonnes), len(nomsColonnes), len(setterValues)))
        for ix in range(len(donnees)):
            donnee = donnees[ix]
            if setterValues[ix]:
                if (donnee is None):
                    donnee = setterValues[ix]
                else:
                    if not isinstance(donnee,type(setterValues[ix])):
                        try:
                            if type(setterValues[ix]) in (int,float):
                                donnee = float(donnee)
                            elif type(setterValues[ix]) == str:
                                donnee = str(donnee)
                        except : pass
            self.__setattr__(codesColonnes[ix], donnee)

class ListView(FastObjectListView):
    """
    Lors de l'instanciation de cette classe vous pouvez y passer plusieurs parametres :

    lstColonnes : censé être une liste d'objets ColumndeFn
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
    menuPersonnel : On peut avoir déjà créé un "pré" menu contextuel auquel
                    viendra s'ajouter le tronc commun
    titreImpression : Le titre qu'on veut donner à la page en cas d'impression
                    par exemple "Titre")
    orientationImpression : L'orientation de l'impression, True pour portrait et
                    False pour paysage

    Pour cette surcouche de OLV j'ai décidé de ne pas laisser la fonction
    OnItemActivated car ça peut changer selon le tableau
    donc ce sera le role de la classe parent (qui appelle ListView) de définir
    une fonction OnItemActivated qui sera utilisée lors du double clic sur une ligne

    Dictionnaire optionnel ou on indique si on veut faire le bilan
                (exemple somme des valeurs)
    """

    def __init__(self, *args, **kwds):
        self.ctrl_footer = None
        self.parent = args[0].parent
        self.pnlfooter = kwds.pop("pnlfooter", None)
        self.checkColonne = kwds.pop("checkColonne",True)
        self.lstColonnes = kwds.pop("lstColonnes", [])
        self.editMode = kwds.pop("editMode", True)
        self.msgIfEmpty = kwds.pop("msgIfEmpty", "Tableau vide")
        self.colonneTri = kwds.pop("colonneTri", None)
        self.sensTri = kwds.pop("sensTri", True)
        self.menuPersonnel = kwds.pop("menuPersonnel", None)
        self.listeDonnees = kwds.pop("listeDonnees", None)
        self.lstCodesColonnes = self.formerCodeColonnes()
        self.lstNomsColonnes = self.formerNomsColonnes()
        self.lstSetterValues = self.formerSetterValues()
        self.dictColFooter = kwds.pop("dictColFooter", {})

        # Choix des options du 'tronc commun' du menu contextuel
        self.exportExcel = kwds.pop("exportExcel", True)
        self.exportTexte = kwds.pop("exportTexte", True)
        self.apercuAvantImpression = kwds.pop("apercuAvantImpression", True)
        self.imprimer = kwds.pop("imprimer", True)
        self.toutCocher = kwds.pop("toutCocher", True)
        self.toutDecocher = kwds.pop("toutDecocher", True)
        self.inverserSelection = kwds.pop("inverserSelection", True)
        if not self.checkColonne:
            self.toutCocher = False
            self.toutDecocher = False
            self.inverserSelection = False

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
        if not 'autoAddRow' in kwds: kwds['autoAddRow']=True
        if not 'sortable' in kwds: kwds['sortable']=False
        FastObjectListView.__init__(self, *args,**kwds)
        # Binds perso
        self.Bind(OLVEvent.EVT_ITEM_CHECKED, self.OnItemChecked)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        if self.editMode:
            self.cellEditMode = FastObjectListView.CELLEDIT_SINGLECLICK

    def SetFooter(self, ctrl=None, dictColFooter={}):
        self.ctrl_footer = ctrl
        self.ctrl_footer.listview = self
        self.ctrl_footer.dictColFooter = dictColFooter

    def MAJ_footer(self):
        if self.ctrl_footer != None:
            self.ctrl_footer.MAJ_totaux()
            self.ctrl_footer.MAJ_affichage()

    def formerTracks(self):
        tracks = list()
        if self.listeDonnees is None:
            return tracks
        for ligneDonnees in self.listeDonnees:
            tracks.append(TrackGeneral(donnees=ligneDonnees,codesColonnes=self.lstCodesColonnes,
                                            nomsColonnes=self.lstNomsColonnes,setterValues=self.lstSetterValues))
        return tracks

    def formerCodeColonnes(self):
        codeColonnes = list()
        for colonne in self.lstColonnes:
            code = colonne.valueGetter
            codeColonnes.append(code)
        return codeColonnes

    def formerNomsColonnes(self):
        nomColonnes = list()
        for colonne in self.lstColonnes:
            nom = colonne.title
            nomColonnes.append(nom)
        return nomColonnes

    def formerSetterValues(self):
        setterValues = list()
        for colonne in self.lstColonnes:
            fmt = colonne.stringConverter
            tip = None
            if colonne.valueSetter != None:
                tip = colonne.valueSetter
            if tip == None:
                tip = ''
                if fmt:
                    fmt = colonne.stringConverter.__name__
                    if fmt[3:] in ('Montant','Solde','Decimal','Entier'):
                        tip = 0.0
                    elif fmt[3:] == 'Date':
                        tip = wx.DateTime.FromDMY(1,0,1900)
            setterValues.append(tip)
        return setterValues

    def InitObjectListView(self):
        # Couleur en alternance des lignes
        self.useExpansionColumn = True
        # On définit les colonnes
        self.SetColumns(self.lstColonnes)
        if self.checkColonne:
            self.CreateCheckStateColumn(0)
        # On définit le message en cas de tableau vide
        self.SetEmptyListMsg(self.msgIfEmpty)
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT))
        self.SetObjects(self.formerTracks())

    def MAJ(self, ID=None):
        self.selectionID = ID
        self.InitObjectListView()
        # Rappel de la sélection d'un item
        if self.selectionID != None and len(self.innerList) > 0:
            self.SelectObject(self.innerList[ID], deselectOthers=True, ensureVisible=True)

    def Selection(self):
        return self.GetSelectedObjects()

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
        if self.parent.barreRecherche:
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
    # Le Panel contiendra le listView et le footer, attention à l'étape généalogique supplémentaire
    def __init__(self, parent, **kwargs):
        id = -1
        self.parent = parent
        stylePanel = wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, parent, id=id, style=stylePanel)
        self.dictColFooter = kwargs.pop("dictColFooter", {})
        if not "id" in kwargs: kwargs["id"] = wx.ID_ANY
        if not "style" in kwargs: kwargs["style"] = wx.LC_REPORT|wx.NO_BORDER|wx.LC_HRULES|wx.LC_VRULES
        kwargs["pnlfooter"]=self

        self.buffertracks = None
        self.ctrl_listview = ListView(self,**kwargs)
        self.ctrl_footer = None
        self.SetFooter(reinit=False)
        self.ctrl_listview.Bind(wx.EVT_CHAR,self.OnChar)
        self.ctrl_listview.Bind(OLVEvent.EVT_CELL_EDIT_FINISHING,self.OnEditFinishing)
        self.ctrl_listview.Bind(OLVEvent.EVT_CELL_EDIT_STARTED,self.OnEditStarted)

        # Layout

    def Sizer(self):
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
        self.Sizer()

    def MAJ(self):
        self.ctrl_listview.MAJ()
        self.ctrl_footer.MAJ()

    def GetListview(self):
        return self.ctrl_listview

    # Handler niveau OLV
    def OnChar(self, event):
        keycode = event.GetUnicodeKey()
        if keycode == 3: self.OnCtrlC()
        if keycode == 24: self.OnCtrlX(event)
        if keycode == 22: self.OnCtrlV(event)
        event.Skip()

    def OnCtrlC(self):
        # action copier
        self.buffertracks = self.ctrl_listview.GetSelectedObjects()
        if len(self.buffertracks) == 0:
            mess = "Pas de sélection faite"
            wx.MessageBox(mess)
        return

    def OnCtrlX(self,event):
        # action copier
        self.buffertracks = self.ctrl_listview.GetSelectedObjects()
        if len(self.buffertracks) == 0:
            mess = "Pas de sélection faite"
            wx.MessageBox(mess)
            return
        for item in self.buffertracks:
            olv = event.EventObject
            ix = olv.lastGetObjectIndex
            olv.modelObjects.remove(item)
            olv.RepopulateList()
            olv._SelectAndFocus(ix)
            wx.MessageBox(u" %d lignes supprimées et mémorisées pour prochain <ctrl> V"%len(self.buffertracks))
        return

    def OnCtrlV(self,event):
        # action coller
        if self.buffertracks and len(self.buffertracks) >0:
            for item in self.buffertracks:
                olv = event.EventObject
                ix = olv.lastGetObjectIndex
                olv.modelObjects.insert(ix,item)
                olv.RepopulateList()
                olv._SelectAndFocus(ix)
        else:
            mess = "Rien en attente de collage, refaites le <ctrl> C ou <ctrl> X"
            wx.MessageBox(mess)
        return

    # Handlers niveau cell Editor
    def OnEditStarted(self, event):
        row, col = self.ctrl_listview.cellBeingEdited
        code = self.ctrl_listview.lstCodesColonnes[col]
        # appel des éventuels spécifiques
        if hasattr(self.Parent, 'OnEditStarted'):
            self.parent.OnEditStarted(code)
        #except:
        #print(sys.exc_info())
        # stockage de la valeur initiale de la dernière cellule éditée
        olv = self.ctrl_listview
        row, col = olv.cellBeingEdited
        track = olv.GetObjectAt(row)
        track.old_data = track.donnees[col]
        event.Skip()

    def OnEditFinishing(self, event):
        # gestion des actions de sortie
        row, col = self.ctrl_listview.cellBeingEdited
        track = self.ctrl_listview.GetObjectAt(row)
        new_data = self.ctrl_listview.cellEditor.GetValue()
        code = self.ctrl_listview.lstCodesColonnes[col]
        # appel des éventuels spécifiques
        if hasattr(self.Parent, 'OnEditFinishing'):
            self.parent.OnEditFinishing(code,new_data)
        # stockage de la nouvelle saisie
        track.__setattr__(code, new_data)
        track.donnees[col] = new_data
        event.Skip()

    def OnEditFunctionKeys(self, event):
        # Fonction appelée par CellEditor.Validator lors de l'activation d'une touche de fonction
        if self.ctrl_listview.cellBeingEdited:
            try:
                self.parent.OnEditFunctionKeys(event)
                event.Skip()
            except:
                row, col = self.ctrl_listview.cellBeingEdited
                wx.MessageBox(u"Touche <F%d> pressée sur cell (%d,%d)\n\n'error: %s'" % (event.GetKeyCode() - wx.WXK_F1 + 1,
                                                                                         row, col, sys.exc_info()[0]))

# ----------- Composition de l'écran -------------------------------------------------------
class PNL_params(wx.Panel):
    #panel de paramètres de l'application
    def __init__(self, parent, dicParams, **kwds):
        self.lanceur = dicParams.pop('lanceur', None)
        self.lstActions = dicParams.pop('lstActions', None)
        self.lstInfos = dicParams.pop('lstInfos', None)
        self.lstBtns = dicParams.pop('lstBtns', None)
        self.dicOnClick = dicParams.pop('dicOnClick', None)
        wx.Panel.__init__(self, parent, **kwds)
        self.parent = parent
        self.ctrl = xusp.CTRL_property(self, matrice=dicParams, enable=True)
        self.Sizer()

    def Sizer(self):
        #composition de l'écran selon les composants
        sizerparams = wx.BoxSizer(wx.HORIZONTAL)
        sizerparams.Add(self.ctrl,1,wx.BOTTOM|wx.LEFT,3)
        self.SetSizerAndFit(sizerparams)

class PNL_corps(wx.Panel):
    #panel olv avec habillage optionnel pour des boutons actions (à droite) des infos (bas gauche) et boutons sorties
    def __init__(self, parent, dicOlv,*args, **kwds):
        hauteur = dicOlv.pop('hauteur',350)
        largeur = dicOlv.pop('largeur',650)
        wx.Panel.__init__(self, parent, *args,  **kwds)
        #ci dessous l'ensemble des autres paramètres possibles pour OLV
        lstParamsOlv = ['id',
                        'style',
                        'lstColonnes',
                        'listeDonnees',
                        'msgIfEmpty',
                        'sensTri',
                        'exportExcel',
                        'exportTexte',
                        'checkColonne',
                        'apercuAvantImpression',
                        'imprimer',
                        'saisie',
                        'toutCocher',
                        'toutDecocher',
                        'inverserSelection',
                        'titreImpression',
                        'orientationImpression',
                        'dictColFooter']
        self.avecFooter = ("dictColFooter" in dicOlv)
        if not self.avecFooter : lstParamsOlv.remove('dictColFooter')
        if 'recherche' in dicOlv: self.barreRecherche = dicOlv['recherche']
        else : self.barreRecherche = True
        self.parent = parent
        #récup des seules clés possibles pour dicOLV
        dicOlvOut = {}
        for key,valeur in dicOlv.items():
            if key in lstParamsOlv:
                 dicOlvOut[key] = valeur

        # choix footer ou pas
        self.olv = PanelListView(self,**dicOlvOut)
        self.ctrlOlv = self.olv.ctrl_listview
        if self.barreRecherche:
            self.ctrloutils = CTRL_Outils(self, listview=self.ctrlOlv, afficherCocher=False)
        self.ctrlOlv.SetMinSize((largeur,hauteur))
        self.ctrlOlv.MAJ()
        self.Sizer()

    def Sizer(self):
        #composition de l'écran selon les composants
        sizerolv = wx.BoxSizer(wx.VERTICAL)
        sizerolv.Add(self.olv, 10, wx.EXPAND, 10)
        if self.barreRecherche:
            sizerolv.Add(self.ctrloutils, 0, wx.EXPAND, 10)
        self.SetSizerAndFit(sizerolv)

class PNL_Pied(wx.Panel):
    #panel infos (gauche) et boutons sorties(droite)
    def __init__(self, parent, dicPied, **kwds):
        self.lanceur = dicPied.pop('lanceur',None)
        self.lstActions = dicPied.pop('lstActions',None)
        self.lstInfos = dicPied.pop('lstInfos',None)
        self.lstBtns = dicPied.pop('lstBtns',None)
        self.dicOnClick = dicPied.pop('dicOnClick',None)
        if (not self.lstBtns) and (not self.lstInfos):
            #force la présence d'un pied d'écran par défaut
            self.lstBtns = [('BtnOK', wx.ID_OK, wx.Bitmap("xpy/Images/100x30/Bouton_ok.png", wx.BITMAP_TYPE_ANY),
                           "Cliquez ici pour fermer la fenêtre")]
        wx.Panel.__init__(self, parent,  **kwds)
        self.parent = parent
        self.Sizer()

    def Sizer(self,reinit = False):
        self.itemsBtns = self.GetItemsBtn(self.lstBtns)
        self.itemsInfos = self.CreateItemsInfos(self.lstInfos)
        nbinfos = len(self.itemsInfos)
        nbcol=(len(self.itemsBtns)+len(self.itemsInfos)+1)
        #composition de l'écran selon les composants
        sizerpied = wx.FlexGridSizer(rows=1, cols=nbcol, vgap=0, hgap=0)
        if self.lstInfos:
            sizerpied.AddMany(self.itemsInfos)
        sizerpied.Add((10,10),1,wx.ALL|wx.EXPAND,5)
        if self.lstBtns:
            sizerpied.AddMany(self.itemsBtns)
        sizerpied.AddGrowableCol(nbinfos)
        self.SetSizer(sizerpied)

    def GetItemsBtn(self,lstBtns):
        # décompactage des paramètres de type bouton, différents constructeurs
        lstWxBtns = []
        for btn in lstBtns:
            # gestion par série :(code, ID, image ou texte, texteToolTip), image ou texte mais pas les deux!
            if isinstance(btn,(tuple,list)):
                try:
                    (code,ID,label,tooltip) = btn
                    if isinstance(label,wx.Bitmap):
                        bouton = wx.BitmapButton(self,ID,label)
                    elif isinstance(label,str):
                        bouton = wx.Button(self,ID,label)
                    else: bouton = wx.Button(self,ID,'Erreur!')
                    bouton.SetToolTip(tooltip)
                    bouton.name = code
                    #le bouton OK est par défaut, il ferme l'écran DLG
                    if code == 'BtnOK':
                        bouton.Bind(wx.EVT_BUTTON, self.OnBoutonOK)
                    #implémente les fonctions bind transmises, soit par le pointeur soit par eval du texte
                    if self.dicOnClick and code in self.dicOnClick:
                        if isinstance(self.dicOnClick[code],str):
                            fonction = lambda evt,code=code: eval(self.dicOnClick[code])
                        else: fonction = self.dicOnClick[code]
                        bouton.Bind(wx.EVT_BUTTON, fonction)
                    lstWxBtns.append((bouton, 0, wx.ALL, 5))
                except:
                    bouton = wx.Button(self, wx.ID_ANY, 'Erreur\nparam!')
                    lstWxBtns.append((bouton, 0, wx.ALL, 5))
            # gestion par classe Button(parent,**kwds
            elif isinstance(btn,dict):
                lstWxBtns.append((Button(self,**btn),0,wx.ALL,5))
        return lstWxBtns

    def CreateItemsInfos(self,lstInfos):
        # images ou texte sont retenus
        self.infosImage = None
        self.infosTexte = None
        lstItems = [(7,7)]
        for item in lstInfos:
            if isinstance(item,wx.Bitmap):
                self.infosImage = wx.StaticBitmap(self, wx.ID_ANY, item)
                lstItems.append((self.infosImage,0,wx.ALIGN_LEFT|wx.TOP,10))
            elif isinstance(item,str):
                self.infosTexte = wx.StaticText(self,wx.ID_ANY,item)
                lstItems.append((self.infosTexte,10,wx.ALIGN_LEFT|wx.ALL|wx.EXPAND,5))
            lstItems.append((7,7))
        return lstItems

    def SetItemsInfos(self,text=None,image=None,):
        # après create  permet de modifier l'info du pied pour dernière image et dernier texte
        if image:
            self.infosImage.SetBitmap(image)
        if text:
            self.infosTexte.SetLabelText(text)

    def OnBoutonOK(self,event):
        self.parent.Close()

# ------------- Lancement ------------------------------------------------------------------
class DLG_tableau(wx.Dialog):
    # minimum fonctionnel dans dialog tout est dans les trois pnl
    def __init__(self,parent,dicParams={},dicOlv={},dicPied={}, **kwds):
        self.parent = parent
        listArbo=os.path.abspath(__file__).split("\\")
        titre = listArbo[-1:][0] + "/" + self.__class__.__name__
        wx.Dialog.__init__(self,None, title=titre, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.pnlParams = PNL_params(self, dicParams)
        self.pnlOlv = PNL_corps(self, dicOlv,  **kwds )
        self.ctrlOlv = self.pnlOlv.ctrlOlv
        self.pnlPied = PNL_Pied(self, dicPied,  **kwds )
        sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=0)
        sizer_base.Add(self.pnlParams, 1, wx.TOP| wx.EXPAND, 3)
        sizer_base.Add(self.pnlOlv, 1, wx.TOP| wx.EXPAND, 3)
        sizer_base.Add(self.pnlPied, 0,wx.ALL|wx.EXPAND, 3)
        sizer_base.AddGrowableCol(0)
        sizer_base.AddGrowableRow(1)
        self.CenterOnScreen()
        self.Layout()
        self.SetSizerAndFit(sizer_base)

    def Close(self):
        self.EndModal(wx.OK)

# ------------ Pour tests ------------------------------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    # tableau OLV central de l'écran ,
    #                    stringConverter=xpy.outils.xformat.FmtMontant
    liste_Colonnes = [
        ColumnDefn("null", 'centre', 0, "IX", valueSetter=''),
        ColumnDefn("clé", 'centre', 60, "cle", valueSetter=True, isSpaceFilling=False ,cellEditorCreator = CellEditor.BooleanEditor),
        ColumnDefn("mot d'ici", 'left', 200, "mot", valueSetter='A saisir', isEditable=True),
        ColumnDefn("nbre", 'right', -1, "nombre", isSpaceFilling=True, valueSetter=0.0,
                   stringConverter=xpy.outils.xformat.FmtDecimal),
        ColumnDefn("prix", 'left', 80, "prix", valueSetter=0.0, isSpaceFilling=True,cellEditorCreator = CellEditor.ComboEditor),
        ColumnDefn("date", 'center', 80, "date", valueSetter=wx.DateTime.FromDMY(1, 0, 1900), isSpaceFilling=True,
                   stringConverter=xpy.outils.xformat.FmtDate),
        ColumnDefn("choice", 'center', 40, "choice", valueSetter="mon item",choices=['CHQ','VRT','ESP'], isSpaceFilling=True,
                   cellEditorCreator = CellEditor.ChoiceEditor,)
    ]
    liste_Donnees = [[1,False, "Bonjour", -1230.05939, -1230.05939, None,"deux"],
                     [2,None, "Bonsoir", 57.5, 208.99,datetime.date.today(),None],
                     [3,'', "Jonbour", 0, 'remisé', datetime.date(2018, 11, 20), "mon item"],
                     [4,29, "Salut", 57.082, 209, wx.DateTime.FromDMY(28, 1, 2019),"Gérer l'entrée dans la cellule"],
                     [None,None, "Salutation", 57.08, 0, wx.DateTime.FromDMY(1, 7, 1997), '2019-10-24'],
                     [None,2, "Python", 1557.08, 29, wx.DateTime.FromDMY(7, 1, 1997), '2000-12-25'],
                     [None,3, "Java", 57.08, 219, wx.DateTime.FromDMY(1, 0, 1900), None],
                     [None,98, "langage C", 10000, 209, wx.DateTime.FromDMY(1, 0, 1900), ''],
                     ]
    dicOlv = {'lstColonnes': liste_Colonnes,
              'listeDonnees': liste_Donnees,
              'hauteur': 350,
              'largeur': 650,
              'checkColonne': False,
              'recherche': True,
              'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",}
    """
              'dictColFooter': {"nombre": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                "mot": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},}
              }
    """

    # boutons de bas d'écran - infos: texte ou objet window.  Les infos sont  placées en bas à gauche
    lstBtns = [('BtnPrec',-1, wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_OTHER, (42, 22)),"Cliquez ici pour test info"),
               ('BtnPrec2',-1, "Ecran\nprécédent", "Retour à l'écran précédent next"),
               ('BtnOK', -1, wx.Bitmap("xpy/Images/100x30/Bouton_fermer.png", wx.BITMAP_TYPE_ANY),"Cliquez ici pour fermer la fenêtre")
               ]
    lstInfos = [wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, ),
                wx.Bitmap("xpy/Images/16x16/Magique.png", wx.BITMAP_TYPE_PNG),
                "Autre\nInfo"]

    def modifLstInfos(self):
        self.SetItemsInfos('C est nouveau',wx.ArtProvider.GetBitmap(wx.ART_FIND, wx.ART_OTHER, (16, 16)))
        self.Refresh()
        return
    dicOnClick = {'BtnPrec': lambda evt: modifLstInfos(evt.EventObject.Parent)}
    # l'info se compmose d'une imgae et d'un texte
    dicPied = {'lstBtns': lstBtns, 'dicOnClick': dicOnClick, "lstInfos": lstInfos}

    # cadre des paramètres
    import datetime
    dicParams = {
            ("ident","Vos paramètres"):[
                {'name': 'date', 'genre': 'Date', 'label': 'Début de période', 'value': datetime.date.today(),
                                    'help': 'Ce préfixe à votre nom permet de vous identifier'},
                {'name': 'utilisateur', 'genre': 'String', 'label': 'Votre identifiant', 'value': "NomSession",
                                    'help': 'Confirmez le nom de sesssion de l\'utilisateur'},
                ],
            }

    exempleframe = DLG_tableau(None,dicParams,dicOlv=dicOlv,dicPied=dicPied)
    app.SetTopWindow(exempleframe)
    ret = exempleframe.ShowModal()
    app.MainLoop()
