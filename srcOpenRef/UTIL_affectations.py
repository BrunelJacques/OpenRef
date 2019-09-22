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
import unicodedata
import srcOpenRef.UTIL_analyses as orua
import srcOpenRef.UTIL_traitements as orut
import srcOpenRef.DATA_Tables as dtt
import xpy.xGestionDB as xdb
import xpy.outils.xformat as xfmt
import xpy.xUTILS_SaisieParams as xusp
import xpy.xGestion_Tableau as xgt
from xpy.outils.ObjectListView import ColumnDefn

def DefColonnes(lstNoms,lstCodes,lstValDef,lstLargeur):
    ix=0
    lstColonnes = []
    for colonne in lstNoms:
        if isinstance(lstValDef[ix],(str,wx.DateTime)):
            posit = 'left'
        else: posit = 'right'
        # ajoute un converter à partir de la valeur par défaut
        if isinstance(lstValDef[ix], (float,)):
            if '%' in colonne:
                stringConverter = xfmt.FmtPercent
            else:
                stringConverter = xfmt.FmtInt
        elif isinstance(lstValDef[ix], int):
            stringConverter = xfmt.FmtInt
        #elif isinstance(lstValDef[ix], datetime.date):
        #    stringConverter = xfmt.FmtDate
        else: stringConverter = None
        lstColonnes.append(ColumnDefn(colonne, posit, lstLargeur[ix],lstCodes[ix], valueSetter=lstValDef[ix],
                                      stringConverter=stringConverter))
        ix +=1
    return lstColonnes

def DateSqlToWxdate(dateEng):
    if dateEng == None : return None

    if isinstance(dateEng,datetime.date):
        return wx.DateTime.FromDMY(dateEng.day,dateEng.month-1,dateEng.year)

    if isinstance(dateEng,str) and len(dateEng) < 10:
        return wx.DateTime.FromDMY(int(dateEng[8:10]),int(dateEng[5:7]-1),int(dateEng[:4]))

def DateSqlToDatetime(dateEng):
    if dateEng == None : return None

    if isinstance(dateEng,datetime.date):
        return dateEng

    if isinstance(dateEng,str) and len(dateEng) < 10:
        return datetime(int(dateEng[:4]),int(dateEng[5:7]),int(dateEng[8:10]))

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
        self.Traitement()

    def Traitement(self):
        # déroulé du traitement, navigation dans le écrans
        self.retour = self.EcranDossiers()

    def ComposeMatrice(self,lstChamps,lstTypes,lstHelp=None,champdeb=None,champfin=None):
        ldmatrice = []
        if champdeb:
            ix1= lstChamps.index(champdeb)
        else: ix1 = 0
        if champfin:
            ix2= lstChamps.index(champfin)
        else: ix2 = len(lstChamps)-1
        for ix in range(ix1,ix2):
            code = ''.join(c for c in unicodedata.normalize('NFD', lstChamps[ix]) if unicodedata.category(c) != 'Mn')
            code = code.lower()
            dicchamp = {
            'genre': lstTypes[ix],
            'name': code,
            'label': lstChamps[ix],
            'help': lstHelp[ix]
                       }
            ldmatrice.append(dicchamp)
        return ldmatrice

    def ComposeDonnees(self,recordset0,lstChamps,champdeb=None,champfin=None):
        lddonnees = []
        if champdeb:
            ix1= lstChamps.index(champdeb)
        else: ix1 = 0
        if champfin:
            ix2= lstChamps.index(champfin)
        else: ix2 = len(lstChamps)-1
        dicdonnees={}
        for ix in range(ix1,ix2):
            code = ''.join(c for c in unicodedata.normalize('NFD', lstChamps[ix]) if unicodedata.category(c) != 'Mn')
            code = code.lower()
            dicdonnees[code] = recordset0[ix]
            lddonnees.append(dicdonnees)
        return lddonnees

    def EcranDossiers(self):
        # appel des dossiers pour affichage
        lstClients = []
        for agc,client,cloture in self.lstDossiers:
            lstClients.append(client)

        # IDdossier,agc,exploitation,cloture,nomExploitation,nbreMois,fiscal,ventes,caNonAff,nbElemCar,elemCar,filieres,productions
        req = """
                SELECT _ident.IDdossier, _ident.IDagc, _ident.IDexploitation, _ident.Clôture, _ident.NomExploitation, 
                _ident.NbreMois, _ident.Fiscal,Sum(_balances.SoldeFin), Sum(((_balances.affectation="") * _balances.SoldeFin)),
                _ident.NbElemCar,_ident.ElemCar, _ident.Filières, _ident.Productions
                FROM _ident 
                LEFT JOIN _balances ON _ident.IDdossier = _balances.IDdossier
                WHERE (((Left(_ident.Clôture,4)) = '%s')
                        AND (_balances.Compte Like '70%%'))
                        AND (_ident.IDexploitation In (%s))
                GROUP BY _ident.IDdossier, IDagc, IDexploitation,Clôture, NomExploitation,
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
        lstNomsColonnes = ["ID","agc","noClient","clôture","nomExploitation","nbreMois","fiscal","ventes",
                           "% affecté","nbElemCar","elemCar","rendement","filières","productions"]
        lstCodesColonnes = ["ID","agc","noclient","cloture","nomexploitation","nbremois","fiscal","ventes",
                           "affect","nbelemCar","elemCar","rendement","filieres","productions"]
        lstValDefColonnes = [0,"","",datetime.date(1900,1,1),"",0,"",0.0,
                           0.0,0,"",0.0,"",""]
        lstLargeurColonnes = [0,40,50,70,120,40,40,70,
                           40,40,50,70,180,180]
        lstDonnees = []
        for IDdossier,IDagc,exploitation,cloture,nomExploitation,nbreMois,fiscal,ventes,caNonAff,nbElemCar,elemCar,filieres,\
            productions in recordset:
            affecT = round(100*(ventes-caNonAff)/ventes)
            if not nbElemCar : nbElemCar = 0.0
            if nbElemCar != 0.0:
                rendement = -ventes / nbElemCar
            else: rendement = 0.0
            lstDonnees.append([IDdossier,IDagc,exploitation,DateSqlToDatetime(cloture),nomExploitation,nbreMois,fiscal,-ventes,affecT,
                               nbElemCar,elemCar,rendement,filieres,productions])

        messBasEcran = "Nbre de dossiers présents: %d "%len(lstDonnees)
        if self.topwin:
            self.topWindow.SetStatusText(messBasEcran)
        # matrice OLV
        lstColonnes = DefColonnes(lstNomsColonnes,lstCodesColonnes,lstValDefColonnes,lstLargeurColonnes)
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
        self.dlg = xgt.DLG_tableau(self,dicOlv=dicOlv,lstBtns= lstBtns,lstActions=lstActions,lstInfos=lstInfos,
                                 dicOnClick=dicOnClick)
        ret = self.dlg.ShowModal()
        print("retour ecran: ",ret)
        self.dlg.Destroy()
        return wx.ID_OK

    def EcranIdent(self):
        # appel d'un dossier pour affichage table ident
        req = """
                SELECT *
                FROM _ident 
                WHERE (_ident.IDdossier = %s)
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
        dictDonnees = {}
        dictMatrice = {}
        dictMatrice['params',None]=self.ComposeMatrice(lstChamps,lstTypes,lstHelp=lstHelp,champdeb='IDjuridique',champfin='ImpSoc')
        dictDonnees['params',None]=self.ComposeDonnees(recordset[0],lstChamps,champdeb='IDjuridique',champfin='ImpSoc')
        dictMatrice['tabfin',None]=self.ComposeMatrice(lstChamps,lstTypes,lstHelp=lstHelp,champdeb='Caf',champfin='RemAssociés')
        dictDonnees['tabfin',None]=self.ComposeDonnees(recordset[0],lstChamps,champdeb='Caf',champfin='RemAssociés')
        dictMatrice['divers',None]=self.ComposeMatrice(lstChamps,lstTypes,lstHelp=lstHelp,champdeb='Productions')
        dictDonnees['divers',None]=self.ComposeDonnees(recordset[0],lstChamps,champdeb='Productions')

        self.dlg = xusp.DLG_monoLigne(None,dldMatrice=dictMatrice,lddDonnees=[dictDonnees],gestionProperty=False,minSize=(1200,500))
        ret = self.dlg.ShowModal()
        print("retour ecran: ",ret)
        #self.dlg.Destroy()
        return wx.ID_OK

    def CtrlSelection(self):
        if len(self.dlg.ctrlOlv.Selection())==0:
            wx.MessageBox("Action Impossible\n\nVous n'avez pas selectionné une ligne!","Préalable requis")
            return False
        return True

    def OnIdent(self):
        if self.CtrlSelection():
            self.IDdossier = self.dlg.ctrlOlv.Selection()[0].ID
            self.EcranIdent()

    def OnBalance(self):
        if self.CtrlSelection():
            wx.MessageBox('clic sur balance')

    def OnAteliers(self):
        if self.CtrlSelection():
            wx.MessageBox('clic sur ateliers')

    def OnProduits(self):
        if self.CtrlSelection():
            wx.MessageBox('clic sur produits')

    def Init_dic_produit(self,produit):
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


#************************   Pour Test ou modèle  *********************************
if __name__ == '__main__':
    app = wx.App(0)
    import os
    os.chdir("..")
    #fn = Affectations(annee='2018',client='009418',agc='prov')
    fn = Affectations(annee=2018,groupe='testAlpes',agc='ANY')
    ret = fn.retour
    print('Retour appli: ',ret)

    app.MainLoop()

