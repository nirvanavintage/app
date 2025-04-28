import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Nirvana Vintage", page_icon="✨", layout="wide")

# ---------- UTILIDADES ---------- #
SHEET_ID = "1reTzFeErA14TRoxaA-PPD5OGfYYXH3Z_0i9bRQeLap8"

def leer(sheet:str):
    url=f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet}"
    return pd.read_csv(url)

def limpiar_prendas(df:pd.DataFrame)->pd.DataFrame:
    df["Vendida"] = df["Vendida"].astype(str).str.lower().isin(["true","1","si"])
    df["Precio"] = pd.to_numeric(df.get("Precio",0), errors="coerce").fillna(0)
    for c in ["Fecha Aviso","Fecha Vendida","Fecha de recepción"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c],errors="coerce").dt.strftime("%d/%m/%Y")
    return df

def pdf_tabla(df:pd.DataFrame,title:str)->bytes:
    pdf=FPDF('L','mm','A4'); pdf.add_page(); pdf.set_auto_page_break(True,10)
    pdf.set_font('Arial','B',14); pdf.cell(0,10,title,ln=1,align='C')
    pdf.set_font('Arial','',10); pdf.cell(0,8,f"Fecha: {datetime.now().strftime('%d/%m/%Y')}",ln=1,align='R'); pdf.ln(4)
    col_w=max(28,pdf.w/(len(df.columns)+1)); row_h=7
    pdf.set_fill_color(220,220,220)
    for col in df.columns: pdf.cell(col_w,row_h,str(col)[:28],1,0,'C',True)
    pdf.ln(row_h); pdf.set_fill_color(255,255,255)
    for _,row in df.iterrows():
        for item in row: pdf.cell(col_w,row_h,str(item)[:28],1)
        pdf.ln(row_h)
    return pdf.output(dest='S').encode('latin1')

# ---------- CARGA ---------- #
prendas=limpiar_prendas(leer("Prendas"))
clientes=leer("Clientes")
HOY=datetime.now().strftime("%d/%m/%Y")

# ---------- HEADER ---------- #
st.markdown("<h1 style='text-align:center;'>✨ Nirvana Vintage: Gestión Diaria ✨</h1>",unsafe_allow_html=True)
col1,col2,col3,col4=st.columns(4)
with col1: st.metric("🛍️ Stock", int((~prendas["Vendida"]).sum()))
with col2: st.metric("✅ Vendidas", int(prendas["Vendida"].sum()))
with col3: st.metric("📅 Avisos Hoy", int(prendas[(prendas["Fecha Aviso"]==HOY)&(~prendas["Vendida"])].shape[0]))
with col4: st.metric("💸 Ventas Hoy", int(prendas[prendas["Fecha Vendida"]==HOY].shape[0]))

st.markdown("""
<div style='text-align:center;'>
 <a href='https://forms.gle/QAXSH5ZP6oCpWEcL6' target='_blank'>📅 Nueva Prenda</a> |
 <a href='https://forms.gle/2BpmDNegKNTNc2dK6' target='_blank'>👤 Nuevo Cliente</a> |
 <a href='https://www.appsheet.com/start/e1062d5c-129e-4947-bed1-cbb925ad7209?platform=desktop#appName=Marcarcomovendido-584406513&view=Marcar%20como%20vendido' target='_blank'>🔄 App Marcar Vendido</a>
</div>
""",unsafe_allow_html=True)

st.markdown("---")
# ---------- MENÚ ---------- #
menu=st.sidebar.radio("📂 Secciones",["Buscar Cliente","Consultar Stock","Consultar Vendidos","Generar Avisos de Hoy","Reporte Diario","Informe Cliente por Entregas"])

# ---------- BUSCAR CLIENTE ---------- #
if menu=="Buscar Cliente":
    nombre=st.text_input("🔍 Nombre cliente")
    if st.button("Buscar") and nombre:
        res=clientes[clientes["Nombre y Apellidos"].str.contains(nombre,case=False,na=False)]
        if res.empty:
            st.error("Cliente no encontrado")
        else:
            st.dataframe(res)
            idc=res.iloc[0]["ID Cliente"]
            lotes=prendas[prendas["Nº Cliente (Formato C-xxx)"]==idc]
            st.markdown(f"**Total prendas:** {len(lotes)} · **Valor:** {lotes['Precio'].sum():.2f}€")
            st.dataframe(lotes)
            if st.button("📄 PDF Cliente"):
                st.download_button("⬇️ Descargar",pdf_tabla(lotes,f"Informe Cliente {res.iloc[0]['Nombre y Apellidos']}") ,file_name=f"cliente_{idc}.pdf",mime="application/pdf")

# ---------- CONSULTAR STOCK ---------- #
elif menu=="Consultar Stock":
    stock=prendas[~prendas["Vendida"]]
    st.dataframe(stock,use_container_width=True)
    if st.button("📄 PDF Stock"):
        st.download_button("⬇️ Stock PDF",pdf_tabla(stock,"Stock Disponible"),file_name="stock_total.pdf",mime="application/pdf")

# ---------- CONSULTAR VENDIDOS ---------- #
elif menu=="Consultar Vendidos":
    vend=prendas[prendas["Vendida"]]
    st.dataframe(vend,use_container_width=True)
    if st.button("📄 PDF Vendidos"):
        st.download_button("⬇️ Vendidos PDF",pdf_tabla(vend,"Prendas Vendidas"),file_name="vendidos_total.pdf",mime="application/pdf")

# ---------- AVISOS HOY ---------- #
elif menu=="Generar Avisos de Hoy":
    avisos=prendas[(prendas["Fecha Aviso"]==HOY)&(~prendas["Vendida"])]
    if avisos.empty:
        st.info("No hay avisos para hoy")
    else:
        st.dataframe(avisos)
        if st.button("📄 PDF Avisos"):
            st.download_button("⬇️ Avisos PDF",pdf_tabla(avisos,"Avisos de Hoy"),file_name="avisos_hoy.pdf",mime="application/pdf")

# ---------- REPORTE DIARIO ---------- #
elif menu=="Reporte Diario":
    avisos=prendas[(prendas["Fecha Aviso"]==HOY)&(~prendas["Vendida"])]
    ventas=prendas[prendas["Fecha Vendida"]==HOY]
    stock=prendas[~prendas["Vendida"]]
    bloques={"Avisos de Hoy":avisos,"Ventas de Hoy":ventas,"Stock Actual":stock}
    for titulo,df in bloques.items():
        st.subheader(f"{titulo} ({len(df)})")
        st.dataframe(df)
    if st.button("📄 PDF Reporte Diario"):
        pdf=FPDF('L'); pdf.add_page(); pdf.set_font('Arial','B',16); pdf.cell(0,10,'Reporte Diario',ln=1,align='C');
        pdf.set_font('Arial','',11); pdf.cell(0,8,f"Fecha {HOY}",ln=1,align='R')
        for titulo,df in bloques.items():
            pdf.ln(4); pdf.set_font('Arial','B',12); pdf.cell(0,8,f"{titulo} ({len(df)})",ln=1)
            pdf.set_font('Arial','',10)
            colw=max(25,pdf.w/(len(df.columns)+1)); rh=6
            pdf.set_fill_color(220,220,220)
            for col in df.columns: pdf.cell(colw,rh,str(col)[:25],1,0,'C',True)
            pdf.ln(rh); pdf.set_fill_color(255,255,255)
            for _,row in df.iterrows():
                for item in row: pdf.cell(colw,rh,str(item)[:25],1)
                pdf.ln(rh)
        st.download_button("⬇️ Reporte Diario PDF",pdf.output(dest='S').encode('latin1'),file_name="reporte_diario.pdf",mime="application/pdf")

# ---------- INFORME CLIENTE POR ENTREGAS ---------- #
elif menu=="Informe Cliente por Entregas":
    nombre=st.text_input("Nombre cliente")
    if st.button("Buscar entregas") and nombre:
        cli=clientes[clientes["Nombre y Apellidos"].str.contains(nombre,case=False,na=False)]
        if cli.empty:
            st.error("Cliente no encontrado")
        else:
            idc=cli.iloc[0]["ID Cliente"]
            df_cli=prendas[prendas["Nº Cliente (Formato C-xxx) "]==idc]
            fechas=df_cli["Fecha de recepción"].unique().tolist()
            seleccion=st.multiselect("Selecciona entregas",fechas)
            if seleccion:
                subset=df_cli[df_cli["Fecha de recepción"].isin(seleccion)]
                st.dataframe(subset)
                if st.button("📄 PDF Cliente x Entregas"):
                    titulo=f"Informe {cli.iloc[0]['Nombre y Apellidos']} - Entregas {', '.join(seleccion)}"
                    st.download_button("⬇️ Descargar PDF",pdf_tabla(subset,titulo),file_name="informe_lotes.pdf",mime="application/pdf")

st.markdown("---")
st.markdown("<div style='text-align:center;'>❤️ Nirvana Vintage 2025</div>",unsafe_allow_html=True)
