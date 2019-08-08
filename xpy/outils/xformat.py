# Il faudra optimiser les fonctions de ce fichier mais plus tard
SYMBOLE = "€"

def FmtDecimal(montant):
    if montant == None or float(montant) == 0.0 :
        return ""
    strMtt = '{:,.2f} '.format(montant)
    strMtt = strMtt.replace(',',' ')
    return strMtt

def FmtMontant(montant):
    if montant == None or float(montant) == 0.0:
        return ""
    strMtt = '{:,.2f} '.format(montant)
    strMtt = strMtt.replace(',',' ')+ SYMBOLE
    return strMtt

def FmtSolde(montant):
    if montant == None :
        return u""
    strMtt = '{:+,.2f} '.format(montant)
    strMtt = strMtt.replace(',',' ')+ SYMBOLE
    return strMtt


if __name__ == '__main__':
    print(FmtDecimal(1230.05189),FmtDecimal(-1230.05189),FmtDecimal(0))
    print(FmtSolde(8520.547),FmtSolde(-8520.547),FmtSolde(0))
    print(FmtMontant(8520.547),FmtMontant(-8520.547),FmtMontant(0))

