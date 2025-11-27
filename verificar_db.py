import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('kronos.db')
cursor = conn.cursor()

# Consultar usuarios
print("--- USUARIOS GUARDADOS EN BASE DE DATOS ---")
try:
    cursor.execute("SELECT username, password FROM users")
    users = cursor.fetchall()
    
    if users:
        for user in users:
            print(f"Usuario: {user[0]} | Contraseña: {user[1]}")
    else:
        print("No hay usuarios guardados todavía.")
except Exception as e:
    print(f"Error leyendo la base de datos: {e}")

conn.close()
