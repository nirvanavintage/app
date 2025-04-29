import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from fpdf import FPDF
import unicodedata

st.set_page_config(page_title="Nirvana Vintage", page_icon="✨", layout="wide")

# Seguridad básica persistente
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("Contraseña:", type="password")
    if st.button("🔓 Entrar"):
        if password == "nirvana2025":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.warning("Contraseña incorrecta. Inténtalo de nuevo.")
    st.stop()

# Botón para recargar datos
if st.button("🔄 Sincronizar datos desde Google Sheets"):
    st.cache_data.clear()

HIDE_COLS_PATTERN = [
    "Marca temporal", "Merged Doc ID", "Merged Doc URL", "Link to merged Doc", "Document Merge Status"
]

def limpiar_df(df: pd.DataFrame) -> pd.DataFrame:
    cols_a_quitar = [c for c in df.columns for pat in HIDE_COLS_PATTERN if pat.lower() in c.lower()]
    return df.drop(columns=cols_a_quitar, errors="ignore")

def clean_text(text):
    if pd.isnull(text):
        return ""
    try:
        return unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    except Exception:
        return str(text)

class PDFCustom(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "🧵 Nirvana Vintage – Informe de Cliente", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

def exportar_datos_cliente(pdf, cliente):
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, "Datos del Cliente", ln=True)
    pdf.set_font("Helvetica", size=9)
    claves = ['ID Cliente', 'Nombre y Apellidos', 'DNI', 'Teléfono', 'Fecha de Alta', 'Nº de Formulario']
    for campo in claves:
        valor = cliente.get(campo, '')
        pdf.cell(50, 6, f"{campo}:", ln=0)
        pdf.cell(0, 6, clean_text(valor), ln=1)
    pdf.ln(4)

def exportar_descripcion_pdf(pdf, df, titulo_bloque):
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, clean_text(titulo_bloque), ln=True, fill=True)
    pdf.set_font("Helvetica", size=9)
    if df.empty:
        pdf.cell(0, 6, "Sin datos.", ln=True)
        return

    df = df.copy()

    if 'Vendida' in df.columns:
        df['Vendida'] = df['Vendida'].astype(str).str.strip().str.lower().isin(['true', '1', 'x'])
    else:
        df['Vendida'] = False

    df['Descripcion'] = df.apply(
        lambda row: (
            f"{row.get('Tipo de prenda', '')}, Talla: {row.get('Talla', '')}, {row.get('Caracteristicas (Color, estampado, material...)', '')}" +
            (f" | ✔ {row.get('Fecha Vendida') or ''}" if row.get('Vendida') else " | ✖ No vendida")
        ), axis=1
    )

    df['Recepcion'] = df['Fecha de recepcion'].astype(str)

    precios = pd.to_numeric(df.get('Precio', 0), errors='coerce').fillna(0)
    df['Precio_Texto'] = precios.map(lambda x: f"{int(x)} €")

    col_w = [35, 160, 25]
    headers = ['Recepcion', 'Descripcion', 'Precio']
    pdf.set_fill_color(225, 225, 225)
    for i, col in enumerate(headers):
        pdf.cell(col_w[i], 7, clean_text(col), border=1, fill=True)
    pdf.ln()
    for _, row in df.iterrows():
        pdf.cell(col_w[0], 6, clean_text(row['Recepcion']), border=1)
        x = pdf.get_x()
        y = pdf.get_y()
        pdf.multi_cell(col_w[1], 6, clean_text(row['Descripcion']), border=1)
        pdf.set_xy(x + col_w[1], y)
        pdf.cell(col_w[2], 6, clean_text(row['Precio_Texto']), border=1)
        pdf.ln()
    pdf.ln(5)

# Carga de datos (simulado para que no falle aquí)
@st.cache_data
def cargar_datos():
    # Simula carga si no está disponible conexión externa
    return pd.DataFrame(), pd.DataFrame()

df_prendas, df_clientes = cargar_datos()

# Sección interactiva
seccion = st.sidebar.selectbox("Secciones", ["Buscar Cliente", "Consultar Stock", "Consultar Vendidos", "Reporte Diario"])

if not df_prendas.empty:
    df_prendas['Vendida'] = df_prendas['Vendida'].astype(str).str.strip().str.lower().isin(['true', '1', 'x'])
    df_limpio = limpiar_df(df_prendas)

    if seccion == "Consultar Stock":
        st.subheader("👕 Prendas en stock")
        stock = df_limpio[df_limpio['Vendida'] == False]
        filtros = st.multiselect("Filtrar por columna", options=stock.columns.tolist())
        for f in filtros:
            opciones = sorted(stock[f].dropna().astype(str).unique())
            seleccion = st.multiselect(f"{f}", opciones, default=opciones)
            stock = stock[stock[f].astype(str).isin(seleccion)]
        st.dataframe(stock, use_container_width=True)
        st.download_button("📥 Descargar CSV", stock.to_csv(index=False).encode(), file_name="stock.csv")

    elif seccion == "Consultar Vendidos":
        st.subheader("✅ Prendas vendidas")
        vendidos = df_limpio[df_limpio['Vendida'] == True]
        filtros = st.multiselect("Filtrar por columna", options=vendidos.columns.tolist())
        for f in filtros:
            opciones = sorted(vendidos[f].dropna().astype(str).unique())
            seleccion = st.multiselect(f"{f}", opciones, default=opciones)
            vendidos = vendidos[vendidos[f].astype(str).isin(seleccion)]
        st.dataframe(vendidos, use_container_width=True)
        st.download_button("📥 Descargar CSV", vendidos.to_csv(index=False).encode(), file_name="vendidos.csv")
