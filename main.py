from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from chat import ask_bot
from database import execute_query, get_connection
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/app")
def serve_frontend():
    return FileResponse("index.html")

@app.get("/")
def home():
    return {"message": "TranspoBot API fonctionne !"}

@app.get("/api/stats")
def get_stats():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT COUNT(*) as total FROM trajets WHERE statut='termine'")
    total = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COUNT(*) as en_cours FROM trajets WHERE statut='en_cours'")
    en_cours = cursor.fetchone()["en_cours"]
    
    cursor.execute("SELECT COUNT(*) as actifs FROM vehicules WHERE statut='actif'")
    actifs = cursor.fetchone()["actifs"]
    
    cursor.execute("SELECT COUNT(*) as ouverts FROM incidents WHERE resolu=FALSE")
    ouverts = cursor.fetchone()["ouverts"]
    
    cursor.close()
    conn.close()
    
    return {
        "total_trajets": total,
        "trajets_en_cours": en_cours,
        "vehicules_actifs": actifs,
        "incidents_ouverts": ouverts
    }

@app.get("/api/trajets/recent")
def get_trajets():
    sql = """
        SELECT t.id, l.code as ligne,
               CONCAT(c.prenom, ' ', c.nom) as chauffeur_nom,
               t.date_heure_depart, t.statut
        FROM trajets t
        JOIN lignes l ON t.ligne_id = l.id
        JOIN chauffeurs c ON t.chauffeur_id = c.id
        ORDER BY t.date_heure_depart DESC
        LIMIT 8
    """
    return execute_query(sql)

@app.post("/api/chat")
def chat(body: dict):
    question = body.get("question", "")
    
    if not question:
        return {"answer": "Posez-moi une question !", "sql": None, "data": []}
    
    try:
        result = ask_bot(question)
        sql = result.get("sql")
        explication = result.get("explication", "")
        data = []
        count = 0
        
        if sql and sql.strip().upper().startswith("SELECT"):
            data = execute_query(sql)
            count = len(data)
        
        return {
            "answer": explication,
            "sql": sql,
            "data": data,
            "count": count
        }
    
    except Exception as e:
        return {
            "answer": "Desole, je n'ai pas pu traiter cette question.",
            "sql": None,
            "data": [],
            "count": 0
        }

@app.get("/api/maintenance")
def get_maintenance():
    sql = """
        SELECT m.id, v.immatriculation, m.type_maintenance, m.description, 
               m.cout, m.date_debut, m.date_fin, m.statut
        FROM maintenance m
        JOIN vehicules v ON m.vehicule_id = v.id
        ORDER BY m.date_debut DESC
    """
    return execute_query(sql)

@app.get("/api/stations")
def get_stations():
    sql = """
        SELECT s.id, l.code as ligne_code, l.nom as ligne_nom, 
               s.nom as station_nom, s.ordre, s.latitude, s.longitude
        FROM stations s
        JOIN lignes l ON s.ligne_id = l.id
        ORDER BY l.code, s.ordre
    """
    return execute_query(sql)

@app.get("/api/stations/{ligne_id}")
def get_stations_by_line(ligne_id: int):
    sql = """
        SELECT s.id, s.nom, s.ordre, s.latitude, s.longitude
        FROM stations s
        WHERE s.ligne_id = %s
        ORDER BY s.ordre
    """
    return execute_query(sql, (ligne_id,))