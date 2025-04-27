import streamlit as st

# --- Configuración básica ---
st.set_page_config(
    page_title="Nirvana Vintage",
    page_icon="👗",
    layout="centered"
)

# --- Título principal ---
st.title("✨ Nirvana Vintage: Gestión Diaria ✨")
st.markdown("---")

# --- Menú de acciones ---
st.subheader("¿Qué quieres hacer hoy?")

# Botones de acciones principales
if st.button("🔍 Buscar Cliente"):
    st.success("Funcionalidad de búsqueda de clientes (próximamente disponible).")

if st.button("📄 Generar Informe Diario"):
    st.success("Generar el informe diario de vencimientos (próximamente disponible).")

if st.button("💬 Resumen Mensajes a Enviar"):
    st.success("Mostrar el resumen de mensajes programados (próximamente disponible).")

# Separador bonito
st.markdown("---")

# --- Formularios de inserción ---
st.subheader("📋 Formularios rápidos")

st.markdown("[➕ Añadir Nueva Prenda](https://forms.gle/Nr4xREV78Y8tEMDj6)", unsafe_allow_html=True)
st.markdown("[➕ Alta Nuevo Cliente](https://forms.gle/2J1FzzDJLwZ1dtSF9)", unsafe_allow_html=True)
st.markdown("[✅ Marcar como Vendida](https://forms.gle/TU-ENLACE-MARCAR-VENDIDA)", unsafe_allow_html=True)

# --- Pie de página ---
st.markdown("---")
st.caption("Creado con ❤️ para Nirvana Vintage • 2025")
