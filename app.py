import streamlit as st
import pandas as pd
import tempfile
import os
import datetime
from datetime import datetime, timedelta
from fpdf import FPDF  # Fallback option

# Try to import pdfkit, but provide fallback
PDFKIT_AVAILABLE = False
try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    st.warning("PDF generation with pdfkit is not available. Using fallback FPDF method.")

# =====================
# Configuración general
# =====================

st.set_page_config(page_title="Nirvana Vintage", page_icon="✨", layout="wide")
HIDE_COLS_PATTERN = [  # nombres exactos o parciales a descartar
    "Marca temporal",              # columna A (timestamp del formulario)
    "Merged Doc ID", "Merged Doc URL", "Link to merged Doc", "Document Merge Status"  # columnas P‑S
]

# Utilidad para ocultar columnas no deseadas
def limpiar_df(df: pd.DataFrame) -> pd.DataFrame:
    cols_a_quitar = [c for c in df.columns for pat in HIDE_COLS_PATTERN if pat.lower() in c.lower()]
    return df.drop(columns=cols_a_quitar, errors="ignore")

# Función para generar PDFs
def df_to_pdf(df, titulo, nombre_archivo):
    # Quitar columnas no deseadas
    cols_mostrar = [c for c in df.columns if c not in [
        "Marca temporal",
        *df.columns[df.columns.str.startswith("Merged Doc")]
    ]]
    df = df[cols_mostrar]
    
    if PDFKIT_AVAILABLE:
        try:
            # Configuración para pdfkit
            WKHTML_PATH = '/usr/bin/wkhtmltopdf'
            pdfkit_config = pdfkit.configuration(wkhtmltopdf=WKHTML_PATH)
            
            # Estilo CSS simple
            css = """
            <style>
              body { font-family: Arial, sans-serif; }
              h2   { text-align:center; }
              table { border-collapse:collapse; width:100%; font-size:10px; }
              th, td { border:1px solid #666; padding:4px; }
              th { background:#eee; }
            </style>
            """
            html = f"<h2>{titulo}</h2>" + df.to_html(index=False)
            full_html = f"<html><head>{css}</head><body>{html}</body></html>"

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                pdfkit.from_string(full_html, tmp.name,
                                configuration=pdfkit_config,
                                options={"page-size": "A4",
                                        "orientation": "Landscape",
                                        "margin-top": "8mm",
                                        "margin-bottom": "8mm",
                                        "margin-left": "8mm",
                                        "margin-right": "8mm"})
                tmp.seek(0)
                st.download_button(
                    "📄 Descargar PDF",
                    tmp.read(),
                    file_name=nombre_archivo,
                    mime="application/pdf"
                )
                os.unlink(tmp.name)
            return
        except Exception as e:
            st.warning(f"No se pudo generar PDF con pdfkit: {str(e)}. Usando método alternativo.")
    
    # Fallback a FPDF si pdfkit no está disponible o falla
    pdf = FPDF(orientation="L")
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, titulo, ln=True, align="C")
    pdf.ln(4)

    col_w = pdf.w / (len(df.columns) + 1)
    for col in df.columns:
        pdf.cell(col_w, 6, str(col), border=1)
    pdf.ln()
    
    for _, row in df.iterrows():
        for item in row:
            pdf.cell(col_w, 5, str(item), border=1)
        pdf.ln()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        st.download_button(
            "📄 Descargar PDF (FPDF)",
            tmp.read(),
            file_name=nombre_archivo,
            mime="application/pdf"
        )
        os.unlink(tmp.name)

# ==========
# Encabezado
# ==========

st.markdown("""
<h1 style='text-align:center'>✨ Nirvana Vintage: Gestión Diaria ✨</h1>
<div style='text-align:center'>
    <a href='https://forms.gle/QAXSH5ZP6oCpWEcL6' target='_blank'>📅 Nueva Prenda</a> |
    <a href='https://forms.gle/2BpmDNegKNTNc2dK6' target='_blank'>👤 Nuevo Cliente</a> |
    <a href='https://www.appsheet.com/start/e1062d5c-129e-4947-bed1-cbb925ad7209?platform=desktop#appName=Marcarcomovendido-584406513&view=Marcar%20como%20vendido' target='_blank'>🔄 App Marcar Vendido</a>
</div>
""", unsafe_allow_html=True)

# ====================
# Cargar datos remotos
# ====================

SHEET_ID = "1reTzFeErA14TRoxaA-PPD5OGfYYXH3Z_0i9bRQeLap8"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="

def cargar(sheet: str) -> pd.DataFrame:
    return pd.read_csv(URL_BASE + sheet)

try:
    df_prendas = cargar("Prendas")
    df_clientes = cargar("Clientes")
except Exception:
    st.error("❌ No se pudieron cargar los datos. Revisa la conexión o los permisos de la hoja Google Sheets.")
    st.stop()

# Normalizar columna Vendida (casilla de verificación)
if "Vendida" in df_prendas.columns:
    df_prendas["Vendida"] = df_prendas["Vendida"].astype(str).str.lower().map({"true": True, "false": False})

# Eliminar columnas que no deben mostrarse
prendas_limpio = limpiar_df(df_prendas)

# ================
# Secciones (menú)
# ================

st.sidebar.markdown("""
<style>
.sidebar-button {
    display: block;
    width: 100%;
    padding: 8px 12px;
    margin: 6px 0;
    background-color: #f0f2f6;
    color: #333;
    text-align: left;
    border-radius: 4px;
    border: 1px solid #ddd;
    text-decoration: none;
    transition: all 0.3s;
}
.sidebar-button:hover {
    background-color: #e0e2e6;
    color: #000;
}
.sidebar-button.active {
    background-color: #4a8bfc;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# Definir las opciones del menú
menu_options = [
    "Buscar Cliente",
    "Consultar Stock",
    "Consultar Vendidos",
    "Generar Avisos de Hoy",
    "Reporte Diario",
    "Informe Cliente por Entregas"
]

# Mostrar el menú como selectbox con estilo de botones
seccion = st.sidebar.selectbox(
    "🪄 Secciones",
    menu_options,
    format_func=lambda x: f"▸ {x}",
    index=0
)

# [Resto del código permanece igual...]
