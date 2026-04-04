import mysql.connector
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

def get_connection():
    # Pour Railway, utiliser DATABASE_URL si disponible
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Parser l'URL de Railway
        parsed = urlparse(database_url)
        return mysql.connector.connect(
            host=parsed.hostname,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            port=parsed.port or 3306
        )
    else:
        # Configuration locale avec variables individuelles
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "transpobot"),
            port=int(os.getenv("DB_PORT", 3306))
        )

def execute_query(sql, params=None, commit=False):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        if commit:
            conn.commit()

        # Pour les SELECT, retourner les résultats
        if sql.strip().upper().startswith("SELECT"):
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        else:
            # Pour INSERT/UPDATE/DELETE, retourner le nombre de lignes affectées
            affected_rows = cursor.rowcount
            cursor.close()
            conn.close()
            return affected_rows

    except mysql.connector.Error as e:
        print(f"❌ Erreur base de données: {e}")
        raise Exception(f"Erreur base de données: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        raise Exception(f"Erreur inattendue: {e}")
        cursor.execute(sql)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results