import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
import unicodedata

# --- Función auxiliar para fpdf ---
def texto_fpdf(txt):
    return unicodedata.normalize('NFKD', str(txt)).encode('latin-1', 'ignore').decode('latin-1')

# --- Seguridad ---
if "acceso_concedido" not in st.session_state:
    st.session_state.acceso_concedido = False

if not st.session_state.acceso_concedido:
    st.title("✨ Nirvana Vintage: Gestión Diaria ✨")
    st.markdown("""
        [🧺 Nueva Prenda](https://forms.gle/QAXSH5ZP6oCpWEcL6)
        | [🧍 Nuevo Cliente](https://forms.gle/2BpmDNegKNTNc2dK6)
        | [🧾 App Marcar Vendido](https://www.appsheet.com/start/e1062d5c-129e-4947-bed1-cbb925ad7209)
    """)
    pwd = st.text_input("Contraseña:", type="password")
    if st.button("🔐 Entrar"):
        if pwd == "nirvana2024":
            st.session_state.acceso_concedido = True
            st.success("Acceso concedido. Recarga la página si no se actualiza.")
        else:
            st.error("Contraseña incorrecta")
    st.stop()

# --- Cargar datos ---
@st.cache_data(ttl=600)
def cargar_datos():
    df_prendas = pd.read_csv("prendas.csv", parse_dates=["Fecha de recepción", "Fecha Vendida"])
    df_clientes = pd.read_csv("clientes.csv", parse_dates=["Marca temporal"])
    return df_prendas, df_clientes

df_prendas, df_clientes = cargar_datos()

# --- Sidebar ---
seccion = st.sidebar.selectbox("📁 Secciones", [
    "Buscar Cliente", "Consultar Stock", "Consultar Vendidos", "Reporte Diario", "Generador de Etiquetas"])

st.title("✨ Nirvana Vintage: Gestión Diaria ✨")

# --- Buscar Cliente ---
if seccion == "Buscar Cliente":
    st.header("🔍 Buscar Cliente")
    nombre = st.text_input("Introduce el nombre del cliente")
    if nombre:
        resultados = df_clientes[df_clientes["Nombre y Apellidos"].str.contains(nombre, case=False, na=False)]
        st.dataframe(resultados)
        if not resultados.empty:
            id_cliente = resultados.iloc[0]["ID Cliente"]
            prendas_cliente = df_prendas[df_prendas["Nº Cliente (Formato C-xxx)"] == id_cliente]
            st.subheader("👜 Prendas del Cliente")
            st.dataframe(prendas_cliente)
            if st.button("📄 Descargar Informe Cliente"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                nombre_cliente = resultados.iloc[0]["Nombre y Apellidos"]
                pdf.cell(0, 10, texto_fpdf(f"Informe de {nombre_cliente}"), ln=True, align='C')
                pdf.ln(10)
                for _, row in prendas_cliente.iterrows():
                    pdf.set_font("Arial", '', 12)
                    pdf.cell(0, 8, texto_fpdf(f"Prenda {row['Tipo de prenda']} - Talla {row['Talla']} - {row['Caracteristicas (Color, estampado, material...)']}"), ln=True)
                buffer = BytesIO()
                pdf.output(buffer)
                buffer.seek(0)
                st.download_button("⬇️ Descargar PDF Informe", buffer.getvalue(), file_name="informe_cliente.pdf")

# --- Consultar Stock ---
elif seccion == "Consultar Stock":
    st.header("📦 Prendas en Stock")
    stock = df_prendas[df_prendas["Vendida"] != True]
    st.dataframe(stock)
    if st.button("⬇️ Descargar Excel Stock"):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            stock.to_excel(writer, index=False)
        buffer.seek(0)
        st.download_button("Descargar Stock Excel", buffer, file_name="stock.xlsx")

# --- Consultar Vendidos ---
elif seccion == "Consultar Vendidos":
    st.header("✅ Prendas Vendidas")
    vendidos = df_prendas[df_prendas["Vendida"] == True]
    st.dataframe(vendidos)
    if st.button("⬇️ Descargar Excel Vendidos"):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            vendidos.to_excel(writer, index=False)
        buffer.seek(0)
        st.download_button("Descargar Vendidos Excel", buffer, file_name="vendidos.xlsx")

# --- Reporte Diario ---
elif seccion == "Reporte Diario":
    st.header("📅 Reporte Diario")
    fecha = st.date_input("Selecciona una fecha", value=datetime.today())
    vendidos_fecha = df_prendas[(df_prendas["Vendida"] == True) & (df_prendas["Fecha Vendida"].dt.date == fecha)]
    st.dataframe(vendidos_fecha)

# --- Generador de Etiquetas ---
elif seccion == "Generador de Etiquetas":
    st.markdown("### 🏷️ Generador de Etiquetas")
    cod = st.text_input("Introduce un código de prenda")
    hoy = pd.Timestamp.today().normalize()

    st.markdown("#### 🔹 Generar una sola etiqueta")
    if st.button("Generar etiqueta única") and cod:
        prenda = df_prendas[df_prendas["ID Prenda"] == cod]
        if not prenda.empty:
            st.dataframe(prenda)
            row = prenda.iloc[0]
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(70, 8, texto_fpdf(f"€ {row['Precio']}"), ln=2)
            pdf.cell(70, 8, texto_fpdf(f"Talla {row['Talla']}"), ln=2)
            pdf.set_font("Arial", '', 10)
            pdf.cell(70, 6, texto_fpdf(f"Cliente: {row['Nº Cliente (Formato C-xxx)']}"), ln=2)
            pdf.cell(70, 6, texto_fpdf(f"Prenda: {row['ID Prenda']}"), ln=2)
            buffer = BytesIO()
            pdf.output(buffer)
            buffer.seek(0)
            st.download_button("⬇️ Descargar Etiqueta", buffer.getvalue(), file_name=f"etiqueta_{cod}.pdf")

    st.markdown("#### 🔹 Generar etiquetas de productos recibidos hoy")
    hoy_recibidas = df_prendas[df_prendas["Fecha de recepción"].dt.normalize() == hoy]
    if not hoy_recibidas.empty:
        st.dataframe(hoy_recibidas)
        if st.button("Generar PDF etiquetas del día"):
            etiquetas_por_fila = 2
            filas_por_pagina = 5
            etiquetas_por_pagina = etiquetas_por_fila * filas_por_pagina
            etiqueta_ancho = 70
            etiqueta_alto = 40

            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=False)

            for i, (_, row) in enumerate(hoy_recibidas.iterrows()):
                if i % etiquetas_por_pagina == 0:
                    pdf.add_page()
                x = 10 + (i % etiquetas_por_fila) * (etiqueta_ancho + 10)
                y = 10 + ((i // etiquetas_por_fila) % filas_por_pagina) * (etiqueta_alto + 10)
                pdf.set_xy(x, y)
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(etiqueta_ancho, 8, texto_fpdf(f"€ {row['Precio']}"), ln=2)
                pdf.cell(etiqueta_ancho, 8, texto_fpdf(f"Talla {row['Talla']}"), ln=2)
                pdf.set_font("Arial", '', 10)
                pdf.cell(etiqueta_ancho, 6, texto_fpdf(f"Cliente: {row['Nº Cliente (Formato C-xxx)']}"), ln=2)
                pdf.cell(etiqueta_ancho, 6, texto_fpdf(f"Prenda: {row['ID Prenda']}"), ln=2)
            buffer = BytesIO()
            pdf.output(buffer)
            buffer.seek(0)
            st.download_button("⬇️ Descargar Todas las Etiquetas", buffer.getvalue(), file_name="etiquetas_recibidas_hoy.pdf")
