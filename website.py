import streamlit as st
import reportlab.pdfgen.canvas as canvas
import tempfile
import os, sys, time, requests
from bs4 import BeautifulSoup
from datetime import date
import plotly.graph_objects as go

# ReportLab imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.units import inch

# --- Streamlit UI ---
st.title("RiceFort - Carbon Footprint Report")

# Instructions
st.write("Welcome to RiceFort! Please select the type of furniture, enter its dimensions, quantity, and client details.")

# Dropdown for furniture types
furniture_type = st.selectbox("Select Furniture Type", ["Chair", "Table", "Sofa", "Shelf", "Cabinet"])

# Client details
client_name = st.text_input("Client Name")
client_email = st.text_input("Client Email")
client_phone = st.text_input("Client Phone")

if client_phone and not client_phone.isdigit():
    st.error("Please enter numbers only for the phone number.")

# Dimensions inputs
length = st.number_input("Length (cm)", min_value=1.0, value=50.0)
width = st.number_input("Width (cm)", min_value=1.0, value=40.0)
height = st.number_input("Height (cm)", min_value=1.0, value=90.0)

# Quantity input
quantity = st.number_input("Quantity", min_value=1, value=1)

# Dynamic carbon footprint calculation
volume_m3 = (length * width * height) / 1_000_000  # cm to m³
density = 550  # kg/m³ for rice husk fiberboards
weight_per_unit = volume_m3 * density
ef = 0.55  # kg CO2e/kg
energy_factor = 0.05  # 0.1 kWh/kg * 0.5 kg CO2e/kWh
cf_per_unit = weight_per_unit * (ef + energy_factor)
total_weight = weight_per_unit * quantity
total_cf = cf_per_unit * quantity

# Competitor scraping
def scrape_competitors(furniture_type, weight_per_unit):
    # placeholder logic until you implement scraping
    comp_ef = 0.8  # kg CO2e/kg for particleboard
    return {
            "IKEA": {"Avg Price (HKD)": 499, "Est. CF per Unit (kg CO2e)": weight_per_unit * comp_ef},
            "Ulferts": {"Avg Price (HKD)": 3500, "Est. CF per Unit (kg CO2e)": weight_per_unit * comp_ef},
            "OVO": {"Avg Price (HKD)": 2500, "Est. CF per Unit (kg CO2e)": weight_per_unit * comp_ef},
        }

comp_data = scrape_competitors(furniture_type, weight_per_unit)

# --- Call your report generation function ---
def create_pdf(filename, furniture_type, dimensions, quantity, client_name,
               total_weight, total_cf, cf_per_unit,
               material, comp_data):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()

    # Custom styles for Times New Roman, 12pt
    header_style = ParagraphStyle(
        name='Header',
        fontName='Times-Bold',
        fontSize=12,
        leading=14,
        spaceAfter=12,
        alignment=TA_CENTER
    )
    normal_style = ParagraphStyle(
        name='Normal12',
        fontName='Times-Roman',
        fontSize=12,
        leading=14,
        spaceAfter=12,
        alignment=TA_JUSTIFY
    )
    heading_style = ParagraphStyle(
        name='Heading2',
        fontName='Times-Bold',
        fontSize=12,
        leading=14,
        spaceAfter=12
    )

    story = []

    # Header
    story.append(Paragraph("RiceFort Limited Carbon Footprint Report", header_style))
    story.append(Paragraph(f"Prepared for: {client_name}", normal_style))
    story.append(Paragraph(f"Focus: Environmental Sustainability for {furniture_type}", normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    exec_summary = (
        f"This report provides a comprehensive overview of the sustainability practices associated with the production of your furniture: "
        f"{quantity} units of {furniture_type} with dimensions {dimensions} cm. "
        f"Total material: {total_weight:.2f} kg. Total carbon footprint: {total_cf:.2f} kg CO2e. "
        f"We are committed to ensuring that our products not only meet the needs of yours but also contribute positively to the environment and society."
    )
    story.append(Paragraph(exec_summary, normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # Company Overview
    story.append(Paragraph("Company Overview", heading_style))
    overview = (
        "RiceFort Limited is Hong Kong's first bio-based materials research and development company focused on rice husk, "
        "dedicated to addressing the challenges of agricultural waste management and reducing carbon emissions. RiceFort aims to "
        "upgrade rice husks into valuable materials, primarily rice husk fiberboards, through structured processes focused on sustainability "
        "and resource utilization. By transforming rice husks into high-value products, RiceFort not only tackles the issue of agricultural "
        "waste management but also promotes a circular economy. This ensures materials are reused and recycled, protecting our forests and "
        "fostering environmental sustainability."
    )
    story.append(Paragraph(overview, normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # Environmental Methodology
    story.append(Paragraph("Environmental Methodology", heading_style))
    method = "Based on ISO 14067 cradle-to-gate. Emission factor: 0.55 kg CO2e/kg + energy emissions (0.05 kg CO2e/kg)."
    story.append(Paragraph(method, normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # Material Usage and Sourcing
    story.append(Paragraph("Material Usage and Sourcing", heading_style))
    material_text = f"Material: {material}, Total: {total_weight:.2f} kg from local rice husks (95% sourced from HK/Guangdong)."
    story.append(Paragraph(material_text, normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # Carbon Footprint Analysis
    story.append(Paragraph("Carbon Footprint Analysis", heading_style))
    cf_text = f"CF per unit: {cf_per_unit:.2f} kg CO2e, Total: {total_cf:.2f} kg CO2e for {quantity} units."
    story.append(Paragraph(cf_text, normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # Competitor Benchmarking
    story.append(Paragraph("Competitor Benchmarking", heading_style))
    data = [['Competitor', 'Avg Price (HKD)', 'Est. CF per Unit (kg CO2e)']]
    for comp, vals in comp_data.items():
        data.append([comp, f"{vals['Avg Price (HKD)']:.2f}", f"{vals['Est. CF per Unit (kg CO2e)']:.2f}"])
    t = Table(data)
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2 * inch))

    # Recommendations and Future Outlook
    story.append(Paragraph("Recommendations and Future Outlook", heading_style))
    rec = "Enhance traceability with blockchain by 2027; target 0.4 kg CO2e/kg by 2030 via solar processing."
    story.append(Paragraph(rec, normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # Appendices
    story.append(Paragraph("Appendices", heading_style))
    app = "Sources: ISO 14067, Climatiq database."
    story.append(Paragraph(app, normal_style))

    doc.build(story)
    return filename

# --- Streamlit button block ---
pdf_path = None
if st.button("Generate Carbon Footprint Report", key="generate_report"):
    dimensions = f"{length} x {width} x {height}"

    # Material info
    material = "Rice Husk Fiberboards"
    pdf_path = create_pdf("report.pdf", furniture_type, dimensions, quantity, client_name,
                          total_weight, total_cf, cf_per_unit,
                          material, comp_data)

if pdf_path:
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="Download Report",
                data=f.read(),
                file_name=f"Carbon_Footprint_Report_{furniture_type}_{date.today()}.pdf",
                mime="application/pdf"
            )
