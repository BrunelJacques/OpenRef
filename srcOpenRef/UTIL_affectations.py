#!/usr/bin/env python
# -*- coding: utf8 -*-

#------------------------------------------------------------------------
# Application :    OpenRef, Gestion des affectations
# Auteurs:          Jacques BRUNEL
# Copyright:       (c) 2019-05     Cerfrance Provence
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import datetime
import srcOpenRef.UTIL_analyses as orua
import srcOpenRef.UTIL_traitements as orut
import srcOpenRef.DATA_Tables as dtt
import xpy.xGestionDB as xdb
import xpy.xUTILS_SaisieParams as xusp
import xpy.xGestion_Tableau as xgt
import xpy.outils.xformat as xfmt

def ComposeLstDonnees(lstNomsColonnes,record,lstChamps):
    # Extrait une liste de donnees d'un record selon une sous liste de champs
    lstdonnees=[]
    for nom in lstNomsColonnes:
        ix = lstChamps.index(nom)
        lstdonnees.append(record[ix])
    return lstdonnees

def ValeursDefaut(lstNomsColonnes,lstChamps,lstTypes):
    # Détermine des valeurs par défaut selon le type des variables
    lstValDef = []
    for colonne in lstNomsColonnes:
        tip = lstTypes[lstChamps.index(colonne)]
        if tip[:3] == 'int': lstValDef.append(0)
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

def VerifSelection(parent,dlg,infos=True):
    # contrôle la selection d'une ligne, puis marque le no dossier et eventuellement texte infos à afficher
    if len(dlg.ctrlOlv.Selection())==0:
        wx.MessageBox("Action Impossible\n\nVous n'avez pas selectionné une ligne!","Préalable requis")
        return False
    parent.ixsel = parent.ctrlolv.donnees.index(parent.ctrlolv.Selection()[0])
    if infos:
        noclient = dlg.ctrlOlv.Selection()[0].noclient
        cloture = dlg.ctrlOlv.Selection()[0].cloture
        nomexploitation = dlg.ctrlOlv.Selection()[0].nomexploitation
        parent.infos = 'Dossier: %s, %s, %s'%(noclient,cloture,nomexploitation)
    return True

class EcranSaisie():
    # affichage d'une ligne en vue de modif, toutes les colonnes ne sont pas reprises
    def __init__(self,parent,ctrlolv,mode,selection,ixsel,cdCateg,nmCateg,pos,minSize,dicOptions,table,wherecle):
        lstCodes = ctrlolv.lstCodesColonnes[2:]
        dictMatrice = {}
        dictDonnees = {}
        donnees, lstNoms, lstHelp = [],[],[]
        for code in lstCodes:
            ixolv = ctrlolv.lstCodesColonnes.index(code)
            donnees.append(selection.donnees[ixolv])
            lstNoms.append(ctrlolv.lstNomsColonnes[ixolv])
            ixtbl = ctrlolv.lstTblChamps.index(ctrlolv.lstNomsColonnes[ixolv])
            lstHelp.append(ctrlolv.lstTblHelp[ixtbl])

        # Lancement de l'écran
        (dictMatrice[(cdCateg,nmCateg)],dictDonnees['params']) \
            = xusp.ComposeMatrice('Compte','SoldeFin',lstNoms, lstHelp=lstHelp,record=donnees,dicOptions=dicOptions)
        dlg = xusp.DLG_monoLigne(parent,dldMatrice=dictMatrice,ddDonnees=dictDonnees,gestionProperty=False,
                                           pos=pos,minSize=minSize)
        ret = dlg.ShowModal()
        if ret == 5101:
            # Retour par validation
            valeurs = dlg.pnl.GetValeurs()
            # mise à jour de l'olv d'origine
            for code in ctrlolv.lstCodesColonnes:
                if code in lstCodes:
                    for categorie, dicDonnees in dlg.ddDonnees.items():
                        if code in dicDonnees:
                            ix = ctrlolv.lstCodesColonnes.index(code)
                            valorigine = selection.donnees[ix]
                            if valorigine != valeurs[categorie][code]:
                                if isinstance(valorigine,(str,datetime.date)):
                                    action = "selection.__setattr__('%s','%s')"%(
                                                ctrlolv.lstCodesColonnes[ix],str(valeurs[categorie][code]))
                                elif isinstance(valorigine, (int, float)):
                                    action = "selection.__setattr__('%s',%d)" % (
                                                ctrlolv.lstCodesColonnes[ix], float(valeurs[categorie][code]))
                                else: wx.MessageBox("%s, type non géré pour modifs: %s"%(code,type(valorigine)))
                                eval(action)
            ctrlolv.MAJ(ixsel)
            # mise à jour table de base de donnee
            lstModifs = []
            for categorie, dicdonnees in valeurs.items():
                for code,valeur in dicdonnees.items():
                    if valeur != None:
                        nom = lstNoms[lstCodes.index(code)]
                        lstModifs.append((nom,valeur))

            if len(lstModifs)>0 and mode == 'modif':
                ret = parent.DBsql.ReqMAJ(table,lstModifs,wherecle,mess='MAJ affectations.%s.Ecran'%table)
                if ret != 'ok':
                    wx.MessageBox(ret)
        parent.ctrlolv.SetFocus()
        parent.ctrlolv.SelectObject(parent.ctrlolv.donnees[ixsel])
        dlg.Destroy()

class Balance():
    def __init__(self,parent):
        self.title = '[UTIL_affectations].Balance'
        self.mess = ''
        self.clic = None
        self.parent = parent
        self.IDdossier = parent.IDdossier

        # pointeur de la base principale ( ouverture par défaut de db_prim via xGestionDB)
        self.DBsql = self.parent.DBsql
        self.retour = self.EcranBalance()

    def EcranBalance(self):
        # appel de la balance du dossier pour affichage
        req = """
                SELECT *
                FROM _Balances
                WHERE (IDdossier = %d) AND (LEFT(IDplanCompte,1) IN ('3','6','7'))
                ;"""%(self.IDdossier)
        retour = self.DBsql.ExecuterReq(req, mess='Util_affectations.EcranBalance')
        if retour == "ok":
            recordset = self.DBsql.ResultatReq()
            if len(recordset) == 0:
                retour = "aucun enregistrement disponible"
        if (not retour == "ok"):
            wx.MessageBox("Erreur : %s"%retour)
            return 'ko'
        lstChamps, lstTypes, lstHelp = dtt.GetChampsTypes('_Balances',tous=True)

        lstNomsColonnes =   xusp.ExtractList(lstChamps,champdeb='IDdossier',champfin='Compte')\
                            + xusp.ExtractList(lstChamps,champdeb='IDplanCompte',champfin='Affectation')\
                            + xusp.ExtractList(lstChamps,champdeb='Libellé',champfin='SoldeFin')
        lstCodesColonnes = [xusp.SupprimeAccents(x) for x in lstNomsColonnes]
        lstValDefColonnes = ValeursDefaut(lstNomsColonnes,lstChamps,lstTypes)
        lstLargeurColonnes = LargeursDefaut(lstNomsColonnes,lstChamps,lstTypes)

        # composition des données du tableau à partir du recordset
        lstDonnees = []
        for record in recordset:
            ligne = ComposeLstDonnees(lstNomsColonnes, record, lstChamps)
            lstDonnees.append(ligne)

        # matrice OLV
        lstColonnes = xusp.DefColonnes(lstNomsColonnes,lstCodesColonnes,lstValDefColonnes,lstLargeurColonnes)
        dicOlv = {
                'lanceur': self,
                'listeColonnes': lstColonnes,
                'listeDonnees': lstDonnees,
                'checkColonne': False,
                'hauteur': 650,
                'largeur': 1300,
                'recherche': True,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                'dictColFooter': {"nomexploitation": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                                }
                }

        # options d'enrichissement de l'écran
        lstBtns = [('BtnOK', wx.ID_OK, wx.Bitmap("xpy/Images/100x30/Bouton_fermer.png", wx.BITMAP_TYPE_ANY),
                    "Cliquez ici pour fermer la fenêtre")]
        # params d'actions: idem boutons, ce sont des boutons placés à droite et non en bas
        lstActions = [('modif',wx.ID_APPLY,'Modifier',"Cliquez ici pour modifier la ligne"),
                      ('eclater',wx.ID_APPLY,'Eclater',"Cliquez ici pour subdiviser le compte"),
                      ('regrouper', wx.ID_APPLY, 'Supprimer', "Supprimer la ligne et reporter le solde dessus"),
                      ]
        # un param par info: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = ["BALANCE -",self.parent.infos,]
        # params des actions ou boutons: name de l'objet, fonction ou texte à passer par eval()
        dicOnClick = {
                      'modif' : 'self.lanceur.OnModif()',
                      'eclater' : 'self.lanceur.OnEclater()',
                      'regrouper' : 'self.lanceur.OnRegrouper()'}
        self.dlgolv = xgt.DLG_tableau(self,dicOlv=dicOlv,lstBtns= lstBtns,lstActions=lstActions,lstInfos=lstInfos,
                                 dicOnClick=dicOnClick)

        #l'objet ctrlolv pourra être appelé, il sert de véhicule à params globaux de l'original
        self.ctrlolv = self.dlgolv.ctrlOlv
        self.ctrlolv.lstTblHelp = lstHelp
        self.ctrlolv.lstTblChamps = lstChamps
        self.ctrlolv.recordset = recordset
        if len(lstDonnees)>0:
            # selection de la première ligne
            self.ctrlolv.SelectObject(self.ctrlolv.donnees[0])
        ret = self.dlgolv.ShowModal()
        return ret

    def OnChildBtnAction(self,event):
        print('Bonjour Enter sur le bouton : ',event.EventObject.nameBtn)
        print( event.EventObject.labelBtn,)
        print('Action prévue : ',event.EventObject.actionBtn)

    def OnChildCtrlAction(self,event):
        print('Bonjour Enter sur le controle : ',event.EventObject.nameCtrl)
        print( event.EventObject.labelCtrl,)
        print('Action prévue : ',event.EventObject.actionCtrl)

    def OnModif(self):
        ctrlolv = self.ctrlolv
        all = ctrlolv.GetObjects()
        selection = ctrlolv.Selection()[0]
        ixsel = all.index(selection)
        if not VerifSelection(self,self.dlgolv,infos=False):
            return
        # Spécificités écran saisie
        table = '_Balances'
        IDenr = "IDligne"
        ID = ctrlolv.recordset[ixsel][ctrlolv.lstTblChamps.index(IDenr)]
        wherecle = "%s = %d" %(IDenr,ID)
        dicOptions = {'affectation':{
                        'genre': 'enum',
                                                'btnLabel': "...",
                        'btnHelp': "Cliquez pour ajouter des affectations à la liste",
                        'btnAction': 'OnNvlAffectation',},
                    'soldefin': {
                        'ctrlAction': 'OnYva',}}
        cdCateg = 'params'
        nmCateg = 'DétailLigne'
        pos = (300,0)
        minSize = (400,1000)
        EcranSaisie(self,self.ctrlolv,'modif',selection,ixsel,cdCateg,nmCateg,pos,minSize,dicOptions,table,wherecle)

    def OnEclater(self):
        if VerifSelection(self,self.dlgolv):
            ret = Balance(self)

    def OnRegrouper(self):
        if VerifSelection(self,self.dlgolv):
            ret = Balance(self)

class Affectations():
    def __init__(self,annee=None, client=None, groupe=None, filiere=None, agc='ANY'):
        self.title = '[UTIL_affectations].Affectations'
        self.mess = ''
        self.annee = annee
        self.clic = None
        # recherche pour affichage bas d'écran
        self.topwin = False
        self.topWindow = wx.GetApp().GetTopWindow()
        if self.topWindow:
            self.topwin = True

        # pointeur de la base principale ( ouverture par défaut de db_prim via xGestionDB)
        self.DBsql = xdb.DB()

        self.dic_Ateliers = {}
        #préchargement de la table des Produits et des coûts
        self.dicProduits, self.lstPrioritesProduits = orut.PrechargeProduits(agc,self.DBsql)

        self.dicCouts = orut.PrechargeCouts(agc,self.DBsql)
        self.dicPlanComp = orut.PrechargePlanCompte(self.DBsql)
        self.lstMotsClesProduits = orut.GetMotsCles(self.dicProduits, avectuple=True)
        self.lstMotsClesCouts = orut.GetMotsCles(self.dicCouts, avectuple=True)
        # détermination de la liste des clients présents, même ceux qui sont validés
        if client:
            self.lancement = "Dossiers du client: %s, année: %s"%(client,self.annee)
            self.lstDossiers = orua.GetExercicesClient(agc,client,self.annee,0,self.DBsql,saufvalide=False)
        elif groupe:
            self.lancement = "Dossiers du groupe: %s, année: %s"%(groupe,self.annee)
            self.lstDossiers=orua.GetClientsGroupes(agc, groupe, self.annee, 0, self.DBsql,saufvalide=False)
        elif filiere:
            self.lancement = "Dossiers de filière: %s, année: %s"%(filiere,self.annee)
            self.lstDossiers = orua.GetClientsFilieres(agc, filiere, self.annee, 0, self.DBsql,saufvalide=False)
        else :
            self.lancement = "Dossiers année: %s"%(self.annee)
            wx.MessageBox("Analyse : Aucun paramètre de lancement ne concerne un dossier")
            return
        if len(self.lstDossiers)==0:
            self.retour = "Aucun Dossier demandé n'a été importé"
            wx.MessageBox(self.retour)
        else:
            self.retour = self.EcranDossiers()

    def EcranDossiers(self):
        # appel des dossiers pour affichage
        lstClients = []
        for agc,client,cloture in self.lstDossiers:
            lstClients.append(client)

        # IDdossier,agc,exploitation,cloture,nomExploitation,nbreMois,fiscal,ventes,caNonAff,nbElemCar,elemCar,filieres,productions
        req = """
                SELECT _Ident.IDdossier, _Ident.IDagc, _Ident.IDexploitation, _Ident.Clôture, _Ident.NomExploitation, 
                _Ident.NbreMois, _Ident.Fiscal,Sum(_Balances.SoldeFin), Sum(((_Balances.affectation="") * _Balances.SoldeFin)),
                _Ident.NbElemCar,_Ident.ElemCar, _Ident.Filières, _Ident.Productions
                FROM _Ident 
                LEFT JOIN _Balances ON _Ident.IDdossier = _Balances.IDdossier
                WHERE (((Left(_Ident.Clôture,4)) = '%s')
                        AND (_Balances.Compte Like '70%%'))
                        AND (_Ident.IDexploitation In (%s))
                GROUP BY _Ident.IDdossier, IDagc, IDexploitation,Clôture, NomExploitation,
                        NbElemCar, ElemCar,Filières, NbreMois, Fiscal, Productions
                ;"""%(str(self.annee),str(lstClients)[1:-1])
        retour = self.DBsql.ExecuterReq(req, mess='Util_affectations.EcranDossiers')
        if retour == "ok":
            recordset = self.DBsql.ResultatReq()
            if len(recordset) == 0:
                retour = "aucun enregistrement disponible"
        if (not retour == "ok"):
            wx.MessageBox("Erreur : %s"%retour)
            return 'ko'
        lstNomsColonnes = ["ID","agc","Noclient","Clôture","nomExploitation","nbreMois","fiscal","ventes",
                           "%affecté","nbElem","Element","Vtes/Elem","filières","productions"]
        lstCodesColonnes = [xusp.SupprimeAccents(x) for x in lstNomsColonnes]

        lstValDefColonnes = [0,"","",datetime.date(1900,1,1),"",0,"",0.0,
                           0.0,0,"",0.0,"",""]
        lstLargeurColonnes = [0,-1,-1,70,120,-1,-1,-1,
                           -1,-1,50,-1,180,180]
        lstDonnees = []
        for IDdossier,IDagc,exploitation,cloture,nomExploitation,nbreMois,fiscal,ventes,caNonAff,nbElemCar,elemCar,filieres,\
            productions in recordset:
            affecT = round(100*(ventes-caNonAff)/ventes)
            if not nbElemCar : nbElemCar = 0.0
            if nbElemCar != 0.0:
                rendement = -ventes / nbElemCar
            else: rendement = 0.0
            dtcloture = xfmt.DateSqlToDatetime(cloture)
            lstDonnees.append([IDdossier,IDagc,exploitation,dtcloture,nomExploitation,nbreMois,fiscal,-ventes,affecT,
                               nbElemCar,elemCar,rendement,filieres,productions])

        messBasEcran = "Nbre de dossiers présents: %d "%len(lstDonnees)
        if self.topwin:
            self.topWindow.SetStatusText(messBasEcran)
        # matrice OLV
        lstColonnes = xusp.DefColonnes(lstNomsColonnes,lstCodesColonnes,lstValDefColonnes,lstLargeurColonnes)
        dicOlv = {
                'lanceur': self,
                'listeColonnes': lstColonnes,
                'listeDonnees': lstDonnees,
                'checkColonne': False,
                'hauteur': 650,
                'largeur': 1250,
                'recherche': True,
                'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                'dictColFooter': {"nomexploitation": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                                }
                }

        # options d'enrichissement de l'écran
        # params d'un bouton : name, ID, Image ou label, tooltip
        lstBtns = [('BtnOK', wx.ID_OK, wx.Bitmap("xpy/Images/100x30/Bouton_fermer.png", wx.BITMAP_TYPE_ANY),
                    "Cliquez ici pour fermer la fenêtre")]
        # params d'actions: idem boutons, ce sont des boutons placés à droite et non en bas
        lstActions = [('ident',wx.ID_APPLY,'Descriptif\ndossier',"Cliquez ici pour gérer l'identification"),
                      ('balance',wx.ID_APPLY,'Balance\nrésultats',"Cliquez ici pour affecter les comptes"),
                      ('ateliers',wx.ID_APPLY,'Ateliers\ndu dossier',"Cliquez ici pour les ateliers"),
                      ('produits',wx.ID_APPLY,'Produits\ndu dossier',"Cliquez ici pour gérer les produits"),]
        # un param par info: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = [self.lancement,]
        # params des actions ou boutons: name de l'objet, fonction ou texte à passer par eval()
        dicOnClick = {'ident' : 'self.lanceur.OnIdent()',
                      'balance' : 'self.lanceur.OnBalance()',
                      'ateliers' : 'self.lanceur.OnAteliers()',
                      'produits' : 'self.lanceur.OnProduits()'}
        self.dlgdossiers = xgt.DLG_tableau(self,dicOlv=dicOlv,lstBtns= lstBtns,lstActions=lstActions,lstInfos=lstInfos,
                                 dicOnClick=dicOnClick)
        self.ctrlolv = self.dlgdossiers.ctrlOlv
        self.ctrlolv.recordset = recordset

        if len(lstDonnees) > 0:
            # selection de la première ligne
            self.dlgdossiers.ctrlOlv.SelectObject(self.dlgdossiers.ctrlOlv.donnees[0])
            self.IDdossier = self.ctrlolv.Selection()[0].id
        ret = self.dlgdossiers.ShowModal()
        return ret

    def EcranIdent(self,ctrlolv,mode):
        # affichage d'une ligne en vue de modif, toutes les colonnes ne sont pas reprises
        # appel d'un dossier pour affichage table ident
        self.IDdossier = ctrlolv.Selection()[0].id
        req = """
                SELECT *
                FROM _Ident 
                WHERE (_Ident.IDdossier = %s)
                ;"""%(self.IDdossier)
        retour = self.DBsql.ExecuterReq(req, mess='Util_affectations.EcranIdent')
        if retour == "ok":
            recordset = self.DBsql.ResultatReq()
            if len(recordset) == 0:
                retour = "aucun enregistrement disponible"
        if (not retour == "ok"):
            wx.MessageBox("Erreur : %s"%retour)
            return 'ko'

        lstChamps, lstTypes, lstHelp = dtt.GetChampsTypes('_Ident',tous=True)
        self.ctrlolv.lstTblChamps = lstChamps
        self.ctrlolv.lstTblHelp = lstHelp
        dictMatrice = {}
        dictDonnees = {}
        (dictMatrice[('params','Paramètres')],dictDonnees['params'])=xusp.ComposeMatrice('IDjuridique','ImpSoc',lstChamps,lstTypes,
                                                                                    lstHelp=lstHelp,record=recordset[0])
        (dictMatrice[('tabfin','Financement')],dictDonnees['tabfin'])=xusp.ComposeMatrice('Caf','RemAssociés',lstChamps,lstTypes,
                                                                                    lstHelp=lstHelp,record=recordset[0])

        (dictMatrice[('divers','Divers')],dictDonnees['divers'])=xusp.ComposeMatrice('Productions','Validé',lstChamps,lstTypes,
                                                                                    lstHelp=lstHelp,record=recordset[0])

        lstNoms, lstCodes = [],[]
        for categorie,lstDicChamps in dictMatrice.items():
            for dicChamp in lstDicChamps:
                lstCodes.append(dicChamp["name"])
                lstNoms.append(dicChamp["label"])
        # fin de la spécificité _Ident

        all = ctrlolv.GetObjects()
        selection = ctrlolv.Selection()[0]
        ixsel = all.index(selection)

        dlg = xusp.DLG_monoLigne(None,dldMatrice=dictMatrice,ddDonnees=dictDonnees,gestionProperty=True,
                                           pos=(300,0),minSize=(400,1000))
        ret = dlg.ShowModal()
        if ret == 5101:
            # Retour par validation
            valeurs = dlg.pnl.GetValeurs()
            # mise à jour de l'olv d'origine
            for code in ctrlolv.lstCodesColonnes:
                if code in lstCodes:
                    for categorie, dicDonnees in dlg.ddDonnees.items():
                        if code in dicDonnees:
                            ix = ctrlolv.lstCodesColonnes.index(code)
                            valorigine = selection.donnees[ix]
                            if valorigine != valeurs[categorie][code]:
                                if isinstance(valorigine,(str,datetime.date)):
                                    action = "selection.__setattr__('%s','%s')"%(
                                                ctrlolv.lstCodesColonnes[ix],str(valeurs[categorie][code]))
                                elif isinstance(valorigine, (int, float)):
                                    action = "selection.__setattr__('%s',%d)" % (
                                                ctrlolv.lstCodesColonnes[ix], valeurs[categorie][code])
                                else: wx.MessageBox("%s, type non géré pour modifs: %s"%(code,type(valorigine)))
                                try:
                                    eval(action)
                                except: pass
            ctrlolv.MAJ(ixsel)
            # mise à jour table de base de donnee
            lstModifs = []
            for categorie, dicdonnees in valeurs.items():
                for code,valeur in dicdonnees.items():
                    if valeur != None:
                        nom = lstNoms[lstCodes.index(code)]
                        lstModifs.append((nom,valeur))

            if len(lstModifs)>0 and mode == 'modif':
                wherecle = "IDdossier = %d"%self.IDdossier
                ret = self.DBsql.ReqMAJ('_Ident',lstModifs,wherecle,mess='MAJ affectations.EcranIdent')
                if ret != 'ok':
                    wx.MessageBox(ret)
        #ctrlolv.Select(ixsel)
        self.ctrlolv.SetFocus()
        self.ctrlolv.SelectObject(self.ctrlolv.donnees[ixsel])
        dlg.Destroy()

    def OnIdent(self):
        if VerifSelection(self,self.dlgdossiers):
            self.EcranIdent(self.ctrlolv,'modif')
            self.ctrlolv.SetFocus()
            self.ctrlolv.SelectObject(self.dlgdossiers.ctrlOlv.donnees[self.ixsel])

    def OnBalance(self):
        if VerifSelection(self,self.dlgdossiers):
            Balance(self)
            self.ctrlolv.SetFocus()
            self.ctrlolv.SelectObject(self.dlgdossiers.ctrlOlv.donnees[self.ixsel])

    def OnAteliers(self):
        if VerifSelection(self,self.dlgdossiers):
            self.IDdossier = self.dlgdossiers.ctrlOlv.Selection()[0].id
            wx.MessageBox('clic sur ateliers')

    def OnProduits(self):
        if VerifSelection(self,self.dlgdossiers):
            self.IDdossier = self.dlgdossiers.ctrlOlv.Selection()[0].id
            wx.MessageBox('clic sur produits')

    """def Init_dic_produit(self,produit):
        #prépare un dictionnaire vide pour les champs nombre réels
        dic = {'IDMproduit':produit}
        for champ in dtt.GetChamps('_Produits',reel=True):
            dic[champ] = 0.0
        dic['IDMatelier'] = self.dicProduits[produit]['idmatelier']
        dic['Comptes'] = []
        dic['AutreProduit'] = 0.0
        dic['CalculAutreProduit'] = []
        dic['Subventions'] = 0.0
        dic['CalculSubvention'] = []
        dic['AutreProd'] = 0.0
        dic['ProdPrincipal'] = 1
        dic['TypesProduit'] = ''
        dic['Production'] = 0.0
        return dic

    def Init_dic_atelier(self,atelier,IDdossier):
        #prépare un dictionnaire vide pour les champs nombre réels et texte provisoirement en liste
        dic = {'IDMatelier':atelier}
        for champ in dtt.GetChamps('_Ateliers',reel=True):
            dic[champ] = 0.0
        for champ in dtt.GetChamps('_Ateliers',texte=True):
            dic[champ] = []
        dic['IDMatelier'] = atelier
        dic['IDdossier'] = IDdossier
        return dic

    def AffecteAtelier(self, IDdossier,atelier,lstComptesRetenus):
        # Balaye la balance  pour affecter à l'atelier tout les comptes non affectés aux produits
        # on récupère les comptes ds balance, on les traite sur le IDplanCompte
        compteencours = ''
        for IDdossier, Compte, IDligne, Libelle, MotsClePres,Quantites1, Unite1, Quantites2, Unite2, SoldeDeb, DBmvt, \
            CRmvt, SoldeFin, IDplanCompte, Affectation in self.balanceCeg:
            if Compte in lstComptesRetenus and Compte != compteencours: continue
            if not IDplanCompte : 
                IDplanCompte = ChercheIDplanCompte(Compte,self.dicPlanComp)
            if  not (IDplanCompte in self.dicPlanComp) : 
                IDplanCompte = ChercheIDplanCompte(Compte,self.dicPlanComp)
            if len(IDplanCompte.strip())==0: continue
            ok = False            
            # ce compte sera affecté à l'atelier
            post = 'cout'
            # si plusieurs lignes successives d'un même compte (quand plusieurs unités de qté) => compteencours cumule
            compteencours = Compte
            lstComptesRetenus.append(Compte)
            def AppendCompte(lstComptes,compte):
                if not compte in lstComptes:
                    lstComptes.append(compte)
                return
            # inversion des signes de balance pour retrouver du positif dans les produits ou stock
            if IDplanCompte[:2] == '74':
                # subventions seront affectées à l'atelier
                self.dic_Ateliers[atelier]['Subventions'] += SoldeFin
                AppendCompte(self.dic_Ateliers[atelier]['CPTSubventions'],Compte)
                post='Subventions'
            elif IDplanCompte[:2] in ('70','71','75','33','34','35','36','37'):
                self.dic_Ateliers[atelier]['AutreProduit'] += SoldeFin
                AppendCompte(self.dic_Ateliers[atelier]['CPTAutreProduit'],Compte)
                post='AutreProduit'
            elif IDplanCompte[:3] in ('307','604'):
                self.dic_Ateliers[atelier]['AutreProduit'] += SoldeFin
                AppendCompte(self.dic_Ateliers[atelier]['CPTAutreProduit'],Compte)
                post = 'AutreProduit'

            #TODO inserer les comptes de charges selon type

            # MAJ _Balances
            affectation = 'A.' + atelier + "." + post
            lstCouples = [('IDplanCompte', IDplanCompte), ('Affectation', affectation)]
            condition = "IDligne = %d" % IDligne
            self.DBsql.ReqMAJ('_Balances', couples=lstCouples, condition=condition, mess= "GeneredicAtelier MAJ _Balances")

        return

    def GenereDicProduit(self, IDdossier, produit, lstMots, lstComptesRetenus, dicProduit=None):
        # Balaye la balance  pour affecter à ce produit, création ou MAJ de dicProduit, et MAJ de self.balanceCeg
        if not dicProduit:
            dicProduit = self.Init_dic_produit(produit)
            dicProduit['IDdossier'] = IDdossier
        lstRadicaux = self.dicProduits[produit]['cptproduit'].split(',')
        compteencours = ''
        atelier = dicProduit['IDMatelier']
        if(not atelier in self.dic_Ateliers) and atelier != 'ANY':
            dicAtelier = self.Init_dic_atelier(atelier,dicProduit['IDdossier'])
            self.dic_Ateliers[atelier] = dicAtelier
        if self.dicProduits[produit]['typesproduit']:
            for tip in self.dicProduits[produit]['typesproduit'].split(','):
                if not tip.lower() in dicProduit['TypesProduit'].lower():
                    dicProduit['TypesProduit'] += (tip + ',')
        # on récupère les comptes ds balance, on les traite sur le IDplanCompte
        for IDdossier, Compte, IDligne, Libelle, MotsClePres,Quantites1, Unite1, Quantites2, Unite2, SoldeDeb, DBmvt, \
            CRmvt, SoldeFin, IDplanCompte, Affectation in self.balanceCeg:
            if not IDplanCompte : 
                IDplanCompte = ChercheIDplanCompte(Compte,self.dicPlanComp)
            if  not (IDplanCompte in self.dicPlanComp) : 
                IDplanCompte = ChercheIDplanCompte(Compte,self.dicPlanComp)
            if len(IDplanCompte.strip())==0: continue
            # test sur liste de mot, on garde ceux qui contiennent un mot clé du produit
            ok = False
            if lstMots:
                # teste la présence du mot clé dans le compte
                for mot in lstMots:
                    if mot in MotsClePres.lower():
                        ok = True
                        #un mot présent suffit pour matcher
                        break
            if not ok: continue
            # ce compte a matché il sera affecté au produit
            affectation = ''
            if Compte in lstComptesRetenus and Compte != compteencours:
                # le compte à déjà été affecté par un autre produit et ce n'est pas une deuxième ligne d'un même compte
                continue
            # si plusieurs lignes successives d'un même compte (quand plusieurs unités de qté) => compteencours cumule
            compteencours = Compte
            # teste si le compte rentre dans les radicaux possibles pour le modèle de produit
            for radical in lstRadicaux:
                if radical == IDplanCompte[:len(radical)]:
                    # le compte rentre dans le produit : calcul du produit
                    lstComptesRetenus.append(Compte)
                    dicProduit['Comptes'].append(Compte)
                    dicProduit['Quantité1'] += Quantites1
                    dicProduit['Quantité2'] += Quantites2
                    # inversion des signes de balance pour retrouver du positif dans les produits ou stock
                    if IDplanCompte[:2] == '70':
                        dicProduit['Ventes'] -= SoldeFin
                    elif IDplanCompte[:2] == '71':
                        dicProduit['DeltaStock'] -= SoldeFin
                    elif IDplanCompte[:2] == '72':
                        dicProduit['AutreProd'] -= SoldeFin
                    elif IDplanCompte[:2] == '74':
                        # les subventions seront affectées à l'atelier même avec mot clé présent niveau produit
                        self.dic_Ateliers[atelier]['Subventions'] += SoldeFin
                        self.dic_Ateliers[atelier]['CPTSubventions'].append(Compte)
                        affectation = 'A.' + atelier + "." + 'Subventions'
                    elif IDplanCompte[:2] == '75':
                        dicProduit['AutreProd'] -= SoldeFin
                    elif IDplanCompte[:2] == '76':
                        self.dic_Ateliers[atelier]['AutreProduit'] += SoldeFin
                        self.dic_Ateliers[atelier]['CPTAutreProduit'].append(Compte)
                        affectation = 'A.' + atelier + "." + 'AutreProduit'
                    elif IDplanCompte[:3] == '603':
                        dicProduit['DeltaStock'] -= SoldeFin
                    elif IDplanCompte[:3] == '604':
                        dicProduit['AchatAnmx'] -= SoldeFin
                    # le paramétrage ne doit pas contenir à la fois des ((603 ou 71) et 3) dans les radicaux
                    elif IDplanCompte[:1] == '3':
                        dicProduit['DeltaStock'] -= SoldeFin - SoldeDeb
                        dicProduit['StockFin'] -= SoldeFin
                    else:
                        dicProduit['AutreProd'] -= SoldeFin
                    production = 0.0
                    for poste in ('Ventes', 'DeltaStock', 'AchatAnmx', 'AutreProd'):
                        production += dicProduit[poste]
                    dicProduit['Production'] = production
                    # MAJ _Balances
                    # enregistrement du compte std et marque d'affectation
                    if affectation == '':
                        affectation = 'P.'+atelier+'.'+produit
                    lstCouples = [('IDplanCompte', IDplanCompte), ('Affectation', affectation)]
                    condition = "IDligne = %d" % IDligne
                    self.DBsql.ReqMAJ('_Balances', couples=lstCouples, condition=condition, mess= "GenereDicProduit MAJ _Balances")
                    break
        return dicProduit

    def Genere_Atelier(self,IDMatelier,dicAtelier):
        # création ou MAJ d'un atelier par son produit et les modèles
        lstDonnees, lstChamps =[], []
        lstChampsTable = dtt.GetChamps('_Ateliers')
        for champ in dicAtelier.keys():
            if champ in lstChampsTable:
                lstChamps.append(champ)
                lstDonnees.append(dicAtelier[champ])
        orui.TronqueData('_Ateliers',lstChamps,lstDonnees)
        ok = self.DBsql.ReqInsert('_Ateliers',lstChamps,lstDonnees,mess= 'Genere_Atelier Atelier : %s'%IDMatelier)
        return ok

    def Genere_Produit(self, dicProduit):
        # création ou MAJ d'un produits par son produit et les modèles
        IDMproduit = dicProduit['IDMproduit']
        lstChampsTable = dtt.GetChamps('_Produits')
        lstChamps = []
        lstDonnees = []
        for champ in dicProduit.keys():
            if champ in lstChampsTable:
                lstChamps.append(champ)
                lstDonnees.append(dicProduit[champ])
        orui.TronqueData('_Produits',lstChamps,lstDonnees)
        ok = self.DBsql.ReqInsert('_Produits', lstChamps, lstDonnees, mess='GenereProduits Produit : %s' % IDMproduit)
        return ok
    """

#************************   Pour Test ou modèle  *********************************
if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    #fn = Affectations(annee='2018',client='041842',agc='ANY')
    fn = Affectations(annee=2018,groupe='testAlpes',agc='ANY')
    ret = fn.retour
    print('Retour appli: ',ret)

    app.MainLoop()

