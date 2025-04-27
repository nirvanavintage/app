import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- Configuración de acceso usando SECRETS ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

credentials_info = {
    "type": st.secrets["google_service_account"]["type"],
    "project_id": st.secrets["google_service_account"]["project_id"],
    "private_key_id": st.secrets["google_service_account"]["private_key_id"],
    "private_key": st.secrets["google_service_account"]["private_key"],
    "client_email": st.secrets["google_service_account"]["client_email"],
    "client_id": st.secrets["google_service_account"]["client_id"],
    "auth_uri": st.secrets["google_service_account"]["auth_uri"],
    "token_uri": st.secrets["google_service_account"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["google_service_account"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["google_service_account"]["client_x509_cert_url"]
}

credentials = Credentials.from_service_account_info(credentials_info, scopes=scope)
client = gspread.authorize(credentials)

# --- Conectar con el Google Sheets ---
spreadsheet = client.open("Stock")
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

# --- Menú de acciones ---
menu = st.sidebar.radio("\ud83d\udd39 Menú Principal", ("Inicio", "Buscar Cliente", "Informe Diario", "Resumen Mensajes", "Formularios"))

if menu == "Inicio":
    st.header("Bienvenida a la Gestión Diaria de Nirvana Vintage")
    st.success("Selecciona una acción en el menú lateral para comenzar.")

elif menu == "Buscar Cliente":
    st.header("\ud83d\udd0d Buscar Cliente")
    nombre_busqueda = st.text_input("Introduce el nombre o teléfono del cliente")

    if nombre_busqueda:
        resultado = df_clientes[df_clientes.apply(lambda row: nombre_busqueda.lower() in row.to_string().lower(), axis=1)]
        if not resultado.empty:
            st.dataframe(resultado)
        else:
            st.warning("No se encontró ningún cliente con esos datos.")

elif menu == "Informe Diario":
    st.header("\ud83d\udcc5 Informe Diario de Mensajes")

    hoy = pd.Timestamp.now(tz='Europe/Madrid').strftime("%d/%m/%Y")
    df_prendas['Fecha Aviso'] = pd.to_datetime(df_prendas['Fecha Aviso'], dayfirst=True, errors='coerce')
    prendas_hoy = df_prendas[(df_prendas['Fecha Aviso'].dt.strftime("%d/%m/%Y") == hoy) & (df_prendas['Vendida'] != True)]

    if prendas_hoy.empty:
        st.info("No hay prendas para avisar hoy.")
    else:
        st.subheader("Mensajes a enviar hoy:")
        for _, fila in prendas_hoy.iterrows():
            cliente = df_clientes[df_clientes['ID Cliente'] == fila['Nº Cliente (Formato C-xxx) ']]
            if not cliente.empty:
                nombre = cliente.iloc[0]['Nombre y Apellidos']
                telefono = cliente.iloc[0]['Teléfono']
                mensaje = f"Hola {nombre}, tu prenda vence pronto. Puedes optar por donarla o recogerla en tienda. \ud83d\udc96"
                st.info(f"**Cliente:** {nombre}\n**Teléfono:** {telefono}\n**Mensaje:** {mensaje}")

elif menu == "Resumen Mensajes":
    st.header("\ud83d\udc8c Resumen de Mensajes Programados")

    df_prendas['Fecha Aviso'] = pd.to_datetime(df_prendas['Fecha Aviso'], dayfirst=True, errors='coerce')
    resumen = df_prendas[(df_prendas['Vendida'] != True)].groupby(df_prendas['Fecha Aviso'].dt.strftime("%d/%m/%Y")).size().reset_index(name='Prendas a Avisar')

    if resumen.empty:
        st.success("Actualmente no hay prendas pendientes de aviso.")
    else:
        st.dataframe(resumen)

elif menu == "Formularios":
    st.header("\ud83d\udcc5 Formularios Rápidos")
    st.markdown("[\u2795 Añadir Nueva Prenda](https://docs.google.com/forms/d/e/FORM_ID_1/viewform)")
    st.markdown("[\u2795 Alta Nuevo Cliente](https://docs.google.com/forms/d/e/FORM_ID_2/viewform)")
    st.markdown("[\u2705 Marcar como Vendida](https://docs.google.com/forms/d/e/FORM_ID_3/viewform)")

# --- Pie de página ---
st.markdown("""
---
*Creado con ❤️ para Nirvana Vintage - 2025*
""")
