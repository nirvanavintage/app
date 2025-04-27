# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Configuración de página ---
st.set_page_config(
    page_title="Nirvana Vintage: Gestión Diaria ✨",
    page_icon="✨",
    layout="centered",
)

# --- Conexión a Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_service_account"], scope)
client = gspread.authorize(credentials)
spreadsheet = client.open("Stock")  # Nombre exacto del archivo
sheet_clientes = spreadsheet.worksheet("Clientes")
sheet_prendas = spreadsheet.worksheet("Prendas")
sheet_stock = spreadsheet.worksheet("Stock")
sheet_vendidas = spreadsheet.worksheet("Vendidas")

# --- Interfaz principal ---
st.title("✨ Nirvana Vintage: Gestión Diaria ✨")
st.markdown("---")

# --- Sección de acciones principales ---
st.subheader("❓ ¿Qué quieres hacer hoy?")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔎 Buscar Cliente"):
        st.info("Funcionalidad de búsqueda de clientes (próximamente disponible).")

with col2:
    if st.button("🗓️ Generar Informe Diario"):
        st.info("Generar el informe de WhatsApps a enviar (próximamente disponible).")

with col3:
    if st.button("💬 Resumen Mensajes a Enviar"):
        st.info("Mostrar el resumen de mensajes programados (próximamente disponible).")

st.markdown("---")

# --- Formularios rápidos ---
st.subheader("📋 Formularios rápidos")

st.markdown(
    """
- ➕ [Añadir Nueva Prenda](https://forms.gle/TU_FORMULARIO_PRENDAS)
- 🆕 [Alta Nuevo Cliente](https://forms.gle/TU_FORMULARIO_CLIENTES)
- ✅ [Marcar como Vendida](https://forms.gle/TU_FORMULARIO_VENDIDAS)
    """
)

st.markdown("---")
st.caption("Creado con ❤️ para Nirvana Vintage • 2025")
