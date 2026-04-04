#!/usr/bin/env python3
"""
Script de test de connexion à la base de données
"""
from database import get_connection, execute_query

def test_connection():
    try:
        print("🔍 Test de connexion à la base de données...")

        # Tester la connexion
        conn = get_connection()
        print("✅ Connexion établie")

        # Tester une requête simple
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        print("✅ Requête de test réussie")
        print("🎉 Base de données opérationnelle !")

        return True

    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("\n🔧 Solutions possibles :")
        print("1. Vérifier que DATABASE_URL est définie (Railway)")
        print("2. Vérifier les variables DB_* dans .env (local)")
        print("3. S'assurer que la base de données MySQL est démarrée")
        print("4. Vérifier les identifiants de connexion")
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)