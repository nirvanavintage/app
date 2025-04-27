import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Nirvana Vintage",
    page_icon="✨",
    layout="centered"
)

# Título principal
st.markdown("<h1 style='text-align: center;'>✨ Nirvana Vintage: Gestión Diaria ✨</h1>", unsafe_allow_html=True)
st.markdown("---")

# Cargar los datos desde el enlace público
url = "https://docs.google.com/spreadsheets/d/1reTzFeErA14TRoxaA-PPD5OGfYYXH3Z_0i9bRQeLap8/export?format=csv"
data = pd.read_csv(url)

# Separar hojas manualmente
clientes = data[data['Nº de Formulario'] == 1]  # Clientes están en hoja Clientes
prendas = data[data['Nº de Formulario'] == 2]   # Prendas en hoja Stock

# Menú de acciones
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
    stock = prendas[prendas["Vendida"] != "Sí"]
    st.success(f"Hay {len(stock)} prendas en stock disponibles.")
    st.dataframe(stock)

elif seleccion == "Consultar Vendidos":
    vendidos = prendas[prendas["Vendida"] == "Sí"]
    st.success(f"Hay {len(vendidos)} prendas vendidas.")
    st.dataframe(vendidos)

# Footer bonito
st.markdown("---")
st.markdown("<p style='text-align: center;'>❤️ Creado con amor para Nirvana Vintage - 2025 ❤️</p>", unsafe_allow_html=True)
