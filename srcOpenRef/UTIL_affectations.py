#!/usr/bin/env python
# -*- coding: utf8 -*-

#------------------------------------------------------------------------
# Application :    OpenRef, Gestion des affectations
# Auteurs:          Jacques BRUNEL
# Copyright:       (c) 2019-05     Cerfrance Provence
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import srcOpenRef.UTIL_analyses as orua
import srcOpenRef.UTIL_import as orui
import srcOpenRef.UTIL_traitements as orut
import xpy.xGestionDB as xdb
import srcOpenRef.DATA_Tables as dtt
from xpy.outils.ObjectListView import ColumnDefn

class Affectations():
    def __init__(self,annee=None, client=None, groupe=None, filiere=None, agc='ANY'):
        self.title = '[UTIL_affectations].Affectations'
        self.mess = ''
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
            lstDossiers = orua.GetExercicesClient(agc,client,annee,0,self.DBsql,saufvalide=False)
        elif groupe:
            lstDossiers=orua.GetClientsGroupes(agc, groupe, annee, 0, self.DBsql,saufvalide=False)
        elif filiere:
            lstDossiers = orua.GetClientsFilieres(agc, filiere, annee, 0, self.DBsql,saufvalide=False)
        else :
            wx.MessageBox("Analyse : Aucun paramètre de lancement ne concerne un dossier")
            return

        # déroulé du traitement
        ret = self.EcranDossiers(lstDossiers,annee)

    def EcranDossiers(self,lstDossiers,annee):
        # appel des dossiers pour affichage
        lstClients = []
        for agc,client,cloture in lstDossiers:
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
                ;"""%(str(annee),str(lstClients)[1:-1])
        retour = self.DBsql.ExecuterReq(req, mess='Util_affectations.EcranDossiers')
        if retour == "ok":
            recordset = self.DBsql.ResultatReq()
        else :
            wx.MessageBox("Erreur : %s"%retour)
            return 'ko'
        lstDonnees = []
        for IDdossier,IDagc,exploitation,cloture,nomExploitation,nbreMois,fiscal,ventes,caNonAff,nbElemCar,elemCar,filieres,\
            productions in recordset:
            affecT = round(100*(ventes-caNonAff)/ventes)
            if not nbElemCar : nbElemCar = 0.0
            if nbElemCar != 0.0:
                rendement = ventes / nbElemCar
            else: rendement = 0.0
            lstDonnees.append([IDdossier,agc,exploitation,cloture,nomExploitation,nbreMois,fiscal,ventes,affecT,
                               nbElemCar,elemCar,rendement,filieres,productions])
        messBasEcran = "Nbre de dossiers présents: %d "%len(lstDonnees)
        if self.topwin:
            self.topWindow.SetStatusText(messBasEcran)
        # matrice OLV
        lstColonnes = [
            ColumnDefn("clé", 'left', 70, "cle", valueSetter=1),
            ColumnDefn("mot d'ici", 'left', 200, "mot", valueSetter=''),
            ColumnDefn("nombre_", 'right', 80, "nombre", valueSetter=0.0,
                       stringConverter=xpy.outils.xformat.FmtDecimal),
            ColumnDefn("prix", 'right', 80, "prix", valueSetter=0.0, stringConverter=xpy.outils.xformat.FmtMontant),
            ColumnDefn("date", 'center', 80, "date", valueSetter=wx.DateTime.FromDMY(1, 0, 1900),
                       stringConverter=xpy.outils.xformat.FmtDate),
            ColumnDefn("date SQL", 'center', 80, "datesql", valueSetter='2000-01-01',
                       stringConverter=xpy.outils.xformat.FmtDate)
        ]
        dicOlv = {'listeColonnes': lstColonnes,
                  'listeDonnees': lstDonnees,
                  'hauteur': 650,
                  'largeur': 850,
                  'recherche': True,
                  'msgIfEmpty': "Aucune donnée ne correspond à votre recherche",
                  'dictColFooter': {"nombre": {"mode": "total", "alignement": wx.ALIGN_RIGHT},
                                    "mot": {"mode": "nombre", "alignement": wx.ALIGN_CENTER},
                                    "prix": {"mode": "total", "alignement": wx.ALIGN_RIGHT}, }
                  }

        # options d'enrichissement de l'écran
        # params d'un bouton : name, ID, Image ou label, tooltip
        lstBtns = [('BtnPrec', wx.ID_FORWARD, wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_OTHER, (42, 22)),
                    "Cliquez ici pour retourner à l'écran précédent"),
                   ('BtnPrec2', wx.ID_PREVIEW_NEXT, "Ecran\nprécédent", "Retour à l'écran précédent next"),
                   ('BtnOK', wx.ID_OK, wx.Bitmap("xpy/Images/100x30/Bouton_fermer.png", wx.BITMAP_TYPE_ANY),
                    "Cliquez ici pour fermer la fenêtre")]
        # params d'actions: idem boutons, ce sont des boutons placés à droite et non en bas
        lstActions = [('Action1', wx.ID_COPY, 'Choix un', "Cliquez pour l'action 1"),
                      ('Action2', wx.ID_CUT, 'Choix deux', "Cliquez pour l'action 2")]
        # un param par info: texte ou objet window.  Les infos sont  placées en bas à gauche
        lstInfos = ['Première', "Voici", wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)),
                    "Autre\nInfo"]
        # params des actions ou boutons: name de l'objet, fonction ou texte à passer par eval()
        dicOnClick = {'Action1': lambda evt: wx.MessageBox('ceci active la fonction action1'),
                      'BtnPrec': 'self.parent.Close()'}
        ecrDos = DLG_tableau(None,dicOlv=dicOlv,lstBtns= lstBtns,lstActions=lstActions,lstInfos=lstInfos,dicOnClick=dicOnClick)
        ret = ecrDos.ShowModal()


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
    fn = Affectations(annee='2018',client='009418',agc='prov')
    #fn = Affectations(annee='2018',groupe='LOT1',agc='prov')
    print('Retour: ',fn)

    app.MainLoop()

