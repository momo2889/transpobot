-- ============================================================
--  TranspoBot — Base de données MySQL
--  Projet GLSi L3 — ESP/UCAD
-- ============================================================


-- Véhicules
CREATE TABLE vehicules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    immatriculation VARCHAR(20) NOT NULL UNIQUE,
    type ENUM('bus','minibus','taxi') NOT NULL,
    capacite INT NOT NULL,
    statut ENUM('actif','maintenance','hors_service') DEFAULT 'actif',
    kilometrage INT DEFAULT 0,
    date_acquisition DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chauffeurs
CREATE TABLE chauffeurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    telephone VARCHAR(20),
    numero_permis VARCHAR(30) UNIQUE NOT NULL,
    categorie_permis VARCHAR(5),
    disponibilite BOOLEAN DEFAULT TRUE,
    vehicule_id INT,
    date_embauche DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicule_id) REFERENCES vehicules(id)
);

-- Lignes / trajets types
CREATE TABLE lignes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    nom VARCHAR(100),
    origine VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    distance_km DECIMAL(6,2),
    duree_minutes INT
);

-- Tarifs
CREATE TABLE tarifs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ligne_id INT NOT NULL,
    type_client ENUM('normal','etudiant','senior') DEFAULT 'normal',
    prix DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (ligne_id) REFERENCES lignes(id)
);

-- Trajets effectués
CREATE TABLE trajets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ligne_id INT NOT NULL,
    chauffeur_id INT NOT NULL,
    vehicule_id INT NOT NULL,
    date_heure_depart DATETIME NOT NULL,
    date_heure_arrivee DATETIME,
    statut ENUM('planifie','en_cours','termine','annule') DEFAULT 'planifie',
    nb_passagers INT DEFAULT 0,
    recette DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ligne_id) REFERENCES lignes(id),
    FOREIGN KEY (chauffeur_id) REFERENCES chauffeurs(id),
    FOREIGN KEY (vehicule_id) REFERENCES vehicules(id)
);

-- Incidents
CREATE TABLE incidents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trajet_id INT NOT NULL,
    type ENUM('panne','accident','retard','autre') NOT NULL,
    description TEXT,
    gravite ENUM('faible','moyen','grave') DEFAULT 'faible',
    date_incident DATETIME NOT NULL,
    resolu BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trajet_id) REFERENCES trajets(id)
);
CREATE TABLE maintenance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicule_id INT NOT NULL,
    type_maintenance ENUM('revision','reparation','controle') NOT NULL,
    description TEXT,
    cout DECIMAL(10,2),
    date_debut DATE NOT NULL,
    date_fin DATE,
    statut ENUM('en_cours','termine') DEFAULT 'en_cours',
    FOREIGN KEY (vehicule_id) REFERENCES vehicules(id)
);

-- Stations d'arrêt
CREATE TABLE stations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ligne_id INT NOT NULL,
    nom VARCHAR(100) NOT NULL,
    ordre INT NOT NULL,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ligne_id) REFERENCES lignes(id)
);
-- ============================================================
--  Données de test
-- ============================================================

INSERT INTO vehicules (immatriculation, type, capacite, statut, kilometrage, date_acquisition) VALUES
('DK-1234-AB', 'bus', 60, 'actif', 45000, '2021-03-15'),
('DK-5678-CD', 'minibus', 25, 'actif', 32000, '2022-06-01'),
('DK-9012-EF', 'bus', 60, 'maintenance', 78000, '2019-11-20'),
('DK-3456-GH', 'taxi', 5, 'actif', 120000, '2020-01-10'),
('DK-7890-IJ', 'minibus', 25, 'actif', 15000, '2023-09-05');

INSERT INTO chauffeurs (nom, prenom, telephone, numero_permis, categorie_permis, vehicule_id, date_embauche) VALUES
('DIOP', 'Mamadou', '+221771234567', 'P-2019-001', 'D', 1, '2019-04-01'),
('FALL', 'Ibrahima', '+221772345678', 'P-2020-002', 'D', 2, '2020-07-15'),
('NDIAYE', 'Fatou', '+221773456789', 'P-2021-003', 'B', 4, '2021-02-01'),
('SECK', 'Ousmane', '+221774567890', 'P-2022-004', 'D', 5, '2022-10-20'),
('BA', 'Aminata', '+221775678901', 'P-2023-005', 'D', NULL, '2023-01-10');

INSERT INTO lignes (code, nom, origine, destination, distance_km, duree_minutes) VALUES
('L1', 'Ligne Dakar-Thiès', 'Dakar', 'Thiès', 70.5, 90),
('L2', 'Ligne Dakar-Mbour', 'Dakar', 'Mbour', 82.0, 120),
('L3', 'Ligne Centre-Banlieue', 'Plateau', 'Pikine', 15.0, 45),
('L4', 'Ligne Aéroport', 'Centre-ville', 'AIBD', 45.0, 60);

INSERT INTO tarifs (ligne_id, type_client, prix) VALUES
(1, 'normal', 2500), (1, 'etudiant', 1500), (1, 'senior', 1800),
(2, 'normal', 3000), (2, 'etudiant', 1800),
(3, 'normal', 500),  (3, 'etudiant', 300),
(4, 'normal', 5000), (4, 'etudiant', 3000);

INSERT INTO trajets (ligne_id, chauffeur_id, vehicule_id, date_heure_depart, date_heure_arrivee, statut, nb_passagers, recette) VALUES
(1, 1, 1, '2026-03-01 06:00:00', '2026-03-01 07:30:00', 'termine', 55, 137500),
(1, 2, 2, '2026-03-01 08:00:00', '2026-03-01 09:30:00', 'termine', 20, 50000),
(2, 3, 4, '2026-03-02 07:00:00', '2026-03-02 09:00:00', 'termine', 4, 12000),
(3, 4, 5, '2026-03-05 07:30:00', '2026-03-05 08:15:00', 'termine', 22, 11000),
(1, 1, 1, '2026-03-10 06:00:00', '2026-03-10 07:30:00', 'termine', 58, 145000),
(4, 2, 2, '2026-03-12 09:00:00', '2026-03-12 10:00:00', 'termine', 18, 90000),
(1, 5, 1, '2026-03-20 06:00:00', NULL, 'en_cours', 45, 112500),

(1, 1, 1, '2024-01-05 06:00:00', '2024-01-05 07:35:00', 'termine', 53, 132500),
(1, 2, 2, '2024-02-14 08:10:00', '2024-02-14 09:45:00', 'termine', 48, 120000),
(2, 3, 4, '2024-03-21 07:30:00', '2024-03-21 09:30:00', 'termine', 38, 110000),
(3, 4, 5, '2024-04-02 07:00:00', '2024-04-02 07:50:00', 'termine', 20, 10000),
(4, 1, 1, '2024-05-10 09:00:00', '2024-05-10 10:00:00', 'termine', 17, 85000),
(1, 2, 2, '2024-06-15 06:20:00', '2024-06-15 07:55:00', 'termine', 62, 155000),
(2, 3, 4, '2024-07-18 07:45:00', '2024-07-18 09:55:00', 'termine', 30, 90000),
(3, 4, 5, '2024-08-22 08:30:00', '2024-08-22 09:15:00', 'termine', 25, 12500),
(4, 1, 1, '2024-09-30 10:00:00', '2024-09-30 11:00:00', 'termine', 14, 70000),
(1, 2, 2, '2024-10-12 06:05:00', '2024-10-12 07:35:00', 'termine', 50, 125000),
(2, 3, 4, '2024-11-25 07:10:00', '2024-11-25 09:20:00', 'termine', 40, 95000),
(3, 4, 5, '2024-12-31 09:15:00', '2024-12-31 10:00:00', 'termine', 28, 14000),

(1, 1, 1, '2025-01-08 06:05:00', '2025-01-08 07:40:00', 'termine', 54, 135000),
(1, 2, 2, '2025-02-13 08:20:00', '2025-02-13 10:00:00', 'termine', 46, 115000),
(2, 3, 4, '2025-03-22 07:35:00', '2025-03-22 09:25:00', 'termine', 33, 82500),
(3, 4, 5, '2025-04-29 07:20:00', '2025-04-29 08:10:00', 'termine', 19, 9500),
(4, 1, 1, '2025-05-16 09:30:00', '2025-05-16 10:25:00', 'termine', 16, 80000),
(1, 2, 2, '2025-06-21 06:05:00', '2025-06-21 07:40:00', 'termine', 59, 147500),
(2, 3, 4, '2025-07-19 08:05:00', '2025-07-19 10:05:00', 'termine', 32, 96000),
(3, 4, 5, '2025-08-25 08:35:00', '2025-08-25 09:20:00', 'termine', 27, 13500),
(4, 1, 1, '2025-09-14 10:10:00', '2025-09-14 11:15:00', 'termine', 15, 75000),
(1, 2, 2, '2025-10-03 06:15:00', '2025-10-03 07:50:00', 'termine', 51, 127500),
(2, 3, 4, '2025-11-27 07:15:00', '2025-11-27 09:20:00', 'termine', 41, 102500),
(3, 4, 5, '2025-12-22 09:10:00', '2025-12-22 10:05:00', 'termine', 29, 14500);

INSERT INTO incidents (trajet_id, type, description, gravite, date_incident, resolu) VALUES
(2, 'retard', 'Embouteillage au centre-ville', 'faible', '2026-03-01 08:45:00', TRUE),
(3, 'panne', 'Crevaison pneu avant droit', 'moyen', '2026-03-02 07:30:00', TRUE),
(6, 'accident', 'Accrochage léger au rond-point', 'grave', '2026-03-12 09:20:00', FALSE);

INSERT INTO maintenance (vehicule_id, type_maintenance, description, cout, date_debut, date_fin, statut) VALUES
(1, 'revision', 'Révision périodique annuelle - freins, moteur, suspension', 150000, '2026-01-15', '2026-01-20', 'termine'),
(2, 'reparation', 'Remplacement climatisation défaillante', 95000, '2026-02-10', '2026-02-12', 'termine'),
(3, 'controle', 'Contrôle technique obligatoire', 25000, '2026-03-01', '2026-03-01', 'termine'),
(4, 'reparation', 'Réparation moteur - surchauffe', 580000, '2026-03-28', NULL, 'en_cours'),
(5, 'revision', 'Révision semestrielle - vidange, filtres, pneus', 75000, '2026-04-01', NULL, 'en_cours'),
(1, 'reparation', 'Réparation carrosserie après accident', 1200000, '2026-03-25', NULL, 'en_cours'),
(2, 'controle', 'Contrôle sécurité avant saison touristique', 15000, '2026-03-15', '2026-03-15', 'termine');

INSERT INTO stations (ligne_id, nom, ordre, latitude, longitude) VALUES
-- Ligne Dakar-Thiès (L1)
(1, 'Gare Routière Dakar', 1, 14.693425, -17.447938),
(1, 'Keur Massar', 2, 14.783333, -17.316667),
(1, 'Keuri Kaw', 3, 14.766667, -17.283333),
(1, 'Niaga', 4, 14.483333, -16.966667),
(1, 'Gare Routière Thiès', 5, 14.791005, -16.926297),

-- Ligne Dakar-Mbour (L2)
(2, 'Gare Routière Dakar', 1, 14.693425, -17.447938),
(2, 'Keur Massar', 2, 14.783333, -17.316667),
(2, 'Sébi Ponty', 3, 14.700000, -17.283333),
(2, 'Koungheul', 4, 13.983333, -16.116667),
(2, 'Gare Routière Mbour', 5, 14.420000, -16.970000),

-- Ligne Centre-Banlieue (L3)
(3, 'Plateau', 1, 14.664167, -17.438056),
(3, 'Marché Kermel', 2, 14.670000, -17.430000),
(3, 'Colobane', 3, 14.680000, -17.420000),
(3, 'Ouakam', 4, 14.690000, -17.410000),
(3, 'Gare Routière Pikine', 5, 14.750000, -17.390000),

-- Ligne Aéroport (L4)
(4, 'Centre-ville Dakar', 1, 14.693425, -17.447938),
(4, 'Marché Kermel', 2, 14.670000, -17.430000),
(4, 'Aéroport Léopold Sédar Senghor', 3, 14.739167, -17.490278);
