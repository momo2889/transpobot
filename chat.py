import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY n'est pas configurée")
    return Groq(api_key=api_key)

SYSTEM_PROMPT = """
Tu es TranspoBot, assistant IA de gestion de transport urbain au Senegal.
Tu as acces a une base MySQL avec ces tables :

- vehicules(id, immatriculation, type, capacite, statut, kilometrage)
  statut possible : 'actif', 'en_maintenance', 'hors_service'

- chauffeurs(id, nom, prenom, telephone, numero_permis, disponibilite, vehicule_id)
  disponibilite possible : 1 (disponible) ou 0 (non disponible)

- lignes(id, code, nom, origine, destination, distance_km)

- tarifs(id, ligne_id, type_client, prix)

- trajets(id, ligne_id, chauffeur_id, vehicule_id, date_heure_depart, date_heure_arrivee, statut, nb_passagers, recette)
  statut possible : 'en_cours', 'termine', 'planifie'
  recette = chiffre d'affaires du trajet (en FCFA)

- incidents(id, trajet_id, type, gravite, date_incident, resolu)
  resolu : 0 (non resolu) ou 1 (resolu)

- maintenance(id, vehicule_id, type_maintenance, description, cout, date_debut, date_fin, statut)
  statut possible : 'en_cours', 'termine', 'planifie'

- stations(id, ligne_id, nom, ordre, latitude, longitude)

Regles IMPORTANTES :
1. Genere UNIQUEMENT des requetes SELECT
2. JAMAIS de INSERT, UPDATE, DELETE, DROP
3. Reponds UNIQUEMENT avec du JSON valide, sans aucun texte avant ou apres :
   {"sql": "SELECT ...", "explication": "..."}
4. Si pas besoin de SQL : {"sql": null, "explication": "Ta reponse ici"}
5. Utilise TOUJOURS les valeurs exactes avec underscore : 'en_cours', 'termine', 'planifie', 'actif', 'en_maintenance'

GESTION DES PERIODES DE TEMPS (pour recette, trajets, etc.) :
- "du mois" / "ce mois" → WHERE MONTH(date_heure_depart) = MONTH(CURRENT_DATE) AND YEAR(date_heure_depart) = YEAR(CURRENT_DATE)
- "de la semaine" / "cette semaine" → WHERE YEARWEEK(date_heure_depart) = YEARWEEK(CURRENT_DATE)
- "d'aujourd'hui" / "aujourd'hui" → WHERE DATE(date_heure_depart) = CURDATE()
- "de l'année" / "cette annee" → WHERE YEAR(date_heure_depart) = YEAR(CURRENT_DATE)
- "de l'année 2025" → WHERE YEAR(date_heure_depart) = 2025
- "de l'année 2024" → WHERE YEAR(date_heure_depart) = 2024
- "des deux derniers mois" → WHERE date_heure_depart >= DATE_SUB(CURRENT_DATE, INTERVAL 2 MONTH)
- "des deux prochains mois" → WHERE date_heure_depart BETWEEN CURRENT_DATE AND DATE_ADD(CURRENT_DATE, INTERVAL 2 MONTH)
- "du mois dernier" → WHERE MONTH(date_heure_depart) = MONTH(CURRENT_DATE) - 1 AND YEAR(date_heure_depart) = YEAR(CURRENT_DATE)
- "de la semaine derniere" → WHERE YEARWEEK(date_heure_depart) = YEARWEEK(CURRENT_DATE) - 1

EXEMPLES :
- Recette du mois : SELECT SUM(recette) as recette_totale FROM trajets WHERE MONTH(date_heure_depart) = MONTH(CURRENT_DATE) AND YEAR(date_heure_depart) = YEAR(CURRENT_DATE)
- Trajets en cours : SELECT t.id, l.code as ligne, CONCAT(c.prenom, ' ', c.nom) as chauffeur, t.date_heure_depart FROM trajets t JOIN lignes l ON t.ligne_id = l.id JOIN chauffeurs c ON t.chauffeur_id = c.id WHERE t.statut = 'en_cours'
- Vehicules actifs : SELECT * FROM vehicules WHERE statut = 'actif'
"""

def ask_bot(question):
    client = get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ],
        temperature=0.1
    )

    content = response.choices[0].message.content.strip()

    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    start = content.find("{")
    end = content.rfind("}") + 1
    if start != -1 and end != 0:
        content = content[start:end]

    return json.loads(content)


def format_answer(question, data):
    """Génère une réponse naturelle quand des données sont trouvées."""
    if not data:
        return None
    client = get_groq_client()
    data_text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    prompt = f"""Tu es TranspoBot, assistant de gestion de transport au Sénégal. On t'a posé cette question : "{question}"

La base de données a retourné ces données :
{data_text}

Réponds directement à la question en une ou deux phrases naturelles et précises en français.
Exemples :
- "La recette totale de 2025 est de 1 250 000 FCFA."
- "Il y a actuellement 8 véhicules actifs."
- "Il y a 2 trajets en cours : Aminata BA sur la ligne L1 et Ibrahima Fall sur la ligne L4."
- "Les 3 chauffeurs disponibles sont : Mamadou Diallo, Fatou Ndiaye et Ibrahima Sow."

Si plusieurs lignes, fais un résumé clair. Sois direct, sans introduction ni détail technique."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()


def format_empty_answer(question):
    """Génère une réponse naturelle quand la requête ne retourne aucun résultat."""
    client = get_groq_client()
    prompt = f"""Tu es TranspoBot, assistant de transport. On t'a posé cette question : "{question}"

La base de données ne contient aucune donnée correspondant à cette question pour le moment.

Génère une réponse courte et naturelle en français adaptée à la question. Exemples :
- "Il n'y a aucun trajet en cours pour le moment."
- "Aucune recette n'a été enregistrée pour cette période."
- "Aucun incident n'est signalé actuellement."
- "Il n'y a aucune maintenance en cours en ce moment."

Réponds en une seule phrase naturelle, sans mention de base de données ou de requête."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()


def build_fallback_answer(data):
    """Construit une réponse lisible sans LLM, utilisée si format_answer échoue."""
    if not data:
        return None

    rows = len(data)
    cols = list(data[0].keys())

    if rows == 1 and len(cols) == 1:
        key = cols[0]
        val = data[0][key]
        return f"Résultat : {val}"

    if rows == 1:
        parts = [f"{k} : {v}" for k, v in data[0].items() if v is not None]
        return " | ".join(parts)

    lines = []
    for row in data[:8]:
        parts = [str(v) for v in row.values() if v is not None]
        lines.append("• " + " — ".join(parts))
    result = f"{rows} résultat(s) :\n" + "\n".join(lines)
    if rows > 8:
        result += f"\n... et {rows - 8} autres."
    return result
