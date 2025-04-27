import streamlit as st
import pandas as pd

# --- Configuración de página ---
st.set_page_config(
    page_title="Nirvana Vintage",
    page_icon="🌟",
    layout="centered"
)

# --- Título principal ---
st.markdown("""
    <h1 style='text-align: center;'>🌟 Nirvana Vintage: Gestión Diaria 🌟</h1>
    <hr>
""", unsafe_allow_html=True)

# --- URL de tu Google Sheets compartido ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1reTzFeErA14TRoxaA-PPD5OGfYYXH3Z_0i9bRQeLap8/export?format=csv"

# --- Carga de datos ---
def cargar_datos():
    try:
        df = pd.read_csv(SHEET_URL)
        return df
    except Exception as e:
        st.error(f"No se pudo cargar la hoja de Google Sheets: {e}")
        return pd.DataFrame()

# --- Menú de acciones ---
st.subheader("👉 ¿Qué quieres hacer hoy?")
opcion = st.selectbox("Selecciona una acción", ("Buscar Cliente", "Generar Informe Diario", "Ver Stock"))

# --- Acciones ---
if opcion == "Buscar Cliente":
    df_clientes = cargar_datos()
    nombre = st.text_input("Introduce el nombre del cliente")
    if st.button("🔍 Buscar"):
        if not df_clientes.empty:
            resultados = df_clientes[df_clientes['Nombre y Apellidos'].str.contains(nombre, case=False, na=False)]
            if not resultados.empty:
                st.success(f"Se encontraron {len(resultados)} cliente(s):")
                st.dataframe(resultados)
            else:
                st.warning("No se encontraron clientes con ese nombre.")

elif opcion == "Generar Informe Diario":
    df_mensajes = cargar_datos()
    if not df_mensajes.empty:
        st.subheader("📢 Resumen de Mensajes a Enviar Hoy")
        # Filtramos por hoy (simulado para ahora mismo)
        hoy = pd.to_datetime("today").date()
        df_mensajes['Fecha de Alta'] = pd.to_datetime(df_mensajes['Fecha de Alta'], errors='coerce')
        mensajes_hoy = df_mensajes[df_mensajes['Fecha de Alta'].dt.date == hoy]
        if not mensajes_hoy.empty:
            for idx, row in mensajes_hoy.iterrows():
                st.info(f"Enviar mensaje a {row['Nombre y Apellidos']} al teléfono {row['Teléfono']}")
        else:
            st.success("No hay mensajes programados para hoy. 😊")

elif opcion == "Ver Stock":
    df_stock = cargar_datos()
    if not df_stock.empty:
        st.subheader("📦 Estado del Stock")
        st.dataframe(df_stock)

# --- Footer bonito ---
st.markdown("""
    <hr>
    <center>💛 Creado con amor para Nirvana Vintage · 2025</center>
""", unsafe_allow_html=True)
