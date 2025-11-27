# ⏳ Kronos Automator - Panel de Control

Sistema automatizado con interfaz web para gestionar el registro de salida en Kronos.

## 🌟 Características

*   **Panel Web Moderno**: Interfaz oscura y fácil de usar.
*   **Programación Flexible**: Elige la hora de salida y el bot se ejecutará automáticamente.
*   **Ejecución Manual**: Botón de pánico para detener el tiempo "Ahora mismo".
*   **Logs en Vivo**: Visualiza qué está haciendo el bot desde el navegador.
*   **Dockerizado**: Fácil de desplegar y mantener.

## 🚀 Instalación y Uso (Docker)

Esta es la forma recomendada de usarlo.

1.  **Configura tus credenciales**:
    Asegúrate de tener el archivo `.env` con tus datos:
    ```env
    KRONOS_USER=tu_usuario
    KRONOS_PASSWORD=tu_password
    ```

2.  **Levanta el servicio**:
    ```bash
    docker-compose up -d --build
    ```

3.  **Accede al Panel**:
    Abre tu navegador y ve a: [http://localhost:5000](http://localhost:5000)

4.  **Configura la Hora**:
    Selecciona la hora a la que quieres que se detenga el cronómetro y dale a "Guardar".

## 🛠️ Instalación Manual (Sin Docker)

Si prefieres correrlo localmente en tu máquina:

1.  Crea el entorno virtual: `python3 -m venv venv`
2.  Instala dependencias: `./venv/bin/pip install -r requirements.txt`
3.  Ejecuta el servidor:
    ```bash
    export PYTHONPATH=$PYTHONPATH:$(pwd)/app
    ./venv/bin/python app/web.py
    ```
4.  Entra a `http://localhost:5000`.

## ⚠️ Notas Importantes

*   **Selectores**: Si la página de Kronos cambia, debes actualizar `app/bot.py` con los nuevos XPATH/ID.
*   **Persistencia**: El horario y los logs se guardan en archivos locales (`schedule.json`, `bot.log`) que están mapeados como volúmenes en Docker, así que no se pierden al reiniciar.
