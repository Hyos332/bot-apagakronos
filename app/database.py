import sqlite3
import logging

DB_NAME = "kronos.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos con las tablas necesarias."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    
    # Tabla de horarios
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
    logging.info("Base de datos inicializada correctamente.")

def add_or_update_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (username, password)
        VALUES (?, ?)
    ''', (username, password))
    conn.commit()
    conn.close()

def get_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_schedule(schedule_id, username, time_str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO schedules (id, username, time)
        VALUES (?, ?, ?)
    ''', (schedule_id, username, time_str))
    conn.commit()
    conn.close()

def delete_schedule(schedule_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM schedules WHERE id = ?', (schedule_id,))
    conn.commit()
    conn.close()

def get_user_schedules(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM schedules WHERE username = ?', (username,))
    schedules = cursor.fetchall()
    conn.close()
    return [dict(s) for s in schedules]

def get_all_schedules_with_credentials():
    """Obtiene todos los horarios junto con las credenciales del usuario."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.time, u.username, u.password
        FROM schedules s
        JOIN users u ON s.username = u.username
    ''')
    results = cursor.fetchall()
    conn.close()
    return [dict(r) for r in results]
