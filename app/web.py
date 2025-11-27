from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
import logging
import json
import os
from bot import KronosBot
import atexit

app = Flask(__name__)

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

def run_bot_job():
    logger.info("⏰ Ejecutando tarea programada...")
    bot = KronosBot()
    success, message = bot.run()
    logger.info(f"Resultado de la tarea: {success} - {message}")

def load_schedules():
    """Carga todos los horarios programados"""
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r') as f:
                data = json.load(f)
                schedules = data.get("schedules", [])
                # Programar cada horario
                for schedule in schedules:
                    schedule_job(schedule["time"], schedule["id"])
                return schedules
        except Exception as e:
            logger.error(f"Error cargando horarios: {e}")
    return []

def save_schedules(schedules):
    """Guarda todos los horarios"""
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump({"schedules": schedules}, f)

def schedule_job(time_str, job_id):
    """Programa un trabajo con un ID específico"""
    hour, minute = map(int, time_str.split(':'))
    
    # Verificar si ya existe un job con ese ID
    existing_job = scheduler.get_job(job_id)
    if existing_job:
        scheduler.remove_job(job_id)
    
    # Programar nuevo trabajo
    scheduler.add_job(
        run_bot_job, 
        'cron', 
        hour=hour, 
        minute=minute,
        id=job_id
    )
    logger.info(f"Tarea programada para las {time_str} (ID: {job_id})")

# Cargar horarios al inicio
current_schedules = load_schedules()

@app.route('/')
def index():
    return render_template('index.html', schedules=current_schedules)

@app.route('/schedules', methods=['GET'])
def get_schedules():
    return jsonify({"schedules": current_schedules})

@app.route('/schedule', methods=['POST'])
def add_schedule():
    global current_schedules
    data = request.json
    time_str = data.get('time')
    
    if not time_str:
        return jsonify({"error": "Hora inválida"}), 400
    
    # Verificar si ya existe ese horario
    if any(s['time'] == time_str for s in current_schedules):
        return jsonify({"error": "Este horario ya está programado"}), 400
    
    # Generar ID único
    schedule_id = f"schedule_{len(current_schedules)}_{time_str.replace(':', '')}"
    
    # Agregar a la lista
    new_schedule = {"id": schedule_id, "time": time_str}
    current_schedules.append(new_schedule)
    
    # Programar el job
    schedule_job(time_str, schedule_id)
    
    # Guardar en archivo
    save_schedules(current_schedules)
    
    return jsonify({
        "message": f"Horario {time_str} agregado",
        "schedule": new_schedule
    })

@app.route('/schedule/<schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    global current_schedules
    
    # Buscar y eliminar de la lista
    current_schedules = [s for s in current_schedules if s['id'] != schedule_id]
    
    # Eliminar el job del scheduler
    try:
        scheduler.remove_job(schedule_id)
    except:
        pass
    
    # Guardar cambios
    save_schedules(current_schedules)
    
    return jsonify({"message": "Horario eliminado"})

@app.route('/run-now', methods=['POST'])
def run_now():
    scheduler.add_job(run_bot_job)
    return jsonify({"message": "Ejecución iniciada en segundo plano"})

@app.route('/logs')
def get_logs():
    if os.path.exists("bot.log"):
        with open("bot.log", "r") as f:
            lines = f.readlines()[-50:]
            return "".join(lines)
    return "No hay logs aún."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
