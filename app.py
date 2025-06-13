import streamlit as st
import json
import os
from fpdf import FPDF
import pdfplumber
from docx import Document
import re
import itertools

RESUME_FILE = "resume.json"

def load_resume():
    if not os.path.exists(RESUME_FILE):
        return {}
    with open(RESUME_FILE, "r") as f:
        return json.load(f)

def save_resume(data):
    with open(RESUME_FILE, "w") as f:
        json.dump(data, f, indent=2)

def export_pdf(data):
    def clean_text(text):
        """Clean text to be compatible with FPDF"""
        return (str(text)
                .replace("•", "-")  # Replace bullets
                .replace("–", "-")  # Replace en-dash
                .replace("'", "'")  # Replace smart quotes
                .replace(""", '"')  # Replace smart quotes
                .replace(""", '"')  # Replace smart quotes
                .encode('latin-1', 'replace').decode('latin-1'))

    pdf = FPDF()
    pdf.add_page()
    
    # Header - Personal Info
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(200, 10, txt=clean_text(data.get("name", "")), ln=True, align='C')
    
    # Contact Info
    pdf.set_font("Arial", size=10)
    contact = data.get("contact", {})
    contact_info = [
        contact.get("email", ""),
        contact.get("phone", ""),
        contact.get("address", "")
    ]
    for info in contact_info:
        if info:
            pdf.cell(200, 6, txt=clean_text(info), ln=True, align='C')
    
    # Summary
    if data.get("summary"):
        pdf.ln(5)
        pdf.set_font("Arial", "B", size=12)
        pdf.cell(0, 10, "Summary", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 5, txt=clean_text(data.get("summary", "")))
    
    # Sections
    sections = data.get("sections", {})
    for section_name, items in sections.items():
        if items:  # Only show non-empty sections
            pdf.ln(5)
            pdf.set_font("Arial", "B", size=12)
            pdf.cell(0, 10, clean_text(section_name), ln=True)
            pdf.set_font("Arial", size=10)
            
            if section_name == "Employment History":
                for job in items:
                    job_title = f"{job.get('title')} at {job.get('company')}"
                    if job.get('location'):
                        job_title += f", {job.get('location')}"
                    pdf.cell(0, 6, clean_text(job_title), ln=True)
                    date_range = f"{job.get('start', '')} - {job.get('end', 'Present')}"
                    pdf.cell(0, 6, clean_text(date_range), ln=True)
                    pdf.ln(2)
            else:
                for item in items:
                    if isinstance(item, str):
                        pdf.cell(0, 6, txt=f"- {clean_text(item)}", ln=True)
            pdf.ln(2)

    pdf.output("resume.pdf")
    return "resume.pdf"

def parse_resume_text(text):
    # Extract name (first non-empty line after 'Functional Resume Sample')
    name = ""
    contact = {"address": "", "email": "", "phone": ""}
    summary = ""
    sections = {}
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    # Find name
    for i, line in enumerate(lines):
        if "Functional Resume Sample" in line:
            name = lines[i+1] if i+1 < len(lines) else ""
            break
    # Find email
    for line in lines:
        email = re.search(r"[\w\.-]+@[\w\.-]+", line)
        if email:
            contact["email"] = email.group(0)
            break
    # Find address (line after name)
    for i, line in enumerate(lines):
        if name and line == name and i+1 < len(lines):
            contact["address"] = lines[i+1]
            break
    # Find summary
    for i, line in enumerate(lines):
        if "Career Summary" in line:
            summary = lines[i+1] if i+1 < len(lines) else ""
            break
    # Section parsing
    def extract_section(header):
        for i, line in enumerate(lines):
            if header in line:
                bullets = []
                for l in lines[i+1:]:
                    if l.startswith("•") or l.startswith("-"):
                        bullets.append(l.lstrip("•-").strip())
                    elif l == "" or l.endswith(":"):
                        break
                return bullets
        return []
    sections["Adult Care Experience"] = extract_section("Adult Care Experience")
    sections["Childcare Experience"] = extract_section("Childcare Experience")
    # Employment History
    employment = []
    for i, line in enumerate(lines):
        if "Employment History" in line:
            for l in lines[i+1:]:
                m = re.match(r"(\d{4})-(\d{4}|Present)\s+(.+?),\s+(.+?),\s+(.+)", l)
                if m:
                    employment.append({
                        "start": m.group(1),
                        "end": m.group(2),
                        "title": m.group(3),
                        "company": m.group(4),
                        "location": m.group(5)
                    })
                else:
                    m2 = re.match(r"(\d{4})-(\d{4}|Present)\s+(.+)", l)
                    if m2:
                        employment.append({
                            "start": m2.group(1),
                            "end": m2.group(2),
                            "title": m2.group(3),
                            "company": "",
                            "location": ""
                        })
                if l.startswith("Education"):
                    break
    sections["Employment History"] = employment
    # Education
    education = []
    for i, line in enumerate(lines):
        if "Education" in line:
            for l in lines[i+1:]:
                if l.startswith("•") or l.startswith("-"):
                    education.append(l.lstrip("•-").strip())
    sections["Education"] = education
    return {
        "name": name,
        "contact": contact,
        "summary": summary,
        "sections": sections
    }

def parse_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    return parse_resume_text(text)

def parse_docx(file):
    doc = Document(file)
    text = "\n".join([para.text for para in doc.paragraphs])
    return parse_resume_text(text)

def main():
    st.title("Auto-Updating Resume App")
    data = load_resume()

    st.header("Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF or DOCX Resume", type=["pdf", "docx"])
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            parsed = parse_pdf(uploaded_file)
        elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            parsed = parse_docx(uploaded_file)
        else:
            st.error("Unsupported file type.")
            return
        data.update(parsed)
        save_resume(data)
        st.success("Resume parsed and saved!")
        st.rerun()

    st.header("Personal Info")
    name = st.text_input("Name", value=data.get("name", ""))
    email = st.text_input("Email", value=data.get("email", ""))
    phone = st.text_input("Phone", value=data.get("phone", ""))
    summary = st.text_area("Summary", value=data.get("summary", ""))

    st.header("Sections")
    sections = data.get("sections", {})
    for section_name, section_content in sections.items():
        with st.expander(section_name):
            if isinstance(section_content, list):
                for item in section_content:
                    st.write(f"• {item}")
            else:
                st.write(section_content)

    if st.button("Save Personal Info"):
        data["name"] = name
        data["email"] = email
        data["phone"] = phone
        data["summary"] = summary
        save_resume(data)
        st.success("Personal info saved!")

    if st.button("Export as PDF"):
        pdf_path = export_pdf(data)
        with open(pdf_path, "rb") as f:
            st.download_button("Download PDF", f, file_name="resume.pdf")

    st.header("Edit Resume")
    with st.form("edit_resume_form"):
        # Name
        name = st.text_input("Name", value=data.get("name", ""))
        # Contact
        contact = data.get("contact", {})
        address = st.text_input("Address", value=contact.get("address", ""))
        email = st.text_input("Email", value=contact.get("email", ""))
        phone = st.text_input("Phone", value=contact.get("phone", ""))
        # Summary
        summary = st.text_area("Summary", value=data.get("summary", ""))
        # Sections
        sections = data.get("sections", {})
        # Adult Care Experience
        ace = sections.get("Adult Care Experience", [])
        st.markdown("**Adult Care Experience**")
        ace_inputs = []
        for i, item in enumerate(ace):
            ace_inputs.append(st.text_area(f"Adult Care Experience #{i+1}", value=item, key=f"ace_{i}"))
        new_ace = st.text_area("Add new Adult Care Experience", value="", key="ace_new")
        # Childcare Experience
        cce = sections.get("Childcare Experience", [])
        st.markdown("**Childcare Experience**")
        cce_inputs = []
        for i, item in enumerate(cce):
            cce_inputs.append(st.text_area(f"Childcare Experience #{i+1}", value=item, key=f"cce_{i}"))
        new_cce = st.text_area("Add new Childcare Experience", value="", key="cce_new")
        # Employment History
        st.markdown("**Employment History**")
        employment = sections.get("Employment History", [])
        emp_inputs = []
        for i, job in enumerate(employment):
            with st.expander(f"Job #{i+1}"):
                title = st.text_input("Title", value=job.get("title", ""), key=f"emp_title_{i}")
                company = st.text_input("Company", value=job.get("company", ""), key=f"emp_company_{i}")
                location = st.text_input("Location", value=job.get("location", ""), key=f"emp_location_{i}")
                start = st.text_input("Start Year", value=job.get("start", ""), key=f"emp_start_{i}")
                end = st.text_input("End Year", value=job.get("end", ""), key=f"emp_end_{i}")
                emp_inputs.append({"title": title, "company": company, "location": location, "start": start, "end": end})
        with st.expander("Add new Employment History"):
            new_title = st.text_input("Title", value="", key="emp_title_new")
            new_company = st.text_input("Company", value="", key="emp_company_new")
            new_location = st.text_input("Location", value="", key="emp_location_new")
            new_start = st.text_input("Start Year", value="", key="emp_start_new")
            new_end = st.text_input("End Year", value="", key="emp_end_new")
        # Education
        st.markdown("**Education**")
        education = sections.get("Education", [])
        edu_inputs = []
        for i, item in enumerate(education):
            edu_inputs.append(st.text_area(f"Education #{i+1}", value=item, key=f"edu_{i}"))
        new_edu = st.text_area("Add new Education", value="", key="edu_new")
        submitted = st.form_submit_button("Save All Changes")
        if submitted:
            # Update all fields
            data["name"] = name
            data["contact"] = {"address": address, "email": email, "phone": phone}
            data["summary"] = summary
            # Update sections
            updated_sections = {}
            updated_sections["Adult Care Experience"] = [x for x in ace_inputs if x.strip()]
            if new_ace.strip():
                updated_sections["Adult Care Experience"].append(new_ace.strip())
            updated_sections["Childcare Experience"] = [x for x in cce_inputs if x.strip()]
            if new_cce.strip():
                updated_sections["Childcare Experience"].append(new_cce.strip())
            updated_sections["Employment History"] = [x for x in emp_inputs if any(x.values())]
            if new_title or new_company or new_location or new_start or new_end:
                if any([new_title, new_company, new_location, new_start, new_end]):
                    updated_sections["Employment History"].append({
                        "title": new_title, "company": new_company, "location": new_location, "start": new_start, "end": new_end
                    })
            updated_sections["Education"] = [x for x in edu_inputs if x.strip()]
            if new_edu.strip():
                updated_sections["Education"].append(new_edu.strip())
            data["sections"] = updated_sections
            save_resume(data)
            st.success("Resume updated!")
            st.rerun()

if __name__ == "__main__":
    main()
