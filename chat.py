import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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