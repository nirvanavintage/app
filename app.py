# -*- coding: utf-8 -*-
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# --- Configuración de la página ---
st.set_page_config(
    page_title="Nirvana Vintage: Gestión Diaria ✨",
    page_icon="✨",
    layout="centered",
)

# --- Título de la app ---
st.title("✨ Nirvana Vintage: Gestión Diaria ✨")
st.markdown("---")

# --- Funciones auxiliares ---
@st.cache_resource
def conectar_sheets():
    """Conecta a Google Sheets usando las credenciales de Streamlit Secrets."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=scope
    )
    client = gspread.authorize(credentials)
    return client

@st.cache_data
def cargar_datos_hoja(nombre_hoja):
    """Carga los datos de una hoja de Google Sheets como DataFrame."""
    client = conectar_sheets()
    spreadsheet = client.open("Stock")  # nombre exacto del archivo
    worksheet = spreadsheet.worksheet(nombre_hoja)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# --- Menú de acciones principales ---
st.subheader("\u2753 ¡Qué quieres hacer hoy?")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("\ud83d\udd0d Buscar Cliente"):
        clientes_df = cargar_datos_hoja("Clientes")
        nombre = st.text_input("Introduce el nombre del cliente:")
        if nombre:
            resultados = clientes_df[clientes_df['Nombre y Apellidos'].str.contains(nombre, case=False, na=False)]
            st.dataframe(resultados)

with col2:
    if st.button("\ud83d\udcc5 Generar Informe Diario"):
        prendas_df = cargar_datos_hoja("Prendas")
        hoy = pd.Timestamp.now().strftime("%d/%m/%Y")
        prendas_hoy = prendas_df[prendas_df['Fecha de Alta'] == hoy]
        if not prendas_hoy.empty:
            st.success(f"Hoy hay {len(prendas_hoy)} prendas registradas.")
            st.dataframe(prendas_hoy)
        else:
            st.info("Hoy no hay prendas nuevas registradas.")

with col3:
    if st.button("\ud83d\udcac Resumen Mensajes a Enviar"):
        vendidas_df = cargar_datos_hoja("Vendidas")
        pendientes = vendidas_df[vendidas_df['Estado'] == 'Pendiente']
        if not pendientes.empty:
            st.success(f"Tienes {len(pendientes)} mensajes de venta pendientes de enviar.")
            st.dataframe(pendientes)
        else:
            st.info("No hay mensajes pendientes para hoy.")

# --- Separador ---
st.markdown("---")

# --- Formularios rápidos ---
st.subheader("\ud83d\udcc4 Formularios rápidos")

st.markdown("""
- [➕ Añadir Nueva Prenda](https://docs.google.com/forms/d/e/FORM_ID_AQUI/viewform)
- [➕ Alta Nuevo Cliente](https://docs.google.com/forms/d/e/FORM_ID_AQUI/viewform)
- [✅ Marcar como Vendida](https://docs.google.com/forms/d/e/FORM_ID_AQUI/viewform)
""")

# --- Pie de página ---
st.markdown("---")
st.markdown("""<center>Creado con ❤️ para Nirvana Vintage · 2025</center>""", unsafe_allow_html=True)
