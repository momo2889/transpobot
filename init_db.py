#!/usr/bin/env python3
"""
Script d'initialisation de la base de données pour Railway
"""
import mysql.connector
import os
from urllib.parse import urlparse

def init_database():
    # Pour Railway, utiliser DATABASE_URL si disponible
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL non trouvée")
        return False

    try:
        # Parser l'URL de Railway
        parsed = urlparse(database_url)

        # Connexion sans base de données spécifique pour créer la DB
        conn = mysql.connector.connect(
            host=parsed.hostname,
            user=parsed.username,
            password=parsed.password,
            port=parsed.port or 3306
        )

        cursor = conn.cursor()

        # Créer la base de données si elle n'existe pas
        db_name = parsed.path.lstrip('/')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"✅ Base de données '{db_name}' créée/vérifiée")

        # Fermer la connexion et se reconnecter à la DB spécifique
        cursor.close()
        conn.close()

        # Se reconnecter à la base spécifique
        conn = mysql.connector.connect(
            host=parsed.hostname,
            user=parsed.username,
            password=parsed.password,
            database=db_name,
            port=parsed.port or 3306
        )

        cursor = conn.cursor()

        # Lire et exécuter le schéma
        with open('schema.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Diviser en statements individuels
        statements = sql_content.split(';')

        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    print(f"✅ Exécuté: {statement[:50]}...")
                except Exception as e:
                    print(f"⚠️ Erreur sur: {statement[:50]}... - {e}")

        conn.commit()
        cursor.close()
        conn.close()

        print("🎉 Base de données initialisée avec succès !")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    exit(0 if success else 1)