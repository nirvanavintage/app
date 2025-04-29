import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from fpdf import FPDF

# =====================
# Configuración general
# =====================

st.set_page_config(page_title="Nirvana Vintage", page_icon="✨", layout="wide")
HIDE_COLS_PATTERN = [
    "Marca temporal",
    "Merged Doc ID", "Merged Doc URL", "Link to merged Doc", "Document Merge Status"
]

# Función para limpiar DataFrame
def limpiar_df(df: pd.DataFrame) -> pd.DataFrame:
    cols_a_quitar = [c for c in df.columns for pat in HIDE_COLS_PATTERN if pat.lower() in c.lower()]
    return df.drop(columns=cols_a_quitar, errors="ignore")

# Función para generar PDF
def df_to_pdf(df, titulo, nombre_archivo):
    cols_mostrar = [c for c in df.columns if c not in [
        "Marca temporal",
        *df.columns[df.columns.str.startswith("Merged Doc")]
    ]]
    df = df[cols_mostrar]

    pdfkit_usable = False
    try:
        import pdfkit
        if os.path.exists('/usr/bin/wkhtmltopdf'):
            config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
            pdfkit_usable = True
    except Exception:
        pdfkit_usable = False
    
    if pdfkit_usable:
        try:
            css = """
            <style>
              body { font-family: Arial, sans-serif; }
              h2   { text-align:center; }
              table { border-collapse:collapse; width:100%; font-size:10px; }
              th, td { border:1px solid #666; padding:4px; }
              th { background:#eee; }
            </style>
            """
            html = f"<h2>{titulo}</h2>" + df.to_html(index=False)
            full_html = f"<html><head>{css}</head><body>{html}</body></html>"

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                pdfkit.from_string(full_html, tmp.name,
                                   configuration=config,
                                   options={"page-size": "A4",
                                            "orientation": "Landscape",
                                            "margin-top": "8mm",
                                            "margin-bottom": "8mm",
                                            "margin-left": "8mm",
                                            "margin-right": "8mm"})
                tmp.seek(0)
                st.download_button(
                    "📄 Descargar PDF",
                    tmp.read(),
                    file_name=nombre_archivo,
                    mime="application/pdf"
                )
                os.unlink(tmp.name)
            return
        except Exception as e:
            st.warning(f"No se pudo generar PDF bonito: {e}. Usando método alternativo.")

    # Fallback a FPDF si no hay pdfkit o falla
    pdf = FPDF(orientation="L")
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, titulo, ln=True, align="C")
    pdf.ln(4)

    col_w = pdf.w / (len(df.columns) + 1)
    for col in df.columns:
        pdf.cell(col_w, 6, str(col), border=1)
    pdf.ln()
    
    for _, row in df.iterrows():
        for item in row:
            pdf.cell(col_w, 5, str(item), border=1)
        pdf.ln()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        st.download_button(
            "📄 Descargar PDF (simple)",
            tmp.read(),
            file_name=nombre_archivo,
            mime="application/pdf"
        )
        os.unlink(tmp.name)
