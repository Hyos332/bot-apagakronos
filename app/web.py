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

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Clave secreta para sesiones

# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Archivo para persistencia
SCHEDULE_FILE = "schedule.json"

# Zona horaria de España
TIMEZONE = timezone('Europe/Madrid')

scheduler = BackgroundScheduler(timezone=TIMEZONE)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# Decorator para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def run_bot_job(username, password):
    """Ejecuta el bot con las credenciales de la sesión"""
    logger.info(f"⏰ Ejecutando tarea programada para usuario: {username}...")
    bot = KronosBot()
    # Sobrescribir credenciales con las de la sesión
    bot.username = username
    bot.password = password
    success, message = bot.run()
    logger.info(f"Resultado de la tarea: {success} - {message}")

def load_schedules(username=None):
    """Carga los horarios programados (opcionalmente filtrados por usuario)"""
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r') as f:
                data = json.load(f)
                all_schedules = data.get("schedules", {})
                
                if username:
                    # Retornar solo los horarios de este usuario
                    return all_schedules.get(username, [])
                else:
                    # Retornar todos (para migración)
                    return all_schedules
        except Exception as e:
            logger.error(f"Error cargando horarios: {e}")
    return [] if username else {}

def save_schedules(username, user_schedules):
    """Guarda los horarios de un usuario específico"""
    # Cargar todos los horarios
    all_schedules = load_schedules()
    
    # Si all_schedules es una lista (formato antiguo), convertir a dict
    if isinstance(all_schedules, list):
        all_schedules = {}
    
    # Actualizar los horarios de este usuario
    all_schedules[username] = user_schedules
    
    # Guardar todo
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump({"schedules": all_schedules}, f)

def schedule_job(time_str, job_id, username, password):
    """Programa un trabajo con credenciales específicas"""
    hour, minute = map(int, time_str.split(':'))
    
    # Verificar si ya existe un job con ese ID
    existing_job = scheduler.get_job(job_id)
    if existing_job:
        scheduler.remove_job(job_id)
    
    # Programar nuevo trabajo con las credenciales
    scheduler.add_job(
        lambda: run_bot_job(username, password),
        'cron', 
        hour=hour, 
        minute=minute,
        id=job_id
    )
    logger.info(f"Tarea programada para las {time_str} (ID: {job_id})")

# Rutas de autenticación
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
    
    # Guardar en sesión
    session['username'] = username
    session['password'] = password
    
    # Cargar y reprogramar horarios de este usuario
    user_schedules = load_schedules(username)
    for schedule in user_schedules:
        schedule_job(schedule["time"], schedule["id"], username, password)
    
    return jsonify({"message": "Login exitoso"})

@app.route('/logout')
def logout():
    session.clear()
    # Limpiar todos los jobs programados
    scheduler.remove_all_jobs()
    return redirect(url_for('login_page'))

# Rutas principales (requieren login)
@app.route('/')
@login_required
def index():
    user_schedules = load_schedules(session['username'])
    return render_template('index.html', schedules=user_schedules, username=session.get('username'))

@app.route('/schedules', methods=['GET'])
@login_required
def get_schedules():
    user_schedules = load_schedules(session['username'])
    return jsonify({"schedules": user_schedules})

@app.route('/schedule', methods=['POST'])
@login_required
def add_schedule():
    data = request.json
    time_str = data.get('time')
    username = session['username']
    
    if not time_str:
        return jsonify({"error": "Hora inválida"}), 400
    
    user_schedules = load_schedules(username)
    
    # Verificar si ya existe ese horario para este usuario
    if any(s['time'] == time_str for s in user_schedules):
        return jsonify({"error": "Este horario ya está programado"}), 400
    
    # Generar ID único con el username
    schedule_id = f"{username}_schedule_{len(user_schedules)}_{time_str.replace(':', '')}"
    
    # Agregar a la lista del usuario
    new_schedule = {"id": schedule_id, "time": time_str}
    user_schedules.append(new_schedule)
    
    # Programar el job con credenciales de la sesión
    schedule_job(time_str, schedule_id, username, session['password'])
    
    # Guardar en archivo
    save_schedules(username, user_schedules)
    
    return jsonify({
        "message": f"Horario {time_str} agregado",
        "schedule": new_schedule
    })

@app.route('/schedule/<schedule_id>', methods=['DELETE'])
@login_required
def delete_schedule(schedule_id):
    username = session['username']
    user_schedules = load_schedules(username)
    
    # Buscar y eliminar de la lista del usuario
    user_schedules = [s for s in user_schedules if s['id'] != schedule_id]
    
    # Eliminar el job del scheduler
    try:
        scheduler.remove_job(schedule_id)
    except:
        pass
    
    # Guardar cambios
    save_schedules(username, user_schedules)
    
    return jsonify({"message": "Horario eliminado"})

@app.route('/run-now', methods=['POST'])
@login_required
def run_now():
    # Capturar credenciales ANTES de pasar al scheduler
    username = session['username']
    password = session['password']
    
    # Ejecutar inmediatamente con credenciales capturadas
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
