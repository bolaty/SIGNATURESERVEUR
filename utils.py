import pyodbc
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

def connect_database():
    try:
        # Connexion à la base de données SQL Server
        """
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f'SERVER={MYSQL_HOST};'
            f'DATABASE={MYSQL_DATABASE};'
            f'UID={MYSQL_USER};'
            f'PWD={MYSQL_PASSWORD};'
            "TrustServerCertificate=no;"
        )
        """
        connection_string = f'DRIVER={{SQL Server}};SERVER={MYSQL_HOST};DATABASE={MYSQL_DATABASE};UID={MYSQL_USER};PWD={MYSQL_PASSWORD}'
        #connection_string = f'DRIVER=ODBC Driver 18 for SQL Server;SERVER={MYSQL_HOST};DATABASE={MYSQL_DATABASE};UID={MYSQL_USER};PWD={MYSQL_PASSWORD}'
        #connection_string = f'DRIVER=ODBC Driver 17 for SQL Server;SERVER={MYSQL_HOST};DATABSE={MYSQL_DATABASE};UID={MYSQL_USER};PWD={MYSQL_PASSWORD};TrustServerCertificate=yes;Encrypt=no;'
        connection = pyodbc.connect(connection_string)
        print("Connexion à la base de données réussie !")
        return connection
    except pyodbc.Error as error:
        print("Erreur lors de la connexion à la base de données :", str(error))
        return None