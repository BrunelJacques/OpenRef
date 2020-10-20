# Il faudra optimiser les fonctions de ce fichier mais plus tard
SYMBOLE = "€"

import wx
import datetime
import unicodedata
from xpy.outils.ObjectListView import ColumnDefn

# fonctions pour OLV

def SupprimeAccents(texte,lower=True):
    # met en minuscule sans accents et sans caractères spéciaux
    code = ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')
    #code = str(unicodedata.normalize('NFD', texte).encode('ascii', 'ignore'))
    if lower: code = code.lower()
    code = ''.join(car for car in code if car not in " %)(.[]',;/\n")
    return code

def GetLstChamps(table=None,cutend=None):
    if cutend: cutend = -cutend
    return [x for x,y,z in table[:cutend] ]

def GetLstColonnes(table=None,cutend=None,IDcache=True):
    if cutend: cutend = -cutend
    lstNomsColonnes = [x for x, y, z in table[:cutend]]
    lstTypes = [y for x, y, z in table[:cutend]]
    lstCodesColonnes = [SupprimeAccents(x,lower=False) for x in lstNomsColonnes]
    lstValDefColonnes = ValeursDefaut(lstNomsColonnes, lstTypes)
    lstLargeurColonnes = LargeursDefaut(lstNomsColonnes, lstTypes,IDcache=IDcache)
    return DefColonnes(lstNomsColonnes, lstCodesColonnes, lstValDefColonnes, lstLargeurColonnes)

def DefColonnes(lstNoms,lstCodes,lstValDef,lstLargeur):
    # Composition d'une liste de définition de colonnes d'un OLV; remarque faux ami: 'nom, code' == 'label, name'
    ix=0
    for lst in (lstCodes,lstValDef,lstLargeur):
        # complète les listes entrées si nécessaire
        if lst == None : lst = []
        if len(lst)< len(lstNoms):
            lst.extend(['']*(len(lstNoms)-len(lst)))
    lstColonnes = []
    for colonne in lstNoms:
        if isinstance(lstValDef[ix],(str,wx.DateTime,datetime.date)):
            posit = 'left'
        else: posit = 'right'
        # ajoute un converter à partir de la valeur par défaut
        if isinstance(lstValDef[ix], (float,)):
            if '%' in colonne:
                stringConverter = FmtPercent
            else:
                stringConverter = FmtDecimal
        elif isinstance(lstValDef[ix], int):
            if '%' in colonne:
                stringConverter = FmtPercent
            else:
                stringConverter = FmtInt
        elif isinstance(lstValDef[ix], (datetime.date,wx.DateTime)):
            stringConverter = FmtDate
        else: stringConverter = None
        if lstLargeur[ix] in ('',None,'None',-1):
            lstLargeur[ix] = -1
            isSpaceFilling = True
        else: isSpaceFilling = False
        code = lstCodes[ix]
        lstColonnes.append(ColumnDefn(title=colonne,align=posit,width=lstLargeur[ix],valueGetter=code,valueSetter=lstValDef[ix],
                                      isSpaceFilling=isSpaceFilling,stringConverter=stringConverter))
        ix += 1
    return lstColonnes

def ValeursDefaut(lstNomsColonnes,lstTypes):
    # Détermine des valeurs par défaut selon le type des variables
    lstValDef = [0,]
    for ix in range(1,len(lstNomsColonnes)):
        tip = lstTypes[ix].lower()
        if tip[:3] == 'int': lstValDef.append(0)
        elif tip[:10] == 'tinyint(1)': lstValDef.append(False)
        elif tip[:5] == 'float': lstValDef.append(0.0)
        elif tip[:4] == 'date': lstValDef.append(wx.DateTime.Today())
        else: lstValDef.append('')
    return lstValDef

def LargeursDefaut(lstNomsColonnes,lstTypes,IDcache=True):
    # Evaluation de la largeur nécessaire des colonnes selon le type de donnee et la longueur du champ
    lstLargDef=[]
    ix =0
    if IDcache:
        lstLargDef = [0,]
        ix = 1
    for ix in range(ix, len(lstNomsColonnes)):
        nomcol = lstNomsColonnes[ix]
        tip = lstTypes[ix]
        tip = tip.lower()
        if tip[:3] == 'int': lstLargDef.append(50)
        elif tip[:5] == 'float': lstLargDef.append(60)
        elif tip[:4] == 'date': lstLargDef.append(80)
        elif tip[:7] == 'varchar':
            lg = int(tip[8:-1])*3
            if lg <= 16: lg=24
            if lg > 150:
                lg = -1
            lstLargDef.append(lg)
        else:
            lstLargDef.append(-1)
    return lstLargDef

def CompareModels(original,actuel):
    # retourne les données modifiées dans le modelobject original % actuel
    lstNews, lstCancels, lstModifs = [], [], []
    # l'id doit être en première position des données
    lstIdActuels = [x.donnees[0] for x in actuel]
    lstIdOriginaux = [x.donnees[0] for x in original]
    # retrouver l'original dans l'actuel
    for track in original:
        if track.donnees[0] in lstIdActuels:
            ix = lstIdActuels.index(track.donnees[0])
            if track.donnees == actuel[ix].donnees:
                continue
            if not actuel[ix].valide:
                continue
            else:
                lstModifs.append(actuel[ix].donnees)
        else: lstCancels.append(track.donnees)
    #repérer les nouveaux
    for track in actuel:
        if track.donnees[0] in lstIdOriginaux:
            continue
        elif not track.vierge: lstNews.append(track.donnees)
    return lstNews,lstCancels,lstModifs

# Conversion wx.Datetime % datetime.date

def DatetimeToWxdate(date):
    assert isinstance(date, (datetime.datetime, datetime.date))
    tt = date.timetuple()
    dmy = (tt[2], tt[1] - 1, tt[0])
    return wx.DateTime.FromDMY(*dmy)

def WxdateToDatetime(date):
    assert isinstance(date, wx.DateTime)
    if date.IsValid():
        ymd = map(int, date.FormatISODate().split('-'))
        return datetime.date(*ymd)
    else:
        return None

# Conversion des dates SQL aaaa-mm-jj

def DateSqlToWxdate(dateiso):
    # Conversion de date récupérée de requête SQL aaaa-mm-jj(ou déjà en datetime) en wx.datetime
    if dateiso == None : return None

    if isinstance(dateiso,datetime.date):
        return wx.DateTime.FromDMY(dateiso.day,dateiso.month-1,dateiso.year)

    if isinstance(dateiso,str) and len(dateiso) < 10:
        return wx.DateTime.FromDMY(int(dateiso[8:10]),int(dateiso[5:7]-1),int(dateiso[:4]))

def DateSqlToDatetime(dateiso):
    # Conversion de date récupérée de requête SQL aaaa-mm-jj (ou déjà en datetime) en datetime
    if dateiso == None : return None

    elif isinstance(dateiso,datetime.date):
        return dateiso

    elif isinstance(dateiso,str) and len(dateiso) >= 10:
        return datetime.date(int(dateiso[:4]),int(dateiso[5:7]),int(dateiso[8:10]))

def DateSqlToFr(dateiso):
    # Conversion de date récupérée de requête SQL aaaa-mm-jj en jj/mm/aaaa
    if not isinstance(dateiso, str) : dateiso = str(dateiso)
    if len(dateiso) < 10: return None
    dateiso = dateiso.strip()
    return '%s/%s/%s'%(dateiso[8:10],dateiso[5:7],dateiso[:4])

def DateFrToSql(datefr):
    # Conversion de date string française reçue en formats divers
    if not isinstance(datefr, str) : datefr = str(datefr)
    datefr = datefr.strip()
    # normalisation des formats divers
    datefr = FmtDate(datefr)
    # transposition
    if len(datefr) < 10: return None
    return '%s-%s-%s'%(datefr[6:10],datefr[3:5],datefr[:2])

def DateFrToWxdate(datefr):
    # Conversion d'une date chaîne jj?mm?aaaa en wx.datetime
    if not isinstance(datefr, str) : datefr = str(datefr)
    datefr = datefr.strip()
    if len(datefr) != 10: return None
    datefr = datefr.strip()
    try:
        dmy = (int(datefr[:2]), int(datefr[3:5]) - 1, int(datefr[6:10]))
        dateout = wx.DateTime.FromDMY(*dmy)
    except: dateout = None
    return dateout

def DateFrToDatetime(datefr):
    # Conversion de date française jj/mm/aaaa (ou déjà en datetime) en datetime
    if datefr == None :
        return None
    elif isinstance(datefr,datetime.date):
        return datefr
    elif isinstance(datefr,str) and len(datefr) >= 10:
        return datetime.date(int(datefr[:4]),int(datefr[5:7]),int(datefr[8:10]))

def WxDateToStr(dte,iso=False):
    # Conversion wx.datetime en chaîne
    if isinstance(dte, wx.DateTime):
        if iso: return dte.Format('%Y-%m-%d')
        else: return dte.Format('%d/%m/%Y')
    else: return str(dte)

def DatetimeToStr(dte,iso=False):
    # Conversion d'une date datetime ou wx.datetime en chaîne
    if isinstance(dte, wx.DateTime):
        if iso: return dte.Format('%Y-%m-%d')
        else: return dte.Format('%d/%m/%Y')
    elif isinstance(dte, datetime.date):
        dd = ("00" + str(dte.day))[-2:]
        mm = ("00" + str(dte.month))[-2:]
        yyyy = ("0000" + str(dte.year))[-4:]
        if iso: return "%s-%s-%s"%(yyyy,mm,dd)
        else: return "%s/%s/%s"%(dd,mm,yyyy)
    else: return str(dte)

# Formatages pour OLV -------------------------------------------------------------------------------------

def SetBgColour(self,montant):
    if montant > 0.0:
        self.SetBackgroundColour(wx.Colour(200, 240, 255))  # Bleu
    elif montant < 0.0:
        self.SetBackgroundColour(wx.Colour(255, 170, 200))  # Rose
    else:
        self.SetBackgroundColour(wx.Colour(200, 255, 180))  # Vert

def FmtDecimal(montant):
    if isinstance(montant,str): montant = montant.replace(',','.')
    if montant == None or montant == '' or float(montant) == 0:
        return ""
    strMtt = '{:,.2f} '.format(float(montant))
    strMtt = strMtt.replace(',',' ')
    return strMtt

def FmtInt(montant):
    if isinstance(montant,str):
        montant = montant.replace(',','.')
    try:
        x=float(montant)
    except: return ""
    if montant == None or montant == '' or float(montant) == 0:
        return ""
    strMtt = '{:,.0f} '.format(int(float(montant)))
    strMtt = strMtt.replace(',',' ')
    return strMtt

def FmtIntNoSpce(montant):
    if isinstance(montant,str):
        montant = montant.replace(',','.')
    try:
        x=float(montant)
    except: return ""
    if montant == None or montant == '' or float(montant) == 0:
        return ""
    strMtt = '{:.0f} '.format(int(float(montant)))
    return strMtt

def FmtPercent(montant):
    if isinstance(montant,str): montant = montant.replace(',','.')
    if montant == None or montant == '' or float(montant) == 0:
        return ""
    strMtt = '{:}% '.format(int(float(montant)))
    return strMtt

def FmtDate(date):
    strdate = ''
    if date == None or date in (wx.DateTime.FromDMY(1,0,1900),'',datetime.date(1900,1,1)):
        return ''
    if isinstance(date,str):
        date = date.replace('-','/')
        tpldate = date.split('/')
        if date == '00:00:00': strdate = ''
        elif len(tpldate)==3:
            strdate = ('00'+tpldate[0])[-2:]+'/'+('00'+tpldate[1])[-2:]+'/'+('20'+tpldate[2])[-4:]
        elif len(date) == 6:
            strdate = (date[:2] + '/' + date[2:4] + '/' + '20'+date[4:])
        elif len(date) == 8:
            strdate = (date[:2] + '/' + date[2:4] + '/' + date[4:])
    else:
        strdate = DatetimeToStr(date)
    return strdate

def FmtCheck(value):
    if value == False:
        return 'N'
    if value == True:
        return 'O'
    return ''

def FmtMontant(montant,prec=2,lg=None):
    out = ''
    if isinstance(montant,str):
        montant = montant.replace(',','.')
        try: montant = float(montant)
        except: pass
    if not isinstance(montant,(int,float)): montant = 0.0
    if float(montant) != 0.0:
        out = "{: ,.{prec}f} {:} ".format(montant,SYMBOLE,prec=prec).replace(',', ' ')
    if lg:
        out = (' '*lg + out)[-lg:]
    return out

def FmtSolde(montant):
    if isinstance(montant,str):montant = montant.replace(',','.')
    if montant == None or montant == '':
        return ""
    strMtt = '{:+,.2f} '.format(float(montant))
    strMtt = strMtt.replace(',',' ')+ SYMBOLE
    return strMtt

# Diverses fonctions-------------------------------------------------------------------------------------------

def Nz(param):
    # fonction Null devient zero, et extrait les chiffres d'une chaîne pour faire un nombre
    if isinstance(param,str):
        tmp = ''
        for x in param:
            if (ord(x) > 42 and ord(x) < 58):
                tmp +=x
        tmp = tmp.replace(',','.')
        lstval = tmp.split('.')
        if len(lstval)>=2: tmp = lstval[0] + '.' + lstval[1]
        param = tmp
    if isinstance(param,int):
        valeur = param
    else:
        try:
            valeur = float(param)
        except: valeur = 0.0
    return valeur

def ListToDict(lstCles,lstValeurs):
    dict = {}
    if isinstance(lstCles,list):
        for cle in lstCles:
            idx = lstCles.index(cle)
            dict[cle] = None
            if isinstance(lstValeurs, (list,tuple)) and len(lstValeurs) >= idx:
                dict[cle] = lstValeurs[idx]
    return dict

def DictToList(dic):
    lstCles = []
    lstValeurs = []
    if isinstance(dic,dict):
        for cle,valeur in dic.items():
            lstCles.append(cle)
            lstValeurs.append(valeur)
    return lstCles,lstValeurs

def PrefixeNbre(param):
    if not isinstance(param,str):
        return ''
    # extrait le préfixe chaîne d'un nombre
    radicalNbre = str(Nz(param))
    ix = len(param)
    if radicalNbre != '0.0':
        ix = param.find(radicalNbre[0])
    return param[:ix]

def LettreSuivante(lettre=''):
        # incrémentation d'un lettrage
        if not isinstance(lettre, str): lettre = 'A'
        if lettre == '': lettre = 'A'
        lastcar = lettre[-1]
        precars = lettre[:-1]
        if ord(lastcar) in (90, 122):
            if len(precars) == 0:
                precars = chr(ord(lastcar) - 25)
            else:
                precars = LettreSuivante(precars)
            new = precars + chr(ord(lastcar) - 25)
        else:
            new = precars + chr(ord(lastcar) + 1)
        return new

def IncrementeRef(ref):
    # incrémente une référence compteur constituée d'un préfixe avec un pseudo nombre ou pas
    pref = PrefixeNbre(ref)
    if len(ref) > len(pref):
        nbre = int(Nz(ref))+1
        lgnbre = len(str(nbre))
        nbrstr = '0'*lgnbre + str(nbre)
        refout = pref + nbrstr[-lgnbre:]
    else:
        # référence type lettrage
        refout = LettreSuivante(ref)
    return refout

def FinDeMois(date):
    # Retourne le dernier jour du mois dans le format reçu
    def action(wxdte):
        # action  calcul fin de mois sur les wx.DateTime
        if isinstance(wxdte,wx.DateTime):
            dteout = wx.DateTime.FromDMY(1,wxdte.GetMonth()+1,wxdte.GetYear())
            dteout -= wx.DateSpan(days=1)
            return dteout
        return None

    if isinstance(date,(datetime.date,datetime.datetime)):
        return WxdateToDatetime(action(DatetimeToWxdate(date)))

    if isinstance(date,str) and '/' in date:
        date = DateFrToWxdate(date)
        return WxDateToStr(action(date),iso=False)

    if isinstance(date,str) and '-' in date:
        date = DateSqlToWxdate(date)
        return WxDateToStr(action(date),iso=True)

    if isinstance(date,wx.DateTime):
        return action(date)
    return date

if __name__ == '__main__':
    import os
    os.chdir("..")
    app = wx.App(0)
    """
    print(FmtDecimal(1230.05189),FmtDecimal(-1230.05189),FmtDecimal(0))
    print(FmtSolde(8520.547),FmtSolde(-8520.547),FmtSolde(0))
    print(FmtMontant(8520.547),FmtMontant(-8520.547),FmtMontant(0))
    print(FmtDate('01022019'))
    print(SupprimeAccents("ÊLève!"))
    """
    print('ok')




