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
def DateSqlToWxdate(dateen):
    # Conversion de date récupérée de requête SQL aaaa-mm-jj(ou déjà en datetime) en wx.datetime
    if dateen == None : return None

    if isinstance(dateen,datetime.date):
        return wx.DateTime.FromDMY(dateen.day,dateen.month-1,dateen.year)

    if isinstance(dateen,str) and len(dateen) < 10:
        return wx.DateTime.FromDMY(int(dateen[8:10]),int(dateen[5:7]-1),int(dateen[:4]))

def DateSqlToDatetime(dateen):
    # Conversion de date récupérée de requête SQL aaaa-mm-jj (ou déjà en datetime) en datetime
    if dateen == None : return None

    if isinstance(dateen,datetime.date):
        return dateen

    if isinstance(dateen,str) and len(dateen) >= 10:
        return datetime.date(int(dateen[:4]),int(dateen[5:7]),int(dateen[8:10]))
    return dateen

def DateSqlToIso(dateen):
    # Conversion de date récupérée de requête SQL aaaa-mm-jj en jj/mm/aaaa
    if not isinstance(dateen, str) : dateen = str(dateen)
    if len(dateen) < 10: return None
    dateen = dateen.strip()
    return '%s/%s/%s'%(dateen[8:10],dateen[5:7],dateen[:4])

def DateIsoToSql(dateen):
    # Conversion de date récupérée de requête SQL aaaa-mm-jj en jj/mm/aaaa
    if not isinstance(dateen, str) : dateen = str(dateen)
    if len(dateen) < 10: return None
    dateen = dateen.strip()
    return '%s-%s-%s'%(dateen[6:10],dateen[3:5],dateen[:2])

# Conversion dates jj?mm?aaaa
def DateStrToWxdate(date,iso=False):
    # Conversion d'une date chaîne jj-mm-aaaa en wx.datetime
    if not isinstance(date, str) : date = str(date)
    if len(date) != 10: return None
    date = date.strip()
    try:
        if iso:
            dmy = (int(date[8:10]), int(date[5:7]) - 1, int(date[:4]))
        else:
            dmy = (int(date[:2]), int(date[3:5]) - 1, int(date[6:10]))
        dateout = wx.DateTime.FromDMY(*dmy)
    except: dateout = None
    #dateout.SetCountry(5) ???
    return dateout

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
        tpldate = date.split('/')
        if len(tpldate)==3:
            strdate = tpldate[0]+'/'+tpldate[1]+'/'+tpldate[2]
        tpldate = date.split('-')
        if len(tpldate) == 3:
            strdate = tpldate[2] + '/' + tpldate[1] + '/' + tpldate[0]
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
    valeur = 0.0
    if isinstance(param,str):
        tmp = ''
        for x in param:
            if (ord(x) > 42 and ord(x) < 58):
                tmp +=x
        tmp = tmp.replace(',','.')
        lstval = tmp.split('.')
        if len(lstval)>=2: tmp = lstval[0] + "." + lstval[1]
        param = tmp
    try:
        valeur = float(param)
    except: pass
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

def FinDeMois(date,iso=False):
    # Retourne le dernier jour du mois
    def action(wxdte):
        if isinstance(wxdte,wx.DateTime):
            dteout = wx.DateTime.FromDMY(1,wxdte.GetMonth()+1,wxdte.GetYear())
            dteout -= wx.DateSpan(days=1)
            return dteout
        return None

    if isinstance(date,str):
        date = DateStrToWxdate(date)
        return WxDateToStr(action(date),iso)

    if isinstance(date,(datetime.date,datetime.datetime)):
        date = DatetimeToWxdate(date)
        return WxdateToDatetime(action(date))

    if isinstance(date,wx.DateTime):
        return action(date)
    return date

if __name__ == '__main__':
    """
    print(FmtDecimal(1230.05189),FmtDecimal(-1230.05189),FmtDecimal(0))
    print(FmtSolde(8520.547),FmtSolde(-8520.547),FmtSolde(0))
    print(FmtMontant(8520.547),FmtMontant(-8520.547),FmtMontant(0))
    """

    print(DateSqlToIso('2020-08-31'))



