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
    pdf = FPDF(orientation="L")
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 10, clean_text(titulo), ln=True, align="C")
    pdf.ln(4)

    col_w = pdf.w / (len(df.columns) + 1)
    for col in df.columns:
        pdf.cell(col_w, 6, clean_text(col), border=1)
    pdf.ln()

    for _, row in df.iterrows():
        for item in row:
            pdf.cell(col_w, 5, clean_text(item), border=1)
        pdf.ln()

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
    stock = prendas_limpio[~df_prendas["Vendida"]]
    vendidos_hoy = prendas_limpio[df_prendas["Vendida"] & (pd.to_datetime(df_prendas["Fecha Vendida"], errors="coerce").dt.normalize() == hoy)]
    avisos_hoy = prendas_limpio[pd.to_datetime(df_prendas["Fecha Aviso"], errors="coerce").dt.normalize() == hoy]

    st.markdown("## Avisos de Hoy")
    st.dataframe(avisos_hoy, use_container_width=True)

    st.markdown("## Ventas de Hoy")
    st.dataframe(vendidos_hoy, use_container_width=True)

    st.markdown("## Stock Actual")
    st.dataframe(stock, use_container_width=True)

    if st.button("📄 PDF Reporte Diario"):
        fecha = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        titulo = f"Reporte Diario – {datetime.today().date().isoformat()}"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf = FPDF(orientation="L")
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)
            pdf.cell(0, 10, clean_text(titulo), ln=True, align="C")
            pdf.ln(5)

            for nombre_seccion, df_sec in [
                ("Avisos de Hoy", avisos_hoy),
                ("Ventas de Hoy", vendidos_hoy),
                ("Stock Actual", stock)
            ]:
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 8, clean_text(nombre_seccion), ln=True)
                pdf.ln(2)
                pdf.set_font("Helvetica", size=9)
                df_sec = limpiar_df(df_sec)
                df_sec = df_sec.astype(str).fillna("")
                if df_sec.empty:
                    pdf.cell(0, 6, "Sin datos.", ln=True)
                else:
                    col_w = pdf.w / (len(df_sec.columns) + 1)
                    for col in df_sec.columns:
                        pdf.cell(col_w, 6, clean_text(col), border=1)
                    pdf.ln()
                    for _, row in df_sec.iterrows():
                        for item in row:
                            pdf.cell(col_w, 5, clean_text(item), border=1)
                        pdf.ln()
                pdf.ln(4)

            pdf.output(tmp.name)
            tmp.seek(0)
            st.download_button("📄 Descargar PDF Diario", tmp.read(), file_name=f"reporte_{fecha}.pdf", mime="application/pdf")
            os.unlink(tmp.name)

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
                fecha = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                titulo = f"Cliente {idc} – {nombre_cliente}"
                df_to_pdf(prendas_cliente, titulo, f"cliente_{idc}_{fecha}.pdf")

st.markdown("---")
st.markdown("<div style='text-align:center'>❤️ Nirvana Vintage 2025</div>", unsafe_allow_html=True)
