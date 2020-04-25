#!/usr/bin/env python
# -*- coding: utf8 -*-

#------------------------------------------------------------------------
# Application :    xPY, Gestion des bases de données
# Auteur:          Jacques Brunel, d'après Yvan LUCAS Noethys
# Copyright:       (c) 2019-04     Cerfrance Provence
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import os
import wx
import mysql.connector
import win32com.client
import sqlite3
import copy
import datetime
import xpy.xUTILS_Config as xucfg

DICT_CONNEXIONS = {}

def NoPunctuation(txt = ''):
    import re
    punctuation = u"'!\"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'"
    regex = re.compile('[%s]' % re.escape(punctuation))
    return regex.sub(' ', txt)

def Supprime_accent(texte):
    liste = [ (u"é", u"e"), (u"è", u"e"), (u"ê", u"e"), (u"ë", u"e"), (u"à", u"a"), (u"û", u"u"), (u"ô", u"o"), (u"ç", u"c"), (u"î", u"i"), (u"ï", u"i"),]
    for a, b in liste :
        texte = texte.replace(a, b)
        texte = texte.replace(a.upper(), b.upper())
    return texte

def DateEngEnDateDD(dateEng):
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def DateDDEnDateEng(datedd):
    if not isinstance(datedd, datetime.date):
        return '1900-01-01'
    aaaa = str(datedd.year)
    mm = ('00'+str(datedd.month))[-2:]
    jj = ('00'+str(datedd.day))[-2:]
    return aaaa+'-'+mm+'-'+jj

class DB():
    # accès à la base de donnees principale
    def __init__(self, IDconnexion = None, config=None, grpConfig='db_prim', nomFichier=None):
        self.echec = 1
        self.IDconnexion = IDconnexion
        self.nomBase = 'personne!'
        if nomFichier:
            self.isNetwork = False
            self.OuvertureFichierLocal(nomFichier)
            return
        if not IDconnexion:
            self.connexion = None
            # appel des params de connexion stockés dans UserProfile
            cfg = xucfg.ParamUser()
            choix= cfg.GetDict(groupe='USER')
            # appel des params de connexion stockés dans Data
            cfg = xucfg.ParamFile()
            configs= cfg.GetDict(groupe='CONFIGS')
            nomConfig = choix['config']
            try:
                # priorité la config passée en kwds puis recherche de la dernière config dans 'USER'
                if config:
                    # Présence de kwds 'config', peut être le nom de la config ou un dictionaire de configuration
                    if isinstance(config, str):
                        nomConfig = config
                    elif isinstance(config,dict):
                        nomConfig = None
                        self.cfgParams = copy.deepcopy(config)
                        for cle, valeur in choix.items():
                            self.cfgParams[cle] = valeur
                if nomConfig:
                    if not (nomConfig in configs['lstIDconfigs']):
                        wx.MessageBox("Le nom de config '%s' n'est pas dans la liste lstIDconfigs"%(nomConfig))
                        return
                    ix = configs['lstIDconfigs'].index(nomConfig)
                    # on récupére les paramétres dans toutes les configs par le pointeur ix dans les clés
                    self.cfgParams = configs['lstConfigs'][ix][grpConfig]
                # on ajoute les choix  de mot passe aux paramètres de la config retenue
                for cle, valeur in choix.items():
                    self.cfgParams[cle] = valeur
                if self.cfgParams['serveur'][-1:] in ('/','\\'):
                    self.nomBase = self.cfgParams['serveur']+self.cfgParams['nameDB']
                else:
                    self.nomBase = self.cfgParams['serveur']+'\\'+self.cfgParams['nameDB']
            except Exception as err:
                wx.MessageBox("La récup des identifiants de connexion a échoué : \nErreur detectee :%s" % err)
                self.erreur = err
                return

            # Ouverture des bases de données selon leur type
            if 'typeDB' in self.cfgParams:
                self.typeDB = self.cfgParams['typeDB'].lower()
            else : self.typeDB = 'Non renseigné'
            if 'typeDB' in self.cfgParams.keys() and  self.cfgParams['typeDB'].lower() in ['mysql','sqlserver']:
                self.isNetwork = True
                # Ouverture de la base de données
                self.ConnexionFichierReseau(self.cfgParams)
            elif 'typeDB' in self.cfgParams.keys() and  self.cfgParams['typeDB'].lower() in ['access','sqlite']:
                self.isNetwork = False
                self.ConnexionFichierLocal(self.cfgParams)
            else :
                wx.MessageBox("Le type de Base de Données '%s' n'est pas géré!" % self.typeDB)
                return

            if self.connexion:
                # Mémorisation de l'ouverture de la connexion et des requêtes
                if len(DICT_CONNEXIONS) == 0:
                    self.IDconnexion = 1
                else:
                    self.IDconnexion = sorted(DICT_CONNEXIONS.keys())[-1]+1
                DICT_CONNEXIONS[self.IDconnexion] = {}
                DICT_CONNEXIONS[self.IDconnexion]['isNetwork'] = self.isNetwork
                DICT_CONNEXIONS[self.IDconnexion]['typeDB'] = self.typeDB
                DICT_CONNEXIONS[self.IDconnexion]['connexion'] = self.connexion
                DICT_CONNEXIONS[self.IDconnexion]['cfgParams'] = self.cfgParams
        else:
            if self.IDconnexion in DICT_CONNEXIONS:
                # la connexion a été conservée (absence de DB.Close)
                self.isNetwork  = DICT_CONNEXIONS[self.IDconnexion]['isNetwork']
                self.typeDB     = DICT_CONNEXIONS[self.IDconnexion]['typeDB']
                self.connexion  = DICT_CONNEXIONS[self.IDconnexion]['connexion']
                self.cfgParams  = DICT_CONNEXIONS[self.IDconnexion]['cfgParams']
                if self.connexion: self.echec = 0

    def Ping(self,serveur):
        if serveur :
            if len(serveur)>2:
                wx.MessageBox("Testez l'accès au serveur '%s'\n\nlancez cmd puis 'ping %s'"%(serveur,serveur))

    def ConnexionFichierReseau(self,config):
        self.connexion = None
        try:
            etape = 'Décompactage de la config'
            host = config['serveur']
            port = config['port']
            user = config['userDB']
            passwd = config['mpUserDB']
            nomFichier = config['nameDB']
            self.pseudo = config['pseudo']
            self.mpUtilisateur = config['mpuser']
            self.utilisateur = os.environ['USERNAME']
            self.domaine =  os.environ['USERDOMAIN']
            etape = 'Création du connecteur %s - %s - %s - %s'%(host,user,passwd, port)
            if self.typeDB == 'mysql':
                self.connexion = mysql.connector.connect(host=host, user=user, passwd=passwd, port=int(port))
                etape = 'Création du curseur, après connexion réussie'
                self.cursor = self.connexion.cursor(buffered=True)
                etape = 'premier accès base pour use %s' %nomFichier
                self.cursor.execute("SHOW DATABASES;")
                listeBases = self.cursor.fetchall()
                # Utilisation
                self.cursor.execute("USE %s;" % nomFichier)
                self.echec = 0
            else:
                wx.MessageBox('Accès BD non développé pour %s' %self.typeDB)
        except Exception as err:
            wx.MessageBox("La connexion MYSQL a echoué à l'étape: %s, sur l'erreur :\n\n%s" %(etape,err))
            self.erreur = err
            if 'connect' in etape:
                self.Ping(config['serveur'])
        if self.connexion:
            if not (nomFichier,) in listeBases:
                lstBases = str(listeBases)
                wx.MessageBox("La base '%s' n'est pas sur le serveur qui porte les bases :\n\n %s" % (nomFichier, lstBases ), style=wx.ICON_STOP)
                self.echec = 1
                self.connexion = None

    def OuvertureFichierLocal(self, nomFichier):
        """ Version LOCALE avec SQLITE """
        # Vérifie que le fichier sqlite existe bien
        if os.path.isfile(nomFichier) == False:
            wx.MessageBox("Le fichier local '%s' demande n'est pas present sur le disque dur."%nomFichier)
            self.echec = 1
            return
        # Initialisation de la connexion
        self.nomBase = nomFichier
        self.typeDB = "sqlite"
        self.ConnectSQLite()

    def ConnexionFichierLocal(self, config):
        self.connexion = None
        try:
            etape = 'Création du connecteur'
            if self.typeDB == 'access':
                self.ConnectAcessADO()
            elif self.typeDB == 'sqlite':
                self.ConnectSQLite()
            elif self.typeDB == 'mySqlLocal':
                self.ConnectMySqlLocal()
            else:
                wx.MessageBox('Accès DB non développé pour %s' %self.typeDB)
        except Exception as err:
            wx.MessageBox("La connexion base de donnée a echoué à l'étape: %s, sur l'erreur :\n\n%s" %(etape,err))
            self.erreur = err

    def ConnectAcessADO(self):
        """Important ne tourne qu'avec: 32bit MS driver - 32bit python!
           N'est pas compatible access 95, mais lit comme access 2002"""
        # Vérifie que le fichier existe bien
        if os.path.isfile(self.nomBase) == False:
            wx.MessageBox("Le fichier %s demandé n'est pas present sur le disque dur."% self.nomBase, style = wx.ICON_WARNING)
            return
        # Initialisation de la connexion
        try:
            self.connexion = win32com.client.Dispatch(r'ADODB.Connection')
            DSN = ('PROVIDER = Microsoft.Jet.OLEDB.4.0;DATA SOURCE = ' + self.nomBase + ';')
            self.connexion.Open(DSN)
            #lecture des tables de la base de données
            cat = win32com.client.Dispatch(r'ADOX.Catalog')
            cat.ActiveConnection = self.connexion
            allTables = cat.Tables
            if len(allTables) == 0:
                wx.MessageBox("La base de donnees %s est présente mais vide " % self.nomBase)
                return
            del cat
            self.cursor = win32com.client.Dispatch(r'ADODB.Recordset')
            self.echec = 0
        except Exception as err:
            wx.MessageBox("La connexion avec la base access %s a echoué : \nErreur détectée :%s" %(self.nomBase,err),
                          style=wx.ICON_WARNING)
            self.erreur = err

    def ConnectSQLite(self):
        # Version LOCALE avec SQLITE
        #nécessite : pip install pysqlite
        # Vérifie que le fichier sqlite existe bien
        if os.path.isfile(self.nomBase) == False:
            wx.MessageBox("Le fichier %s demandé n'est pas present sur le disque dur."% self.nomBase, style = wx.ICON_WARNING)
            return
        # Initialisation de la connexion
        try:
            self.connexion = sqlite3.connect(self.nomBase.encode('utf-8'))
            self.cursor = self.connexion.cursor()
            self.echec = 0
        except Exception as err:
            wx.MessageBox("La connexion avec la base de donnees SQLITE a echoué : \nErreur détectée :%s" % err, style = wx.ICON_WARNING)
            self.erreur = err

    def ExecuterReq(self, req, mess=None, affichError=True):
        # Pour parer le pb des () avec MySQL
        #if self.typeDB == 'mysql' :
        #    req = req.replace("()", "(10000000, 10000001)")
        try:
            if self.typeDB == 'access':
                self.recordset = []
                # methode Access ADO
                self.cursor.Open(req, self.connexion)
                if not self.cursor.BOF:
                    self.cursor.MoveFirst()
                    while not self.cursor.EOF:
                        record = []
                        go = True
                        i=0
                        while go:
                            try:
                                record.append(self.cursor(i).value)
                                i += 1
                            except Exception:
                                go = False
                        self.recordset.append(record)
                        self.cursor.MoveNext()
                    self.retourReq = "ok"
                else:
                    self.retourReq = "Aucun enregistrement"
                self.cursor.Close()
            else:
                # autres types de connecteurs
                self.cursor.execute(req)
                self.retourReq = 'ok'
        except Exception as err:
            self.echec = 1
            if mess:
                self.retourReq = mess +'\n\n'
            else: self.retourReq = 'Erreur xGestionDB\n\n'
            self.retourReq +=  ("ExecuterReq:\n%s\n\nErreur detectee:\n%s"% (req, str(err)))
            if affichError:
                wx.MessageBox(self.retourReq)
        finally:
            return self.retourReq

    def ResultatReq(self):
        if self.echec == 1 : return []
        resultat = []
        try :
            if self.typeDB == 'access':
                resultat = self.recordset
            else:
                resultat = self.cursor.fetchall()
                # Pour contrer MySQL qui fournit des tuples alors que SQLITE fournit des listes
                if self.typeDB == 'mysql' and type(resultat) == tuple :
                    resultat = list(resultat)
        except :
            pass
        return resultat

    def DonneesInsert(self,donnees):
        # décompacte les données en une liste  ou liste de liste pour requêtes Insert
        donneesValeurs = '('
        def Compose(liste):
            serie = ''
            for valeur in liste:
                if isinstance(valeur,(int,float)):
                    val = "%s, " %str(valeur)
                elif isinstance(valeur, (tuple, list,dict)):
                    val = "'%s', "%str(valeur)[1:-1].replace('\'', '')
                else:
                    val = "'%s', "%str(valeur).replace('\'', '')
                serie += "%s"%(val)
            return serie[:-2]
        if isinstance(donnees[0], (tuple,list)):
            for (liste) in donnees:
                serie = Compose(liste)
                donneesValeurs += "%s ), ("%(serie)
            donneesValeurs = donneesValeurs[:-4]
        else:
            donneesValeurs += "%s"%Compose(donnees)
        return donneesValeurs +')'

    def ReqInsert(self, nomTable="", lstChamps=[], lstlstDonnees=[],lstDonnees=None,commit=True, mess=None, affichError=True):
        """ Permet d'insérer les lstChamps ['ch1','ch2',..] et lstlstDonnees [[val11,val12...],[val21],[val22]...]
            self.newID peut être appelé ensuite pour récupérer le dernier'D """
        if lstDonnees:
            lsttemp=[]
            lstChamps=[]
            for (champ,donnee) in lstDonnees:
                lstChamps.append(champ)
                lsttemp.append(donnee)
            lstlstDonnees.append(lsttemp)
        if len(lstChamps)* len(lstlstDonnees) == 0:
            if affichError:
                wx.MessageBox('%s\n\nChamps ou données absents'%mess)
            return '%s\n\nChamps ou données absents'%mess
        valeurs = self.DonneesInsert(lstlstDonnees)
        champs = '( ' + str(lstChamps)[1:-1].replace('\'','') +' )'
        req = """INSERT INTO %s 
              %s 
              VALUES %s ;""" % (nomTable, champs, valeurs)
        self.retourReq = "ok"
        self.newID= 0
        try:
            # Enregistrement
            self.cursor.execute(req)
            if commit == True :
                self.Commit()
            # Récupération de l'ID
            if self.typeDB == 'mysql' :
                # Version MySQL
                self.cursor.execute("SELECT LAST_INSERT_ID();")
            else:
                # Version Sqlite
                self.cursor.execute("SELECT last_insert_rowid() FROM %s" % nomTable)
            self.newID = self.cursor.fetchall()[0][0]
        except Exception as err:
            self.echec = 1
            if mess:
                self.retourReq = mess +'\n\n'
            else: self.retourReq = 'Erreur xGestionDB\n\n'
            self.retourReq +=  ("ReqInsert:\n%s\n\nErreur detectee:\n%s"% (req, str(err)))
            if affichError:
                wx.MessageBox(self.retourReq)
        finally:
            return self.retourReq

    def CoupleMAJ(self,champ, valeur):
        nonetype = type(None)
        if isinstance(valeur,(int,float)):
            val = "%s, " %str(valeur)
        elif isinstance(valeur, (nonetype)):
            val = "NULL, "
        elif isinstance(valeur, (tuple, list,dict)):
            val = str(valeur)[1:-1]
            val = val.replace("'","")
            val = "'%s', "%val
        else: val = "\"%s\", "%str(valeur)
        couple = " %s = %s"%(champ,val)
        return couple

    def DonneesMAJ(self,donnees):
        # décompacte les données en une liste de couples pour requêtes MAJ
        donneesCouples = ""
        if isinstance(donnees, (tuple,list)):
            for (champ,valeur) in donnees:
                couple = self.CoupleMAJ(champ, valeur)
                donneesCouples += "%s"%(couple)
        elif isinstance((donnees,dict)):
            for (champ, valeur) in donnees.items():
                couple = self.CoupleMAJ(champ, valeur)
                donneesCouples += "%s" % (couple)
        else: return None
        donneesCouples = donneesCouples[:-2]+' '
        return donneesCouples

    def ListesMAJ(self,lstChamps,lstDonnees):
        # assemble des données en une liste de couples pour requêtes MAJ
        donneesCouples = ''
        for ix in range(len(lstChamps)):
            couple = self.CoupleMAJ(lstChamps[ix], lstDonnees[ix])
            donneesCouples += "%s"%(couple)
        donneesCouples = donneesCouples[:-2]+' '
        return donneesCouples

    def ReqMAJ(self, nomTable='',couples=None,nomChampID=None,ID=None,condition=None,lstDonnees=[],lstChamps=[],
               mess=None, affichError=True, IDestChaine = False):
        """ Permet de mettre à jour des couples présentées en dic ou liste de tuples"""
        # si couple est None, on en crée à partir de lstChamps et lstDonnees
        if couples :
            update = self.DonneesMAJ(couples)
        elif (len(lstChamps) > 0) and (len(lstChamps) == len(lstDonnees)):
            update = self.ListesMAJ(lstChamps,lstDonnees)
        if nomChampID and ID:
            # un nom de champ avec un ID vient s'ajouter à la condition
            if IDestChaine == False and (isinstance(ID, int )):
                condID = " (%s=%d) "%(nomChampID, ID)
            else:
                condID = " (%s='%s') "%(nomChampID, ID)
            if condition:
                condition += " AND %s "%(condID)
            else: condition = condID
        elif (not condition) or (len(condition.strip()==0)):
            # si pas de nom de champ et d'ID, la condition ne doit pas être vide sinon tout va updater
            condition = " FALSE "
        req = "UPDATE %s SET  %s WHERE %s ;" % (nomTable, update, condition)
        # Enregistrement
        try:
            self.cursor.execute(req,)
            self.Commit()
            self.retourReq = "ok"
        except Exception as err:
            self.echec = 1
            if mess:
                self.retourReq = mess + '\n\n'
            else:
                self.retourReq = 'Erreur xGestionDB\n\n'
            self.retourReq += ("ReqMAJ:\n%s\n\nErreur detectee:\n%s" % (req, str(err)))
            if affichError:
                wx.MessageBox(self.retourReq)
        finally:
            return self.retourReq

    def ReqDEL(self, nomTable,champID="",ID=None, condition="", commit=True, mess=None, affichError=True):
        """ Suppression d'un enregistrement ou d'un ensemble avec condition de type where"""
        if len(condition)==0:
            condition = champID+" = %d"%ID
        self.retourReq = "ok"
        req = "DELETE FROM %s WHERE %s ;" % (nomTable, condition)
        try:
            self.cursor.execute(req)
            if commit == True :
                self.Commit()
                self.retourReq = "ok"
        except Exception as err:
            self.echec = 1
            if mess:
                self.retourReq = mess + '\n\n'
            else:
                self.retourReq = 'Erreur xGestionDB\n\n'
            self.retourReq += ("ReqMAJ:\n%s\n\nErreur detectee:\n%s" % (req, str(err)))
            if affichError:
                wx.MessageBox(self.retourReq)
        finally:
            return self.retourReq

    def Commit(self):
        if self.connexion:
            self.connexion.commit()

    def Close(self):
        try :
            self.connexion.close()
            del DICT_CONNEXIONS[self.IDconnexion]
        except :
            pass

    def IsTableExists(self, nomTable=""):
        """ Vérifie si une table donnée existe dans la base """
        tableExists = False
        for (nomTableTmp,) in self.GetListeTables() :
            if nomTableTmp == nomTable :
                tableExists = True
        return tableExists

    def IsIndexExists(self, nomIndex=""):
        """ Vérifie si un index existe dans la base """
        indexExists = False
        if self.lstIndex == []:
            self.lstIndex = self.GetListeIndex()
        if nomIndex in self.lstIndex :
            indexExists = True
        return indexExists

    def CreationUneTable(self, dicoDB={},table=None, fenetreParente=None):
        #dicoDB=DATA_Tables.DB_DATA
        retour = None
        if table == None : return retour
        if not self.IsTableExists(table) :
            # Affichage dans la StatusBar
            if fenetreParente != None :
                fenetreParente.SetStatusText(("Création de la table de données %s...") % table)
            req = "CREATE TABLE %s (" % table
            for descr in dicoDB[table]:
                nomChamp = descr[0]
                typeChamp = descr[1]
                # Adaptation à Sqlite
                if self.isNetwork == False and typeChamp == "LONGBLOB" : typeChamp = "BLOB"
                # Adaptation à MySQL :
                if self.isNetwork == True and typeChamp == "INTEGER PRIMARY KEY AUTOINCREMENT" : typeChamp = "INTEGER PRIMARY KEY AUTO_INCREMENT"
                if self.isNetwork == True and typeChamp == "FLOAT" : typeChamp = "REAL"
                if self.isNetwork == True and typeChamp == "DATE" : typeChamp = "VARCHAR(10)"
                if self.isNetwork == True and typeChamp.startswith("VARCHAR") :
                    nbreCaract = int(typeChamp[typeChamp.find("(")+1:typeChamp.find(")")])
                    if nbreCaract > 255 :
                        typeChamp = "TEXT(%d)" % nbreCaract
                    if nbreCaract > 20000 :
                        typeChamp = "MEDIUMTEXT"
                # ------------------------------
                req = req + "%s %s, " % (nomChamp, typeChamp)
            req = req[:-2] + ")"
            retour = self.ExecuterReq(req)
            if retour == "ok":
                    self.Commit()
        return retour
        #fin CreationUneTable

    def CreationIndex(self,nomIndex="",listeIndex={}):
        """ Création d'un index """
        nomTable = listeIndex[nomIndex]["table"]
        nomChamp = listeIndex[nomIndex]["champ"]

        if self.IsTableExists(nomTable) :
            #print "Creation de l'index : %s" % nomIndex
            if nomIndex[:2] == "PK":
                req = "CREATE UNIQUE INDEX %s ON %s (%s);" % (nomIndex, nomTable, nomChamp)
            else :
                req = "CREATE INDEX %s ON %s (%s);" % (nomIndex, nomTable, nomChamp)
            retour = self.ExecuterReq(req)
            print(nomIndex, "-----------/-------------",retour)
            if retour == "ok":
                    self.Commit()

    def GetListeTables(self):
        if self.typeDB == 'sqlite' :
            # Version Sqlite
            req = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            self.ExecuterReq(req)
            listeTables = self.ResultatReq()
        else:
            # Version MySQL
            req = "SHOW TABLES;"
            self.ExecuterReq(req)
            listeTables = self.ResultatReq()
        return listeTables

    def GetListeChamps2(self, nomTable=""):
        """ Affiche la liste des champs de la table donnée """
        listeChamps = []
        if self.typeDB == 'sqlite':
            # Version Sqlite
            req = "PRAGMA table_info('%s');" % nomTable
            self.ExecuterReq(req)
            listeTmpChamps = self.ResultatReq()
            for valeurs in listeTmpChamps:
                listeChamps.append((valeurs[1], valeurs[2]))
        else:
            # Version MySQL
            req = "SHOW COLUMNS FROM %s;" % nomTable
            self.ExecuterReq(req)
            listeTmpChamps = self.ResultatReq()
            for valeurs in listeTmpChamps:
                listeChamps.append((valeurs[0], valeurs[1]))
        return listeChamps

    def GetListeIndex(self):
        if self.typeDB == 'sqlite':
            # Version Sqlite
            req = "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;"
            self.ExecuterReq(req)
            listeIndex = self.ResultatReq()
        else:
            # Version MySQL
            listeIndex = []
            for table in self.GetListeTables():
                req = "SHOW INDEX IN %s;" % str(table[0])
                self.ExecuterReq(req)
                for index in self.ResultatReq():
                    if str(index[2]) != 'PRIMARY':
                        listeIndex.append(str(index[2]))
        return listeIndex

    def MaFonctionTest(self):
        import pyodbc
        """Important: 32bit MS driver - 32bit python!"""
        """N'est pas compatible access 95"""
        cnxn = pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=c:/temp/test.mdb;')
        cursor = cnxn.cursor()
        cursor.execute("select * from table1")
        for row in cursor.fetchall():
            print(row)

        csr = cnxn.cursor()
        csr.close()
        del csr
        cnxn.close()

        import mysql
        cnx = mysql.connector.connect(host='192.168.1.43', user='root', database='matthania_data',password='pr0V1522')
        cursor = cnx.cursor()

        query = ("SELECT * FROM caisses")

        cursor.execute(query)

        for ligne in cursor:
          print(ligne)

        cursor.close()
        cnx.close()



        import pymysql.cursors

        # Connect to the database
        connection = pymysql.connect(host='192.168.1.43',
                                     user='root',
                                     password='pr0V1522',
                                     db='matthania_data',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)

        try:
            with connection.cursor() as cursor:
                # Read a single record
                sql = "SELECT * FROM `caisses` "
                cursor.execute(sql,)
                for ligne in cursor:
                    print(ligne)

                result = cursor.fetchmany(size=2)
                print(result)


            with connection.cursor() as cursor:
                # Create a new record
                sql = "SELECT IDcaisse FROM caisses;"
                cursor.execute(sql, ('IDcaisse',))
                result = cursor.fetchone()
                print(result)

            # connection is not autocommit by default. So you must commit to save
            # your changes.
            connection.commit()

            with connection.cursor() as cursor:
                # Read a single record
                sql = "SELECT `id`, `password` FROM `users` WHERE `email`=%s"
                cursor.execute(sql, ('webmaster@python.org',))
                result = cursor.fetchone()
                print(result)

        finally:
            connection.close()

if __name__ == "__main__":
    app = wx.App()
    DB1 = DB(config={'typeDB':'access','serveur':'C:/Quadra/DATABASE/gi/0000/','nameDB':'qgi.mdb'})
    f = DB1.ExecuterReq('SELECT count(Code) FROM clients ;')
    print(f)
    print(DB1.ResultatReq()[0][0])

    """
    DB1 = DB()
    print(DB1)
    print(len(DICT_CONNEXIONS),DB1.IDconnexion)
    DB2 = DB()
    print(DB2.echec)
    print(len(DICT_CONNEXIONS),DB2.IDconnexion)
    DB1.Close()
    print(len(DICT_CONNEXIONS),DB2.IDconnexion)
    """