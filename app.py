import streamlit as st
import pandas as pd
from fpdf import FPDF

# Configurar página
st.set_page_config(page_title="Nirvana Vintage: Gestión Diaria", page_icon="🌟", layout="centered")

# Cargar los datos
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLu0AApD3jURHD8QQubDUSEadQt_oLgSb8vI5MJ5oOd_jTx2Kw31frmeKU6FcdVA/pub?output=csv"
data = pd.read_csv(sheet_url)

clientes = data[data['ID Cliente'].notna()][['ID Cliente', 'Nombre y Apellidos', 'Teléfono', 'Fecha de Alta', 'DNI']]
prendas = data[data['ID Prenda'].notna()][['ID Prenda', 'Nº Cliente (Formato C-xxx)', 'Fecha de recepción', 'Tipo de prenda', 'Vendida', 'Marca', 'Precio', 'Talla']]

# Título principal
st.markdown("""
<h1 style='text-align: center;'>🌟 Nirvana Vintage: Gestión Diaria 🌟</h1>
""", unsafe_allow_html=True)

# Menú principal
st.markdown("""
<h2>📄 ¿Qué quieres hacer hoy?</h2>
""", unsafe_allow_html=True)

accion = st.selectbox("Selecciona una acción", ("Buscar Cliente", "Consultar Stock", "Consultar Vendidos"))

# Buscar cliente
def buscar_cliente():
    nombre = st.text_input("Introduce el nombre del cliente")
    if st.button("🔍 Buscar"):
        resultados = clientes[clientes['Nombre y Apellidos'].str.contains(nombre, case=False, na=False)]
        if not resultados.empty:
            st.success(f"Se encontraron {len(resultados)} cliente(s):")
            st.dataframe(resultados)

            id_cliente = resultados.iloc[0]['ID Cliente']
            prendas_cliente = prendas[prendas['Nº Cliente (Formato C-xxx)'] == id_cliente]

            stock = prendas_cliente[prendas_cliente['Vendida'] != True]
            vendidos = prendas_cliente[prendas_cliente['Vendida'] == True]

            st.subheader("Prendas en Stock")
            st.dataframe(stock)

            st.subheader("Prendas Vendidas")
            st.dataframe(vendidos)

            if st.button("💾 Generar Informe en PDF"):
                generar_pdf(resultados.iloc[0], stock, vendidos)

        else:
            st.warning("No se encontraron clientes con ese nombre.")

# Consultar stock
def consultar_stock():
    st.subheader("Stock disponible")
    stock = prendas[prendas['Vendida'] != True]
    st.success(f"Hay {len(stock)} prendas en stock:")
    st.dataframe(stock)

# Consultar vendidos
def consultar_vendidos():
    st.subheader("Prendas Vendidas")
    vendidos = prendas[prendas['Vendida'] == True]
    st.success(f"Hay {len(vendidos)} prendas vendidas:")
    st.dataframe(vendidos)

# Funciones PDF
def generar_pdf(cliente, stock, vendidos):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Informe Cliente Nirvana Vintage", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Nombre: {cliente['Nombre y Apellidos']}", ln=True)
    pdf.cell(0, 10, f"Teléfono: {cliente['Teléfono']}", ln=True)
    pdf.cell(0, 10, f"Fecha de Alta: {cliente['Fecha de Alta']}", ln=True)
    pdf.cell(0, 10, f"DNI: {cliente['DNI']}", ln=True)
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Prendas en Stock", ln=True)
    pdf.set_font("Arial", '', 10)
    for index, row in stock.iterrows():
        pdf.cell(0, 8, f"{row['ID Prenda']} - {row['Tipo de prenda']} ({row['Marca']})", ln=True)
    
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Prendas Vendidas", ln=True)
    pdf.set_font("Arial", '', 10)
    for index, row in vendidos.iterrows():
        pdf.cell(0, 8, f"{row['ID Prenda']} - {row['Tipo de prenda']} ({row['Marca']})", ln=True)

    pdf_output = f"{cliente['Nombre y Apellidos'].replace(' ', '_')}_informe.pdf"
    pdf.output(pdf_output)

    with open(pdf_output, "rb") as f:
        st.download_button(label="🔗 Descargar Informe PDF", data=f, file_name=pdf_output, mime='application/octet-stream')

# Ejecutar acción
if accion == "Buscar Cliente":
    buscar_cliente()
elif accion == "Consultar Stock":
    consultar_stock()
elif accion == "Consultar Vendidos":
    consultar_vendidos()

# Formularios rápidos
st.markdown("""
---

<h2>📅 Formularios Rápidos</h2>

- [➕ Añadir Nueva Prenda](https://forms.gle/QAXSH5ZP6oCpWEcL6)
- [➕ Alta Nuevo Cliente](https://forms.gle/2BpmDNegKNTNc2dK6)
- [✅ Marcar como Vendida (App)](https://www.appsheet.com/start/e1062d5c-129e-4947-bed1-cbb925ad7209?platform=desktop#appName=Marcarcomovendido-584406513&view=Marcar%20como%20vendido)

<p style='text-align: center;'>❤️ Creado con amor para Nirvana Vintage - 2025 ❤️</p>
""", unsafe_allow_html=True)
