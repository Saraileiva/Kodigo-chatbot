import os
import requests
import datetime
import pytz
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentType, Tool, initialize_agent
import locale  # <-- ¡NUEVA IMPORTACIÓN!
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

PORT = int(os.environ.get('PORT', '8080')) # Puerto estándar de Render
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL') # URL pública que Render proporciona

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


# Reusa la función de la Tool (que debe estar definida en la sección 2)
# from . import obtener_clima_tool # Si estuviera en otro archivo

async def clima_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /clima [ciudad]."""
    
    # 1. Extraer la ciudad de los argumentos (ej: /clima San Salvador)
    if not context.args:
        await update.message.reply_text("Por favor, especifica una ciudad. Ejemplo: /clima Tokio")
        return
    
    ciudad_query = " ".join(context.args)
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # 2. Llamar directamente a la función que usa la API (la misma que usa la Tool)
    try:
        resultado_clima = obtener_clima_tool(ciudad_query)
        
        # 3. Enviar el resultado. Usamos HTML por si la función devuelve emojis o Markdown.
        await update.message.reply_text(resultado_clima, parse_mode='HTML')
        
    except Exception as e:
        print(f"Error en el comando /clima: {e}")
        await update.message.reply_text("Lo siento, no pude obtener el clima para esa ciudad.")

async def saludo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /saludo [nombre]."""
    
    if not context.args:
        # Si el usuario solo escribe /saludo, usamos su nombre de usuario
        nombre = update.message.from_user.first_name or "Usuario"
    else:
        # Si el usuario escribe /saludo Sarahy, usamos Sarahy
        nombre = " ".join(context.args)
        
    response_text = f"👋 ¡Hola, {nombre}! Es un placer saludarte. ¿En qué puedo ayudarte hoy?"
    await update.message.reply_text(response_text)



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
        "**/clima [ciudad]** - Información meteorológica de una ciudad específica.\n" # <-- ¡Añadido!
        "**/saludo [nombre]** - Un comando personalizado para saludar.\n\n" # <-- ¡Añadido!
        "Cualquier otra pregunta será respondida por la IA y sus herramientas (Clima/Calculadora)."
    )
    await update.message.reply_text(help_message, parse_mode='Markdown')


async def fecha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /fecha mostrando la fecha y hora local."""
    
    # Usamos una zona horaria común (por ejemplo, hora local en El Salvador)
    timezone = pytz.timezone('America/El_Salvador') 
    now = datetime.datetime.now(timezone)
    
    # ⚠️ Nota: Para que los días y meses salgan en español (ej: martes, octubre), 
    # necesitas tener la configuración de 'locale' en tu script.
    
    fecha_format = now.strftime('%A, %d de %B de %Y')
    hora_format = now.strftime('%H:%M:%S')
    
    response_text = (
        f"📅 <b>Fecha y Hora Actual</b>\n" # Usamos <b> para HTML
        f"Fecha: {fecha_format}\n"
        f"Hora: {hora_format} (Zona: {timezone})"
    )
    # 🚨 CAMBIO CLAVE AQUÍ: Usamos parse_mode='HTML' para evitar errores del parser.
    await update.message.reply_text(response_text, parse_mode='HTML')

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
        clean_output = agent_output.replace('**', '<b>').replace('<b>', '</b>', 1) 
        clean_output = html.escape(agent_output)

        # Enviar la respuesta del agente (ya sea de Gemini o de una Tool)
        await update.message.reply_text(clean_output, parse_mode='HTML')
        
    except Exception as e:
        print(f"Error al invocar al agente LangChain: {e}")
        await update.message.reply_text("Lo siento, hubo un error interno al procesar tu solicitud con la IA. Intenta de nuevo.")


# ==============================================================================
# 6. FUNCIÓN MAIN Y EJECUCIÓN
# ==============================================================================

def main() -> None:
    """Inicia el bot de Telegram."""

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    RENDER_URL = os.getenv("RENDER_URL")  # Ej: "https://tu-app.onrender.com/"
    PORT = int(os.getenv("PORT", "8080"))

    # Verificación de token
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: No se encontró TELEGRAM_BOT_TOKEN. Configúralo en tu entorno.")
        return

    # Crear aplicación
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Agregar comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("fecha", fecha))
    application.add_handler(CommandHandler("clima", clima_command))
    application.add_handler(CommandHandler("saludo", saludo_command))

    # Manejar mensajes de texto
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Detectar entorno (Render o local)
    if os.getenv("PORT"):  # Render usa PORT
        if not RENDER_URL:
            print("🚨 ERROR: Falta la variable RENDER_URL. Configúrala en Render Dashboard.")
            return

        print(f"🚀 Iniciando bot con Webhook en Render ({RENDER_URL})...")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_BOT_TOKEN,
            webhook_url=f"{RENDER_URL}{TELEGRAM_BOT_TOKEN}"
        )
    else:
        print("🧩 Ejecutando bot localmente con Polling... (Ctrl+C para detener)")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()