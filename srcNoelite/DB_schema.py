#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, Matthania ajout des tables sp�cifiques
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

# description des tables de l'application
DB_TABLES = {
    "clients":[
                ("IDclient", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID de la famille"),
                ("libelle", "VARCHAR(40)", u"libell� de la famille pour les adresses"),
                ("rue", "VARCHAR(255)", u"Adresse de la personne"),
                ("cp", "VARCHAR(10)", u"Code postal de la personne"),
                ("ville", "VARCHAR(100)", u"Ville de la personne"),
                ("fixe", "VARCHAR(50)", u"Tel domicile de la personne"),
                ("mobile", "VARCHAR(50)", u"Tel mobile perso de la personne"),
                ("mail", "VARCHAR(50)", u"Email perso de la personne"),
                ("refus_pub", "INTEGER", u"Refus de publicit�s papier"),
                ("refus_mel", "INTEGER", u"Refus de publicit�s demat"),
                ], #Coordonn�es clients, remplac� par une vue dans Noethys

    "modes_reglements":[
                ("IDmode", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID mode de r�glement"),
                ("label", "VARCHAR(100)", u"Label du mode"),
                ("image", "LONGBLOB", u"Image du mode"),
                ("numero_piece", "VARCHAR(10)", u"Num�ro de pi�ce (None|ALPHA|NUM)"),
                ("nbre_chiffres", "INTEGER", u"Nbre de chiffres du num�ro"),
                ("frais_gestion", "VARCHAR(10)", u"Frais de gestion None|LIBRE|FIXE|PRORATA"),
                ("frais_montant", "FLOAT", u"Montant fixe des frais"),
                ("frais_pourcentage", "FLOAT", u"Prorata des frais"),
                ("frais_arrondi", "VARCHAR(20)", u"M�thode d'arrondi"),
                ("frais_label", "VARCHAR(200)", u"Label de la prestation"),
                ("type_comptable", "VARCHAR(200)", u"Type comptable (banque ou caisse)"),
                ("code_compta", "VARCHAR(200)", u"Code comptable pour export vers logiciels de compta"),
                        ], # Modes de r�glements

    "emetteurs":[
                ("IDemetteur", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID Emetteur"),
                ("IDmode", "INTEGER", u"ID du mode concern�"),
                ("nom", "VARCHAR(200)", u"Nom de l'�metteur"),
                ("image", "LONGBLOB", u"Image de l'emetteur"),
                ], # Emetteurs bancaires pour les modes de r�glements

    "payeurs":[
                ("IDpayeur", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID Payeur"),
                ("IDcompte_payeur", "INTEGER", u"ID du compte payeur concern�"),
                ("nom", "VARCHAR(100)", u"Nom du payeur"),
                ], # Payeurs apparaissant sur les r�glements re�us pour un compte payeur-client

    "comptes_bancaires":[
                ("IDcompte", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID Compte"),
                ("nom", "VARCHAR(100)", u"Intitul� du compte"),
                ("numero", "VARCHAR(50)", u"Num�ro du compte"),
                ("defaut", "INTEGER", u"(0/1) Compte s�lectionn� par d�faut"),
                ("raison", "VARCHAR(400)", u"Raison sociale"),
                ("code_etab", "VARCHAR(400)", u"Code �tablissement"),
                ("code_guichet", "VARCHAR(400)", u"Code guichet"),
                ("code_nne", "VARCHAR(400)", u"Code NNE pour pr�l�vements auto."),
                ("cle_rib", "VARCHAR(400)", u"Cl� RIB pour pr�l�vements auto."),
                ("cle_iban", "VARCHAR(400)", u"Cl� IBAN pour pr�l�vements auto."),
                ("iban", "VARCHAR(400)", u"Num�ro IBAN pour pr�l�vements auto."),
                ("bic", "VARCHAR(400)", u"Num�ro BIC pour pr�l�vements auto."),
                ("code_ics", "VARCHAR(400)", u"Code NNE pour pr�l�vements auto."),
            ], # Comptes bancaires de l'organisateur
                                    
    "reglements":[
                ("IDreglement", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID R�glement"),
                ("IDcompte_payeur", "INTEGER", u"ID compte du payeur(client par simplification, Noethys les distingue"),
                ("date", "DATE", u"Date d'�mission du r�glement"),
                ("IDmode", "INTEGER", u"ID du mode de r�glement"),
                ("IDemetteur", "INTEGER", u"ID de l'�metteur du r�glement"),
                ("numero_piece", "VARCHAR(30)", u"Num�ro de pi�ce"),
                ("montant", "FLOAT", u"Montant du r�glement"),
                ("IDpayeur", "INTEGER", u"ID du payeur"),
                ("observations", "VARCHAR(200)", u"Observations"),
                ("numero_quittancier", "VARCHAR(30)", u"Num�ro de quittancier"),
                ("IDprestation_frais", "INTEGER", u"ID de la prestation de frais de gestion"),
                ("IDcompte", "INTEGER", u"ID du compte bancaire pour l'encaissement"),
                ("date_differe", "DATE", u"Date de l'encaissement diff�r�"),
                ("encaissement_attente", "INTEGER", u"(0/1) Encaissement en attente"),
                ("IDdepot", "INTEGER", u"ID du d�p�t"),
                ("date_saisie", "DATE", u"Date de saisie du r�glement"),
                ("IDutilisateur", "INTEGER", u"Utilisateur qui a fait la saisie"),
                ("IDprelevement", "INTEGER", u"ID du pr�l�vement"),
                ("avis_depot", "DATE", u"Date de l'envoi de l'avis de d�p�t"),
                ("IDpiece", "INTEGER", u"IDpiece pour PES V2 ORMC"),
                ("compta", "INTEGER", u"Pointeur de transfert en compta"),
                ], # R�glements

    "parametres":[
                ("IDparametre", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID parametre"),
                ("categorie", "VARCHAR(200)", u"Cat�gorie"),
                ("nom", "VARCHAR(200)", u"Nom"),
                ("parametre", "VARCHAR(30000)", u"Parametre"),
                ], # Param�tres du contexte ou options choisies

    "secteurs":[
                ("IDsecteur", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID pays postal"),
                ("nom", "VARCHAR(255)", u"Nom du pays postal"),
                                    ], # pays postaux inclus � la suite de la ville (apr�s une fin de ligne)

    "utilisateurs":[
                ("IDutilisateur", "INTEGER PRIMARY KEY AUTOINCREMENT", u"IDutilisateur"),
                ("sexe", "VARCHAR(5)", u"Sexe de l'utilisateur"),
                ("nom", "VARCHAR(200)", u"Nom de l'utilisateur"),
                ("prenom", "VARCHAR(200)", u"Pr�nom de l'utilisateur"),
                ("mdp", "VARCHAR(100)", u"Mot de passe"),
                ("profil", "VARCHAR(100)", u"Profil (Administrateur ou utilisateur)"),
                ("actif", "INTEGER", u"Utilisateur actif"),
                ("image", "VARCHAR(200)", u"Images"),
                                    ], # Utilisateurs identifiables

    "sauvegardes_auto":[ ("IDsauvegarde", "INTEGER PRIMARY KEY AUTOINCREMENT", u"IDsauvegarde"),
                ("nom", "VARCHAR(455)", u"Nom de la proc�dure de sauvegarde auto"),
                ("observations", "VARCHAR(455)", u"Observations"),
                ("date_derniere", "DATE", u"Date de la derni�re sauvegarde"),
                ("sauvegarde_nom", "VARCHAR(455)", u"Sauvegarde Nom"),
                ("sauvegarde_motdepasse", "VARCHAR(455)", u"Sauvegarde mot de passe"),
                ("sauvegarde_repertoire", "VARCHAR(455)", u"sauvegarde R�pertoire"),
                ("sauvegarde_emails", "VARCHAR(455)", u"Sauvegarde Emails"),
                ("sauvegarde_fichiers_locaux", "VARCHAR(455)", u"Sauvegarde fichiers locaux"),
                ("sauvegarde_fichiers_reseau", "VARCHAR(455)", u"Sauvegarde fichiers r�seau"),
                ("condition_jours_scolaires", "VARCHAR(455)", u"Condition Jours scolaires"),
                ("condition_jours_vacances", "VARCHAR(455)", u"Condition Jours vacances"),
                ("condition_heure", "VARCHAR(455)", u"Condition Heure"),
                ("condition_poste", "VARCHAR(455)", u"Condition Poste"),
                ("condition_derniere", "VARCHAR(455)", u"Condition Date derni�re sauvegarde"),
                ("condition_utilisateur", "VARCHAR(455)", u"Condition Utilisateur"),
                ("option_afficher_interface", "VARCHAR(455)", u"Option Afficher interface (0/1)"),
                ("option_demander", "VARCHAR(455)", u"Option Demander (0/1)"),
                ("option_confirmation", "VARCHAR(455)", u"Option Confirmation (0/1)"),
                ("option_suppression", "VARCHAR(455)", u"Option Suppression sauvegardes obsol�tes"),
                                    ], # proc�dures de sauvegardes automatiques

    "droits":[                   ("IDdroit", "INTEGER PRIMARY KEY AUTOINCREMENT", u"IDdroit"),
                ("IDutilisateur", "INTEGER", u"IDutilisateur"),
                ("IDmodele", "INTEGER", u"IDmodele"),
                ("categorie", "VARCHAR(200)", u"Cat�gorie de droits"),
                ("action", "VARCHAR(200)", u"Type d'action"),
                ("etat", "VARCHAR(455)", u"Etat"),
                                    ], # Droits des utilisateurs

    "modeles_droits":[     ("IDmodele", "INTEGER PRIMARY KEY AUTOINCREMENT", u"IDmodele"),
                ("nom", "VARCHAR(455)", u"Nom du mod�le"),
                ("observations", "VARCHAR(455)", u"Observations"),
                ("defaut", "INTEGER", u"Mod�le par d�faut (0/1)"),
                                    ], # Mod�les de droits

    "compta_exercices":[("IDexercice", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID Exercice"),
                ("nom", "VARCHAR(400)", u"Nom de l'exercice"),
                ("date_debut", "DATE", u"Date de d�but"),
                ("date_fin", "DATE", u"Date de fin"),
                ("defaut", "INTEGER", u"Propos� par d�faut (0/1)"),
                ("actif", "INTEGER", u"Actif pour �critures nouvelles (0/1)"),
                ("cloture", "INTEGER", u"Cl�tur�, l'exercice ne peut plus �tre actif(0/1)"),
                                    ], # Compta : Exercices

    'immobilisations':[
                ('IDimmo','INTEGER PRIMARY KEY AUTOINCREMENT',"Cl� Unique"),
                ('compteImmo','VARCHAR(10)',"compte comptable de l'immobilisation"),
                ('cleAppel','VARCHAR(16)',"cl� usuelle appel, identifie l'ensemble de composants par son libelle"),
                ('analytique','VARCHAR(8)',"Section analytique"),
                ('dteAcquisition','DATE',"date de la premi�re acquisition des �l�ments de l'immo"),
                ('compteDotation','VARCHAR(10)',"compte comptable de la dotation aux immos"),
                ('libelle','VARCHAR(200)',"texte pour les �dition ou choix de ligne "),
                ('descriptif','TEXT',"d�scriptif libre"),
                ('etat', 'VARCHAR(5)', "�tat des immos s'�tend � tout l'ensemble immo"),
                ],# fiches immobilisations

    'immosComposants':[
                ('IDcomposant', 'INTEGER PRIMARY KEY AUTOINCREMENT',"Cl� Unique"),
                ('IDimmo', 'INTEGER', "reprise de l'ent�te immo"),
                ('libComposant','VARCHAR(200)',"texte pour les �dition en ligne"),
                ('quantite','FLOAT',"quantit�s fractionnables � la cession"),
                ('valeur','FLOAT',"valeur d'acquisition"),
                ('dteMiseEnService','DATE',"date de mise en service pour d�but amort"),
                ('compteFrn','VARCHAR(10)',"contrepartie de l'�criture d'acquisition"),
                ('libelleFrn','VARCHAR(200)',"libell� modifiable"),
                ('type','VARCHAR(1)',"D�gressif Lin�aire Nonamort"),
                ('tauxLineaire','FLOAT',"taux � appliquer � la valeur d'acquisition"),
                ('coeffDegressif','FLOAT',"taux � appliquer � la VNC"),
                ('amortAnterieur','FLOAT',"cumul des amortissements � l'ouverture"),
                ('dotation','FLOAT',"dotation de l'exercice"),
                ('cessionType','VARCHAR(5)',"type de cession (cession partielle cr�e un nouvel �l�ment)"),
                ('cessionDate','DATE',"date de la cession"),
                ('cessionQte','FLOAT',"qt� c�d�e"),
                ('cessionValeur','FLOAT',"valeur de la cession"),
                ('section','VARCHAR(10)',"Deuxi�me axe analytique"),
                ('nbrePlaces','FLOAT',"Ne renseigner que pour �l�ment z�ro, capacit� d'accueil pour v�hicules,tentes, batiment "),
                ('noSerie','VARCHAR(32)',"Immatriculation ou no identifiant"),
                ('dtMaj','DATE',"Date de derni�re modif"),
                ('user','INTEGER',"ID de l'utilisateur"),],# subdivisions des fiches immobilisations
    
    'vehiculesCouts':[
                ('IDvcout','INTEGER PRIMARY KEY AUTOINCREMENT',"Cl� Unique"),
                ('IDimmo','INTEGER',"cl� usuelle d'appel, identifie l'composant principal 0 par son libelle"),
                ('cloture','DATE',"Date de cl�ture de l'exercice"),
                ('prixKmVte','FLOAT',"Prix de base du km factur� avant remise"),
                ('carburants','FLOAT',"Co�t des carburants pour l'exercice"),
                ('entretien','FLOAT',"Co�t de l'entretien (charges variables selon km)"),
                ('servicesFixes','FLOAT',"Autres co�ts fixes � l'ann�e"),
                ('dotation','FLOAT',"Dotation aux amortissments"),
                ('grossesRep','FLOAT',"Grosses r�parations immobilis�es (d�taill�es dans la fiche immo)"),
                ('plusValue','FLOAT',"R�sultat du calcul sur la cession dans fiche immo"),
                ('kmDebut','INTEGER',"Kilom�trage en d�but d'exercice"),
                ('kmFin','INTEGER',"Kilom�trage en fin d'exercice"),
                ('dtMaj','DATE',"Date de derni�re modif"),
                ('user','INTEGER',"ID de l'utilisateur"),],# El�ments de co�ts annuels
    
    'vehiculesConsos':[
                ('IDvconso','INTEGER PRIMARY KEY AUTOINCREMENT',"Cl� Unique"),
                ('IDimmo','INTEGER',"ID de l'immo"),
                ('cloture','DATE',"Date de cl�ture de l'exercice"),
                ('typeTiers','VARCHAR(1)',"'C'lient, 'S'ection interne,'P'partenaires,'E'mploy�s"),
                ('IDtiers','VARCHAR(8)',"Section analytique consommatrice ou no client"),
                ('dteKmDeb','DATE',"Date du relv� km d�but"),
                ('kmDeb','INTEGER',"kilom�trage de d�part"),
                ('dteKmFin','DATE',"Date du relv� km fin"),
                ('kmFin','INTEGER',"kilom�trage de fin"),
                ('dtMaj','DATE',"Date de derni�re modif"),
                ('user','INTEGER',"ID de l'utilisateur"),],# affectation des consommations internes par section
    }

# index cl� unique
DB_PK = {
        "PK_matArticles_artCodeArticle"  :  {"table"  :  "matArticles",  "champ" : "artCodeArticle", },
        "PK_vehiculesCouts_IDimmo_cloture": {"table": "vehicules", "champ": "IDimmo, cloture"},}

# index sans contrainte
DB_IX = {
        "index_reglements_IDcompte_payeur": {"table": "reglements", "champ": "IDcompte_payeur"},#index de Noethys
        "IX_immobilisations_compteImmo_cleAppel": {"table": "immobilisations", "champ": "compteImmo,cleAppel"},
        "IX_immosComposants_IDimmo": {"table": "immosComposants", "champ": "IDimmo"},
        "IX_vehiculesConsos_IDimmo_cloture": {"table": "vehicules", "champ": "IDimmo, cloture"},}

# ----------------------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    """ Affichage de stats sur les tables """
    nbreChamps = 0
    for nomTable, listeChamps in DB_TABLES.items() :
        nbreChamps += len(listeChamps)
    print("Nbre de champs DATA =", nbreChamps)
    print("Nbre de tables DATA =", len(DB_TABLES.keys()))