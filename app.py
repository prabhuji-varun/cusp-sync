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
if "patients" not in st.session_state: st.session_state.patients=[]
if "institute" not in st.session_state: st.session_state.institute=None

# ========= Utility =========
def gen_id():
    today=datetime.date.today().strftime("%Y%m%d")
    count=sum(1 for p in st.session_state.patients if p["id"].startswith(f"P{today}-"))
    return f"P{today}-{count+1:03d}"

def cost_total(treats):
    return sum(COSTS.get(t,0) for t in treats)

def df_patients():
    if not st.session_state.patients: return pd.DataFrame()
    df=pd.DataFrame(st.session_state.patients)
    df["Total"]=df["treatments"].apply(cost_total)
    return df

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
    treat_default = [t for t in (existing["treatments"] if existing else []) if t in treat_list]
    treat = st.multiselect("Treatments", treat_list, default=treat_default, key="treat_live")

    # --- Step 6: Register / Update patient ---
    if st.button("Register / Route"):
        if not (name and doc and treat):
            st.error("Please fill all required fields.")
        else:
            if existing:
                existing.update({
                    "age": age, "department": dept, "doctor": doc, "treatments": treat,
                    "date": datetime.date.today().isoformat()
                })
                st.success(f"Patient {name} updated successfully!")
            else:
                st.session_state.patients.insert(0, {
                    "id": gen_id(), "name": name, "age": age, "department": dept,
                    "doctor": doc, "treatments": treat, "date": datetime.date.today().isoformat()
                })
                st.success(f"New patient {name} registered successfully!")

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
        # PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)

        for _, r in df.iterrows():
            # Replace special characters with ASCII-safe equivalents
            line = f"{r['id']} - {r['name']} ({r['department']}) Rs. {r['Total']}"
            pdf.multi_cell(0, 8, line)

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
    df=df_patients()
    if df.empty: st.info("No data yet.")
    else:
        doc_sel=st.selectbox("Select Doctor",sorted(df["doctor"].unique()))
        df_doc=df[df["doctor"]==doc_sel]
        total_cases=len(df_doc)
        revenue=int(df_doc["Total"].sum())
        st.metric("Total Cases",total_cases)
        st.metric("Total Revenue (₹)",revenue)
        st.bar_chart(df_doc.explode("treatments")["treatments"].value_counts())

# ========= Department Dashboard =========
elif tab=="Department Dashboard":
    st.subheader("Department Dashboard")
    df=df_patients()
    if df.empty: st.info("No data yet.")
    else:
        df_sum=df.groupby("department").agg(Cases=("id","count"),Revenue=("Total","sum"))
        st.bar_chart(df_sum)
        st.dataframe(df_sum)

# ========= Diagnostics =========
elif tab=="Diagnostics":
    st.subheader("System Diagnostics Summary")
    cols=st.columns(2)
    for i,d in enumerate(DEPARTMENTS):
        with cols[i%2]:
            st.markdown(f"### {d}")
            st.write(f"Doctors : {len(DOCTORS[d])}")
            st.write(f"Treatments : {len(DEPARTMENT_TREATMENTS[d])}")
