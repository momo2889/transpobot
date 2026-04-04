import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def execute_query(sql, params=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results