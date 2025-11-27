import os
import time
import logging
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

class KronosBot:
    def __init__(self):
        # Cargar variables de entorno
        load_dotenv()
        
        self.url = "https://kronos.ctdesarrollo-sdr.org/mi-tiempo-hoy"
        self.username = os.getenv("KRONOS_USER")
        self.password = os.getenv("KRONOS_PASSWORD")
        
        # --- CONFIGURACIÓN DE SELECTORES ---
        self.selectors = {
            "login_user_input": (By.ID, "username"), 
            "login_pass_input": (By.ID, "password"),
            "login_submit_btn": (By.XPATH, "//button[@type='submit']"),
            "stop_button": (By.XPATH, "//button[contains(@class, 'btn-stop') or contains(text(), 'Detener')]") 
        }

        self.driver = None

    def setup_driver(self):
        """Configura e inicia el navegador Chrome."""
        logging.info("Configurando navegador...")
        chrome_options = Options()
        
        # En Docker es OBLIGATORIO usar headless y no-sandbox
        chrome_options.add_argument("--headless") 
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-infobars")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info("Navegador iniciado correctamente.")

    def login(self):
        """Maneja el inicio de sesión."""
        logging.info("Verificando necesidad de login...")
        
        if self.username and self.password:
            try:
                logging.info("Intentando login automático...")
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(self.selectors["login_user_input"])
                ).send_keys(self.username)
                
                self.driver.find_element(*self.selectors["login_pass_input"]).send_keys(self.password)
                self.driver.find_element(*self.selectors["login_submit_btn"]).click()
                
                logging.info("Credenciales enviadas.")
            except Exception as e:
                logging.warning(f"Login automático falló o no fue necesario: {e}")
        else:
            logging.info("No hay credenciales. En modo Headless (Docker) esto fallará si la sesión no es persistente.")

    def stop_timer(self):
        """Espera y hace clic en el botón de detener tiempo."""
        try:
            logging.info("Buscando botón de detener tiempo...")
            button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable(self.selectors["stop_button"])
            )
            logging.info(f"Botón encontrado: {button.text}")
            button.click()
            logging.info("✅ ¡ÉXITO! Se ha hecho clic en el botón de detener.")
            time.sleep(5)
        except Exception as e:
            logging.error(f"❌ ERROR: No se pudo encontrar el botón: {e}")
            # Guardar captura de pantalla para debug en Docker
            self.driver.save_screenshot("error_screenshot.png")
            raise e

    def run(self):
        """Ejecuta el flujo completo."""
        try:
            self.setup_driver()
            self.driver.get(self.url)
            self.login()
            self.stop_timer()
            return True, "Tarea completada con éxito"
        except Exception as e:
            return False, str(e)
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    bot = KronosBot()
    bot.run()
