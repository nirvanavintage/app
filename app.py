import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from fpdf import FPDF
import unicodedata

st.set_page_config(page_title="Nirvana Vintage", page_icon="✨", layout="wide")

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

def exportar_descripcion_pdf(pdf, df, titulo_bloque):
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 8, clean_text(titulo_bloque), ln=True)
    pdf.set_font("Helvetica", size=8)
    if df.empty:
        pdf.cell(0, 6, "Sin datos.", ln=True)
        return

    df = df.copy()
    df['Vendida'] = df.get('Vendida', False).fillna(False)
    df['Descripcion'] = df.apply(
        lambda row: (
            f"{row.get('Tipo de prenda', '')}, Talla: {row.get('Talla', '')}, {row.get('Caracteristicas (Color, estampado, material...)', '')}" +
            (f" | ✔ {row.get('Fecha Vendida')}" if row.get('Vendida') else " | ✖ No vendida")
        ), axis=1
    )

    if 'Fecha de recepcion' in df.columns:
        df['Recepcion'] = pd.to_datetime(df['Fecha de recepcion'], errors='coerce').dt.strftime('%d/%m/%Y')
    else:
        df['Recepcion'] = ''

    precios = pd.to_numeric(df.get('Precio', 0), errors='coerce').fillna(0)
    df['Precio_Texto'] = precios.map(lambda x: f"{int(x)} €")

    col_w = [30, 180, 25]
    headers = ['Recepcion', 'Descripcion', 'Precio']
    for i, col in enumerate(headers):
        pdf.cell(col_w[i], 6, clean_text(col), border=1)
    pdf.ln()
    for _, row in df.iterrows():
        pdf.cell(col_w[0], 6, clean_text(row['Recepcion']), border=1)
        x = pdf.get_x()
        y = pdf.get_y()
        pdf.multi_cell(col_w[1], 6, clean_text(row['Descripcion']), border=1)
        pdf.set_xy(x + col_w[1], y)
        pdf.cell(col_w[2], 6, clean_text(row['Precio_Texto']), border=1)
        pdf.ln()
    pdf.ln(6)

# El resto del código permanece sin cambios

# (...)

def generar_pdf_prendas(df, titulo):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, clean_text(titulo), ln=True, align="C")
    pdf.ln(5)
    exportar_descripcion_pdf(pdf, df, "Listado")
    total = pd.to_numeric(df['Precio'], errors='coerce').fillna(0).sum()
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 8, clean_text(f"Total prendas: {len(df)} | Total vendido: {int(total)} €"), ln=True)
    return pdf

st.markdown("""
<h1 style='text-align:center'>✨ Nirvana Vintage: Gestión Diaria ✨</h1>
<div style='text-align:center'>
    <a href='https://forms.gle/QAXSH5ZP6oCpWEcL6' target='_blank'>📅 Nueva Prenda</a> |
    <a href='https://forms.gle/2BpmDNegKNTNc2dK6' target='_blank'>👤 Nuevo Cliente</a> |
    <a href='https://www.appsheet.com/start/e1062d5c-129e-4947-bed1-cbb925ad7209?platform=desktop#appName=Marcarcomovendido-584406513&view=Marcar%20como%20vendido' target='_blank'>🔄 App Marcar Vendido</a>
</div>
""", unsafe_allow_html=True)

menu_options = ["Buscar Cliente", "Consultar Stock", "Consultar Vendidos", "Generar Avisos de Hoy", "Reporte Diario"]
seccion = st.sidebar.selectbox("🪄 Secciones disponibles:", menu_options, index=0)

SHEET_ID = "1reTzFeErA14TRoxaA-PPD5OGfYYXH3Z_0i9bRQeLap8"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="

@st.cache_data
def cargar(sheet: str) -> pd.DataFrame:
    return pd.read_csv(URL_BASE + sheet)

try:
    df_prendas = cargar("Prendas")
    df_clientes = cargar("Clientes")
except Exception:
    st.error("❌ No se pudieron cargar los datos. Revisa conexión o permisos de la hoja.")
    st.stop()

if "Vendida" in df_prendas.columns:
    df_prendas["Vendida"] = df_prendas["Vendida"].astype(str).str.strip().str.lower().map({"true": True, "false": False, "": False})

if "Precio" in df_prendas.columns:
    df_prendas["Precio"] = pd.to_numeric(df_prendas["Precio"], errors="coerce")

prendas_limpio = limpiar_df(df_prendas)

if seccion == "Buscar Cliente":
    nombre = st.text_input("Nombre cliente")
    if nombre:
        if st.button("🔍 Buscar"):
            clientes_match = df_clientes[df_clientes["Nombre y Apellidos"].str.contains(nombre, case=False, na=False)]
            st.session_state['clientes_match'] = clientes_match.to_dict("records")

    if 'clientes_match' in st.session_state:
        clientes_df = pd.DataFrame(st.session_state['clientes_match'])
        if clientes_df.empty:
            st.warning("No se encontraron coincidencias.")
        else:
            st.success(f"Se encontraron {len(clientes_df)} cliente(s)")
            st.dataframe(limpiar_df(clientes_df), use_container_width=True)
            ids = clientes_df["ID Cliente"].unique()
            prendas_cliente = prendas_limpio[prendas_limpio["Nº Cliente (Formato C-xxx)"].isin(ids)]
            st.subheader("👜 Prendas del cliente")
            st.dataframe(prendas_cliente, use_container_width=True)
            if st.button("📄 PDF Informe del Cliente"):
                nombre_cliente = clientes_df.iloc[0]["Nombre y Apellidos"]
                idc = clientes_df.iloc[0]["ID Cliente"]
                titulo = f"Informe del cliente {idc} – {nombre_cliente}"
                prendas_ventas = prendas_cliente[~prendas_cliente['Fecha Vendida'].isna()]
                prendas_stock = prendas_cliente[prendas_cliente['Fecha Vendida'].isna()]
                pdf = FPDF(orientation="L", unit="mm", format="A4")
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 14)
                pdf.cell(0, 10, clean_text(titulo), ln=True, align="C")
                pdf.ln(4)
                exportar_descripcion_pdf(pdf, prendas_ventas, "🟢 Prendas Vendidas")
                exportar_descripcion_pdf(pdf, prendas_stock, "🟡 Prendas en stock")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    pdf.output(tmp.name)
                    tmp.seek(0)
                    st.download_button("📄 Descargar PDF Informe Cliente", tmp.read(), file_name=f"informe_cliente_{idc}.pdf", mime="application/pdf")
                    os.unlink(tmp.name)

elif seccion == "Reporte Diario":
    fecha_seleccionada = st.date_input("Selecciona una fecha para el reporte", value=datetime.today().date())
    fecha_dt = pd.to_datetime(fecha_seleccionada).normalize()
    df_prendas['Fecha Vendida'] = pd.to_datetime(df_prendas['Fecha Vendida'], errors='coerce')
    vendidos_fecha = df_prendas[
        (~df_prendas['Fecha Vendida'].isna()) &
        (df_prendas['Fecha Vendida'].dt.normalize() == fecha_dt)
    ]
    st.subheader(f"✅ Prendas Vendidas el {fecha_dt.date()} ({len(vendidos_fecha)})")
    st.dataframe(vendidos_fecha, use_container_width=True)

    if st.button("📄 PDF Ventas de la Fecha"):
        pdf = generar_pdf_prendas(vendidos_fecha, f"Ventas del {fecha_dt.strftime('%d/%m/%Y')}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf.output(tmp.name)
            tmp.seek(0)
            st.download_button("📄 Descargar PDF", tmp.read(), file_name=f"ventas_{fecha_dt.strftime('%Y-%m-%d')}.pdf", mime="application/pdf")
            os.unlink(tmp.name)
