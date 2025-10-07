# 🤖 Asistente de Telegram con Gemini y LangChain

Este proyecto es un **bot de Telegram inteligente** desarrollado en **Python** que utiliza **Google Gemini AI** como cerebro principal, orquestado por el framework **LangChain**.  
El bot es capaz de manejar conversaciones naturales y utilizar herramientas específicas (*Tools*) para obtener información en tiempo real, como el clima y resultados de cálculos matemáticos.

---

## 🌟 Funcionalidades Clave

Este proyecto cubre las funcionalidades obligatorias del **Bootcamp**, incluyendo los niveles **Básico**, **Intermedio** y **Avanzado**:

| Nivel        | Funcionalidad           | Descripción                                                                 |
|---------------|--------------------------|------------------------------------------------------------------------------|
| **Básico**    | Conversación Inteligente | Integración con **Gemini 2.5 Flash** (vía LangChain) para responder preguntas complejas. |
| **Básico**    | Comandos Estáticos       | `/start`, `/help`, `/fecha` (Fecha y hora actual).                          |
| **Intermedio**| LangChain Tools          | Implementación de dos *Tools* personalizadas: **Clima** y **Calculadora**.  |
| **Avanzado**  | LangChain Agent          | El bot usa un **Agente (Agent)** que decide automáticamente qué *Tool* usar (o si responder con Gemini) basándose en la intención del usuario. |

---

## 🛠️ Tecnologías Utilizadas

- **Lenguaje:** Python 3.10+
- **Framework de IA:** LangChain  
- **Modelo de Lenguaje:** `langchain-google-genai` (Gemini 2.5 Flash)  
- **API del Bot:** `python-telegram-bot` (v20.x)  
- **APIs Externas:** OpenWeatherMap (para la *Tool* de Clima)  
- **Gestión de Entorno:** `python-dotenv`

---

## 🚀 Guía de Instalación y Configuración

Sigue estos pasos para poner el bot en funcionamiento en tu máquina local.

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Saraileiva/Kodigo-chatbot.git
cd Kodigo-chatbot


### 2. Configuración del entorno virtual

# Crear el entorno virtual (usando python3.12 según tu sistema)
python3.12 -m venv bot_env 

# Activar el entorno virtual
source bot_env/bin/activate

### 3. Instalación de dependencias

Con el entorno activado, instala todas las librerías necesarias:

pip install python-telegram-bot==20.7 langchain langchain-google-genai python-dotenv requests pytz

### 4. Obtener y Configurar API Keys

El bot requiere tres claves de acceso para funcionar correctamente:
	•	TELEGRAM_BOT_TOKEN: Obtenido al crear tu bot con @BotFather en Telegram.
	•	GEMINI_API_KEY: Obtenido desde Google AI Studio (necesaria para el Agente).
	•	WEATHER_API_KEY: Obtenido desde OpenWeatherMap (necesaria para la Tool de Clima).

Crea un archivo llamado .env en la raíz del proyecto y agrega tus claves:

TELEGRAM_BOT_TOKEN="pega_aqui_tu_token_de_telegram"
GEMINI_API_KEY="pega_aqui_tu_clave_de_gemini"
WEATHER_API_KEY="pega_aqui_tu_clave_de_open_weathermap"

### 5. Ejecución del Bot

Asegúrate de que el entorno virtual esté activo y ejecuta el script principal:
python bot.py

Estructura del Proyecto

El proyecto sigue una estructura simple y funcional, ideal para el desarrollo rápido:

/
├── .env                  # Claves secretas (IGNORADO por Git)
├── .gitignore            # Archivo para ignorar dependencias y claves
├── bot.py                # Contiene toda la lógica del bot, handlers y el Agente/Tools
├── requirements.txt      # Lista de dependencias del proyecto
└── README.md             # Este archivo