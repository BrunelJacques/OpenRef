#!/usr/bin/env python
# -*- coding: utf8 -*-

#------------------------------------------------------------------------
# Application :    OpenRef, Description des tables
# Auteurs:          Jacques BRUNEL
# Copyright:       (c) 2019-06     Cerfrance Provence
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


DB_TABLES = {
    'cFilière' : [
        ("IDagc",  'varchar(8)', ' NOT NULL', "Spécifique à une AGC"),
        ("IDfilière",  'varchar(128)', ' NOT NULL', "Désignation courte de la filière"),
        ("NomFilière",  'mediumtext', '  ', "Désignation longue ou commentaire pluri lignes"),
        ("Requête",  'mediumtext', '  ', "requête SQL permettant de sélectionner la population"),
        ],
    'cGroupe' : [
        ("IDagc",  'varchar(8)', ' NOT NULL', "Spécifique à une AGC"),
        ("IDgroupe",  'varchar(128)', ' NOT NULL', "Désignation courte du groupe"),
        ("NomGroupe",  'mediumtext', '  ', "Désignation longue ou commentaire pluri lignes"),
        ("Membres",  'mediumtext', '  ', "liste des ID des exploitations retenues dans le groupe"),
        ],
    'cType' : [
        ("IDtype",  'varchar(8)', ' NOT NULL', "Identifiant unique"),
        ("NomType",  'varchar(128)', ' DEFAULT NULL', "Nom du type de coût ou de produit"),
        ("Produits",  'tinyint(1)', ' DEFAULT NULL', "Usage pour les produits ou ateliers"),
        ("Coûts",  'int(11)', ' DEFAULT NULL', "Usage pour les coûts"),
        ],
    'cPlanComptes':[
                   ("IDplanCompte",'varchar(8)','NOT NULL COMMENT', "Radical des comptes entrant dans cet item"),
                   ("Abrégé",'varchar(16)','DEFAULT NULL COMMENT', "Désignation courte"),
                   ("NomCompte",'varchar(128)','DEFAULT NULL COMMENT', "Désignation longue"),
                   ("Type",'varchar(128)','DEFAULT NULL COMMENT', "Liste des TypesProduit ou TypesCoût qui alimenteront la zone équivalente dans les produits")
        ],
    'mAtelier' : [
        ("IDMatelier",  'varchar(16)', ' NOT NULL', "Sert de clé externe"),
        ("NomAtelier",  'varchar(40)', ' DEFAULT NULL', "Nom du modèle d'atelier"),
        ("UnitéCapacité",  'varchar(8)', ' DEFAULT NULL', "Libellé de l'unité utilisée pour mesurer la capacité"),
        ("IDagc",  'varchar(16)', ' DEFAULT NULL', "Atelier spécifique à une agc, si null s'applique à l'ensemble"),
        ("TypesProduit",  'varchar(128)', ' DEFAULT NULL', "Liste des types de produits auxquels par défaut se rattachent les produits de l'atelier"),
        ("IDsecteur",  'varchar(8)', ' DEFAULT NULL', "La définition de secteurs d'activité permet de filtrer ou regrouper les ateliers"),
        ],
    'mCoût' : [
        ("IDMatelier",  'varchar(16)', ' NOT NULL', "Rattachement à un modèle d'atelier"),
        ("IDMcoût",  'varchar(16)', ' NOT NULL', "Sert de clé externe (associé avec IDMatelier)"),
        ("NomCoût",  'varchar(64)', ' DEFAULT NULL', "Nom du modèle de coût"),
        ("SaisirQté",  'tinyint(1)', ' DEFAULT NULL', "OUI si la saisie de quantités est attendue"),
        ("UnitéQté",  'varchar(8)', ' DEFAULT NULL', "Unité à utliser pour la saisie de quantités"),
        ("SaisirDeltaStock",  'tinyint(1)', ' DEFAULT NULL', "Oui si la saisies des variations de stocks est attendue"),
        ("SaisirEffectif",  'tinyint(1)', ' DEFAULT NULL', "Oui si la saisie des effectifs est attendue"),
        ("CptCoût",  'varchar(128)', ' DEFAULT NULL', "Liste des comptes entrant dans le calcul, éventuellement préfixés d'un signe"),
        ("MotsCles",  'varchar(200)', ' DEFAULT NULL', "Liste de mots clés ou tuple pour automate de génération"),
        ("TypesCoût",  'varchar(128)', ' DEFAULT NULL', "Liste des types de coûts auquel il se rattache naturellement"),
        ],
    'mProduit' : [
        ("IDMatelier",  'varchar(16)', ' NOT NULL', "Rattachement à un atelier"),
        ("IDMproduit",  'varchar(16)', ' NOT NULL', "Sert de clé externe (associé avec IDMatelier)"),
        ("NomProduit",  'varchar(64)', ' DEFAULT NULL', "Nom du modèle de produit"),
        ("MoisRécolte",  'varchar(2)', ' DEFAULT NULL', "Mois habituel servant à calculer l'année de récolte"),
        ("ProdPrincipal",  'tinyint(1)', ' DEFAULT NULL', "En général est-il un produit principal"),
        ("SaisirSurface",  'tinyint(1)', ' DEFAULT NULL', "La saisie de la sole est-elle attendue"),
        ("UniteSAU",  'varchar(8)', ' DEFAULT NULL', "Unité de surface à utiliser"),
        ("coefHa",  'float', ' DEFAULT NULL', "Rapport de l'unité de surface à l'ha"),
        ("SaisirQté1",  'tinyint(1)', ' DEFAULT NULL', "La saisie de la qté1 est elle attendue"),
        ("UnitéQté1",  'varchar(10)', ' DEFAULT NULL', "Unité de qté1 à utiliser"),
        ("coefUGB",  'float', ' DEFAULT NULL', "Les Qtés1 seront transformées en UGB selon ce rapport"),
        ("SaisirQté2",  'tinyint(1)', ' DEFAULT NULL', "idem Qte1"),
        ("UnitéQté2",  'varchar(10)', ' DEFAULT NULL', "idem Qte1"),
        ("SaisirEffectif",  'tinyint(1)', ' DEFAULT NULL', "La saisie de l'effectif moyen est-il attendue"),
        ("SaisirDeltaStock",  'tinyint(1)', ' DEFAULT NULL', "Saisie de la variation de stock, attendue"),
        ("SaisirStockFin",  'tinyint(1)', ' DEFAULT NULL', "Saisie des stocks fin, attendue"),
        ("PUmaxi",  'float', ' DEFAULT NULL', "Contrôle lors de la saisie"),
        ("PUmini",  'float', ' DEFAULT NULL', "Contrôle lors de la saisie"),
        ("RdtMaxi",  'float', ' DEFAULT NULL', "Contrôle lors de la saisie"),
        ("RdtMini",  'float', ' DEFAULT NULL', "Contrôle lors de la saisie"),
        ("CptProduit",  'varchar(128)', ' DEFAULT NULL', "Liste des radicaux des comptes entrant dans le calcul, éventuellement préfixés d'un signe"),
        ("MotsCles",  'varchar(200)', ' DEFAULT NULL', "Saisie de mots clés ou tuples pour automate de génération"),
        ("CtrlBloquant",  'varchar(128)', ' DEFAULT NULL', "Les contrôles doivent-ils bloquer la saisie si négatif"),
        ("TypesProduit",  'varchar(128)', ' DEFAULT NULL', "Liste des types de produits auxquels il se rattache"),
        ],
    '_Ateliers' : [
        ("IDdossier",  'int(8)', ' NOT NULL', "Agc, exploitation, exercice"),
        ("IDMatelier",  'varchar(16)', ' NOT NULL', "ID de l'atelier modèle"),
        ("NomPersonnalisé",  'mediumtext', '  ', "Nom de l'atelier plus détaillé que le modèle"),
        ("Capacité",  'float', ' DEFAULT NULL', "Capacité de l'atelier en nombre de l'unité précisée dans le modèle d'atelier"),
        ("ProrataStructure",  'int(2)', ' DEFAULT NULL', "Permet d'affecter un poids de la structure différent d'une répartition par défaut selon les montant de la production de l'année"),
        ("AutreProduit",  'float', ' DEFAULT NULL', "Valeur calculée ou forcée des autres produits de l'atelier non détaillés par la table produits"),
        ("CPTAutreProduit",  'varchar(128)', '  ', "Liste de comptes pour déterminer la valeur autre produit par défaut"),
        ("Subventions",  'float', ' DEFAULT NULL', " Valeur calculée ou forcée des subventions affectées à l'atelier"),
        ("CPTSubvention",  'varchar(128)', '  ', "Liste de comptes pour déterminer la valeur des subventions affectées à l'atelier"),
        ("Comm",  'float', ' DEFAULT NULL,', ''),
        ("CPTComm",  'varchar(128)', '  ', "Liste de comptes pour déterminer la valeur de la commercialisation non détaillée dans les coûts"),
        ("Conditionnement",  'float', ' DEFAULT NULL,', ''),
        ("CPTConditionnement",  'varchar(128)', '  ', "Liste de comptes pour déterminer la valeur du conditionnement non détaillé dans les coûts"),
        ("AutresAppros",  'float', ' DEFAULT NULL,', ''),
        ("CPTAppros",  'varchar(128)', '  ', " Liste de comptes pour déterminer la valeur de l'approvisionnement non détaillé dans les coûts"),
        ("AutresServices",  'float', ' DEFAULT NULL,', ''),
        ("CPTServices",  'varchar(128)', '  ', " Liste de comptes pour déterminer la valeur des services extérieurs non détaillé dans les coûts"),
        ("AmosSpécif",  'float', ' DEFAULT NULL,', ''),
        ("CPTAmosSpécif",  'varchar(128)', '  ', " Liste de comptes pour déterminer la valeur de l'amortissement spécifique à l'atelier non détaillé dans les coûts"),
        ("Validation",  'tinyint(1)', ' DEFAULT NULL', "Si les champs montants ou texte sont 'Null', ils sont remplacés par les valeurs calculées et ne seront plus modifiés automatiquement par calcul, sauf demande expresse."),
        ],
    '_Coûts' : [
        ("IDdossier",  'int(8)', ' NOT NULL', "Agc, Exploitation, Clôture"),
        ("IDMatelier",  'varchar(16)', ' NOT NULL', "Code de l'atelier Modèle dont il hérite"),
        ("IDMcoût",  'varchar(16)', ' NOT NULL', "Code du coût Modèle dont il hérite"),
        ("QteCoût",  'float', ' DEFAULT NULL', "Somme des quantités dont la nature est celle du modèle pour quantité 1"),
        ("Comptes",  'varchar(128)', ' DEFAULT NULL', "Liste des radicaux des comptes entrant dans le calcul de la charge, éventuellement préfixé d'un signe"),
        ("Charge",  'float', ' DEFAULT NULL', "Précalculé c'est le cumul des comptes précités avec prorata correspondant à chacun (100% par défaut), l avaleur a pu être forcée après calcul et reste figée si validation de l'atelier"),
        ("DeltaStock",  'float', ' DEFAULT NULL', "Précalculé par les comptes précités filtrés sur 603 et 713"),
        ("TypesCoût",  'varchar(128)', ' DEFAULT NULL', "Liste des types de coût de la table cTypeCoût, auxquels se rattache ce coût"),
        ("NoLigne",  'int(2)', ' DEFAULT NULL', "Ordre d'apparition de la ligne dans un tableau de bord"),
        ],
    '_Ident' : [
        ("Iddossier",  'int(8)', ' NOT NULL',"Identifiant unique repris comme clé externe dans les autres tables"),
        ("IDagc",  'varchar(8)', ' NOT NULL', ''),
        ("IDexploitation",  'varchar(8)', ' NOT NULL,', ''),
        ("Clôture",  'date', ' NOT NULL', ''),
        ("IDuser",  'varchar(64)', ' DEFAULT NULL', "Trace du dernier domaine.user qui a modifié le dossier"),
        ("IDlocalisation",  'varchar(8)', ' DEFAULT NULL', "Agence (Implantation) de la compta qui a servi à l'import (trace du programme d'import)"),
        ("IDjuridique",  'varchar(8)', ' DEFAULT NULL', "Forme juridique de l'exploitation du dossier"),
        ("NomExploitation",  'varchar(128)', ' DEFAULT NULL,', ''),
        ("IDCodePostal",  'varchar(8)', ' DEFAULT NULL,', ''),
        ("Siren",  'int(9)', ' DEFAULT NULL', "Peut servir pour un Siret"),
        ("IDnaf",  'varchar(16)', ' DEFAULT NULL', "Naf classique ou étendu"),
        ("Filières",  'varchar(2048)', ' DEFAULT NULL', "Liste des filières pour lesquelles le dossier a matché lors d'un appel de constitution d'une filière"),
        ("NbreMois",  'int(2)', ' DEFAULT NULL', "Nombre de mois de l'exercice"),
        ("Fiscal",  'varchar(8)', ' DEFAULT NULL', "Rapporte le code fiscal utilisé dans l'AGC pour ce dossier (pas d'ID contrôlé)"),
        ("ImpSoc",  'tinyint(1)', ' DEFAULT NULL', "Oui = fiscalité IS, NON à l'IR, Null si inconnu"),
        ("Caf",  'float', ' DEFAULT NULL', "Valeurs du tableau de financement, jusqu'à la variation du FDR vérifiable par la balance"),
        ("SubvReçues",  'float', ' DEFAULT NULL,', ''),
        ("Cessions",  'float', ' DEFAULT NULL,', ''),
        ("NvxEmprunts",  'float', ' DEFAULT NULL,', ''),
        ("Apports",  'float', ' DEFAULT NULL,', ''),
        ("Investissements",  'float', ' DEFAULT NULL,', ''),
        ("RbtEmprunts",  'float', ' DEFAULT NULL,', ''),
        ("Prélèvements",  'float', ' DEFAULT NULL,', ''),
        ("RemAssociés",  'float', ' DEFAULT NULL,', ''),
        ("Productions",  'mediumblob', '  ', "Ce commentaire sur la production reprendra dans un premier temps la récupération du descriptif de l'exploitation dans la compta."),
        ("Analyse",  'mediumblob', '  ', "Commentaire appuyant l'analyse "),
        ("Remarques",  'mediumblob', '  ', "Analyse générale à adjoindre à celle du tableau de financement. Les trois analyses ont vocation à être concaténées dans les documents de présentation des comptes"),
        ("SAUfermage",  'float', ' DEFAULT NULL', "Surfaces de l'ensemble de l'exploitation"),
        ("SAUmétayage",  'float', ' DEFAULT NULL,', ''),
        ("SAUfvd",  'float', ' DEFAULT NULL', "SAU faire valoir direct"),
        ("SAUmad",  'float', ' DEFAULT NULL', "Surface mise à disposition par les associés ou autre"),
        ("SAU",  'float', ' DEFAULT NULL', "SAU globale si elle n'est pas détaillé ci-dessus"),
        ("NbreAssociés",  'float', ' DEFAULT NULL', "Nombre de personnes quelque soit sa participation"),
        ("MOexploitants",  'float', ' DEFAULT NULL', "en UTH somme des fractions de temps complet d'exploitants"),
        ("MOpermanents",  'float', ' DEFAULT NULL', "en UTH"),
        ("MOsaisonniers",  'float', ' DEFAULT NULL', "en UTH"),
        ("NbElemCar",  'float', ' DEFAULT "1"', "Nombre d'éléments caractéristiques de l'exploitation (diviseur signifiant)"),
        ("ElemCar",  'varchar(8)', ' DEFAULT "Unité"', "Nature de l'élément caractéristique de l'exploitation"),
        ("Analytique",  'varchar(32)', ' DEFAULT NULL', "Signature informatique de la méthode analytique qui a permis de récupérer l'information avant sa validation, et de l'intervenant qui a validé l'info"),
        ("Validé",  'tinyint(1)', ' DEFAULT NULL', "Fige les infos pour les automates de traitement qui ignoreront alors le dossier"),
        ],
    '_Produits' : [
        ("IDdossier",  'int(8)', ' NOT NULL', "Agc, Exploitation, Clôture"),
        ("IDMatelier",  'varchar(16)', ' NOT NULL', "Code de l'atelier modèle duquel il hérite "),
        ("IDMproduit",  'varchar(16)', ' NOT NULL', "Code du produit modèle définissant ses propriétés"),
        ("NomProdForcé",  'varchar(32)', ' DEFAULT NULL', "Peut remplacer le nom du produit modèle donné par défaut"),
        ("AnnéeRécolte",  'varchar(4)', ' DEFAULT NULL', "Pourra être utilisé dans les tableaux de bord comme précision ou pour des filtres"),
        ("SurfaceProd",  'float', ' DEFAULT NULL', "Mesure de la sole dans l'unité précisée dans le modèle de produit"),
        ("Comptes",  'varchar(128)', ' DEFAULT NULL', "Liste des comptes retenus dans le dossier (par défaut liste prise dans le modèle)"),
        ("Quantité1",  'float', ' DEFAULT NULL', "Quantités saisies dans la compta pour l'unité Qté1 précisée dans le modèle"),
        ("Quantité2",  'float', ' DEFAULT NULL', "Quantités saisies dans la compta pour l'unité Qté2 précisée dans le modèle"),
        ("EffectifMoyen",  'float', ' DEFAULT NULL', "Moyenne des quantités début et fin prise dans les comptes de stocks"),
        ("Ventes",  'float', ' DEFAULT NULL', "comptes 70 et 72 de la liste des comptes"),
        ("AchatAnmx",  'float', ' DEFAULT NULL', "comptes 604 de la liste des comptes"),
        ("DeltaStock",  'float', ' DEFAULT NULL', "Comptes 71 de la liste des comptes"),
        ("AutreProd",  'float', ' DEFAULT NULL', "Autres comptes 7 de la liste non pris ci-dessus"),
        ("StockFin",  'float', ' DEFAULT NULL', "Somme des quantités saisies dans les Comptes 3 de la liste des comptes"),
        ("ProdPrincipal",  'tinyint(1)', ' DEFAULT NULL', "Oui si le produit n'est pas accessoire"),
        ("TypesProduit",  'varchar(128)', ' DEFAULT NULL', "Liste des types de produits auquel il se rattache par sa nature"),
        ("NoLigne",  'int(2)', ' DEFAULT NULL', ''),
    ]}

def GetChamps(table,tous = True,reel=False,deci=False,dte=False):
    lstChamps = []
    # les params d'un type précisé désactivent le param tous
    if reel or deci or dte : tous=False
    for ligne in DB_TABLES[table]:
        champ = ligne[0]
        genre = ligne[1][:3]
        if tous:
            lstChamps.append(champ)
        elif reel and genre == 'flo': lstChamps.append(champ)
        elif deci and genre == 'int': lstChamps.append(champ)
        elif dte and genre == 'dat': lstChamps.append(champ)
    return lstChamps

if __name__ == '__main__':
    import wx
    app = wx.App(0)
    for table in DB_TABLES.keys():
        print('Table %s :\t'%table,GetChamps(table))
    app.MainLoop()
