# Il faudra optimiser les fonctions de ce fichier mais plus tard
SYMBOLE = "€"

import wx
import datetime

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
                            ('DIFFERENT','différent de '),
                            ('EGAL','égal à '),
                            ('PASVIDE',"pas à blanc "),
                            ('VIDE','est à blanc '),
                            ('INFEGAL', 'inférieur ou égal à '),
                            ('SUPEGAL', 'supérieur ou égal à ')],
}

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

    if isinstance(dateen,str) and len(dateen) < 10:
        return datetime(int(dateen[:4]),int(dateen[5:7]),int(dateen[8:10]))

def DateStrToWxdate(date,iso=False):
    # Conversion d'une date chaîne jj-mm-aaaa en wx.datetime
    if not isinstance(date, str) : date = str(date)
    if len(date) < 10: return None
    if iso:
        dmy = (int(date[8:10]), int(date[5:7]) - 1, int(date[:4]))
    else:
        dmy = (int(date[:2]), int(date[3:5]) - 1, int(date[6:10]))
    dateout = wx.DateTime.FromDMY(*dmy)
    dateout.SetCountry(5)
    return dateout

def DatetimeToStr(dte,iso=False):
    # Conversion d'une date datetime ou wx.datetime en chaîne
    if isinstance(dte, wx.DateTime):
        if iso: return dte.Format('%Y-%m-%d')
        else: return dte.Format('%d/%m/%Y')
    elif isinstance(dte, datetime.date):
        if iso: return "%s-%s-%s"%(dte.year,dte.month,dte.day)
        else: return "%s/%s/%s"%(dte.day,dte.month,dte.year)
    else: return str(dte)

def FmtDecimal(montant):
    if isinstance(montant,str): montant.replace(',','.')
    if montant == None or montant == '' or float(montant) == 0:
        return ""
    strMtt = '{:,.2f} '.format(float(montant))
    strMtt = strMtt.replace(',',' ')
    return strMtt

def FmtInt(montant):
    if isinstance(montant,str):
        montant.replace(',','.')
    try:
        x=float(montant)
    except: return ""
    if montant == None or montant == '' or float(montant) == 0:
        return ""
    strMtt = '{:,.0f} '.format(int(float(montant)))
    strMtt = strMtt.replace(',',' ')
    return strMtt

def FmtPercent(montant):
    if isinstance(montant,str):montant.replace(',','.')
    if montant == None or montant == '' or float(montant) == 0:
        return ""
    strMtt = '{:}% '.format(int(float(montant)))
    return strMtt

def FmtDate(date):
    if date == None or date == wx.DateTime.FromDMY(1,0,1900) or date == '':
        return ''
    if isinstance(date,str):
        tpldate = date.split('-')
        if len(tpldate)!=3: return ''
        strdate = tpldate[2]+'/'+tpldate[1]+'/'+tpldate[0]
    else:
        strdate = DatetimeToStr(date)
    return strdate

def FmtMontant(montant):
    if isinstance(montant,str): montant.replace(',','.')
    if montant == None or montant == '' or float(montant) == 0.0:
        return ""
    strMtt = '{:,.2f} '.format(float(montant))
    strMtt = strMtt.replace(',',' ')+ SYMBOLE
    return strMtt

def FmtSolde(montant):
    if isinstance(montant,str):montant.replace(',','.')
    if montant == None or montant == '':
        return ""
    strMtt = '{:+,.2f} '.format(float(montant))
    strMtt = strMtt.replace(',',' ')+ SYMBOLE
    return strMtt

def Nz(param):
    # fonction Null devient zero
    valeur = 0.0
    try:
        valeur = float(param)
    except: pass
    return valeur

if __name__ == '__main__':
    print(FmtDecimal(1230.05189),FmtDecimal(-1230.05189),FmtDecimal(0))
    print(FmtSolde(8520.547),FmtSolde(-8520.547),FmtSolde(0))
    print(FmtMontant(8520.547),FmtMontant(-8520.547),FmtMontant(0))

