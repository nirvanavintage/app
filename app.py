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

    columnas_finales = []
    if {'ID Prenda', 'Nº Cliente (Formato C-xxx)', 'Fecha de recepción', 'Tipo de prenda', 'Talla', 'Características (Color, estampado, material...)', 'Precio', 'Vendida', 'Fecha Vendida'}.issubset(df.columns):
        df['Cliente'] = df['Nº Cliente (Formato C-xxx)']
        df['Recepción'] = df['Fecha de recepción']
        df['Descripción'] = df['Tipo de prenda'].fillna('') + \
                            ', Talla: ' + df['Talla'].fillna('') + \
                            ', ' + df['Características (Color, estampado, material...)'].fillna('')
        df['Precio'] = pd.to_numeric(df['Precio'], errors='coerce').fillna(0).map(lambda x: f"{x:,.0f} €".replace(",", "."))
        df['Vendida'] = df.apply(lambda row: f"✔ {row['Fecha Vendida']}" if str(row['Vendida']).lower() == 'true' else '✖', axis=1)
        columnas_finales = ['ID Prenda', 'Cliente', 'Recepción', 'Vendida', 'Descripción', 'Precio']
        df = df[columnas_finales]
    else:
        df = df.astype(str).fillna("")

    df = df.astype(str).fillna("")

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, clean_text(titulo), ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", size=8)

    col_widths = {}
    total_width = 277
    fixed_widths = {
        'ID Prenda': 25,
        'Cliente': 25,
        'Recepción': 28,
        'Vendida': 32,
        'Descripción': 120,
        'Precio': 25
    }
    for col in df.columns:
        col_widths[col] = fixed_widths.get(col, total_width / len(df.columns))

    for col in df.columns:
        pdf.cell(col_widths[col], 6, clean_text(col), border=1, ln=0)
    pdf.ln()

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
    "Reporte Diario"
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
    st.error("❌ No se pudieron cargar los datos. Revisa conexión o permisos de la hoja.")
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
            prendas_ventas = prendas_cliente[prendas_cliente['Vendida'] == True]
            if not prendas_ventas.empty:
                if st.button("📄 PDF Informe del Cliente"):
                    fecha = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                    nombre_cliente = clientes_match.iloc[0]["Nombre y Apellidos"]
                    idc = clientes_match.iloc[0]["ID Cliente"]
                    titulo = f"Informe del cliente {idc} – {nombre_cliente}"

                    prendas_en_stock = prendas_cliente[prendas_cliente['Vendida'] != True]
                    lotes = prendas_cliente.copy()
                    lotes['Precio'] = pd.to_numeric(lotes['Precio'], errors='coerce').fillna(0)
                    lotes['Fecha de recepción'] = pd.to_datetime(lotes['Fecha de recepción'], errors='coerce')
                    resumen_lotes = lotes.groupby('Fecha de recepción').agg(
                        Total_Prendas=('ID Prenda', 'count'),
                        Valor_Total=('Precio', 'sum')
                    ).reset_index()
                    resumen_lotes = resumen_lotes.sort_values('Fecha de recepción', ascending=False)
                    resumen_lotes['Fecha de recepción'] = resumen_lotes['Fecha de recepción'].dt.strftime('%d/%m/%Y')
                    resumen_lotes['Valor_Total'] = resumen_lotes['Valor_Total'].apply(lambda x: f"{x:,.0f} €".replace(",", "."))

                    pdf = FPDF(orientation="L", unit="mm", format="A4")
                    pdf.set_auto_page_break(auto=True, margin=15)
                    pdf.add_page()
                    pdf.set_font("Helvetica", "B", 14)
                    pdf.cell(0, 10, clean_text(titulo), ln=True, align="C")
                    pdf.ln(4)
                    pdf.set_font("Helvetica", size=8)

                    def exportar_bloque(df, titulo):
                        if df.empty:
                            pdf.cell(0, 6, "Sin datos.", ln=True)
                        else:
                            df = limpiar_df(df).astype(str).fillna("")
                            col_w = pdf.w / (len(df.columns) + 1)
                            for col in df.columns:
                                pdf.cell(col_w, 6, clean_text(col), border=1)
                            pdf.ln()
                            for _, row in df.iterrows():
                                for item in row:
                                    pdf.cell(col_w, 5, clean_text(item), border=1)
                                pdf.ln()
                        pdf.ln(6)

                    pdf.set_font("Helvetica", "B", 10)
                    pdf.cell(0, 8, "🟢 Prendas Vendidas", ln=True)
                    pdf.set_font("Helvetica", size=8)
                    exportar_bloque(prendas_ventas, "Vendidas")

                    pdf.set_font("Helvetica", "B", 10)
                    pdf.cell(0, 8, "🟡 Prendas en stock", ln=True)
                    pdf.set_font("Helvetica", size=8)
                    exportar_bloque(prendas_en_stock, "En stock")

                    pdf.set_font("Helvetica", "B", 10)
                    pdf.cell(0, 8, "📦 Lotes de Entrega", ln=True)
                    pdf.set_font("Helvetica", size=8)
                    exportar_bloque(resumen_lotes, "Lotes")

                    total_ventas = lotes[lotes['Vendida'] == True]['Precio'].sum()
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.cell(0, 8, f"💰 Total vendido: {total_ventas:,.0f} €".replace(",", "."), ln=True)

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        pdf.output(tmp.name)
                        tmp.seek(0)
                        st.download_button("📄 Descargar PDF Informe Cliente", tmp.read(), file_name=f"cliente_{idc}_{fecha}.pdf", mime="application/pdf")
                        os.unlink(tmp.name)

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
    fecha_seleccionada = st.date_input("Selecciona una fecha para el reporte", value=datetime.today().date())
    fecha_dt = pd.to_datetime(fecha_seleccionada)
    vendidos_fecha = prendas_limpio[df_prendas["Vendida"] & (pd.to_datetime(df_prendas["Fecha Vendida"], errors="coerce").dt.normalize() == fecha_dt)]
    st.subheader(f"✅ Prendas Vendidas el {fecha_dt.date()} ({len(vendidos_fecha)})")
    st.dataframe(vendidos_fecha, use_container_width=True)

    if st.button("📄 PDF Ventas de la Fecha"):
        fecha_str = fecha_dt.strftime("%Y-%m-%d")
        hora_str = datetime.now().strftime("%H%M%S")
        titulo = f"Ventas del día {fecha_str}"
        df_to_pdf(vendidos_fecha, titulo, f"ventas_{fecha_str}_{hora_str}.pdf")
