import json
import sqlite3
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
DB_NAME = "kronos.db"
SCHEDULE_FILE = "schedule.json"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            time TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Base de datos inicializada.")

def migrate():
    print("Iniciando migración...")
    
    # 1. Inicializar DB
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 2. Migrar usuario del .env (si existe)
    env_user = os.getenv("KRONOS_USER")
    env_pass = os.getenv("KRONOS_PASSWORD")
    
    if env_user and env_pass:
        print(f"Migrando usuario desde .env: {env_user}")
        cursor.execute('INSERT OR REPLACE INTO users (username, password) VALUES (?, ?)', (env_user, env_pass))
    
    # 3. Migrar horarios desde schedule.json
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r') as f:
                data = json.load(f)
                all_schedules = data.get("schedules", {})
                
                count = 0
                for username, schedules in all_schedules.items():
                    # Si el usuario no existe en DB (y no es el del env), lo creamos con password vacía o placeholder
                    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                    if not cursor.fetchone():
                        print(f"Usuario {username} encontrado en schedules pero no en .env. Creando con password temporal...")
                        # Intentamos usar la password del env si el nombre es muy parecido? No, mejor placeholder.
                        # El usuario tendrá que loguearse de nuevo para actualizarla.
                        # Pero si ponemos placeholder, el bot fallará hasta entonces. Es lo esperado.
                        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, "PENDING_LOGIN"))
                    
                    for s in schedules:
                        s_id = s.get("id")
                        s_time = s.get("time")
                        
                        # Verificar si ya existe
                        cursor.execute('SELECT * FROM schedules WHERE id = ?', (s_id,))
                        if not cursor.fetchone():
                            cursor.execute('INSERT INTO schedules (id, username, time) VALUES (?, ?, ?)', (s_id, username, s_time))
                            count += 1
                
                print(f"Se han migrado {count} horarios.")
        except Exception as e:
            print(f"Error leyendo schedule.json: {e}")
    else:
        print("No se encontró schedule.json")
    
    conn.commit()
    conn.close()
    print("Migración completada.")

if __name__ == "__main__":
    migrate()
