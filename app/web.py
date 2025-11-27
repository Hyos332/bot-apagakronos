from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import json
import os
from bot import KronosBot
import atexit

app = Flask(__name__)

# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Archivo para persistencia simple
SCHEDULE_FILE = "schedule.json"

scheduler = BackgroundScheduler()
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

def run_bot_job():
    logger.info("⏰ Ejecutando tarea programada...")
    bot = KronosBot()
    success, message = bot.run()
    logger.info(f"Resultado de la tarea: {success} - {message}")

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            data = json.load(f)
            time_str = data.get("time")
            if time_str:
                schedule_job(time_str)
                return time_str
    return None

def schedule_job(time_str):
    # time_str formato "HH:MM"
    hour, minute = map(int, time_str.split(':'))
    
    # Limpiar trabajos anteriores
    scheduler.remove_all_jobs()
    
    # Programar nuevo trabajo
    scheduler.add_job(run_bot_job, 'cron', hour=hour, minute=minute)
    logger.info(f"Tarea programada para las {time_str}")

# Cargar horario al inicio
current_schedule = load_schedule()

@app.route('/')
def index():
    return render_template('index.html', schedule=current_schedule)

@app.route('/schedule', methods=['POST'])
def update_schedule():
    global current_schedule
    data = request.json
    time_str = data.get('time')
    
    if not time_str:
        return jsonify({"error": "Hora inválida"}), 400
        
    schedule_job(time_str)
    current_schedule = time_str
    
    # Guardar en archivo
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump({"time": time_str}, f)
        
    return jsonify({"message": f"Programado para las {time_str}", "time": time_str})

@app.route('/run-now', methods=['POST'])
def run_now():
    # Ejecutar en segundo plano para no bloquear
    scheduler.add_job(run_bot_job)
    return jsonify({"message": "Ejecución iniciada en segundo plano"})

@app.route('/logs')
def get_logs():
    if os.path.exists("bot.log"):
        with open("bot.log", "r") as f:
            # Leer las últimas 50 líneas
            lines = f.readlines()[-50:]
            return "".join(lines)
    return "No hay logs aún."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
