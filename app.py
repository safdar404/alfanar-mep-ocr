import streamlit as st
import requests
import cv2
import numpy as np
import pandas as pd
from PIL import Image as PILImage
from pdf2image import convert_from_path
import re
from collections import Counter
import io
import os

st.set_page_config(page_title="Alfanar MEP OCR Analyzer", layout="wide")

# --- Branding ---
logo_path = "alfanar-logo.png"
if os.path.exists(logo_path):
    logo_img = PILImage.open(logo_path)
    st.image(logo_img, width=150)
st.title("📐 Alfanar MEP Drawing Analyzer (OCR Powered via API)")

# --- File uploader ---
uploaded_files = st.file_uploader(
    "Upload MEP PDFs or Images", 
    type=["pdf", "png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

all_data = []

def run_ocr_space(img_bytes):
    api_key = 'helloworld'  # Use your own OCR.space API key for production
    payload = {
        'isOverlayRequired': False,
        'apikey': api_key,
        'language': 'eng',
    }
    files = {
        'file': ('image.jpg', img_bytes)
    }
    r = requests.post('https://api.ocr.space/parse/image', data=payload, files=files)
    result = r.json()
    try:
        return result['ParsedResults'][0]['ParsedText']
    except:
        return ""

if uploaded_files:
    for uploaded_file in uploaded_files:
        ext = uploaded_file.name.split(".")[-1].lower()
        images = []
        if ext == "pdf":
            with open("temp.pdf", "wb") as f:
                f.write(uploaded_file.getbuffer())
            images = convert_from_path("temp.pdf", dpi=200)
        else:
            images = [PILImage.open(uploaded_file)]

        for page_num, image in enumerate(images, start=1):
            st.markdown(f"### File: {uploaded_file.name} - Page {page_num}")
            st.image(image, caption="📷 Original Drawing", use_column_width=True)

            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (1000, 1000), interpolation=cv2.INTER_AREA)
            _, thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            pil_thresh = PILImage.fromarray(thresh)

            buf = io.BytesIO()
            pil_thresh.save(buf, format='JPEG')
            img_bytes = buf.getvalue()

            with st.spinner("🔍 Running OCR..."):
                ocr_text = run_ocr_space(img_bytes)

            st.subheader("📝 OCR Text")
            st.text_area("OCR Output", ocr_text, height=150)

            # Extraction
            text_lines = ocr_text.upper().splitlines()
            labels = ['SAD', 'RAD', 'EAD', 'FAD', 'FD', 'VCD']
            detected_labels, airflows, sizes = [], [], []

            for line in text_lines:
                for label in labels:
                    if label in line:
                        detected_labels.append(label)
                match_flow = re.search(r"(\d+)\s*L/S", line)
                if match_flow:
                    airflows.append(int(match_flow.group(1)))
                match_size = re.search(r"(\d{2,4})\s*[xX*]\s*(\d{2,4})", line)
                if match_size:
                    sizes.append(f"{match_size.group(1)}x{match_size.group(2)}")

            st.write("✅ Detected Labels:", detected_labels)
            st.write("💨 Airflows:", airflows)
            st.write("📏 Sizes:", sizes)

            label_counts = Counter(detected_labels)
            avg_air = sum(airflows) // len(airflows) if airflows else 0
            common_size = sizes[0] if sizes else "N/A"

            for label in labels:
                all_data.append({
                    "File": uploaded_file.name,
                    "Page": page_num,
                    "Component": label,
                    "Count": label_counts[label],
                    "Average Airflow (L/s)": avg_air if label_counts[label] else 0,
                    "Common Size": common_size if label_counts[label] else "N/A"
                })

    if all_data:
        df_all = pd.DataFrame(all_data)
        st.subheader("📊 Summary Table")
        st.dataframe(df_all, use_container_width=True)

        towrite = io.BytesIO()
        df_all.to_excel(towrite, index=False)
        towrite.seek(0)
        st.download_button("📥 Download Excel", towrite, "summary.xlsx", mime="application/vnd.ms-excel")

st.markdown("---")
st.caption("© 2025 Alfanar MEP Analyzer | Powered by OCR.space API")
