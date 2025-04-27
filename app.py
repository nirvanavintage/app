import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# --- Configuración básica ---
st.set_page_config(
    page_title="Nirvana Vintage",
    page_icon="✨",
    layout="centered"
)

# --- Autenticación Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name('claves.json', scope)
client = gspread.authorize(credentials)

# --- Cargar las hojas ---
spreadsheet = client.open("Stock")
hoja_prendas = spreadsheet.worksheet("Prendas")
hoja_clientes = spreadsheet.worksheet("Clientes")

# --- Funciones útiles ---
def generar_informe_diario():
    df_prendas = pd.DataFrame(hoja_prendas.get_all_records())
    df_clientes = pd.DataFrame(hoja_clientes.get_all_records())

    hoy = datetime.now().strftime("%d/%m/%Y")
    df_prendas['Fecha Aviso'] = pd.to_datetime(df_prendas['Fecha Aviso'], dayfirst=True, errors='coerce')
    prendas_hoy = df_prendas[(df_prendas['Fecha Aviso'].dt.strftime("%d/%m/%Y") == hoy) & (df_prendas['Vendida'] != True)]

    if prendas_hoy.empty:
        st.info("✅ No hay prendas para avisar hoy.")
        return

    st.subheader("📋 Informe de WhatsApps a Enviar Hoy")

    for _, fila in prendas_hoy.iterrows():
        cliente = df_clientes[df_clientes['ID Cliente'] == fila['Nº Cliente (Formato C-xxx) ']]
        if not cliente.empty:
            nombre = cliente.iloc[0]['Nombre y Apellidos']
            telefono = cliente.iloc[0]['Teléfono']
            st.markdown(f"**Cliente:** {nombre}  \n"
                        f"**Teléfono:** {telefono}  \n"
                        f"**Prenda:** {fila['Tipo de prenda']}  \n"
                        f"**Marca:** {fila.get('Marca', 'N/A')}  \n"
                        f"**Opciones:** Renovar o Donar")
            st.markdown("---")

def buscar_cliente():
    nombre_buscado = st.text_input("🔎 Escribe el nombre o parte del nombre del cliente:")
    if nombre_buscado:
        df_clientes = pd.DataFrame(hoja_clientes.get_all_records())
        resultados = df_clientes[df_clientes['Nombre y Apellidos'].str.contains(nombre_buscado, case=False, na=False)]

        if not resultados.empty:
            st.success("Resultados encontrados:")
            st.dataframe(resultados)
        else:
            st.warning("❌ No se encontró ningún cliente.")

def resumen_mensajes():
    df_prendas = pd.DataFrame(hoja_prendas.get_all_records())
    hoy = datetime.now().strftime("%d/%m/%Y")
    df_prendas['Fecha Aviso'] = pd.to_datetime(df_prendas['Fecha Aviso'], dayfirst=True, errors='coerce')
    total = df_prendas[(df_prendas['Fecha Aviso'].dt.strftime("%d/%m/%Y") == hoy) & (df_prendas['Vendida'] != True)].shape[0]

    st.subheader("📊 Resumen de Mensajes")
    st.success(f"Hoy se deben enviar **{total} mensajes** de aviso de vencimiento.")

# --- Página principal ---
st.title("✨ Nirvana Vintage: Gestión Diaria ✨")
st.markdown("---")

# --- Menú principal ---
st.subheader("📌 ¿Qué quieres hacer hoy?")

opcion = st.selectbox("", ("Selecciona una opción", 
                           "🔎 Buscar Cliente", 
                           "📋 Generar Informe Diario", 
                           "📊 Resumen Mensajes a Enviar"))

if opcion == "🔎 Buscar Cliente":
    buscar_cliente()

elif opcion == "📋 Generar Informe Diario":
    generar_informe_diario()

elif opcion == "📊 Resumen Mensajes a Enviar":
    resumen_mensajes()

# --- Enlaces rápidos ---
st.markdown("---")
st.subheader("📝 Formularios Rápidos")

st.markdown("""
- [➕ Añadir Nueva Prenda](https://forms.gle/2J1FzzDJLwZ1dtSF9)
- [➕ Alta Nuevo Cliente](https://forms.gle/Nr4xREV78Y8tEMDj6)
- [✅ Marcar como Vendida](https://docs.google.com/spreadsheets/d/1rE7zErEfA14TRoxaA-PPD5OGYYXh3Zr_0j9bRQeLap8/edit#gid=0)
""")

# --- Footer bonito ---
st.markdown("---")
st.caption("Creado con ❤️ para Nirvana Vintage - 2025")
