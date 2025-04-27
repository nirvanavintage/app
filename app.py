import streamlit as st
import pandas as pd
from fpdf import FPDF

st.set_page_config(page_title="Nirvana Vintage", page_icon="✨", layout="centered")

st.title(":sparkles: Nirvana Vintage: Gestión Diaria :sparkles:")
st.markdown("---")

# Enlaces
st.sidebar.header("🔗 Formularios y App")
st.sidebar.markdown("[Formulario Nueva Prenda](https://forms.gle/QAXSH5ZP6oCpWEcL6)")
st.sidebar.markdown("[Formulario Nuevo Cliente](https://forms.gle/2BpmDNegKNTNc2dK6)")
st.sidebar.markdown("[App Marcar como Vendido](https://www.appsheet.com/start/e1062d5c-129e-4947-bed1-cbb925ad7209?platform=desktop#appName=Marcarcomovendido-584406513&view=Marcar%20como%20vendido)")

# Cargar datos
df_clientes = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vT3M3U_N5T5_-dLw0V_3pA8mrDulz-cznJNHwFM1GcfjxzqM8j5mfJpRzF4YBOZBsgjsvDRKsDnpD7I/pub?gid=1775701755&single=true&output=csv")
df_prendas = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vT3M3U_N5T5_-dLw0V_3pA8mrDulz-cznJNHwFM1GcfjxzqM8j5mfJpRzF4YBOZBsgjsvDRKsDnpD7I/pub?gid=517323538&single=true&output=csv")

# Convertir columna 'Vendida' (casillas) a booleano si existe
df_prendas["Vendida"] = df_prendas["Vendida"].fillna(False).astype(bool)

# Opciones de acción
accion = st.selectbox("Selecciona una acción", ["Buscar Cliente", "Consultar Stock", "Consultar Vendidos"])

if accion == "Buscar Cliente":
    nombre_cliente = st.text_input("Introduce el nombre del cliente")
    if st.button("🔍 Buscar"):
        resultados = df_clientes[df_clientes["Nombre y Apellidos"].str.contains(nombre_cliente, case=False, na=False)]
        if not resultados.empty:
            st.success(f"Se encontraron {len(resultados)} cliente(s):")
            st.dataframe(resultados)
            id_cliente = resultados.iloc[0]["ID Cliente"]

            prendas_cliente = df_prendas[df_prendas["Nº Cliente (Formato C-xxx)"] == id_cliente]
            stock_cliente = prendas_cliente[prendas_cliente["Vendida"] == False]
            vendidos_cliente = prendas_cliente[prendas_cliente["Vendida"] == True]

            st.subheader(":hanger: Prendas en Stock")
            if not stock_cliente.empty:
                st.dataframe(stock_cliente)
            else:
                st.info("No hay prendas en stock.")

            st.subheader(":shopping_bags: Prendas Vendidas")
            if not vendidos_cliente.empty:
                st.dataframe(vendidos_cliente)
            else:
                st.info("No hay prendas vendidas.")

            # Generar PDF
            if st.button("🔖 Generar Informe en PDF"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)

                pdf.cell(0, 10, f"Cliente: {resultados.iloc[0]['Nombre y Apellidos']}", ln=True)
                pdf.cell(0, 10, f"ID Cliente: {id_cliente}", ln=True)
                pdf.cell(0, 10, "", ln=True)

                pdf.cell(0, 10, "Prendas en Stock:", ln=True)
                for index, row in stock_cliente.iterrows():
                    pdf.cell(0, 10, f"{row['ID Prenda']} - {row['Tipo de prenda']}", ln=True)

                pdf.cell(0, 10, "", ln=True)
                pdf.cell(0, 10, "Prendas Vendidas:", ln=True)
                for index, row in vendidos_cliente.iterrows():
                    pdf.cell(0, 10, f"{row['ID Prenda']} - {row['Tipo de prenda']}", ln=True)

                pdf_output = f"informe_{id_cliente}.pdf"
                pdf.output(pdf_output)

                with open(pdf_output, "rb") as file:
                    st.download_button(label="🔖 Descargar Informe PDF", data=file, file_name=pdf_output, mime="application/pdf")
        else:
            st.error("No se encontró ningún cliente.")

elif accion == "Consultar Stock":
    tipo_filtro = st.selectbox("Filtrar por tipo de prenda", ["Todos"] + sorted(df_prendas["Tipo de prenda"].dropna().unique().tolist()))
    stock = df_prendas[df_prendas["Vendida"] == False]
    if tipo_filtro != "Todos":
        stock = stock[stock["Tipo de prenda"] == tipo_filtro]

    st.success(f"Hay {len(stock)} prenda(s) en stock.")
    st.dataframe(stock)

elif accion == "Consultar Vendidos":
    tipo_filtro = st.selectbox("Filtrar por tipo de prenda", ["Todos"] + sorted(df_prendas["Tipo de prenda"].dropna().unique().tolist()))
    vendidos = df_prendas[df_prendas["Vendida"] == True]
    if tipo_filtro != "Todos":
        vendidos = vendidos[vendidos["Tipo de prenda"] == tipo_filtro]

    st.success(f"Hay {len(vendidos)} prenda(s) vendidas.")
    st.dataframe(vendidos)

st.markdown("""
---
<div style='text-align: center;'>💔 Creado con amor para Nirvana Vintage - 2025 💔</div>
""", unsafe_allow_html=True)
