#!/usr/bin/env python
# -*- coding: utf8 -*-

#------------------------------------------------------------------------
# Application :    OpenRef, Génération des exports d'analyses
# Auteurs:          Jacques BRUNEL
# Copyright:       (c) 2019-05     Cerfrance Provence
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import xpy.xGestionDB as xdb
import srcOpenRef.DATA_Tables as dtt
import unicodedata

CHAMPS_TABLES = {
    '_Ident' : ['IDdossier','IDagc','IDexploitation','Clôture','IDuser','IDlocalisation','IDjuridique','NomExploitation',
                'IDCodePostal','Siren','IDnaf','Filières','NbreMois','Fiscal','ImpSoc','Caf','SubvReçues','Cessions',
                'NvxEmprunts','Apports','Investissements','RbtEmprunts','Prélèvements','RemAssociés','Productions',
                'Analyse','Remarques','SAUfermage','SAUmétayage','SAUfvd','SAUmad','SAU','NbreAssociés',
                'MOexploitants','MOpermanents','MOsaisonniers','NbElemCar','ElemCar','Analytique','Validé'],
    '_Infos' : ['IDdossier','IDMinfo','Numerique','Bool','Texte'],
    '_Balances':['IDdossier','Compte','IDligne','Libellé','MotsCléPrés','Quantités1','Unité1','Quantités2','Unité2',
                 'SoldeDeb','DBmvt','CRmvt','SoldeFin','IDplanCompte','Affectation'],
    'wVariables':[ 'Ordre','Colonne','Code','Libelle','Type','Fonction','Param','Atelier','Produit','Observation'],
    }

def DecoupeParam(texte):
    # isole les mots ou filtres du texte comme paramètres de fonctions Produits ou Coûts
    # lstFiltres est une liste de tuples (type,listeMotsFiltrés)
    lstNoms = []
    lstFiltres = []
    if texte and len(texte)>0:
        # suppression des accents, forcé en minuscule, normalisé
        texte = ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')
        texte = texte.lower()
        texte = texte.replace('[','(')
        texte = texte.replace(']',')')
        texte = texte.replace("'","")
        texte = texte.strip()
        # des parenthèses externes sont supprimées
        if texte[0] == '(' and texte[-1] == ')': texte = texte[1:-1]
        expression = str(texte)
        # différentiation d'un séparateur dans et hors parenthèses internes pour découpage avec imbrication
        sep = ';'
        lstCar = [',', ';']
        ix = 0
        for lettre in texte:
            if lettre == '(': sep = ','
            if lettre == ')': sep = ';'
            if lettre in lstCar:
                if len(texte) > ix+1 : fin = texte[ix+1:]
                else: fin = ''
                expression = expression[:ix] + sep + fin
            ix +=1
        lstItems = expression.split(';')
        for item in lstItems:
            #réduction des imbrications de parenthèses
            lstnm = []
            lstfl = []
            if '(' in item:
                ix1 = item.index('(')
                if ')' in item:
                    # récupération de la dernière parenthèse, par usage de liste inversée [::-1]
                    ix2 = len(item) - 1 - item[::-1].index(')')
                    lstnm,lstfl = DecoupeParam(item[ix1:ix2+1])
                else: wx.MessageBox("Echec Fonction Produits en UTILS_analyses.DecoupParam\n\nManque parenthèse fermante :\n %s"%item)
                for fl in lstfl:
                    lstFiltres.append(fl.strip())
            lstItems2 = item.strip().split('=')
            if len(lstItems2)==2:
                #présence de filtre on récupére l'argument du filtre
                if len(lstnm) == 0:
                    lstnm.append(str(lstItems2[1]).strip())
                filtre = (lstItems2[0], lstnm)
                lstFiltres.append(filtre)
            elif len(lstItems2)>2:
                wx.MessageBox("Echec Fonction Produits en UTILS_analyses.DecoupParam\n\nDécoupage des arguments impossible :\n %s"%item)
            else:
                #pas filtre, on prend le nom
                for fl in lstfl:
                    lstFiltres.append(fl.strip())
                for nm in lstnm:
                    lstNoms.append(nm.strip())
                if lstnm == []:
                    lstNoms.append(item.strip())
    return lstNoms,lstFiltres

def ListsToDic(listecles, donnees, poscle=0):
    #le dictionnaire généré a pour clé les champs dans liste clé en minuscules
    dic = {}
    if isinstance(donnees[0],(tuple,list)):
        for serie in donnees:
            dic[serie[poscle]] = {}
            try:
                for ix in range(len(listecles)):
                    dic[serie[poscle]][listecles[ix].lower()] = serie[ix]
            except: continue
    else:
        try:
            for ix in range(len(listecles)):
                dic[listecles[ix].lower()] = donnees[ix]
        except: pass
    return dic

def PrechargeAnalyse(analyse, DBsql):
    # constitue un dictionnaire des variables à traiter : clé 'ordre de traitement' et champ colonne 'ordre de sortie'
    lstChamps = CHAMPS_TABLES['wVariables']
    if analyse:
        req = """SELECT wVariables.Ordre, wAnalyses.Colonne, wVariables.Code, wVariables.Libelle, wVariables.Type, wVariables.Fonction, wVariables.Param, wVariables.Atelier, wVariables.Produit
                FROM wVariables INNER JOIN wAnalyses ON wVariables.Code = wAnalyses.Code
                WHERE (((wAnalyses.IDanalyse)='%s'));""" % analyse
    else:
        req = """SELECT Ordre, Ordre, Code, Libelle, Type, Fonction, Param, Atelier, Produit
                 FROM wVariables;"""
    retour = DBsql.ExecuterReq(req, mess='accès OpenRef précharge wVariables')
    dic = {}
    if retour == "ok":
        recordset = DBsql.ResultatReq()
        if len(recordset)>0:
            dic = ListsToDic(lstChamps, recordset)
        else:
            wx.MessageBox("L'analyse choisie n'a aucune variable associée, elle est donc incalculable")
            return {}
    return dic

def GetExercicesClient(agc='*',client='001990',annee='1900',nbanter='0',DBsql=None,saufvalide=False):
    if not nbanter: nbanter = '0'
    if not annee: annee = '1900'
    annees = "( %s"%annee
    if int(nbanter)>0:
        try:
            an = int(annee)
            for i in range(int(nbanter)):
                annees += ", %s"%(str(an-i-1),)
        except: pass
    annees+=")"
    lstExercices = []

    condition = ''
    if saufvalide :
        condition += 'AND ((Validé = 0) OR (Validé IS NULL) )'
    if not (agc in ['*','','any']):
        condition += "AND (IDagc = '%s') "%agc
    req = """SELECT IDagc, IDexploitation, Clôture
            FROM _Ident
            WHERE ( IDexploitation='%s') AND (LEFT(Clôture,4) IN %s ) %s;
            ;"""%(client,str(annees),condition)
    retour = DBsql.ExecuterReq(req, mess='accès OpenRef GetExercicesClient')
    if retour == "ok":
        lstExercices = DBsql.ResultatReq()
    return lstExercices

def NormaliseSQL(requete):
    # les requêtes crées par access doivent être transposées
    requete = requete.replace("\"","'")
    requete = requete.replace("*","%")
    requete = requete.replace("[","")
    requete = requete.replace("]","")
    #transposition de la date access en norme mysql
    try:
        if '#' in requete:
            ix = requete.index('#')
            ix2 = requete.index('#',ix+1)
            dateaccess = requete[ix:-(ix2+1)]
            i = ix2+1
            datesql = "'" + dateaccess[i-5:i-1]+'-'+dateaccess[i-8:i-6]+'-'+dateaccess[i-11:i-9]+ "'"
            requete = requete.replace(dateaccess,datesql)
    except: wx.MessageBox("Impossible de transposer la date encadrée par # dans %s"%requete)
    #gestion du ';' final
    requete = requete.strip()
    if not (requete[-1:] == ';'):
        requete = requete + ';'
    return requete

def NormaliseType(valeur,typeVariable,dicinfos=False):
    if dicinfos :
        #choix de la position dans le tuple de dicInfos
        if isinstance(valeur,tuple):
            if typeVariable.lower() in ('nombre', 'float', 'réel', 'décimal','entier'):
                valeur = valeur(1)+valeur(0)
            else: valeur = valeur(2)
    # gestion des 'None' dans les valeurs
    if typeVariable.lower() in ('str','texte','alpha','date'):
        if valeur: valeur = str(valeur)
        else: valeur = ''
    elif typeVariable.lower() in ('entier'):
        if valeur: valeur = int(valeur)
        else: valeur = 0
    elif typeVariable.lower() in ('nombre','float','réel','décimal'):
        if valeur: valeur = round(float(valeur),4)
        else: valeur = 0.0
    else :
        if valeur: valeur = chr(valeur)
        else: valeur = ''
    return valeur

def GetClientsFilieres(agc, filieres, annee, nbanter, DBsql,saufvalide=False):
    lstClients = []
    fil = filieres.replace(',',';')
    lstFilieres = fil.split(';')
    # traitement de la liste des filières choisies
    for filiere in lstFilieres:
        if len(filiere.strip()) > 1 :
            # appel de la requête correspondant à la filières en cours
            req = """SELECT Requête
                    FROM cFilières
                    WHERE ((IDagc='%s') OR (IDagc Like '*')) AND (IDfilière = '%s')
                    ;"""%(agc, filiere)
            retour = DBsql.ExecuterReq(req, mess='accès OpenRef GetClientsFilieres')
            if retour == "ok":
                recordset = DBsql.ResultatReq()
                for record in recordset:
                    if not record[0]:
                        continue
                    requete = record[0].strip()
                    requete = NormaliseSQL(requete)
                    mots = requete.split(' ')
                    # appel des clients répondants à la requête
                    if mots[0].upper() == 'SELECT':
                        req = requete
                    elif mots[0].upper() == 'WHERE':
                        req = """SELECT IDexploitation FROM _Ident %s"""%requete
                    elif len(mots[0]) == 0:
                        continue
                    else :
                        req = """SELECT IDexploitation FROM _Ident WHERE %s"""%requete
                    retour = DBsql.ExecuterReq(req, mess='accès OpenRef GetClientsFilieres2 %s'%filiere)
                    if retour == "ok":
                        recordset = DBsql.ResultatReq()
                        for record in recordset:
                            lstClients.append(record[0])
    if lstClients == []:
        wx.MessageBox("Aucun client ne correspond aux requêtes des filières %s"%lstFilieres)
        return []
    lstExercices = []
    for client in lstClients:
            lstExercices.extend(GetExercicesClient(agc=agc, client=client, annee=annee, nbanter=nbanter, DBsql=DBsql,saufvalide=saufvalide))
    return lstExercices

def GetClientsGroupes(agc, groupes, annee, nbanter, DBsql,saufvalide=False):
    lstClients = []
    fil = groupes.replace(',',';')
    lstGroupes = fil.split(';')
    # traitement de la liste des groupes choisis
    for groupe in lstGroupes:
        if len(groupe.strip()) > 1 :
            # appel de la requête correspondant à la groupes en cours
            req = """SELECT Membres
                    FROM cGroupes
                    WHERE ((IDagc='%s') OR (IDagc Like '*')) AND (IDgroupe = '%s')
                    ;"""%(agc, groupe)
            retour = DBsql.ExecuterReq(req, mess='accès OpenRef GetClientsGroupes')
            if retour == "ok":
                recordset = DBsql.ResultatReq()
                for record in recordset:
                    mots = record[0]
                    mots = mots.replace(',',';')
                    mots = mots.replace(chr(9),';')
                    mots = mots.split(';')
                    for client in mots:
                        client = "000000" + client
                        client = client[-6:]
                        lstClients.append(client)
    if lstClients == []:
        wx.messageBox("Aucun client ne correspond aux requêtes des groupes %s"%lstGroupes)
        return []
    lstExercices = []
    for client in lstClients:
            lstExercices.extend(GetExercicesClient(agc=agc, client=client, annee=annee, nbanter=nbanter, DBsql=DBsql,saufvalide=saufvalide))
    return lstExercices

class Fonctions(object):
    # classe des fonctions utilisables dans le calcul des variables, pour un dossier pointé
    def __init__(self,parent, tplIdent, dicAnalyse = None, agcuser=None):
        self.parent = parent
        self.dicAnalyse = dicAnalyse
        self.agcuser = agcuser
        self.title = '[UTIL_analyses].Fonctions'
        def Topwin():
            topwin = False
            try:
                # enrichissement du titre pour débug
                nameclass = self.parent.__class__.__name__
                self.title = nameclass + ': ' + self.title
                self.topWindow = wx.GetApp().GetTopWindow()
                if self.topWindow:
                    topwin = True
            except:
                pass
            return topwin
        self.topwin = Topwin()
        self.errorResume = False
        self.messBasEcran = ''
        self.tplIdent = tplIdent
        (self.IDagc, self.IDexploitation, self.Cloture) = self.tplIdent

        # pointeur de la base principale ( ouverture par défaut de db_prim via xGestionDB)
        self.DBsql = xdb.DB()

        #préchargement des infos du dossier
        def PrechargeIdent():
            lstChamps = CHAMPS_TABLES['_Ident']
            req = """SELECT * FROM _Ident
                    WHERE (IDagc = '%s'   AND IDexploitation = '%s' AND Clôture = '%s')
                    ;""" % self.tplIdent
            retour = self.DBsql.ExecuterReq(req, mess='accès OpenRef précharge _Ident')
            dic = {}
            if retour == "ok":
                recordset = self.DBsql.ResultatReq()
                dic = ListsToDic(lstChamps, recordset[0])
            return dic
        def PrechargeInfos():
            req = """SELECT * FROM _Infos
                    WHERE (IDdossier = '%s')
                    ;""" % self.dicIdent['iddossier']
            retour = self.DBsql.ExecuterReq(req, mess='accès OpenRef précharge _Infos')
            dic = {}
            if retour == "ok":
                recordset = self.DBsql.ResultatReq()
                for ligne in recordset:
                    dic[ligne[0]] = (ligne[1],ligne[2],ligne[3])
            return dic
        self.dicIdent = PrechargeIdent()
        self.dicInfos = PrechargeInfos()
        #dicVariables contient le résultat des variables du client, dicAnalyse la liste des expressions de calculs
        self.dicVariables = {}
        self.lstfonctions = ['Ident','Infosident','Communeinsee','Balancemvt','Balance_N1','Balance','Produits','Calcul','Div','Nz']

    def Ident(self,param,*args):
        mess = ''
        expression = str(param[:])
        expr = str(param[:])
        valeur = None
        #découpage de l'expression expression en mots non blancs
        for car in ('+','-','\'','(',')','[',']','/','*',','):
            expr = expr.replace(car,';')
        lstmots = expr.split(';')

        #remplacement des valeurs prises dans la table ident ou infoIdent
        lstfn = []
        for motex in lstmots:
            mot = motex.strip()
            if len(mot) > 0:
                if mot in self.dicIdent.keys():
                    valeur = self.dicIdent[mot]
                    valeur = NormaliseType(valeur,self.typeVariable)
                    expression = expression.replace(mot,str(valeur))
                    continue
                if mot in self.dicInfos.keys():
                    valeurs = self.Infosident(mot)
                    valeurs = NormaliseType(valeur,self.typeVariable,dicinfos=True)
                    expression = expression.replace('mot',str(valeur))
                    continue
                if mot.title() in self.lstfonctions:
                    lstfn.append(mot)
                    continue
                mess += "Le composant %s n'est pas connu dans fonction Ident\t>>Vérifiez les paramètres des variables\n"%mot

        for mot in lstfn:
            expression, err = self.Fonction(mot, expression)
            if (not expression) or err:
                mess += err + "\n"
                break
        try:
            valeur = eval(expression)
        except Exception as err:
            valeur = expression
        return valeur,mess

    def Infosident(self,param,*args):
        valeur = None
        for car in ('+','-',',',';','&'):
            param = param.replace(car,' ')
        lstComposants = param.split(' ')
        for composant in lstComposants:
            if len(composant)>0:
                if composant in self.dicInfos:
                    if valeur:
                        if isinstance(valeur,str):
                            valeur += ' ' + str(self.dicInfos[composant])
                        else:
                            valeur += self.dicInfos[composant]
                    else: valeur = self.dicInfos[composant]
                    valeur = NormaliseType(valeur,self.typeVariable)
        return valeur,''

    def Balance(self,param, *args, mvt=False, n1=False):
        mess = ''
        param = param.upper()
        par2 = param.replace('-',',-').replace('+',',+')
        lstComposants = par2.replace(';',',').split(',')
        valeur = 0.0
        lstChamps = CHAMPS_TABLES['_Balances']
        for composant in lstComposants:
            # extraction du signe
            signe = 1
            compos = composant.strip()
            if composant[0] in ('-','+'):
                if composant[0] == '-': signe = -1
                compos = composant[1:]
                compos = compos.strip()
            # extraction du préfixe
            i = 0
            while compos[i] in ('D','C','%'):
                i += 1
            prefixe = compos[0:i]
            radical = compos[i:]
            try:
                j = int(radical)
            except:
                mess += "\tSeul les chiffres sont admis dans le radical '%s' d'un compte\n" % radical
            #appel des valeurs dans la balance éclatement du solde en deux colonnes
            if mvt :
                select = "SUM(round(DBmvt,2)),SUM(round(CRmvt,2))"
            else:
                select = "SUM(IF(SoldeFin > 0,round(SoldeFin,2),0)),SUM(IF(SoldeFin < 0, round(-SoldeFin,2),0))"
            if n1:
                # option n-1 ne permet pas le calcul des mouvements
                select = "SUM(IF(SoldeDeb > 0,round(SoldeDeb,2),0)),SUM(IF(SoldeDeb < 0, round(-SoldeDeb,2),0))"

            req = """SELECT %s
                    FROM _Balances
                    WHERE (IDdossier = '%s' 
                            AND Compte LIKE '%s')
                    ;""" %(select, self.dicIdent['iddossier'], radical+'%')
            retour = self.DBsql.ExecuterReq(req, mess='accès OpenRef précharge _Ident')
            montant = 0.0
            if retour == "ok":
                recordset = self.DBsql.ResultatReq()
                for slddeb, sldcre in recordset:
                    if not slddeb: slddeb = 0
                    if not sldcre: sldcre = 0
                    if prefixe == '':
                        if radical[0] == '7': montant = -(slddeb - sldcre)
                            #inversion pour la classe 7 pour que les montants créditeurs soient positifs
                        else: montant = slddeb - sldcre
                    #le premier caractère du préfixe détermine le sens
                    elif prefixe == 'DC': montant = slddeb - sldcre
                    elif prefixe == 'CD': montant = sldcre - slddeb
                    elif prefixe == 'D': montant = slddeb
                    elif prefixe == 'C': montant = sldcre
                    elif prefixe == 'DC%':
                        if (slddeb - sldcre) > 0.0: montant = slddeb
                        else: montant = 0.0
                    elif prefixe == 'CD%':
                        if (slddeb - sldcre) < 0.0: montant = -slddeb
                        else: montant = 0.0
                    else : mess = "\tLe préfixe '%s', n'est pas géré dans le radical %s\n"%(prefixe,radical)
            valeur += signe*montant
        if mess != '': mess = ("Balance: %s"%mess)
        return valeur,mess

    def Balancemvt(self,param,*args):
        return self.Balance(param,mvt = True)

    def Balance_N1(self, param,*args):
        return self.Balance(param, n1=True)

    def Produits(self, calcul,ateliers,produits,*args):
        mess = ''
        result = 0.00
        ateliersNoms,ateliersFiltres = DecoupeParam(ateliers)
        produitsNoms,produitsFiltres = DecoupeParam(produits)

        # éléments de requêtes
        where = 'WHERE IDdossier = %d '%self.dicIdent['iddossier']
        def AjoutWhere(champ,lstRetenus):
            txt = "AND %s in ( %s) "%(champ,str(lstRetenus)[1:-1])
        if len(ateliersNoms) > 0:
            where += AjoutWhere('IDMatelier',ateliersNoms)
        if len(produitsNoms) > 0:
            where += AjoutWhere('IDMproduit',produitsNoms)
        """
        if len(produitsFiltres)>0:
            for champmodele,params:
                if champmodele.lower() == 'type':
                    ajout = "AND ( mProduits = "
                    for param in params:"""


        ok = False
        # préparation de la requête sur _Produits
        champs_Produits =  dtt.GetChamps('_Produits',reel=True)
        if calcul.lower() in champs_Produits.lower():
            # accès direct dans la table _Produits
            champs = champs_Produits[champs_Produits.lower().index(calcul.lower())]
            ok = True
        elif calcul.lower() == 'production':
            champs = "Ventes, DeltaStock,AutreProd, AchatAnmx"
            ok = True
        elif calcul.lower == 'pu':
            champs = "Ventes,Quantité1"
            ok = True
        if ok:
            champs += ", TypesProduit"
            req = """SELECT %s 
                    FROM _Produits
                    %s;""" %(champs,where)
            retour = self.DBsql.ExecuterReq(req, mess='accès OpenRef Fonctions.Produits')
            if retour == "ok":
                recordset = self.DBsql.ResultatReq()
                # traitement du retour requête, group by reconstitué sur les champs appelés
                lstChamps = champs.split(',')
                dicRet={}
                ix = 0
                for champ in lstChamps[:-1]:
                    dicRet[champ] = 0.0
                    for record in recordset:
                        if record[ix]:
                            dicRet[champ] += float(record[ix])
                    ix += 1
                if calcul.lower() == 'pu':
                    try:
                        result = round(dicRet['Ventes']/dicRet['Quantité1'],2)
                    except:
                        result = dicRet['Ventes']
                if calcul.lower() == 'production':
                    try:
                        result = round(dicRet['Ventes']+dicRet['DeltaStock']+dicRet['AutreProd']-dicRet['AchatAnmx'],2)
                    except:
                        result = dicRet['Ventes']

            else :
                # échec requete
                mess = retour
                return 0.0,mess

        #autres modes de calculs à gérer à l'avenir
        elif calcul == 'Unité':
            pass
        elif calcul == 'Capacité':
            pass
        return result,mess

    def Calcul(self,param,*args):
        #réduire un argument param de fonction calcul contenant une expression
        mess = ''

        #Cas d'une variables de destination nommée dans le param de calcul 'Vxxx = zzzz'
        valeur = None
        lst = param.split('=')
        if len(lst) >2  :
            return 0.0,"Calcul: deux signes égal dans %s"%param
        elif len(lst)==1:
            nomvar = None
            expression = lst[0]
        else:
            nomvar = lst[0]
            expression = lst[1]
        if len(lst) >2  :
            return 0.0,"deux signes égal dans %s"%(param)
        expr = expression

        #découpage de l'expression de la variable en mots non blancs
        for car in ('+','-','\'','(',')','[',']','/','*',','):
            expr = expr.replace(car,';')
        lstmots = expr.split(';')

        #remplacement des variables déjà calculées par leurs valeurs
        for motex in lstmots:
            mot = motex.strip()
            if len(mot) > 0:
                if mot in self.dicVariables:
                    valeur = self.dicVariables[mot]
                    if isinstance(valeur, float): valeur = round(valeur,4)
                    if not valeur: valeur = 0.0
                    ixdep = expression.index(mot)
                    ixfin = ixdep + len(mot)
                    expression = expression[:ixdep] + str(valeur) + expression[ixfin:]

        # test si nom de fonction on lance la fonction
        yafonction = True
        while yafonction:
            yafonction = False
            for mot in self.lstfonctions:
                if mot.lower() in expression.lower():
                    yafonction = True
                    expression,err = self.Fonction(mot,expression)
                    if (not expression) or err:
                        mess += err+"\n"
                        yafonction = False
                        break

        #final toutes les substitutions sensées faites
        try:
            valeur = eval(expression)
        except Exception as err:
            mess += "\nvariable '%s' : tente 'eval(%s)' >>%s\n"%(param,expression,err)
        if mess == '':
            if nomvar:
                self.dicVariables[nomvar.lower()] = valeur
            return valeur,mess
        else:
            if not self.errorResume:
                rep = wx.MessageBox('Erreurs rencontrées : ABANDON ? \n\n%s'%mess,style = wx.YES_NO|wx.ICON_STOP)
                if rep == wx.NO:
                    # les prochaines erreurs seront cumulées sans interruption
                    self.errorResume = True
                if self.topwin:
                    if len(mess)>100: mess = mess[:50] + '...'+mess[-50:]
                    self.messBasEcran += mess
                    self.messBasEcran = self.messBasEcran[-300:]
                    self.topWindow.SetStatusText(self.messBasEcran)
            return 0,mess

    def Div(self,param,*args):
        # fonction division arrangée
        mess = ''
        lst = param.split(',')
        if len(lst) != 2  :
            return 0.0,"Div  : il n'y a pas diviseur et dividende dans %s"%param
        valeur = 0.0
        try:
            a = float(lst[0])
            b = float(lst[1])
            valeur = round(a/b,2)
        except:
            pass
        return valeur,''

    def Nz(self,param,*args):
        # fonction Null devient zero
        mess = ''
        valeur = 0.0
        try:
            valeur = float(param)
        except: pass
        return valeur,''

    # nouvel appel d'une fonction désignée par un mot  trouvé dans expression : Réduction  de l'expression
    def Fonction(self,mot, expression,*args):
        err = ''
        try:
            def Separearg(mot,expression):
                motmin = mot.lower()
                err = ''
                if len(mot)>0:
                    debmot= expression.index(motmin)
                else :
                    debmot=0
                finmot= debmot+len(mot)
                # vérifie les parenthèses derrière fonction
                if expression[finmot:finmot+1] != '(':
                    err = "manque une parenthèse ouvrante derrière '%s' dans %s"%(mot,expression)
                    return None, err
                x,niv =1,1
                for car in expression[finmot+1:]:
                    if car == '(': niv +=1
                    if car == ')': niv -=1
                    if niv == 0:
                        lgarg = x
                        break
                    x += 1
                if niv > 0:
                    err = "manque une parenthèse fermante derrière '%s' dans %s"%(mot,expression)
                finfn = finmot + lgarg
                debut = expression[:debmot]
                fonction = expression[ debmot: finmot]
                arguments = expression[ finmot+1 : finfn]
                fin = expression[finfn+1:]
                return debut,fonction,arguments,fin,err
            debut, fonction, arguments, fin, err = Separearg(mot,expression)

            # recherche d'éventuelles imbrications de fonctions
            def Imbrication(arguments):
                err = ''
                #test de présence de fonction dans l'argument boucle tant qu'il y a à faire
                go = True
                while go:
                    go = False
                    for fn in self.lstfonctions:
                        if fn.lower() in arguments:
                            go = True
                            arguments,err = self.Fonction(fn,arguments)
                            if err != '':
                                ok = False
                                return None, err
                    # test de parenthèses imbriquées agregation préalable
                go = True
                while go:
                    go = False
                    if '(' in arguments:
                        if not ')' in arguments:
                            err = "manque une parenthèse fermante derrière '%s' dans %s" % (mot, arguments)
                            return None, err
                        go = True
                        ix = arguments.index('(')
                        ssdebut, ssfonction, ssarg, ssfin, err = Separearg('',arguments[ix:])
                        valeur, err = self.Calcul(ssarg)
                        if err == '' :
                            arguments = arguments.replace('(%s)'%ssarg,str(valeur))
                        else: return None, err
                return arguments, err
            arguments, err = Imbrication(arguments)
            if err == '':
                #insertion d'apostrophes pour des paramétres en str
                formule = fonction[:].title()+"('%s')"%arguments
                formule = 'self.'+formule
                valeur, err = eval(formule)
                expression = "%s%s%s"%(debut,str(valeur),fin)
        except Exception as err:
             return None,err
        return expression,err
        #fin de Fonction

    # exécute la fonction avec args(expression) désignée par la colonne 'fonction' de wVariables
    def Variable(self,code,libelle,fonction,param,atelier,produit):
        mess = ''
        if atelier == '': atelier = None
        if produit == '': produit = None

        # controle du formalisme des arguments
        if not(libelle and fonction and param ): mess = "%s : impossible car sont obligatoires : libelle,fonction,param 1\n"%code
        elif not isinstance(param,str) : mess = "Chaîne attendue, le paramètre1 pour '%s' est de type: %s\n"%(libelle,type(param))
        elif len(param) == 0 : mess = "Le paramètre1 de '%s' ne peut pas être une chaîne vide\n"%libelle
        elif fonction.title() not in self.lstfonctions : mess = "La fonction '%s.%s' n'est pas connue\nPossibles : %s\n"%(libelle,fonction, str(self.lstfonctions))

        if mess == '':
            try:
                #appel de la fonction et des trois arguments possibles
                expr = "self.%s(\"%s\",\"%s\",\"%s\")"%(fonction.title(), param.lower(),atelier,produit)
                valeur, mess = eval(expr)
            except Exception as err:
                mess = expr + '\n' + str(err)
        if mess!='':
            mess = "%s: %s"%(code,mess)
            valeur = None
        else:
            #stockage de la variable
            self.dicVariables[code.lower()]=valeur
            self.dicVariables[libelle.lower()] = valeur
        return valeur,mess

    # déroule toutes les variables de l'analyse pour composer la ligne des données du client
    def ComposeLigne(self):
        mess = ''
        dicLigne={}
        try:
            for variable in sorted(self.dicAnalyse.keys()):
                self.typeVariable = self.dicAnalyse[variable]['type']
                valeur, mess = self.Variable(
                                            code=self.dicAnalyse[variable]['code'],
                                            libelle=self.dicAnalyse[variable]['libelle'],
                                            fonction=self.dicAnalyse[variable]['fonction'],
                                            param=self.dicAnalyse[variable]['param'],
                                            atelier=self.dicAnalyse[variable]['atelier'],
                                            produit=self.dicAnalyse[variable]['produit'])
                dicLigne[self.dicAnalyse[variable]['code']] = valeur
                if mess != '':
                    #présence d'erreurs
                    mess = 'variable %s : %s'%(variable, mess)
                    if not self.errorResume:
                        break
        except KeyboardInterrupt:
            wx.MessageBox('Arret clavier Ctrl C\n\nrapport erreurs :\n%s'%mess)

        return dicLigne,mess

    def Close(self):
        try:
            self.DBsql.Close()
        except:pass
        wx.MessageBox('Au revoir Fonctions...')

class Analyse():
    def __init__(self,analyse=None, annee=None, nbanter=0, client=None, groupe=None, filiere=None, gestable=None, agc=None):

        # recherche pour affichage bas d'écran
        self.topwin = False
        self.topWindow = wx.GetApp().GetTopWindow()
        if self.topWindow:
            self.topwin = True

        # pointeur de la base principale ( ouverture par défaut de db_prim via xGestionDB)
        self.DBsql = xdb.DB()
        self.dicExport={}
        self.mess = ''

        #préchargement des variables contenues dans l'analyse
        dicAnalyse = PrechargeAnalyse(analyse,self.DBsql)
        def LstChampsExp(dicAnalyse):
            lst=[]
            for key in sorted(dicAnalyse.keys()):
                code = dicAnalyse[key]['code']
                type = dicAnalyse[key]['type']
                label = dicAnalyse[key]['libelle']
                lst.append((code,type,label))
                colonne = dicAnalyse[key]['colonne']
                if colonne >0 :
                    self.dicExport[colonne]= code
            return lst
        self.lstChampsExp = LstChampsExp(dicAnalyse)

        # vérifie ou crée la table xAnalyse_agc_nomAnalyse
        ok = self.GestionTable(agc,analyse,gestable)
        if not ok : return

        # détermination des clients à traiter
        if client:
            lstDossiers = GetExercicesClient(agc,client,annee, nbanter,self.DBsql)
        elif groupe:
            lstDossiers=GetClientsGroupes(agc, groupe, annee, nbanter, self.DBsql)
        elif filiere:
            lstDossiers = GetClientsFilieres(agc, filiere, annee, nbanter, self.DBsql)
        else :
            wx.MessageBox("Analyse : Aucun paramètre de lancement ne concerne un dossier")
            return

        # déroulé du traitement
        messBasEcran = ''
        nbreOK = 0
        for tplIdent in lstDossiers:
            messBasEcran += "%s "%tplIdent[1]
            retour = 'ko'
            fn = Fonctions(self, tplIdent, dicAnalyse, agcuser=agc)
            dicLigne, mess = fn.ComposeLigne()
            if len(dicLigne) > 0:
                retour = self.ExporteLigne(tplIdent,dicLigne)
                if retour == 'ok':
                    nbreOK += 1
            if len(mess) > 0:
                self.mess += mess+'\n'
            del fn
            if self.topwin:
                messBasEcran += retour + ', '
                messBasEcran = messBasEcran[-230:]
                self.topWindow.SetStatusText(messBasEcran)
        wx.MessageBox("%d dossiers traités"%nbreOK)

    # enregistre dans la table de l'analyse
    def ExporteLigne(self,tplIdent,dicLigne):
        agc,exploitation,exercice = tplIdent
        lstDonnees=[]
        lstChamps=[]
        for colonne, code in self.dicExport.items():
            if code in dicLigne:
                lstDonnees.append(dicLigne[code])
                lstChamps.append(code)
        ret = self.DBsql.ReqInsert(self.nomTable,lstChamps,lstDonnees,mess='Insert %s, %s'%(exploitation,exercice))
        if ret != 'ok':
            wx.MessageBox('Export de la ligne\n\nerreur sur dossier : %s\n%s'%(str(tplIdent),ret))
        return ret

    def GestionTable(self,agc, analyse, gestable):
        nbChampsTable = 0
        self.nomTable = 'xExp_%s_%s'%(agc,analyse)
        tableExist = self.DBsql.IsTableExists(self.nomTable)
        ok = True
        if (not tableExist) and ('Créer' in gestable):
            self.CreationTable(self.nomTable,self.lstChampsExp)
        elif tableExist and ('Purger' in gestable):
            req = "DROP TABLE %s" %self.nomTable
            retour = self.DBsql.ExecuterReq(req)
            if retour == "ok":
                self.DBsql.Commit()
            self.CreationTable(self.nomTable,self.lstChampsExp)
        elif tableExist and ('Ajout' in gestable):
            pass
        else:
            ok = False
            if tableExist :
                wx.MessageBox("Rejet de la demande\n\nVous voulez : '%s' !\n La table '%s' existe déjà"%(str(gestable),self.nomTable))
            else:
                wx.MessageBox("Rejet de la demande\n\nVous voulez : '%s' !\n La table '%s' n'existe pas" % (str(gestable), self.nomTable))
        if ok:
            #test du nombre de variables prochain calcul % champs table
            req = "SHOW COLUMNS FROM  %s" % self.nomTable
            retour = self.DBsql.ExecuterReq(req)
            if retour == "ok":
                recordset = self.DBsql.ResultatReq()
                if len(recordset) > 0:
                    nbChampsTable = len(recordset)
            if len(self.lstChampsExp) != nbChampsTable:
                wx.MessageBox("Rejet de la demande\n\nVous voulez écrire %d variables dans une table à %d champs!"%(self.lstChampsExp, nbChampsTable))
        return ok

    def CreationTable(self,nomTable,lstChampsExp):
        for code, nature, comment in lstChampsExp:
            comment = comment.replace("'"," ")
            code = code.replace("'"," ")
        req = "CREATE TABLE %s (" % nomTable
        for nomChamp,typeChamp,labelChamp in lstChampsExp:
            if typeChamp.lower() in ('date') : typeChamp = "VARCHAR(10)"
            elif typeChamp.lower() in ('int','integer','entier'): typeChamp = "INT"
            elif typeChamp.lower() in ('nombre','réel','num'): typeChamp = "FLOAT"
            elif typeChamp.lower() in ('text','texte','alpha'): typeChamp = "VARCHAR(64)"
            elif typeChamp.lower() in ('blob','longtext'): typeChamp = "BLOB"
            elif typeChamp.lower() in ('bool','boolean','booléen','vraifaux'): typeChamp = "TINYINT(1)"
            else : typeChamp = 'TEXT(250)'
            req = req + "%s %s NULL COMMENT '%s', " % (nomChamp, typeChamp, labelChamp)
        req = req[:-2] + ")"
        retour = self.DBsql.ExecuterReq(req)
        if retour == "ok":
                self.DBsql.Commit()

#************************   Pour Test ou modèle  *********************************
if __name__ == '__main__':
    app = wx.App(0)
    dicanalyse = {100:{'ordre': 10000, 'colonne': 1000, 'code': 'V100', 'libelle': 'Produit de élevage caprin', 'type': 'nombre',
                       'fonction': 'Produits', 'param': 'Production', 'atelier': '(brebis,caprin), type = (vitipart, fromagerie),nontype = agneau', 'produit': ''},}
    fn = Fonctions(None,('prov','009418','2018-08-31'),dicAnalyse=dicanalyse,agcuser='prov')
    valeur = fn.ComposeLigne()
    print('valeur variable: ',valeur[0])
    print('erreurs: ',valeur[1],'-')

    app.MainLoop()

