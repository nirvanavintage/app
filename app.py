import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# Configurar la página
st.set_page_config(page_title="Nirvana Vintage", page_icon="✨", layout="wide")

# Función para generar PDFs bonitos
def generar_pdf(dataframe, titulo):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    fecha = datetime.now().strftime("%d/%m/%Y")
    pdf.cell(0, 10, f"{titulo}", ln=True, align='C')
    pdf.cell(0, 10, f"Fecha de generación: {fecha}", ln=True, align='C')
    pdf.ln(10)

    col_width = max(30, pdf.w / (len(dataframe.columns) + 2))
    row_height = 8

    pdf.set_fill_color(220, 220, 220)
    for col in dataframe.columns:
        pdf.cell(col_width, row_height, str(col), border=1, fill=True)
    pdf.ln()

    pdf.set_fill_color(255, 255, 255)
    for i in range(len(dataframe)):
        for col in dataframe.columns:
            pdf.cell(col_width, row_height, str(dataframe.iloc[i][col]), border=1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin1')

# --- PORTADA ---
st.markdown("<h1 style='text-align: center;'>✨ Nirvana Vintage: Gestión Diaria ✨</h1>", unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center;'>
    <a href='https://forms.gle/QAXSH5ZP6oCpWEcL6' target='_blank'>📅 Nueva Prenda</a> |
    <a href='https://forms.gle/2BpmDNegKNTNc2dK6' target='_blank'>👤 Nuevo Cliente</a> |
    <a href='https://www.appsheet.com/start/e1062d5c-129e-4947-bed1-cbb925ad7209?platform=desktop#appName=Marcarcomovendido-584406513&view=Marcar%20como%20vendido' target='_blank'>🔄 App Marcar Vendido</a>
</div>
""", unsafe_allow_html=True)

# --- DATOS ---
sheet_id = "1reTzFeErA14TRoxaA-PPD5OGfYYXH3Z_0i9bRQeLap8"
prendas_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Prendas"
clientes_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Clientes"

try:
    prendas = pd.read_csv(prendas_url)
    clientes = pd.read_csv(clientes_url)
except:
    st.error("No se pudieron cargar los datos.")
    st.stop()

prendas["Vendida"] = prendas["Vendida"].astype(str).str.lower().map({"true": True, "false": False})

# --- RESUMEN ---
col1, col2, col3 = st.columns(3)

with col1:
    stock_count = prendas[prendas["Vendida"] == False].shape[0]
    st.metric("👕 Prendas en Stock", stock_count)

with col2:
    vendidos_count = prendas[prendas["Vendida"] == True].shape[0]
    st.metric("✅ Prendas Vendidas", vendidos_count)

with col3:
    hoy = datetime.now().strftime("%d/%m/%Y")
    avisos_count = prendas[(prendas["Fecha Aviso"] == hoy) & (prendas["Vendida"] == False)].shape[0]
    st.metric("📅 Avisos de Hoy", avisos_count)

st.markdown("---")

# --- MENU PRINCIPAL ---
opciones = ["Buscar Cliente", "Consultar Stock", "Consultar Vendidos", "Generar Avisos de Hoy"]
seleccion = st.sidebar.radio("Selecciona una sección:", opciones)

if seleccion == "Buscar Cliente":
    nombre_cliente = st.text_input("Introduce el nombre del cliente")
    if st.button("🔍 Buscar Cliente"):
        resultados = clientes[clientes["Nombre y Apellidos"].str.contains(nombre_cliente, case=False, na=False)]
        if not resultados.empty:
            st.success(f"Se encontraron {len(resultados)} cliente(s)")
            st.dataframe(resultados)
            ids_cliente = resultados["ID Cliente"].unique()

            stock_cliente = prendas[(prendas["Nº Cliente (Formato C-xxx)"] .isin(ids_cliente)) & (prendas["Vendida"] == False)]
            vendidas_cliente = prendas[(prendas["Nº Cliente (Formato C-xxx)"] .isin(ids_cliente)) & (prendas["Vendida"] == True)]

            st.subheader("🍋 Prendas en Stock")
            if not stock_cliente.empty:
                st.dataframe(stock_cliente)
                pdf_stock = generar_pdf(stock_cliente, "Prendas en Stock del Cliente")
                st.download_button("⬇️ Descargar Stock PDF", pdf_stock, file_name="stock_cliente.pdf", mime="application/pdf")
            else:
                st.info("No hay prendas en stock.")

            st.subheader("✅ Prendas Vendidas")
            if not vendidas_cliente.empty:
                st.dataframe(vendidas_cliente)
                pdf_vendidas = generar_pdf(vendidas_cliente, "Prendas Vendidas del Cliente")
                st.download_button("⬇️ Descargar Vendidas PDF", pdf_vendidas, file_name="vendidas_cliente.pdf", mime="application/pdf")
            else:
                st.info("No hay prendas vendidas.")
        else:
            st.error("Cliente no encontrado.")

elif seleccion == "Consultar Stock":
    st.subheader("🍋 Stock disponible")
    stock = prendas[prendas["Vendida"] == False]

    st.dataframe(stock)
    if not stock.empty:
        pdf_stock_total = generar_pdf(stock, "Listado de Stock Actual")
        st.download_button("⬇️ Descargar Stock Total", pdf_stock_total, file_name="stock_total.pdf", mime="application/pdf")

elif seleccion == "Consultar Vendidos":
    st.subheader("✅ Prendas Vendidas")
    vendidos = prendas[prendas["Vendida"] == True]

    st.dataframe(vendidos)
    if not vendidos.empty:
        pdf_vendidos_total = generar_pdf(vendidos, "Listado de Vendidos")
        st.download_button("⬇️ Descargar Vendidos", pdf_vendidos_total, file_name="vendidos_total.pdf", mime="application/pdf")

elif seleccion == "Generar Avisos de Hoy":
    st.subheader("📅 Avisos de WhatsApp para hoy")
    avisos = prendas[(prendas["Fecha Aviso"] == hoy) & (prendas["Vendida"] == False)]

    if not avisos.empty:
        st.success(f"Se encontraron {len(avisos)} avisos.")
        st.dataframe(avisos)

        pdf_avisos = generar_pdf(avisos, "Avisos de WhatsApp del Día")
        st.download_button("⬇️ Descargar Avisos PDF", pdf_avisos, file_name="avisos_hoy.pdf", mime="application/pdf")
    else:
        st.info("No hay avisos para hoy.")

st.markdown("---")
st.markdown("<p style='text-align: center;'>❤️ Creado con amor para Nirvana Vintage - 2025 ❤️</p>", unsafe_allow_html=True)
