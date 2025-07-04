import streamlit as st
from PIL import Image
import easyocr
import numpy as np
import pandas as pd
import io
import re
from collections import Counter
from pdf2image import convert_from_path
import os

st.set_page_config(page_title="Alfanar MEP OCR Analyzer", layout="wide")

# Load logo if present
logo_path = "alfanar-logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=150)

st.title("📐 Alfanar MEP Drawing Analyzer (Streamlit Cloud Ready)")

uploaded_files = st.file_uploader(
    "📤 Upload MEP PDF or Images", 
    type=["pdf", "png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

reader = easyocr.Reader(['en'], gpu=False)
all_data = []

if uploaded_files:
    for file in uploaded_files:
        ext = file.name.split(".")[-1].lower()
        images = []
        if ext == "pdf":
            with open("temp.pdf", "wb") as f:
                f.write(file.read())
            images = convert_from_path("temp.pdf", dpi=200)
        else:
            images = [Image.open(file)]

        for idx, image in enumerate(images):
            st.subheader(f"📷 {file.name} - Page {idx+1}")
            st.image(image, use_column_width=True)

            # OCR
            result = reader.readtext(np.array(image), detail=0)
            ocr_text = "\n".join(result)
            st.text_area("📝 OCR Output", ocr_text, height=200)

            # Extraction
            lines = ocr_text.upper().splitlines()
            labels = ['SAD', 'RAD', 'EAD', 'FAD', 'FD', 'VCD']
            detected = []
            airflows = []
            sizes = []

            for line in lines:
                for lbl in labels:
                    if lbl in line:
                        detected.append(lbl)
                flow = re.search(r"(\d+)\s*L/S", line)
                if flow:
                    airflows.append(int(flow.group(1)))
                size = re.search(r"(\d{2,4})\s*[xX*]\s*(\d{2,4})", line)
                if size:
                    sizes.append(f"{size.group(1)}x{size.group(2)}")

            st.write("✅ Labels:", detected)
            st.write("💨 Airflows:", airflows)
            st.write("📏 Sizes:", sizes)

            counts = Counter(detected)
            avg_flow = sum(airflows) // len(airflows) if airflows else 0
            main_size = sizes[0] if sizes else "N/A"

            for label in labels:
                all_data.append({
                    "File": file.name,
                    "Page": idx+1,
                    "Component": label,
                    "Count": counts[label],
                    "Average Airflow (L/s)": avg_flow if counts[label] else 0,
                    "Common Size": main_size if counts[label] else "N/A"
                })

if all_data:
    df = pd.DataFrame(all_data)
    st.subheader("📊 Summary Table")
    st.dataframe(df)

    towrite = io.BytesIO()
    df.to_excel(towrite, index=False)
    towrite.seek(0)
    st.download_button("📥 Download Excel Report", towrite, "MEP_summary.xlsx")
    
st.caption("© 2025 Alfanar MEP Analyzer")
