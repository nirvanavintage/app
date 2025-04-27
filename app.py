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

# Cargar datos correctos
sheet_id = "1reTzFeErA14TRoxaA-PPD5OGfYYXH3Z_0i9bRQeLap8"
prendas_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Prendas"
clientes_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Clientes"

# Leer datos
try:
    prendas = pd.read_csv(prendas_url)
    clientes = pd.read_csv(clientes_url)
except Exception as e:
    st.error("No se pudieron cargar los datos.")
    st.stop()

# Normalizar la columna Vendida
if "Vendida" in prendas.columns:
    prendas["Vendida"] = prendas["Vendida"].astype(str).str.lower().map({"true": True, "false": False})

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
    stock = prendas[prendas["Vendida"] == False]
    st.success(f"Hay {len(stock)} prendas disponibles en stock:")
    st.dataframe(stock)

elif seleccion == "Consultar Vendidos":
    vendidos = prendas[prendas["Vendida"] == True]
    st.success(f"Hay {len(vendidos)} prendas vendidas:")
    st.dataframe(vendidos)

# Footer bonito
st.markdown("---")
st.markdown("<p style='text-align: center;'>❤️ Creado con amor para Nirvana Vintage - 2025 ❤️</p>", unsafe_allow_html=True)
