import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Nirvana Vintage",
    page_icon="✨",
    layout="centered"
)

# Título bonito
st.markdown("<h1 style='text-align: center;'>✨ Nirvana Vintage: Gestión Diaria ✨</h1>", unsafe_allow_html=True)
st.markdown("---")

# Cargar datos
url = "https://docs.google.com/spreadsheets/d/1reTzFeErA14TRoxaA-PPD5OGfYYXH3Z_0i9bRQeLap8/export?format=csv"
data = pd.read_csv(url)

# Comprobar si existe columna Vendida
if 'Vendida' in data.columns:
    data['Vendida'] = data['Vendida'].astype(str).str.lower().map({'true': True, 'false': False})

# Dividir datos si existen las columnas
if 'Nombre y Apellidos' in data.columns:
    clientes = data.dropna(subset=['Nombre y Apellidos'])
else:
    clientes = pd.DataFrame()

if 'Vendida' in data.columns:
    prendas = data.dropna(subset=['Vendida'])
else:
    prendas = pd.DataFrame()

# Opciones
st.subheader("📝 ¿Qué quieres hacer hoy?")

opciones = ["Buscar Cliente", "Consultar Stock", "Consultar Vendidos"]
seleccion = st.selectbox("Selecciona una acción", opciones)

if seleccion == "Buscar Cliente":
    nombre_cliente = st.text_input("Introduce el nombre del cliente")
    if st.button("🔍 Buscar"):
        resultados = clientes[clientes["Nombre y Apellidos"].str.contains(nombre_cliente, case=False, na=False)]
        if not resultados.empty:
            st.success(f"Se encontraron {len(resultados)} cliente(s):")
            st.dataframe(resultados)
        else:
            st.error("No se encontraron clientes con ese nombre.")

elif seleccion == "Consultar Stock":
    if not prendas.empty:
        stock = prendas[prendas["Vendida"] == False]
        st.success(f"Hay {len(stock)} prendas en stock disponibles.")
        st.dataframe(stock)
    else:
        st.error("No se pudo encontrar información de stock.")

elif seleccion == "Consultar Vendidos":
    if not prendas.empty:
        vendidos = prendas[prendas["Vendida"] == True]
        st.success(f"Hay {len(vendidos)} prendas vendidas.")
        st.dataframe(vendidos)
    else:
        st.error("No se pudo encontrar información de prendas vendidas.")

# Footer bonito
st.markdown("---")
st.markdown("<p style='text-align: center;'>❤️ Creado con amor para Nirvana Vintage - 2025 ❤️</p>", unsafe_allow_html=True)
