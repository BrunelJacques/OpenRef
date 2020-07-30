#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import wx
import wx.html as html
import datetime

COULEUR_FOND = wx.Colour(96,73,123)

class CTRL_html(html.HtmlWindow):
    def __init__(self, parent):
        html.HtmlWindow.__init__(self, parent, -1, style=wx.html.HW_NO_SELECTION | wx.html.HW_SCROLLBAR_NEVER )
        self.parent = parent
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()
        self.SetBorders(0)
        self.SetMinSize((368, 30))
        self.SetTexte()
    
    def SetTexte(self, texte="test"):
        try :
            self.SetPage("""<BODY'><FONT SIZE=20>%s</FONT></BODY>""" % texte)
            self.SetBackgroundColour(wx.Colour(196,173,223))
        except :
            pass

class Panel_Titre(wx.Panel):
    def __init__(self, parent, size=(1500, 145),pos=(0,0),image="xpy/Images/Globe.ico",posImage=(20, 10),
                 texte="monAppli...",posLabel=(160, 40),tailleFont=18,couleurFond=None):
        wx.Panel.__init__(self, parent, name="panel_titre", id=-1, size=size, pos=pos, style=wx.TAB_TRAVERSAL)
        
        self.image_titre = wx.StaticBitmap(self, -1, wx.Bitmap(image, wx.BITMAP_TYPE_ANY), pos=posImage)
        if not couleurFond: couleurFond = COULEUR_FOND
        self.SetForegroundColour(couleurFond)
        self.label = wx.StaticText(self, -1, texte, pos=posLabel)
        self.label.SetFont(wx.Font(tailleFont, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))

class Panel_Buttons(wx.Panel):
    def __init__(self, parent,lstButtons=[], size=(-1, -1),tailleFont=18,couleurFond=None,
                 sizeBtn=(80,80)):
        wx.Panel.__init__(self, parent, name="panel_accueil", id=-1, size=size, style=wx.TAB_TRAVERSAL)

        self.image_gauche_haut = wx.StaticBitmap(self, -1, wx.Bitmap("xpy/Images/Noethys.png", wx.BITMAP_TYPE_PNG))
        self.image_gauche_bas = wx.StaticBitmap(self, -1, wx.Bitmap("xpy/Images/Noethys.png", wx.BITMAP_TYPE_PNG))
        self.image_droit_bas = wx.StaticBitmap(self, -1, wx.Bitmap("xpy/Images/Noethys.png", wx.BITMAP_TYPE_PNG))

        # self.bouton = wx.Button(self.topPanel,-1,label = "action",pos=(100,300),size=sizeBtn)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetBackgroundColour(COULEUR_FOND)

    def __do_layout(self):
        grid_sizer = wx.FlexGridSizer(rows=1, cols=3, vgap=30, hgap=30)
        #grid_sizer.Add((1, 1), 0, wx.EXPAND, 0)
        grid_sizer.Add(self.image_gauche_bas, 1, wx.ALL, 40)
        grid_sizer.Add(self.image_gauche_haut, 1, wx.ALL, 0)
        grid_sizer.Add(self.image_droit_bas, 1, wx.ALL, 20)
        self.SetSizer(grid_sizer)
        grid_sizer.AddGrowableRow(0)
        grid_sizer.AddGrowableCol(0)

class Panel_General(wx.Panel):
    def __init__(self, parent,size=(-1, -1),lstButtons = None):
        wx.Panel.__init__(self, parent, name="panel_general", id=-1, size=size, style=wx.TAB_TRAVERSAL)
        self.SetForegroundColour(COULEUR_FOND)
        self.image_titre = Panel_Titre(self)
        self.ctrl= Panel_Buttons(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.image_titre, 0, wx.EXPAND, 0)
        if lstButtons:
            sizer.Add(self.ctrl, 1, wx.ALIGN_TOP|wx.ALL, 0)
        self.SetSizer(sizer)
        self.Layout()

# -------------------------- pour tests -------------------------------------------------------------------------------
class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        lstButtons = [
            {"code": "modifAdresses", "label": ("&Modification d'adresses Individus\tCtrl-I"),
             "infobulle": (u"Gestion de l'adresses de rattachement des personnes (soit la leur soit celle de leur hébergeur"),
             "image": "Images/16x16/Editeur_email.png",
             "action": "On_Adresses_individus", "genre": wx.ITEM_NORMAL},
            {"code": "modifAdressesF", "label": ("&Modification d'adresses Familles\tCtrl-F"),
             "infobulle": (u"Gestion des adresses des familles, mais pas de tous les individus de la famille"),
             "image": "Images/16x16/Editeur_email.png",
             "action": "On_Adresses_familles", "genre": wx.ITEM_NORMAL},
            "-",
            {"code": "gestionReglements", "label": ("&Gestion des règlements\tCtrl-R"),
             "infobulle": (u"Gestion de bordereau de règlements : remise de chèques, arrivée de virements, de dons..."),
             "image": "Images/16x16/Impayes.png",
             "action": "On_reglements_bordereau", "genre": wx.ITEM_NORMAL},
        ]
        panel = Panel_General(self,lstButtons=lstButtons)
        self.SetSize((1200, 700))

if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    os.chdir("..")
    frame_1 = MyFrame(None, -1, "TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()