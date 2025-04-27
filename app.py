import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- Configuración de acceso ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_file('claves.json', scopes=SCOPE)
client = gspread.authorize(credentials)

# --- Conectar con el Google Sheets ---
spreadsheet = client.open("Stock")  # nombre exacto del archivo
hoja_prendas = spreadsheet.worksheet("Prendas")
hoja_clientes = spreadsheet.worksheet("Clientes")

# --- Cargar datos en DataFrames ---
df_prendas = pd.DataFrame(hoja_prendas.get_all_records())
df_clientes = pd.DataFrame(hoja_clientes.get_all_records())

# --- Configuración visual Streamlit ---
st.set_page_config(
    page_title="Nirvana Vintage",
    page_icon="🌟",
    layout="centered"
)

# --- Título Principal ---
st.title("\ud83c\udf1f Nirvana Vintage: Gestión Diaria \ud83c\udf1f")
st.markdown("---")

# --- Menú Principal ---
menu = st.sidebar.selectbox(
    "Selecciona una opción:",
    ("Inicio", "Buscar Cliente", "Generar Informe Diario", "Resumen Mensajes")
)

if menu == "Inicio":
    st.subheader("\ud83d\udcc5 Accesos Rápidos")
    st.markdown("- [➕ Añadir Nueva Prenda](https://docs.google.com/forms/d/e/FORM_ID/viewform)")
    st.markdown("- [➕ Alta Nuevo Cliente](https://docs.google.com/forms/d/e/FORM_ID/viewform)")
    st.markdown("- [✅ Marcar como Vendida](https://docs.google.com/forms/d/e/FORM_ID/viewform)")
    st.markdown("---")
    st.info("Selecciona una acción en el menú de la izquierda para comenzar.")

elif menu == "Buscar Cliente":
    st.subheader("🔍 Buscar Cliente")
    nombre = st.text_input("Nombre del Cliente")
    if nombre:
        resultados = df_clientes[df_clientes['Nombre y Apellidos'].str.contains(nombre, case=False, na=False)]
        if not resultados.empty:
            st.dataframe(resultados)
        else:
            st.warning("Cliente no encontrado.")

elif menu == "Generar Informe Diario":
    st.subheader("📉 Informe de Recordatorios para WhatsApp")
    hoy = pd.Timestamp.now(tz='Europe/Madrid').strftime("%d/%m/%Y")
    df_hoy = df_prendas[(df_prendas['Fecha Aviso'] == hoy) & (df_prendas['Vendida'] != True)]

    if df_hoy.empty:
        st.success("No hay prendas para recordar hoy \ud83c\udf1f")
    else:
        st.write(f"### Recordatorios para hoy: {hoy}")
        for _, row in df_hoy.iterrows():
            cliente = df_clientes[df_clientes['ID Cliente'] == row['Nº Cliente (Formato C-xxx) ']]
            if not cliente.empty:
                nombre = cliente.iloc[0]['Nombre y Apellidos']
                telefono = cliente.iloc[0]['Teléfono']
                mensaje = (f"Hola {nombre}, tu prenda '{row['Tipo de prenda']}' vence pronto. "
                           f"¿Deseas renovarla, donarla o recogerla?")
                st.info(f"**Cliente:** {nombre} | **Teléfono:** {telefono}\n\n{mensaje}")

elif menu == "Resumen Mensajes":
    st.subheader("📢 Resumen de Mensajes a Enviar")
    hoy = pd.Timestamp.now(tz='Europe/Madrid').strftime("%d/%m/%Y")
    df_hoy = df_prendas[(df_prendas['Fecha Aviso'] == hoy) & (df_prendas['Vendida'] != True)]
    resumen = []

    for _, row in df_hoy.iterrows():
        cliente = df_clientes[df_clientes['ID Cliente'] == row['Nº Cliente (Formato C-xxx) ']]
        if not cliente.empty:
            nombre = cliente.iloc[0]['Nombre y Apellidos']
            telefono = cliente.iloc[0]['Teléfono']
            resumen.append(f"{nombre} ({telefono}) - {row['Tipo de prenda']}")

    if resumen:
        for r in resumen:
            st.write(f"- {r}")
    else:
        st.success("Hoy no hay mensajes programados \ud83d\ude80")

# --- Footer ---
st.markdown("""
---
*Creado con ❤️ para Nirvana Vintage - 2025*
""")
