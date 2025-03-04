#import eventlet
#eventlet.monkey_patch()  # Patch eventlet AVANT les imports Flask

from flask import Flask, jsonify, request, render_template
from extensions import SocketIO, emit
import eventlet
import eventlet.wsgi
from flask_cors import CORS
import logging as logger
import os
from service.Signature import mise_a_jour_signaturepad

logger.basicConfig(level="DEBUG")

from routes import api_bp
from config import connected_cashiers  # On importe uniquement ce qui est nécessaire

# Initialisation de Flask
app = Flask(__name__)
CORS(app)  # Activation du CORS

# Configuration de SocketIO
socketio = SocketIO(app, cors_allowed_origins="*",async_mode="eventlet")

# Quand une caissière se connecte au WebSocket
@socketio.on('connect_cashier')
def handle_connect_cashier(data):
    cashier_id = data.get('OP_CODEOPERATEUR')
    if cashier_id:
        connected_cashiers[cashier_id] = request.sid
        logger.debug(f"Caissière connectée: {cashier_id} avec SID: {request.sid}")
        emit('status', {'message': 'Caissière connectée', 'cashier_id': cashier_id}, broadcast=True)
    else:
        logger.warning("Tentative de connexion sans OP_CODEOPERATEUR")

# Quand une caissière se déconnecte
'''
@socketio.on('disconnect')
def handle_disconnect():
    if len(connected_cashiers) > 0 :
        for cashier_id, sid in list(connected_cashiers.items()):
            if sid == request.sid:
                del connected_cashiers[cashier_id]
                logger.debug(f"Caissière déconnectée: {cashier_id}")
                emit('status', {'message': 'Caissière déconnectée', 'cashier_id': cashier_id}, broadcast=True)
            else:
                logger.warning("Tentative de deconnexion sans OP_CODEOPERATEUR")


@socketio.on('disconnect')
def handle_disconnect():
    #global connected_cashiers
    
    cashier_to_remove = None
    if len(connected_cashiers) > 0 :
        # Rechercher la caissière à déconnecter
        for cashier_id, sid in connected_cashiers.items():
            if sid == request.sid:
                cashier_to_remove = cashier_id
                break

        if cashier_to_remove:
            del connected_cashiers[cashier_to_remove]
            #logger.debug(f"Caissière déconnectée: {cashier_to_remove}")

            # Émettre l'événement de déconnexion à tous les clients
            #emit('status', {'message': 'Caissière déconnectée', 'cashier_id': cashier_to_remove}, broadcast=True)
        #else:
        #    logger.warning("Tentative de déconnexion sans OP_CODEOPERATEUR")

'''

# Nouvelle fonction pour transmettre la signature à une caissière spécifique
@socketio.on('send_signature')
def handle_signature(data):
    signature_info = {
        'AG_CODEAGENCE': str(data.get('AG_CODEAGENCE', '')),
        'SIGNATURE': str(data.get('SIGNATURE', '')),
        'PHOTO': str(data.get('PHOTO', '')),
        'SG_CODESIGNATURE': str(data.get('SG_CODESIGNATURE', '')),
        'OP_CODEOPERATEUR': str(data.get('OP_CODEOPERATEUR', '')),
        'CL_IDCLIENT': str(data.get('CL_IDCLIENT', '')),
        'EJ_IDEPARGNANTJOURNALIER': str(data.get('EJ_IDEPARGNANTJOURNALIER', '')),
        'SG_DATESIGNATURE': str(data.get('SG_DATESIGNATURE', '')),
        'SG_TOKENSIGNATURE': str(data.get('SG_TOKENSIGNATURE', '')),
        'SG_NOMSIGNATURE': str(data.get('SG_NOMSIGNATURE', '')),
        'SG_STATUTSIGNATURE': str(data.get('SG_STATUTSIGNATURE', '')),
        'NT_CODENATURESIGNATUREPAD': str(data.get('NT_CODENATURESIGNATUREPAD', '')),
        'TYPEOPERATION': str(data.get('TYPEOPERATION', ''))
    }
    from utils import connect_database
    
    # Connexion à la base de données
    db_connection = connect_database()

    try:
            with db_connection.cursor() as cursor:
                cursor.execute("BEGIN TRANSACTION")
                
                
                mise_a_jour_signaturepad(db_connection, signature_info)
                
                
                
            cashier_id = signature_info['OP_CODEOPERATEUR']

            if cashier_id in connected_cashiers:
                cashier_sid = connected_cashiers[cashier_id]
                logger.debug(f"Envoi de la signature à la caissière {cashier_id} avec SID: {cashier_sid}")
                emit('receive_signature', signature_info, room=cashier_sid)
            else:
                logger.warning(f"Caissière {cashier_id} non connectée, impossible d'envoyer la signature")
        
    except Exception as e:
            db_connection.rollback()
            return  jsonify({'message': str(e), 'cashier_id': signature_info['OP_CODEOPERATEUR']})
        
    

    



# Configuration du dossier d'upload
UPLOAD_FOLDER = 'D:/UploadFile'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Assurez-vous que le dossier existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def hello():
    return render_template('home.html')

# Enregistrement du blueprint API
app.register_blueprint(api_bp, url_prefix='/api')

# Exécution du serveur
if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 6001)), app)
    #eventlet.wsgi.server(eventlet.listen(('192.168.1.12', 6001)), app)
    #socketio.run(app, host="0.0.0.0", port=6001, debug=True, allow_unsafe_werkzeug=True)