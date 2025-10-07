import os
import requests
import datetime
import pytz
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentType, Tool, initialize_agent

import html  # Para escapar caracteres especiales en HTML
# ==============================================================================
# 1. SETUP INICIAL Y CARGA DE VARIABLES DE ENTORNO
# ==============================================================================
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY") 

if not TELEGRAM_BOT_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN no configurada.")
if not GEMINI_API_KEY:
    print("ADVERTENCIA: GEMINI_API_KEY no encontrada. El bot solo responderá a comandos estáticos.")
if not WEATHER_API_KEY:
    print("ADVERTENCIA: WEATHER_API_KEY no encontrada. La herramienta de Clima no funcionará.")


# ==============================================================================
# 2. DEFINICIÓN DE TOOLS PARA LANGCHAIN
# ==============================================================================

# --- Tool 1: Clima ---
def obtener_clima_tool(ciudad: str) -> str:
    """Útil para responder preguntas sobre el clima y la temperatura actual en cualquier ciudad. Usar el formato 'Ciudad, Código de País', ej. 'Paris, FR'."""
    if not WEATHER_API_KEY:
        return "ERROR: La clave de OpenWeatherMap no está configurada."
        
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={WEATHER_API_KEY}&units=metric&lang=es"
        response = requests.get(url)
        data = response.json()

        if data.get("cod") != 200:
            return f"Error al obtener el clima: {data.get('message', 'Ciudad no encontrada.')}"

        temperatura = data['main']['temp']
        sensacion = data['main']['feels_like']
        descripcion = data['weather'][0]['description']
        humedad = data['main']['humidity']
        
        return (
            f"El clima en **{ciudad}** es:\n"
            f"🌡️ **Temperatura:** {temperatura}°C (Se siente {sensacion}°C)\n"
            f"☁️ **Condición:** {descripcion.capitalize()}\n"
            f"💧 **Humedad:** {humedad}%"
        )
    except Exception as e:
        return f"Ocurrió un error al procesar la solicitud de clima: {e}"

# --- Tool 2: Calculadora (Nivel Intermedio) ---
def calculator_tool(expression: str) -> str:
    """Evalúa una expresión matemática y devuelve el resultado. Útil para cálculos complejos, ej: '5 * (10 + 2)'."""
    try:
        # Nota: Usar eval() es riesgoso en producción, pero es práctico para este ejercicio de bootcamp.
        result = eval(expression)
        return str(result)
    except Exception:
        return "Error: No pude calcular la expresión matemática proporcionada."


# ==============================================================================
# 3. INICIALIZACIÓN DE LANGCHAIN AGENT
# ==============================================================================

# Configuración de Tools
tools = [
    Tool(
        name="Clima",
        func=obtener_clima_tool,
        description=obtener_clima_tool.__doc__
    ),
    Tool(
        name="Calculadora",
        func=calculator_tool,
        description=calculator_tool.__doc__
    )
]

# Inicialización del Agente Gemini
agent = None
if GEMINI_API_KEY:
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.2)
    
    # Inicialización del agente que decidirá qué Tool usar
    try:
        agent = initialize_agent(
            tools, 
            llm, 
            # AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION es ideal para funciones con argumentos
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, 
            verbose=True, # Muestra el proceso de pensamiento del agente en la consola
            handle_parsing_errors=True,
            max_iterations=5 # Evita loops infinitos
        )
    except Exception as e:
        print(f"Error al inicializar el agente LangChain: {e}")
else:
    print("ADVERTENCIA: Agente Gemini NO inicializado por falta de clave.")


# ==============================================================================
# 4. HANDLERS DE COMANDOS ESTÁTICOS DE TELEGRAM
# ==============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /start con un mensaje de bienvenida."""
    welcome_message = (
        "🤖 **¡Hola! Soy tu Asistente Inteligente impulsado por Gemini y LangChain.**\n\n"
        "Puedo:\n"
        "🧠 Responder preguntas complejas.\n"
        "🌡️ Darte el **clima** actual (ej: *¿Qué tiempo hace en Tokyo, JP?*).\n"
        "➕ Resolver **cálculos** (ej: *¿Cuánto es 500 por 1.15?*).\n\n"
        "Escribe **/help** para ver todos los comandos disponibles."
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /help con una lista de funcionalidades."""
    help_message = (
        "📋 **Lista de Comandos:**\n\n"
        "**/start** - Mensaje de bienvenida.\n"
        "**/help** - Muestra esta lista de comandos.\n"
        "**/fecha** - Muestra la fecha y hora actual.\n"
        "Cualquier otra pregunta será respondida por la IA."
    )
    await update.message.reply_text(help_message, parse_mode='Markdown')

async def fecha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /fecha mostrando la fecha y hora local."""
    # Usamos una zona horaria común, puedes cambiarla a 'America/El_Salvador'
    timezone = pytz.timezone('America/New_York') 
    now = datetime.datetime.now(timezone)
    
    fecha_format = now.strftime('%A, %d de %B de %Y')
    hora_format = now.strftime('%H:%M:%S')
    
    response_text = (
        f"📅 **Fecha y Hora Actual**\n"
        f"Fecha: {fecha_format}\n"
        f"Hora: {hora_format} (Zona: {timezone})"
    )
    await update.message.reply_text(response_text, parse_mode='Markdown')


# ==============================================================================
# 5. HANDLER PRINCIPAL DE MENSAJES (LANGCHAIN AGENT)
# ==============================================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía el mensaje del usuario al agente Gemini para procesar."""
    if not agent:
        await update.message.reply_text("Lo siento, la IA no está activa. Revisa tu GEMINI_API_KEY.")
        return

    user_text = update.message.text
    
    # 📝 Indicar que el bot está escribiendo (UX)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # El agente procesa el mensaje, decide si usa una Tool o responde directamente
        response = agent.invoke({"input": user_text})

        agent_output = response["output"]

        # 1. Escapar el texto: Convierte caracteres especiales a entidades HTML
        # Esto asegura que caracteres como <, >, & y * sean tratados como texto.
        clean_output = html.escape(agent_output)

        # 2. Reemplazar caracteres Markdown V2 que pueden causar problemas.
        # Esto es un refuerzo si el escape no fue suficiente.
        # Reemplazamos los asteriscos * (que causaban el error) por algo inocuo.
        clean_output = clean_output.replace('\\*', '*') 
        clean_output = clean_output.replace('*', '') # Elimina asteriscos restantes si es necesario
        

        # Enviar la respuesta del agente (ya sea de Gemini o de una Tool)
        await update.message.reply_text(response["output"], parse_mode='HTML')
        
    except Exception as e:
        print(f"Error al invocar al agente LangChain: {e}")
        await update.message.reply_text("Lo siento, hubo un error interno al procesar tu solicitud con la IA. Intenta de nuevo.")


# ==============================================================================
# 6. FUNCIÓN MAIN Y EJECUCIÓN
# ==============================================================================

def main() -> None:
    """Inicia el bot de Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        print("La aplicación no puede iniciar por falta de TELEGRAM_BOT_TOKEN.")
        return
        
    # Crear la aplicación y pasarle el token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Añadir handlers para comandos estáticos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("fecha", fecha))
    
    # Manejar cualquier otro mensaje de texto con el agente (Nivel Avanzado)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Iniciar el bot
    print("El bot se está ejecutando... Presiona Ctrl+C para detenerlo.")
    # El polling es el método que usa el bot para preguntar a Telegram por nuevos mensajes
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()