import streamlit as st
import pandas as pd
from fpdf import FPDF

st.set_page_config(page_title="Nirvana Vintage", page_icon="✨", layout="wide")

st.title(":sparkles: Nirvana Vintage: Gestión Diaria :sparkles:")
st.markdown("---")

# Enlaces
st.sidebar.header("🔗 Formularios y App")
st.sidebar.markdown("[Formulario Nueva Prenda](https://forms.gle/QAXSH5ZP6oCpWEcL6)")
st.sidebar.markdown("[Formulario Nuevo Cliente](https://forms.gle/2BpmDNegKNTNc2dK6)")
st.sidebar.markdown("[App Marcar como Vendido](https://www.appsheet.com/start/e1062d5c-129e-4947-bed1-cbb925ad7209?platform=desktop#appName=Marcarcomovendido-584406513&view=Marcar%20como%20vendido)")

# Cargar datos
clientes_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3M3U_N5T5_-dLw0V_3pA8mrDulz-cznJNHwFM1GcfjxzqM8j5mfJpRzF4YBOZBsgjsvDRKsDnpD7I/pub?gid=1775701755&single=true&output=csv"
prendas_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3M3U_N5T5_-dLw0V_3pA8mrDulz-cznJNHwFM1GcfjxzqM8j5mfJpRzF4YBOZBsgjsvDRKsDnpD7I/pub?gid=517323538&single=true&output=csv"

df_clientes = pd.read_csv(clientes_url)
df_prendas = pd.read_csv(prendas_url)

# Asegurar conversión correcta de la columna Vendida
if "Vendida" in df_prendas.columns:
    df_prendas["Vendida"] = df_prendas["Vendida"].fillna(False).astype(bool)

# Opciones
accion = st.selectbox("Selecciona una acción", ["Buscar Cliente", "Consultar Stock", "Consultar Vendidos"])

# Función para exportar tabla a PDF en horizontal
def generar_pdf_tabla(nombre_archivo, titulo, dataframe):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, titulo, ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=10)
    col_width = pdf.w / (len(dataframe.columns) + 1)

    # Cabecera
    for col in dataframe.columns:
        pdf.cell(col_width, 10, col, border=1)
    pdf.ln()

    # Datos
    for index, row in dataframe.iterrows():
        for item in row:
            pdf.cell(col_width, 10, str(item), border=1)
        pdf.ln()

    pdf.output(nombre_archivo)

# Opciones de acción
if accion == "Buscar Cliente":
    nombre_cliente = st.text_input("Introduce el nombre del cliente")
    if st.button("🔍 Buscar"):
        resultados = df_clientes[df_clientes["Nombre y Apellidos"].str.contains(nombre_cliente, case=False, na=False)]
        if not resultados.empty:
            st.success(f"Se encontró {len(resultados)} cliente(s):")
            st.dataframe(resultados)

            id_cliente = resultados.iloc[0]["ID Cliente"]

            prendas_cliente = df_prendas[df_prendas["Nº Cliente (Formato C-xxx)"] == id_cliente]
            stock_cliente = prendas_cliente[prendas_cliente["Vendida"] == False]
            vendidos_cliente = prendas_cliente[prendas_cliente["Vendida"] == True]

            st.subheader(":hanger: Prendas en Stock")
            if not stock_cliente.empty:
                st.dataframe(stock_cliente)
            else:
                st.info("No hay prendas en stock.")

            st.subheader(":shopping_bags: Prendas Vendidas")
            if not vendidos_cliente.empty:
                st.dataframe(vendidos_cliente)
            else:
                st.info("No hay prendas vendidas.")

            if st.button("🔖 Generar Informe PDF del Cliente"):
                informe_nombre = f"informe_cliente_{id_cliente}.pdf"
                generar_pdf_tabla(informe_nombre, f"Informe de {resultados.iloc[0]['Nombre y Apellidos']}", prendas_cliente)
                with open(informe_nombre, "rb") as file:
                    st.download_button(label="📄 Descargar Informe PDF", data=file, file_name=informe_nombre, mime="application/pdf")
        else:
            st.error("No se encontró ningún cliente.")

elif accion == "Consultar Stock":
    tipo_filtro = st.selectbox("Filtrar por tipo de prenda", ["Todos"] + sorted(df_prendas["Tipo de prenda"].dropna().unique().tolist()))
    stock = df_prendas[df_prendas["Vendida"] == False]
    if tipo_filtro != "Todos":
        stock = stock[stock["Tipo de prenda"] == tipo_filtro]

    st.success(f"Hay {len(stock)} prenda(s) en stock.")
    st.dataframe(stock)

    if st.button("📄 Generar PDF de Stock"):
        stock_nombre = "stock_total.pdf"
        generar_pdf_tabla(stock_nombre, "Stock disponible", stock)
        with open(stock_nombre, "rb") as file:
            st.download_button(label="📥 Descargar PDF", data=file, file_name=stock_nombre, mime="application/pdf")

elif accion == "Consultar Vendidos":
    tipo_filtro = st.selectbox("Filtrar por tipo de prenda", ["Todos"] + sorted(df_prendas["Tipo de prenda"].dropna().unique().tolist()))
    vendidos = df_prendas[df_prendas["Vendida"] == True]
    if tipo_filtro != "Todos":
        vendidos = vendidos[vendidos["Tipo de prenda"] == tipo_filtro]

    st.success(f"Hay {len(vendidos)} prenda(s) vendidas.")
    st.dataframe(vendidos)

    if st.button("📄 Generar PDF de Vendidos"):
        vendidos_nombre = "vendidos_total.pdf"
        generar_pdf_tabla(vendidos_nombre, "Prendas Vendidas", vendidos)
        with open(vendidos_nombre, "rb") as file:
            st.download_button(label="📥 Descargar PDF", data=file, file_name=vendidos_nombre, mime="application/pdf")

st.markdown("""
---
<div style='text-align: center;'>❤️ Creado con amor para Nirvana Vintage - 2025 ❤️</div>
""", unsafe_allow_html=True)
