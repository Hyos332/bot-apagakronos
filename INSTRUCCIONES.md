# 🤖 Bot Apaga-Kronos

Este script automatiza el proceso de detener el registro de tiempo en Kronos.

## 📋 Requisitos Previos

1.  Tener **Python** instalado (versión 3.7 o superior).
2.  Tener **Google Chrome** instalado.

## 🚀 Instalación

1.  Abre una terminal en la carpeta del proyecto.
2.  Crea un entorno virtual y actívalo (recomendado para evitar conflictos):
    ```bash
    python3 -m venv venv
    ```
3.  Instala las dependencias necesarias ejecutando:
    ```bash
    ./venv/bin/pip install -r requirements.txt
    ```
4.  Configura tus credenciales (Opcional):
    *   Crea una copia del archivo `.env.example` y llámalo `.env` (si no lo has hecho ya).
    *   Edita `.env` y pon tu usuario y contraseña si deseas login automático.

## ⚙️ Configuración Crítica (Selectores)

Dado que no tengo acceso al código fuente de la página de Kronos, **necesitas identificar el botón de "Detener" tú mismo** y actualizar el script.

1.  Abre Chrome y entra a [https://kronos.ctdesarrollo-sdr.org/mi-tiempo-hoy](https://kronos.ctdesarrollo-sdr.org/mi-tiempo-hoy).
2.  Haz clic derecho sobre el botón que usas para detener el tiempo y selecciona **"Inspeccionar"**.
3.  Se abrirá el panel de desarrollador resaltando el código del botón. Busca atributos como `id`, `class`, o `name`.
4.  Abre el archivo `main.py` y busca la sección `self.selectors`.
5.  Actualiza `stop_button` con la información correcta. También actualiza `login_user_input` y `login_pass_input` si quieres que el login funcione.

    *   **Si tiene ID:**
        ```python
        "stop_button": (By.ID, "id_del_boton")
        ```
    *   **Si tiene una clase única:**
        ```python
        "stop_button": (By.CLASS_NAME, "clase_del_boton")
        ```
    *   **Por texto (XPATH):**
        ```python
        "stop_button": (By.XPATH, "//button[contains(text(), 'Texto Exacto del Botón')]")
        ```

## ▶️ Ejecución Manual

Para probar que funciona:

```bash
./venv/bin/python main.py
```

## ⏰ Programación Automática

### En Windows (Task Scheduler)

1.  Abre el **Programador de Tareas** (Task Scheduler).
2.  "Crear tarea básica...".
3.  Nombre: "Apagar Kronos".
4.  Desencadenador: "Diariamente" -> Configura la hora (ej. 18:00).
5.  Acción: "Iniciar un programa".
6.  Programa/Script: Busca tu ejecutable de `python.exe` (puedes verlo con `where python` en CMD).
    *   Ejemplo: `C:\Users\TuUsuario\AppData\Local\Programs\Python\Python39\python.exe`
7.  Argumentos: Escribe el nombre del script: `main.py`.
8.  **Importante**: En "Iniciar en" (Start in), pon la ruta completa de la carpeta donde está este script.

### En Linux/macOS (Cron)

1.  Abre la terminal y escribe `crontab -e`.
2.  Añade una línea al final para ejecutarlo de lunes a viernes a las 18:00 (ejemplo):
    ```bash
    0 18 * * 1-5 cd /ruta/a/tu/bot-apagakronos && /usr/bin/python3 main.py >> bot.log 2>&1
    ```
    *(Asegúrate de usar la ruta correcta a tu python y a la carpeta del proyecto)*.

## ⚠️ Advertencia de Seguridad

*   **Credenciales**: Nunca compartas tu archivo `.env`. Añádelo a `.gitignore` si usas Git.
*   **Políticas de Empresa**: Asegúrate de que automatizar este proceso no viole las políticas de TI de tu empresa. Este bot simplemente automatiza un clic, pero siempre es mejor preguntar.
