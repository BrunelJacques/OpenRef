# Il faudra optimiser les fonctions de ce fichier mais plus tard
SYMBOLE = "€"

import wx
import datetime

# Filtres OLV conditions possibles
CHOIX_FILTRES = {float:[
                            ('EGAL','égal à '),
                            ('DIFFERENT','différent de '),
                            ('INF','inférieur à '),
                            ('INFEGAL','inférieur ou égal à '),
                            ('SUP','supérieur à '),
                            ('SUPEGAL','supérieur ou égal à ')],
                 int:[
                            ('EGAL','égal à '),
                            ('DIFFERENT','différent de '),
                            ('INF','inférieur à '),
                            ('INFEGAL','inférieur ou égal à '),
                            ('SUP','supérieur à '),
                            ('SUPEGAL','supérieur ou égal à ')],
                 bool:[
                            ('EGAL','égal à '),
                            ('DIFFERENT','différent de '),],
                 wx.DateTime: [
                            ('EGAL', 'égal à '),
                            ('DIFFERENT', 'différent de '),
                            ('INF', 'avant '),
                            ('INFEGAL', 'avant ou égal à '),
                            ('SUP', 'après '),
                            ('SUPEGAL', 'après ou égal à ')],
                 datetime.date: [
                            ('EGAL', 'égal à '),
                            ('DIFFERENT', 'différent de '),
                            ('INF', 'avant '),
                            ('INFEGAL', 'avant ou égal à '),
                            ('SUP', 'après '),
                            ('SUPEGAL', 'après ou égal à ')],
                 datetime.datetime: [
                            ('EGAL', 'égal à '),
                            ('DIFFERENT', 'différent de '),
                            ('INF', 'avant '),
                            ('INFEGAL', 'avant ou égal à '),
                            ('SUP', 'après '),
                            ('SUPEGAL', 'après ou égal à ')],
                 str:[
                            ('CONTIENT','contient '),
                            ('CONTIENTPAS','ne contient pas '),
                            ('COMMENCE','commence par '),
                            ('DIFFERENT','différent de '),
                            ('EGAL','égal à '),
                            ('PASVIDE',"pas à blanc "),
                            ('VIDE','est à blanc '),
                            ('DANS','dans la liste '),
                            ('INFEGAL', 'inférieur ou égal à '),
                            ('SUPEGAL', 'supérieur ou égal à ')],
}

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

# Formatages--------------------------------------------------------------------------------------------------

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
    if date == None or date == wx.DateTime.FromDMY(1,0,1900) or date == '':
        return ''
    if isinstance(date,str):
        date = date.replace('-','/')
        tpldate = date.split('/')
        if len(tpldate)==3:
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
        if len(lstval)>=2: tmp = lstval[0] + "." + lstval[1]
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
        nbrstr = "0"*lgnbre + str(nbre)
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

    if isinstance(date,str) and "/" in date:
        date = DateFrToWxdate(date)
        return WxDateToStr(action(date),iso=False)

    if isinstance(date,str) and "-" in date:
        date = DateSqlToWxdate(date)
        return WxDateToStr(action(date),iso=True)

    if isinstance(date,wx.DateTime):
        return action(date)
    return date

if __name__ == '__main__':
    """
    print(FmtDecimal(1230.05189),FmtDecimal(-1230.05189),FmtDecimal(0))
    print(FmtSolde(8520.547),FmtSolde(-8520.547),FmtSolde(0))
    print(FmtMontant(8520.547),FmtMontant(-8520.547),FmtMontant(0))
    """

    print(FmtDate('01022019'))




