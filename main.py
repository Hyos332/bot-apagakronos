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
        # IMPORTANTE: Debes actualizar estos selectores con los valores reales de la página.
        # Usa Inspeccionar Elemento en tu navegador para encontrarlos.
        self.selectors = {
            # Selectores de Login (si se va a automatizar el login)
            "login_user_input": (By.ID, "username"),  # Ejemplo: cambiar "username" por el ID real
            "login_pass_input": (By.ID, "password"),  # Ejemplo: cambiar "password" por el ID real
            "login_submit_btn": (By.XPATH, "//button[@type='submit']"),
            
            # Selector del botón de APAGAR/DETENER
            # Busca un botón que contenga texto como "Detener", "Salida", "Stop", etc.
            # Ejemplo XPATH: "//button[contains(text(), 'Detener')]"
            "stop_button": (By.XPATH, "//button[contains(@class, 'btn-stop') or contains(text(), 'Detener')]") 
        }

        self.driver = None

    def setup_driver(self):
        """Configura e inicia el navegador Chrome."""
        logging.info("Configurando navegador...")
        chrome_options = Options()
        # chrome_options.add_argument("--headless") # Descomentar para ejecutar sin ventana visible
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-infobars")
        
        # Mantiene el navegador abierto si el script termina (opcional, útil para depurar)
        chrome_options.add_experimental_option("detach", True)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info("Navegador iniciado correctamente.")

    def login(self):
        """Maneja el inicio de sesión."""
        logging.info("Verificando necesidad de login...")
        
        # Si tenemos credenciales en el .env, intentamos usarlas
        if self.username and self.password:
            try:
                logging.info("Intentando login automático con credenciales proporcionadas...")
                
                # Esperar a que aparezca el campo de usuario
                user_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(self.selectors["login_user_input"])
                )
                pass_field = self.driver.find_element(*self.selectors["login_pass_input"])
                submit_btn = self.driver.find_element(*self.selectors["login_submit_btn"])

                user_field.clear()
                user_field.send_keys(self.username)
                pass_field.clear()
                pass_field.send_keys(self.password)
                submit_btn.click()
                
                logging.info("Credenciales enviadas.")
            except Exception as e:
                logging.warning(f"No se pudo realizar el login automático (quizás ya estás logueado o los selectores están mal): {e}")
        else:
            logging.info("No se detectaron credenciales en .env. Esperando login manual...")

    def stop_timer(self):
        """Espera y hace clic en el botón de detener tiempo."""
        try:
            logging.info("Buscando botón de detener tiempo...")
            
            # Esperamos hasta 60 segundos para que el usuario se loguee manualmente (si es necesario)
            # y la página cargue el botón.
            button = WebDriverWait(self.driver, 60).until(
                EC.element_to_be_clickable(self.selectors["stop_button"])
            )
            
            # Opcional: Verificar texto del botón antes de clicar para asegurar
            logging.info(f"Botón encontrado: {button.text}")
            
            button.click()
            logging.info("✅ ¡ÉXITO! Se ha hecho clic en el botón de detener.")
            
            # Esperar un poco para asegurar que la acción se procese
            time.sleep(5)
            
        except Exception as e:
            logging.error(f"❌ ERROR: No se pudo encontrar o hacer clic en el botón. Detalles: {e}")
            logging.info("Sugerencia: Revisa los selectores en la configuración del script.")

    def run(self):
        """Ejecuta el flujo completo."""
        try:
            self.setup_driver()
            self.driver.get(self.url)
            
            self.login()
            
            self.stop_timer()
            
        except Exception as e:
            logging.error(f"Error crítico en la ejecución: {e}")
        finally:
            if self.driver:
                logging.info("Cerrando navegador...")
                self.driver.quit()

if __name__ == "__main__":
    bot = KronosBot()
    bot.run()
