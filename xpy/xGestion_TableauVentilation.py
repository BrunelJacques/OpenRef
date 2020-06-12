#!/usr/bin/python3
# -*- coding: utf-8 -*-

#  Jacques Brunel x Sébastien Gouast
#  MATTHANIA - évolution xGestion_Tableau.py ne reçoit pas les données mais une requête avec filtre qui s'actualise
#  2020/06/02

import wx
import os
import xpy.xGestion_TableauRecherche as xgtr
from xpy.outils.ObjectListView import FastObjectListView, ColumnDefn,CellEditor,OLVEvent
from xpy.outils import xformat

# ------------------------------------------------------------------------------------------------------------------

class PNL_pied(wx.Panel):
    def __init__(self, parent,**kwds):
        name = kwds.pop('name',"pnlPied")
        style = kwds.pop('style',wx.BORDER_NONE)
        montant = kwds.pop('montant',0.0)
        size = kwds.pop('size',(500, 35))
        sizeFont = kwds.pop('sizeFont',11)
        self.formate = kwds.pop('format',xformat.FmtMontant)
        self.SetBgColour = kwds.pop('format',xformat.SetBgColour)
        self.tooltip = kwds.pop('tooltip',"Montant du solde à affecter")
        self.couleurFond = wx.Colour(220,230,240)

        wx.Panel.__init__(self, parent, id=-1, name=name,style=style)
        self.SetBackgroundColour(self.couleurFond)


        # Montant
        self.txtMontant = wx.StaticText(self, wx.ID_ANY,"Règlement:",size=(80,20),style=wx.ALIGN_CENTER_HORIZONTAL)
        self.ctrlMontant = wx.StaticText(self, -1,self.formate(montant),size=(80,20),style=wx.ALIGN_LEFT|wx.BORDER_NONE)
        fontmtt = wx.Font(sizeFont-1, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,False)
        for txt in (self.txtMontant, self.ctrlMontant):
            txt.SetFont(fontmtt)
        # Solde
        self.txtSolde = wx.StaticText(self, wx.ID_ANY,"",style=wx.ALIGN_CENTER_HORIZONTAL)
        self.ctrlSolde = wx.StaticText(self, -1,"",style=wx.ALIGN_RIGHT|wx.BORDER_SIMPLE)
        fontsld = wx.Font(sizeFont, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,False)
        for txt in (self.txtSolde,self.ctrlSolde):
            txt.SetFont(fontsld)
            txt.SetToolTip(self.tooltip)

        # Layout
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=5, vgap=5, hgap=0)
        grid_sizer_base.Add(self.txtMontant, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 3)
        grid_sizer_base.Add(self.ctrlMontant, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER | wx.ALL, 3)
        grid_sizer_base.Add((10,45), 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER | wx.ALL, 3)
        grid_sizer_base.Add(self.txtSolde, 1, wx.ALIGN_CENTER | wx.ALL, 3)
        grid_sizer_base.Add(self.ctrlSolde, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 3)
        self.SetSizerAndFit(grid_sizer_base)

    def SetSolde(self, montant=0.0):
        """ MAJ integrale du controle avec MAJ des donnees """
        self.ctrlSolde.SetLabel(self.formate(montant))
        xformat.SetBgColour(self.ctrlSolde, montant)
        if montant == 0.0:
            self.txtSolde.SetLabel("Totalement affecté!")
            self.txtSolde.SetMinSize((200,20))
            self.ctrlSolde.SetMaxSize((0,20))
            xformat.SetBgColour(self.txtSolde, montant)
        else:
            self.txtSolde.SetLabel("Reste à affecter:")
            self.txtSolde.SetBackgroundColour(self.couleurFond)
            self.txtSolde.SetMinSize((115,20))
            self.ctrlSolde.SetMinSize((90,20))

        self.Refresh()

# ------------------------------------------------------------------------------------------------------------------

class PNL_tableau(xgtr.PNL_tableau):
    def __init__(self, parent, dicOlv,*args, **kwds):
        self.montant = kwds.pop('montant',1)
        self.solde = self.montant
        dicOlv['recherche'] = False
        dicOlv['cellEditMode'] = FastObjectListView.CELLEDIT_SINGLECLICK
        dicOlv['style'] =  wx.LC_REPORT|wx.NO_BORDER|wx.LC_HRULES|wx.LC_VRULES| wx.LC_SINGLE_SEL
        xgtr.PNL_tableau.__init__(self, parent, dicOlv, *args,  **kwds)

        # spécificités pour ventilation
        self.flagSkipEdit = False
        self.pnlPied = PNL_pied(self,montant=self.montant)
        self.pnlPied.SetSolde(self.solde)
        self.ctrlOlv.CreateCheckStateColumn(0)
        self.ProprietesOlv()
        self.ctrlOlv.MAJ()
        self.Sizer()

    def ProprietesOlv(self):
        self.ctrlOlv.Bind(wx.EVT_CONTEXT_MENU, self.ctrlOlv.OnContextMenu)
        self.ctrlOlv.Bind(OLVEvent.EVT_CELL_EDIT_FINISHING,self.OnEditFinishing)
        #self.ctrlOlv.Bind(OLVEvent.EVT_CELL_EDIT_STARTED,self.OnEditStarted)

    def SetVentilation(self):
        # Recalcule la répartition
        pass

    def OnEditFinishing(self,event):
        if self.flagSkipEdit : return
        self.flagSkipEdit = True
        # gestion des actions de sortie
        row, col = self.ctrlOlv.cellBeingEdited
        if self.ctrlOlv.checkStateColumn:
            col -= 1
        track = self.ctrlOlv.GetObjectAt(row)
        new_data = self.ctrlOlv.cellEditor.GetValue()
        code = self.ctrlOlv.lstCodesColonnes[col]
        # appel des éventuels spécifiques cf xGestion_TableauEditor
        if hasattr(self.Parent, 'OnEditFinishing'):
            self.parent.OnEditFinishing(code,new_data)
        # stockage de la nouvelle saisie
        track.__setattr__(code, new_data)
        track.donnees[col] = new_data
        self.SetVentilation()
        event.Skip()
        self.flagSkipEdit = False

class DLG_tableau(xgtr.DLG_tableau):
    # minimum fonctionnel dans dialog tout est dans pnl
    def __init__(self,parent,dicOlv={}, **kwds):
        dicOlv['pnlTableau'] = PNL_tableau
        xgtr.DLG_tableau.__init__(self,parent,dicOlv)

# -- pour tests -----------------------------------------------------------------------------------------------------

def GetDonnees(matrice,filtre = ""):
    donnees = [
                [None,wx.DateTime.FromDMY(15, 11, 2018),'2019-04-09',"Bonjour", -1230.05939, -1230.05939, 0.0,],
                [None, wx.DateTime.FromDMY(18, 3, 2019), '20/06/2019', "jourwin", 12045.039, 1293.9, 0.0, ],
                [None, wx.DateTime.FromDMY(18, 3, 2019), '2019-06-20', "sqljourbon", None, 1293.9, 125.65, ],
                [None, wx.DateTime.FromDMY(1, 5, 2018), '2019-05-30', "bye", 25.1, 25.1, 0.0, ],
    ]
    donneesFiltrees = [x for x in donnees if filtre.upper() in x[3].upper() ]
    return donneesFiltrees

liste_Colonnes = [
    ColumnDefn("clé", 'left', 60, "zero",valueSetter=1,isSpaceFilling =False,isEditable=False),
    ColumnDefn("date", 'center', 80, "date",valueSetter=wx.DateTime.FromDMY(1,0,1900),isSpaceFilling = True,
               stringConverter=xformat.FmtDate,isEditable=False),
    ColumnDefn("date SQL", 'center', 80, "datesql", valueSetter='2000-01-01',isSpaceFilling = True,
               stringConverter=xformat.FmtDate,isEditable=False),
    ColumnDefn("mot d'ici", 'left', 200, "mot",valueSetter=0.0,
               stringConverter=xformat.FmtMontant,isEditable=False,),
    ColumnDefn("montant", 'right', 80, "montant", valueSetter=0,isSpaceFilling=True,
               stringConverter=xformat.FmtMontant,isEditable=False,),
    ColumnDefn("à régler", 'right', 80, "reste",valueSetter=0.0,isSpaceFilling=True,
               stringConverter=xformat.FmtMontant,isEditable=False),
    ColumnDefn("Affecté", 'right', 80, "affecte", valueSetter=0.0, isSpaceFilling=True,
               stringConverter=xformat.FmtMontant,cellEditorCreator=CellEditor.FloatEditor),
    ]
dicOlv = {'listeColonnes':liste_Colonnes,
                'getDonnees':GetDonnees,
                'hauteur':650,
                'largeur':850,
                'msgIfEmpty':"Aucune donnée ne correspond à votre recherche",
        }

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    dicBandeau = {'titre':"Ma Ventilation", 'texte':"mon introduction", 'hauteur':15, 'nomImage':"xpy/Images/32x32/Matth.png"}
    dicOlv['dicBandeau'] = dicBandeau
    exempleframe = DLG_tableau(None,dicOlv=dicOlv,lstBtns= None)
    app.SetTopWindow(exempleframe)
    ret = exempleframe.ShowModal()
    if exempleframe.GetSelection():
        print(exempleframe.GetSelection().donnees)
    else: print(None)
    app.MainLoop()
