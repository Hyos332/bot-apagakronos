import json
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = "app/kronos.db"
SCHEDULE_FILE = "schedule.json"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def migrate():
    print("Iniciando migración...")
    
    # 1. Conectar a DB (se creará si no existe gracias a database.init_db() que deberíamos llamar, 
    # pero aquí lo haremos manual o importando)
    # Mejor importamos app.database para asegurar consistencia
    import sys
    sys.path.append(os.path.join(os.getcwd(), 'app'))
    import database
    
    # Asegurar que estamos usando la ruta correcta para la DB en database.py
    # database.py usa "kronos.db" relativo. Si lo ejecutamos desde root, será root/kronos.db?
    # web.py está en app/, así que database.py (en app/) usará app/kronos.db si se ejecuta desde app?
    # No, si ejecutamos `python app/web.py` desde root, el CWD es root.
    # Si ejecutamos `cd app && python web.py`, el CWD es app.
    # Dockerfile suele establecer WORKDIR.
    
    # Vamos a verificar el Dockerfile para ver el WORKDIR.
    pass

if __name__ == "__main__":
    migrate()
