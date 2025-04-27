import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Configuración básica ---
st.set_page_config(
    page_title="Nirvana Vintage",
    page_icon="✨",
    layout="centered"
)

# --- Conectar con Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_service_account"], scope)
client = gspread.authorize(credentials)

# --- Cargar hoja de cálculo ---
spreadsheet = client.open("Stock")
clientes_sheet = spreadsheet.worksheet("Clientes")
prendas_sheet = spreadsheet.worksheet("Prendas")
vendidas_sheet = spreadsheet.worksheet("Vendidas")

# --- Título principal ---
st.markdown("<h1 style='text-align: center;'>✨ Nirvana Vintage: Gestión Diaria ✨</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Menú de acciones ---
st.subheader("❓ ¿Qué quieres hacer hoy?")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔎 Buscar Cliente"):
        st.success("Funcionalidad de búsqueda de clientes disponible próximamente.")

with col2:
    if st.button("📝 Generar Informe Diario"):
        st.success("Funcionalidad de generación de informe diario disponible próximamente.")

with col3:
    if st.button("💬 Resumen Mensajes a Enviar"):
        st.success("Funcionalidad de resumen de mensajes disponible próximamente.")

st.markdown("---")

# --- Formularios de inserción ---
st.subheader("📄 Formularios Rápidos")

st.markdown(
    """
    - ➕ [Añadir Nueva Prenda](https://forms.gle/TU_FORMULARIO_PRENDA)
    - ➕ [Alta Nuevo Cliente](https://forms.gle/TU_FORMULARIO_CLIENTE)
    - ✅ [Marcar como Vendida](https://forms.gle/TU_FORMULARIO_VENDIDA)
    """
)

st.markdown("---")
st.markdown("<div style='text-align: center;'>Creado con ❤️ para Nirvana Vintage - 2025</div>", unsafe_allow_html=True)
