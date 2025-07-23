import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, date
from fpdf import FPDF
from io import BytesIO
import unicodedata
import base64
import tempfile  

import pandas as pd
import os
from datetime import datetime
RUTA_CLIENTES = "clientes.csv"
RUTA_PRENDAS = "prendas.csv"

# --- Generador de Etiquetas ---
from fpdf import FPDF

class EtiquetaPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='L', unit='mm', format='A4')
        self.set_auto_page_break(auto=False)

    def add_etiqueta_grande(self, precio, talla, cliente, prenda_id):
        self.add_page()
        self.set_xy(0, 50)

        # Precio grande
        self.set_font("Arial", 'B', 48)
        self.cell(297, 25, f"EUR {precio}", ln=True, align="C")

        # Talla
        self.set_font("Arial", 'B', 36)
        self.cell(297, 20, f"Talla {talla}", ln=True, align="C")

        # Cliente y Prenda
        self.set_font("Arial", '', 24)
        self.cell(297, 15, f"Cliente: {cliente}", ln=True, align="C")
        self.cell(297, 15, f"Prenda: {prenda_id}", ln=True, align="C")

COLUMNAS_CLIENTES = [
    "ID Cliente", "Nombre y Apellidos", "Teléfono", "Fecha de Alta", "Número Formulario"
]

COLUMNAS_PRENDAS = [
    "ID Prenda", "Nº Cliente (Formato C-xxx)", "Tipo de prenda", "Talla", "Precio",
    "¿Donación o devolución?", "Fecha de recepción", "¿Lujo?", "% Beneficio Cliente",
    "Vendida", "Fecha Vendida", "Fecha Aviso"
]

# Crear si no existen
if not os.path.exists(RUTA_CLIENTES):
    pd.DataFrame(columns=COLUMNAS_CLIENTES).to_csv(RUTA_CLIENTES, index=False)

if not os.path.exists(RUTA_PRENDAS):
    pd.DataFrame(columns=COLUMNAS_PRENDAS).to_csv(RUTA_PRENDAS, index=False)

# Carga
df_clientes = pd.read_csv(RUTA_CLIENTES)
df_prendas = pd.read_csv(RUTA_PRENDAS)

def texto_fpdf(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")

st.set_page_config(page_title="Nirvana Vintage", page_icon="✨", layout="wide")

# --- Título y botones externos ---
st.markdown("""
<style>
h1 {
    text-align: center;
    font-size: 36px;
    color: #fdd835;
    font-weight: bold;
    margin-bottom: 20px;
}
.link-buttons {
    text-align: center;
    margin-bottom: 40px;
}
.link-buttons a {
    margin: 0 10px;
    padding: 10px 20px;
    background-color: #262730;
    color: white;
    border-radius: 8px;
    text-decoration: none;
    font-weight: bold;
    border: 1px solid #444;
    display: inline-block;
}
.link-buttons a:hover {
    background-color: #444;
}
</style>

<h1>✨ Nirvana Vintage: Gestión Diaria ✨</h1>
""", unsafe_allow_html=True)

# --- Archivos locales ---
archivo_prendas = "prendas.csv"
archivo_clientes = "clientes.csv"

# --- Crear si no existen ---
if not os.path.exists(archivo_prendas):
    columnas_prendas = [
        "ID Prenda", "Nº Cliente (Formato C-xxx)", "Tipo de prenda", "Talla",
        "Marca", "Caracteristicas (Color, estampado, material...)", "Precio",
        "Fecha de recepción", "Vendida", "Fecha Vendida", "Fecha Aviso"
    ]
    pd.DataFrame(columns=columnas_prendas).to_csv(archivo_prendas, index=False)

if not os.path.exists(archivo_clientes):
    columnas_clientes = ["ID Cliente", "Nombre", "Teléfono", "Email", "Fecha Alta"]
    pd.DataFrame(columns=columnas_clientes).to_csv(archivo_clientes, index=False)

# --- Cargar datos ---
df_prendas = pd.read_csv(archivo_prendas)
df_clientes = pd.read_csv(archivo_clientes)


# Sección inicializada para evitar NameError
if "seccion" not in st.session_state:
    st.session_state.seccion = ""

col1, col2, col3 = st.columns([1, 1, 1])

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("➕ Añadir Prenda"):
        st.session_state.seccion = "Añadir Prenda"
    if st.button("🔍 Añadir Cliente"):
        st.session_state.seccion = "Añadir Cliente"
    if st.button("✔️ Marcar Vendida"):
        st.session_state.seccion = "Marcar Vendida"


with col2:
    if st.button("📦 Consultar Stock"):
        st.session_state.seccion = "Consultar Stock"
    if st.button("✅ Consultar Vendidos"):
        st.session_state.seccion = "Consultar Vendidos"
    if st.button("🏷️ Generador de Etiquetas"):
        st.session_state.seccion = "Generador de Etiquetas"

with col3:
    if st.button("📑 Reporte Diario"):
        st.session_state.seccion = "Reporte Diario"
    if st.button("📅 Gestión de Citas"):
        st.session_state.seccion = "Gestión de Citas"
    if st.button("📩 Avisos"):
        st.session_state.seccion = "Avisos"

# Si no hay sección seleccionada aún
if not st.session_state.seccion:
    st.info("Selecciona una sección para comenzar.")
    st.stop()

# Guardamos la sección activa
seccion = st.session_state.seccion

# Conversión de datos (ya cargados desde CSV)
df_prendas["Vendida"] = df_prendas["Vendida"].astype(str).str.lower().isin(["true", "1", "yes", "x"])
df_prendas["Fecha Vendida"] = pd.to_datetime(df_prendas["Fecha Vendida"], errors="coerce")
df_prendas["Fecha de recepción"] = pd.to_datetime(df_prendas["Fecha de recepción"], errors="coerce")

if seccion == "Añadir Cliente":
    st.header("🆕 Alta de Cliente")

    nombre = st.text_input("Nombre y Apellidos")
    telefono = st.text_input("Teléfono")
    num_formulario = st.text_input("Número de Formulario")

    if st.button("Guardar Cliente"):
        if not nombre or not telefono or not num_formulario:
            st.warning("Completa todos los campos.")
        else:
            # ID Cliente único
            existentes = df_clientes["ID Cliente"].dropna().tolist()
            i = 1
            while f"C-{i:03}" in existentes:
                i += 1
            nuevo_id = f"C-{i:03}"

            nuevo_cliente = {
                "ID Cliente": nuevo_id,
                "Nombre y Apellidos": nombre,
                "Teléfono": telefono,
                "Fecha de Alta": date.today().isoformat(),
                "Número Formulario": num_formulario
            }

            df_clientes.loc[len(df_clientes)] = nuevo_cliente
            df_clientes.to_csv(RUTA_CLIENTES, index=False)
            st.success(f"Cliente {nuevo_id} guardado.")
elif seccion == "Añadir Prenda":
    st.header("👕 Añadir Nueva Prenda")

    clientes_disponibles = df_clientes["ID Cliente"].dropna().unique().tolist()
    cliente = st.selectbox("Cliente (ID)", sorted(clientes_disponibles))
    tipo = st.text_input("Tipo de prenda")
    talla = st.text_input("Talla")
    precio = st.number_input("Precio (€)", min_value=0.0, step=0.5)
    origen = st.selectbox("¿Donación o devolución?", ["Donación", "Devolución"])
    lujo = st.checkbox("¿Es de lujo?")
    porcentaje = st.slider("Porcentaje beneficio para el cliente", 0, 100, 30)

    if st.button("Guardar Prenda"):
        if not cliente or not tipo or not talla:
            st.warning("Completa todos los campos necesarios.")
        else:
            existentes = df_prendas["ID Prenda"].dropna().tolist()
            i = 1
            while f"P-{i:03}" in existentes:
                i += 1
            nuevo_id = f"P-{i:03}"

            nueva_prenda = {
                "ID Prenda": nuevo_id,
                "Nº Cliente (Formato C-xxx)": cliente,
                "Tipo de prenda": tipo,
                "Talla": talla,
                "Precio": precio,
                "¿Donación o devolución?": origen,
                "Fecha de recepción": date.today().isoformat(),
                "¿Lujo?": "Sí" if lujo else "No",
                "% Beneficio Cliente": porcentaje,
                "Vendida": False,
                "Fecha Vendida": "",
                "Fecha Aviso": ""
            }

            df_prendas.loc[len(df_prendas)] = nueva_prenda
            df_prendas.to_csv(RUTA_PRENDAS, index=False)
            st.success(f"Prenda {nuevo_id} guardada.")
elif seccion == "Marcar Vendida":
    st.header("✔️ Marcar Prenda como Vendida")

    id_prenda = st.text_input("Introduce el código de la prenda (ej: P-014)")

    if st.button("✅ Marcar como vendida"):
        idx = df_prendas[df_prendas["ID Prenda"] == id_prenda].index
        if idx.empty:
            st.warning("⚠️ No se encontró ninguna prenda con ese código.")
        else:
            df_prendas.loc[idx, "Vendida"] = True
            df_prendas.loc[idx, "Fecha Vendida"] = date.today().isoformat()
            df_prendas.to_csv(RUTA_PRENDAS, index=False)
            st.success(f"✅ Prenda {id_prenda} marcada como vendida.")

elif seccion == "Consultar Stock":
    st.header("📦 Prendas en Stock")

    try:
        df_prendas = pd.read_csv("prendas.csv")
    except FileNotFoundError:
        st.error("❌ No se encontró el archivo local de prendas.")
        st.stop()

    df_prendas["Vendida"] = df_prendas["Vendida"].astype(str).str.lower().isin(["true", "1", "yes", "x", "sí"])

    stock = df_prendas[df_prendas["Vendida"] != True].copy()

    stock["Fecha de recepción"] = pd.to_datetime(stock["Fecha de recepción"], errors="coerce").dt.strftime("%d/%m/%Y")
    stock["Descripción"] = stock.apply(
        lambda row: f"{row.get('Tipo de prenda', '')} | Talla {row.get('Talla', '')} | Marca {row.get('Marca', '') or 'Sin marca'} | Características: {row.get('Caracteristicas (Color, estampado, material...)', '') or 'Sin descripción'}",
        axis=1
    )

    columnas_filtro = [col for col in ["Talla", "Tipo de prenda", "Marca", "¿Donación o devolución?"] if col in stock.columns]

    with st.expander("⚙️ Filtros"):
        for columna in columnas_filtro:
            opciones = stock[columna].dropna().unique().tolist()
            seleccion = st.multiselect(f"Filtrar por {columna}", opciones, default=[])
            if seleccion:
                stock = stock[stock[columna].isin(seleccion)]

    columnas_visibles = ["ID Prenda", "Nº Cliente (Formato C-xxx)", "Fecha de recepción", "Precio", "Descripción"]
    st.dataframe(stock[columnas_visibles], use_container_width=True)

    if st.button("⬇️ Descargar Excel Stock"):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            stock[columnas_visibles].to_excel(writer, index=False, sheet_name="Stock")
        buffer.seek(0)
        st.download_button("Descargar Stock Excel", buffer, file_name="stock_filtrado.xlsx")

    if st.button("🖨️ Descargar PDF Stock"):
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Stock de Prendas (filtrado)", ln=True, align='C')
        pdf.ln(5)

        col_widths = [35, 50, 35, 20, 100]

        pdf.set_font("Arial", 'B', 10)
        for i, col in enumerate(columnas_visibles):
            pdf.cell(col_widths[i], 8, texto_fpdf(col), border=1)
        pdf.ln()

        pdf.set_font("Arial", '', 9)
        for _, row in stock[columnas_visibles].iterrows():
            for i, col in enumerate(columnas_visibles):
                texto = str(row[col]) if pd.notna(row[col]) else ""
                if col == "Descripción":
                    y_before = pdf.get_y()
                    x_before = pdf.get_x()
                    pdf.multi_cell(col_widths[i], 8, texto_fpdf(texto), border=1)
                    y_after = pdf.get_y()
                    pdf.set_y(y_before)
                    pdf.set_x(x_before + col_widths[i])
                else:
                    pdf.cell(col_widths[i], 8, texto_fpdf(texto), border=1)
            pdf.ln()

        buffer = BytesIO()
        pdf_output = pdf.output(dest='S').encode('latin-1')
        buffer.write(pdf_output)

        buffer.seek(0)
        st.download_button("⬇️ Descargar PDF", buffer.getvalue(), file_name="stock_filtrado.pdf")

elif seccion == "Consultar Vendidos":
    st.header("✅ Prendas Vendidas")

    try:
        df_prendas = pd.read_csv("prendas.csv")
    except FileNotFoundError:
        st.error("❌ No se encontró el archivo local de prendas.")
        st.stop()

    df_prendas["Vendida"] = df_prendas["Vendida"].astype(str).str.lower().isin(["true", "1", "yes", "x", "sí"])
    vendidos = df_prendas[df_prendas["Vendida"] == True].copy()
    vendidos["Fecha Vendida"] = pd.to_datetime(vendidos["Fecha Vendida"], errors="coerce")
    vendidos["Fecha Formateada"] = vendidos["Fecha Vendida"].dt.strftime("%d/%m/%Y")

    with st.expander("📅 Filtrar por Fecha de Venta"):
        col1, col2 = st.columns(2)
        fecha_unica = col1.date_input("Filtrar por un día exacto", value=None)
        fecha_inicio = col2.date_input("O por rango: Desde", value=None)
        fecha_fin = col2.date_input("Hasta", value=None)

        if fecha_unica:
            vendidos = vendidos[vendidos["Fecha Vendida"].dt.date == fecha_unica]
        elif fecha_inicio and fecha_fin:
            vendidos = vendidos[(vendidos["Fecha Vendida"].dt.date >= fecha_inicio) & 
                                (vendidos["Fecha Vendida"].dt.date <= fecha_fin)]

    vendidos["Descripción"] = vendidos.apply(
        lambda row: f"{row.get('Tipo de prenda', '')} | Talla {row.get('Talla', '')} | Marca {row.get('Marca', '') or 'Sin marca'} | Características: {row.get('Caracteristicas (Color, estampado, material...)', '') or 'Sin descripción'}",
        axis=1
    )

    columnas_filtro = [col for col in ["Talla", "Tipo de prenda", "Marca", "¿Donación o devolución?"] if col in vendidos.columns]
    with st.expander("⚙️ Otros Filtros"):
        for columna in columnas_filtro:
            opciones = vendidos[columna].dropna().unique().tolist()
            seleccion = st.multiselect(f"Filtrar por {columna}", opciones, default=[])
            if seleccion:
                vendidos = vendidos[vendidos[columna].isin(seleccion)]

    columnas_visibles = ["ID Prenda", "Nº Cliente (Formato C-xxx)", "Fecha Formateada", "Precio", "Descripción"]
    st.dataframe(vendidos[columnas_visibles], use_container_width=True)

    if st.button("⬇️ Descargar Excel Vendidos"):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            vendidos[columnas_visibles].to_excel(writer, index=False, sheet_name="Vendidos")
        buffer.seek(0)
        st.download_button("Descargar Excel", buffer, file_name="vendidos_filtrado.xlsx")

    if st.button("🖨️ Descargar PDF Vendidos"):
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Prendas Vendidas (filtrado)", ln=True, align='C')
        pdf.ln(5)

        col_widths = [35, 50, 35, 20, 110]

        pdf.set_font("Arial", 'B', 10)
        for i, col in enumerate(columnas_visibles):
            pdf.cell(col_widths[i], 8, texto_fpdf(col), border=1)
        pdf.ln()

        pdf.set_font("Arial", '', 9)
        for _, row in vendidos[columnas_visibles].iterrows():
            for i, col in enumerate(columnas_visibles):
                texto = str(row[col]) if pd.notna(row[col]) else ""
                if col == "Descripción":
                    y_before = pdf.get_y()
                    x_before = pdf.get_x()
                    pdf.multi_cell(col_widths[i], 8, texto_fpdf(texto), border=1)
                    y_after = pdf.get_y()
                    pdf.set_y(y_before)
                    pdf.set_x(x_before + col_widths[i])
                else:
                    pdf.cell(col_widths[i], 8, texto_fpdf(texto), border=1)
            pdf.ln()

        buffer = BytesIO()
        pdf_output = pdf.output(dest='S').encode('latin-1')
        buffer.write(pdf_output)

        buffer.seek(0)
        st.download_button("⬇️ Descargar PDF", buffer.getvalue(), file_name="vendidos_filtrado.pdf")

elif seccion == "Generador de Etiquetas":
    st.markdown("### 🏷️ Generador de Etiquetas")
    hoy = pd.Timestamp.today().normalize()
    fecha_hoy_str = hoy.strftime("%Y-%m-%d")

    try:
        df_prendas = pd.read_csv("prendas.csv")
    except FileNotFoundError:
        st.error("❌ No se encontró el archivo local de prendas.")
        st.stop()

    df_prendas["Fecha Vendida"] = pd.to_datetime(df_prendas["Fecha Vendida"], errors='coerce')
    codigos_disponibles = df_prendas["ID Prenda"].dropna().unique().tolist()
    cod = st.selectbox("Selecciona una prenda (formato P-XXX)", sorted(codigos_disponibles))

    st.markdown("#### 🔹 Generar una sola etiqueta")
        if cod and st.button("Generar etiqueta única"):
        prenda = df_prendas[df_prendas["ID Prenda"] == cod]
        if not prenda.empty:
            st.dataframe(prenda)
            row = prenda.iloc[0]

            precio = str(row.get("Precio", ""))
            talla = row.get("Talla", "")
            cliente = row.get("Nº Cliente (Formato C-xxx)", "")
            prenda_id = row.get("ID Prenda", "")

            pdf = EtiquetaPDF()
            pdf.add_etiqueta_grande(precio, talla, cliente, prenda_id)

            buffer = BytesIO()
            pdf_output = pdf.output(dest='S').encode('latin-1')
            buffer.write(pdf_output)
            buffer.seek(0)

            st.download_button(
                "⬇️ Descargar Etiqueta",
                buffer.getvalue(),
                file_name=f"etiqueta_{prenda_id}_{fecha_hoy_str}.pdf"
            )

    st.markdown("#### 🔹 Generar etiquetas de productos vendidos hoy")
    vendidas_hoy = df_prendas[df_prendas["Fecha Vendida"].dt.normalize() == hoy]

    if not vendidas_hoy.empty:
        st.dataframe(vendidas_hoy)

        if st.button("⬇️ Generar PDF etiquetas del día"):
            pdf = EtiquetaPDF()
            for _, row in vendidas_hoy.iterrows():
                precio = str(row.get("Precio", ""))
                talla = row.get("Talla", "")
                cliente = row.get("Nº Cliente (Formato C-xxx)", "")
                prenda_id = row.get("ID Prenda", "")
                pdf.add_etiqueta(precio, talla, cliente, prenda_id)

            buffer = BytesIO()
            pdf_output = pdf.output(dest='S').encode('latin-1')
            buffer.write(pdf_output)
            buffer.seek(0)

            st.download_button(
                "⬇️ Descargar Etiquetas Vendidas Hoy",
                buffer.getvalue(),
                file_name=f"etiquetas_vendidas_{fecha_hoy_str}.pdf"
            )
    else:
        st.info("No hay prendas vendidas hoy para generar etiquetas.")
elif seccion == "Reporte Diario": 
    st.header("📑 Reporte Diario")

    # Carga desde archivos locales
    try:
        df_prendas = pd.read_csv("prendas.csv")
        df_clientes = pd.read_csv("clientes.csv")
    except FileNotFoundError:
        st.error("❌ No se encuentran los archivos locales 'prendas.csv' y/o 'clientes.csv'")
        st.stop()

    fecha_reporte = st.date_input("Selecciona la fecha", pd.Timestamp.today(), format="YYYY/MM/DD")
    hoy = pd.Timestamp(fecha_reporte).normalize()

    # --- Ventas del día ---
    df_prendas["Fecha Vendida"] = pd.to_datetime(df_prendas["Fecha Vendida"], errors="coerce")
    ventas_dia = df_prendas[df_prendas["Fecha Vendida"].dt.normalize() == hoy]

    # Cálculos de totales
    total_ganado = ventas_dia["Precio"].sum()
    comision_clientes = (ventas_dia["Precio"] * 0.3).sum()
    total_neto = total_ganado - comision_clientes

    st.markdown(f"**💰 Total bruto (€):** {total_ganado:.2f}")
    st.markdown(f"**👛 Comisión clientes (30%):** {comision_clientes:.2f}")
    st.markdown(f"**📈 Total neto (€):** {total_neto:.2f}")

    # --- Nuevos clientes del día ---
    df_clientes = df_clientes.copy()

    # Eliminar columnas "Marca temporal" y "Merged..." si existen
    if "Marca temporal" in df_clientes.columns:
        df_clientes["Marca temporal"] = pd.to_datetime(df_clientes["Marca temporal"], errors="coerce")
        nuevas_altas = df_clientes[df_clientes["Marca temporal"].dt.normalize() == hoy]
    else:
        nuevas_altas = pd.DataFrame()

    columnas_merge = [col for col in df_clientes.columns if col.startswith("Merged")]
    df_clientes = df_clientes.drop(columns=columnas_merge, errors="ignore")

    st.subheader("🆕 Nuevos Clientes del Día")
    if not nuevas_altas.empty:
        st.dataframe(nuevas_altas)
    else:
        st.info("No hay nuevos clientes registrados ese día.")

    # --- Tabla de ventas ---
    columnas_visibles = ["ID Prenda", "Nº Cliente (Formato C-xxx)", "Tipo de prenda", "Talla", "Precio", "Fecha Vendida"]
    st.subheader("🛍️ Ventas del Día")
    st.dataframe(ventas_dia[columnas_visibles])

    # --- Exportar Excel ---
    if st.button("⬇️ Descargar Reporte en Excel"):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            ventas_dia[columnas_visibles].to_excel(writer, sheet_name="Ventas", index=False)
            nuevas_altas.to_excel(writer, sheet_name="Clientes", index=False)
        buffer.seek(0)
        st.download_button(
            label="Descargar Excel",
            data=buffer,
            file_name=f"reporte_diario_{hoy.date()}.xlsx"
        )

    # --- Exportar PDF ---
    if st.button("Descargar Reporte en PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Reporte Diario - {hoy.date()}", ln=True, align='C')
        pdf.ln(10)

        # Totales
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, f"Total ganado: EUR {total_ganado:.2f}", ln=True)
        pdf.cell(0, 8, f"Comisión clientes (30%): EUR {comision_clientes:.2f}", ln=True)
        pdf.cell(0, 8, f"Total neto: EUR {total_neto:.2f}", ln=True)
        pdf.ln(10)

        # Ventas del Día
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "Ventas del Día:", ln=True)

        if not ventas_dia.empty:
            pdf.set_font("Arial", '', 10)
            for _, row in ventas_dia.iterrows():
                try:
                    idp = str(row.get("ID Prenda", ""))
                    cliente = str(row.get("Nº Cliente (Formato C-xxx)", ""))
                    tipo = str(row.get("Tipo de prenda", ""))
                    talla = str(row.get("Talla", ""))
                    precio = str(row.get("Precio", ""))
                    fecha = row.get("Fecha Vendida")
                    fecha_str = pd.to_datetime(fecha, errors='coerce').strftime("%d/%m/%Y") if pd.notna(fecha) else "Fecha inválida"

                    linea = f"- {idp} | Cliente: {cliente} | {tipo} Talla {talla} | EUR {precio} | {fecha_str}"
                    pdf.cell(0, 6, linea, ln=True)
                except:
                    pdf.cell(0, 6, "Error al mostrar una venta.", ln=True)
        else:
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 6, "No hay ventas registradas ese día.", ln=True)

        # Altas del día
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "Nuevos clientes del día:", ln=True)

        if not nuevas_altas.empty:
            pdf.set_font("Arial", '', 10)
            for _, row in nuevas_altas.iterrows():
                try:
                    datos = [f"{col}: {str(row[col])}" for col in nuevas_altas.columns if pd.notna(row[col])]
                    linea = " | ".join(datos)
                    pdf.cell(0, 6, linea[:90], ln=True)  # cortar si es muy largo
                except:
                    pdf.cell(0, 6, "Error al mostrar un cliente.", ln=True)
        else:
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 6, "No hay nuevos clientes registrados ese día.", ln=True)

        buffer = BytesIO()
        pdf_output = pdf.output(dest='S').encode('latin-1')
        buffer.write(pdf_output)

        buffer.seek(0)
        st.download_button("⬇ Descargar PDF", buffer.getvalue(), file_name=f"reporte_diario_{hoy.date()}.pdf")
elif seccion == "Avisos":
    st.header("📢 Avisos a Clientes")

    # --- Cargar datos ---
    try:
        df_prendas = pd.read_csv("prendas.csv")
        df_clientes = pd.read_csv("clientes.csv")
    except FileNotFoundError:
        st.error("❌ Archivos 'prendas.csv' o 'clientes.csv' no encontrados.")
        st.stop()

    fecha_objetivo = st.date_input("Selecciona la fecha para los avisos", pd.Timestamp.today())

    # --- AVISOS POR FECHA DE AVISO ---
    st.subheader("📅 Prendas con Aviso en la Fecha Seleccionada")

    if "Fecha Aviso" in df_prendas.columns:
        df_aviso = df_prendas.copy()
        df_aviso["Fecha Aviso"] = pd.to_datetime(df_aviso["Fecha Aviso"], errors="coerce")
        df_aviso_filtrado = df_aviso[df_aviso["Fecha Aviso"].dt.normalize() == pd.Timestamp(fecha_objetivo)]

        if not df_aviso_filtrado.empty:
            for _, row in df_aviso_filtrado.iterrows():
                id_cliente = row.get("Nº Cliente (Formato C-xxx)", "")
                cliente_info = df_clientes[df_clientes["ID Cliente"] == id_cliente].squeeze()
                nombre = cliente_info.get("Nombre y Apellidos", "Desconocido")
                telefono = cliente_info.get("Teléfono", "No disponible")
                prenda = row.get("Tipo de prenda", "")
                talla = row.get("Talla", "")

                mensaje = f"Hola {nombre}, tu prenda ({prenda} talla {talla}) está a punto de caducar. ¿Deseas donarla o pasar a recogerla?"
                st.markdown(f"""
                **Cliente:** {nombre}  
                **Teléfono:** {telefono}  
                **Prenda:** {prenda} | Talla {talla}  
                **Mensaje sugerido:**""")
                st.code(mensaje)
                st.button(f"✅ Marcar mensaje como revisado", key=f"copy_{id_cliente}")
                st.divider()
        else:
            st.info("No hay prendas con aviso para esa fecha.")
    else:
        st.warning("La columna 'Fecha Aviso' no existe en el archivo de prendas.")

    # --- NUEVOS CLIENTES DEL DÍA ---
    st.subheader("🆕 Nuevos Clientes con Ficha")

    if "Fecha de Alta" in df_clientes.columns:
        df_clientes["Fecha de Alta"] = pd.to_datetime(df_clientes["Fecha de Alta"], errors="coerce")
        nuevos = df_clientes[df_clientes["Fecha de Alta"].dt.normalize() == pd.Timestamp(fecha_objetivo)]

        if not nuevos.empty:
            for _, cliente in nuevos.iterrows():
                idc = cliente["ID Cliente"]
                nombre = cliente.get("Nombre y Apellidos", "Sin nombre")
                telefono = cliente.get("Teléfono", "Sin número")
                prendas_cliente = df_prendas[df_prendas["Nº Cliente (Formato C-xxx)"] == idc]

                mensaje = f"Hola {nombre}, gracias por traer tus prendas a Nirvana. Aquí tienes tu ficha con lo que has entregado."
                st.markdown(f"""
                **Nombre:** {nombre}  
                **Teléfono:** {telefono}  
                **Mensaje sugerido:**""")
                st.code(mensaje)
                st.button(f"✅ Marcar mensaje como revisado", key=f"copy_new_{idc}")

                if not prendas_cliente.empty:
                    st.markdown("**Resumen de prendas entregadas:**")
                    for _, prenda in prendas_cliente.iterrows():
                        tipo = prenda.get("Tipo de prenda", "")
                        talla = prenda.get("Talla", "")
                        fecha_rec = prenda.get("Fecha de recepción", "")
                        st.markdown(f"- {tipo}, Talla {talla}, recibida el {fecha_rec}")
                else:
                    st.markdown("_No hay prendas asociadas._")
                st.divider()
        else:
            st.info("No hay nuevos clientes registrados ese día.")
    else:
        st.warning("La columna 'Fecha de Alta' no existe en el archivo de clientes.")
elif seccion == "Gestión de Citas":
    import os
    import pandas as pd
    from datetime import datetime, timedelta, date

    st.header("📅 Gestión de Citas")

    archivo_csv = "citas.csv"
    if not os.path.exists(archivo_csv):
        columnas = ["Fecha", "Hora Inicio", "Hora Fin", "Nombre", "Teléfono", "Tipo Visita", "Notas"]
        pd.DataFrame(columns=columnas).to_csv(archivo_csv, index=False)

    df_citas = pd.read_csv(archivo_csv)
    df_citas["Fecha"] = pd.to_datetime(df_citas["Fecha"], errors="coerce").dt.date
    df_citas["Hora Inicio"] = df_citas["Hora Inicio"].astype(str)
    df_citas["Hora Fin"] = df_citas["Hora Fin"].astype(str)

    if "semana_inicio" not in st.session_state:
        hoy = date.today()
        st.session_state.semana_inicio = hoy - timedelta(days=hoy.weekday())

    semana_inicio = st.session_state.semana_inicio
    semana_fin = semana_inicio + timedelta(days=6)

    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("⬅ Semana anterior"):
            st.session_state.semana_inicio -= timedelta(days=7)
            st.rerun()
    with col3:
        if st.button("Semana siguiente ➡"):
            st.session_state.semana_inicio += timedelta(days=7)
            st.rerun()

    st.markdown(f"### 🗓️ Semana: {semana_inicio.strftime('%d/%m/%Y')} - {semana_fin.strftime('%d/%m/%Y')}")
    st.markdown("### 📆 Calendario Semanal")

    intervalos = [(f"{h:02d}:00", f"{h:02d}:30") for h in range(10, 20)] + [(f"{h:02d}:30", f"{h+1:02d}:00") for h in range(10, 19)]
    intervalos = sorted(intervalos)
    dias_semana = [semana_inicio + timedelta(days=i) for i in range(7)]
    nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    seleccionado = None

    # Cabecera del calendario
    columnas = st.columns([1] + [1 for _ in range(7)])
    columnas[0].markdown("**Hora**")
    for i in range(7):
        columnas[i + 1].markdown(f"**{nombres_dias[i]}<br>{dias_semana[i].strftime('%d/%m')}**", unsafe_allow_html=True)

    for inicio, fin in intervalos:
        columnas = st.columns([1] + [1 for _ in range(7)])
        columnas[0].markdown(f"**{inicio} - {fin}**")
        for i, dia in enumerate(dias_semana):
            ocupado = df_citas[
                (df_citas["Fecha"] == dia) &
                (((df_citas["Hora Inicio"] <= inicio) & (df_citas["Hora Fin"] > inicio)) |
                 ((df_citas["Hora Inicio"] < fin) & (df_citas["Hora Fin"] >= fin)))
            ]
            if ocupado.empty:
                boton_key = f"{dia}_{inicio}_{fin}"
                if columnas[i + 1].button("Reservar", key=boton_key):
                    seleccionado = (dia, inicio, fin)
            else:
                nombre = ocupado.iloc[0]["Nombre"] if "Nombre" in ocupado.columns else "Ocupado"
                columnas[i + 1].markdown(f"<span style='color:red; font-weight:bold;'>❌ {nombre}</span>", unsafe_allow_html=True)

    if seleccionado:
        dia, inicio, fin = seleccionado
        st.subheader("➕ Reservar nueva cita")
        st.info(f"Reservando para el **{dia.strftime('%A %d/%m/%Y')}**, de **{inicio} a {fin}**")
        nombre = st.text_input("👤 Nombre")
        telefono = st.text_input("📞 Teléfono")
        tipo_visita = st.selectbox("🔁 Tipo de visita", ["Entrega", "Devolución"])
        notas = st.text_area("📝 Notas (opcional)")

        if st.button("✅ Confirmar reserva"):
            conflicto = df_citas[
                (df_citas["Fecha"] == dia) &
                (((df_citas["Hora Inicio"] <= inicio) & (df_citas["Hora Fin"] > inicio)) |
                 ((df_citas["Hora Inicio"] < fin) & (df_citas["Hora Fin"] >= fin)))
            ]
            if not conflicto.empty:
                st.error("❌ Ese hueco ya está ocupado.")
                st.stop()

            nueva = pd.DataFrame({
                "Fecha": [dia],
                "Hora Inicio": [inicio],
                "Hora Fin": [fin],
                "Nombre": [nombre],
                "Teléfono": [telefono],
                "Tipo Visita": [tipo_visita],
                "Notas": [notas]
            })
            df_citas = pd.concat([df_citas, nueva], ignore_index=True)
            df_citas.to_csv(archivo_csv, index=False)
            st.success("✅ Cita guardada correctamente.")
            st.rerun()
