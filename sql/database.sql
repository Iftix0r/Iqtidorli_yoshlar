-- Iqtidorli Yoshlar Platform — MySQL Database
CREATE DATABASE IF NOT EXISTS iqtidorli_yoshlar CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE iqtidorli_yoshlar;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('yosh','mentor','investor','admin') DEFAULT 'yosh',
    region VARCHAR(100),
    bio TEXT,
    avatar VARCHAR(255),
    score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    skill_name VARCHAR(80) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    link VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE contests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    deadline DATE,
    prize VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Demo ma'lumotlar
INSERT INTO users (full_name, email, password, role, region, score) VALUES
('Asilbek Toshmatov', 'asilbek@example.com', '$2y$10$examplehash1', 'yosh', 'Namangan viloyati', 980),
('Zulfiya Rahimova',  'zulfiya@example.com',  '$2y$10$examplehash2', 'yosh', 'Samarqand viloyati', 945),
('Jasur Mirzayev',   'jasur@example.com',    '$2y$10$examplehash3', 'yosh', 'Farg\'ona viloyati', 912),
('Nilufar Xasanova', 'nilufar@example.com',  '$2y$10$examplehash4', 'yosh', 'Qashqadaryo viloyati', 887);

INSERT INTO skills (user_id, skill_name) VALUES
(1,'React'),(1,'Node.js'),(1,'AI'),
(2,'Figma'),(2,'Branding'),
(3,'Python'),(3,'ML'),(3,'SQL'),
(4,'Flutter'),(4,'Dart');

INSERT INTO contests (title, description, deadline, prize) VALUES
('IT Startap Tanlovi 2026', 'Eng yaxshi IT startap loyihasi uchun grant', '2026-06-30', '50,000,000 so\'m'),
('Yoshlar Innovatsiya Festivali', 'Barcha sohalarda innovatsion g\'oyalar', '2026-07-15', '30,000,000 so\'m'),
('Raqamli O\'zbekiston Hackathon', '48 soatlik dasturlash musobaqasi', '2026-05-20', '20,000,000 so\'m');
