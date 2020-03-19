#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Matthania
# Auteur:          Jacques Brunel, janvier 2020
# Licence:         Licence GNU GPL
# Permet une saisie d'adresse Noethys
#------------------------------------------------------------------------

import wx
import xpy.outils.xbandeau      as xbd
import srcNoelite.DLG_Villes    as ndv
import srcNoelite.UTILS_SaisieAdresse as usa
import xpy.outils.xchoixListe   as xcl


class CTRL_Bouton_image(wx.Button):
    def __init__(self, parent, id=wx.ID_APPLY, texte="", cheminImage=None):
        wx.Button.__init__(self, parent, id=id, label=texte)
        if cheminImage:
            self.SetBitmap(wx.Bitmap(cheminImage))
        self.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.SetInitialSize()

class CTRL_champ(wx.Panel):
    # Gestion d'une ligne de l'adresse; composée de label, bouton et ctrl
    def __init__(self,parent,nom,label,aide="",valdef="",choices=[""],btntip=u"Gestion",btnonclic=None):
        wx.Panel.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.choices = choices
        self.label = wx.StaticText(self, -1, label + u" :", style=wx.ALIGN_RIGHT,size=(140,20))
        if nom == "ville":
            self.ctrl = wx.ComboBox(self,-1,value=valdef,choices=choices,style=wx.TE_PROCESS_ENTER)
            self.ctrl.SetSelection(0)
            self.ctrl.Bind(wx.EVT_COMBOBOX,self.parent.OnChoixVille)
            self.bouton = wx.Button(self, -1, "...", size=(20, 20))
            self.bouton.SetToolTip(btntip)
            self.bouton.Bind(wx.EVT_BUTTON, btnonclic)
        elif nom in ("forcer"):
            self.ctrl = wx.CheckBox(self, -1)
        else:
            self.ctrl = wx.TextCtrl(self, -1, valdef,style=wx.TE_PROCESS_ENTER, size=(230,20))
            self.ctrl.SetMaxLength(38)
        self.ctrl.Bind(wx.EVT_TEXT_ENTER, self.parent.OnKeyEnter)
        self.ctrl.Bind(wx.EVT_KILL_FOCUS, self.parent.OnKillFocusChamp)
        self.ctrl.nom = nom
        self.label.SetToolTip(aide)
        self.ctrl.SetToolTip(aide)
        if nom in ('pays','forcer'):
            self.ctrl.Enable(False)

        self.__do_layout()

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=1, cols=3, vgap=0, hgap=0)
        gridsizer_base.Add(self.label, 1, wx.ALIGN_CENTRE_VERTICAL| wx.ALIGN_RIGHT | wx.TOP|wx.RIGHT, 5)
        if self.ctrl.nom in ("ville"):
            gridsizer_base.Add(self.bouton, 0, wx.ALIGN_CENTRE_VERTICAL| wx.ALIGN_RIGHT | wx.TOP|wx.RIGHT, 5)
        else:
            gridsizer_base.Add((10,10), 0, wx.TOP | wx.RIGHT, 5)
        gridsizer_base.Add(self.ctrl, 1, wx.ALIGN_CENTRE_VERTICAL| wx.ALIGN_RIGHT | wx.TOP| wx.RIGHT | wx.EXPAND, 5)
        gridsizer_base.AddGrowableCol(2)
        gridsizer_base.AddGrowableRow(0)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        self.Layout()

class PnlAdresse(wx.Panel):
    # Gestion des lignes composant l'adresse
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, style=wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.lstCpVillesPays = []
        self.oldCp = ""
        self.oldVille = ""
        self.goEvent = True
        lstLignes = [
            ['appart',  u"Appart,Esc,Etage|Service",
             u"Réservé au numéro de l'appartement, escalier ou étage\nPour une administration le nom du service est accepté"],
            ['batiment',u"Bâtiment, Résidence", u"Un numéro une lettre doivent être précédés de BATIMENT, zone optionnelle"],
            ['rue',     u"No et nom de rue",   u"Aucun caractère spécial ou ponctuation n'est accepté", u"Obligatoire"],
            ['bp',      u"BP, CS, TSA, lieu dit",     u"Uniquement pour préciser une distribution spéciale ou un lieu dit"],
            ['cp', u"Code Postal", u"Saisir le début du code postal", u"Obligatoire"],
            ['ville', u"Ville", u"Choix de la ville ou gestion par '...'", u"Obligatoire",["Choisir..."],
            u"Gestion des villes et des codes postaux",self.OnClicVille],
            ['pays', u"Pays étranger",
                    u"Seulement pour l'étranger, à blanc pour le pays national\nGestion des pays par les villes", u"",],
            ['forcer', u"Forcer la saisie", u"Permet de passer outre les contrôles de sortie, procédure exceptionnelle!", ],
        ]
        self.lstCtrl = []
        self.lstNomsChamps = []
        for ligne in lstLignes:
            self.lstCtrl.append(CTRL_champ(self,*ligne))
            self.lstNomsChamps.append(ligne[0])
        self.__do_layout()

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=len(self.lstCtrl), cols=1, vgap=0, hgap=0)
        for ligne in self.lstCtrl:
            gridsizer_base.Add(ligne, 1, wx.ALL | wx.EXPAND, 5)

        gridsizer_base.AddGrowableCol(0)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        self.Layout()

    def MAJ(self):
        self.__do_layout()

    def SetVilles(self):
        # pose les choices pour ville et pays
        self.oldVille = self.lstCtrl[self.lstNomsChamps.index("ville")].ctrl.GetValue()
        self.oldPays = self.lstCtrl[self.lstNomsChamps.index("pays")].ctrl.GetValue()
        if len(self.lstCpVillesPays)>0:
            self.lstVilles = []
            self.lstPays = []
            for cp,ville,pays in self.lstCpVillesPays:
                self.lstVilles.append(ville.upper())
                self.lstPays.append(pays.upper())
            ville = self.lstVilles[0]
            if self.oldVille.upper() in self.lstVilles:
                ville = self.oldVille
            self.SetChoices("ville",self.lstVilles)
            self.SetValue("ville",self.lstVilles[self.lstVilles.index(ville)])
            self.SetValue("pays",self.lstPays[self.lstVilles.index(ville)])
        else:
            self.SetValue("ville",u"Gérer la ville")

    def GetVillesDuCp(self,filtrecp):
        # Appelle les villes et pays du code postal et prépare les listes des choices
        self.lstCpVillesPays = usa.GetVilles("cp",filtrecp)
        lstNomsVilles = []
        lstCp = []
        lstCpChoix = []
        self.lstPays = []
        for cp, ville, pays in self.lstCpVillesPays:
            lstNomsVilles.append(ville)
            if cp not in lstCp:
                lstCp.append(cp)
                if len(pays)>0:
                    txt = u" en " + pays
                else: txt = u""
                lstCpChoix.append([cp,ville + txt])
            else:
                lstCpChoix[lstCp.index(cp)][1]+= u"," + ville
            if ville not in lstNomsVilles:
                lstNomsVilles.append(ville)
            if pays not in self.lstPays:
                self.lstPays.append(pays)
        if len(lstCp)>1:
            # le cp saisi est ambigu, plusieurs réponses
            dlg = xcl.Dialog(self,listeOriginale=lstCpChoix,LargeurCode=180,titre=u"Précisez le code postal",
                                          intro=u"Sinon allez choisir le champ du nom de la ville")
            ret = dlg.ShowModal()
            if ret == wx.ID_OK:
                choix = dlg.GetChoix()[0]
                self.oldCp = choix
                self.SetValue("cp",choix)
                # Relance sur le code postal pour alimenter correctement la liste des villes et sortie par elif suivant
                ret = self.GetVillesDuCp(choix)
            dlg.Destroy()
            return ret
        elif len(lstCp) == 1:
            self.oldCp = lstCp[0]
            self.SetValue("cp", lstCp[0])
            return wx.ID_OK
        else:
            wx.MessageBox(u"Code postal inconnu\n\nPassez par la gestion des villes pour le créer")
            return wx.ID_ABORT

    def GetVilleDuNom(self,ville):
        # Appelle les villes correspondant au nom partiellement fourni
        self.lstCpVillesPays = usa.GetVilles("ville",ville)
        lstChoix = []
        self.lstVilles = []
        lstCp = []
        self.lstPays = []
        for cp, ville, pays in self.lstCpVillesPays:
            lstChoix.append((ville, cp +u"\t        " +  pays))
            lstCp.append(cp)
            self.lstVilles.append(ville)
            self.lstPays.append(pays)
        if len(lstChoix)>1:
            # la ville  saisie est ambigue ou plusieurs occurences de la ville
            dlg = xcl.DialogAffiche(self,listeOriginale=lstChoix,LargeurCode=180,titre=u"Précisez la ville",
                                          intro=u"Sinon allez choisir la ville par '...'")
            ret = dlg.ShowModal()
            if ret == wx.ID_OK:
                ix = lstChoix.index(dlg.GetChoix())
                ville = self.lstVilles[ix]
                self.SetValue("ville",ville)
                self.SetValue("cp", lstCp[ix])
                self.SetValue("pays", self.lstPays[ix])
                self.GetVillesDuCp()
            dlg.Destroy()

    def SetAdresse(self,adresse=[]):
        # met l'adresse en sept lignes, dans les champs de saisie
        if len(adresse) != 7:
            mess = u"PnlAdresse.SetAdresse: Adresse n'ayant pas 7 lignes!\n\n%s"%str(adresse)
            wx.MessageBox(mess)
            return
        for ix in range(7):
            self.lstCtrl[ix].ctrl.SetValue(adresse[ix])
        cp = self.lstCtrl[self.lstNomsChamps.index("cp")].ctrl.GetValue()
        self.lstCpVillesPays = usa.GetVilles("cp", cp)
        self.lstVilles= [vil for cp,vil,pays in self.lstCpVillesPays]
        self.lstPays= [pays for cp,vil,pays in self.lstCpVillesPays]
        self.SetChoices("ville", self.lstVilles)
        return

    def GetAdresse(self):
        # retourne l'adresse saisie dans les champs
        adresse = []
        for ix in range(7):
            adresse.append(self.lstCtrl[ix].ctrl.GetValue())
        return adresse

    #Gestion de la sortie du code postal
    def OnKillFocusChamp(self,event):
        # Gestion de la sortie de certains champs
        if event.EventObject.nom == "cp" and self.goEvent:
            self.goEvent = False
            cp = self.lstCtrl[self.lstNomsChamps.index("cp")].ctrl.Value
            if self.oldCp != cp and len(cp)>1:
                # Le code postal a été modifié, recherche des villes associées
                ret = self.GetVillesDuCp(cp)
                if ret == wx.ID_OK:
                    self.SetVilles()
        elif event.EventObject.nom == "ville" and self.goEvent:
            self.goEvent = False
            ville = self.lstCtrl[self.lstNomsChamps.index("ville")].ctrl.Value
            if self.oldVille != ville and len(ville) > 1:
                # Le code postal a été modifié, recherche des villes associées
                ret = self.GetVilleDuNom(ville)
            self.goEvent = True
        event.Skip()

    def OnKeyEnter(self,event):
        if event.EventObject.nom in ("cp","ville","pays"):
            self.OnKillFocusChamp(event)
            event.Skip()
            return
        ix = self.lstNomsChamps.index(event.EventObject.nom) +1
        self.lstCtrl[ix].ctrl.SetFocus()
        event.Skip()

    def OnChoixVille(self,event):
        ix = self.lstNomsChamps.index("ville")
        ville = self.lstCtrl[ix].ctrl.GetValue()
        self.SetValue("pays", self.lstPays[self.lstVilles.index(ville)])
        self.SetValue("ville",ville)
        self.lstCtrl[0].ctrl.SetFocus()
        event.Skip()

    def OnClicVille(self,event):
        dlg = ndv.Dialog(None, modeImportation=True)
        if dlg.ShowModal() == wx.ID_OK:
            cp, ville, pays = dlg.GetVille()
            self.SetValue("cp",cp)
            self.SetValue("ville",ville)
            self.SetValue("pays", pays)
        dlg.Destroy()
        event.Skip()

    def SetValue(self,champ,valeur):
        # SetValue de 'valeur' sur le ctrl de la ligne nommée par 'champ'
        ixChamp = self.lstNomsChamps.index(champ)
        self.lstCtrl[ixChamp].ctrl.SetValue(valeur)

    def SetString(self,champ,valeur):
        # SetValue de 'valeur' sur le ctrl de la ligne nommée par 'champ'
        ixChamp = self.lstNomsChamps.index(champ)
        self.lstCtrl[ixChamp].ctrl.SetValue(valeur)

    def SetChoices(self,champ,lstval,pos=0):
        # SetChoices de 'valeur' sur le wx.Choice de la ligne nommée par 'champ'
        ixChamp = self.lstNomsChamps.index(champ)
        self.lstCtrl[ixChamp].ctrl.Set(lstval)

class DlgSaisieAdresse(wx.Dialog):
    # Gestion de l'adresse dans sa fenêtre
    def __init__(self,IDindividu,LargeurCode=180,LargeurLib=100,minSize=(180, 350),titre=u"Saisie d'une adresse normalisée",
                 intro=u"Lignes limitées à 38 caractères"):
        wx.Dialog.__init__(self, None, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.SetTitle("aDLG_SaisieAdresse")
        self.choix= None
        self.IDindividu = IDindividu
        self.minSize = minSize
        self.wCode = LargeurCode
        self.wLib = LargeurLib
        self.liste = []
        # Bandeau
        self.ctrl_bandeau = xbd.Bandeau(self, titre=titre, texte=intro,  hauteur=15, nomImage="xpy/Images/32x32/Matth.png")
        # conteneur des données
        self.panelAdresse = PnlAdresse(self)
        self.lstCtrl = self.panelAdresse.lstCtrl
        self.lstNomsChamps = self.panelAdresse.lstNomsChamps

        self.lstAdresse, self.IDindividuLu,(nom,prenom) = usa.GetDBadresse(self.IDindividu,retNom=True)
        if self.IDindividu == self.IDindividuLu:
            self.panelAdresse.SetAdresse(self.lstAdresse)
        else:
            mess = "Cette personne avait l'adresse de %s %s\n\nVoulez-vous lui créer une adresse personnelle?"%(prenom,nom)
            mess += "\nSinon changez l'adresse de l'individu %s"%self.IDindividuLu
            ret = wx.MessageBox(mess,"Pas d'adresse personnelle",style=wx.YES_NO|wx.CENTER)
            if ret != wx.YES:
                self.Destroy()

        # Boutons
        self.bouton_remonte = CTRL_Bouton_image(self, texte=u"Remonte\nex adr.", cheminImage="xpy/Images/32x32/Actualiser.png",)
        self.bouton_ok = CTRL_Bouton_image(self, texte=u"Valider", cheminImage="xpy/Images/32x32/Valider.png")
        self.bouton_fermer = CTRL_Bouton_image(self, texte=u"Abandon", cheminImage="xpy/Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetMinSize(self.minSize)
        self.bouton_remonte.SetToolTip(u"Cliquez ici pour remonter la première saisie")
        self.bouton_fermer.SetToolTip(u"Cliquez ici pour abandonner la saisie")
        self.bouton_ok.SetToolTip(u"Cliquez ici pour enregistrer les modifications")
        # Binds
        self.bouton_remonte.Bind(wx.EVT_BUTTON, self.OnClicRemonte)
        self.bouton_ok.Bind(wx.EVT_BUTTON, self.OnClicOk)
        self.bouton_fermer.Bind(wx.EVT_BUTTON, self.OnClicFermer)

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)
        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        gridsizer_base.Add(self.panelAdresse, 1, wx.LEFT|wx.EXPAND, 10)
        gridsizer_base.Add((5, 5), 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)

        # Boutons
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=0, hgap=0)
        gridsizer_boutons.Add(self.bouton_remonte, 0, wx.EXPAND, 0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_fermer, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_ok, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(1)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnClicRemonte(self, event):
        self.lstAdresse = usa.GetDBoldAdresse(IDindividu=self.IDindividu)
        if not self.lstAdresse :
            wx.MessageBox(u"Pas d'adresse antérieure stockée!")
        else:
            self.panelAdresse.SetAdresse(self.lstAdresse)
            self.panelAdresse.MAJ()
        event.Skip()

    def OnClicFermer(self, event):
        # Abandon
        if event : event.Skip()
        self.EndModal(wx.ID_CANCEL)

    def OnClicOk(self, event):
        saisie = self.panelAdresse.GetAdresse()
        self.lstAdresse = usa.TransposeAdresse(saisie)
        nonmodifiee=True
        for i in range(len(saisie)):
            if saisie[i].upper() != self.lstAdresse[i].upper():
                nonmodifiee = False
        forcer = self.lstCtrl[self.lstNomsChamps.index("forcer")].ctrl.Value
        validee = False
        if not forcer:
            mess = usa.Validation(self.lstAdresse)
            if mess == wx.ID_OK:
                validee = True

        self.lstCtrl[self.lstNomsChamps.index("forcer")].ctrl.Enable(True)
        self.panelAdresse.SetAdresse(self.lstAdresse)
        self.panelAdresse.MAJ()
        def enregistre():
            # Enregistrement de l'adresse et sortie
            ret = usa.SetDBadresse(None,self.IDindividu,self.lstAdresse)
            if ret != "ok":
                wx.MessageBox(self, u"Pas d'écriture possible !\nAbandon de la modification\n%s"%ret)
                self.EndModal(wx.ID_ABORT)
            else:
                # archive cette adresse s'il n'y en a pas d'autre
                exadresse = usa.GetDBoldAdresse(self.IDindividu)
                if not exadresse:
                    ret = usa.SetDBoldAdresse(None,self.IDindividu, self.lstAdresse)
                self.EndModal(wx.ID_OK)

        if (validee and nonmodifiee) or forcer:
            enregistre()
        elif validee:
            self.panelAdresse.SetAdresse(self.lstAdresse)
            wx.MessageBox(u"L'adresse vient d'être reformatée !\nValidez à nouveau pour confirmer")
        elif nonmodifiee:
            wx.MessageBox(mess+"\n\nPour sortir quand même sans abandonner, vous pouvez cocher la case 'Forcer la saisie'")
        event.Skip()

if __name__ == u"__main__":
    app = wx.App(0)
    import os
    os.chdir("..")
    dlg = wx.Frame(None)
    dlg.individu = 15977
    dlg2 = DlgSaisieAdresse(dlg.individu, titre=u"Adresse de %d"%dlg.individu)
    dlg2.ShowModal()
    app.MainLoop()
