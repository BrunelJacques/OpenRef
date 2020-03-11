#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, Jacques Brunel
# Licence:         Licence GNU GPL
# Permet un choix dans une liste et retourne l'indice
#------------------------------------------------------------------------


import wx, copy
from xpy.outils.ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils
import xpy.outils.xbandeau as xbd
import xpy.xGestionDB


def FormateMontant(montant):
    if montant == None or montant == "": return ""
    if int(montant) == 0: return ""
    return u"%.2f " % (montant)

def LettreSuivante(lettre=''):
    if not isinstance(lettre,str): lettre = 'A'
    if lettre == '': lettre = 'A'
    # incrémentation d'un lettrage
    lastcar = lettre[-1]
    precars = lettre[:-1]
    if ord(lastcar) in (90,122):
        if len(precars) == 0:
            precars = chr(ord(lastcar)-25)
        else:
            precars= LettreSuivante(precars)
        new = precars + chr(ord(lastcar)-25)
    else:
        new = precars + chr(ord(lastcar) + 1)
    return new

class CTRL_Solde(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="panel_solde", style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL,
                          size=(100, 40))
        self.parent = parent

        # Solde du compte
        self.ctrl_solde = wx.StaticText(self, -1, u"0.00 ")
        font = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.ctrl_solde.SetFont(font)

        # Layout
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_solde, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)
        # self.SetToolTip(u"Solde")
        self.ctrl_solde.SetToolTip(u"Solde")

    def SetSolde(self, montant=0.0):
        """ MAJ integrale du controle avec MAJ des donnees """
        if montant > 0.0:
            label = u"+ %.2f " % (montant)
            self.SetBackgroundColour("#C4BCFC")  # Bleu
        elif montant == 0.0:
            label = u"0.00 "
            self.SetBackgroundColour("#5DF020")  # Vert
        else:
            label = u"- %.2f " % (-montant,)
            self.SetBackgroundColour("#F81515")  # Rouge
        self.ctrl_solde.SetLabel(label)
        self.Layout()
        self.Refresh()

class Track(object):
    def __init__(self, donnees,champs):
        for ix in range(len(champs)):
            champ= champs[ix]
            if isinstance(donnees[ix],(int,bool,float)):
                commande = "self.%s = donnees[ix]"%(champ)
            else:
                commande = "self.%s = donnees[ix]"%(champ)
            exec(commande)



class DialogLettrage(wx.Dialog):
    # Gestion d'un lettrage à partir de deux dictionnaires
    def __init__(self, parent,dicList1={},lstChamps1=[],dicList2={},lstChamps2=[],lstLettres=[],columnSort=3,
                 LargeurCode=80,LargeurLib=100,minSize=(350, 350),titre=u"Lettrage des montants",
                 intro=u"Cochez les lignes associées puis cliquez sur lettrage...", altOK = False):
        wx.Dialog.__init__(self, None, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)

        self.SetTitle("xchoixListe.DialogLettrage")
        self.parent = parent
        self.lstLettresOriginal = copy.deepcopy(lstLettres)
        self.lstLettres = lstLettres
        self.dicList1 = dicList1
        self.dicList2 = dicList2
        self.lstChamps1 = lstChamps1
        self.lstChamps2 = lstChamps2
        self.columnSort = columnSort
        self.altOK = altOK
        self.choix = None
        self.parent = parent
        self.minSize = minSize
        self.wCode = LargeurCode
        self.wLib = LargeurLib
        self.nbValeurs = len(lstChamps2)
        if len(lstChamps1) > len(lstChamps2): self.nbValeurs = len(lstChamps1)
        self.nbColonnes = self.nbValeurs + 4
        self.lstLibels = [u"DC",u"ID",u"Let",]+([u"",]*(self.nbValeurs-1))+[u"Débits",u"Crédits",]

        #composition des libelles colonnes et des codes
        i=3
        for item in lstChamps1:
            if item.lower() == u"montant": continue
            self.lstLibels[i] = item
            i +=1
        i=3
        for item in lstChamps2:
            if item.lower() == u"montant": continue
            if self.lstLibels[i] != item:
                self.lstLibels[i] += u"/%s"%item
            i +=1
        # le code est le dernier mot du libellé de la colonne, sans accent et en minuscule
        self.lstCodes = [xpy.xGestionDB.Supprime_accent(x.split(u"/")[-1].strip()).lower() for x in self.lstLibels]
        # vérif unicité code
        lstano = [x for x in self.lstCodes if self.lstCodes.count(x)>1]
        if len(lstano)>0:
            wx.MessageBox(u"Les noms des champs doivent être uniques dans un même liste liste!\n voir le doublon: '%s'"%lstano[0], u"Impossible")
            return
        # constitution de la liste de données et calcul au passage de la largeur nécessaire pour les colonnes
        self.lstDonnees = []
        self.lstWidth = [30]*self.nbColonnes # préalimentation d'une largeur par défaut
        self.lstWidth[1]=60 # lardeur de la colonne ID
        multiwidth = 6 # multiplicateur du nombre de caratère maxi dans la colonne pour déterminer la largeur
        for libel in self.lstLibels:
            if self.lstWidth[self.lstLibels.index(libel)] < multiwidth*len(libel)+10:
                self.lstWidth[self.lstLibels.index(libel)] = multiwidth*len(libel)+10
        for sens in (+1,-1):
            # les montants seront alignés dans les deux colonnes le plus à droite
            if sens == +1:
                ixMtt = self.nbColonnes-2
                dic = dicList1
                champs = lstChamps1
            else:
                ixMtt = self.nbColonnes-1
                dic = dicList2
                champs = lstChamps2
            if not "montant" in str(champs).lower():
                wx.MessageBox(u"Les listes de données n'ont pas chacune un champ 'montant'!",u"Impossible")
                return
            nbval = len(champs)
            # balayage des deux dictionnaires de données et de leur liste de champs
            for key,item in dic.iteritems():
                donnee=[sens,key,""] + ([""]*(self.nbValeurs-1)) + [0.0,0.0]
                ixVal = 3
                for i in range(nbval):
                    if u"montant" in champs[i].lower():
                        valMtt = item[i]
                        continue
                    donnee[ixVal] = item[i]
                    if isinstance(item[i],(str)):
                        lg = len(item[i])
                    else: lg = len(str(item[i]))
                    if self.lstWidth[ixVal] < lg*multiwidth + 10: self.lstWidth[ixVal] = lg*multiwidth + 10
                    ixVal += 1
                # ajout du montant à droite
                donnee[ixMtt] = valMtt
                self.lstDonnees.append(donnee)

        # Bandeau
        self.ctrl_bandeau = xbd.Bandeau(self, titre=titre, texte=intro, hauteurHtml=15,
                                                 nomImage="xpy.Images/22x22/matth.png")
        # conteneur des données
        self.listview = FastObjectListView(self, id=-1, style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES)
        self.listview.SetMinSize((10, 10))
        self.barre_recherche = CTRL_Outils(self, listview=self.listview, afficherCocher=True)

        # Boutons
        self.bouton_lettrer = wx.Button(self, id = wx.ID_APPLY,label="Lettrer")
        self.bouton_lettrer.SetBitmap(wx.Bitmap("xpy/Images/32x32/Action.png"))
        self.bouton_delettrer = wx.Button(self, label=u"DeLettrer", )
        self.bouton_delettrer.SetBitmap(wx.Bitmap("xpy/Images/32x32/Depannage.png"))
        self.bouton_fermer = wx.Button(self, label=u"Annuler",)
        self.bouton_fermer.SetBitmap(wx.Bitmap("xpy/Images/32x32/Annuler.png"))
        self.bouton_ok = wx.Button(self, label=u"Valider", )
        self.bouton_ok.SetBitmap(wx.Bitmap("xpy/Images/32x32/Valider.png"))
        self.__set_properties()
        self.MAJ()
        self.__do_layout()

    def __set_properties(self):
        # TipString, Bind et constitution des colonnes de l'OLV
        self.SetMinSize(self.minSize)
        self.bouton_lettrer.SetToolTip(u"Cliquez ici après avoir coché des lignes à associer")
        self.bouton_delettrer.SetToolTip(u"Cliquez ici après avoir sélectionné une ligne de la lettre à supprimer")
        self.bouton_ok.SetToolTip(u"Cliquez ici pour valider et enregistrer les modifications")
        self.bouton_fermer.SetToolTip(u"Cliquez ici pour abandonner les modifications")
        self.listview.SetToolTip(u"Double Cliquez pour cocher")
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnClicOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnClicFermer, self.bouton_fermer)
        self.Bind(wx.EVT_BUTTON, self.OnClicLettrer, self.bouton_lettrer)
        self.Bind(wx.EVT_BUTTON, self.OnClicDelettrer, self.bouton_delettrer)
        self.listview.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnDblClic)

        # Couleur en alternance des lignes
        self.listview.oddRowsBackColor = "#F0FBED"
        self.listview.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.listview.useExpansionColumn = True

        # Construction des colonnes de l'OLV
        lstColumns = [ ColumnDefn("coche", "left", 0, 0),]
        for ix in range(self.nbColonnes-2):
            if ix in (1,2):
                justif = 'right'
            else: justif = 'left'
            code = self.lstCodes[ix]
            lstColumns.append(ColumnDefn(self.lstLibels[ix], justif, width=self.lstWidth[ix], valueGetter=code,
                                         maximumWidth=self.lstWidth[ix],isEditable=False,isSpaceFilling=True,))
        lstColumns.append(ColumnDefn(self.lstLibels[-2],'right',maximumWidth=80,valueGetter="debits",stringConverter=FormateMontant,
                                     isEditable=False,isSpaceFilling=True))
        lstColumns.append(ColumnDefn(self.lstLibels[-1],'right',maximumWidth=80,valueGetter="credits",stringConverter=FormateMontant,
                                     isEditable=False,isSpaceFilling=True))
        self.listview.SetColumns(lstColumns)
        self.listview.SetSortColumn(self.columnSort)
        self.listview.CreateCheckStateColumn(0)

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)

        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        gridsizer_base.Add(self.listview, 5, wx.LEFT | wx.RIGHT | wx.EXPAND, 0)
        gridsizer_base.Add(self.barre_recherche, 1, wx.EXPAND, 0)
        gridsizer_base.Add((5, 5), 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 0)

        # Boutons
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=6, vgap=0, hgap=0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_lettrer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_delettrer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_fermer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_ok, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(0)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def MAJ(self):
        lettre = "a"
        # réinit lettrage à partir de lstLettres
        self.dicEquiLet = {}
        self.dicLettres = {}
        for ID1,ID2 in self.lstLettres:
            let3 = None
            try:
                let1 = self.dicLettres[(+1,ID1)]
            except: let1=None
            try:
                let2 = self.dicLettres[(-1,ID2)]
            except: let2=None
            if let1 and let2:
                #lignes déjà lettrées
                if let1 != let2:
                    # fusionne let1 dans let2
                    for sens in (+1,-1):
                        for key,item in self.dicLettres.items():
                            if key == (sens,ID1) or key == (sens,ID2):
                                if item == let2 : item = let1
            # on étend la lettre déjà présente
            elif let1: self.dicLettres[(-1,ID2)] = let1
            elif let2: self.dicLettres[(+1,ID1)] = let2
            # pose la lettre dans les deux lignes car non encore lettrées
            else:
                self.dicLettres[(+1,ID1)] = lettre
                self.dicLettres[(-1,ID2)] = lettre
                let3 = lettre
                lettre = LettreSuivante(lettre)
            for let9 in (let1,let2,let3):
                if let9 and (not let9 in self.dicEquiLet):
                    self.dicEquiLet[let9] = 0.0

        # calcul de l'équilibre
        for donnee in self.lstDonnees:
            if (donnee[0],donnee[1]) in self.dicLettres:
                let = self.dicLettres[(donnee[0],donnee[1])]
                self.dicEquiLet[let] += donnee[0]*(donnee[-1]+donnee[-2])
        # application de la lettre dans les données et vérif de l'équilibre pour la mettre en majuscules
        for donnee in self.lstDonnees:
            key = (donnee[0],donnee[1])
            if key in self.dicLettres:
                let = self.dicLettres[key]
                if abs(self.dicEquiLet[let]) < 0.5:
                    let = let.upper()
                donnee[2] = let
            else: donnee[2] = ""
        # constitution des données track pour l'OLV
        self.tracks = [Track(don,self.lstCodes) for don in self.lstDonnees]
        self.listview.SetObjects(self.tracks)
        #self.listview.Refresh()
        self.listview.CocheListeRien()
        #self.__do_layout()

    def OnDblClic(self, event):
        state = self.listview.GetCheckState(self.listview.GetSelectedObject())
        if state:
            state = False
        else:
            state = True
        self.listview.SetCheckState(self.listview.GetSelectedObject(), state)
        self.listview.Refresh()

    def ClearLetters(self,choix):
        # récup des ID à lettrer, puis suppression des items
        lstID1 = []
        lstID2 = []
        for ligne in choix:
            if ligne.dc == +1: lstID1.append(ligne.id)
            else: lstID2.append(ligne.id)
            ligne.let = ''
        # constitution de la liste des suppressions dans lstLettres
        lstSupprimer = []
        for ID1,ID2 in self.lstLettres:
            if ID1 in lstID1 or ID2 in lstID2:
                lstSupprimer.append((ID1,ID2))
        # suppression des ancienes lettres
        for item in lstSupprimer:
            self.lstLettres.remove(item)
        return lstID1,lstID2

    def OnClicLettrer(self, event):
        choix = self.listview.GetCheckedObjects()
        if self.listview.GetSelectedObjects()[0] not in choix:
            # attention la sélection n'est pas cochée
            wx.MessageBox(u"La ligne sélectionnée n'est pas cochée!\n\nrisque de quiproquo sur le travail demandé")
            event.Skip()
            return
        # on ne relettre pas les lettres majuscules qui sont équilibrées
        lettrer = [x for x in choix if x.let.lower() == x.let]
        if len(lettrer) == 0:
            wx.MessageBox(u"Pas de lettre modifiable !\n\nIl faut cocher des lettres en minuscule ou sans lettre pour pouvoir lettrer")
            event.Skip()
            return
        lstID1,lstID2 = self.ClearLetters(choix)
        # ajout de nouveaux lettrages produit cartésien des lignes cochées
        if lstID1 == [] : lstID1=[None]
        if lstID2 == [] : lstID2=[None]
        for ID1 in lstID1:
            for ID2 in lstID2:
                self.lstLettres.append((ID1,ID2))
        event.Skip()
        self.MAJ()

    def OnClicDelettrer(self, event):
        choix = self.listview.GetCheckedObjects()
        if self.listview.GetSelectedObjects()[0] not in choix:
            # attention la sélection n'est pas cochée
            wx.MessageBox(u"La ligne sélectionnée n'est pas cochée!\n\nrisque de quiproquo sur le travail demandé")
            event.Skip()
            return
        delettrer = [x for x in choix if (x.let.lower() == x.let) and (x.let != '')]
        if len(delettrer) == 0:
            wx.MessageBox(u"Pas de lettre modifiable !\n\nIl faut cocher des lettres en minuscule pour pouvoir delettrer")
        lstID1,listID2 = self.ClearLetters(choix)
        event.Skip()
        self.MAJ()

    def OnClicFermer(self, event):
        self.choix = []
        self.EndModal(wx.ID_CANCEL)

    def OnClicOk(self, event):
        self.EndModal(wx.ID_OK)

    def GetLettresSuppr(self):
        return [x for x in self.lstLettresOriginal if not x in self.lstLettres]

    def GetLettresNews(self):
        return [(x,y) for (x,y) in self.lstLettres if not (x,y) in self.lstLettresOriginal]

class DialogCoches(wx.Dialog):
    def __init__(self, parent, listeOriginale=[("Choix1","Texte1"),("Choix2","Texte2"),],columnSort=1,
                 LargeurCode=80,LargeurLib=100,minSize=(350, 350),titre=u"Faites un choix !",
                 intro=u"Double Clic sur la ou les réponses souhaitées...", altOK = False):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)

        self.SetTitle("xchoixListe.DialogCoches")
        self.columnSort = columnSort
        self.altOK = altOK
        self.choix= None
        self.parent = parent
        self.minSize = minSize
        self.wCode = LargeurCode
        self.wLib = LargeurLib
        self.liste = []
        self.nbColonnes=0
        for item in listeOriginale :
            if isinstance(item,(list,tuple)):
                self.nbColonnes = len(item)
            else:
                self.nbColonnes = 1
                item = (str(item),)
            self.liste.append(item)

        # Bandeau
        self.ctrl_bandeau = xbd.Bandeau(self, titre=titre, texte=intro,  hauteur=15, nomImage="xpy/Images/32x32/Python.png")
        # conteneur des données
        self.listview = FastObjectListView(self)
        # Boutons
        self.bouton_ok = wx.Button(self, label=u"Valider" )
        self.bouton_ok.SetBitmap(wx.Bitmap("xpy/Images/32x32/Valider.png"))
        self.bouton_fermer = wx.Button(self, label=u"Annuler")
        self.bouton_fermer.SetBitmap(wx.Bitmap("xpy/Images/32x32/Annuler.png"))

        self.__set_properties()
        self.__do_layout()
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnClicOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnClicFermer, self.bouton_fermer)
        self.listview.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.OnDblClic)

    def __set_properties(self):
        self.SetMinSize(self.minSize)
        self.bouton_fermer.SetToolTip(u"Cliquez ici pour fermer")
        self.listview.SetToolTip(u"Double Cliquez pour choisir")
        # Couleur en alternance des lignes
        self.listview.oddRowsBackColor = "#F0FBED"
        self.listview.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.listview.useExpansionColumn = True

        if self.nbColonnes >1:
            filCode = False
        else: filCode = True
        lstColumns = [
            ColumnDefn("Code", "left", 0, 0),
            ColumnDefn("Code", "left", self.wCode, 0,isSpaceFilling=filCode),]
        if self.nbColonnes >1:
            texte = "Libelle (non modifiables)"
            for ix in range(1,self.nbColonnes):
                lstColumns.append(ColumnDefn(texte, "left", self.wLib, ix, isSpaceFilling=True))
                texte = "-"

        self.listview.SetColumns(lstColumns)
        self.listview.SetSortColumn(self.columnSort)
        self.listview.CreateCheckStateColumn(0)
        self.listview.SetObjects(self.liste)

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)

        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        gridsizer_base.Add(self.listview, 5, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)
        gridsizer_base.Add((5, 5), 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)

        # Boutons
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=0, hgap=0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_ok, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_fermer, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(0)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnClicFermer(self, event):
        self.choix = []
        self.EndModal(wx.ID_CANCEL)

    def OnClicOk(self, event):
        self.choix = self.listview.GetCheckedObjects()
        if len(self.choix) == 0:
            dlg = wx.MessageDialog(self, u"Pas de sélection faite !\nIl faut choisir ou cliquer sur annuler", u"Accord Impossible", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            if self.nbColonnes == 1:
                self.choix = [x[0] for x in self.choix]
            self.EndModal(wx.ID_OK)

    def OnDblClic(self, event):
        state = self.listview.GetCheckState(self.listview.GetSelectedObject())
        if state :
            state = False
        else : state = True
        self.listview.SetCheckState(self.listview.GetSelectedObject(),state)
        self.listview.Refresh()

class Dialog(wx.Dialog):
    def __init__(self, parent, listeOriginale=[("Choix1","Texte1"),],LargeurCode=150,LargeurLib=100,colSort=0, minSize=(600, 350),
                 titre=u"Faites un choix !", intro=u"Double Clic sur la réponse souhaitée..."):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.SetTitle("xchoixListe")
        self.choix= None
        self.colSort = colSort
        self.parent = parent
        self.minSize = minSize
        self.wCode = LargeurCode
        self.wLib = LargeurLib
        self.liste = []
        ix = 1
        for item in listeOriginale :
            if len(item) == 1:
                self.liste.append((ix,item[0]))
            else:
                self.liste.append(item)
            ix += 1

        # Bandeau
        self.ctrl_bandeau = xbd.Bandeau(self, titre=titre, texte=intro,  hauteur=15, nomImage="xpy/Images/32x32/Python.png")
        # conteneur des données
        self.listview = FastObjectListView(self)
        # Boutons
        self.bouton_ok = wx.Button(self, label=u"Valider",)
        self.bouton_ok.SetBitmap(wx.Bitmap("xpy/Images/32x32/Valider.png"))
        self.bouton_fermer = wx.Button(self, label=u"Annuler", )
        self.bouton_fermer.SetBitmap(wx.Bitmap("xpy/Images/32x32/Annuler.png"))

        self.__set_properties()
        self.__do_layout()
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnDblClicOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnDblClicFermer, self.bouton_fermer)
        self.listview.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.OnDblClic)

    def __set_properties(self):
        self.SetMinSize(self.minSize)
        self.bouton_fermer.SetToolTip(u"Cliquez ici pour fermer")
        self.listview.SetToolTip(u"Double Cliquez pour choisir")
        # Couleur en alternance des lignes
        self.listview.oddRowsBackColor = "#F0FBED"
        self.listview.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.listview.useExpansionColumn = True
        self.listview.SetColumns([
            ColumnDefn("Code", "left", self.wCode,  0),
            ColumnDefn("Libelle (non modifiables)", "left", self.wLib, 1,isSpaceFilling = True),
            ])
        self.listview.SetSortColumn(self.listview.columns[self.colSort])
        self.listview.SetObjects(self.liste)

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)

        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        gridsizer_base.Add(self.listview, 5, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)
        gridsizer_base.Add((5, 5), 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)

        # Boutons
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=0, hgap=0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_ok, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_fermer, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(0)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnDblClicFermer(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnDblClicOk(self, event):
        self.choix = self.listview.GetSelectedObject()
        if self.choix == None:
            dlg = wx.MessageDialog(self, u"Pas de sélection faite !\nIl faut choisir ou cliquer sur annuler", u"Accord Impossible", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.EndModal(wx.ID_OK)

    def OnDblClic(self, event):
        self.choix = self.listview.GetSelectedObject()
        self.EndModal(wx.ID_OK)

    def GetChoix(self):
        self.choix = self.listview.GetSelectedObject()
        return self.choix

if __name__ == u"__main__":

    app = wx.App(0)
    import os
    os.chdir("..")
    os.chdir("..")
    #dialog_3 = DialogLettrage(None,{12456:[u"choïx 1",15]},[u"libellé1",u"Montant"],{6545:[u"éssai",50,25]},[u"libellé2",u"libellé1","montant"],[(12456,None),])
    dialog_3 = DialogCoches(None,)
    app.SetTopWindow(dialog_3)
    print(dialog_3.ShowModal())
    print(dialog_3.choix)
    del dialog_3
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    print(dialog_1.ShowModal())
    print(dialog_1.GetChoix())
    del dialog_1
    dialog_2 = DialogCoches(None,listeOriginale=["choix1","text1","suite1","choix2","text2","suite2"])
    app.SetTopWindow(dialog_2)
    print(dialog_2.ShowModal())
    print(dialog_2.choix)
    del dialog_2
    app.MainLoop()
