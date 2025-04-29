import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from fpdf import FPDF
import unicodedata

# =====================
# Configuración general
# =====================

st.set_page_config(page_title="Nirvana Vintage", page_icon="✨", layout="wide")
HIDE_COLS_PATTERN = [
    "Marca temporal",
    "Merged Doc ID", "Merged Doc URL", "Link to merged Doc", "Document Merge Status"
]

# =====================
# Funciones auxiliares
# =====================

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
    cols_mostrar = [c for c in df.columns if c not in [
        "Marca temporal",
        *df.columns[df.columns.str.startswith("Merged Doc")]
    ]]
    df = df[cols_mostrar]

    pdfkit_usable = False
    try:
        import pdfkit
        if os.path.exists('/usr/bin/wkhtmltopdf'):
            config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
            pdfkit_usable = True
    except Exception:
        pdfkit_usable = False

    if pdfkit_usable:
        try:
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
                                   configuration=config,
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
            st.warning(f"No se pudo generar PDF bonito: {e}. Usando método alternativo.")

    # Backup con FPDF2
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
            "📄 Descargar PDF (simple)",
            tmp.read(),
            file_name=nombre_archivo,
            mime="application/pdf"
        )
        os.unlink(tmp.name)

# ========================
# Encabezado y navegación
# ========================

st.markdown("""
<h1 style='text-align:center'>✨ Nirvana Vintage: Gestión Diaria ✨</h1>
<div style='text-align:center'>
    <a href='https://forms.gle/QAXSH5ZP6oCpWEcL6' target='_blank'>📅 Nueva Prenda</a> |
    <a href='https://forms.gle/2BpmDNegKNTNc2dK6' target='_blank'>👤 Nuevo Cliente</a> |
    <a href='https://www.appsheet.com/start/e1062d5c-129e-4947-bed1-cbb925ad7209?platform=desktop#appName=Marcarcomovendido-584406513&view=Marcar%20como%20vendido' target='_blank'>🔄 App Marcar Vendido</a>
</div>
""", unsafe_allow_html=True)

# ===============
# Menú personalizado
# ===============
st.sidebar.markdown("""
    <style>
    .sidebar .sidebar-content {
        padding: 2rem 1rem;
    }
    .sidebar .css-1d391kg { font-size: 20px; font-weight: bold; }
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

# ========================
# Cargar datos
# ========================

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

# ========================
# Secciones funcionales
# ========================

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
    vendidos_hoy = prendas_limpio[(df_prendas["Vendida"]) & (pd.to_datetime(df_prendas["Fecha Vendida"], errors="coerce").dt.normalize() == hoy)] if "Fecha Vendida" in df_prendas else pd.DataFrame()
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
        df_full = pd.concat([
            pd.DataFrame({"__SECCIÓN__": ["Avisos de Hoy"]}),
            avisos_hoy,
            pd.DataFrame({"__SECCIÓN__": ["Ventas de Hoy"]}),
            vendidos_hoy,
            pd.DataFrame({"__SECCIÓN__": ["Stock Actual"]}),
            stock
        ])
        df_to_pdf(df_full, titulo, f"reporte_{fecha}.pdf")

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
