import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta

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

seccion = st.sidebar.radio(
    "🪄 Secciones",
    [
        "Buscar Cliente",
        "Consultar Stock",
        "Consultar Vendidos",
        "Generar Avisos de Hoy",
        "Reporte Diario",
        "Informe Cliente por Entregas",
    ],
    index=0,
)

# --------------
# Buscar Cliente
# --------------
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

# ----------------
# Consultar Stock
# ----------------
elif seccion == "Consultar Stock":
    st.subheader("🍋 Stock Actual")
    stock = prendas_limpio[~df_prendas["Vendida"]]
    st.dataframe(stock, use_container_width=True)

# ------------------
# Consultar Vendidos
# ------------------
elif seccion == "Consultar Vendidos":
    st.subheader("✅ Prendas Vendidas")
    vendidos = prendas_limpio[df_prendas["Vendida"]]
    st.dataframe(vendidos, use_container_width=True)

# ----------------------
# Generar Avisos de Hoy
# ----------------------
elif seccion == "Generar Avisos de Hoy":
    hoy = pd.Timestamp.today().normalize()
    avisos_hoy = prendas_limpio[pd.to_datetime(df_prendas["Fecha Aviso"], errors="coerce").dt.normalize() == hoy]
    st.subheader(f"📣 Avisos para {hoy.date()}: {len(avisos_hoy)}")
    st.dataframe(avisos_hoy, use_container_width=True)

# --------------
# Reporte Diario
# --------------
elif seccion == "Reporte Diario":
    hoy = pd.Timestamp.today().normalize()
    stock = prendas_limpio[~df_prendas["Vendida"]]
    vendidos_hoy = prendas_limpio[(df_prendas["Vendida"]) & (pd.to_datetime(df_prendas["Fecha Vendida"], errors="coerce").dt.normalize() == hoy)] if "Fecha Vendida" in df_prendas else pd.DataFrame()
    avisos_hoy = prendas_limpio[pd.to_datetime(df_prendas["Fecha Aviso"], errors="coerce").dt.normalize() == hoy]

    st.markdown("## Avisos de Hoy")
    st.dataframe(avisos_hoy, use_container_width=True)

    st.markdown("## Ventas de Hoy")
    st.dataframe(vendidos_hoy, use_container_width=True)

    st.markdown("## Stock Actual")
    st.dataframe(stock, use_container_width=True)

    if st.button("📄 PDF Reporte Diario"):
        pdf = FPDF(orientation="L")
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Reporte Diario - {hoy.date()}", ln=True, align="C")
        pdf.ln(4)

        def tabla(df, titulo):
            pdf.set_font("Arial", style="B", size=11)
            pdf.cell(0, 8, titulo, ln=True)
            pdf.set_font("Arial", size=9)
            col_w = pdf.w / (len(df.columns) + 1)
            for col in df.columns:
                pdf.cell(col_w, 6, col, border=1)
            pdf.ln()
            for _, row in df.iterrows():
                for item in row:
                    pdf.cell(col_w, 5, str(item), border=1)
                pdf.ln()
            pdf.ln(4)

        tabla(avisos_hoy, "Avisos de Hoy")
        tabla(vendidos_hoy, "Ventas de Hoy")
        tabla(stock, "Stock Actual")

        fname = f"reporte_{hoy.strftime('%Y-%m-%d_%H%M%S')}.pdf"
        pdf.output(fname)
        with open(fname, "rb") as f:
            st.download_button("Descargar", f, file_name=fname, mime="application/pdf")

# ---------------------------------
# Informe Cliente por Entregas (Lote)
# ---------------------------------
else:
    nombre = st.text_input("Nombre cliente")
    if st.button("Buscar entregas") and nombre:
        cliente = df_clientes[df_clientes["Nombre y Apellidos"].str.contains(nombre, case=False, na=False)]
        if cliente.empty:
            st.warning("No se encontró el cliente.")
        else:
            idc = cliente.iloc[0]["ID Cliente"]
            prendas_cliente = prendas_limpio[prendas_limpio["Nº Cliente (Formato C-xxx)"] == idc]
            st.dataframe(prendas_cliente, use_container_width=True)
            if st.button("📄 PDF Informe Cliente"):
                pdf = FPDF(orientation="L")
                pdf.add_page()
                pdf.set_font("Arial", style="B", size=12)
                pdf.cell(0, 8, f"Informe Cliente – {cliente.iloc[0]['Nombre y Apellidos']} ({idc})", ln=True)
                pdf.set_font("Arial", size=9)
                pdf.ln(4)

                col_w = pdf.w / (len(prendas_cliente.columns) + 1)
                for col in prendas_cliente.columns:
                    pdf.cell(col_w, 6, col, border=1)
                pdf.ln()
                for _, row in prendas_cliente.iterrows():
                    for item in row:
                        pdf.cell(col_w, 5, str(item), border=1)
                    pdf.ln()

                fname = f"informe_{idc}_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.pdf"
                pdf.output(fname)
                with open(fname, "rb") as f:
                    st.download_button("Descargar", f, file_name=fname, mime="application/pdf")

st.markdown("---")
st.markdown("<div style='text-align:center'>❤️ Nirvana Vintage 2025</div>", unsafe_allow_html=True)
