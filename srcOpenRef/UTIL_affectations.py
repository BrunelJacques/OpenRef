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

def AteliersOuverts(parent,IDdossier,DBsql):
    lstAteliers = []
    req = """SELECT mateliers.IDMatelier
            FROM _ateliers 
            INNER JOIN mateliers ON _ateliers.IDMatelier = mateliers.IDMatelier
            WHERE (_ateliers.IDdossier = %d)
            """%IDdossier
    retour = DBsql.ExecuterReq(req, mess='Util_affectations.AteliersOuverts')
    if not retour == "ok":
        wx.MessageBox("Erreur : %s"%retour)
    else:
        recordset = DBsql.ResultatReq()
        for IDatelier in recordset:
            lstAteliers.append(IDatelier)
    return lstAteliers

def ProduitsOuverts(parent,IDdossier,DBsql):
    lstProduits = []
    req = """SELECT mproduits.IDMatelier,mproduits.IDMproduit
            FROM _produits 
            INNER JOIN mproduits ON _produits.IDMproduit = mproduits.IDMproduit
            WHERE (_produits.IDdossier = %d)
            """%IDdossier
    retour = DBsql.ExecuterReq(req, mess='Util_affectations.ProduitsOuverts')
    if not retour == "ok":
        wx.MessageBox("Erreur : %s"%retour)
    else:
        recordset = DBsql.ResultatReq()
        for IDatelier,IDproduit in recordset:
            lstProduits.append((IDatelier,IDproduit))
    return lstProduits

def CoutsOuverts(parent,IDdossier,DBsql):
    lstCouts = []
    req = """SELECT mCoûts.IDMatelier,mCoûts.IDMcoût
            FROM _Coûts 
            INNER JOIN mCoûts ON _Coûts.IDMcoût = mCoûts.IDMcoût
            WHERE (_Coûts.IDdossier = %d)
            """%IDdossier
    retour = DBsql.ExecuterReq(req, mess='Util_affectations.CoutsOuverts')
    if not retour == "ok":
        wx.MessageBox("Erreur : %s"%retour)
    else:
        recordset = DBsql.ResultatReq()
        for IDatelier,IDcout in recordset:
            lstCouts.append((IDatelier,IDcout))
    return lstCouts

def AffectsActifs(parent,IDdossier,DBsql):
    # retourne les affectations possibles (première et deuxième parties du nom)
    lstAffects = ['']
    for IDatelier in AteliersOuverts(parent,IDdossier,DBsql):
        lstAffects.append("A.%s"%IDatelier)
    for IDatelier,IDproduit in ProduitsOuverts(parent,IDdossier,DBsql):
        lstAffects.append("P.%s.%s"%(IDatelier,IDproduit))
    for IDatelier,IDproduit in CoutsOuverts(parent,IDdossier,DBsql):
        lstAffects.append("C.%s.%s"%(IDatelier,IDproduit))
    lstAffects.append("I.TabFin")
    return lstAffects

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

class EcranSaisie():
    # affichage d'une ligne de table en vue de modif, toutes les champs ne sont pas gérés dans parent
    def __init__(self,parent,ctrlolv,selection):
        #liste des champs à gérer
        lstCodes = parent.lstEcrCodes
        dictMatrice = {}
        dictDonnees = {}
        # Reprise des valeurs completes de la table
        req = """SELECT *
                FROM %s
                WHERE %s;"""%(parent.table,parent.wherecle)
        retour = parent.DBsql.ExecuterReq(req, mess='Util_affectations.EcranSaisie : %s'%parent.table)
        if retour == "ok":
            recordset = parent.DBsql.ResultatReq()
            if len(recordset) == 0:
                retour = "aucun enregistrement disponible"
        if (not retour == "ok"):
            wx.MessageBox("Erreur : %s"%retour)
            return 'ko'

        # initialisation des variables de la table affichées à l'écran
        donnees, lstNoms, lstValdef, lstHelp = [],[],[],[]
        for code in lstCodes:
            if code in ctrlolv.lstTblCodes:
                ixtbl = ctrlolv.lstTblCodes.index(code)
                valeur = recordset[0][ixtbl]
                if not valeur: valeur = ctrlolv.lstTblValdef[ixtbl]
                if code in ctrlolv.lstCodesColonnes:
                    # cas ou un traitement du parent peut avoir changé la valeur native
                    valolv = selection.donnees[ctrlolv.lstCodesColonnes.index(code)]
                    if valolv != valeur : valeur = valolv
                donnees.append(valeur)
                lstNoms.append(ctrlolv.lstTblChamps[ixtbl])
                lstValdef.append(ctrlolv.lstTblValdef[ixtbl])
                lstHelp.append(ctrlolv.lstTblHelp[ixtbl])

        # Lancement de l'écran
        param= parent.paramMatrice
        (dictMatrice[(param['cdCateg'],param['nmCateg'])],dictDonnees[param['cdCateg']]) \
            = xusp.ComposeMatrice(param['champDeb'],param['champFin'],lstNoms, lstHelp=lstHelp,record=donnees,
                                  dicOptions=parent.dicOptions,lstCodes=lstCodes)
        parent.dlg = xusp.DLG_monoLigne(parent,dldMatrice=dictMatrice,ddDonnees=dictDonnees,gestionProperty=False,
                                           pos=param['pos'],minSize=param['minSize'])
        retdlg = parent.dlg.ShowModal()
        if retdlg == 5101:
            # Retour par validation
            valeurs = parent.dlg.pnl.GetValeurs()
            # mise à jour de l'olv d'origine
            for code in lstCodes:
                for categorie, dicDonnees in parent.dlg.ddDonnees.items():
                    if code in dicDonnees and code in ctrlolv.lstCodesColonnes:
                        # pour chaque colonne de la selection de l'olv
                        valorigine = recordset[0][ctrlolv.lstTblCodes.index(code)]
                        if (not valorigine):
                            valorigine = valeurs[categorie][code]
                            flag = True
                        else : flag = False
                        if flag or (valorigine != valeurs[categorie][code]):
                            ix = ctrlolv.lstCodesColonnes.index(code)
                            selection.donnees[ctrlolv.lstCodesColonnes.index(code)] = valeurs[categorie][code]
                            if isinstance(valorigine,(str,datetime.date)):
                                action = "selection.__setattr__('%s','%s')"%(
                                            ctrlolv.lstCodesColonnes[ix],str(valeurs[categorie][code]))
                            elif isinstance(valorigine, (int, float)):
                                if valeurs[categorie][code] in (None,''):
                                    valeurs[categorie][code]='0'
                                action = "selection.__setattr__('%s',%d)" % (
                                            ctrlolv.lstCodesColonnes[ix], float(valeurs[categorie][code]))
                            else: wx.MessageBox("UTIL_Affectaions.EcranSaisie\n\n%s, type non géré pour modifs: %s"%(code,type(valorigine)))
                            eval(action)
            ctrlolv.MAJ(parent.ixsel)
            # mise à jour table de base de donnee
            lstModifs = []
            for categorie, dicdonnees in valeurs.items():
                for code,valeur in dicdonnees.items():
                    if valeur in (None,''): valeur = lstValdef[lstCodes.index(code)]
                    nom = lstNoms[lstCodes.index(code)]
                    lstModifs.append((nom,valeur))

            if len(lstModifs)>0 and parent.mode == 'modif':
                ret = parent.DBsql.ReqMAJ(parent.table,lstModifs,
                                          parent.wherecle,mess='MAJ affectations.%s.Ecran'%parent.table)
                if ret != 'ok':
                    wx.MessageBox(ret)
            if len(lstModifs) > 0 and parent.mode == 'copie':
                lstMaj,lstIns = parent.Copier(lstModifs,recordset[0])
                ret = parent.DBsql.ReqMAJ(parent.table,lstMaj,parent.wherecle,mess='MAJ affectations.%s.Ecran'%parent.table)
                if ret != 'ok': wx.MessageBox(ret)
                insChamps = [x for x,y in lstIns]
                insDonnees = [y for x,y in lstIns]
                ret = parent.DBsql.ReqInsert(parent.table, insChamps,insDonnees,mess='Insert affectations.%s.Ecran' % parent.table)
                if ret != 'ok': wx.MessageBox(ret)
        parent.ctrlolv.SetFocus()
        parent.ctrlolv.SelectObject(parent.ctrlolv.donnees[parent.ixsel])
        parent.dlg.Destroy()
        del parent.dlg

class Balance():
    def __init__(self,parent):
        self.title = '[UTIL_affectations].Balance'
        #table qui sera gérée par les actions
        self.table = '_Balances'
        self.mess = ''
        self.clic = None
        self.parent = parent
        self.IDdossier = parent.IDdossier
        self.lastAction = ''

        # pointeur de la base principale ( ouverture par défaut de db_prim via xGestionDB)
        self.DBsql = self.parent.DBsql
        self.retour = self.EcranBalance()

    def EcranBalance(self):
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
        lstActions = [('modif',wx.ID_APPLY,'Modifier',"Cliquez ici pour modifier la ligne"),
                      ('eclater',wx.ID_APPLY,'Eclater',"Cliquez ici pour subdiviser le compte"),
                      ('regrouper', wx.ID_APPLY, 'Supprimer', "Supprimer la ligne et reporter le solde dessus"),
                      ]
        # un param par info: texte ou objet window.  Les infos sont  placées en bas à gauche
        self.trace = self.parent.trace + "- BALANCE"
        self.infos = self.parent.infos
        lstInfos = [self.infos,self.trace]
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
        self.ctrlolv.lstTblCodes = [xusp.SupprimeAccents(x) for x in lstChamps]
        self.ctrlolv.lstTblValdef = ValeursDefaut(lstChamps,lstChamps,lstTypes)
        self.ctrlolv.recordset = recordset
        if len(lstDonnees)>0:
            # selection de la première ligne
            self.ctrlolv.SelectObject(self.ctrlolv.donnees[0])
        ret = self.dlgolv.ShowModal()
        return ret
        
    def AppelSaisie(self,mode):
        self.mode = mode
        ctrlolv = self.ctrlolv
        all = ctrlolv.GetObjects()
        selection = ctrlolv.Selection()[0]
        self.ixsel = all.index(selection)
        if not VerifSelection(self,self.dlgolv,infos=False):
            return
        # Spécificités écran saisie
        IDenr = "IDligne"
        ID = ctrlolv.recordset[self.ixsel][ctrlolv.lstTblChamps.index(IDenr)]
        self.wherecle = "%s = %d" %(IDenr,ID)
        valuesAffect = AffectsActifs(self,self.IDdossier,self.DBsql)
        self.dicOptions = {'affectation':{
                        'values': valuesAffect,
                        'genre': 'enum',
                        'btnLabel': "...",
                        'btnHelp': "Cliquez pour ajouter des affectations à la liste",
                        'btnAction': 'OnAjoutAffect',},
                    'soldefin': {
                        'ctrlAction': 'OnYva',}}
        champdeb = 'Compte'
        champfin = 'SoldeFin'
        codedeb = self.ctrlolv.lstCodesColonnes[self.ctrlolv.lstNomsColonnes.index(champdeb)]
        codefin = self.ctrlolv.lstCodesColonnes[self.ctrlolv.lstNomsColonnes.index(champfin)]
        self.lstEcrCodes = xusp.ExtractList(self.ctrlolv.lstCodesColonnes,codedeb,codefin)
        self.paramMatrice = {'cdCateg':'compte',"nmCateg":'DétailLigne','champDeb':champdeb,'champFin':champfin}
        self.paramMatrice['pos'] = (300, 0)
        self.paramMatrice['minSize'] = (400, 1000)

        EcranSaisie(self,self.ctrlolv,selection)

    def OnModif(self):
        self.AppelSaisie('modif')

    def OnEclater(self):
        self.AppelSaisie('copie')

    def Copier(self,lstModifs,recOrigine):
        lstIns, lstMaj = [('IDdossier',self.IDdossier)],[]
        for champ,valeur in lstModifs:
            ix = self.ctrlolv.lstTblChamps.index(champ)
            valorigine = recOrigine[ix]
            valdef = self.ctrlolv.lstTblValdef[ix]
            if not valorigine: valorigine = valdef
            if isinstance(valdef,(int,float)):
                valeur = float(valeur)
                valreste = valorigine - valeur
                if valreste < 0.0 : valreste = 0.0
                lstMaj.append((champ,valreste))
                lstIns.append((champ,valeur))
            else:
                lstMaj.append((champ,valorigine))
                lstIns.append((champ,valeur))
        return lstMaj,lstIns

    def OnRegrouper(self):
        self.AppelSaisie('del')

    def OnChildBtnAction(self,event):
        self.action = 'self.%s(event)' % event.EventObject.actionBtn
        try:
            eval(self.action)
        except Exception as err:
            wx.MessageBox("Echec sur lancement action sur btn: '%s' \nLe retour d'erreur est : \n%s"%(self.action, err))

    def OnChildCtrlAction(self,event):
        self.action = 'self.%s(event)' % event.EventObject.actionCtrl
        try:
            eval(self.action)
        except Exception as err:
            wx.MessageBox("Echec sur lancement action sur ctrl: '%s' \nLe retour d'erreur est : \n%s"%(self.action, err))

    def OnAjoutAffect(self,event):
        Produits(self)

class Produits():
    def __init__(self, parent):
        self.title = '[UTIL_affectations].Produits'
        self.table = '_Produits'
        self.mess = ''
        self.clic = None
        self.parent = parent
        self.IDdossier = parent.IDdossier
        self.lastAction = ''

        # pointeur de la base principale ( ouverture par défaut de db_prim via xGestionDB)
        self.DBsql = self.parent.DBsql
        self.retour = self.EcranProduits()

    def EcranProduits(self):
        champsRequete = "IDmatelier,IDmproduit,nomProduitDef,nomProduit,moisRecolte,prodPrincipalDef,surfaceProd,unite,\
        comptes,quantite,unite,ventes,achatAnmx,deltaStock,autreProd,prodPrincipal,TypesProduit,NoLigne,StockFin,Effectif"
        self.lstCodesRequete = [xusp.SupprimeAccents(x) for x in champsRequete.split(',')]
        # appel des produits utilisés dans le dossier pour affichage en tableau
        req = """SELECT _produits.IDMatelier, _produits.IDMproduit, mproduits.NomProduit, _produits.NomProdForcé, 
                        mproduits.MoisRécolte, mproduits.ProdPrincipal, _produits.SurfaceProd, mproduits.UniteSAU,
                        _produits.Comptes, _produits.Quantité1, mproduits.UnitéQté1, _produits.Ventes, 
                        _produits.AchatAnmx, _produits.DeltaStock, _produits.AutreProd, _produits.ProdPrincipal, 
                        _produits.TypesProduit, _produits.NoLigne,_produits.StockFin, _produits.EffectifMoyen
                FROM _produits 
                INNER JOIN mproduits ON (_produits.IDMproduit = mproduits.IDMproduit) 
                            AND (_produits.IDMatelier = mproduits.IDMatelier)
                WHERE _produits.IDdossier = %s
                ;""" % (self.IDdossier)
        retour = self.DBsql.ExecuterReq(req, mess='Util_affectations.ListeProduits')
        if retour == "ok":
            recordset = self.DBsql.ResultatReq()
            if len(recordset) == 0:
                retour = "aucun enregistrement disponible"
        if (not retour == "ok"):
            wx.MessageBox("Erreur : %s" % retour)
            return 'ko'

        lstNomsColonnes = ["ix","Atelier","Produit","NomProduit","MoisRecolte","Principal","SurfaceProd","UniteSAU",
                           "Comptes","Quantité","Unité","Production","Types","NoLigne","StockFin","Effectif"]
        # la listes ChampsColonnes permet de faire le lien avec la table d'origine en modification
        lstChampsColonnes = ["ix", "IDMatelier", "IDMproduit", "nomProdForce", "MoisRecolte", "ProdPrincipal","SurfaceProd", "UniteSau",
                            "Comptes", "Quantite1", "UniteQte1", "Product", "TypesProduit", "NoLigne", "StockFin","EffectifMoyen"]
        lstCodesColonnes = [xusp.SupprimeAccents(x) for x in lstChampsColonnes]

        lstValDefColonnes = [0,"","","",0,0,0.0,"",
                           "",0.0,"",0.0,"",0,0.0,0.0]
        lstLargeurColonnes = [0,60,60,60,60,60,60,60,
                           280,-1,60,-1,100,60,-1,-1]
        lstDonnees = []
        ix=0
        # composition des données du tableau à partir du recordset
        for IDmatelier,IDmproduit,nomProduitDef,nomProduit,moisRecolte,prodPrincipalDef,surfaceProd,unite,\
            comptes,quantite,unite,ventes,achatAnmx,deltaStock,autreProd,prodPrincipal,\
            TypesProduit,NoLigne,StockFin,Effectif in recordset:
            product = 0.0
            # calcul du produit
            for prod in [ventes,achatAnmx,deltaStock,autreProd]:
                product += xfmt.Nz(prod)
            product = round(product,2)
            if not nomProduit: nomProduit = nomProduitDef
            if not prodPrincipal: prodPrincipal = prodPrincipalDef
            lstDonnees.append([ix,IDmatelier,IDmproduit,nomProduit,moisRecolte,prodPrincipal,surfaceProd,unite,
                               comptes,quantite,unite,product,TypesProduit,NoLigne,StockFin,Effectif])
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
            'dictColFooter': {"nomexploitation": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                              }
        }

        # options d'enrichissement de l'écran de saisie
        lstBtns = [('BtnOK', wx.ID_OK, wx.Bitmap("xpy/Images/100x30/Bouton_fermer.png", wx.BITMAP_TYPE_ANY),
                    "Cliquez ici pour fermer la fenêtre")]
        # params d'actions: idem boutons, ce sont des boutons placés à droite et non en bas
        lstActions = [('ajout', wx.ID_APPLY, 'Ajouter', "Cliquez ici pour ajouter une ligne"),
                      ('modif', wx.ID_APPLY, 'Modifier', "Cliquez ici pour modifier la ligne"),
                      ('suppr', wx.ID_APPLY, 'Supprimer', "Supprimer la ligne"),
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
        ret = self.dlgolv.ShowModal()
        return ret

    def AppelSaisie(self, mode):
        self.mode = mode
        ctrlolv = self.ctrlolv
        all = ctrlolv.GetObjects()
        selection = ctrlolv.Selection()[0]
        self.ixsel = all.index(selection)
        if not VerifSelection(self, self.dlgolv, infos=False):
            return
        # Spécificités écran saisie
        IDenr1 = "idmatelier"
        ID1 = ctrlolv.recordset[self.ixsel][self.lstCodesRequete.index(IDenr1)]
        IDenr2 = "idmproduit"
        ID2 = ctrlolv.recordset[self.ixsel][self.lstCodesRequete.index(IDenr2)]
        self.wherecle = "(IDdossier = %d) AND (%s = '%s') AND (%s = '%s')" % (self.IDdossier, IDenr1, ID1, IDenr2, ID2)
        self.dicOptions = {}
        champdeb = 'NomProdForcé'
        champfin = 'NoLigne'
        codedeb = self.ctrlolv.lstTblCodes[self.ctrlolv.lstTblChamps.index(champdeb)]
        codefin = self.ctrlolv.lstTblCodes[self.ctrlolv.lstTblChamps.index(champfin)]
        self.lstEcrCodes = xusp.ExtractList(self.ctrlolv.lstTblCodes,codedeb,codefin)
        self.paramMatrice = {'cdCateg':'produit',"nmCateg":'_Produit','champDeb':champdeb,'champFin':champfin}
        self.paramMatrice['pos'] = (350, 100)
        self.paramMatrice['minSize'] = (300, 400)
        retour = EcranSaisie(self, self.ctrlolv, selection)


    def OnModif(self):
        self.AppelSaisie('modif')

    def OnAjouter(self):
        self.AppelSaisie('ajout')

    def OnSupprimer(self):
        self.AppelSaisie('del')

    def OnChildBtnAction(self, event):
        self.action = 'self.%s(event)' % event.EventObject.actionBtn
        try:
            eval(self.action)
        except Exception as err:
            wx.MessageBox(
                "Echec sur lancement action sur btn: '%s' \nLe retour d'erreur est : \n%s" % (self.action, err))

    def OnChildCtrlAction(self, event):
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
            self.IDdossier = self.dlgdossiers.ctrlOlv.Selection()[0].id
            wx.MessageBox('clic sur ateliers')

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

