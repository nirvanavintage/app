import streamlit as st
import pandas as pd
from fpdf import FPDF

# Configurar la página
st.set_page_config(
    page_title="Nirvana Vintage",
    page_icon="✨",
    layout="wide"
)

# Título principal
st.markdown("<h1 style='text-align: center;'>✨ Nirvana Vintage: Gestión Diaria ✨</h1>", unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center;'>
    <a href='https://forms.gle/QAXSH5ZP6oCpWEcL6' target='_blank'>📅 Nueva Prenda</a> | 
    <a href='https://forms.gle/2BpmDNegKNTNc2dK6' target='_blank'>👤 Nuevo Cliente</a> | 
    <a href='https://www.appsheet.com/start/e1062d5c-129e-4947-bed1-cbb925ad7209?platform=desktop#appName=Marcarcomovendido-584406513&view=Marcar%20como%20vendido' target='_blank'>🔄 App Marcar Vendido</a>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Cargar datos de Google Sheets
sheet_id = "1reTzFeErA14TRoxaA-PPD5OGfYYXH3Z_0i9bRQeLap8"
prendas_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Prendas"
clientes_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Clientes"

try:
    prendas = pd.read_csv(prendas_url)
    clientes = pd.read_csv(clientes_url)
except Exception as e:
    st.error("No se pudieron cargar los datos.")
    st.stop()

# Normalizar columna Vendida
if "Vendida" in prendas.columns:
    prendas["Vendida"] = prendas["Vendida"].astype(str).str.lower().map({"true": True, "false": False})

# Opciones principales
st.subheader("🗋 ¿Qué quieres hacer hoy?")
opciones = ["Buscar Cliente", "Consultar Stock", "Consultar Vendidos"]
seleccion = st.selectbox("Selecciona una acción", opciones)

# Función para generar PDF horizontal
def generar_pdf(dataframe, titulo):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, titulo, ln=True, align='C')
    pdf.ln(10)

    col_width = pdf.w / (len(dataframe.columns) + 1)

    for col in dataframe.columns:
        pdf.cell(col_width, 10, str(col), border=1)
    pdf.ln()

    for i in range(len(dataframe)):
        for col in dataframe.columns:
            pdf.cell(col_width, 10, str(dataframe.iloc[i][col]), border=1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin1')

if seleccion == "Buscar Cliente":
    nombre_cliente = st.text_input("Introduce el nombre del cliente")
    if st.button("🔍 Buscar"):
        resultados = clientes[clientes["Nombre y Apellidos"].str.contains(nombre_cliente, case=False, na=False)]
        if not resultados.empty:
            st.success(f"Se encontraron {len(resultados)} cliente(s):")
            st.dataframe(resultados, use_container_width=True)
            ids_cliente = resultados["ID Cliente"].unique()

            stock_cliente = prendas[(prendas["Nº Cliente (Formato C-xxx)"].isin(ids_cliente)) & (prendas["Vendida"] == False)]
            vendidas_cliente = prendas[(prendas["Nº Cliente (Formato C-xxx)"].isin(ids_cliente)) & (prendas["Vendida"] == True)]

            st.subheader("🍋 Prendas en Stock:")
            if not stock_cliente.empty:
                st.dataframe(stock_cliente, use_container_width=True)
                pdf_stock = generar_pdf(stock_cliente, "Prendas en Stock")
                st.download_button("⬇️ Descargar Stock (PDF)", pdf_stock, file_name="stock_cliente.pdf", mime="application/pdf")
            else:
                st.info("No hay prendas en stock para este cliente.")

            st.subheader("✅ Prendas Vendidas:")
            if not vendidas_cliente.empty:
                st.dataframe(vendidas_cliente, use_container_width=True)
                pdf_vendidas = generar_pdf(vendidas_cliente, "Prendas Vendidas")
                st.download_button("⬇️ Descargar Vendidas (PDF)", pdf_vendidas, file_name="vendidas_cliente.pdf", mime="application/pdf")
            else:
                st.info("No hay prendas vendidas para este cliente.")
        else:
            st.error("No se encontraron clientes con ese nombre.")

elif seleccion == "Consultar Stock":
    st.subheader("🍋 Prendas en Stock")
    stock = prendas[prendas["Vendida"] == False]

    talla = st.selectbox("Filtrar por Talla", ["Todas"] + sorted(stock["Talla"].dropna().unique()))
    tipo_prenda = st.selectbox("Filtrar por Tipo de Prenda", ["Todas"] + sorted(stock["Tipo de prenda"].dropna().unique()))
    marca = st.selectbox("Filtrar por Marca", ["Todas"] + sorted(stock["Marca"].dropna().unique()))

    if talla != "Todas":
        stock = stock[stock["Talla"] == talla]
    if tipo_prenda != "Todas":
        stock = stock[stock["Tipo de prenda"] == tipo_prenda]
    if marca != "Todas":
        stock = stock[stock["Marca"] == marca]

    st.success(f"Hay {len(stock)} prendas disponibles en stock.")
    st.dataframe(stock, use_container_width=True)

    if not stock.empty:
        pdf_stock = generar_pdf(stock, "Stock Disponible")
        st.download_button("⬇️ Descargar Stock (PDF)", pdf_stock, file_name="stock_total.pdf", mime="application/pdf")

elif seleccion == "Consultar Vendidos":
    st.subheader("✅ Prendas Vendidas")
    vendidos = prendas[prendas["Vendida"] == True]

    talla = st.selectbox("Filtrar por Talla", ["Todas"] + sorted(vendidos["Talla"].dropna().unique()))
    tipo_prenda = st.selectbox("Filtrar por Tipo de Prenda", ["Todas"] + sorted(vendidos["Tipo de prenda"].dropna().unique()))
    marca = st.selectbox("Filtrar por Marca", ["Todas"] + sorted(vendidos["Marca"].dropna().unique()))

    if talla != "Todas":
        vendidos = vendidos[vendidos["Talla"] == talla]
    if tipo_prenda != "Todas":
        vendidos = vendidos[vendidos["Tipo de prenda"] == tipo_prenda]
    if marca != "Todas":
        vendidos = vendidos[vendidos["Marca"] == marca]

    st.success(f"Hay {len(vendidos)} prendas vendidas.")
    st.dataframe(vendidos, use_container_width=True)

    if not vendidos.empty:
        pdf_vendidos = generar_pdf(vendidos, "Prendas Vendidas")
        st.download_button("⬇️ Descargar Vendidos (PDF)", pdf_vendidos, file_name="vendidos_total.pdf", mime="application/pdf")

st.markdown("---")
st.markdown("<p style='text-align: center;'>❤️ Creado con amor para Nirvana Vintage - 2025 ❤️</p>", unsafe_allow_html=True)
