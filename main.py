from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from chat import ask_bot, format_answer, build_fallback_answer
from database import execute_query, get_connection
import json
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="templates")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/stations", response_class=HTMLResponse)
def stations(request: Request):
    return templates.TemplateResponse("stations.html", {"request": request})

@app.get("/maintenance", response_class=HTMLResponse)
def maintenance(request: Request):
    return templates.TemplateResponse("maintenance.html", {"request": request})

@app.get("/add-data", response_class=HTMLResponse)
def add_data(request: Request):
    return templates.TemplateResponse("add-data.html", {"request": request})

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
        return {"answer": "Posez-moi une question !", "count": 0}

    explication = ""
    data = []
    count = 0

    try:
        result = ask_bot(question)
        sql = result.get("sql")
        explication = result.get("explication", "")

        if sql and sql.strip().upper().startswith("SELECT"):
            data = execute_query(sql)
            count = len(data)
    except Exception as e:
        return {"answer": f"[ERREUR étape 1] {e}", "count": 0}

    # DEBUG temporaire — à retirer une fois le problème identifié
    if not data:
        return {
            "answer": f"[DEBUG] sql généré = {repr(sql)} | explication = {repr(explication)} | data vide",
            "count": 0
        }

    try:
        answer = format_answer(question, data)
        if answer:
            return {"answer": answer, "count": count}
    except Exception as e:
        return {"answer": f"[ERREUR format_answer] {e} | fallback: {build_fallback_answer(data)}", "count": count}

    return {"answer": build_fallback_answer(data), "count": count}

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

@app.get("/api/lines")
def get_lines():
    sql = "SELECT * FROM lignes ORDER BY code"
    return execute_query(sql)

@app.get("/api/vehicles")
def get_vehicles():
    sql = "SELECT * FROM vehicules ORDER BY immatriculation"
    return execute_query(sql)

@app.get("/api/drivers")
def get_drivers():
    sql = "SELECT * FROM chauffeurs ORDER BY nom, prenom"
    return execute_query(sql)

@app.post("/api/vehicles")
def add_vehicle(vehicle: dict):
    required_fields = ['immatriculation', 'type', 'capacite']
    for field in required_fields:
        if field not in vehicle or not vehicle[field]:
            raise HTTPException(status_code=400, detail=f"Champ {field} requis")

    sql = """
        INSERT INTO vehicules (immatriculation, type, capacite, statut, kilometrage, date_acquisition)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        vehicle['immatriculation'],
        vehicle['type'],
        vehicle['capacite'],
        vehicle.get('statut', 'actif'),
        vehicle.get('kilometrage'),
        vehicle.get('date_acquisition')
    )
    execute_query(sql, params, commit=True)
    return {"message": "Véhicule ajouté avec succès"}

@app.post("/api/drivers")
def add_driver(driver: dict):
    required_fields = ['nom', 'prenom', 'numero_permis']
    for field in required_fields:
        if field not in driver or not driver[field]:
            raise HTTPException(status_code=400, detail=f"Champ {field} requis")

    sql = """
        INSERT INTO chauffeurs (nom, prenom, telephone, numero_permis, categorie_permis, date_embauche)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        driver['nom'],
        driver['prenom'],
        driver.get('telephone'),
        driver['numero_permis'],
        driver.get('categorie_permis', 'D'),
        driver.get('date_embauche')
    )
    execute_query(sql, params, commit=True)
    return {"message": "Chauffeur ajouté avec succès"}

@app.post("/api/lines")
def add_line(line: dict):
    required_fields = ['code', 'origine', 'destination']
    for field in required_fields:
        if field not in line or not line[field]:
            raise HTTPException(status_code=400, detail=f"Champ {field} requis")

    sql = """
        INSERT INTO lignes (code, nom, origine, destination, distance_km, duree_minutes)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        line['code'],
        line.get('nom'),
        line['origine'],
        line['destination'],
        line.get('distance_km'),
        line.get('duree_minutes')
    )
    execute_query(sql, params, commit=True)
    return {"message": "Ligne ajoutée avec succès"}

@app.post("/api/trips")
def add_trip(trip: dict):
    required_fields = ['ligne_id', 'chauffeur_id', 'vehicule_id', 'date_heure_depart']
    for field in required_fields:
        if field not in trip or not trip[field]:
            raise HTTPException(status_code=400, detail=f"Champ {field} requis")

    sql = """
        INSERT INTO trajets (ligne_id, chauffeur_id, vehicule_id, date_heure_depart, statut, nb_passagers)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        trip['ligne_id'],
        trip['chauffeur_id'],
        trip['vehicule_id'],
        trip['date_heure_depart'],
        trip.get('statut', 'planifie'),
        trip.get('nb_passagers')
    )
    execute_query(sql, params, commit=True)
    return {"message": "Trajet ajouté avec succès"}

@app.post("/api/maintenance")
def add_maintenance(maintenance: dict):
    required_fields = ['vehicule_id', 'type_maintenance', 'description', 'date_debut']
    for field in required_fields:
        if field not in maintenance or not maintenance[field]:
            raise HTTPException(status_code=400, detail=f"Champ {field} requis")

    sql = """
        INSERT INTO maintenance (vehicule_id, type_maintenance, description, cout, date_debut, date_fin, statut)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        maintenance['vehicule_id'],
        maintenance['type_maintenance'],
        maintenance['description'],
        maintenance.get('cout'),
        maintenance['date_debut'],
        maintenance.get('date_fin'),
        'en_cours' if not maintenance.get('date_fin') else 'termine'
    )
    execute_query(sql, params, commit=True)
    return {"message": "Maintenance ajoutée avec succès"}

# Authentication routes (basic implementation)
users_db = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"}
}

@app.post("/api/auth/login")
def login(credentials: dict):
    username = credentials.get('username')
    password = credentials.get('password')

    if not username or not password:
        raise HTTPException(status_code=400, detail="Nom d'utilisateur et mot de passe requis")

    user = users_db.get(username)
    if not user or user['password'] != password:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")

    return {
        "token": f"fake_token_{username}",
        "user": {"username": username, "role": user['role']}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)