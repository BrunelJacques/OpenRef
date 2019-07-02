import os
import platform


def LanceFichierExterne(nomFichier) :
    """ Ouvre un fichier externe sous windows ou linux """
    if platform.system() == "Windows":
        nomFichier = nomFichier.replace("/", "\\")
        os.startfile(nomFichier)
    if platform.system() == "Linux":
        os.system("xdg-open " + nomFichier)
