import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from fpdf import FPDF
from io import BytesIO
import xlsxwriter

st.set_page_config(page_title="Nirvana Vintage", page_icon="✨", layout="wide")

# Seguridad básica persistente
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
            st.experimental_rerun()
        else:
            st.warning("Contraseña incorrecta. Inténtalo de nuevo.")
    st.stop()

# Encabezado
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
seccion = st.sidebar.selectbox("Secciones", ["Buscar Cliente", "Consultar Stock", "Consultar Vendidos", "Reporte Diario"])

# Datos
SHEET_ID = "1reTzFeErA14TRoxaA-PPD5OGfYYXH3Z_0i9bRQeLap8"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="

@st.cache_data
def cargar(sheet):
    return pd.read_csv(URL_BASE + sheet)

try:
    df_prendas = cargar("Prendas")
    df_clientes = cargar("Clientes")
except:
    st.error("❌ No se pudieron cargar los datos.")
    st.stop()

if df_prendas["Vendida"].dtype != bool:
    df_prendas["Vendida"] = df_prendas["Vendida"].fillna(False).astype(str).str.lower().isin(["true", "1", "yes", "x"])

if seccion == "Buscar Cliente":
    nombre = st.text_input("🔍 Introduce el nombre del cliente")
    if nombre:
        resultados = df_clientes[df_clientes["Nombre y Apellidos"].str.contains(nombre, case=False, na=False)]
        st.dataframe(resultados, use_container_width=True)

elif seccion == "Consultar Stock":
    stock = df_prendas[df_prendas["Vendida"] == False]
    st.dataframe(stock, use_container_width=True)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        stock.to_excel(writer, index=False, sheet_name="Stock")
    st.download_button("⬇️ Descargar Stock (Excel)", output.getvalue(), file_name="stock.xlsx")

elif seccion == "Consultar Vendidos":
    vendidos = df_prendas[df_prendas["Vendida"] == True]
    st.dataframe(vendidos, use_container_width=True)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        vendidos.to_excel(writer, index=False, sheet_name="Vendidos")
    st.download_button("⬇️ Descargar Vendidos (Excel)", output.getvalue(), file_name="vendidos.xlsx")

elif seccion == "Reporte Diario":
    fecha = st.date_input("Selecciona una fecha para el reporte", value=datetime.today())
    fecha_dt = pd.to_datetime(fecha)
    df_prendas["Fecha Vendida"] = pd.to_datetime(df_prendas["Fecha Vendida"], errors="coerce")
    vendidos_dia = df_prendas[df_prendas["Vendida"] & (df_prendas["Fecha Vendida"].dt.date == fecha_dt.date())]
    st.subheader(f"✅ Prendas Vendidas el {fecha_dt.strftime('%d/%m/%Y')} ({len(vendidos_dia)})")
    st.dataframe(vendidos_dia, use_container_width=True)

    if st.button("📄 Descargar PDF del Día"):
        class PDF(FPDF):
            def header(self):
                self.set_font("Helvetica", "B", 12)
                self.cell(0, 10, f"Ventas del {fecha_dt.strftime('%d/%m/%Y')}", ln=True, align="C")
                self.ln(5)

        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=10)

        total = 0
        for _, row in vendidos_dia.iterrows():
            talla = str(row['Talla']) if pd.notna(row['Talla']) else ""
            desc = f"{row['Tipo de prenda']}, Talla: {talla}, {row.get('Caracteristicas (Color, estampado, material...)', '')}"
            precio = pd.to_numeric(row['Precio'], errors='coerce')
            total += 0 if pd.isna(precio) else precio
            pdf.cell(0, 10, desc.strip(), ln=True)

        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, f"Total prendas: {len(vendidos_dia)} | Total vendido: {int(total)} €", ln=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf.output(tmp.name)
            tmp.seek(0)
            st.download_button("📄 Descargar PDF", tmp.read(), file_name=f"ventas_{fecha_dt.strftime('%Y-%m-%d')}.pdf", mime="application/pdf")
            os.unlink(tmp.name)
