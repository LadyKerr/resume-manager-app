# Resume Manager App

A Streamlit application that allows users to manage their resume data and export it as a PDF.

## Features
- Upload and parse existing resumes (PDF/DOCX)
- Edit resume information through a user-friendly form
- Export resume as PDF
- Store resume data in JSON format

## Getting Started

### Prerequisites
- Python 3.x
- pip3

### Installation

1. Clone the repository
```bash
git clone https://github.com/LadyKerr/resume-manager-app.git
cd resume-manager-app
```

2. Install dependencies
```bash
pip3 install -r requirements.txt
```

3. Run the application
```bash
streamlit run app.py
```

## Usage
1. Upload your existing resume (PDF/DOCX)
2. Edit your resume information using the form interface
3. Export your resume as PDF

## Technologies Used
- Python
- Streamlit - For the web interface
- FPDF - For PDF generation
- python-docx - For parsing DOCX files
- pdfplumber - For parsing PDF files
