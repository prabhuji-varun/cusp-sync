# app.py  — CuspSync (Python Streamlit Edition)

import streamlit as st
import pandas as pd
import datetime
import io
from fpdf import FPDF
import base64

st.set_page_config(page_title="CuspSync", layout="wide")

# ========= Master Data =========
DEPARTMENTS = [
    "Oral Medicine",
    "Pedodontics",
    "Oral Surgery",
    "Periodontics",
    "Public Health Dentistry",
    "Conservative Dentistry and Endodontics",
    "Prosthodontics",
    "Orthodontics",
    "Oral Pathology",
    "Implantology",
]

DOCTORS = {
    "Oral Medicine": [
        "Dr. Ramesh Iyer","Dr. Sneha Pillai","Dr. Manoj Kumar","Dr. Anjali Rao",
        "Dr. Kavitha Nair","Dr. Rahul Menon"
    ],
    "Pedodontics": [
        "Dr. Priya Sharma","Dr. Sanjay Shetty","Dr. Shreya Dutta",
        "Dr. Aditya Mehta","Dr. Kiran Kumar","Dr. Neha Bansal"
    ],
    "Oral Surgery": [
        "Dr. Ravi Shankar","Dr. Meena Krishnan","Dr. Arvind Rao",
        "Dr. Suresh Patil","Dr. Divya Joshi","Dr. Ajay Singh"
    ],
    "Periodontics": [
        "Dr. Vinay Deshmukh","Dr. Ritu Patel","Dr. Sameer Joshi",
        "Dr. Gauri Kulkarni","Dr. Deepak Jain","Dr. Shruthi Nair"
    ],
    "Public Health Dentistry": [
        "Dr. Sudha Reddy","Dr. Karthik Rao","Dr. Meera Thomas",
        "Dr. Rohit Patel","Dr. Rekha Singh","Dr. Vishal Jain"
    ],
    "Conservative Dentistry and Endodontics": [
        "Dr. Varun Prabhuji","Dr. Sai Manaswini","Dr. Arvind Iyer",
        "Dr. Sneha Reddy","Dr. Rahul Das","Dr. Kavya Pillai"
    ],
    "Prosthodontics": [
        "Dr. Sandeep Shetty","Dr. Harini Raj","Dr. Raghav Gupta",
        "Dr. Tina Paul","Dr. Akshay Nair","Dr. Nisha Verma"
    ],
    "Orthodontics": [
        "Dr. Manjunath Rao","Dr. Shweta Sharma","Dr. Adarsh Bhat",
        "Dr. Divya Kapoor","Dr. Ramesh Nair","Dr. Snehal Shah"
    ],
    "Oral Pathology": [
        "Dr. Preeti Sharma","Dr. Arjun Menon","Dr. Priyanka Rao",
        "Dr. Vivek Nair","Dr. Sneha Krishnan","Dr. Kiran Das"
    ],
    "Implantology": [
        "Dr. Rohan Mehta","Dr. Anusha Nair","Dr. Vikram Rao",
        "Dr. Suma Iyer","Dr. Prakash Bhat","Dr. Neeta Menon"
    ],
}

COSTS = {
    "Radiograph":50,"Check up":50,"Scaling":500,"Extraction":100,
    "Flouride Application":300,"Pulpectomy":1000,"Pulpotomy":1000,
    "Crown Placement":1000,"Space Maintainer Placement":1500,
    "Fracture Stabilization":2000,"Suture Removal":0,"Scaling And Curettage":700,
    "Flap Surgery":1000,"Frenectomy":1000,"Bone Grafting":3000,
    "Counseling":0,"Follow Up":0,"Root Canal Treatment":1200,
    "Access Opening":0,"Working Length Determination":0,"BMP":0,
    "Obturation":0,"Post Endodontic Restoration":350,"Crown Preparation":0,
    "Crown Cementation":2000,"Impression Recorded":0,"Shade Selection":0,
    "Veneer Preparation":0,"Veneer Cementation":5000,"Composite Restoration":350,
    "Amalgam Restoration":250,"Inlay Preparation":0,"Inlay Cementation":300,
    "Post Space Preparation":0,"Post Cementation":1000,"Bleaching":1000,
    "Wax Pattern Recorded For Cast Post":0,"Irrigation":0,
    "Intracanal Medicament Placement":0,"Full Mouth Rehabilitation":100000,
    "Complete Denture":1000,"Removable Partial Denture":2500,"Over Denture":5000,
    "Fixed Orthodontic Treatment":10000,"Removable Orthodontic Treatment":2000,
    "Retainer Placement":500,"Photographs Taken":0,"Bracket Placement Done":0,
    "Biopsy":200,"Blood Investigation":200,"Implant":15000
}

DEPARTMENT_TREATMENTS = {
    "Oral Medicine":["Radiograph","Check up"],
    "Pedodontics":["Scaling","Extraction","Flouride Application","Pulpectomy",
                   "Pulpotomy","Crown Placement","Space Maintainer Placement"],
    "Oral Surgery":["Extraction","Fracture Stabilization","Suture Removal","Biopsy","Implant"],
    "Periodontics":["Scaling And Curettage","Flap Surgery","Frenectomy","Bone Grafting","Implant"],
    "Public Health Dentistry":["Counseling","Follow Up"],
    "Conservative Dentistry and Endodontics":[
        "Root Canal Treatment","Access Opening","Working Length Determination","BMP","Obturation",
        "Post Endodontic Restoration","Crown Preparation","Crown Cementation","Impression Recorded",
        "Shade Selection","Veneer Preparation","Veneer Cementation","Composite Restoration",
        "Amalgam Restoration","Inlay Preparation","Inlay Cementation","Post Space Preparation",
        "Post Cementation","Bleaching","Wax Pattern Recorded For Cast Post",
        "Irrigation","Intracanal Medicament Placement","Full Mouth Rehabilitation"
    ],
    "Prosthodontics":["Crown Preparation","Crown Cementation","Impression Recorded","Shade Selection",
                      "Complete Denture","Removable Partial Denture","Over Denture",
                      "Full Mouth Rehabilitation","Implant"],
    "Orthodontics":["Fixed Orthodontic Treatment","Removable Orthodontic Treatment",
                    "Retainer Placement","Photographs Taken","Bracket Placement Done"],
    "Oral Pathology":["Biopsy","Blood Investigation"],
    "Implantology":["Implant"]
}

# ========= State =========
# ========= Utility =========
def gen_id():
    today=datetime.date.today().strftime("%Y%m%d")
    count=sum(1 for p in st.session_state.patients if p["id"].startswith(f"P{today}-"))
    return f"P{today}-{count+1:03d}"

def cost_total(treats):
    if isinstance(treats, list):
        total = 0
        for t in treats:
            if isinstance(t, dict):
                total += COSTS.get(t.get("name", ""), 0)
            else:
                total += COSTS.get(t, 0)
        return total
    return 0

def df_patients():
    records = []
    for p in st.session_state.patients:
        for t in p["treatments"]:
            if isinstance(t, dict):
                records.append({
                    "id": p["id"],
                    "name": p["name"],
                    "age": p["age"],
                    "department": t.get("department", p["department"]),
                    "doctor": t.get("doctor", p["doctor"]),
                    "treatment": t.get("name", ""),
                    "cost": COSTS.get(t.get("name", ""), 0),
                    "date": p["date"]
                })
    df = pd.DataFrame(records)
    if not df.empty:
        df["Total"] = df["cost"]
    return df

DATA_FILE = "patients_db.csv"

def load_patients():
    try:
        df = pd.read_csv(DATA_FILE)
        df["treatments"] = df["treatments"].apply(lambda x: eval(x) if isinstance(x, str) else x)
        return df.to_dict(orient="records")
    except FileNotFoundError:
        return []

def save_patients():
    df = pd.DataFrame(st.session_state.patients)
    if not df.empty:
        df["treatments"] = df["treatments"].apply(lambda x: str(x))
        df.to_csv(DATA_FILE, index=False)

if "patients" not in st.session_state:
    st.session_state.patients = load_patients()
if "institute" not in st.session_state: st.session_state.institute=None

# ========= Sidebar =========
st.sidebar.title("🦷 CuspSync")
tab=st.sidebar.radio("Go to",["Register","History","Doctor Dashboard","Department Dashboard","Diagnostics"])

# ========= Institution Setup =========
if st.session_state.institute is None:
    st.header("Institution Registration")
    name = st.text_input("Institution / College / Hospital Name")
    address = st.text_area("Address")
    banner = st.file_uploader("Upload Banner (PNG/JPG)")

    if st.button("Save & Continue"):
        if name and address and banner:
            data = banner.read()
            b64 = base64.b64encode(data).decode()
            st.session_state.institute = {"name": name, "address": address, "banner": b64}
            st.success("✅ Institution details saved! Please click below to proceed.")
            st.stop()
        else:
            st.error("Please fill all fields and upload banner.")

    if st.session_state.institute:
        if st.button("Continue to App"):
            st.experimental_rerun()
        st.stop()

inst = st.session_state.institute

if inst is not None:
    if inst.get("banner"):
        st.image(io.BytesIO(base64.b64decode(inst["banner"])), use_column_width=True)
    st.title(f"🏥 {inst.get('name', '')}")
    st.caption(inst.get("address", ''))
else:
    st.warning("Please register your institution to proceed.")
    st.stop()

# ========= Register =========
if tab == "Register":
    st.subheader("Register / Follow-up Patient")

    # --- Step 1: Enter Patient ID ---
    pid = st.text_input("Patient ID (Leave blank for new patient)")
    existing = next((p for p in st.session_state.patients if p["id"] == pid), None) if pid else None

    # --- Step 2: Autofill patient info if found ---
    if existing:
        st.info(f"Existing patient found: {existing['name']}")
        name = st.text_input("Patient Name", value=existing["name"])
        age = st.number_input("Age", 0, 120, value=int(existing["age"]))
    else:
        name = st.text_input("Patient Name")
        age = st.number_input("Age", 0, 120, 25)

    # --- Step 3: Select department (live update) ---
    dept = st.selectbox("Department", DEPARTMENTS, key="dept_live")

    # --- Step 4: Doctor dropdown dynamically updates ---
    doc_list = DOCTORS[dept]
    default_doc = existing["doctor"] if existing and existing["doctor"] in doc_list else doc_list[0]
    doc = st.selectbox("Doctor", doc_list, index=doc_list.index(default_doc), key="doc_live")

    # --- Step 5: Treatment dropdown dynamically updates ---
    treat_list = DEPARTMENT_TREATMENTS[dept]
    treat_default = [t["name"] for t in (existing["treatments"] if existing else []) if t["name"] in treat_list] if existing else []
    treat = st.multiselect("Treatments", treat_list, default=treat_default, key="treat_live")

    # --- Step 6: Register / Update patient ---
    if st.button("Register / Route"):
        if not (name and doc and treat):
            st.error("Please fill all required fields.")
        else:
            if existing:
                existing.update({
                    "age": age, "department": dept, "doctor": doc,
                    "treatments": [{"name": t, "doctor": doc, "department": dept} for t in treat],
                    "date": datetime.date.today().isoformat()
                })
                st.success(f"Patient {name} updated successfully!")
                save_patients()
            else:
                st.session_state.patients.insert(0, {
                    "id": gen_id(), "name": name, "age": age, "department": dept,
                    "doctor": doc, "treatments": [{"name": t, "doctor": doc, "department": dept} for t in treat],
                    "date": datetime.date.today().isoformat()
                })
                st.success(f"New patient {name} registered successfully!")
                save_patients()

# ========= History =========
elif tab=="History":
    st.subheader("Patient History")
    df=df_patients()
    if df.empty:
        st.info("No patient records yet.")
    else:
        st.dataframe(df,use_container_width=True)
        # Excel download
        bio=io.BytesIO()
        with pd.ExcelWriter(bio,engine="openpyxl") as w: df.to_excel(w,index=False)
        st.download_button("📊 Download Excel",bio.getvalue(),
            "patient_history.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        from fpdf import FPDF

        # PDF generation with Unicode-safe font and margins
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.add_font("HeiseiKakuGo-W5", "", fname=None, uni=True)
        pdf.set_font("HeiseiKakuGo-W5", size=12)
        pdf.set_left_margin(10)
        pdf.set_right_margin(10)

        for _, r in df.iterrows():
            text = f"{r['id']} - {r['name']} ({r['department']}) Rs. {r['Total']}"
            safe_text = ''.join(ch if ord(ch) < 128 else '?' for ch in text)
            if len(safe_text) > 200:
                safe_text = safe_text[:200] + "..."
            try:
                pdf.multi_cell(0, 8, safe_text, align="L")
            except Exception:
                pdf.multi_cell(0, 8, "Error rendering text line.", align="L")

        pdf_output = pdf.output(dest="S")
        if isinstance(pdf_output, str):
            pdf_bytes = pdf_output.encode("latin1", "replace")
        elif isinstance(pdf_output, (bytes, bytearray)):
            pdf_bytes = bytes(pdf_output)
        else:
            pdf_bytes = b""

        st.download_button(
            "🖨 Download PDF",
            data=pdf_bytes,
            file_name="patient_history.pdf",
            mime="application/pdf"
        )

# ========= Doctor Dashboard =========
elif tab=="Doctor Dashboard":
    st.subheader("Doctor Dashboard")
    df = df_patients()
    if df.empty:
        st.info("No data yet.")
    else:
        doctor_summary = df.groupby(["doctor","department"]).agg(Cases=("treatment","count"),Revenue=("cost","sum")).reset_index()
        doctor_sel = st.selectbox("Select Doctor", sorted(doctor_summary["doctor"].unique()))
        df_doc = doctor_summary[doctor_summary["doctor"] == doctor_sel]
        st.dataframe(df_doc, use_container_width=True)
        st.bar_chart(df_doc.set_index("department")[["Cases","Revenue"]])

        bio = io.BytesIO()
        with pd.ExcelWriter(bio, engine="openpyxl") as w:
            df_doc.to_excel(w, index=False)
        st.download_button("📊 Download Excel", bio.getvalue(),
                           "doctor_dashboard.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.add_font("HeiseiKakuGo-W5", "", fname=None, uni=True)
        pdf.set_font("HeiseiKakuGo-W5", size=12)
        for _, r in df_doc.iterrows():
            line = " | ".join([f"{col}: {r[col]}" for col in df_doc.columns])
            pdf.multi_cell(0, 8, line)
        pdf_bytes = pdf.output(dest="S").encode("latin1", "replace")
        st.download_button("🖨 Download PDF", data=pdf_bytes,
                           file_name="doctor_dashboard.pdf",
                           mime="application/pdf")

# ========= Department Dashboard =========
elif tab=="Department Dashboard":
    st.subheader("Department Dashboard")
    df = df_patients()
    if df.empty:
        st.info("No data yet.")
    else:
        dept_summary = df.groupby("department").agg(Cases=("treatment","count"),Revenue=("cost","sum")).reset_index()
        st.dataframe(dept_summary, use_container_width=True)
        st.bar_chart(dept_summary.set_index("department")[["Cases","Revenue"]])

        bio = io.BytesIO()
        with pd.ExcelWriter(bio, engine="openpyxl") as w:
            dept_summary.to_excel(w, index=False)
        st.download_button("📊 Download Excel", bio.getvalue(),
                           "department_dashboard.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.add_font("HeiseiKakuGo-W5", "", fname=None, uni=True)
        pdf.set_font("HeiseiKakuGo-W5", size=12)
        for _, r in dept_summary.iterrows():
            line = " | ".join([f"{col}: {r[col]}" for col in dept_summary.columns])
            pdf.multi_cell(0, 8, line)
        pdf_bytes = pdf.output(dest="S").encode("latin1", "replace")
        st.download_button("🖨 Download PDF", data=pdf_bytes,
                           file_name="department_dashboard.pdf",
                           mime="application/pdf")

# ========= Diagnostics =========
elif tab=="Diagnostics":
    st.subheader("System Diagnostics Summary")
    cols=st.columns(2)
    for i,d in enumerate(DEPARTMENTS):
        with cols[i%2]:
            st.markdown(f"### {d}")
            st.write(f"Doctors : {len(DOCTORS[d])}")
            st.write(f"Treatments : {len(DEPARTMENT_TREATMENTS[d])}")
