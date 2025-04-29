import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from fpdf import FPDF
from io import BytesIO
import unicodedata
import base64


def texto_fpdf(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")

st.set_page_config(page_title="Nirvana Vintage", page_icon="✨", layout="wide")

# Seguridad persistente
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <h1 style='text-align:center'>✨ Nirvana Vintage: Gestión Diaria ✨</h1>
    """, unsafe_allow_html=True)

    password = st.text_input("Contraseña:", type="password")
    if st.button("🔓 Entrar"):
        if password == "nirvana2025":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.warning("Contraseña incorrecta. Inténtalo de nuevo.")
    st.stop()

# Encabezado principal
st.markdown("""
<h1 style='text-align:center'>✨ Nirvana Vintage: Gestión Diaria ✨</h1>
<div style='text-align:center'>
    <a href='https://forms.gle/QAXSH5ZP6oCpWEcL6' target='_blank'>📅 Nueva Prenda</a> |
    <a href='https://forms.gle/2BpmDNegKNTNc2dK6' target='_blank'>👤 Nuevo Cliente</a> |
    <a href='https://www.appsheet.com/start/e1062d5c-129e-4947-bed1-cbb925ad7209?platform=desktop#appName=Marcarcomovendido-584406513&view=Marcar%20como%20vendido' target='_blank'>🔄 App Marcar Vendido</a>
</div>
""", unsafe_allow_html=True)

# Botón sincronizar
if st.button("🔄 Sincronizar datos desde Google Sheets"):
    st.cache_data.clear()
    st.rerun()

# Sidebar
seccion = st.sidebar.selectbox("Secciones", [
    "Buscar Cliente", "Consultar Stock", "Consultar Vendidos", "Reporte Diario", "Generador de Etiquetas"
])

# Datos
SHEET_ID = "1reTzFeErA14TRoxaA-PPD5OGfYYXH3Z_0i9bRQeLap8"
URL_BASE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="

@st.cache_data(show_spinner=False)
def cargar(sheet):
    return pd.read_csv(URL_BASE + sheet)

try:
    df_prendas = cargar("Prendas")
    df_clientes = cargar("Clientes")
except:
    st.error("❌ No se pudieron cargar los datos.")
    st.stop()

# Conversión
df_prendas["Vendida"] = df_prendas["Vendida"].astype(str).str.lower().isin(["true", "1", "yes", "x"])
df_prendas["Fecha Vendida"] = pd.to_datetime(df_prendas["Fecha Vendida"], errors="coerce")
df_prendas["Fecha de recepción"] = pd.to_datetime(df_prendas["Fecha de recepción"], errors="coerce")# --- Buscar Cliente ---
# --- Buscar Cliente ---
if seccion == "Buscar Cliente":
    st.header("🔍 Buscar Cliente")
    nombres_disponibles = df_clientes["Nombre y Apellidos"].dropna().unique().tolist()
    nombre = st.selectbox("Selecciona el cliente", sorted(nombres_disponibles))

    if nombre:
        resultados = df_clientes[df_clientes["Nombre y Apellidos"] == nombre]
        st.subheader("📄 Datos del Cliente")
        st.dataframe(resultados, use_container_width=True)

        if not resultados.empty:
            id_cliente = resultados.iloc[0].get("ID Cliente", "Desconocido")
            nombre_cliente = resultados.iloc[0].get("Nombre y Apellidos", "Sin Nombre")
            prendas_cliente = df_prendas[df_prendas["Nº Cliente (Formato C-xxx)"] == id_cliente]

            st.subheader("👜 Prendas del Cliente")
            st.dataframe(prendas_cliente, use_container_width=True)

            if st.button("📄 Descargar Informe Cliente"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, f"Informe del cliente {id_cliente} {nombre_cliente}", ln=True, align='C')
                pdf.ln(10)

                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, "Datos del cliente:", ln=True)
                for col in ["ID Cliente", "Teléfono", "Email", "Fecha de Alta", "DNI"]:
                    valor = resultados.iloc[0].get(col, "")
                    pdf.set_font("Arial", '', 11)
                    pdf.cell(0, 7, f"{col}: {valor}", ln=True)

                pdf.ln(5)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, "Prendas entregadas:", ln=True)

                if not prendas_cliente.empty:
                    prendas_cliente = prendas_cliente.sort_values("Fecha de recepción")
                    fecha_actual = None
                    for _, row in prendas_cliente.iterrows():
                        fecha_recepcion = row.get("Fecha de recepción")
                        if pd.notna(fecha_recepcion):
                            fecha_str = fecha_recepcion.strftime("%d/%m/%Y")
                            if fecha_str != fecha_actual:
                                pdf.ln(5)
                                pdf.set_font("Arial", 'B', 11)
                                pdf.cell(0, 7, f"Recepción: {fecha_str}", ln=True)
                                fecha_actual = fecha_str
                        pdf.set_font("Arial", '', 10)
                        descripcion = f"- {row.get('Tipo de prenda', '')} | Talla {row.get('Talla', '')} | {row.get('Caracteristicas (Color, estampado, material...)', '')}"
                        pdf.cell(0, 6, descripcion, ln=True)
                else:
                    pdf.set_font("Arial", '', 10)
                    pdf.cell(0, 6, "No hay prendas registradas para este cliente.", ln=True)

                buffer = BytesIO()
                pdf.output(buffer)
                buffer.seek(0)
                st.download_button("⬇️ Descargar PDF Informe", buffer.getvalue(), file_name=f"informe_cliente_{id_cliente}.pdf")
elif seccion == "Consultar Stock":
    st.header("📦 Prendas en Stock")

    stock = df_prendas[df_prendas["Vendida"] != True].copy()

    # Formatear fecha y crear columna de descripción agrupada
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

        col_widths = [35, 50, 35, 20, 100]  # Aumentado el ancho de Descripción

        pdf.set_font("Arial", 'B', 10)
        for i, col in enumerate(columnas_visibles):
            pdf.cell(col_widths[i], 8, col, border=1)
        pdf.ln()

        pdf.set_font("Arial", '', 9)
        for _, row in stock[columnas_visibles].iterrows():
            for i, col in enumerate(columnas_visibles):
                texto = str(row[col]) if pd.notna(row[col]) else ""
                if col == "Descripción":
                    y_before = pdf.get_y()
                    x_before = pdf.get_x()
                    pdf.multi_cell(col_widths[i], 8, texto, border=1)
                    y_after = pdf.get_y()
                    pdf.set_y(y_before)
                    pdf.set_x(x_before + col_widths[i])
                else:
                    pdf.cell(col_widths[i], 8, texto, border=1)
            pdf.ln()

        buffer = BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        st.download_button("⬇️ Descargar PDF", buffer.getvalue(), file_name="stock_filtrado.pdf")

elif seccion == "Consultar Vendidos":
    st.header("✅ Prendas Vendidas")

    vendidos = df_prendas[df_prendas["Vendida"] == True].copy()
    vendidos["Fecha Vendida"] = pd.to_datetime(vendidos["Fecha Vendida"], errors="coerce")
    vendidos["Fecha Formateada"] = vendidos["Fecha Vendida"].dt.strftime("%d/%m/%Y")

    # Filtros de fecha
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

    # Descripción enriquecida
    vendidos["Descripción"] = vendidos.apply(
        lambda row: f"{row.get('Tipo de prenda', '')} | Talla {row.get('Talla', '')} | Marca {row.get('Marca', '') or 'Sin marca'} | Características: {row.get('Caracteristicas (Color, estampado, material...)', '') or 'Sin descripción'}",
        axis=1
    )

    # Filtros adicionales
    columnas_filtro = [col for col in ["Talla", "Tipo de prenda", "Marca", "¿Donación o devolución?"] if col in vendidos.columns]
    with st.expander("⚙️ Otros Filtros"):
        for columna in columnas_filtro:
            opciones = vendidos[columna].dropna().unique().tolist()
            seleccion = st.multiselect(f"Filtrar por {columna}", opciones, default=[])
            if seleccion:
                vendidos = vendidos[vendidos[columna].isin(seleccion)]

    columnas_visibles = ["ID Prenda", "Nº Cliente (Formato C-xxx)", "Fecha Formateada", "Precio", "Descripción"]
    st.dataframe(vendidos[columnas_visibles], use_container_width=True)

    # Excel export
    if st.button("⬇️ Descargar Excel Vendidos"):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            vendidos[columnas_visibles].to_excel(writer, index=False, sheet_name="Vendidos")
        buffer.seek(0)
        st.download_button("Descargar Excel", buffer, file_name="vendidos_filtrado.xlsx")

    # PDF export
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
            pdf.cell(col_widths[i], 8, col, border=1)
        pdf.ln()

        pdf.set_font("Arial", '', 9)
        for _, row in vendidos[columnas_visibles].iterrows():
            for i, col in enumerate(columnas_visibles):
                texto = str(row[col]) if pd.notna(row[col]) else ""
                if col == "Descripción":
                    y_before = pdf.get_y()
                    x_before = pdf.get_x()
                    pdf.multi_cell(col_widths[i], 8, texto, border=1)
                    y_after = pdf.get_y()
                    pdf.set_y(y_before)
                    pdf.set_x(x_before + col_widths[i])
                else:
                    pdf.cell(col_widths[i], 8, texto, border=1)
            pdf.ln()

        buffer = BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        st.download_button("⬇️ Descargar PDF", buffer.getvalue(), file_name="vendidos_filtrado.pdf")
# --- Generador de Etiquetas ---
elif seccion == "Generador de Etiquetas":
    st.markdown("### 🏷️ Generador de Etiquetas")
    hoy = pd.Timestamp.today().normalize()
    fecha_hoy_str = hoy.strftime("%Y-%m-%d")

    # --- Etiqueta única ---
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

            pdf = FPDF(orientation='L', unit='mm', format=(74, 105))  # Verdadero horizontal A7
            pdf.add_page()
            pdf.set_font("Arial", 'B', 22)
            pdf.set_xy(0, 20)
            pdf.cell(105, 12, "EUR " + precio, ln=2, align='C')
            pdf.set_font("Arial", 'B', 20)
            pdf.cell(105, 10, f"Talla {talla}", ln=2, align='C')
            pdf.set_font("Arial", '', 14)
            pdf.cell(105, 8, f"Cliente: {cliente}", ln=2, align='C')
            pdf.cell(105, 8, f"Prenda: {prenda_id}", ln=2, align='C')

            buffer = BytesIO()
            pdf.output(buffer)
            buffer.seek(0)
            st.download_button(
                "⬇️ Descargar Etiqueta",
                buffer.getvalue(),
                file_name=f"etiqueta_{prenda_id}_{fecha_hoy_str}.pdf"
            )

    # --- Etiquetas de productos vendidos hoy ---
    st.markdown("#### 🔹 Generar etiquetas de productos vendidos hoy")
    if "Fecha Vendida" in df_prendas.columns:
        df_prendas["Fecha Vendida"] = pd.to_datetime(df_prendas["Fecha Vendida"], errors='coerce')
        vendidas_hoy = df_prendas[df_prendas["Fecha Vendida"].dt.normalize() == hoy]
    else:
        vendidas_hoy = pd.DataFrame()

    if not vendidas_hoy.empty:
        st.dataframe(vendidas_hoy)

        if st.button("⬇️ Generar PDF etiquetas del día"):
            pdf = FPDF(orientation='L', unit='mm', format=(74, 105))  # Horizontal real
            pdf.set_auto_page_break(auto=False)

            for _, row in vendidas_hoy.iterrows():
                precio = str(row.get("Precio", ""))
                talla = row.get("Talla", "")
                cliente = row.get("Nº Cliente (Formato C-xxx)", "")
                prenda_id = row.get("ID Prenda", "")

                pdf.add_page()
                pdf.set_font("Arial", 'B', 22)
                pdf.set_xy(0, 20)
                pdf.cell(105, 12, "EUR " + precio, ln=2, align='C')
                pdf.set_font("Arial", 'B', 20)
                pdf.cell(105, 10, f"Talla {talla}", ln=2, align='C')
                pdf.set_font("Arial", '', 14)
                pdf.cell(105, 8, f"Cliente: {cliente}", ln=2, align='C')
                pdf.cell(105, 8, f"Prenda: {prenda_id}", ln=2, align='C')

            buffer = BytesIO()
            pdf.output(buffer)
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

    fecha_reporte = st.date_input("Selecciona la fecha", pd.Timestamp.today(), format="YYYY/MM/DD")
    hoy = pd.Timestamp(fecha_reporte).normalize()

    # --- Ventas del día ---
    df_prendas["Fecha Vendida"] = pd.to_datetime(df_prendas["Fecha Vendida"], errors="coerce")
    ventas_dia = df_prendas[df_prendas["Fecha Vendida"].dt.normalize() == hoy]

    # Cálculos de totales
    total_ganado = ventas_dia["Precio"].sum()
    comision_clientes = (ventas_dia["Precio"] * 0.3).sum()
    total_neto = total_ganado - comision_clientes

    st.markdown(f"**💰 Total ganado (€)**\n\n{total_ganado:.2f}")
    st.markdown(f"**👛 Comisión clientes (30%)**\n\n{comision_clientes:.2f}")
    st.markdown(f"**📈 Total neto (€)**\n\n{total_neto:.2f}")

    # --- Nuevos clientes del día ---
    df_clientes = df_clientes.copy()
    if "Marca temporal" in df_clientes.columns:
        df_clientes["Marca temporal"] = pd.to_datetime(df_clientes["Marca temporal"], errors="coerce")
        df_clientes = df_clientes.drop(columns=["Marca temporal"])

    columnas_merge = [col for col in df_clientes.columns if col.startswith("Merged")]
    df_clientes = df_clientes.drop(columns=columnas_merge, errors="ignore")
    nuevas_altas = df_clientes[df_clientes["Marca temporal"].dt.normalize() == hoy] if "Marca temporal" in df_clientes.columns else pd.DataFrame()

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

    
    if st.button("Descargar Reporte en PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
    
        pdf.set_font(style="B", size=16)
        pdf.cell(0, 10, f" Reporte Diario - {hoy.date()}", ln=True, align="C")
        pdf.ln(10)
    
        pdf.set_font(style="", size=12)
        pdf.cell(0, 8, f" Total ganado: EUR {total_ganado:.2f}", ln=True)
        pdf.cell(0, 8, f" Comisión clientes (30%): EUR {comision_clientes:.2f}", ln=True)
        pdf.cell(0, 8, f"Total neto: EUR {total_neto:.2f}", ln=True)
        pdf.ln(8)
    
        pdf.set_font(style="B", size=12)
        pdf.cell(0, 8, " Ventas del Día:", ln=True)
        pdf.set_font(size=10)
    
        for _, row in ventas_dia[columnas_visibles].iterrows():
            try:
                id_prenda = str(row.get("ID Prenda", ""))
                cliente = str(row.get("Nº Cliente (Formato C-xxx)", ""))
                tipo = str(row.get("Tipo de prenda", ""))
                talla = str(row.get("Talla", ""))
                precio = str(row.get("Precio", ""))
                fecha = pd.to_datetime(row.get("Fecha Vendida", ""), errors='coerce')
                fecha_str = fecha.date().isoformat() if pd.notna(fecha) else "Fecha inválida"
    
                linea = f"- {id_prenda} | Cliente: {cliente} | {tipo} Talla {talla} | EUR {precio} | {fecha_str}"
                pdf.multi_cell(0, 8, linea)
            except:
                pdf.multi_cell(0, 8, "⚠ Error al mostrar una venta.")
    
        pdf.ln(8)
    
        if not nuevas_altas.empty:
            pdf.set_font(style="B", size=12)
            pdf.cell(0, 8, "Altas de nuevos clientes:", ln=True)
            pdf.set_font(size=10)
            for _, row in nuevas_altas.iterrows():
                try:
                    linea = " - ".join([f"{col}: {str(row[col])}" for col in nuevas_altas.columns if pd.notna(row[col])])
                    pdf.multi_cell(0, 8, linea)
                    pdf.ln(1)
                except:
                    pdf.multi_cell(0, 8, " Error al mostrar un cliente.")
    
        buffer = BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        st.download_button(
            label="Descargar PDF",
            data=buffer.getvalue(),
            file_name=f"reporte_diario_{hoy.date()}.pdf"
        )
