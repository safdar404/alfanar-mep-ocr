# Alfanar MEP OCR Analyzer

This is a Streamlit web app to extract airflow and duct size data from mechanical drawings using OCR.

## Features
- Upload PDF or images
- Auto-extracts "SAD", "RAD", etc. and airflow/sizes
- Download Excel summary
- Uses OCR.space API (no Tesseract installation needed)

## To Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

© 2025 Alfanar GIS Team
