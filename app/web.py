from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
import logging
import json
import os
from bot import KronosBot
import atexit
from functools import wraps
import database

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Clave secreta para sesiones

# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Zona horaria de España
TIMEZONE = timezone('Europe/Madrid')

scheduler = BackgroundScheduler(timezone=TIMEZONE)

# --- FUNCIONES AUXILIARES ---

def run_bot_job(username, password):
    """Ejecuta el bot con las credenciales proporcionadas"""
    logger.info(f"⏰ Ejecutando tarea programada para usuario: {username}...")
    bot = KronosBot()
    bot.username = username
    bot.password = password
    success, message = bot.run()
    logger.info(f"Resultado de la tarea: {success} - {message}")

def schedule_job(time_str, job_id, username, password):
    """Programa un trabajo en el scheduler"""
    hour, minute = map(int, time_str.split(':'))
    
    # Verificar si ya existe un job con ese ID y eliminarlo si es necesario
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    # Programar nuevo trabajo
    scheduler.add_job(
        lambda: run_bot_job(username, password),
        'cron', 
        hour=hour, 
        minute=minute,
        id=job_id
    )
    logger.info(f"Tarea programada para las {time_str} (ID: {job_id})")

def restore_jobs():
    """Restaura todos los trabajos desde la base de datos al iniciar"""
    logger.info("Restaurando trabajos programados desde la base de datos...")
    try:
        schedules = database.get_all_schedules_with_credentials()
        count = 0
        for s in schedules:
            schedule_job(s['time'], s['id'], s['username'], s['password'])
            count += 1
        logger.info(f"✅ Se han restaurado {count} trabajos programados.")
    except Exception as e:
        logger.error(f"❌ Error restaurando trabajos: {e}")

# --- INICIALIZACIÓN ---

# Inicializar DB
database.init_db()

# Iniciar Scheduler
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# Restaurar trabajos existentes
restore_jobs()

# --- DECORADORES ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- RUTAS ---

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Usuario y contraseña requeridos"}), 400
    
    # Guardar/Actualizar usuario en DB (para tener la contraseña persistente)
    database.add_or_update_user(username, password)
    
    # Guardar en sesión
    session['username'] = username
    session['password'] = password
    
    # Reprogramar horarios de este usuario (por si acaso hubo cambios o es un nuevo login)
    user_schedules = database.get_user_schedules(username)
    for schedule in user_schedules:
        schedule_job(schedule["time"], schedule["id"], username, password)
    
    return jsonify({"message": "Login exitoso"})

@app.route('/logout')
def logout():
    session.clear()
    # NOTA: No eliminamos los jobs del scheduler al hacer logout, 
    # porque queremos que sigan corriendo en el servidor.
    return redirect(url_for('login_page'))

@app.route('/')
@login_required
def index():
    user_schedules = database.get_user_schedules(session['username'])
    return render_template('index.html', schedules=user_schedules, username=session.get('username'))

@app.route('/schedules', methods=['GET'])
@login_required
def get_schedules():
    user_schedules = database.get_user_schedules(session['username'])
    return jsonify({"schedules": user_schedules})

@app.route('/schedule', methods=['POST'])
@login_required
def add_schedule():
    data = request.json
    time_str = data.get('time')
    username = session['username']
    password = session['password'] # Usamos la de la sesión, que está sincronizada con DB
    
    if not time_str:
        return jsonify({"error": "Hora inválida"}), 400
    
    user_schedules = database.get_user_schedules(username)
    
    # Verificar duplicados
    if any(s['time'] == time_str for s in user_schedules):
        return jsonify({"error": "Este horario ya está programado"}), 400
    
    # Generar ID único
    schedule_id = f"{username}_schedule_{len(user_schedules)}_{time_str.replace(':', '')}"
    
    # Guardar en DB
    database.add_schedule(schedule_id, username, time_str)
    
    # Programar el job
    schedule_job(time_str, schedule_id, username, password)
    
    return jsonify({
        "message": f"Horario {time_str} agregado",
        "schedule": {"id": schedule_id, "time": time_str}
    })

@app.route('/schedule/<schedule_id>', methods=['DELETE'])
@login_required
def delete_schedule(schedule_id):
    # Eliminar de DB
    database.delete_schedule(schedule_id)
    
    # Eliminar del scheduler
    try:
        scheduler.remove_job(schedule_id)
    except:
        pass
    
    return jsonify({"message": "Horario eliminado"})

@app.route('/run-now', methods=['POST'])
@login_required
def run_now():
    username = session['username']
    password = session['password']
    
    # Ejecutar inmediatamente
    scheduler.add_job(lambda: run_bot_job(username, password))
    return jsonify({"message": "Ejecución iniciada en segundo plano"})

@app.route('/logs')
@login_required
def get_logs():
    if os.path.exists("bot.log"):
        with open("bot.log", "r") as f:
            lines = f.readlines()[-50:]
            return "".join(lines)
    return "No hay logs aún."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
