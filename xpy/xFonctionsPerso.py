#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import sys
import wx.html as html
import os
import webbrowser

def DateEngFr(textDate):
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateFrEng(textDate):
    text = str(textDate[6:10]) + "/" + str(textDate[3:5]) + "/" + str(textDate[:2])
    return text

# --------------------------------------------------------------------------------------------------------

def BoucleFrameOuverte(nom, WindowEnCours) :
    """ Est utilisée dans FrameOuverte """
    for children in WindowEnCours.GetChildren():
        if children.GetName() == nom : return children
        if len(children.GetChildren()) > 0 :
            tmp = BoucleFrameOuverte(nom, children)
            if tmp != None : return tmp
    return None

def FrameOuverte(nom) :
    """ Permet de savoir si une frame est ouverte ou pas..."""
    topWindow = wx.GetApp().GetTopWindow() 
    # Analyse le TopWindow
    if topWindow.GetName() == nom : return True
    # Analyse les enfants de topWindow
    reponse = BoucleFrameOuverte(nom, topWindow)
    return reponse

def SetModalFrameParente(frameActuelle):
    """ Rend modale la frame parente """
    try :
        frameActuelle.GetParent().GetTopLevelParent().MakeModal(True)
    except : 
        pass

# -------------------------------------------------------------------------------------------------------
# Fonction qui modifie le wx.StaticText pour gérer le redimensionnement des StaticText

class StaticWrapText(wx.StaticText):
    """A StaticText-like widget which implements word wrapping."""
    
    def __init__(self, *args, **kwargs):
        wx.StaticText.__init__(self, *args, **kwargs)

        # store the initial label
        self.__label = super(StaticWrapText, self).GetLabel()

        # listen for sizing events
        self.Bind(wx.EVT_SIZE, self.OnSize)
        
    def SetLabel(self, newLabel):
        """Store the new label and recalculate the wrapped version."""
        self.__label = newLabel
        self.__wrap()

    def GetLabel(self):
        """Returns the label (unwrapped)."""
        return self.__label
    
    def __wrap(self):
        """Wraps the words in label."""
        words = self.__label.split()
        lines = []

        # get the maximum width (that of our parent)
        max_width = self.GetParent().GetVirtualSizeTuple()[0]-20 # J'ai ajouté le -20 ici
        
        index = 0
        current = []

        for word in words:
            current.append(word)

            if self.GetTextExtent(" ".join(current))[0] > max_width:
                del current[-1]
                lines.append(" ".join(current))

                current = [word]

        # pick up the last line of text
        lines.append(" ".join(current))

        # set the actual label property to the wrapped version
        super(StaticWrapText, self).SetLabel("\n".join(lines))

        # refresh the widget
        self.Refresh()
        
    def OnSize(self, event):
        # dispatch to the wrap method which will 
        # determine if any changes are needed
        self.__wrap()
        self.GetParent().Layout()

# -------------------------------------------------------------------------------------------------------

class BarreTitre(wx.Panel):
    def __init__(self, parent, titre=(u"Titre"), infoBulle="", arrondis=False, couleurFondPanel=None):
        wx.Panel.__init__(self, parent, -1, size=(-1, 80))
        couleurFond = (70, 70, 70)
        # Contrôles
        self.barreTitre = wx.StaticText(self, -1, " " + titre)
        self.barreTitre.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.barreTitre.SetBackgroundColour(couleurFond)
        self.barreTitre.SetForegroundColour('White')
        # Panel
        self.SetBackgroundColour(couleurFond)
        self.SetToolTipString(infoBulle)
        self.barreTitre.SetToolTipString(infoBulle)
        # Positionnement
        sizer_base = wx.BoxSizer(wx.HORIZONTAL)
        sizer_base.Add(self.barreTitre, 0, wx.EXPAND|wx.ALL, 3)
        self.SetSizer(sizer_base)
        
        if arrondis == True :
            # Crée des coins arrondis
            self.couleurFondPanel = couleurFondPanel
            self.espaceBord = 0
            self.coinArrondi = 5
            self.hauteurTitre = 40
            self.couleurFondTitre = couleurFond
            # Bind pour dessin
            self.Bind(wx.EVT_PAINT, self.OnPaint)
            self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
   
         
    def OnPaint(self, event):
        dc= wx.PaintDC(self)
        dc= wx.BufferedDC(dc)
        largeurDC, hauteurDC= self.GetSizeTuple()
        dc.SetBackground(wx.Brush(self.couleurFondPanel))
        dc.Clear()       
        dc.SetBrush(wx.Brush(self.couleurFondTitre))
        dc.DrawRoundedRectangle(0+self.espaceBord, 0+self.espaceBord, largeurDC-(self.espaceBord*2), self.hauteurTitre, self.coinArrondi)

    def OnEraseBackground(self, event):
        pass 
        

# ---------------------------------------------------------------------------------------------------------------------------------------------------------

class PanelArrondi(wx.Panel):
    def __init__(self, parent, ID=-1, name="gadget", texteTitre=""):
        wx.Panel.__init__(self, parent, ID, name=name)
        self.texteTitre = texteTitre
        
        self.SetBackgroundColour((122, 161, 230))
        
        # Création fond
        self.espaceBord = 10
        self.coinArrondi = 5
        self.hauteurTitre = 17
        self.couleurFondDC = self.GetBackgroundColour()
        self.couleurFondCadre = (214, 223, 247)
        self.couleurFondTitre = (70, 70, 70)
        self.couleurBord = (70, 70, 70)
        self.couleurDegrade = (130, 190, 235)
        self.couleurTexteTitre = (255, 255, 255)
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)      
        self.Bind(wx.EVT_SIZE, self.OnSize)
         
    def OnPaint(self, event):
        dc= wx.PaintDC(self)
        dc= wx.BufferedDC(dc)
        largeurDC, hauteurDC= self.GetSizeTuple()
        
        # paint le fond
        dc.SetBackground(wx.Brush(self.couleurFondDC))
        dc.Clear()       
        
        # Cadre du groupe
        dc.SetBrush(wx.Brush(self.couleurFondCadre))
        dc.DrawRoundedRectangle(0+self.espaceBord, 0+self.espaceBord, largeurDC-(self.espaceBord*2), hauteurDC-(self.espaceBord*2), self.coinArrondi)
        # Barre de titre
        dc.SetBrush(wx.Brush(self.couleurFondTitre))
        dc.DrawRoundedRectangle(0+self.espaceBord, 0+self.espaceBord, largeurDC-(self.espaceBord*2), self.hauteurTitre+self.coinArrondi, self.coinArrondi)
        # Dégradé
        dc.GradientFillLinear((self.espaceBord+1, self.espaceBord+7, largeurDC-(self.espaceBord*2)-2, self.hauteurTitre-2), (214, 223, 247), (0, 0, 0), wx.NORTH)
        # Cache pour enlever l'arrondi inférieur de la barre de titre
        dc.SetBrush(wx.Brush(self.couleurFondCadre))
        dc.SetPen(wx.Pen(self.couleurFondCadre, 0))
        dc.DrawRectangle(self.espaceBord+1, self.espaceBord+self.hauteurTitre+1, largeurDC-(self.espaceBord*2)-2, self.coinArrondi+5)
        # Titre
        font = wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD) 
        dc.SetFont(font)
        dc.SetTextForeground(self.couleurTexteTitre)
        dc.DrawText(self.texteTitre, self.espaceBord+7, self.espaceBord+2)

    def OnEraseBackground(self, event):
        pass   
        
    def OnSize(self, event):
        self.Refresh() 
        event.Skip()
                        
# ----------------------------------------------------------------------------------------------------------------------------------------------------------
        
def sendTextMail():
    """ Envoyer un mail avec smtp """
    import smtplib
    try:
        addressTarget = ("test@wanadoo.fr",)
        smtpServer = 'smtp.orange.fr'
        sourceAddress = 'test@fPython.fr'
        MAIL_SUBJECT="sujet du mail"
        MAIL_CONTENT = _(u"ceci est le contenu du mail")
        
        server = smtplib.SMTP( smtpServer, '25', 'localhost' )
        msg = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % ( sourceAddress, ", ".join( addressTarget ), MAIL_SUBJECT))
        msg = msg + MAIL_CONTENT
        server.sendmail( sourceAddress, addressTarget, msg )
        server.quit()
        print("Envoi mail Ok")
    except smtplib.SMTPException:
        print(msg)

def EnvoyerMail(adresses = [], sujet="", message=""):
    """ Envoyer un Email avec le client de messagerie par défaut """
    if len(adresses) == 1 :
        commande = "mailto:%s" % adresses[0]
    else:
        commande = "mailto:%s" % adresses[0] + "?"
        if len(adresses) > 1 :
            commande+= "bcc=%s" % adresses[1]
        for adresse in adresses[2:] :
            commande+= "&bcc=%s" % adresse
    if sujet != "" : 
        if len(adresses) == 1 : 
            commande += "?"
        else :
            commande += "&"
        commande += "subject=%s" % sujet
    if message != "" : 
        if len(adresses) == 1 and sujet == "" : 
            commande += "?"
        else:
            commande += "&"
        commande += "body=%s" % message
    #print commande
    webbrowser.open(commande)

def CompareVersions(versionApp="", versionMaj=""):
    """ Compare 2 versions de TeamWorks """
    """ Return True si la version MAJ est plus récente """
    a,b = [[int(n) for n in version.split(".")] for version in [versionMaj, versionApp]]
    return a>b

def VideRepertoireTemp():
    """ Supprimer tous les fichiers du répertoire TEMP """
    listeFichiers = os.listdir("Temp")
    try :
        for nomFichier in listeFichiers :
            os.remove("Temp/" + nomFichier)
    except Exception:
        pass

def VideRepertoireUpdates(forcer=False):
    """ Supprimer les fichiers temporaires du répertoire Updates """
    listeReps = os.listdir("Updates")
    numVersionActuelle = GetVersionLogiciel()
    import shutil
    try :
        for nomRep in listeReps :
            resultat = CompareVersions(versionApp=numVersionActuelle, versionMaj=nomRep)
            if resultat == False or forcer == True :
                # Le rep est pour une version égale ou plus ancienne
                if numVersionActuelle != nomRep or forcer == True :
                    # La version est ancienne
                    print("Suppression du repertoire temporaire Updates %s" % nomRep)
                    listeFichiersRep = os.listdir("Updates/%s" % nomRep)
                    # Suppression du répertoire
                    shutil.rmtree("Updates/%s" % nomRep)
                else:
                    # La version est égale : on la laisse pour l'instant
                    pass
    except : 
        pass
        
def ListeImprimantes():
    """ Recherche les imprimantes installées """
    if sys.platform.startswith("win") :
        import win32print
        
    listeImprimantesLocales = []
    listeImprimantesReseau = []
    listeToutesImprimantes = []

    try:
        for (Flags,pDescription,pName,pComment) in list(win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL,None,1)):
            listeImprimantesLocales.append(pName)
            listeToutesImprimantes.append(pName)
    except : pass
        
    try:   
        for (Flags,pDescription,pName,pComment) in list(win32print.EnumPrinters(win32print.PRINTER_ENUM_CONNECTIONS,None,1)):
            listeImprimantesReseau.append(pName)
            listeToutesImprimantes.append(pName)
    except : pass
    
    nomImprimanteDefaut = ""
    try :
        nomImprimanteDefaut = win32print.GetDefaultPrinter()
    except : pass

    return nomImprimanteDefaut, listeToutesImprimantes, listeImprimantesLocales, listeImprimantesReseau

def EnleveAccents(chaineUnicode):
    """ Enlève les accents d'une chaine unicode """
    import unicodedata
    if type(chaineUnicode) == str : 
        chaineUnicode = chaineUnicode.decode("iso-8859-15")
    resultat = unicodedata.normalize('NFKD', chaineUnicode).encode('ascii','ignore')
    return resultat

def GetVersionLogiciel():
    """ Recherche du numéro de version du logiciel """
    fichierVersion = open("Versions.txt", "r")
    txtVersion = fichierVersion.readlines()[0]
    fichierVersion.close() 
    pos_debut_numVersion = txtVersion.find("n")
    pos_fin_numVersion = txtVersion.find("(")
    numVersion = txtVersion[pos_debut_numVersion+1:pos_fin_numVersion].strip()
    if len(numVersion) < 7 : numVersion = "0.0.0.0"
    return numVersion

def LanceFichierExterne(nomFichier) :
    """ Ouvre un fichier externe sous windows ou linux """
    nomSysteme = sys.platform
    if nomSysteme.startswith("win") : 
        nomFichier = nomFichier.replace("/", "\\")
        os.startfile(nomFichier)
    if "linux" in nomSysteme : 
        os.system("xdg-open " + nomFichier)

def Envoi_mail(adresseExpediteur="", listeDestinataires=[], listeDestinatairesCCI=[], sujetMail="", texteMail="", listeFichiersJoints=[], serveur="localhost", port=None, ssl=False, listeImages=[]):
    """ Envoi d'un mail avec pièce jointe
    import smtplib
    import os
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEBase import MIMEBase
    from email.MIMEText import MIMEText
    from email.MIMEImage import MIMEImage
    from email.MIMEAudio import MIMEAudio
    from email.Utils import COMMASPACE, formatdate
    from email import Encoders
    import mimetypes
    
    assert type(listeDestinataires)==list
    assert type(listeFichiersJoints)==list

    # Création du message
    msg = MIMEMultipart()
    msg['From'] = adresseExpediteur
    msg['To'] = COMMASPACE.join(listeDestinataires)
    msg['Bcc'] = COMMASPACE.join(listeDestinatairesCCI)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = sujetMail
##    msg.attach( MIMEText(texteMail, 'html') )
    msg.attach( MIMEText(texteMail.encode('utf-8'), 'html', 'utf-8') )
        
    # Attache des pièces jointes
    for fichier in listeFichiersJoints:
        ctype, encoding = mimetypes.guess_type(fichier)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compresses), so
            # use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        if maintype == 'text':
            fp = open(chemin)
            # Note : we should handle calculating the charset
            part = MIMEText(fp.read(), _subtype=subtype)
            fp.close()
        elif maintype == 'image':
            fp = open(fichier, 'rb')
            part = MIMEImage(fp.read(), _subtype=subtype)
            fp.close()
        elif maintype == 'audio':
            fp = open(fichier, 'rb')
            part = MIMEAudio(fp.read(), _subtype=subtype)
            fp.close()
        else:
            fp = open(fichier, 'rb')
            part = MIMEBase(maintype, subtype)
            part.set_payload(fp.read())
            fp.close()
            # Encode the payload using Base64
            Encoders.encode_base64(part)
        # Set the filename parameter
        nomFichier= os.path.basename(fichier)
        if type(nomFichier) == unicode :
            nomFichier = supprime_accent(nomFichier)
        part.add_header('Content-Disposition','attachment',filename=nomFichier)
        msg.attach(part)
        
    if ssl == False :
        # Envoi standard
        smtp = smtplib.SMTP(serveur)
    else:
        # Si identification SSL nécessaire :
        smtp = smtplib.SMTP(serveur, port)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(adresseExpediteur.encode('utf-8'), passwd.encode('utf-8'))
        
    smtp.sendmail(adresseExpediteur, listeDestinataires + listeDestinatairesCCI, msg.as_string())
    smtp.close()
    """

def supprime_accent(mot):
    """ supprime les accents du texte source """
    out = ""
    for c in mot:
        if c == u'é' or c == u'è' or c == u'ê':
            c = 'e'
        elif c == u'à':
            c = 'a'
        elif c == u'ù' or c == u'û':
            c = 'u'
        elif c == u'î':
            c = 'i'
        elif c == u'ç':
            c = 'c'
        out += c
    return str(out)

def Supprime_accent(texte):
    liste = [ (u"é", u"e"), (u"è", u"e"), (u"ê", u"e"), (u"ë", u"e"), (u"à", u"a"), (u"û", u"u"), (u"ô", u"o"), (u"ç", u"c"), (u"î", u"i"), (u"ï", u"i"), (u"/", u""), (u"\\", u""), ]
    for a, b in liste :
        texte = texte.replace(a, b)
        texte = texte.replace(a.upper(), b.upper())
    return texte

def Supprime_accent2(texte):
    liste = [ (u"é", u"e"), (u"è", u"e"), (u"ê", u"e"), (u"ë", u"e"), (u"à", u"a"), (u"û", u"u"), (u"ô", u"o"), (u"ç", u"c"), (u"î", u"i"), (u"ï", u"i"), ]
    for a, b in liste :
        texte = texte.replace(a, b)
        texte = texte.replace(a.upper(), b.upper())
    return texte

def OuvrirCalculatrice():
    if sys.platform.startswith("win") : LanceFichierExterne("calc.exe")
    if "linux" in sys.platform : os.system("gcalctool")

def Formate_taille_octets(size):
    """
    fonction qui prend en argument un nombre d'octets
    et renvoie la taille la plus adapté
    """
    seuil_Kio = 1024
    seuil_Mio = 1024 * 1024
    seuil_Gio = 1024 * 1024 * 1024

    if size > seuil_Gio:
        return "%.2f Go" % (size/float(seuil_Gio))
    elif size > seuil_Mio:
        return "%.2f Mo" % (size/float(seuil_Mio))
    elif size > seuil_Kio:
        return "%.2f Ko" % (size/float(seuil_Kio))
    else:
        return "%i o" % size

if __name__ == "__main__":
    pass
    