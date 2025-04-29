import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from fpdf import FPDF
import unicodedata

st.set_page_config(page_title="Nirvana Vintage", page_icon="✨", layout="wide")

HIDE_COLS_PATTERN = [
    "Marca temporal",
    "Merged Doc ID", "Merged Doc URL", "Link to merged Doc", "Document Merge Status"
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

def df_to_pdf(df, titulo, nombre_archivo):
    df = limpiar_df(df)
    df = df.copy()

    # Fusionar columnas para hacerlo más compacto
    if {'Tipo de prenda', 'Talla', 'Características (Color, estampado, material...)'}.issubset(df.columns):
        df["Descripción"] = (
            df["Tipo de prenda"].fillna('') + ", Talla: " + df["Talla"].fillna('') +
            ", " + df["Características (Color, estampado, material...)"].fillna('')
        )
        df.drop(["Tipo de prenda", "Talla", "Características (Color, estampado, material...)"], axis=1, inplace=True)

    df = df.astype(str).fillna("")

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, clean_text(titulo), ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", size=8)
    col_widths = {}
    total_width = 277  # A4 landscape width minus margins

    # Calcular anchos proporcionales
    base_width = total_width / len(df.columns)
    for col in df.columns:
        col_widths[col] = base_width

    # Cabecera
    for col in df.columns:
        pdf.cell(col_widths[col], 6, clean_text(col), border=1, ln=0)
    pdf.ln()

    # Filas
    for _, row in df.iterrows():
        y_before = pdf.get_y()
        max_y = y_before
        x_start = pdf.get_x()
        for col in df.columns:
            text = clean_text(row[col])
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.multi_cell(col_widths[col], 4, text, border=1)
            max_y = max(max_y, pdf.get_y())
            pdf.set_xy(x + col_widths[col], y)
        pdf.set_y(max_y)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        st.download_button(
            "📄 Descargar PDF",
            tmp.read(),
            file_name=nombre_archivo,
            mime="application/pdf"
        )
        os.unlink(tmp.name)

# =========
# Encabezado
# =========

st.markdown("""
<h1 style='text-align:center'>✨ Nirvana Vintage: Gestión Diaria ✨</h1>
<div style='text-align:center'>
    <a href='https://forms.gle/QAXSH5ZP6oCpWEcL6' target='_blank'>📅 Nueva Prenda</a> |
    <a href='https://forms.gle/2BpmDNegKNTNc2dK6' target='_blank'>👤 Nuevo Cliente</a> |
    <a href='https://www.appsheet.com/start/e1062d5c-129e-4947-bed1-cbb925ad7209?platform=desktop#appName=Marcarcomovendido-584406513&view=Marcar%20como%20vendido' target='_blank'>🔄 App Marcar Vendido</a>
</div>
""", unsafe_allow_html=True)

# ===============
# Menú
# ===============

st.sidebar.markdown("""
<style>
.sidebar .sidebar-content {
    padding: 2rem 1rem;
}
.sidebar .stSelectbox > div { font-size: 18px; }
</style>
""", unsafe_allow_html=True)

menu_options = [
    "Buscar Cliente",
    "Consultar Stock",
    "Consultar Vendidos",
    "Generar Avisos de Hoy",
    "Reporte Diario",
    "Informe Cliente por Entregas"
]

seccion = st.sidebar.selectbox("🪄 Secciones disponibles:", menu_options, index=0)

# =============
# Cargar datos
# =============

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

if "Vendida" in df_prendas.columns:
    df_prendas["Vendida"] = df_prendas["Vendida"].astype(str).str.lower().map({"true": True, "false": False})

prendas_limpio = limpiar_df(df_prendas)

# =============
# Secciones
# =============

if seccion == "Buscar Cliente":
    nombre = st.text_input("Nombre cliente")
    if st.button("🔍 Buscar") and nombre:
        clientes_match = df_clientes[df_clientes["Nombre y Apellidos"].str.contains(nombre, case=False, na=False)]
        if clientes_match.empty:
            st.warning("No se encontraron coincidencias.")
        else:
            st.success(f"Se encontraron {len(clientes_match)} cliente(s)")
            st.dataframe(limpiar_df(clientes_match), use_container_width=True)
            ids = clientes_match["ID Cliente"].unique()
            prendas_cliente = prendas_limpio[prendas_limpio["Nº Cliente (Formato C-xxx)"].isin(ids)]
            st.subheader("👜 Prendas del cliente")
            st.dataframe(prendas_cliente, use_container_width=True)

elif seccion == "Consultar Stock":
    st.subheader("🍋 Stock Actual")
    stock = prendas_limpio[~df_prendas["Vendida"]]
    st.dataframe(stock, use_container_width=True)

elif seccion == "Consultar Vendidos":
    st.subheader("✅ Prendas Vendidas")
    vendidos = prendas_limpio[df_prendas["Vendida"]]
    st.dataframe(vendidos, use_container_width=True)

elif seccion == "Generar Avisos de Hoy":
    hoy = pd.Timestamp.today().normalize()
    avisos_hoy = prendas_limpio[pd.to_datetime(df_prendas["Fecha Aviso"], errors="coerce").dt.normalize() == hoy]
    st.subheader(f"📣 Avisos para {hoy.date()}: {len(avisos_hoy)}")
    st.dataframe(avisos_hoy, use_container_width=True)

elif seccion == "Reporte Diario":
    hoy = pd.Timestamp.today().normalize()
    vendidos_hoy = prendas_limpio[df_prendas["Vendida"] & (pd.to_datetime(df_prendas["Fecha Vendida"], errors="coerce").dt.normalize() == hoy)]
    st.subheader(f"✅ Prendas Vendidas hoy {hoy.date()} ({len(vendidos_hoy)})")
    st.dataframe(vendidos_hoy, use_container_width=True)

    if st.button("📄 PDF Ventas de Hoy"):
        fecha = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        titulo = f"Ventas del día {datetime.today().date().isoformat()}"
        df_to_pdf(vendidos_hoy, titulo, f"ventas_{fecha}.pdf")

elif seccion == "Informe Cliente por Entregas":
    nombre = st.text_input("Nombre cliente")
    if st.button("Buscar entregas") and nombre:
        cliente = df_clientes[df_clientes["Nombre y Apellidos"].str.contains(nombre, case=False, na=False)]
        if cliente.empty:
            st.warning("No se encontró el cliente.")
        else:
            idc = cliente.iloc[0]["ID Cliente"]
            nombre_cliente = cliente.iloc[0]["Nombre y Apellidos"]
            prendas_cliente = prendas_limpio[prendas_limpio["Nº Cliente (Formato C-xxx)"] == idc]
            st.dataframe(prendas_cliente, use_container_width=True)
            if st.button("📄 PDF Informe Cliente"):
                prendas_ventas = prendas_cliente[prendas_cliente['Vendida'] == True]
                if prendas_ventas.empty:
                    st.warning("Este cliente no tiene prendas vendidas para mostrar en el informe.")
                else:
                    fecha = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                    titulo = f"Informe de ventas – Cliente {idc} – {nombre_cliente}"
                    df_to_pdf(prendas_ventas, titulo, f"cliente_{idc}_{fecha}.pdf")

st.markdown("---")
st.markdown("<div style='text-align:center'>❤️ Nirvana Vintage 2025</div>", unsafe_allow_html=True)
