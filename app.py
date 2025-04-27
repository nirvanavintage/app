import streamlit as st
import pandas as pd

# Configuración básica de la página
st.set_page_config(
    page_title="Nirvana Vintage",
    page_icon="✨",
    layout="centered"
)

# Título principal
st.markdown("""
<h1 style='text-align: center;'>✨ Nirvana Vintage: Gestión Diaria ✨</h1>
<hr style='border:1px solid #444;'>
""", unsafe_allow_html=True)

# Cargar datos de Google Sheets
sheet_url = "https://docs.google.com/spreadsheets/d/1reTzFeErA14TRoxaA-PPD5OGfYYXH3Z_0i9bRQeLap8/export?format=csv"
df = pd.read_csv(sheet_url)

# Sidebar con acciones
st.subheader("\ud83d\udcc4 ¿Qué quieres hacer hoy?")
accion = st.selectbox("Selecciona una acción", ("Buscar Cliente", "Consultar Stock", "Consultar Vendidos"))

# Buscar cliente
if accion == "Buscar Cliente":
    nombre_cliente = st.text_input("Introduce el nombre del cliente")
    if st.button("\ud83d\udd0d Buscar"):
        resultados = df[df['Nombre y Apellidos'].str.contains(nombre_cliente, case=False, na=False)]
        if not resultados.empty:
            st.success(f"Se encontraron {len(resultados)} cliente(s):")
            st.dataframe(resultados)
        else:
            st.warning("No se encontraron clientes con ese nombre.")

# Consultar Stock (prendas no vendidas)
elif accion == "Consultar Stock":
    stock = df[df['Vendida'] == 'No'] if 'Vendida' in df.columns else pd.DataFrame()
    if not stock.empty:
        st.success(f"Hay {len(stock)} prendas en stock.")
        st.dataframe(stock)
    else:
        st.warning("No hay prendas en stock registradas.")

# Consultar Vendidos (prendas vendidas)
elif accion == "Consultar Vendidos":
    vendidos = df[df['Vendida'] == 'Sí'] if 'Vendida' in df.columns else pd.DataFrame()
    if not vendidos.empty:
        st.success(f"Hay {len(vendidos)} prendas vendidas.")
        st.dataframe(vendidos)
    else:
        st.warning("No hay prendas vendidas registradas.")

# Footer bonito
st.markdown("""
<br>
<p style='text-align: center;'>💖 Creado con amor para Nirvana Vintage - 2025</p>
""", unsafe_allow_html=True)
