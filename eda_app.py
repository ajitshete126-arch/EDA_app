# save this as eda_app.py

import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
from itertools import combinations
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# Extra for PDF table extraction
try:
    import camelot
except:
    camelot = None

# Page config
st.set_page_config(page_title="EDA Web App", layout="wide")

# App title
st.title("📊 Exploratory Data Analysis (EDA) Web App")

# File uploader (CSV + Excel + PDF)
uploaded_file = st.file_uploader("Upload your CSV, Excel, or PDF file", type=["csv", "xlsx", "xls", "pdf"])

# Google Sheets link input
sheet_url = st.text_input("Or paste a Google Sheets link (must be public/shareable):")

df = None

if uploaded_file:
    if uploaded_file.name.endswith(".pdf"):
        if camelot is None:
            st.error("⚠️ Please install camelot: pip install camelot-py[cv]")
        else:
            try:
                tables = camelot.read_pdf(uploaded_file, pages="all")
                if tables and len(tables) > 0:
                    df = tables[0].df  # take first table
                    st.success("✅ Loaded table from PDF successfully")
                else:
                    st.error("❌ No tables found in PDF")
            except Exception as e:
                st.error(f"PDF reading failed: {e}")
    else:
        # Try CSV first
        encodings_to_try = ["utf-8", "utf-8-sig", "latin1", "ISO-8859-1", "cp1252"]
        for enc in encodings_to_try:
            try:
                df = pd.read_csv(uploaded_file, encoding=enc, on_bad_lines="skip")
                st.success(f"✅ File loaded successfully as CSV using {enc} encoding")
                break
            except Exception:
                df = None

        # If CSV failed → try Excel
        if df is None:
            try:
                df = pd.read_excel(uploaded_file, engine="openpyxl")
                st.success("✅ File loaded successfully as Excel")
            except Exception:
                df = None

elif sheet_url:
    try:
        if "docs.google.com" in sheet_url:
            if "export?format=csv" not in sheet_url:
                sheet_url = sheet_url.replace("/edit#gid=", "/export?format=csv&gid=")
            df = pd.read_csv(sheet_url)
            st.success("✅ Loaded Google Sheet successfully")
        else:
            st.error("❌ Please enter a valid Google Sheets link")
    except Exception as e:
        st.error(f"Failed to load Google Sheet: {e}")

# Proceed only if DataFrame loaded
if df is not None:
    # Data preview
    st.subheader("👀 Data Preview")
    st.write(df.head())
    st.write(f"**Shape:** {df.shape}")
    st.write(f"**Columns:** {list(df.columns)}")

    # Summary statistics
    st.subheader("📈 Summary Statistics")
    try:
        st.write(df.describe(include="all"))
    except Exception:
        st.warning("⚠️ Could not generate statistics for this dataset")

    # Missing values
    st.subheader("❌ Missing Values")
    missing = df.isnull().sum()
    st.write(missing)

    # 🔁 Duplicate values
    st.subheader("🔁 Duplicate Values")
    duplicate_count = df.duplicated().sum()
    st.write(f"**Number of duplicate rows:** {duplicate_count}")
    if duplicate_count > 0:
        st.write("Duplicate rows:")
        st.write(df[df.duplicated()])

    # 📊 Histogram (interactive)
    st.subheader("📊 Histogram")
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if numeric_cols:
        hist_col = st.selectbox("Select a column for histogram:", options=numeric_cols, key="hist")
        fig, ax = plt.subplots()
        sns.histplot(df[hist_col], kde=True, ax=ax)
        st.pyplot(fig)
    else:
        st.warning("No numeric columns available for histogram.")

    # 📉 Bar Chart (interactive)
    st.subheader("📉 Bar Chart")
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    if cat_cols:
        bar_col = st.selectbox("Select a categorical column for bar chart:", options=cat_cols, key="bar")
        fig, ax = plt.subplots()
        df[bar_col].value_counts().plot(kind='bar', ax=ax)
        ax.set_ylabel("Count")
        ax.set_xlabel(bar_col)
        st.pyplot(fig)
    else:
        st.warning("No categorical columns available for bar chart.")

    # 🥧 Pie Chart (interactive)
    st.subheader("🥧 Pie Chart")
    if cat_cols:
        pie_col = st.selectbox("Select a categorical column for pie chart:", options=cat_cols, key="pie")
        pie_data = df[pie_col].value_counts()
        fig, ax = plt.subplots()
        ax.pie(pie_data, labels=pie_data.index, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)
    else:
        st.warning("No categorical columns available for pie chart.")

    # 🔵 Scatter Plot (interactive)
    st.subheader("🔵 Scatter Plot")
    col1, col2 = st.columns(2)
    with col1:
        x_axis = st.selectbox("Choose X-axis (numeric):", options=numeric_cols, key="scatter_x")
    with col2:
        y_axis = st.selectbox("Choose Y-axis (numeric):", options=numeric_cols, key="scatter_y")

    if x_axis and y_axis:
        fig, ax = plt.subplots()
        sns.scatterplot(data=df, x=x_axis, y=y_axis, ax=ax)
        st.pyplot(fig)

    # 📥 Export EDA Summary to PDF
    st.subheader("📥 Export EDA Report as PDF")

    def create_pdf():
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("📊 EDA Report", styles['Title']))
        elements.append(Spacer(1, 12))

        # Dataset info
        elements.append(Paragraph(f"Shape: {df.shape}", styles['Normal']))
        elements.append(Paragraph(f"Columns: {list(df.columns)}", styles['Normal']))
        elements.append(Spacer(1, 12))

        # Missing values
        elements.append(Paragraph("❌ Missing Values", styles['Heading2']))
        miss_table = [["Column", "Missing Count"]] + [[col, val] for col, val in missing.items()]
        table = Table(miss_table)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.grey),
                                   ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                                   ('ALIGN',(0,0),(-1,-1),'CENTER'),
                                   ('GRID',(0,0),(-1,-1),1,colors.black)]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        # Duplicate values
        elements.append(Paragraph("🔁 Duplicate Values", styles['Heading2']))
        elements.append(Paragraph(f"Number of duplicate rows: {duplicate_count}", styles['Normal']))

        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    pdf_data = create_pdf()

    st.download_button(
        label="📄 Download Full EDA Report as PDF",
        data=pdf_data,
        file_name="EDA_Report.pdf",
        mime="application/pdf"
    )

