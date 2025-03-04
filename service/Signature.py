from flask import Blueprint, request, jsonify,current_app as app,send_file
import pyodbc
import datetime
from datetime import datetime
from typing import List
import json
import requests
import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid
#import pyodbc
import sys
sys.path.append("../")
from config import connected_cashiers,socketio,LIENCLIENT,CODECRYPTAGE,LIENAPISMS

import threading
import os
import base64
import random
import string

class clsAgence:
    def __init__(self):
        self.AG_RAISONSOCIAL = ''
        self.AG_EMAILMOTDEPASSE = ''
        self.AG_EMAIL = ''

def insertion_signaturepad(connection, signature_info):
    params = {
        'SG_CODESIGNATURE': '',  # Doit être défini dans la procédure (calculé comme MAX + 1)
        'AG_CODEAGENCE': int(signature_info['AG_CODEAGENCE']),
        'OP_CODEOPERATEUR': int(signature_info['OP_CODEOPERATEUR']),
        'CL_IDCLIENT': signature_info['CL_IDCLIENT'] if 'CL_IDCLIENT' in signature_info and signature_info['CL_IDCLIENT'] else '',
        'EJ_IDEPARGNANTJOURNALIER': signature_info['EJ_IDEPARGNANTJOURNALIER'] if 'EJ_IDEPARGNANTJOURNALIER' in signature_info and signature_info['EJ_IDEPARGNANTJOURNALIER'] else '',
        'SG_DATESIGNATURE': datetime.strptime(signature_info['SG_DATESIGNATURE'], "%d/%m/%Y"),
        'SG_TOKENSIGNATURE': signature_info['SG_TOKENSIGNATURE'],
        'SG_NOMSIGNATURE': signature_info['SG_NOMSIGNATURE'],
        'SG_STATUTSIGNATURE': signature_info['SG_STATUTSIGNATURE'],
        'NT_CODENATURESIGNATUREPAD': int(signature_info['NT_CODENATURESIGNATUREPAD']),
        'TYPEOPERATION': 0
    }

    try:
        cursor = connection.cursor()
        cursor.execute("EXEC dbo.PC_SIGNATUREPAD ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?", list(params.values()))
        connection.commit()
        
    except Exception as e:
        connection.rollback()
        raise Exception(f"Erreur lors de l'insertion : {str(e)}")
    
    # Récupération des résultats
    try:
        
        clsAgence = pvgTableLabelAgence(connection, signature_info['AG_CODEAGENCE'],CODECRYPTAGE)
        
        # Démarrer le traitement asynchrone dans un thread
        if "@" in clsAgence.AG_EMAIL :
                get_commit(connection,signature_info)
                thread_traitement = threading.Thread(target=traitement_asynchrone, args=(connection, clsAgence, signature_info))
                thread_traitement.daemon = True  # Définir le thread comme démon
                thread_traitement.start()
       
    except Exception as e:
         # En cas d'erreur, annuler la transaction
        cursor.execute("ROLLBACK")
        MYSQL_REPONSE = f'Impossible de récupérer les résultats de la procédure stockée : {str(e.args[1])}'
        raise Exception(MYSQL_REPONSE)

def mise_a_jour_signaturepad(connection, signature_info):
    
    # Vérifier si le répertoire de téléchargement est configuré
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        return jsonify({"message": "Répertoire de téléchargement non configuré", "result": "FALSE"}), 500
    
    #Generer le nom du fichier
   
    # Décoder la signature base64
    image_data = base64.b64decode(signature_info['SIGNATURE'].split(',')[1])
    # Concaténation pour obtenir le chemin complet du fichier
    nom_signature = generer_nom_signature()
    file_path = os.path.join(upload_folder, nom_signature)
    
        
    params = {
        'SG_CODESIGNATURE':   signature_info['SG_CODESIGNATURE'],
        'AG_CODEAGENCE': int(signature_info['AG_CODEAGENCE']),
        'OP_CODEOPERATEUR': int(signature_info['OP_CODEOPERATEUR']),
        'CL_IDCLIENT': '',#signature_info['CL_IDCLIENT'] if 'CL_IDCLIENT' in signature_info and signature_info['CL_IDCLIENT'] else None,
        'EJ_IDEPARGNANTJOURNALIER':'',# signature_info['EJ_IDEPARGNANTJOURNALIER'] if 'EJ_IDEPARGNANTJOURNALIER' in signature_info and signature_info['EJ_IDEPARGNANTJOURNALIER'] else None,
        'SG_DATESIGNATURE': datetime.strptime(signature_info['SG_DATESIGNATURE'], "%d/%m/%Y"),
        'SG_TOKENSIGNATURE': signature_info['SG_TOKENSIGNATURE'],
        'SG_NOMSIGNATURE': nom_signature,
        'SG_STATUTSIGNATURE': 'O',
        'NT_CODENATURESIGNATUREPAD': int(signature_info['NT_CODENATURESIGNATUREPAD']),
        'TYPEOPERATION': 1
    }

    try:
        cursor = connection.cursor()
        cursor.execute("EXEC dbo.PC_SIGNATUREPAD ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?", list(params.values()))
        connection.commit()
        
        # Sauvegarder l'image sur le serveur
        with open(file_path, "wb") as f:
         f.write(image_data)
         
         
        get_commit(connection,signature_info)
        
        """
        # Envoyer une notification via WebSocket à la caissière concernée
        cashier_id = signature_info['OP_CODEOPERATEUR']
        if cashier_id in connected_cashiers:
            socketio.emit('notification', {'message': 'Nouvelle signature enregistrée'}, room=connected_cashiers[cashier_id])
        """
    except Exception as e:
        connection.rollback()
        raise Exception(f"Erreur lors de la mise à jour : {str(e)}")

def generer_nom_signature():
    # Générer une chaîne aléatoire de 12 caractères (lettres et chiffres)
    nom_aleatoire = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    
    # Ajouter l'extension .png
    nom_signature = f"{nom_aleatoire}.png"
    
    return nom_signature
def List_signaturepad(connection, SG_CODESIGNATURE,NT_CODENATURESIGNATUREPAD,SG_NOMSIGNATURE,SG_TOKENSIGNATURE,
                      CODECRYPTAGE,TYPEOPERATION):
    """
    Récupère les données de la fonction SQL FT_IM_CTCONTRATPARTYPE avec le code de cryptage fourni.
        @SG_CODESIGNATURE as int,
        @NT_CODENATURESIGNATUREPAD AS int, 
        @SG_NOMSIGNATURE AS varchar(1000),
        @SG_TOKENSIGNATURE as varchar(1000),
        @CODECRYPTAGE as varchar(50),
        @TYPEOPERATION as varchar(1)
    :param connection: Connexion à la base de données SQL Server
    :param codecryptage: Le code de cryptage utilisé pour décrypter les données
    :return: Liste de dictionnaires représentant les enregistrements de la table intermédiaire
    """
    
    try:
        cursor = connection.cursor()
        # Validation et récupération des données pour la suppression
        SG_CODESIGNATURE = SG_CODESIGNATURE if SG_CODESIGNATURE else None
        NT_CODENATURESIGNATUREPAD = NT_CODENATURESIGNATUREPAD if NT_CODENATURESIGNATUREPAD else None
        CODECRYPTAGE = CODECRYPTAGE
        TYPEOPERATION = TYPEOPERATION
       
       
        # Exécuter la fonction SQL avec le codecryptage comme paramètre
        cursor.execute("SELECT * FROM dbo.FT_SIGNATUREPADPARTYPE(?,?,?,?,?,?)", (SG_CODESIGNATURE,NT_CODENATURESIGNATUREPAD,SG_NOMSIGNATURE,SG_TOKENSIGNATURE,
                      CODECRYPTAGE,TYPEOPERATION))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            upload_folder = app.config.get('UPLOAD_FOLDER')
            filepath = os.path.join(upload_folder, row.SG_NOMSIGNATURE)
            if os.path.exists(filepath):
               filepath = filepath#send_file(filepath, as_attachment=True) 
            result = {
                'SG_CODESIGNATURE': row.SG_CODESIGNATURE,
                'AG_CODEAGENCE': row.AG_CODEAGENCE,
                'OP_CODEOPERATEUR': row.OP_CODEOPERATEUR,
                'CL_IDCLIENT': row.CL_IDCLIENT,
                'EJ_IDEPARGNANTJOURNALIER': row.EJ_IDEPARGNANTJOURNALIER,
                'SG_DATESIGNATURE': row.SG_DATESIGNATURE.strftime("%d/%m/%Y"),
                'SG_TOKENSIGNATURE': row.SG_TOKENSIGNATURE,
                'SG_NOMSIGNATURE': row.SG_NOMSIGNATURE,
                'SG_STATUTSIGNATURE': row.SG_STATUTSIGNATURE,
                'NT_CODENATURESIGNATUREPAD': row.NT_CODENATURESIGNATUREPAD,
                'LIENSDOC': filepath
            }
            
            # Ajouter le dictionnaire à la liste des résultats
            results.append(result)
        
        return results

    except Exception as e:
        # En cas d'erreur, lever une exception avec un message approprié
        MYSQL_REPONSE = e.args[1]
        if "varchar" in MYSQL_REPONSE:
               MYSQL_REPONSE = MYSQL_REPONSE.split("[SQL Server]", 1)[1].split(".", 1)[0]
        raise Exception(MYSQL_REPONSE)



def suppression_signaturepad(connection, sg_codesignature):
    params = {
        'SG_CODESIGNATURE': sg_codesignature,
        'AG_CODEAGENCE': None,  # Non utilisé
        'OP_CODEOPERATEUR': None,  # Non utilisé
        'CL_IDCLIENT': None,  # Non utilisé
        'EJ_IDEPARGNANTJOURNALIER': None,  # Non utilisé
        'SG_DATESIGNATURE': parse_datetime('01/01/1900'),  # Non utilisé
        'SG_TOKENSIGNATURE': None,  # Non utilisé
        'SG_NOMSIGNATURE': None,  # Non utilisé
        'SG_STATUTSIGNATURE': None,  # Non utilisé
        'NT_CODENATURESIGNATUREPAD': None,  # Non utilisé
        'TYPEOPERATION': 2
    }

    try:
        cursor = connection.cursor()
        cursor.execute("EXEC dbo.PC_SIGNATUREPAD ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?", list(params.values()))
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise Exception(f"Erreur lors de la suppression : {str(e)}")


def pvgTableLabelAgence(connection, *vppCritere):
    cursor = connection.cursor()

    if len(vppCritere) == 2:
        vapCritere = " WHERE AG_CODEAGENCE=? AND AG_ACTIF='O'"
        vapNomParametre = ('@AG_CODEAGENCE',)
        vapValeurParametre = (vppCritere[0])
    else:
        vapCritere = ""
        vapNomParametre = ()
        vapValeurParametre = ()

    vapRequete = f"""
        SELECT 
            CAST(DECRYPTBYPASSPHRASE('{vppCritere[1]}', AG_EMAIL) AS varchar(150)) AS AG_EMAIL,
            CAST(DECRYPTBYPASSPHRASE('{vppCritere[1]}', AG_EMAILMOTDEPASSE) AS varchar(150)) AS AG_EMAILMOTDEPASSE,
            AG_RAISONSOCIAL
        FROM AGENCE 
        {vapCritere}
    """
    try:
        cursor.execute(vapRequete, vapValeurParametre)
    except Exception as e:
        cursor.close()
        cursor.execute("ROLLBACK")
        MYSQL_REPONSE = f'Impossible d\'exécuter la procédure stockée : {str(e.args[1])}'
        raise Exception(MYSQL_REPONSE)
    
    try:
        rows = cursor.fetchall()

        clsAgenceObj = clsAgence()

        for row in rows:
            clsAgenceObj.AG_EMAIL = row[0]
            clsAgenceObj.AG_EMAILMOTDEPASSE = row[1]
            clsAgenceObj.AG_RAISONSOCIAL = row[2]

        # Retourne l'objet
        return clsAgenceObj
    except Exception as e:
        cursor.close()
        cursor.execute("ROLLBACK")
        MYSQL_REPONSE = f'Impossible d\'exécuter la procédure stockée : {str(e.args[1])}'
        raise Exception(MYSQL_REPONSE)  
    
def traitement_asynchrone(connection, clsAgence, resultatUsers):
    try:
        # Votre traitement asynchrone ici
        #for idx in range(len(resultatUsers)):
        if "@" in resultatUsers['CL_EMAIL']:
                smtpServeur = "smtp.gmail.com"
                portSmtp = 587
                adresseEmail = clsAgence.AG_EMAIL
                motDePasse = clsAgence.AG_EMAILMOTDEPASSE
                destinataire = resultatUsers['CL_EMAIL']#'bolatykouassieuloge@gmail.com'
                sujet = "Token de Connexion"
                corpsMessage = "votre code de signature est : " + resultatUsers['SG_TOKENSIGNATURE']
                message = MIMEMultipart()
                message['From'] = adresseEmail
                message['To'] = destinataire
                message['Subject'] = sujet
                message.attach(MIMEText(corpsMessage, 'plain'))
                with smtplib.SMTP(smtpServeur, portSmtp) as server:
                    server.starttls()
                    server.login(adresseEmail, motDePasse)
                    server.sendmail(adresseEmail, destinataire, message.as_string())
                    
        #for idx in range(len(resultatUsers)):
            # Préparation de l'appel à l'API SMS et mise à jour du SMS
        LIENDAPISMS = LIENAPISMS + "Service/wsApisms.svc/SendMessage"
        Objet ={}
                # Appel de l'API SMS
        if not IsValidateIP(LIENDAPISMS):
                Objet["SL_RESULTAT"] = "FALSE"
                Objet["SL_MESSAGE"] = "L'API SMS doit être configurée !!!"
                    
                return Objet
        corpsMessagesms = 'votre code de signature est :' + resultatUsers["SG_TOKENSIGNATURE"]
        reponse = excecuteServiceWebNew(resultatUsers, "post", LIENDAPISMS,corpsMessagesms)
            
        if reponse or len(reponse) == 0:
            
            pass

    except Exception as e:
        #connection.close() 
        print("Erreur lors du traitement asynchrone:", e)

def excecuteServiceWebNew(Objetenv, method, url,corpsMessagesms):
    objList = []
    Objet={}
    headers = {'Content-Type': 'application/json'}
    try:
        Objet={
            "Objet": [
                { 
                    "CO_CODECOMPTE": "",
                    "CodeAgence": Objetenv['AG_CODEAGENCE'],
                    "RECIPIENTPHONE": Objetenv['CL_TELEPHONE'],
                    "SM_RAISONNONENVOISMS": "xxx",
                    "SM_DATEPIECE": "14-01-2025",
                    "LO_LOGICIEL": "01",
                    "OB_NOMOBJET": "test",
                    "SMSTEXT": corpsMessagesms,
                    "INDICATIF": "225",
                    "SM_NUMSEQUENCE": "1",
                    "SM_STATUT": "E"
                }
            ]
        }
        response = requests.request(method, url, json=Objet, headers=headers)
        if response.status_code == 200:
            objList = response.json()
    except requests.exceptions.RequestException as e:
        # Log.Error("Testing log4net error logging - Impossible d'atteindre le service Web")
        pass
    except Exception as ex:
        # Log.Error("Testing log4net error logging - " + str(ex))
        pass
    return objList


def get_commit(connection,clsBilletages):
    try:
       for row in clsBilletages: 
        cursor = connection.cursor()
        params = {
            'AG_CODEAGENCE3': '1000',
            'MC_DATEPIECE3': '01/01/1900'
        }
        try:
            connection.commit()
            cursor.execute("EXECUTE [PC_COMMIT]  ?, ?", list(params.values()))
            #instruction pour valider la commande de mise à jour
            connection.commit()
        except Exception as e:
            # En cas d'erreur, annuler la transaction
            cursor.execute("ROLLBACK")
            cursor.close()
            MYSQL_REPONSE = e.args[1]
            if "varchar" in MYSQL_REPONSE:
               MYSQL_REPONSE = MYSQL_REPONSE.split("varchar", 1)[1].split("en type de donn", 1)[0]
               
            raise Exception(MYSQL_REPONSE)
    except Exception as e:
        MYSQL_REPONSE = f'Erreur lors du commit des opérations: {str(e)}'
        raise Exception(MYSQL_REPONSE)     
    
def IsValidateIP(ipaddress):
    ValidateIP = False
    ipaddress = ipaddress.replace("/ZenithwebClasse.svc/", "")
    ipaddress = ipaddress.replace("/Service/wsApisms.svc/SendMessage", "")

    if not ipaddress:
        return ValidateIP

    if "http://" in ipaddress:
        ipaddress = ipaddress.replace("http://", "")

    if "https://" in ipaddress:
        ipaddress = ipaddress.replace("https://", "")

    adresse = ipaddress.split(':')

    if len(adresse) != 2:
        return ValidateIP

    HostURI = adresse[0]
    PortNumber = adresse[1].replace("/", "")

    ValidateIP = PingHost(HostURI, int(PortNumber))
    return ValidateIP    
 
def PingHost(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)  # Timeout de 1 seconde
        result = sock.connect_ex((host, port))
        if result == 0:
            return True
        else:
            return False
    except Exception as e:
        print("Erreur lors de la tentative de ping :", e)
        return False
 
    
def parse_datetime(date_str):
    """Convertit une chaîne de caractères en datetime. Renvoie None si la conversion échoue."""
    if not date_str:
        return None
    
    # Liste des formats possibles
    date_formats = ["%d/%m/%Y","%d-%m-%Y", "%Y-%m-%d %H:%M:%S"]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Si aucun format ne correspond, lever une exception
    raise ValueError(f"Format de date invalide: {date_str}")    