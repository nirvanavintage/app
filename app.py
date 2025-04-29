import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from fpdf import FPDF
from io import BytesIO
import unicodedata
import base64

st.set_page_config(page_title="Nirvana Vintage", page_icon="✨", layout="wide")

# Seguridad persistente
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <h1 style='text-align:center'>✨ Nirvana Vintage: Gestión Diaria ✨</h1>
    <div style='text-align:center'>
        <a href='https://forms.gle/QAXSH5ZP6oCpWEcL6' target='_blank'>📅 Nueva Prenda</a> |
        <a href='https://forms.gle/2BpmDNegKNTNc2dK6' target='_blank'>👤 Nuevo Cliente</a> |
        <a href='https://www.appsheet.com/start/e1062d5c-129e-4947-bed1-cbb925ad7209?platform=desktop#appName=Marcarcomovendido-584406513&view=Marcar%20como%20vendido' target='_blank'>🔄 App Marcar Vendido</a>
    </div>
    """, unsafe_allow_html=True)

    password = st.text_input("Contraseña:", type="password")
    if st.button("🔓 Entrar"):
        if password == "nirvana2025":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.warning("Contraseña incorrecta. Inténtalo de nuevo.")
    st.stop()

# Encabezado principal
st.markdown("""
<h1 style='text-align:center'>✨ Nirvana Vintage: Gestión Diaria ✨</h1>
<div style='text-align:center'>
    <a href='https://forms.gle/QAXSH5ZP6oCpWEcL6' target='_blank'>📅 Nueva Prenda</a> |
    <a href='https://forms.gle/2BpmDNegKNTNc2dK6' target='_blank'>👤 Nuevo Cliente</a> |
    <a href='https://www.appsheet.com/start/e1062d5c-129e-4947-bed1-cbb925ad7209?platform=desktop#appName=Marcarcomovendido-584406513&view=Marcar%20como%20vendido' target='_blank'>🔄 App Marcar Vendido</a>
</div>
""", unsafe_allow_html=True)

# Botón sincronizar
if st.button("🔄 Sincronizar datos desde Google Sheets"):
    st.cache_data.clear()
    st.rerun()

# Sidebar
seccion = st.sidebar.selectbox("Secciones", [
    "Buscar Cliente", "Consultar Stock", "Consultar Vendidos", "Reporte Diario", "Generador de Etiquetas"
])

# Datos
SHEET_ID = "1reTzFeErA14TRoxaA-PPD5OGfYYXH3Z_0i9bRQeLap8"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="

@st.cache_data(show_spinner=False)
def cargar(sheet):
    return pd.read_csv(URL_BASE + sheet)

try:
    df_prendas = cargar("Prendas")
    df_clientes = cargar("Clientes")
except:
    st.error("❌ No se pudieron cargar los datos.")
    st.stop()

# Conversión
df_prendas["Vendida"] = df_prendas["Vendida"].astype(str).str.lower().isin(["true", "1", "yes", "x"])
df_prendas["Fecha Vendida"] = pd.to_datetime(df_prendas["Fecha Vendida"], errors="coerce")
df_prendas["Fecha de recepción"] = pd.to_datetime(df_prendas["Fecha de recepción"], errors="coerce")

# Aquí iría el resto de funcionalidades
if seccion == "Reporte Diario":
    st.subheader("📆 Reporte Diario")
    fecha = st.date_input("Selecciona una fecha para el reporte")
    vendidas_dia = df_prendas[df_prendas["Fecha Vendida"].dt.date == fecha and df_prendas["Vendida"] == True]
    st.dataframe(vendidas_dia)

elif seccion == "Consultar Stock":
    st.subheader("📦 Prendas en stock")
    stock = df_prendas[~df_prendas["Vendida"]]
    st.dataframe(stock)

elif seccion == "Consultar Vendidos":
    st.subheader("✅ Prendas Vendidas")
    vendidos = df_prendas[df_prendas["Vendida"]]
    st.dataframe(vendidos)

elif seccion == "Buscar Cliente":
    st.subheader("🔍 Buscar Cliente")
    nombre = st.text_input("Nombre cliente")
    if nombre:
        coincidencias = df_clientes[df_clientes["Nombre y Apellidos"].str.contains(nombre, case=False)]
        st.dataframe(coincidencias)
# SECCIÓN: Generador de Etiquetas
if seccion == "Generador de Etiquetas":
    st.markdown("### 🏷️ Generador de Etiquetas")
    cod = st.text_input("Introduce un código de prenda")
    hoy = pd.Timestamp.today().normalize()

    st.markdown("#### 🔹 Generar una sola etiqueta")
    if st.button("Generar etiqueta única") and cod:
        prenda = df_prendas[df_prendas["ID Prenda"] == cod]
        if not prenda.empty:
            st.dataframe(prenda)
            row = prenda.iloc[0]
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=False)
            pdf.add_page()
            pdf.set_xy(10, 10)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(70, 8, texto_fpdf(f"€ {row['Precio']}"), ln=2)
            pdf.cell(70, 8, texto_fpdf(f"Talla {row['Talla']}"), ln=2)
            pdf.set_font("Arial", '', 10)
            pdf.cell(70, 6, texto_fpdf(f"Cliente: {row['Nº Cliente (Formato C-xxx)']}"), ln=2)
            pdf.cell(70, 6, texto_fpdf(f"Prenda: {row['ID Prenda']}"), ln=2)
            buffer = BytesIO()
            pdf.output(buffer)
            buffer.seek(0)
            st.download_button("⬇️ Descargar Etiqueta", buffer.getvalue(), file_name=f"etiqueta_{cod}.pdf")
        else:
            st.warning("No se encontró la prenda.")

    st.markdown("#### 🔹 Generar etiquetas de productos vendidos hoy")
    hoy_vendidas = df_prendas[(df_prendas["Vendida"]) & (df_prendas["Fecha Vendida"].dt.date == hoy.date())]
    if not hoy_vendidas.empty:
        st.dataframe(hoy_vendidas)
        if st.button("Generar PDF con etiquetas del día"):
            etiquetas_por_fila = 2
            filas_por_pagina = 5
            etiquetas_por_pagina = etiquetas_por_fila * filas_por_pagina
            etiqueta_ancho = 70
            etiqueta_alto = 40

            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=False)

            for i, (_, row) in enumerate(hoy_vendidas.iterrows()):
                if i % etiquetas_por_pagina == 0:
                    pdf.add_page()

                x = 10 + (i % etiquetas_por_fila) * (etiqueta_ancho + 10)
                y = 10 + ((i // etiquetas_por_fila) % filas_por_pagina) * (etiqueta_alto + 10)

                pdf.set_xy(x, y)
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(etiqueta_ancho, 8, texto_fpdf(f"€ {row['Precio']}"), ln=2)
                pdf.cell(etiqueta_ancho, 8, texto_fpdf(f"Talla {row['Talla']}"), ln=2)
                pdf.set_font("Arial", '', 10)
                pdf.cell(etiqueta_ancho, 6, texto_fpdf(f"Cliente: {row['Nº Cliente (Formato C-xxx)']}"), ln=2)
                pdf.cell(etiqueta_ancho, 6, texto_fpdf(f"Prenda: {row['ID Prenda']}"), ln=2)

            buffer = BytesIO()
            pdf.output(buffer)
            buffer.seek(0)
            st.download_button("⬇️ Descargar Todas las Etiquetas", buffer.getvalue(), file_name="etiquetas_vendidas_hoy.pdf")
