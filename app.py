# -*- coding: utf-8 -*-
"""
Created on Sun May 11 08:45:30 2025

@author: scedermas
"""

import streamlit as st
import google.generativeai as genai # Importar la librería de Gemini
import sqlite3
import pyperclip
import speech_recognition as sr
from audiorecorder import audiorecorder

# ... (otras importaciones que ya tienes como speech_recognition, audiorecorder, etc.)

# --- Configuración de la API Key de Gemini y Modelo (como la tienes) ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError): # Manejar ambos errores si secrets.toml no existe o la key no está.
    GOOGLE_API_KEY = "TU_GOOGLE_API_KEY_AQUI" # Placeholder
    if GOOGLE_API_KEY == "TU_GOOGLE_API_KEY_AQUI":
        st.warning("API Key de Google Gemini no configurada de forma segura. Funcionalidad de IA limitada.")

model_rewrite = None
if GOOGLE_API_KEY and GOOGLE_API_KEY != "TU_GOOGLE_API_KEY_AQUI":
    genai.configure(api_key=GOOGLE_API_KEY)
    # Puedes configurar el modelo aquí con parámetros de generación si lo deseas
    generation_config_rewrite = genai.GenerationConfig(
        temperature=0.7  # Un valor entre 0.0 y 1.0. Más alto = más creativo/diverso.
                         # 0.7 es un buen punto de partida para equilibrio.
    )
    model_rewrite = genai.GenerativeModel(
        model_name='gemini-1.5-flash', # o 'gemini-1.5-pro' para mayor calidad (puede ser más lento/costoso)
        generation_config=generation_config_rewrite
    )
else:
    st.error("La API Key de Google Gemini no está configurada. La función de reescritura estará deshabilitada.")

def rewrite_text_cordial_gemini(text_to_rewrite):
    if not model_rewrite:
        return "Error: Modelo Gemini para reescritura no inicializado (revisa la API Key)."
    
    # Nuevo prompt más detallado
    prompt = f"""
    Tu tarea es reescribir la 'Frase original' en español. La 'Frase reescrita' debe ser:
    1.  **Cordial y Profesional:** Mantén un tono amable y adecuado para la comunicación con clientes.
    2.  **Clara y Comprensible:** El mensaje debe ser fácil de entender, sin ambigüedades.
    3.  **Natural y Fluida:** El texto debe sonar natural, no robótico. Evita la concisión extrema si esto sacrifica la naturalidad o la completitud del mensaje. Busca una expresión bien conectada y agradable de leer.
    4.  **Gramaticalmente Impecable:** Presta especial atención al uso correcto y completo de:
        * Signos de puntuación (comas, puntos, signos de interrogación, exclamación, etc.).
        * Mayúsculas y minúsculas según las normas del español.
        * Todos los acentos (tildes) necesarios.
    5.  **Foco en la Reescritura:** Entrega únicamente la frase reescrita. No añadas introducciones, comentarios sobre tu proceso, ni despedidas.

    Frase original: "{text_to_rewrite}"
    Frase reescrita:
    """
    
    try:
        response = model_rewrite.generate_content(prompt)
        # A veces Gemini puede añadir Markdown para negritas si el prompt es muy estructurado.
        # Si ves "**Frase reescrita:**" en el output, puedes limpiarlo.
        # Por ahora, asumimos que .text.strip() es suficiente.
        rewritten_text = response.text.strip()
        
        # Opcional: Limpieza adicional si el modelo a veces incluye el prefijo "Frase reescrita:"
        if rewritten_text.lower().startswith("frase reescrita:"):
            rewritten_text = rewritten_text[len("frase reescrita:"):].strip()
            
        return rewritten_text
    except Exception as e:
        st.error(f"Error al reescribir el texto con Gemini: {e}")
        return f"Error al reescribir el texto con Gemini: {e} (Prompt utilizado: {prompt[:200]}...)" # Mostrar parte del prompt puede ayudar a depurar


def suggest_sales_bridge_gemini(context=""):
    if not model_suggestion:
        return "Error: Modelo Gemini para sugerencias no inicializado (revisa la API Key)."
    try:
        prompt = f"""
        El caso de un cliente ha sido resuelto.
        Contexto adicional (opcional): {context}
        Sugiere un script corto y amigable para hacer un puente hacia una venta, ofreciendo un producto o servicio relevante de forma natural.
        No añadas introducciones ni despedidas, solo entrega el script sugerido.
        Script sugerido:
        """
        response = model_suggestion.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error al generar sugerencia de venta con Gemini: {e}")
        return f"Error al generar sugerencia de venta con Gemini: {e}"

def suggest_survey_invitation_gemini(context=""):
    if not model_suggestion:
        return "Error: Modelo Gemini para sugerencias no inicializado (revisa la API Key)."
    try:
        prompt = f"""
        El caso de un cliente ha sido resuelto.
        Contexto adicional (opcional): {context}
        Sugiere un script corto, agradable y efectivo para invitar al cliente a completar una encuesta de satisfacción.
        No añadas introducciones ni despedidas, solo entrega el script sugerido.
        Script sugerido:
        """
        response = model_suggestion.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error al generar invitación a encuesta con Gemini: {e}")
        return f"Error al generar invitación a encuesta con Gemini: {e}"

# --- Resto de la Lógica de la Aplicación Streamlit (como se definió antes) ---

# Conexión a la base de datos SQLite
def get_db_connection():
    conn = sqlite3.connect('app_data.db')
    conn.row_factory = sqlite3.Row
    return conn

# Crear tablas si no existen
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS frequent_scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            template TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0
        )
    ''')
    # Ejemplo de inserción (descomentar y modificar si es necesario para la primera ejecución)
    # scripts_iniciales = [
    #     ("Saludo Inicial Cliente Nuevo", "¡Hola [Nombre Cliente]! Gracias por contactarnos en [Nombre Empresa]. ¿En qué puedo ayudarte hoy con tu línea [Numero Linea]?"),
    #     ("Confirmación de Resolución", "Me alegra confirmar que hemos resuelto tu consulta sobre [Tema Consulta], [Nombre Cliente]."),
    #     ("Despedida Cordial", "Ha sido un placer ayudarte hoy, [Nombre Cliente]. ¡Que tengas un excelente día!")
    # ]
    # for name, template in scripts_iniciales:
    #     cursor.execute("INSERT OR IGNORE INTO frequent_scripts (name, template) VALUES (?, ?)", (name, template))
    conn.commit()
    conn.close()

init_db()

st.title("🤖 Asistente de Interacción con Clientes (con Gemini)")

# --- Transcripción de Voz ---
st.header("🎤 Transcripción de Voz")
if 'transcribed_text' not in st.session_state:
    st.session_state.transcribed_text = ""

# El componente audiorecorder
# Asegúrate de que la key sea única si tienes varios audiorecorders
audio_from_recorder = audiorecorder("Haz clic para grabar", "Grabando...", key="audio_recorder_main")

if len(audio_from_recorder) > 0:
    st.audio(audio_from_recorder.export().read()) # Muestra el audio, confirmando que se grabó

    # --- Procesamiento para SpeechRecognition ---
    try:
        # audio_from_recorder es un objeto pydub.AudioSegment
        # Convertir a un formato estándar para SpeechRecognition:
        # 1. Mono (un solo canal)
        # 2. Tasa de muestreo de 16000 Hz (común para STT)
        # 3. Profundidad de bits de 16 bits (sample_width = 2 bytes)
        
        st.info("Procesando audio para transcripción...")

        audio_segment = audio_from_recorder # Es un AudioSegment de Pydub
        
        # Convertir a mono
        audio_segment = audio_segment.set_channels(1)
        
        # Establecer tasa de muestreo (e.g., 16kHz)
        audio_segment = audio_segment.set_frame_rate(16000)
        
        # Establecer profundidad de bits a 16-bit PCM (sample_width = 2 bytes)
        audio_segment = audio_segment.set_sample_width(2)

        # Obtener los datos crudos (bytes), la tasa de muestreo y el ancho de muestra
        raw_audio_data = audio_segment.raw_data
        sample_rate = audio_segment.frame_rate
        sample_width_bytes = audio_segment.sample_width

        # Crear un objeto AudioData para SpeechRecognition
        audio_data_for_sr = sr.AudioData(raw_audio_data, sample_rate, sample_width_bytes)

        r = sr.Recognizer()
        with st.spinner("Transcribiendo audio..."):
            text = r.recognize_google(audio_data_for_sr, language="es-ES")
        
        st.session_state.transcribed_text = text
        #st.success(f"Texto transcrito: {text}")

    except sr.UnknownValueError:
        st.error("Google Speech Recognition no pudo entender el audio.")
    except sr.RequestError as e:
        st.error(f"No se pudieron obtener resultados del servicio Google Speech Recognition; {e}")
    except Exception as e:
        # Mostrar el error específico para ayudar a depurar más si es necesario
        st.error(f"Ocurrió un error detallado al procesar el audio: {type(e).__name__} - {e}")
        # También puedes loggear el error completo si quieres más detalles en los logs de Streamlit Cloud
        # import traceback
        # st.error(traceback.format_exc())
transcribed_text_area = st.text_area("Texto Transcrito:", value=st.session_state.transcribed_text, height=150, key="transcribed_display_main")
if transcribed_text_area != st.session_state.transcribed_text:
    st.session_state.transcribed_text = transcribed_text_area

# --- Refinar Texto con Gemini ---
st.header("✍️ Refinar Texto (con Gemini)")
if 'rewritten_text' not in st.session_state:
    st.session_state.rewritten_text = ""

if st.button("Reescribir Texto (Cordial, Conciso, Claro)"):
    if st.session_state.transcribed_text:
        if model_rewrite: # Verificar que el modelo esté inicializado
            with st.spinner("Reescribiendo con Gemini..."):
                st.session_state.rewritten_text = rewrite_text_cordial_gemini(st.session_state.transcribed_text)
        else:
            st.error("La función de reescritura no está disponible. Verifica la configuración de la API Key de Gemini.")
    else:
        st.warning("No hay texto transcrito para reescribir.")

rewritten_text_display = st.text_area("Texto Reescrito:", value=st.session_state.rewritten_text, height=150, key="rewritten_display_main")
if rewritten_text_display != st.session_state.rewritten_text:
    st.session_state.rewritten_text = rewritten_text_display

# --- Copiar al Portapapeles ---
if st.button("Copiar Texto Reescrito al Portapapeles 📋"):
    if st.session_state.rewritten_text:
        try:
            pyperclip.copy(st.session_state.rewritten_text)
            st.success("¡Texto reescrito copiado al portapapeles!")
        except pyperclip.PyperclipException as e:
            st.error(f"No se pudo copiar al portapapeles: {e}. Asegúrate de tener 'xclip' o 'xsel' (Linux), 'pbcopy' (macOS), o que estás en Windows.")
    else:
        st.warning("No hay texto reescrito para copiar.")

# --- Scripts Frecuentes (Sidebar) ---
st.sidebar.header("📚 Scripts Frecuentes")

def get_frequent_scripts():
    conn = get_db_connection()
    scripts_db = conn.execute("SELECT id, name, template FROM frequent_scripts ORDER BY usage_count DESC, name LIMIT 15").fetchall()
    conn.close()
    return scripts_db

frequent_scripts = get_frequent_scripts()

st.sidebar.subheader("Personalizar Script")
nombre_cliente_script = st.sidebar.text_input("Nombre del Cliente:", key="script_nombre_cliente_sidebar")
numero_linea_script = st.sidebar.text_input("Número de Línea/ID:", key="script_numero_linea_sidebar")
info_adicional_script = st.sidebar.text_input("Info Adicional (ej: producto, motivo consulta):", key="script_info_adicional_sidebar")


if frequent_scripts:
    script_options = {script['name']: script['template'] for script in frequent_scripts}
    selected_script_name = st.sidebar.selectbox("Selecciona un script:", options=list(script_options.keys()), key="selected_frequent_script_sidebar")

    if selected_script_name:
        selected_template = script_options[selected_script_name]
        personalized_script = selected_template.replace("[Nombre Cliente]", nombre_cliente_script if nombre_cliente_script else "cliente")
        personalized_script = personalized_script.replace("[Numero Linea]", numero_linea_script if numero_linea_script else "su servicio")
        personalized_script = personalized_script.replace("[Info Adicional]", info_adicional_script if info_adicional_script else "") # Placeholder genérico

        st.sidebar.text_area("Script Personalizado:", value=personalized_script, height=200, key="personalized_script_display_sidebar")
        if st.sidebar.button("Copiar Script Personalizado 📋", key="copy_frequent_script_sidebar"):
            try:
                pyperclip.copy(personalized_script)
                st.sidebar.success("Script personalizado copiado.")
            except pyperclip.PyperclipException as e:
                st.sidebar.error(f"No se pudo copiar: {e}")
        if st.sidebar.button("Usar Script en Área Principal", key="use_frequent_script_sidebar"):
            st.session_state.transcribed_text = personalized_script
            st.rerun()
else:
    st.sidebar.info("No hay scripts frecuentes cargados.")

# --- Finalización del Caso con Gemini (Sidebar o Main) ---
st.sidebar.header("🏁 Finalización del Caso")
resolution_context_sidebar = st.sidebar.text_input("Breve resumen de la resolución (opcional):", key="resolution_context_input_sidebar")

if st.sidebar.button("Obtener Sugerencias Post-Resolución (Gemini)", key="get_suggestions_sidebar"):
    if model_suggestion: # Verificar que el modelo esté inicializado
        st.sidebar.subheader("Sugerencias Post-Resolución:")
        with st.sidebar.spinner("Generando sugerencias con Gemini..."):
            # Puente a la Venta
            st.sidebar.markdown("**Puente a la Venta:**")
            sales_suggestion = suggest_sales_bridge_gemini(resolution_context_sidebar)
            st.sidebar.text_area("Script de Venta Sugerido:", value=sales_suggestion, height=100, key="sales_script_display_sidebar")
            if st.sidebar.button("Copiar Script de Venta 📋", key="copy_sales_script_sidebar"):
                try:
                    pyperclip.copy(sales_suggestion)
                    st.sidebar.success("Script de venta copiado.")
                except pyperclip.PyperclipException as e:
                    st.sidebar.error(f"No se pudo copiar: {e}")

            # Invitación a Encuesta
            st.sidebar.markdown("**Invitación a Encuesta:**")
            survey_suggestion = suggest_survey_invitation_gemini(resolution_context_sidebar)
            st.sidebar.text_area("Script de Encuesta Sugerido:", value=survey_suggestion, height=100, key="survey_script_display_sidebar")
            if st.sidebar.button("Copiar Script de Encuesta 📋", key="copy_survey_script_sidebar"):
                try:
                    pyperclip.copy(survey_suggestion)
                    st.sidebar.success("Script de encuesta copiado.")
                except pyperclip.PyperclipException as e:
                    st.sidebar.error(f"No se pudo copiar: {e}")
    else:
        st.sidebar.error("La función de sugerencias no está disponible. Verifica la configuración de la API Key de Gemini.")

# --- Sección para Administrar Scripts (opcional, podría ir en otra página) ---
with st.expander("Administrar Scripts Frecuentes"):
    st.subheader("Añadir Nuevo Script Frecuente")
    with st.form("new_script_form", clear_on_submit=True):
        new_script_name = st.text_input("Nombre del nuevo script:")
        new_script_template = st.text_area("Plantilla del nuevo script (usa [Nombre Cliente], [Numero Linea], [Info Adicional]):")
        submitted_new_script = st.form_submit_button("Guardar Nuevo Script")

        if submitted_new_script:
            if new_script_name and new_script_template:
                try:
                    conn = get_db_connection()
                    conn.execute("INSERT INTO frequent_scripts (name, template) VALUES (?, ?)", (new_script_name, new_script_template))
                    conn.commit()
                    conn.close()
                    st.success(f"Script '{new_script_name}' guardado.")
                    # No es necesario st.rerun() aquí si clear_on_submit=True y no necesitas recargar inmediatamente la lista de selección.
                    # Si la lista de selección debe actualizarse al instante, puedes usar st.rerun() o manejar el estado.
                except sqlite3.Error as e:
                    st.error(f"Error al guardar en la base de datos: {e}")
            else:
                st.warning("El nombre y la plantilla del script no pueden estar vacíos.")

    st.subheader("Eliminar Script Frecuente")
    scripts_for_deletion = get_frequent_scripts()
    if scripts_for_deletion:
        script_names_for_deletion = {script['name']: script['id'] for script in scripts_for_deletion}
        script_to_delete_name = st.selectbox("Selecciona script a eliminar:", options=list(script_names_for_deletion.keys()), key="delete_script_select", index=None) # index=None para que no haya nada seleccionado por defecto

        if script_to_delete_name:
            if st.button(f"Eliminar Script '{script_to_delete_name}'", key="delete_script_button"):
                script_id_to_delete = script_names_for_deletion[script_to_delete_name]
                try:
                    conn = get_db_connection()
                    conn.execute("DELETE FROM frequent_scripts WHERE id = ?", (script_id_to_delete,))
                    conn.commit()
                    conn.close()
                    st.success(f"Script '{script_to_delete_name}' eliminado.")
                    st.rerun() # Para actualizar la lista de scripts inmediatamente
                except sqlite3.Error as e:
                    st.error(f"Error al eliminar de la base de datos: {e}")
    else:
        st.info("No hay scripts para eliminar.")