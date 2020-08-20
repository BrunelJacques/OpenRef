import wx,os
import platform
import csv


def LanceFichierExterne(nomFichier) :
    """ Ouvre un fichier externe sous windows ou linux """
    if platform.system() == "Windows":
        nomFichier = nomFichier.replace("/", "\\")
        os.startfile(nomFichier)
    if platform.system() == "Linux":
        os.system("xdg-open " + nomFichier)

def GetFichierCsv(nomFichier,delimiter="\t",detect=True):
    if platform.system() == "Windows":
        nomFichier = nomFichier.replace("/", "\\")
    # ouverture du fichier en lecture seule
    fichier = open(nomFichier, "rt")
    # csv.reader est la fonction qui lit le fichier ouvert
    donnees = [x for x in csv.reader(fichier,delimiter=delimiter)]
    fichier.close()
    if detect and len(donnees[0]) == 1:
        # le séparateur n'etait pas le bon ou inexistant, essais avec ';'
        donnees = GetFichierCsv(nomFichier, delimiter=";")
    return donnees

if __name__ == '__main__':
    app = wx.App(0)
    os.chdir("..")
    donnees = GetFichierCsv("c:/temp/fichierTestPointVirgule.csv")
    for ligne in donnees:
        print(ligne)
    app.MainLoop()

