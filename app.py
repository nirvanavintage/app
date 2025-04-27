import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- Configuracion de la pagina ---
st.set_page_config(
    page_title="Nirvana Vintage",
    page_icon="🌟",
    layout="wide"
)

# --- Conexion a Google Sheets ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = Credentials.from_service_account_file("credenciales.json", scopes=SCOPE)
client = gspread.authorize(CREDS)

# --- Carga de datos ---
HOJA_PRENDAS = 'Prendas'
HOJA_CLIENTES = 'Clientes'

spreadsheet = client.open("Stock")  # Nombre exacto del Google Sheets
hoja_prendas = spreadsheet.worksheet(HOJA_PRENDAS)
hoja_clientes = spreadsheet.worksheet(HOJA_CLIENTES)

# --- Funciones ---
def generar_informe_diario():
    st.subheader("📊 Informe Diario de WhatsApps")

    # Obtener datos
    prendas = pd.DataFrame(hoja_prendas.get_all_records())
    clientes = pd.DataFrame(hoja_clientes.get_all_records())

    hoy = datetime.now().strftime("%d/%m/%Y")

    # Filtrar prendas que tienen Fecha Aviso = hoy y no estan vendidas
    prendas_hoy = prendas[(prendas['Fecha Aviso'] == hoy) & (prendas['Vendida'] != True)]

    if prendas_hoy.empty:
        st.info("🚫 No hay mensajes para enviar hoy.")
        return

    # Juntar datos con cliente
    resultado = pd.merge(prendas_hoy, clientes, left_on='Nº Cliente (Formato C-xxx) ', right_on='ID Cliente', how='left')

    resultado['Mensaje'] = resultado.apply(lambda x: f"Hola {x['Nombre y Apellidos']}, tu prenda '{x['Tipo de prenda']}' vence pronto. \
    Por favor confirma si deseas recuperarla o donarla.", axis=1)

    mostrar = resultado[['Nombre y Apellidos', 'Teléfono', 'Tipo de prenda', 'Mensaje']]

    st.success(f"🎉 Hoy hay {len(mostrar)} mensajes a enviar.")
    st.dataframe(mostrar, use_container_width=True)

    # Descargar como CSV
    csv = mostrar.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="🔗 Descargar Informe CSV",
        data=csv,
        file_name=f"whatsapp_informe_{hoy.replace('/', '-')}.csv",
        mime='text/csv'
    )

# --- Interfaz Web ---
st.title("💫 Nirvana Vintage: Gestión Diaria")
st.markdown("---")

menu = st.sidebar.radio("🔍 Navegación", ["Inicio", "Generar Informe Diario", "Próximamente"])

if menu == "Inicio":
    st.header("🚼 Acciones rápidas")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Buscar Cliente"):
            st.warning("Función disponible próximamente.")

    with col2:
        if st.button("📅 Generar Informe Diario"):
            generar_informe_diario()

    with col3:
        if st.button("📰 Resumen Mensajes a Enviar"):
            st.warning("Función disponible próximamente.")

    st.markdown("---")
    st.subheader("📄 Formularios Rápidos")
    st.markdown("""
    - [➕ Añadir Nueva Prenda](https://forms.gle/Nr4xREV78Y8tEMDj6)
    - [➕ Alta Nuevo Cliente](https://forms.gle/2J1FzzDJLwZ1dtSF9)
    - [☑️ Marcar como Vendida](#)
    """)

elif menu == "Generar Informe Diario":
    generar_informe_diario()

else:
    st.info("🌟 Muy pronto más funcionalidades...")

# --- Footer ---
st.markdown("""
---
Creado con ❤️ para Nirvana Vintage - 2025
""")
