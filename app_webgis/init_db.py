import sqlite3
import os
import glob
from werkzeug.security import generate_password_hash

DB_PATH = 'database.db'
GEOPORTAL_DIR = '../' # Parent dir has the layers

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create Users Table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    # Pre-seed users
    users = [
        ('admin', generate_password_hash('Admin@123'), 'admin'),
        ('org', generate_password_hash('Org@123'), 'org'),
        ('user', generate_password_hash('User@123'), 'user')
    ]
    cursor.executemany('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)', users)
    
    # 2. Create Layers Table
    cursor.execute('''
        CREATE TABLE layers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            filename TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            category TEXT NOT NULL
        )
    ''')
    
    ordered_layers = [
        ('Angra dos Reis', 'angra.geojson', 1, 'Limite Municipal - IBGE'),
        ('Angra dos Reis Buffer (0,1 grau)', 'buffer_angra_geojson.geojson', 1, 'Limite Municipal (Buffer) - IBGE'),
        ('Hidrografia', 'hidrografia.geojson', 1, 'Hidrografia - IBGE'),
        ('Bacia Hidrográfica - Buffer', 'BHangra_buffer_GJ.geojson', 1, 'Hidrografia'),
        ('Área Urbanizada', 'areasurbanizadas.geojson', 1, 'IBGE'),
        ('Pontos de Deslizamento Registrados', 'pontos_angra.geojson', 1, 'Ocorrências')
    ]
        
    cursor.executemany('INSERT INTO layers (name, filename, is_active, category) VALUES (?, ?, ?, ?)', ordered_layers)

    # 3. Create Submissions Table (Curadoria)
    cursor.execute('''
        CREATE TABLE submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            filename TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente',
            feedback TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Banco de dados criado com sucesso e usuários pré-configurados!")

if __name__ == '__main__':
    init_db()
