import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta

# ░░ CONFIGURACIÓN BÁSICA ░░
st.set_page_config(page_title="Nirvana Vintage", page_icon="✨", layout="wide")

# === UTILIDADES ============================================================

def load_google_sheet(sheet_id: str, sheet_name: str) -> pd.DataFrame:
    """Carga un sheet público como CSV y devuelve un DataFrame."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(url)

def clean_prendas(df: pd.DataFrame) -> pd.DataFrame:
    # Normalizar Vendida ✔ / ❌
    if "Vendida" in df.columns:
        df["Vendida"] = df["Vendida"].astype(str).str.lower().map({"true": True, "false": False, "1": True, "0": False}).fillna(False)
    # Ocultar columnas que no se quieren visualizar (A  y P‑S)
    cols_to_hide = [
        "Marca temporal",  # Columna A
        *df.columns[df.columns.get_indexer(["P"]):]  # P hasta final si existen
    ]
    cols_to_hide = [c for c in cols_to_hide if c in df.columns]
    return df.drop(columns=cols_to_hide, errors="ignore")


def make_pdf_table(title: str, df: pd.DataFrame, filename: str):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(0, 10, txt=title, ln=True)
    pdf.ln(4)

    # Cabeceras
    pdf.set_font("Arial", "B", 10)
    col_w = 280 / len(df.columns)
    for col in df.columns:
        pdf.cell(col_w, 8, col[:25], 1, 0, 'C')
    pdf.ln()

    pdf.set_font("Arial", size=9)
    for _, row in df.iterrows():
        for val in row:
            pdf.cell(col_w, 6, str(val)[:30], 1, 0, 'C')
        pdf.ln()
    pdf.output(filename)

# === CARGA DE DATOS ========================================================
SHEET_ID = "1reTzFeErA14TRoxaA-PPD5OGfYYXH3Z_0i9bRQeLap8"

try:
    df_prendas_raw = load_google_sheet(SHEET_ID, "Prendas")
    df_clientes = load_google_sheet(SHEET_ID, "Clientes")
    df_prendas = clean_prendas(df_prendas_raw.copy())
except Exception as e:
    st.error("❌ No se pudieron cargar los datos de Google Sheets. Asegúrate de que el documento sea público.")
    st.stop()

# === SIDEBAR / NAVEGACIÓN ==================================================
with st.sidebar:
    st.header("📂 Secciones")
    section = st.radio(
        "", [
            "🏷️ Buscar Cliente",
            "📦 Consultar Stock",
            "🛍️ Consultar Vendidos",
            "📲 Generar Avisos de Hoy",
            "📊 Reporte Diario",
            "📝 Informe Cliente por Entregas"
        ],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.subheader("🔗 Formularios y App")
    st.markdown("[➕ Nueva Prenda](https://forms.gle/QAXSH5ZP6oCpWEcL6)")
    st.markdown("[👤 Nuevo Cliente](https://forms.gle/2BpmDNegKNTNc2dK6)")
    st.markdown("[🔄 App Marcar Vendido](https://www.appsheet.com/start/e1062d5c-129e-4947-bed1-cbb925ad7209?platform=desktop#appName=Marcarcomovendido-584406513&view=Marcar%20como%20vendido)")

# === CABECERA MÉTRICAS =====================================================
col1, col2, col3, col4 = st.columns(4)
col1.metric("📦 Stock", int((df_prendas["Vendida"] == False).sum()))
col2.metric("✅ Vendidas", int((df_prendas["Vendida"] == True).sum()))
# Avisos hoy
hoy = pd.Timestamp.today().normalize()
avisos_hoy = df_prendas_raw[df_prendas_raw["Fecha Aviso"].astype(str).str.startswith(hoy.strftime("%d/%m/%Y"))]
col3.metric("📲 Avisos Hoy", len(avisos_hoy))
col4.metric("💸 Ventas Hoy", int((df_prendas_raw["Fecha Vendida"].astype(str).str.startswith(hoy.strftime("%d/%m/%Y"))).sum()))

# === SECCIONES ============================================================

if section.startswith("🏷️"):
    st.subheader("🔍 Buscar Cliente")
    nombre = st.text_input("Nombre cliente")
    if st.button("Buscar") and nombre:
        res = df_clientes[df_clientes["Nombre y Apellidos"].str.contains(nombre, case=False, na=False)]
        if res.empty:
            st.warning("No se encontraron clientes.")
        else:
            st.dataframe(res, use_container_width=True)
            ids = res["ID Cliente"].unique()
            prendas_cli = df_prendas[df_prendas_raw["Nº Cliente (Formato C-xxx)"].isin(ids)]
            st.write("### 🍋 Stock del cliente")
            st.dataframe(prendas_cli[prendas_cli["Vendida"] == False])
            st.write("### ✅ Vendidas del cliente")
            st.dataframe(prendas_cli[prendas_cli["Vendida"] == True])

elif section.startswith("📦"):
    st.subheader("📦 Prendas en Stock")
    st.dataframe(df_prendas[df_prendas["Vendida"] == False], use_container_width=True)
    if st.button("📥 Descargar PDF Stock"):
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        fname = f"stock_total_{ts}.pdf"
        make_pdf_table("Stock disponible", df_prendas[df_prendas["Vendida"] == False], fname)
        with open(fname, "rb") as f:
            st.download_button("Descargar PDF", f, fname)

elif section.startswith("🛍️"):
    st.subheader("🛍️ Prendas Vendidas")
    st.dataframe(df_prendas[df_prendas["Vendida"] == True], use_container_width=True)
    if st.button("📥 Descargar PDF Vendidos"):
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        fname = f"vendidos_{ts}.pdf"
        make_pdf_table("Prendas vendidas", df_prendas[df_prendas["Vendida"] == True], fname)
        with open(fname, "rb") as f:
            st.download_button("Descargar PDF", f, fname)

elif section.startswith("📲"):
    st.subheader("📲 Avisos para hoy")
    st.dataframe(avisos_hoy.drop(columns=[c for c in avisos_hoy.columns if c not in df_prendas.columns]), use_container_width=True)

elif section.startswith("📊"):
    st.subheader("📊 Reporte de Ventas")
    rango = st.selectbox("Rango de fechas", ["Hoy", "Última semana", "Último mes"])
    if rango == "Hoy":
        fecha_ini = hoy
    elif rango == "Última semana":
        fecha_ini = hoy - timedelta(days=7)
    else:
        fecha_ini = hoy - timedelta(days=30)
    ventas = df_prendas_raw[(df_prendas_raw["Vendida"] == True) & (pd.to_datetime(df_prendas_raw["Fecha Vendida"], dayfirst=True, errors='coerce') >= fecha_ini)]
    st.dataframe(clean_prendas(ventas), use_container_width=True)
    if st.button("📥 Descargar PDF Ventas") and not ventas.empty:
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        fname = f"ventas_{ts}.pdf"
        make_pdf_table("Ventas", clean_prendas(ventas), fname)
        with open(fname, "rb") as f:
            st.download_button("Descargar PDF", f, fname)

elif section.startswith("📝"):
    st.subheader("📝 Informe por Entregas")
    nombre = st.text_input("Nombre cliente")
    if st.button("Buscar entregas") and nombre:
        res = df_clientes[df_clientes["Nombre y Apellidos"].str.contains(nombre, case=False, na=False)]
        if res.empty:
            st.warning("No se encontró el cliente.")
        else:
            cli = res.iloc[0]
            idc = cli["ID Cliente"]
            prendas_cli = df_prendas_raw[df_prendas_raw["Nº Cliente (Formato C-xxx)"] == idc]
            entrega_fechas = prendas_cli.groupby("Fecha de recepción").size().reset_index(name="Nº Prendas")
            st.dataframe(entrega_fechas)
            if st.button("📥 Generar PDF informe cliente"):
                ts = datetime.now().strftime("%Y%m%d_%H%M")
                fname = f"informe_{idc}_{ts}.pdf"
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(0, 10, f"Cliente: {cli['Nombre y Apellidos']} ({idc})", ln=True)
                pdf.cell(0, 10, f"Teléfono: {cli['Teléfono']}", ln=True)
                pdf.ln(5)
                pdf.cell(0, 10, "Entregas:", ln=True)
                for _, row in entrega_fechas.iterrows():
                    pdf.cell(0, 8, f"{row['Fecha de recepción']}  -  {row['Nº Prendas']} prenda(s)", ln=True)
                pdf.ln(4)
                pdf.cell(0, 10, "Detalle de Prendas:", ln=True)
                for _, row in clean_prendas(prendas_cli).iterrows():
                    pdf.cell(0, 8, f"{row['ID Prenda']}  |  {row['Tipo de prenda']}  |  Vendida: {row['Vendida']} | Precio: {row.get('Precio',0)}", ln=True)
                pdf.output(fname)
                with open(fname, "rb") as f:
                    st.download_button("Descargar PDF", f, fname)

# === FOOTER ===============================================================
st.markdown("<br><div style='text-align:center;'>💖 Nirvana Vintage 2025</div>", unsafe_allow_html=True)
