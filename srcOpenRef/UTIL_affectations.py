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
import xpy.xGestion_Ligne as xgl
import xpy.outils.xformat as xfmt
import xpy.outils.xselection as xsel

def Tronque35(txt):
    # tronque les  premiers caractères d'une chaîne
    try:
        return txt[35:]
    except: return txt

def ComposeLstDonnees(lstNomsColonnes,record,lstChamps):
    # retourne les données pour colonnes, extraites d'un record défini par une liste de champs
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
        elif tip[:10] == 'tinyint(1)': lstValDef.append(True)
        elif tip[:5] == 'float': lstValDef.append(0.0)
        elif tip[:4] == 'date': lstValDef.append(datetime.date(1900,1,1))
        else: lstValDef.append('')
    return lstValDef

def LargeursDefaut(lstNomsColonnes,lstChamps,lstTypes):
    # Evaluation de la largeur nécessaire des colonnes selon le type de donnee et la longueur du champ
    lstLargDef = []
    for colonne in lstNomsColonnes:
        if colonne in lstChamps:
            tip = lstTypes[lstChamps.index(colonne)]
        else: tip = 'int'
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

def VerifSelection(parent,dlg,infos=True,mode='modif'):
    # contrôle la selection d'une ligne, puis marque le no dossier et eventuellement texte infos à afficher
    if len(dlg.ctrlOlv.Selection())==0 and mode != 'ajout':
        wx.MessageBox("Action Impossible\n\nVous n'avez pas selectionné une ligne!","Préalable requis")
        return False
    if len(dlg.ctrlOlv.Selection()) == 0:
        dlg.ctrlOlv.SelectObject(dlg.ctrlOlv.GetObjects()[0])
    parent.ixsel = parent.ctrlolv.donnees.index(parent.ctrlolv.Selection()[0])
    if infos:
        noclient = dlg.ctrlOlv.Selection()[0].noclient
        cloture = dlg.ctrlOlv.Selection()[0].cloture
        nomexploitation = dlg.ctrlOlv.Selection()[0].nomexploitation
        parent.infos = 'Dossier: %s, %s, %s'%(noclient,cloture,nomexploitation)
    return True

def AteliersOuverts(IDdossier,DBsql):
    lstAteliers = []
    req = """SELECT mAteliers.IDMatelier
            FROM _Ateliers 
            INNER JOIN mAteliers ON _Ateliers.IDMatelier = mAteliers.IDMatelier
            WHERE (_Ateliers.IDdossier = %d)
            """%IDdossier
    retour = DBsql.ExecuterReq(req, mess='Util_affectations.AteliersOuverts')
    if not retour == "ok":
        wx.MessageBox("Erreur : %s"%retour)
    else:
        recordset = DBsql.ResultatReq()
        for (IDatelier,) in recordset:
            lstAteliers.append(IDatelier)
    return lstAteliers

def AteliersFermes(dossier,DBsql):
    lstAteliers = []
    req = """SELECT mAteliers.IDMatelier
            FROM mAteliers 
            LEFT JOIN _Ateliers ON _Ateliers.IDMatelier = mAteliers.IDMatelier
            WHERE (((_Ateliers.IDMatelier) Is Null)) OR (((_Ateliers.IDdossier) <> %d))
            GROUP BY mAteliers.IDMatelier;
            """%(dossier)
    retour = DBsql.ExecuterReq(req, mess='Util_affectations.AteliersFermés')
    if not retour == "ok":
        wx.MessageBox("Erreur : %s"%retour)
    else:
        recordset = DBsql.ResultatReq()
        for (IDatelier,) in recordset:
            lstAteliers.append((IDatelier))
    return lstAteliers

def ProduitsOuverts(IDdossier,DBsql):
    lstProduits = []
    req = """SELECT mProduits.IDMatelier,mProduits.IDMproduit
            FROM _Produits 
            INNER JOIN mProduits ON _Produits.IDMproduit = mProduits.IDMproduit
            WHERE (_Produits.IDdossier = %d)
            """%IDdossier
    retour = DBsql.ExecuterReq(req, mess='Util_affectations.ProduitsOuverts')
    if not retour == "ok":
        wx.MessageBox("Erreur : %s"%retour)
    else:
        recordset = DBsql.ResultatReq()
        for IDatelier,IDproduit in recordset:
            lstProduits.append((IDatelier,IDproduit))
    return lstProduits

def ProduitsFermes(dossier,idmatelier,DBsql):
    lstProduits = []
    req = """SELECT mProduits.IDMproduit
            FROM mProduits 
            LEFT JOIN _Produits ON _Produits.IDMproduit = mProduits.IDMproduit
            WHERE ( (_Produits.IDdossier = %d OR _Produits.IDdossier IS NULL)
                    AND mProduits.IDMatelier = '%s'
                    AND _Produits.IDMatelier is NULL)
            """%(dossier,idmatelier)
    retour = DBsql.ExecuterReq(req, mess='Util_affectations.ProduitsFermés')
    if not retour == "ok":
        wx.MessageBox("Erreur : %s"%retour)
    else:
        recordset = DBsql.ResultatReq()
        for (IDproduit,) in recordset:
            lstProduits.append((IDproduit))
    return lstProduits

def CoutsPossibles(IDdossier,DBsql):
    lstCouts = []
    req = """SELECT mCoûts.IDMatelier, mCoûts.IDMcoût
            FROM mCoûts 
                 LEFT JOIN _Ateliers ON mCoûts.IDMatelier = _Ateliers.IDMatelier
            WHERE ((_Ateliers.IDdossier) = %d) 
                    OR ((mCoûts.IDMatelier)="ANY")
            ;"""%IDdossier
    retour = DBsql.ExecuterReq(req, mess='Util_affectations.CoutsPossibles')
    if not retour == "ok":
        wx.MessageBox("Erreur : %s"%retour)
    else:
        recordset = DBsql.ResultatReq()
        for IDatelier,IDcout in recordset:
            if IDatelier == 'ANY': IDatelier = '*'
            lstCouts.append((IDatelier,IDcout))
    return lstCouts

def AffectsActifs(IDdossier,DBsql):
    # retourne les affectations possibles pour les marges ( le poste est demandé à la sortie pour les ateliers)
    lstAffects = ['']
    ateliersOuverts = AteliersOuverts(IDdossier,DBsql)
    for IDatelier in ateliersOuverts:
        lstAffects.append("A.%s._"%IDatelier)
    for IDatelier,IDproduit in ProduitsOuverts(IDdossier,DBsql):
        lstAffects.append("P.%s.%s"%(IDatelier,IDproduit))
    for IDatelier,IDcout in CoutsPossibles(IDdossier,DBsql):
        if IDatelier == '*' and len(ateliersOuverts) == 1:
            IDatelier = ateliersOuverts[0]
        lstAffects.append("C.%s.%s"%(IDatelier,IDcout))
    lstAffects.append("I.TabFin._")
    return lstAffects

def PlanComptes(classe,DBsql):
    # retourne les comptes officiels de la classe précisée
    lstComptes = []
    req = """SELECT IDplanCompte, NomCompte
            FROM cPlanComptes
            WHERE (cPlanComptes.IDplanCompte) Like '%s%%';
            """%classe
    retour = DBsql.ExecuterReq(req, mess='Util_affectations.PlanComptes')
    if not retour == "ok":
        wx.MessageBox("Erreur : %s"%retour)
    else:
        recordset = DBsql.ResultatReq()
        for IDplanCompte,NomCompte in recordset:
            sep = '_' * (7 - len(IDplanCompte))
            lstComptes.append('%s%s %s'%(IDplanCompte,sep,NomCompte))
    if len(lstComptes) == 0 and classe != '':
        lstComptes= PlanComptes('',DBsql)
    return lstComptes

def LstFromModeles(DBsql):
    # retourne les lignes des tables modèles
    lstModeles = []
    req = """
            SELECT IDMatelier,IDMproduit,NomProduit
            FROM mProduits
            ;"""
    retour = DBsql.ExecuterReq(req, mess='Util_affectations.mProduits')
    if not retour == "ok":
        wx.MessageBox("Erreur : %s"%retour)
    else:
        recordset = DBsql.ResultatReq()
        for IDMatelier,IDMproduit,NomProduit in recordset:
            lstModeles.append(IDMatelier+'_ Prod_'+IDMproduit+'_'+NomProduit)

    req = """
            SELECT IDMatelier,IDMcoût,NomCoût
            FROM mCoûts
            ;"""
    retour = DBsql.ExecuterReq(req, mess='Util_affectations.mCoûts')
    if not retour == "ok":
        wx.MessageBox("Erreur : %s"%retour)
    else:
        recordset = DBsql.ResultatReq()
        for IDMatelier,IDMproduit,NomCoût in recordset:
            lstModeles.append(IDMatelier+'_Coût_'+IDMproduit+'_'+NomCoût)
    l =  sorted(lstModeles)
    return l

#----------------------------------------------------------------------

class Balance():
    def __init__(self,parent):
        self.title = '[UTIL_affectations].Balance'
        #table qui sera gérée par les actions
        self.table = '_Balances'
        self.mess = ''
        self.clic = None
        self.parent = parent
        self.IDdossier = parent.IDdossier

        # pointeur de la base principale ( ouverture par défaut de db_prim via xGestionDB)
        self.DBsql = self.parent.DBsql
        self.retour = self.EcranBalance()

    # Gestion de l'OLV
    def EcranBalance(self,ixsel=0):
        # appel de la balance du dossier pour affichage
        req = """
                SELECT *
                FROM %s
                WHERE (IDdossier = %d) AND (LEFT(IDplanCompte,1) IN ('3','6','7'))
                ;"""%(self.table,self.IDdossier)
        retour = self.DBsql.ExecuterReq(req, mess='Util_affectations.%s'%self.table)
        if retour == "ok":
            recordset = self.DBsql.ResultatReq()
            if len(recordset) == 0:
                retour = "aucun enregistrement disponible"
        if (not retour == "ok"):
            wx.MessageBox("Erreur : %s"%retour)
            return 'ko'
        lstChamps, lstTypes, lstHelp = dtt.GetChampsTypes(self.table,tous=True)
        lstNomsColonnes =   xusp.ExtractList(lstChamps,champDeb='IDdossier',champFin='Compte')\
                            + xusp.ExtractList(lstChamps,champDeb='IDplanCompte',champFin='Affectation')\
                            + xusp.ExtractList(lstChamps,champDeb='Libellé',champFin='SoldeFin')
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

        # options d'enrichissement de l'écran de saisie
        lstBtns = [('BtnOK', wx.ID_OK, wx.Bitmap("xpy/Images/100x30/Bouton_fermer.png", wx.BITMAP_TYPE_ANY),
                    "Cliquez ici pour fermer la fenêtre")]
        # params d'actions: idem boutons, ce sont des boutons placés à droite et non en bas
        lstActions = [('ajout',wx.ID_APPLY,'Ajouter',"Cliquez ici pour ajouter une ligne"),
                    ('modif',wx.ID_APPLY,'Modifier',"Cliquez ici pour modifier la ligne"),
                    ('copier',wx.ID_APPLY,'Copier',"Cliquez ici pour copier la ligne"),
                    ('eclater',wx.ID_APPLY,'Eclater',"Cliquez ici pour subdiviser le compte"),
                    ('supprimer', wx.ID_APPLY, 'Supprimer', "Supprimer la ligne et reporter le solde dessus"),
                      ]
        # un param par info: texte ou objet window.  Les infos sont  placées en bas à gauche
        self.trace = self.parent.trace + "- BALANCE"
        self.infos = self.parent.infos
        lstInfos = [self.infos,self.trace]
        # params des actions ou boutons: name de l'objet, fonction ou texte à passer par eval()
        dicOnClick = {
                      'ajout' : 'self.lanceur.OnAjout()',
                      'modif' : 'self.lanceur.OnModif()',
                      'copier' : 'self.lanceur.OnCopier()',
                      'eclater' : 'self.lanceur.OnEclater()',
                      'supprimer' : 'self.lanceur.OnSupprimer()'}
        self.dlgolv = xgt.DLG_tableau(self,dicOlv=dicOlv,lstBtns= lstBtns,lstActions=lstActions,lstInfos=lstInfos,
                                 dicOnClick=dicOnClick)

        #l'objet ctrlolv pourra être appelé, il sert de véhicule à params globaux de l'original
        self.ctrlolv = self.dlgolv.ctrlOlv
        self.ctrlolv.lstTblHelp = lstHelp
        self.ctrlolv.lstTblChamps = lstChamps
        self.ctrlolv.lstTblCodes = [xusp.SupprimeAccents(x) for x in lstChamps]
        self.ctrlolv.lstTblValdef = ValeursDefaut(lstChamps,lstChamps,lstTypes)
        self.ctrlolv.recordset = recordset
        if len(lstDonnees)>0:
            # selection de la première ligne ou du pointeur précédent
            self.ctrlolv.SelectObject(self.ctrlolv.donnees[ixsel])
        ret = self.dlgolv.ShowModal()
        return ret

    def OnAjout(self):
        self.AppelSaisie('ajout')
        self.Reinit()

    def OnModif(self):
        self.AppelSaisie('modif')

    def OnCopier(self):
        self.AppelSaisie('copie')
        self.Reinit()

    def OnEclater(self):
        self.AppelSaisie('eclat')
        self.Reinit()

    def OnSupprimer(self):
        self.AppelSaisie('suppr')
        #self.ctrlolv.MAJ()

    def Reinit(self):
        ix = self.ixsel
        self.dlgolv.Close()
        del self.ctrlolv
        self.EcranBalance(ixsel = ix)

    # gestion de la ligne
    def AppelSaisie(self,mode):
        # personnalisation de la grille de saisie
        ctrlolv = self.ctrlolv
        champdeb = 'IDdossier'
        champfin = 'SoldeFin'
        kwds = {'pos': (300, 100)}
        kwds['minSize'] = (500, 500)

        codedeb = ctrlolv.lstCodesColonnes[ctrlolv.lstNomsColonnes.index(champdeb)]
        codefin = ctrlolv.lstCodesColonnes[ctrlolv.lstNomsColonnes.index(champfin)]
        lstEcrCodes = xusp.ExtractList(ctrlolv.lstCodesColonnes,codedeb,codefin)
        all = ctrlolv.innerList
        selection = ctrlolv.Selection()[0]
        self.ixsel = all.index(selection)

        # personnalisation des actions
        self.valuesAffect = AffectsActifs(self.IDdossier,self.DBsql)
        classe = selection.compte[1]
        valuesPlanCompte = PlanComptes(classe,self.DBsql)
        dicOptions = {
                'affectation':{
                    'values': self.valuesAffect,
                    'genre': 'combo',
                    'ctrlAction': 'OnModifAffect',
                    'btnLabel': "...",
                    'btnHelp': "Cliquez pour ouvrir un nouveau prouit à ce dossier",
                    'btnAction': 'OnAjoutAffect',},
                'idplancompte':{
                    'values': valuesPlanCompte,
                    'genre': 'enum',},
                'IDdossier': {'enable': False},
                'soldefin': {'enable': False},
                'soldedeb': {'ctrlAction': 'CalculSolde',},
                'crmvt': {'ctrlAction': 'CalculSolde',},
                'dbmvt': {'ctrlAction': 'CalculSolde',}}

        # lancement de l'écran de saisie
        self.saisie = xgl.Gestion_ligne(self, self.DBsql, self.table, dtt, mode, ctrlolv,**kwds)
        if self.saisie.ok and mode != 'suppr':
            self.saisie.SetBlocGrille(lstEcrCodes,dicOptions,'Gestion des produits ouverts')
            self.saisie.InitDlg()
            self.FinSaisie()
        del self.saisie

    def OnChildBtnAction(self,event):
        self.action = 'self.%s(event)' % event.EventObject.actionBtn
        try:
            eval(self.action)
        except Exception as err:
            wx.MessageBox("Echec sur lancement action sur btn: '%s' \nLe retour d'erreur est : \n%s"%(self.action, err),style=wx.ICON_WARNING)

    def OnChildCtrlAction(self,event):
        self.action = 'self.%s(event)' % event.EventObject.actionCtrl
        try:
            eval(self.action)
            event.Skip()
        except Exception as err:
            wx.MessageBox("Echec sur lancement action sur ctrl: '%s' \nLe retour d'erreur est : \n%s"%(self.action, err),style=wx.ICON_WARNING)
        print()

    def CalculSolde(self,event):
        valeurs = self.saisie.dlg.pnl.GetValeurs()
        for categorie, dicDonnees in valeurs.items():
            if 'soldedeb' in  dicDonnees:
                soldedeb = dicDonnees['soldedeb']
                cdCateg = categorie
            if 'dbmvt' in  dicDonnees: dbmvt = dicDonnees['dbmvt']
            if 'crmvt' in  dicDonnees: crmvt = dicDonnees['crmvt']
        soldefin= str(round(xfmt.Nz(soldedeb) - xfmt.Nz(crmvt) + xfmt.Nz(dbmvt),2))
        ddDonnees = {cdCateg:{'soldefin':soldefin}}
        ret = self.saisie.dlg.pnl.SetValeurs(ddDonnees)
        event.Skip()

    def OnModifAffect(self,event):
        affect = self.saisie.dlg.pnl.GetOneValue('affectation')
        if '*' in affect:
            cout = affect.split('.')[2]
            lstAteliers = []
            for ligne in self.valuesAffect:
                tplligne = ligne.split('.')
                if len(tplligne) == 3:
                    if tplligne[0] == 'A':
                        donnees = (tplligne[1],)
                        if not donnees in lstAteliers:
                            lstAteliers.append(donnees)
            lstColonnes =[("Atelier", "left", -1, "col1")]
            dlgsel = xsel.DLG_selection(None,lstColonnes=lstColonnes,lstValeurs=lstAteliers,
                                        title="Choix de l'atelier à imputer '%s'"%cout,minsize=(250,350))
            ret = dlgsel.ShowModal()
            if ret == wx.ID_OK:
                # Réinit des values de ctrl affetation
                atelier = lstAteliers[dlgsel.GetSelections()][0]
                for item in self.valuesAffect:
                    ix = self.valuesAffect.index(item)
                    self.valuesAffect[ix] = item.replace('*',atelier)
                affect = affect.replace('*', atelier)
                self.saisie.dlg.pnl.SetOneValues('affectation',self.valuesAffect)
                self.saisie.dlg.pnl.SetOneValue('affectation',affect)
            dlgsel.Destroy()
        event.Skip()

    def OnAjoutAffect(self,event):
        # action du bouton d'affectation
        produits = Produits(self,visu=False)
        produits.AppelSaisie('ajout')
        # réinitialisation de l'écran de saisie
        self.valuesAffect = AffectsActifs(self.IDdossier,self.DBsql)
        for (cdcateg,nmcateg),lstlignes in self.saisie.dictMatrice.items():
            for dicligne in lstlignes:
                if dicligne['name'] == 'affectation':
                    ddDonnees={cdcateg:{'affectation':self.valuesAffect}}
                    break
        self.saisie.dlg.pnl.SetOneValues(ddDonnees)
        self.saisie.dlg.pnl.Refresh()
        event.Skip()

    def Validation(self,valeurs):
        messfinal = "Validation de la saisie\n\nFaut-il forcer l'enregistrement mal saisi?\n"
        retfinal = True
        # ensemble des traitements de sortie dans une liste déroulée
        for item in [self.TronqueCompte(valeurs),]:
            ret,mess = item
            messfinal += "\n%s"%mess
            #une seule erreur provoquera l'affichage de la confirmation nécessaire
            retfinal *= ret
        if not retfinal :
            retfinal = wx.YES == wx.MessageBox(messfinal,style=wx.YES_NO)
        return retfinal

    def TronqueCompte(self,valeurs):
        # retire le libellé qui avait été mis en suffixe de compte dans la combo box
        mess = ''
        for categorie, dicDonnees in valeurs.items():
            if 'idplancompte' in  dicDonnees:
                decoup = dicDonnees['idplancompte'].split('_')
                if len(decoup)>0 :
                    dicDonnees['idplancompte'] = decoup[0]
                    mess = 'compte tronqué'
        return True, mess

    def FinSaisie(self):
        #prise en compte de l'affectation dans les produits, ateliers ou coûts
        affectation = self.saisie.dlg.pnl.GetOneValue('affectation')
        oldaffect = self.saisie.lstOlvValeur[self.ctrlolv.lstCodesColonnes.index('affectation')]
        #mise à jour des produits couts ateliers suite aux modifs
        if affectation != oldaffect:
            ret = orut.Affectation(self.IDdossier,oldaffect,self.DBsql)
            ret += orut.Affectation(self.IDdossier,affectation,self.DBsql)
            if ret != 'okok':
                ret = ret.replace('ok',' - ')
                wx.MessageBox("Erreur UTIL_affectation.Balance.FinSaisie\n\nAffectation: '%s' vers '%s'\n%s"
                              %(oldaffect,affectation,ret))

class Ateliers():
    def __init__(self, parent,visu=True):
        self.title = '[UTIL_affectations].Ateliers'
        self.table = '_Ateliers'
        self.visu = visu
        self.mess = ''
        self.clic = None
        self.parent = parent
        self.IDdossier = parent.IDdossier

        # pointeur de la base principale ( ouverture par défaut de db_prim via xGestionDB)
        self.DBsql = self.parent.DBsql
        self.retour = self.EcranAteliers()

    def EcranAteliers(self,ixsel=0):
        champsRequete = dtt.GetChamps('_Ateliers')
        champsRequete.extend(['NomAtelier','UnitéCapacité'])
        self.lstCodesRequete = [xusp.SupprimeAccents(x) for x in champsRequete]
        champsSelect =  [ '_Ateliers.%s'%x for x in dtt.GetChamps('_Ateliers')]
        champsSelect.extend(['mAteliers.NomAtelier','mAteliers.UnitéCapacité'])
        champsSelect = str(champsSelect)[1:-1]
        champsSelect = champsSelect.replace("'","")
        # appel des ateliers utilisés dans le dossier pour affichage en tableau
        req = """SELECT %s
                FROM _Ateliers 
                INNER JOIN mAteliers ON (_Ateliers.IDMatelier = mAteliers.IDMatelier) 
                WHERE _Ateliers.IDdossier = %s
                ;""" % (champsSelect,self.IDdossier)
        retour = self.DBsql.ExecuterReq(req, mess='Util_affectations.ListeAteliers')
        if retour == "ok":
            recordset = self.DBsql.ResultatReq()
            if len(recordset) == 0:
                wx.MessageBox("Remarque: %s" %"aucun atelier n'est encore affecté")
        if (not retour == "ok"):
            wx.MessageBox("Erreur : %s" % retour)
            return 'ko'

        lstNomsColonnes = ['ix','Dossier','Atelier','Désignation','Capacité','UnitéCapacité','ProduitsDivers','Subventions',
                           'Distribution','Conditionnement','ApprosDivers','ServicesDivers','AmosSpécif']
        # la listes ChampsColonnes permet de faire le lien avec la table d'origine en modification
        lstChampsColonnes = ['ix','IDdossier','IDMatelier','Désignation','Capacité','UnitéCapacité','AutreProduit','Subventions',
                             'Comm','Conditionnement','AutresAppros','AutresServices','AmosSpécif',]
        lstCodesColonnes = [xusp.SupprimeAccents(x) for x in lstChampsColonnes]

        lstValDefColonnes = [0,0,"","",0.0,"",0.0,0.0,
                            0.0,0.0,0.0,0.0,0.0]
        lstChamps, lstTypes, lstHelp = dtt.GetChampsTypes(self.table,tous=True)
        lstLargeurColonnes = LargeursDefaut(lstChampsColonnes,lstChamps,lstTypes)
        lstDonnees = []
        ix=0
        # composition des données du tableau à partir du recordset
        for record in recordset:
            ligne = []
            # ajustement des valeurs
            designation = record[champsRequete.index('NomPersonnalisé')]
            if not designation or  designation == '':
                designation = record[champsRequete.index('NomAtelier')]
            # constitution des lignes de données
            for champ in lstChampsColonnes:
                if champ in champsRequete:
                    val = record[champsRequete.index(champ)]
                else:
                    if champ == 'ix': val = ix
                    elif champ == 'Désignation': val = designation
                    else: print(champ)
                ligne.append(val)
            lstDonnees.append(ligne)
            ix += 1
        # matrice OLV
        lstColonnes = xusp.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)

        dicOlv = {
            'lanceur': self,
            'listeColonnes': lstColonnes,
            'listeDonnees': lstDonnees,
            'checkColonne': False,
            'hauteur': 650,
            'largeur': 1300,
            'recherche': True,
            'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
            'dictColFooter': {"designation": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                              }
        }

        # options d'enrichissement de l'écran DLG
        lstBtns = [('BtnOK', wx.ID_OK, wx.Bitmap("xpy/Images/100x30/Bouton_fermer.png", wx.BITMAP_TYPE_ANY),
                    "Cliquez ici pour fermer la fenêtre")]
        # params d'actions: idem boutons, ce sont des boutons placés à droite et non en bas
        lstActions = [('ajout', wx.ID_APPLY, 'Ajouter', "Ajouter un nouvel atelier dans le dossier"),
                      ('modif', wx.ID_APPLY, 'Modifier', "Modifier les propriétés du atelier pour le dossier"),
                      ('suppr', wx.ID_APPLY, 'Supprimer', "Supprimer le atelier dans le dossier"),
                      ]
        # un param par info: texte ou objet window.  Les infos sont  placées en bas à gauche
        self.trace = self.parent.trace + " - ATELIERS OUVERTS"
        self.infos = self.parent.infos
        lstInfos = [self.infos, self.trace]
        # params des actions ou boutons: name de l'objet, fonction ou texte à passer par eval()
        dicOnClick = {
            'ajout': 'self.lanceur.OnAjouter()',
            'modif': 'self.lanceur.OnModif()',
            'suppr': 'self.lanceur.OnSupprimer()'}
        self.dlgolv = xgt.DLG_tableau(self, dicOlv=dicOlv, lstBtns=lstBtns, lstActions=lstActions, lstInfos=lstInfos,
                                      dicOnClick=dicOnClick)


        # rappel des propriétés de la table
        self.lstTblChamps, lstTypes, lstHelp = dtt.GetChampsTypes(self.table, tous=True)

        # l'objet ctrlolv pourra être appelé, il sert de véhicule à params globaux de l'original
        self.ctrlolv = self.dlgolv.ctrlOlv
        self.ctrlolv.lstTblHelp = lstHelp
        self.ctrlolv.lstTblChamps = self.lstTblChamps
        self.ctrlolv.lstTblCodes = [xusp.SupprimeAccents(x) for x in self.lstTblChamps]
        self.ctrlolv.lstTblValdef = ValeursDefaut(self.lstTblChamps,self.lstTblChamps,lstTypes)
        self.ctrlolv.recordset = recordset
        if len(lstDonnees) > 0:
            # selection de la première ligne
            self.ctrlolv.SelectObject(self.ctrlolv.donnees[0])
        ret = wx.ID_OK
        if len(lstDonnees)>0:
            # selection de la première ligne ou du pointeur précédent
            self.ctrlolv.SelectObject(self.ctrlolv.donnees[ixsel])
        if self.visu:
            ret = self.dlgolv.ShowModal()
        return ret

    def OnModif(self):
        self.AppelSaisie('modif')

    def OnAjouter(self):
        self.AppelSaisie('ajout')
        self.Reinit()

    def OnSupprimer(self):
        self.AppelSaisie('suppr')

    def Reinit(self):
        ix = self.ixsel
        self.dlgolv.Close()
        del self.ctrlolv
        self.EcranAteliers(ixsel = ix)

    def AppelSaisie(self, mode):
        ctrlolv = self.ctrlolv

        # personnalisation de la grille de saisie : champs à visualiser, position
        champdeb = 'IDMatelier'
        champfin = 'Validation'
        lstEcrChamps = xusp.ExtractList(self.lstTblChamps,champdeb,champfin)
        lstEcrCodes = [xgl.SupprimeAccents(x) for x in lstEcrChamps]

        kwds = {'pos': (350, 20)}
        kwds['minSize'] = (350, 600)
        all = ctrlolv.innerList
        selection = ctrlolv.Selection()
        if len(selection)>0:
            self.ixsel = all.index(selection[0])
        else: self.ixsel = 0

        # personnalisation des actions
        dicOptions = {'idmatelier': {'enable': False,},}
        # disable de tous les champs de synthèse
        for ix in range(self.lstTblChamps.index('AutreProduit'),self.lstTblChamps.index('CPTAmosSpécif')+1):
            code = xusp.SupprimeAccents(self.lstTblChamps[ix])
            if code[:3]=='cpt':
                dicOptions[code] = {
                    'enable': False,
                    'btnLabel': "...",
                    'btnHelp': "Cliquez pour gérer l'affectation des comptes",
                    'btnAction': 'OnComptes',}
            else:
                dicOptions[code] = {'enable': False,}

        if mode == 'ajout':
            lstAteliers = AteliersFermes(self.IDdossier, self.DBsql)
            dicOptions['idmatelier']={'genre':'enum',
                                      'values': lstAteliers,
                                      'enable':True,
                                      'help': "Choisissez un atelier à ouvrir",
                                      }

        # lancement de l'écran de saisie
        lstcle = [('IDdossier',self.IDdossier)]
        self.saisie = xgl.Gestion_ligne(self, self.DBsql, self.table, dtt, mode, ctrlolv,lstcle,**kwds)
        if self.saisie.ok and mode != 'suppr':
            self.saisie.SetBlocGrille(lstEcrCodes,dicOptions,'Gestion des ateliers ouverts')
            if mode == 'ajout':
                # RAZ de toutes les données
                self.saisie.dictDonnees = {}
            self.saisie.InitDlg()
        del self.saisie

    def Validation(self,valeurs):
        # test de sortie d'écran
        messfinal = "Validation de la saisie\n\nFaut-il forcer l'enregistrement mal saisi?\n"
        retfinal = True
        # l'ensemble des traitements de sortie sont dans une liste déroulée à programmer ici
        for item in [self.VerifCleUnique(valeurs),]:
            ret,mess = item
            messfinal += "\n%s"%mess
            #une seule erreur provoquera l'affichage de la confirmation nécessaire
            retfinal *= ret
        if not retfinal :
            retfinal = wx.YES == wx.MessageBox(messfinal,style=wx.YES_NO)
        return retfinal

    def VerifCleUnique(self,valeurs):
        mess = ''
        for categorie, dicDonnees in valeurs.items():
            idmatelier = dicDonnees['idmatelier']
        unique = True
        if len(idmatelier)  == 0:
            # les champs sont-ils renseignés (ont des longueurs non nulles)
            unique = False
            mess += "Il faut choisir obligatoirement un atelier dans les possibles"
        if not self.saisie.mode in ['modif','consult']:
            # on continue en vérifiant si la clé n'est pas dans l'OLV d'origine
            lstOlvDonnees=self.ctrlolv.donnees
            lstOlvCodes = self.ctrlolv.lstCodesColonnes
            ixdos,ixatel = lstOlvCodes.index('iddossier'),lstOlvCodes.index('idmatelier'),
            for ligne in lstOlvDonnees:
                valeurs = ligne.donnees
                if (self.IDdossier,idmatelier) == (valeurs[ixdos],valeurs[ixatel]):
                    unique = False
                    mess += "L'atelier %s, est déjà ouvert dans le dossier!"%(idmatelier)
        return unique, mess

    def OnComptes(self,event):
        wx.MessageBox('En projet une liste de comptes à cocher!!\n pour une saisie en rafale des affectations...')
        event.Skip()

    def OnChildBtnAction(self, event):
        # relais des actions sur les boutons du bas d'écran
        self.action = 'self.%s(event)' % event.EventObject.actionBtn
        try:
            eval(self.action)
        except Exception as err:
            wx.MessageBox(
                "Echec sur lancement action sur btn: '%s' \nLe retour d'erreur est : \n%s" % (self.action, err))

    def OnChildCtrlAction(self, event):
        # relais des actions sur les boutons de droite
        self.action = 'self.%s(event)' % event.EventObject.actionCtrl
        try:
            eval(self.action)
        except Exception as err:
            wx.MessageBox(
                "Echec sur lancement action sur ctrl: '%s' \nLe retour d'erreur est : \n%s" % (self.action, err))

class Produits():
    def __init__(self, parent,visu=True):
        self.title = '[UTIL_affectations].Produits'
        self.table = '_Produits'
        self.visu = visu
        self.mess = ''
        self.clic = None
        self.parent = parent
        self.IDdossier = parent.IDdossier

        # pointeur de la base principale ( ouverture par défaut de db_prim via xGestionDB)
        self.DBsql = self.parent.DBsql
        self.retour = self.EcranProduits()

    def EcranProduits(self,ixsel=0):
        champsRequete = "IDdossier,IDmatelier,IDmproduit,nomProduitDef,nomProduit,moisRecolte,prodPrincipalDef,surfaceProd,uniteSau,\
        comptes,quantite,uniteQte,ventes,achatAnmx,deltaStock,autreProd,prodPrincipal,TypesProduit,NoLigne,StockFin,Effectif"
        self.lstCodesRequete = [xusp.SupprimeAccents(x) for x in champsRequete.split(',')]
        # appel des produits utilisés dans le dossier pour affichage en tableau
        req = """SELECT _Produits.IDdossier,_Produits.IDMatelier, _Produits.IDMproduit, mProduits.NomProduit, _Produits.NomProdForcé, 
                        mProduits.MoisRécolte, mProduits.ProdPrincipal, _Produits.SurfaceProd, mProduits.UniteSAU,
                        _Produits.Comptes, _Produits.Quantité1, mProduits.UnitéQté1, _Produits.Ventes, 
                        _Produits.AchatAnmx, _Produits.DeltaStock, _Produits.AutreProd, _Produits.ProdPrincipal, 
                        _Produits.TypesProduit, _Produits.NoLigne,_Produits.StockFin, _Produits.EffectifMoyen
                FROM _Produits 
                INNER JOIN mProduits ON (_Produits.IDMproduit = mProduits.IDMproduit) 
                            AND (_Produits.IDMatelier = mProduits.IDMatelier)
                WHERE _Produits.IDdossier = %s
                ;""" % (self.IDdossier)
        retour = self.DBsql.ExecuterReq(req, mess='Util_affectations.ListeProduits')
        if retour == "ok":
            recordset = self.DBsql.ResultatReq()
            if len(recordset) == 0:
                wx.MessageBox("Remarque: %s" %"aucun produit n'est encore affecté")
        if (not retour == "ok"):
            wx.MessageBox("Erreur : %s" % retour)
            return 'ko'

        lstNomsColonnes = ["ix","IDdossier","Atelier","Produit","Désignation","MoisRecolte","Principal",
                           "SurfaceProd","UniteSAU","Comptes","Quantité","Unité","Production","Types",
                           "NoLigne","StockFin","Effectif"]
        # la listes ChampsColonnes permet de faire le lien avec la table d'origine en modification
        lstChampsColonnes = ["ix","IDdossier", "IDMatelier", "IDMproduit", "nomProdCompos", "MoisRécolte", "ProdPrincipal",
                             "SurfaceProd","UnitéSau","Comptes", "Quantité1", "UnitéQté1", "Product", "TypesProduit",
                             "NoLigne", "StockFin","EffectifMoyen"]
        lstCodesColonnes = [xusp.SupprimeAccents(x) for x in lstChampsColonnes]

        lstValDefColonnes = [0,0,"","","",0,0,0.0,"",
                           "",0.0,"",0.0,"",0,0.0,0.0]
        lstLargeurColonnes = [0,0,60,60,60,60,60,60,60,
                           280,-1,60,-1,100,60,-1,-1]
        lstDonnees = []
        ix=0
        # composition des données du tableau à partir du recordset
        for IDdossier,IDmatelier,IDmproduit,nomProduitDef,nomProduit,moisRecolte,prodPrincipalDef,surfaceProd,uniteSau,\
            comptes,quantite,uniteQte,ventes,achatAnmx,deltaStock,autreProd,prodPrincipal,\
            TypesProduit,NoLigne,StockFin,Effectif in recordset:
            product = 0.0
            # calcul du produit
            for prod in [ventes,achatAnmx,deltaStock,autreProd]:
                product += xfmt.Nz(prod)
            product = round(product,2)
            if not nomProduit: nomProduit = nomProduitDef
            if not prodPrincipal: prodPrincipal = prodPrincipalDef
            lstDonnees.append([ix,IDdossier,IDmatelier,IDmproduit,nomProduit,moisRecolte,prodPrincipal,surfaceProd,uniteSau,
                               comptes,quantite,uniteQte,product,TypesProduit,NoLigne,StockFin,Effectif])
            ix += 1
        # matrice OLV
        lstColonnes = xusp.DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)
        dicOlv = {
            'lanceur': self,
            'listeColonnes': lstColonnes,
            'listeDonnees': lstDonnees,
            'checkColonne': False,
            'hauteur': 650,
            'largeur': 1300,
            'recherche': True,
            'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
            'dictColFooter': {"idmproduit": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                              }
        }

        # options d'enrichissement de l'écran DLG
        lstBtns = [('BtnOK', wx.ID_OK, wx.Bitmap("xpy/Images/100x30/Bouton_fermer.png", wx.BITMAP_TYPE_ANY),
                    "Cliquez ici pour fermer la fenêtre")]
        # params d'actions: idem boutons, ce sont des boutons placés à droite et non en bas
        lstActions = [('ajout', wx.ID_APPLY, 'Ajouter', "Ajouter un nouveau produit dans le dossier"),
                      ('modif', wx.ID_APPLY, 'Modifier', "Modifier les propriétés du produit pour le dossier"),
                      ('suppr', wx.ID_APPLY, 'Supprimer', "Supprimer le produit dans le dossier"),
                      ]
        # un param par info: texte ou objet window.  Les infos sont  placées en bas à gauche
        self.trace = self.parent.trace + " - PRODUITS OUVERTS"
        self.infos = self.parent.infos
        lstInfos = [self.infos, self.trace]
        # params des actions ou boutons: name de l'objet, fonction ou texte à passer par eval()
        dicOnClick = {
            'ajout': 'self.lanceur.OnAjouter()',
            'modif': 'self.lanceur.OnModif()',
            'suppr': 'self.lanceur.OnSupprimer()'}
        self.dlgolv = xgt.DLG_tableau(self, dicOlv=dicOlv, lstBtns=lstBtns, lstActions=lstActions, lstInfos=lstInfos,
                                      dicOnClick=dicOnClick)

        # l'objet ctrlolv pourra être appelé, il sert de véhicule à params globaux de l'original
        lstChamps, lstTypes, lstHelp = dtt.GetChampsTypes(self.table, tous=True)
        self.ctrlolv = self.dlgolv.ctrlOlv
        self.ctrlolv.lstTblHelp = lstHelp
        self.ctrlolv.lstTblChamps = lstChamps
        self.ctrlolv.lstTblCodes = [xusp.SupprimeAccents(x) for x in lstChamps]
        self.ctrlolv.lstTblValdef = ValeursDefaut(lstChamps,lstChamps,lstTypes)
        self.ctrlolv.recordset = recordset
        if len(lstDonnees) > 0:
            # selection de la première ligne
            self.ctrlolv.SelectObject(self.ctrlolv.donnees[0])
        ret = wx.ID_OK
        if len(lstDonnees)>0:
            # selection de la première ligne ou du pointeur précédent
            self.ctrlolv.SelectObject(self.ctrlolv.donnees[ixsel])
        if self.visu:
            ret = self.dlgolv.ShowModal()
        return ret

    def OnModif(self):
        self.AppelSaisie('modif')

    def OnAjouter(self):
        self.AppelSaisie('ajout')
        self.Reinit()

    def OnSupprimer(self):
        self.AppelSaisie('suppr')

    def Reinit(self):
        ix = self.ixsel
        self.dlgolv.Close()
        del self.ctrlolv
        self.EcranProduits(ixsel = ix)

    def AppelSaisie(self, mode):
        ctrlolv = self.ctrlolv

        # personnalisation de la grille de saisie : champs à visualiser, position
        champdeb = 'IDMatelier'
        champfin = 'NoLigne'
        lstTblChamps = dtt.GetChamps(self.table, tous=True)
        lstEcrChamps = xusp.ExtractList(lstTblChamps,champdeb,champfin)
        lstEcrCodes = [xgl.SupprimeAccents(x) for x in lstEcrChamps]

        kwds = {'pos': (350, 20)}
        kwds['minSize'] = (350, 600)
        all = ctrlolv.innerList
        selection = ctrlolv.Selection()
        if len(selection)>0:
            self.ixsel = all.index(selection[0])
        else: self.ixsel = 0

        # personnalisation des actions
        dicOptions = {'idmatelier': {'enable': False, },
                    'idmproduit': {'enable': False, },
                    'comptes': {'enable': False, },
                    'ventes': {'enable': False, },
                    'achatanmx': {'enable': False, },
                    'deltastock': {'enable': False, },
                    'autreprod': {'enable': False, },
                    'stockfin': {'enable': False, },
                    }
        if mode == 'ajout':
            lstAteliers = AteliersOuverts(self.IDdossier,self.DBsql)
            if len(lstAteliers) == 0:
                wx.MessageBox("Aucun atelier ouvert!/nL'affectation d'un produit doit se faire sur un atelier ouvert.")
                return
            if len(selection)>0:
                idmatelier = selection[0].idmatelier
            else:
                idmatelier = lstAteliers[0]
            lstProduits = ProduitsFermes(self.IDdossier, idmatelier, self.DBsql)

            dicOptions['idmatelier']={'genre':'enum',
                                      'values': lstAteliers,
                                      'enable':True,
                                      'help': "Choisissez un atelier ouvert",
                                      'ctrlAction': 'OnChoixAtelier',
                                      }
            dicOptions['idmproduit']={'genre':'enum',
                                    'values': lstProduits,
                                    'enable':True,
                                    'help': "Choisissez un produit à ouvrir",
                                    }

        # lancement de l'écran de saisie
        lstcle = [('IDdossier',self.IDdossier)]
        self.saisie = xgl.Gestion_ligne(self, self.DBsql, self.table, dtt, mode, ctrlolv,lstcle,**kwds)
        if self.saisie.ok and mode != 'suppr':
            self.saisie.SetBlocGrille(lstEcrCodes,dicOptions,'Gestion des produits ouverts')
            if mode == 'ajout':
                # RAZ de toutes les données
                self.saisie.dictDonnees = {}
            self.saisie.InitDlg()
        del self.saisie

    def Validation(self,valeurs):
        # test de sortie d'écran
        messfinal = "Validation de la saisie\n\nFaut-il forcer l'enregistrement mal saisi?\n"
        retfinal = True
        # l'ensemble des traitements de sortie sont dans une liste déroulée à programmer ici
        for item in [self.VerifCleUnique(valeurs),]:
            ret,mess = item
            messfinal += "\n%s"%mess
            #une seule erreur provoquera l'affichage de la confirmation nécessaire
            retfinal *= ret
        if not retfinal :
            retfinal = wx.YES == wx.MessageBox(messfinal,style=wx.YES_NO)
        return retfinal

    def VerifCleUnique(self,valeurs):
        mess = ''
        for categorie, dicDonnees in valeurs.items():
            idmatelier = dicDonnees['idmatelier']
            idmproduit = dicDonnees['idmproduit']
        unique = True
        if len(idmatelier) * len(idmproduit) == 0:
            # les champs sont-ils renseignés (ont des longueurs non nulles)
            unique = False
            mess += "Il faut choisir obligatoirement un atelier et un produit dans les possibles"
        if not self.saisie.mode in ['modif','consult']:
            # on continue en vérifiant si la clé n'est pas dans l'OLV d'origine
            lstOlvDonnees=self.ctrlolv.donnees
            lstOlvCodes = self.ctrlolv.lstCodesColonnes
            ixdos,ixatel,ixprod = lstOlvCodes.index('iddossier'),lstOlvCodes.index('idmatelier'),lstOlvCodes.index('idmproduit'),
            for ligne in lstOlvDonnees:
                valeurs = ligne.donnees
                if (self.IDdossier,idmatelier,idmproduit) == (valeurs[ixdos],valeurs[ixatel],valeurs[ixprod]):
                    unique = False
                    mess += "Le produit %s de l'atelier %s, est déjà ouvert dans le dossier!"%(idmproduit,idmatelier)
        return unique, mess

    def OnChoixAtelier(self,event):
        # un atelier différent à été choisi, il faut réactualiser les produits possibles
        selection = self.ctrlolv.Selection()[0]
        # la selection est celle d' l'OLV parent qui doit être rafraichie avec la nvle donnée
        idmatelier = self.saisie.dlg.pnl.GetOneValue('idmatelier')
        ixcol = self.ctrlolv.lstCodesColonnes.index('idmatelier')
        selection.donnees[ixcol] = idmatelier
        selection.idmatelier = idmatelier
        # raz du produit qui ne correspond plus
        ixcol = self.ctrlolv.lstCodesColonnes.index('idmproduit')
        selection.donnees[ixcol] = ''
        selection.idmproduit = ''
        # réinitialisation de l'écran de saisie par envoi d'une setOneValues pour les items d'une combo
        valuesProduits = ProduitsFermes(self.IDdossier,idmatelier,self.DBsql)
        for (cdcateg,nmcateg),lstlignes in self.saisie.dictMatrice.items():
            for dicligne in lstlignes:
                if dicligne['name'] == 'idmproduit':
                    ddDonnees={cdcateg:{'idmproduit':valuesProduits}}
                    break
        self.saisie.dlg.pnl.SetOneValues(ddDonnees)
        self.saisie.dlg.pnl.Refresh()
        event.Skip()

    def OnChildBtnAction(self, event):
        # relais des actions sur les boutons du bas d'écran
        self.action = 'self.%s(event)' % event.EventObject.actionBtn
        try:
            eval(self.action)
        except Exception as err:
            wx.MessageBox(
                "Echec sur lancement action sur btn: '%s' \nLe retour d'erreur est : \n%s" % (self.action, err))

    def OnChildCtrlAction(self, event):
        # relais des actions sur les boutons de droite
        self.action = 'self.%s(event)' % event.EventObject.actionCtrl
        try:
            eval(self.action)
        except Exception as err:
            wx.MessageBox(
                "Echec sur lancement action sur ctrl: '%s' \nLe retour d'erreur est : \n%s" % (self.action, err))

class Affectations():
    def __init__(self,annee=None, client=None, groupe=None, filiere=None, agc='ANY'):
        self.title = '[UTIL_affectations].Affectations'
        self.mess = ''
        self.trace = ''
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

        # IDdossier,agc,exploitation,cloture,nomExploitation,valide,nbreMois,fiscal,ventes,caNonAff,nbElemCar,elemCar,filieres,productions
        req = """
                SELECT _Ident.IDdossier, _Ident.IDagc, _Ident.IDexploitation, _Ident.Clôture, _Ident.NomExploitation, _Ident.Validé,
                _Ident.NbreMois, _Ident.Fiscal,Sum(_Balances.SoldeFin), Sum(((_Balances.affectation="") * _Balances.SoldeFin)),
                _Ident.NbElemCar,_Ident.ElemCar, _Ident.Filières, _Ident.Productions
                FROM _Ident 
                LEFT JOIN _Balances ON _Ident.IDdossier = _Balances.IDdossier
                WHERE (((Left(_Ident.Clôture,4)) = '%s')
                        AND (_Balances.Compte Like '70%%'))
                        AND (_Ident.IDexploitation In (%s))
                GROUP BY _Ident.IDdossier, IDagc, IDexploitation,Clôture, NomExploitation,Validé,
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
        lstNomsColonnes = ["ID","agc","Noclient","Clôture","nomExploitation","validé","nbreMois","fiscal","ventes",
                           "%affecté","nbElem","Element","Vtes/Elem","filières","productions"]
        lstCodesColonnes = [xusp.SupprimeAccents(x) for x in lstNomsColonnes]

        lstValDefColonnes = [0,"","",datetime.date(1900,1,1),"",0,0,"",0.0,
                           0.0,0,"",0.0,"",""]
        lstLargeurColonnes = [0,40,40,70,120,40,40,40,40,
                           40,40,50,40,180,180]
        lstDonnees = []
        for IDdossier,IDagc,exploitation,cloture,nomExploitation,valide,nbreMois,fiscal,ventes,caNonAff,nbElemCar,elemCar,filieres,\
            productions in recordset:
            affecT = round(100*(ventes-caNonAff)/ventes)
            if not nbElemCar : nbElemCar = 0.0
            if nbElemCar != 0.0:
                rendement = -ventes / nbElemCar
            else: rendement = 0.0
            dtcloture = xfmt.DateSqlToDatetime(cloture)
            lstDonnees.append([IDdossier,IDagc,exploitation,dtcloture,nomExploitation,valide,nbreMois,fiscal,-ventes,affecT,
                               nbElemCar,elemCar,rendement,filieres,productions])

        messBasEcran = "Nbre de dossiers présents: %d "%len(lstDonnees)
        if self.topwin:
            self.topWindow.SetStatusText(messBasEcran)
        # matrice OLV
        lstColonnes = xusp.DefColonnes(lstNomsColonnes,lstCodesColonnes,lstValDefColonnes,lstLargeurColonnes)
        # forcer l'alignement à droite des production pour éviter le titre
        colonneprod = lstColonnes[-1]
        colonneprod.stringConverter = Tronque35
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
                      ('produits',wx.ID_APPLY,'Produits\ndu dossier',"Cliquez ici pour gérer les produits ouverts dans le dossier"),]
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
        self.ctrlolv.Bind(wx.EVT_LIST_ITEM_SELECTED,self.OnSelection)

        if len(lstDonnees) > 0:
            # selection de la première ligne
            self.dlgdossiers.ctrlOlv.SelectObject(self.dlgdossiers.ctrlOlv.donnees[0])
            self.IDdossier = self.ctrlolv.Selection()[0].id
        ret = self.dlgdossiers.ShowModal()
        return ret

    def EcranIdent(self,ctrlolv,mode):
        # affichage d'une ligne en vue de modif, toutes les colonnes ne sont pas reprises
        # appel d'un dossier pour affichage table ident
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
        self.ctrlolv.lstTblCodes = [xusp.SupprimeAccents(x) for x in lstChamps]
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
                                           pos=(300,10),minSize=(400,700))
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

    def OnSelection(self,event):
        self.IDdossier = self.ctrlolv.Selection()[0].id

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
            Ateliers(self)
            self.ctrlolv.SetFocus()
            self.ctrlolv.SelectObject(self.dlgdossiers.ctrlOlv.donnees[self.ixsel])

    def OnProduits(self):
        if VerifSelection(self,self.dlgdossiers):
            Produits(self)
            self.ctrlolv.SetFocus()
            self.ctrlolv.SelectObject(self.dlgdossiers.ctrlOlv.donnees[self.ixsel])


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

