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
- chauffeurs(id, nom, prenom, telephone, numero_permis, disponibilite, vehicule_id)
- lignes(id, code, nom, origine, destination, distance_km)
- tarifs(id, ligne_id, type_client, prix)
- trajets(id, ligne_id, chauffeur_id, vehicule_id, date_heure_depart, date_heure_arrivee, statut, nb_passagers, recette)
- incidents(id, trajet_id, type, gravite, date_incident, resolu)
- maintenance(id, vehicule_id, type_maintenance, description, cout, date_debut, date_fin, statut)
- stations(id, ligne_id, nom, ordre, latitude, longitude)

Regles IMPORTANTES :
1. Genere UNIQUEMENT des requetes SELECT
2. JAMAIS de INSERT, UPDATE, DELETE, DROP
3. Reponds UNIQUEMENT avec du JSON valide, sans aucun texte avant ou apres :
{"sql": "SELECT ...", "explication": "Voici les resultats..."}
4. Si pas besoin de SQL :
{"sql": null, "explication": "Ta reponse ici"}
5. Si un utilisateur demande le "chiffre d'affaire" ou les "recettes", il s'agit de la colonne `recette` dans la table `trajets`. Exemple total: SELECT SUM(recette) FROM trajets;
6. Pour filtrer sur le "mois", ou "ajourd'hui", utilise bien les fonctions SQL (ex: MONTH(date_heure_depart) = MONTH(CURRENT_DATE))
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
    """Génère une réponse en langage naturel à partir des données SQL via LLM."""
    if not data:
        return None

    client = get_groq_client()
    data_text = json.dumps(data, ensure_ascii=False, indent=2, default=str)

    prompt = f"""Tu es TranspoBot, assistant de gestion de transport au Sénégal. On t'a posé cette question : "{question}"

La base de données a retourné ces données :
{data_text}

Réponds directement à la question en une ou deux phrases naturelles et précises en français.
Exemples de format attendu :
- "La recette totale de 2025 est de 1 250 000 FCFA."
- "Il y a actuellement 8 véhicules actifs."
- "Les 3 chauffeurs disponibles sont : Mamadou Diallo, Fatou Ndiaye et Ibrahima Sow."
- "Il y a 2 trajets en cours : Aminata BA sur la ligne L1 et Ibrahima Fall sur la ligne L4."

Si les données contiennent plusieurs lignes, fais un résumé clair et lisible. Sois direct, sans introduction ni explication technique."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()


def build_fallback_answer(data):
    """Construit une réponse lisible sans LLM, utilisée si format_answer échoue."""
    if not data:
        return None

    rows = len(data)
    cols = list(data[0].keys())

    # Valeur unique (ex: COUNT, SUM)
    if rows == 1 and len(cols) == 1:
        key = cols[0]
        val = data[0][key]
        return f"Résultat : **{val}**"

    # Une seule ligne, plusieurs colonnes
    if rows == 1:
        parts = [f"{k} : {v}" for k, v in data[0].items() if v is not None]
        return " | ".join(parts)

    # Plusieurs lignes
    lines = []
    for row in data[:8]:
        parts = [str(v) for v in row.values() if v is not None]
        lines.append("• " + " — ".join(parts))
    result = f"{rows} résultat(s) trouvé(s) :\n" + "\n".join(lines)
    if rows > 8:
        result += f"\n... et {rows - 8} autres."
    return result
