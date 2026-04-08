from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from chat import ask_bot, format_answer, format_empty_answer, build_fallback_answer
from database import execute_query, get_connection
from datetime import datetime, timedelta, timezone
import json, secrets, os
app = FastAPI()

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Templates
templates = Jinja2Templates(directory="templates")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return RedirectResponse(url="/login")

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
def get_stats(request: Request):
    get_current_user(request)
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
def get_trajets(request: Request):
    get_current_user(request)
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
def chat(request: Request, body: dict):
    get_current_user(request)
    question = body.get("question", "")

    if not question:
        return {"answer": "Posez-moi une question !", "count": 0}

    if len(question) > 500:
        return {"answer": "Question trop longue (500 caractères max).", "count": 0}

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
        print(f"[ERREUR ask_bot/execute_query] {e}")
        return {"answer": "Je n'ai pas pu analyser cette question. Reformulez-la différemment.", "count": 0}

    if not data:
        try:
            return {"answer": format_empty_answer(question), "count": 0}
        except Exception:
            return {"answer": explication or "Aucun résultat trouvé pour cette question.", "count": 0}

    try:
        answer = format_answer(question, data)
        if answer:
            return {"answer": answer, "count": count}
    except Exception as e:
        print(f"[ERREUR format_answer] {e}")

    return {"answer": build_fallback_answer(data) or explication, "count": count}

@app.get("/api/maintenance")
def get_maintenance(request: Request):
    get_current_user(request)
    sql = """
        SELECT m.id, v.immatriculation, m.type_maintenance, m.description, 
               m.cout, m.date_debut, m.date_fin, m.statut
        FROM maintenance m
        JOIN vehicules v ON m.vehicule_id = v.id
        ORDER BY m.date_debut DESC
    """
    return execute_query(sql)

@app.get("/api/stations")
def get_stations(request: Request):
    get_current_user(request)
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
def get_lines(request: Request):
    get_current_user(request)
    sql = "SELECT * FROM lignes ORDER BY code"
    return execute_query(sql)

@app.get("/api/vehicles")
def get_vehicles(request: Request):
    get_current_user(request)
    sql = "SELECT * FROM vehicules ORDER BY immatriculation"
    return execute_query(sql)

@app.get("/api/drivers")
def get_drivers(request: Request):
    get_current_user(request)
    sql = "SELECT * FROM chauffeurs ORDER BY nom, prenom"
    return execute_query(sql)

@app.post("/api/vehicles")
def add_vehicle(request: Request, vehicle: dict):
    require_admin(request)
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
def add_driver(request: Request, driver: dict):
    require_admin(request)
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
def add_line(request: Request, line: dict):
    require_admin(request)
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
def add_trip(request: Request, trip: dict):
    require_admin(request)
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
def add_maintenance(request: Request, maintenance: dict):
    require_admin(request)
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

# ===== AUTHENTIFICATION =====
# Mots de passe lus depuis les variables d'environnement (Railway)
users_db = {
    "admin":     {"password": os.getenv("ADMIN_PASSWORD", "admin123"),     "role": "admin",     "display": "Administrateur"},
    "president": {"password": os.getenv("PRESIDENT_PASSWORD", "president123"), "role": "president", "display": "Président"},
}

# Tokens actifs : {token: {username, role, display, expires_at}}
active_tokens: dict = {}
TOKEN_TTL = timedelta(hours=8)

# Rate limiting login : {ip: {"count": int, "blocked_until": datetime|None}}
login_attempts: dict = {}
MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

def _get_ip(request: Request) -> str:
    return request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()

def _check_rate_limit(ip: str):
    now = datetime.now(timezone.utc)
    data = login_attempts.get(ip, {"count": 0, "blocked_until": None})
    if data["blocked_until"] and now < data["blocked_until"]:
        secs = int((data["blocked_until"] - now).total_seconds())
        raise HTTPException(status_code=429, detail=f"Trop de tentatives. Réessayez dans {secs // 60 + 1} min.")

def _record_failure(ip: str):
    now = datetime.now(timezone.utc)
    data = login_attempts.get(ip, {"count": 0, "blocked_until": None})
    data["count"] = data.get("count", 0) + 1
    if data["count"] >= MAX_ATTEMPTS:
        data["blocked_until"] = now + timedelta(minutes=LOCKOUT_MINUTES)
        data["count"] = 0
    login_attempts[ip] = data

def get_current_user(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    entry = active_tokens.get(token)
    if not entry:
        raise HTTPException(status_code=401, detail="Token invalide")
    if datetime.now(timezone.utc) > entry["expires_at"]:
        active_tokens.pop(token, None)
        raise HTTPException(status_code=401, detail="Session expirée, reconnectez-vous")
    return entry

def require_admin(request: Request):
    user = get_current_user(request)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé à l'administrateur")
    return user

@app.post("/api/auth/login")
def auth_login(request: Request, credentials: dict):
    ip = _get_ip(request)
    _check_rate_limit(ip)
    username = credentials.get("username", "").strip()
    password = credentials.get("password", "")
    user = users_db.get(username)
    # secrets.compare_digest évite les attaques par timing
    if not user or not secrets.compare_digest(password, user["password"]):
        _record_failure(ip)
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    login_attempts.pop(ip, None)  # reset si succès
    token = secrets.token_hex(32)
    active_tokens[token] = {
        "username": username, "role": user["role"],
        "display": user["display"], "expires_at": datetime.now(timezone.utc) + TOKEN_TTL
    }
    return {"token": token, "user": {"username": username, "role": user["role"], "display": user["display"]}}

@app.get("/api/auth/verify")
def auth_verify(request: Request):
    user = get_current_user(request)
    return {"username": user["username"], "role": user["role"], "display": user["display"]}

@app.post("/api/auth/logout")
def auth_logout(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    active_tokens.pop(token, None)
    return {"message": "Déconnecté"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)