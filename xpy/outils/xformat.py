# Il faudra optimiser les fonctions de ce fichier mais plus tard
import decimal

SYMBOLE = "€"


def FloatToDecimal(montant=0, plusProche=False):
    """ Transforme un float en decimal """
    if not montant:
        montant = 0
    return decimal.Decimal("%.2f" % montant)


def FormateMontant(montant):
    if montant == None or montant == 0.0 or montant == FloatToDecimal(0.0):
        return u""
    return u"%.2f %s" % (montant, SYMBOLE)


def FormateSolde(montant):
    if montant == None or montant == 0.0 or montant == FloatToDecimal(0.0):
        return u""
    if montant >= decimal.Decimal(str("0.0")):
        return u"+ %.2f %s" % (montant, SYMBOLE)
    else:
        return u"- %.2f %s" % (-montant, SYMBOLE)


if __name__ == '__main__':
    print(FormateSolde(0.547))
    print(FloatToDecimal(0.055, plusProche=False))
