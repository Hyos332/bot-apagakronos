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

def load_schedules():
    """Carga todos los horarios programados"""
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r') as f:
                data = json.load(f)
                schedules = data.get("schedules", [])
                # NO programar aquí, se programará después del login
                return schedules
        except Exception as e:
            logger.error(f"Error cargando horarios: {e}")
    return []

def save_schedules(schedules):
    """Guarda todos los horarios"""
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump({"schedules": schedules}, f)

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
    
    # Cargar y reprogramar horarios con las nuevas credenciales
    schedules = load_schedules()
    for schedule in schedules:
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
    schedules = load_schedules()
    return render_template('index.html', schedules=schedules, username=session.get('username'))

@app.route('/schedules', methods=['GET'])
@login_required
def get_schedules():
    schedules = load_schedules()
    return jsonify({"schedules": schedules})

@app.route('/schedule', methods=['POST'])
@login_required
def add_schedule():
    data = request.json
    time_str = data.get('time')
    
    if not time_str:
        return jsonify({"error": "Hora inválida"}), 400
    
    schedules = load_schedules()
    
    # Verificar si ya existe ese horario
    if any(s['time'] == time_str for s in schedules):
        return jsonify({"error": "Este horario ya está programado"}), 400
    
    # Generar ID único
    schedule_id = f"schedule_{len(schedules)}_{time_str.replace(':', '')}"
    
    # Agregar a la lista
    new_schedule = {"id": schedule_id, "time": time_str}
    schedules.append(new_schedule)
    
    # Programar el job con credenciales de la sesión
    schedule_job(time_str, schedule_id, session['username'], session['password'])
    
    # Guardar en archivo
    save_schedules(schedules)
    
    return jsonify({
        "message": f"Horario {time_str} agregado",
        "schedule": new_schedule
    })

@app.route('/schedule/<schedule_id>', methods=['DELETE'])
@login_required
def delete_schedule(schedule_id):
    schedules = load_schedules()
    
    # Buscar y eliminar de la lista
    schedules = [s for s in schedules if s['id'] != schedule_id]
    
    # Eliminar el job del scheduler
    try:
        scheduler.remove_job(schedule_id)
    except:
        pass
    
    # Guardar cambios
    save_schedules(schedules)
    
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
