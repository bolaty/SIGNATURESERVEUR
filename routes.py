from flask import Blueprint,request, jsonify,current_app
from extensions import socketio
#from flask_socketio import SocketIO, emit
from service.Signature import insertion_signaturepad,mise_a_jour_signaturepad,suppression_signaturepad,List_signaturepad

from models.models import clsObjetEnvoi
from utils import connect_database
from datetime import datetime
from config import MYSQL_REPONSE,connected_cashiers
import random
import string
api_bp = Blueprint('api', __name__)


################################################################
#                  GESTION SIGNATURE                           #
################################################################

@api_bp.route('insertion_signaturepad', methods=['POST'])
def pvginsertion_signaturepad():
    request_data = request.json
    SG_TOKENSIGNATURE = generer_code_aleatoire()   
    # Vérification que l'objet est bien présent dans la requête
    if 'Objet' not in request_data:
        return jsonify({"SL_MESSAGE": "Données manquantes. Code erreur (300) : voir le noeud Objet", "SL_RESULTAT": 'FALSE'})
    
    for row in request_data['Objet']:
        signature_info = {}
        #connected_cashiers[row.get('OP_CODEOPERATEUR', '')] = SG_TOKENSIGNATURE#request.sid
        # Validation et récupération des données pour l'insertion ou la modification
        if row.get('TYPEOPERATION', '') == '0' or row.get('TYPEOPERATION', '') == '1':
            signature_info['AG_CODEAGENCE'] = str(row.get('AG_CODEAGENCE', ''))
            signature_info['CODECRYPTAGE'] = str(row.get('CODECRYPTAGE', ''))
            signature_info['CL_EMAIL'] = str(row.get('CL_EMAIL', ''))
            signature_info['CL_TELEPHONE'] = str(row.get('CL_TELEPHONE', ''))
            signature_info['SG_CODESIGNATURE'] = str(row.get('SG_CODESIGNATURE', ''))
            signature_info['OP_CODEOPERATEUR'] = str(row.get('OP_CODEOPERATEUR', ''))
            signature_info['CL_IDCLIENT'] = str(row.get('CL_IDCLIENT', ''))
            signature_info['EJ_IDEPARGNANTJOURNALIER'] = str(row.get('EJ_IDEPARGNANTJOURNALIER', ''))
            signature_info['SG_DATESIGNATURE'] = str(row.get('SG_DATESIGNATURE', ''))
            signature_info['SG_TOKENSIGNATURE'] = SG_TOKENSIGNATURE
            signature_info['SG_NOMSIGNATURE'] = str(row.get('SG_NOMSIGNATURE', ''))
            signature_info['SG_STATUTSIGNATURE'] = str(row.get('SG_STATUTSIGNATURE', ''))
            signature_info['NT_CODENATURESIGNATUREPAD'] = str(row.get('NT_CODENATURESIGNATUREPAD', ''))
            signature_info['TYPEOPERATION'] = str(row.get('TYPEOPERATION', ''))
            if signature_info['TYPEOPERATION'] == '1' :
               signature_info['SIGNATURE'] = str(row.get('SIGNATURE', ''))
               signature_info['SG_CODESIGNATURE'] = str(row.get('SG_CODESIGNATURE', ''))
               
        if signature_info['TYPEOPERATION'] == '2' :
            signature_info['SG_CODESIGNATURE'] = str(row.get('SG_CODESIGNATURE', ''))
            signature_info['CODECRYPTAGE'] = str(row.get('CODECRYPTAGE', ''))
        # Vérification que toutes les données obligatoires sont présentes pour l'insertion ou la modification
        
        if signature_info['TYPEOPERATION'] == '0':  # Insertion
            if not all([signature_info['AG_CODEAGENCE'], signature_info['SG_DATESIGNATURE'],signature_info['SG_DATESIGNATURE'],signature_info['OP_CODEOPERATEUR'],  signature_info['NT_CODENATURESIGNATUREPAD'], signature_info['SG_TOKENSIGNATURE'], signature_info['SG_TOKENSIGNATURE']]):
               return jsonify({"SL_MESSAGE": "Données manquantes ou incorrectes. Code erreur (301)", "SL_RESULTAT": 'FALSE'})
        elif signature_info['TYPEOPERATION'] == '1':  # Mise à jour
            if not all([signature_info['SG_CODESIGNATURE']]):
               return jsonify({"SL_MESSAGE": "Données manquantes ou incorrectes. Code erreur (301)", "SL_RESULTAT": 'FALSE'})
        elif signature_info['TYPEOPERATION'] == '2':  # Suppression
            if not all([signature_info['SG_CODESIGNATURE']]):
               return jsonify({"SL_MESSAGE": "Données manquantes ou incorrectes. Code erreur (301)", "SL_RESULTAT": 'FALSE'})
        
        
        # Connexion à la base de données
        db_connection = connect_database()

        try:
            with db_connection.cursor() as cursor:
                cursor.execute("BEGIN TRANSACTION")
                
                # Insertion, modification ou suppression en fonction du type d'opération
                if signature_info['TYPEOPERATION'] == '0':  # Insertion
                    insertion_signaturepad(db_connection, signature_info)
                elif signature_info['TYPEOPERATION'] == '1':  # Mise à jour
                    mise_a_jour_signaturepad(db_connection, signature_info)
                elif signature_info['TYPEOPERATION'] == '2':  # Suppression
                    suppression_signaturepad(db_connection, signature_info)
                
                # Valider la transaction
                #db_connection.commit()
                
            if signature_info['TYPEOPERATION'] == '1':
              return jsonify({'message': 'Opération réussie', 'cashier_id': signature_info['OP_CODEOPERATEUR']})
            if signature_info['TYPEOPERATION'] == '0':
              return jsonify({'message': 'Opération réussie', 'cashier_id': signature_info['OP_CODEOPERATEUR']})
        
        except Exception as e:
            db_connection.rollback()
            return  jsonify({'message': str(e), 'cashier_id': signature_info['OP_CODEOPERATEUR']})#jsonify({"SL_MESSAGE": f"Erreur lors de l'opération : {str(e)}", "SL_RESULTAT": 'FALSE'})
        
        finally:
            db_connection.close()

@api_bp.route('/List_signaturepad', methods=['POST'])
def pvgList_signaturepad():
    request_data = request.json
    
    if 'Objet' not in request_data:
        return jsonify({"SL_MESSAGE": "Données manquantes.code erreur (300) voir le noeud Objet", "SL_RESULTAT": 'FALSE'})

    for row in request_data['Objet']:
        signature_info = {}
        
        # Validation et récupération des données pour la suppression
        signature_info['SG_CODESIGNATURE'] = row.get('SG_CODESIGNATURE') if 'SG_CODESIGNATURE' in signature_info and signature_info['SG_CODESIGNATURE'] else None
        signature_info['NT_CODENATURESIGNATUREPAD'] = row.get('NT_CODENATURESIGNATUREPAD') if 'NT_CODENATURESIGNATUREPAD' in signature_info and signature_info['NT_CODENATURESIGNATUREPAD'] else None #if 'CU_CODECOMPTEUTULISATEUR' in documentcontrat_info and documentcontrat_info['CU_CODECOMPTEUTULISATEUR'] else None
        signature_info['SG_NOMSIGNATURE'] = row.get('SG_NOMSIGNATURE') 
        signature_info['SG_TOKENSIGNATURE'] = row.get('SG_TOKENSIGNATURE')
        signature_info['TYPEOPERATION'] = row.get('TYPEOPERATION')
        signature_info['CODECRYPTAGE'] = row.get('CODECRYPTAGE')
        # Vérification que toutes les données obligatoires sont présentes
        
        #if not all([signature_info['SG_CODESIGNATURE']]):
           #return jsonify({"SL_MESSAGE": "Données manquantes ou incorrectes.code erreur (301) SG_CODESIGNATURE", "SL_RESULTAT": 'FALSE'}), 200
       
        # Connexion à la base de données
        db_connection = connect_database()

        try:
            with db_connection.cursor() as cursor:
                cursor.execute("BEGIN TRANSACTION")
                
                # Appeler la fonction de liste selon les criteres ou récupération
                response = List_signaturepad(db_connection,str(row.get('SG_CODESIGNATURE', '')),str(row.get('NT_CODENATURESIGNATUREPAD', '')),str(row.get('SG_NOMSIGNATURE', '')),str(row.get('SG_TOKENSIGNATURE', '')),str(row.get('CODECRYPTAGE', '')), str(row.get('TYPEOPERATION', '')))
                
                if len(response) > 0:
                    cursor.execute("COMMIT")
                    return jsonify({"SL_MESSAGE": "Opération effectuée avec succès !!!", "SL_RESULTAT": 'TRUE'}, response)
                else:
                    cursor.execute("ROLLBACK")
                    return jsonify({"SL_MESSAGE": "code signature invalide !!!.", "SL_RESULTAT": 'FALSE'})
        
        except Exception as e:
            db_connection.rollback()
            return jsonify({"SL_MESSAGE":  str(e.args[0]), "SL_RESULTAT": 'FALSE'})
        
        finally:
            db_connection.close() 


################################################################
#                  GESTION COMPTE PRODUIT                      #
################################################################


# Fonction pour générer un code aléatoire
def generer_code_aleatoire(taille=6):
    lettres_chiffres = string.ascii_uppercase + string.digits
    return ''.join(random.choice(lettres_chiffres) for _ in range(taille))               

def parse_numeric(value):
    """Vérifie si la valeur est un nombre et la convertit. Renvoie une exception si la conversion échoue."""
    if value is None or value == '':
        return None
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Format numérique invalide: {value}")


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

def get_commit(connection,clsBilletages):
    try:
       for row in clsBilletages: 
        cursor = connection
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