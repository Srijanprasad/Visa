import streamlit as st
from datetime import date
import time
import os
import json
from io import BytesIO
import requests
from uuid import uuid4
from pinecone import Pinecone
import torch

# ================= 1. INITIAL CONFIG & GDS THEME =================
st.set_page_config(
    page_title="Check UK Visa Eligibility - GOV.UK", 
    layout="wide", 
    page_icon="🇬🇧"
)

# Load environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "visa-rag-index"
EMBEDDING_DIM = 384

# Initialize Session State
if 'common' not in st.session_state: st.session_state['common'] = {}
if 'eligibility' not in st.session_state: st.session_state['eligibility'] = {}
if 'messages' not in st.session_state: st.session_state['messages'] = []
if 'assessment_complete' not in st.session_state: st.session_state['assessment_complete'] = False
if 'assessment_results' not in st.session_state: st.session_state['assessment_results'] = {}

# ================= EMBEDDINGS & PINECONE ================
@st.cache_resource
def load_embeddings():
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"}
    )

@st.cache_resource
def init_pinecone():
    if not PINECONE_API_KEY:
        return None
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index_names = [i["name"] for i in pc.list_indexes()]
        
        if INDEX_NAME not in index_names:
            pc.create_index(
                name=INDEX_NAME,
                dimension=EMBEDDING_DIM,
                metric="cosine",
                spec={"serverless": {"cloud": "aws", "region": "us-east-1"}}
            )
        
        return pc.Index(INDEX_NAME)
    except Exception as e:
        st.sidebar.error(f"Pinecone init failed: {str(e)}")
        return None

# Load resources
try:
    embeddings = load_embeddings()
    pinecone_index = init_pinecone()
except Exception as e:
    embeddings = None
    pinecone_index = None

def assess_graduate():
    data = st.session_state['eligibility']
    required_yes = ['currently_in_uk', 'course_completed', 'education_provider_is_licensed', 'provider_reported_completion_to_home_office', 'student_visa_valid_on_application_date']
    required_text = ['course_level_completed', 'original_cas_reference']
    missing = []
    for f in required_yes + required_text:
        val = data.get(f, '')
        if val == '' or (f in required_yes and val not in ['Yes', 'No']):
            missing.append(f)
    if missing:
        status = "Cannot Be Determined"
        rationale = f"Cannot be determined from given data due to missing entities: {', '.join(missing)}."
    else:
        all_yes = all(data[f] == 'Yes' for f in required_yes)
        if all_yes:
            status = "Eligible"
            rationale = f"Eligibility determined as Eligible because currently_in_uk = {data['currently_in_uk']}, course_completed = {data['course_completed']}, education_provider_is_licensed = {data['education_provider_is_licensed']}, provider_reported_completion_to_home_office = {data['provider_reported_completion_to_home_office']}, student_visa_valid_on_application_date = {data['student_visa_valid_on_application_date']}, and required text fields are provided."
        else:
            status = "Not Eligible"
            no_fields = [f for f in required_yes if data[f] == 'No']
            rationale = f"Eligibility determined as Not Eligible because {' = No, '.join(no_fields)} = No."
    return status, rationale, missing

def assess_student():
    data = st.session_state['eligibility']
    required_yes = ['has_cas', 'education_provider_is_licensed', 'course_full_time', 'meets_financial_requirement', 'funds_held_for_28_days', 'english_requirement_met']
    required_text = ['cas_reference_number', 'course_level']
    missing = []
    for f in required_yes + required_text:
        val = data.get(f, '')
        if val == '' or (f in required_yes and val not in ['Yes', 'No']):
            missing.append(f)
    if missing:
        status = "Cannot Be Determined"
        rationale = f"Cannot be determined from given data due to missing entities: {', '.join(missing)}."
    else:
        all_yes = all(data[f] == 'Yes' for f in required_yes)
        if all_yes:
            status = "Eligible"
            rationale = f"Eligibility determined as Eligible because has_cas = {data['has_cas']}, education_provider_is_licensed = {data['education_provider_is_licensed']}, course_full_time = {data['course_full_time']}, meets_financial_requirement = {data['meets_financial_requirement']}, funds_held_for_28_days = {data['funds_held_for_28_days']}, english_requirement_met = {data['english_requirement_met']}, and required fields are provided."
        else:
            status = "Not Eligible"
            no_fields = [f for f in required_yes if data[f] == 'No']
            rationale = f"Eligibility determined as Not Eligible because {' = No, '.join(no_fields)} = No."
    return status, rationale, missing

def assess_skilled_worker():
    data = st.session_state['eligibility']
    required_yes = ['job_offer_confirmed', 'employer_is_licensed_sponsor', 'certificate_of_sponsorship_issued', 'job_is_eligible_occupation', 'meets_minimum_salary_threshold', 'english_requirement_met', 'criminal_record_certificate_required', 'criminal_record_certificate_provided']
    required_text = ['cos_reference_number', 'job_title', 'soc_code']
    missing = []
    for f in required_yes + required_text:
        val = data.get(f, '')
        if val == '' or (f in required_yes and val not in ['Yes', 'No']):
            missing.append(f)
    if missing:
        status = "Cannot Be Determined"
        rationale = f"Cannot be determined from given data due to missing entities: {', '.join(missing)}."
    else:
        all_yes = all(data[f] == 'Yes' for f in required_yes)
        if all_yes:
            status = "Eligible"
            rationale = f"Eligibility determined as Eligible because job_offer_confirmed = {data['job_offer_confirmed']}, employer_is_licensed_sponsor = {data['employer_is_licensed_sponsor']}, certificate_of_sponsorship_issued = {data['certificate_of_sponsorship_issued']}, job_is_eligible_occupation = {data['job_is_eligible_occupation']}, meets_minimum_salary_threshold = {data['meets_minimum_salary_threshold']}, english_requirement_met = {data['english_requirement_met']}, criminal_record_certificate_required = {data['criminal_record_certificate_required']}, criminal_record_certificate_provided = {data['criminal_record_certificate_provided']}, and required fields are provided."
        else:
            status = "Not Eligible"
            no_fields = [f for f in required_yes if data[f] == 'No']
            rationale = f"Eligibility determined as Not Eligible because {' = No, '.join(no_fields)} = No."
    return status, rationale, missing

def assess_health_care():
    data = st.session_state['eligibility']
    required_yes = ['job_offer_confirmed', 'employer_is_licensed_healthcare_sponsor', 'certificate_of_sponsorship_issued', 'job_is_eligible_healthcare_role', 'meets_healthcare_salary_rules', 'professional_registration_required', 'professional_registration_provided', 'english_requirement_met']
    required_text = ['cos_reference_number', 'job_title', 'soc_code', 'professional_registration_number']
    missing = []
    for f in required_yes + required_text:
        val = data.get(f, '')
        if val == '' or (f in required_yes and val not in ['Yes', 'No']):
            missing.append(f)
    if missing:
        status = "Cannot Be Determined"
        rationale = f"Cannot be determined from given data due to missing entities: {', '.join(missing)}."
    else:
        all_yes = all(data[f] == 'Yes' for f in required_yes)
        if all_yes:
            status = "Eligible"
            rationale = f"Eligibility determined as Eligible because job_offer_confirmed = {data['job_offer_confirmed']}, employer_is_licensed_healthcare_sponsor = {data['employer_is_licensed_healthcare_sponsor']}, certificate_of_sponsorship_issued = {data['certificate_of_sponsorship_issued']}, job_is_eligible_healthcare_role = {data['job_is_eligible_healthcare_role']}, meets_healthcare_salary_rules = {data['meets_healthcare_salary_rules']}, professional_registration_required = {data['professional_registration_required']}, professional_registration_provided = {data['professional_registration_provided']}, english_requirement_met = {data['english_requirement_met']}, and required fields are provided."
        else:
            status = "Not Eligible"
            no_fields = [f for f in required_yes if data[f] == 'No']
            rationale = f"Eligibility determined as Not Eligible because {' = No, '.join(no_fields)} = No."
    return status, rationale, missing

def assess_visitor():
    data = st.session_state['eligibility']
    required_yes = ['purpose_is_permitted_under_visitor_rules', 'stay_within_6_months_limit', 'accommodation_arranged', 'return_or_onward_travel_planned', 'intends_to_leave_uk_after_visit', 'sufficient_funds_for_stay']
    required_text = ['purpose_of_visit']
    missing = []
    for f in required_yes + required_text:
        val = data.get(f, '')
        if val == '' or (f in required_yes and val not in ['Yes', 'No']):
            missing.append(f)
    if missing:
        status = "Cannot Be Determined"
        rationale = f"Cannot be determined from given data due to missing entities: {', '.join(missing)}."
    else:
        all_yes = all(data[f] == 'Yes' for f in required_yes)
        if all_yes:
            status = "Eligible"
            rationale = f"Eligibility determined as Eligible because purpose_is_permitted_under_visitor_rules = {data['purpose_is_permitted_under_visitor_rules']}, stay_within_6_months_limit = {data['stay_within_6_months_limit']}, accommodation_arranged = {data['accommodation_arranged']}, return_or_onward_travel_planned = {data['return_or_onward_travel_planned']}, intends_to_leave_uk_after_visit = {data['intends_to_leave_uk_after_visit']}, sufficient_funds_for_stay = {data['sufficient_funds_for_stay']}, and required fields are provided."
        else:
            status = "Not Eligible"
            no_fields = [f for f in required_yes if data[f] == 'No']
            rationale = f"Eligibility determined as Not Eligible because {' = No, '.join(no_fields)} = No."
    return status, rationale, missing

def generate_report_text():
    """Generate formatted text report for download"""
    report = "="*80 + "\n"
    report += "UK VISA ELIGIBILITY ASSESSMENT REPORT\n"
    report += "Generated: " + str(date.today()) + "\n"
    report += "="*80 + "\n\n"
    
    # Personal Details Section
    report += "APPLICANT IDENTITY & PROFILE\n"
    report += "-"*80 + "\n"
    common_fields = [
        ("Full Name (as per passport)", 'full_name'),
        ("Date of Birth", 'dob'),
        ("Nationality", 'nationality'),
        ("Passport Number", 'passport_num'),
        ("Passport Issue Date", 'p_issue'),
        ("Passport Expiry Date", 'p_expiry'),
        ("Country of Application / Current Location", 'location'),
        ("Visa Type Applying For", 'visa_type'),
        ("Purpose of Visit", 'purpose'),
        ("Intended Travel / Start Date", 'start_date'),
        ("Intended Length of Stay", 'stay_len'),
        ("Funds Available", 'funds'),
        ("English Language Requirement Met", 'english'),
        ("Criminal History Declaration", 'criminal'),
        ("Previous UK Visa Refusal", 'refusal'),
        ("Email Address", 'email'),
        ("Phone Number", 'phone'),
        ("Current Address", 'address')
    ]
    
    for display, key in common_fields:
        value = st.session_state['common'].get(key, 'Not Provided')
        if value == '' or (key == 'funds' and value == 0):
            value = 'Not Provided'
        report += f"{display}: {value}\n"
    
    # Eligibility Details
    results = st.session_state.get('assessment_results', {})
    if results:
        report += "\n" + "="*80 + "\n"
        report += f"{results['visa_type']} - ELIGIBILITY VERIFICATION\n"
        report += "="*80 + "\n"
        
        for field, value in results.get('fields', []):
            report += f"{field}: {value}\n"
        
        report += "\n" + "-"*80 + "\n"
        report += "DETERMINATION\n"
        report += "-"*80 + "\n"
        report += f"Eligibility Status: {results['status']}\n"
        report += f"Rationale: {results['rationale']}\n"
        
        # Summary
        report += "\n" + "="*80 + "\n"
        report += "CONSOLIDATED ASSESSMENT SUMMARY\n"
        report += "="*80 + "\n"
        report += f"Eligible Visa Categories: {results['eligible']}\n"
        report += f"Ineligible Visa Categories: {results['ineligible']}\n"
        report += f"Visa Categories with Insufficient Data: {results['insufficient']}\n"
        report += f"Missing or Incomplete Entities: {results['missing_entities']}\n"
        report += f"Data-Driven Next Steps: {results['next_steps']}\n"
    
    report += "\n" + "="*80 + "\n"
    report += "END OF REPORT\n"
    report += "="*80 + "\n"
    
    return report

def apply_gov_uk_theme():
    flag_url = "https://upload.wikimedia.org/wikipedia/commons/a/a5/Flag_of_the_United_Kingdom_%281-2%29.svg"
    
    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), url("{flag_url}") !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
    }}

    [data-testid="stMain"] {{ background: transparent !important; }}

    [data-testid="stSidebar"] {{
        background-color: #0b0c0c !important;
        border-right: 5px solid #1d70b8 !important;
    }}
    
    h1, h2, h3, .stMarkdown p {{
        color: #ffffff !important;
        font-family: "GDS Transport", Arial, sans-serif !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }}

    .gds-card {{
        background-color: #ffffff !important; 
        padding: 40px; 
        border: 1px solid #0b0c0c;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
        margin-bottom: 25px;
        border-radius: 0px;
    }}

    .gds-card h1, .gds-card h2, .gds-card h3, .gds-card p, .gds-card label, .gds-card span, .gds-card div {{
        color: #0b0c0c !important;
        text-shadow: none !important;
    }}

    .stButton>button {{
        background-color: #00703c !important; 
        color: white !important;
        border-radius: 0px !important;
        width: 100% !important;
        font-size: 20px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 0 #002d18 !important;
        border: none !important;
        padding: 15px !important;
        text-transform: uppercase;
    }}
    .stButton>button:hover {{ background-color: #005a30 !important; }}

    input, select, textarea {{
        border: 2px solid #0b0c0c !important;
        background-color: #f3f2f1 !important;
    }}
    
    .stChatMessage {{
        background-color: #f3f2f1 !important;
        border: 1px solid #0b0c0c !important;
        border-radius: 0px !important;
    }}
    
    .stDownloadButton>button {{
        background-color: #1d70b8 !important;
        color: white !important;
        border-radius: 0px !important;
        font-weight: bold !important;
    }}
    </style>
    """, unsafe_allow_html=True)

apply_gov_uk_theme()

# ================= 2. NAVIGATION =================
with st.sidebar:
    st.image("https://assets.publishing.service.gov.uk/media/685a6144f05cab1603ade693/govuk-logo-lockup.png", width=220)
    st.markdown("<h2 style='color:white;'>VISA PORTAL</h2>", unsafe_allow_html=True)
    selected = st.radio("PHASE", ["1. Service Overview", "2. Personal Details", "3. Eligibility Check", "4. Policy Expert"])
    st.divider()
    st.info("Policy: Jan 2026")

# Banner
st.markdown("""
<div style="background-color: #0b0c0c; padding: 15px 50px; border-bottom: 8px solid #1d70b8; margin: -75px -100px 30px -100px; display: flex; justify-content: space-between;">
    <img src="https://assets.publishing.service.gov.uk/media/685a6144f05cab1603ade693/govuk-logo-lockup.png" height="40">
    <div style="color:white; font-weight:bold; background:#f47738; padding:5px 10px; height:fit-content;">BETA</div>
</div>
""", unsafe_allow_html=True)

# ================= 3. PAGES =================

if selected == "1. Service Overview":
    st.markdown("<h1>Check your UK visa requirements</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div class="">
        <h3>Official Decision Support System</h3>
        <p>Analyze your eligibility against the <b>2026 Immigration Rules</b>. This engine processes:</p>
        <ul>
            <li>Common Identity Entities</li>
            <li>Appendix Finance Requirements</li>
            <li>Route-Specific Compliance (Student, Worker, Graduate, etc.)</li>
        </ul>
        <p>Complete all sections to generate a verified compliance score.</p>
    </div>
    """, unsafe_allow_html=True)

elif selected == "2. Personal Details":
    st.markdown("<h1>Identity Profile</h1>", unsafe_allow_html=True)
    with st.form("common_entities"):
        st.markdown('<div class="gds-card">', unsafe_allow_html=True)
        st.subheader("Core Information (18 Entities)")
        c1, c2, c3 = st.columns(3)
        
        st.session_state['common']['full_name'] = c1.text_input("Full Name (Passport)")
        st.session_state['common']['dob'] = c1.date_input("Date of Birth")
        st.session_state['common']['nationality'] = c1.text_input("Nationality")
        st.session_state['common']['passport_num'] = c2.text_input("Passport Number")
        st.session_state['common']['p_issue'] = c2.date_input("Issue Date")
        st.session_state['common']['p_expiry'] = c2.date_input("Expiry Date")
        st.session_state['common']['email'] = c3.text_input("Email Address")
        st.session_state['common']['phone'] = c3.text_input("Phone Number")
        st.session_state['common']['location'] = c3.text_input("Country of Application")
        
        st.divider()
        b1, b2, b3 = st.columns(3)
        st.session_state['common']['visa_type'] = b1.selectbox("Visa Type", ["Student Visa", "Skilled Worker Visa", "Graduate Visa", "Health & Care Visa", "Visitor Visa"])
        st.session_state['common']['purpose'] = b1.text_input("Purpose of Visit")
        st.session_state['common']['start_date'] = b1.date_input("Intended Start Date")
        st.session_state['common']['stay_len'] = b2.text_input("Intended Length of Stay")
        st.session_state['common']['funds'] = b2.number_input("Funds Available (£)", min_value=0)
        st.session_state['common']['english'] = b2.selectbox("English Met?", ["Yes", "No"])
        st.session_state['common']['criminal'] = b3.radio("Criminal History?", ["No", "Yes"], horizontal=True)
        st.session_state['common']['refusal'] = b3.radio("Previous Refusal?", ["No", "Yes"], horizontal=True)
        st.session_state['common']['address'] = b3.text_area("Current Address")
        
        if st.form_submit_button("AUTHENTICATE PROFILE"):
            st.success("Identity profile verified and locked.")
        st.markdown('</div>', unsafe_allow_html=True)

elif selected == "3. Eligibility Check":
    v_type = st.session_state['common'].get('visa_type')
    if not v_type:
        st.error("Please complete Personal Details first.")
    else:
        st.markdown(f"<h1>Assessment: {v_type}</h1>", unsafe_allow_html=True)
        with st.form("elig_form"):
            st.markdown('<div class="">', unsafe_allow_html=True)
            
            if v_type == "Graduate Visa":
                c1, c2, c3 = st.columns(3)
                st.session_state['eligibility']['currently_in_uk'] = c1.selectbox("Currently in UK?", ["Yes", "No"])
                st.session_state['eligibility']['current_uk_visa_type'] = c1.selectbox("Current Visa Type", ["Student", "Tier 4"])
                st.session_state['eligibility']['course_completed'] = c1.selectbox("Course Completed?", ["Yes", "No"])
                st.session_state['eligibility']['course_level_completed'] = c2.text_input("Course Level Completed")
                st.session_state['eligibility']['education_provider_is_licensed'] = c2.selectbox("Licensed Provider?", ["Yes", "No"])
                st.session_state['eligibility']['original_cas_reference'] = c2.text_input("Original CAS Reference")
                st.session_state['eligibility']['provider_reported_completion_to_home_office'] = c3.selectbox("Provider Reported Completion to Home Office?", ["Yes", "No"])
                st.session_state['eligibility']['student_visa_valid_on_application_date'] = c3.selectbox("Student Visa Valid on Application Date?", ["Yes", "No"])
            
            elif v_type == "Student Visa":
                c1, c2, c3 = st.columns(3)
                st.session_state['eligibility']['has_cas'] = c1.selectbox("Has CAS?", ["Yes", "No"])
                st.session_state['eligibility']['cas_reference_number'] = c1.text_input("CAS Reference Number")
                st.session_state['eligibility']['education_provider_is_licensed'] = c1.selectbox("Education Provider Licensed?", ["Yes", "No"])
                st.session_state['eligibility']['course_level'] = c2.text_input("Course Level")
                st.session_state['eligibility']['course_full_time'] = c2.selectbox("Course Full-Time?", ["Yes", "No"])
                st.session_state['eligibility']['course_start_date'] = c2.date_input("Course Start Date")
                st.session_state['eligibility']['course_end_date'] = c3.date_input("Course End Date")
                st.session_state['eligibility']['course_duration_months'] = c3.number_input("Duration (Months)")
                st.session_state['eligibility']['meets_financial_requirement'] = c3.selectbox("Meets Financial Requirement?", ["Yes", "No"])
                st.session_state['eligibility']['funds_held_for_28_days'] = c3.selectbox("Funds held for 28 days?", ["Yes", "No"])
                st.session_state['eligibility']['english_requirement_met'] = c3.selectbox("English Requirement Met?", ["Yes", "No"])

            elif v_type == "Skilled Worker Visa":
                c1, c2, c3 = st.columns(3)
                st.session_state['eligibility']['job_offer_confirmed'] = c1.selectbox("Job Offer Confirmed?", ["Yes", "No"])
                st.session_state['eligibility']['employer_is_licensed_sponsor'] = c1.selectbox("Employer is Licensed Sponsor?", ["Yes", "No"])
                st.session_state['eligibility']['certificate_of_sponsorship_issued'] = c1.selectbox("Certificate of Sponsorship Issued?", ["Yes", "No"])
                st.session_state['eligibility']['cos_reference_number'] = c2.text_input("CoS Reference Number")
                st.session_state['eligibility']['job_title'] = c2.text_input("Job Title")
                st.session_state['eligibility']['soc_code'] = c2.text_input("SOC Code")
                st.session_state['eligibility']['job_is_eligible_occupation'] = c3.selectbox("Eligible Occupation?", ["Yes", "No"])
                st.session_state['eligibility']['salary_offered'] = c3.number_input("Salary Offered (£)")
                st.session_state['eligibility']['meets_minimum_salary_threshold'] = c3.selectbox("Meets Minimum Salary Threshold?", ["Yes", "No"])
                st.session_state['eligibility']['english_requirement_met'] = c3.selectbox("English Requirement Met?", ["Yes", "No"])
                st.session_state['eligibility']['criminal_record_certificate_required'] = c3.selectbox("Criminal Record Certificate Required?", ["Yes", "No"])
                st.session_state['eligibility']['criminal_record_certificate_provided'] = c3.selectbox("Criminal Record Certificate Provided?", ["Yes", "No"])

            elif v_type == "Health & Care Visa":
                c1, c2, c3 = st.columns(3)
                st.session_state['eligibility']['job_offer_confirmed'] = c1.selectbox("Job Offer Confirmed?", ["Yes", "No"])
                st.session_state['eligibility']['employer_is_licensed_healthcare_sponsor'] = c1.selectbox("Employer is Licensed Healthcare Sponsor?", ["Yes", "No"])
                st.session_state['eligibility']['certificate_of_sponsorship_issued'] = c1.selectbox("Certificate of Sponsorship Issued?", ["Yes", "No"])
                st.session_state['eligibility']['cos_reference_number'] = c2.text_input("CoS Reference Number")
                st.session_state['eligibility']['job_title'] = c2.text_input("Job Title")
                st.session_state['eligibility']['soc_code'] = c2.text_input("SOC Code")
                st.session_state['eligibility']['job_is_eligible_healthcare_role'] = c3.selectbox("Eligible Healthcare Role?", ["Yes", "No"])
                st.session_state['eligibility']['salary_offered'] = c3.number_input("Salary Offered (£)")
                st.session_state['eligibility']['meets_healthcare_salary_rules'] = c3.selectbox("Meets Healthcare Salary Rules?", ["Yes", "No"])
                st.session_state['eligibility']['professional_registration_required'] = c3.selectbox("Professional Registration Required?", ["Yes", "No"])
                st.session_state['eligibility']['professional_registration_provided'] = c3.selectbox("Professional Registration Provided?", ["Yes", "No"])
                st.session_state['eligibility']['professional_registration_number'] = c3.text_input("Professional Registration Number")
                st.session_state['eligibility']['english_requirement_met'] = c3.selectbox("English Requirement Met?", ["Yes", "No"])

            elif v_type == "Visitor Visa":
                c1, c2 = st.columns(2)
                st.session_state['eligibility']['purpose_of_visit'] = c1.text_input("Purpose of Visit")
                st.session_state['eligibility']['purpose_is_permitted_under_visitor_rules'] = c1.selectbox("Purpose Permitted Under Visitor Rules?", ["Yes", "No"])
                st.session_state['eligibility']['intended_length_of_stay_months'] = c1.number_input("Intended Length of Stay (Months)")
                st.session_state['eligibility']['stay_within_6_months_limit'] = c1.selectbox("Stay Within 6 Months Limit?", ["Yes", "No"])
                st.session_state['eligibility']['accommodation_arranged'] = c2.selectbox("Accommodation Arranged?", ["Yes", "No"])
                st.session_state['eligibility']['return_or_onward_travel_planned'] = c2.selectbox("Return or Onward Travel Planned?", ["Yes", "No"])
                st.session_state['eligibility']['intends_to_leave_uk_after_visit'] = c2.selectbox("Intend to Leave UK After Visit?", ["Yes", "No"])
                st.session_state['eligibility']['sufficient_funds_for_stay'] = c2.selectbox("Sufficient Funds for Stay?", ["Yes", "No"])

            submitted = st.form_submit_button("RUN COMPLIANCE ANALYSIS")
            st.markdown('</div>', unsafe_allow_html=True)

        if submitted:
            # Display the assessment
            st.markdown("## Applicant Identity & Profile")
            common_fields = [
                ("Full Name (as per passport)", 'full_name'),
                ("Date of Birth", 'dob'),
                ("Nationality", 'nationality'),
                ("Passport Number", 'passport_num'),
                ("Passport Issue Date", 'p_issue'),
                ("Passport Expiry Date", 'p_expiry'),
                ("Country of Application / Current Location", 'location'),
                ("Visa Type Applying For", 'visa_type'),
                ("Purpose of Visit", 'purpose'),
                ("Intended Travel / Start Date", 'start_date'),
                ("Intended Length of Stay", 'stay_len'),
                ("Funds Available", 'funds'),
                ("English Language Requirement Met (Yes / No)", 'english'),
                ("Criminal History Declaration (Yes / No)", 'criminal'),
                ("Previous UK Visa Refusal (Yes / No)", 'refusal'),
                ("Email Address", 'email'),
                ("Phone Number", 'phone'),
                ("Current Address", 'address')
            ]
            table_data = []
            for display, key in common_fields:
                value = st.session_state['common'].get(key, 'Not Provided')
                if value == '' or (key == 'funds' and value == 0):
                    value = 'Not Provided'
                table_data.append([display, str(value)])
            st.table(table_data)

            # Visa section
            visa_fields_data = []
            if v_type == "Graduate Visa":
                st.markdown("## Graduate Visa – Eligibility Verification")
                grad_fields = [
                    ("currently_in_uk", "Currently in UK"),
                    ("current_uk_visa_type", "Current UK Visa Type"),
                    ("course_completed", "Course Completed"),
                    ("course_level_completed", "Course Level Completed"),
                    ("education_provider_is_licensed", "Education Provider is Licensed"),
                    ("provider_reported_completion_to_home_office", "Provider Reported Completion to Home Office"),
                    ("original_cas_reference", "Original CAS Reference"),
                    ("student_visa_valid_on_application_date", "Student Visa Valid on Application Date")
                ]
                grad_table = []
                for key, display in grad_fields:
                    value = st.session_state['eligibility'].get(key, 'Not Provided')
                    if value == '':
                        value = 'Not Provided'
                    grad_table.append([display, str(value)])
                    visa_fields_data.append((display, str(value)))
                st.table(grad_table)
                status, rationale, missing = assess_graduate()

            elif v_type == "Student Visa":
                st.markdown("## Student Visa – Eligibility Verification")
                student_fields = [
                    ("has_cas", "Has CAS"),
                    ("cas_reference_number", "CAS Reference Number"),
                    ("education_provider_is_licensed", "Education Provider is Licensed"),
                    ("course_level", "Course Level"),
                    ("course_full_time", "Course Full-Time"),
                    ("course_start_date", "Course Start Date"),
                    ("course_end_date", "Course End Date"),
                    ("course_duration_months", "Course Duration Months"),
                    ("meets_financial_requirement", "Meets Financial Requirement"),
                    ("funds_held_for_28_days", "Funds Held for 28 Days"),
                    ("english_requirement_met", "English Requirement Met")
                ]
                student_table = []
                for key, display in student_fields:
                    value = st.session_state['eligibility'].get(key, 'Not Provided')
                    if value == '':
                        value = 'Not Provided'
                    student_table.append([display, str(value)])
                    visa_fields_data.append((display, str(value)))
                st.table(student_table)
                status, rationale, missing = assess_student()

            elif v_type == "Skilled Worker Visa":
                st.markdown("## Skilled Worker Visa – Eligibility Verification")
                skilled_fields = [
                    ("job_offer_confirmed", "Job Offer Confirmed"),
                    ("employer_is_licensed_sponsor", "Employer is Licensed Sponsor"),
                    ("certificate_of_sponsorship_issued", "Certificate of Sponsorship Issued"),
                    ("cos_reference_number", "CoS Reference Number"),
                    ("job_title", "Job Title"),
                    ("soc_code", "SOC Code"),
                    ("job_is_eligible_occupation", "Job is Eligible Occupation"),
                    ("salary_offered", "Salary Offered"),
                    ("meets_minimum_salary_threshold", "Meets Minimum Salary Threshold"),
                    ("english_requirement_met", "English Requirement Met"),
                    ("criminal_record_certificate_required", "Criminal Record Certificate Required"),
                    ("criminal_record_certificate_provided", "Criminal Record Certificate Provided")
                ]
                skilled_table = []
                for key, display in skilled_fields:
                    value = st.session_state['eligibility'].get(key, 'Not Provided')
                    if value == '':
                        value = 'Not Provided'
                    skilled_table.append([display, str(value)])
                    visa_fields_data.append((display, str(value)))
                st.table(skilled_table)
                status, rationale, missing = assess_skilled_worker()

            elif v_type == "Health & Care Visa":
                st.markdown("## Health & Care Visa – Eligibility Verification")
                health_fields = [
                    ("job_offer_confirmed", "Job Offer Confirmed"),
                    ("employer_is_licensed_healthcare_sponsor", "Employer is Licensed Healthcare Sponsor"),
                    ("certificate_of_sponsorship_issued", "Certificate of Sponsorship Issued"),
                    ("cos_reference_number", "CoS Reference Number"),
                    ("job_title", "Job Title"),
                    ("soc_code", "SOC Code"),
                    ("job_is_eligible_healthcare_role", "Job is Eligible Healthcare Role"),
                    ("salary_offered", "Salary Offered"),
                    ("meets_healthcare_salary_rules", "Meets Healthcare Salary Rules"),
                    ("professional_registration_required", "Professional Registration Required"),
                    ("professional_registration_provided", "Professional Registration Provided"),
                    ("professional_registration_number", "Professional Registration Number"),
                    ("english_requirement_met", "English Requirement Met")
                ]
                health_table = []
                for key, display in health_fields:
                    value = st.session_state['eligibility'].get(key, 'Not Provided')
                    if value == '':
                        value = 'Not Provided'
                    health_table.append([display, str(value)])
                    visa_fields_data.append((display, str(value)))
                st.table(health_table)
                status, rationale, missing = assess_health_care()

            elif v_type == "Visitor Visa":
                st.markdown("## Visitor Visa – Eligibility Verification")
                visitor_fields = [
                    ("purpose_of_visit", "Purpose of Visit"),
                    ("purpose_is_permitted_under_visitor_rules", "Purpose is Permitted Under Visitor Rules"),
                    ("intended_length_of_stay_months", "Intended Length of Stay Months"),
                    ("stay_within_6_months_limit", "Stay Within 6 Months Limit"),
                    ("accommodation_arranged", "Accommodation Arranged"),
                    ("return_or_onward_travel_planned", "Return or Onward Travel Planned"),
                    ("intends_to_leave_uk_after_visit", "Intends to Leave UK After Visit"),
                    ("sufficient_funds_for_stay", "Sufficient Funds for Stay")
                ]
                visitor_table = []
                for key, display in visitor_fields:
                    value = st.session_state['eligibility'].get(key, 'Not Provided')
                    if value == '':
                        value = 'Not Provided'
                    visitor_table.append([display, str(value)])
                    visa_fields_data.append((display, str(value)))
                st.table(visitor_table)
                status, rationale, missing = assess_visitor()

            st.markdown(f"**{v_type} Determination**")
            st.markdown(f"* Eligibility Status: {status}")
            st.markdown(f"* Determination Rationale: {rationale}")
            
            # AI-Generated Official Assessment
            # st.markdown("---")
            # st.markdown('<div class="gds-card">', unsafe_allow_html=True)
            # st.markdown("###  OFFICIAL ASSESSMENT ANALYSIS")
            # st.markdown("**UK Home Office Immigration Rules - January 2026**")
            
            try:
                # Prepare context for AI explanation
                reasons = []
                if status == "Not Eligible":
                    # Extract reasons from rationale
                    if "because" in rationale.lower():
                        reason_text = rationale.split("because")[1].strip()
                        reasons = [reason_text]
                elif status == "Cannot Be Determined":
                    reasons = [f"Missing required information: {', '.join(missing)}"]
                
                # Build context from all collected data
                context_parts = []
                context_parts.append(f"Visa Type: {v_type}")
                context_parts.append(f"Applicant Name: {st.session_state['common'].get('full_name', 'Not Provided')}")
                context_parts.append(f"Nationality: {st.session_state['common'].get('nationality', 'Not Provided')}")
                context_parts.append(f"Date of Birth: {st.session_state['common'].get('dob', 'Not Provided')}")
                context_parts.append(f"Passport Number: {st.session_state['common'].get('passport_num', 'Not Provided')}")
                
                # Add visa-specific fields
                for field, value in visa_fields_data:
                    context_parts.append(f"{field}: {value}")
                
                context = "\n".join(context_parts)
                
                # Create official government-style prompt for Ollama
                prompt = f"""You are an official UK Home Office Immigration Assessment System. Generate an OFFICIAL government assessment report using ONLY the provided context.

ASSESSMENT DECISION: {status}
LEGAL BASIS: UK Immigration Rules (January 2026)
NON-COMPLIANCE FACTORS: {', '.join(reasons) if reasons else 'NONE - All requirements satisfied' if status == 'Eligible' else 'Insufficient documentation provided'}

APPLICATION CONTEXT:
{context}

Generate an OFFICIAL HOME OFFICE ASSESSMENT in the following format:

**ASSESSMENT REFERENCE**: HO-ASSESS-{v_type.replace(' ', '-').upper()}-2026-{hash(st.session_state['common'].get('passport_num', '000'))%10000:04d}

**EXECUTIVE SUMMARY**
[2-3 sentences stating the decision and primary legal basis]

**DETAILED FINDINGS**
[Structured analysis of each requirement against Immigration Rules]

**REGULATORY COMPLIANCE STATUS**
 Requirements Met: [List specific criteria satisfied]
 Requirements Not Met: [List specific deficiencies, if any]
 Insufficient Evidence: [List missing documentation, if any]

**STATUTORY GUIDANCE**
[Official next steps based on UK Immigration Rules]

**LEGAL NOTICE**
This assessment is generated based on information provided and current Immigration Rules. Final decisions are made by UK Visas and Immigration (UKVI) caseworkers.

Use formal, authoritative government language. Be precise and reference specific Immigration Rule requirements where applicable."""

                ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
                ollama_model = os.getenv("OLLAMA_MODEL", "llama2")
                
                with st.spinner(" Generating Official Home Office Assessment..."):
                    response = requests.post(
                        ollama_url,
                        json={
                            "model": ollama_model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.1,
                                "num_predict": 800
                            }
                        },
                        timeout=90
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        explanation = result.get("response", "").strip()
                        if explanation:
                            st.markdown(explanation)
                            
                            # Add official warning box
                            st.markdown("---")
                            st.warning("""
                            ** IMPORTANT LEGAL NOTICE**
                            
                            This automated assessment is provided for guidance purposes only. It does not constitute an official decision by UK Visas and Immigration (UKVI). 
                            
                            All visa applications are subject to review by qualified UKVI caseworkers who will make the final determination based on:
                            - Complete application documentation
                            - Immigration Rules in force at the time of decision
                            - Individual circumstances and supporting evidence
                            
                            For official guidance, visit: **www.gov.uk/browse/visas-immigration**
                            """)
                        else:
                            st.error(" Assessment generation failed. Please ensure Ollama service is operational.")
                    else:
                        st.error(f" Home Office Assessment System Error: API Status {response.status_code}")
                        
            except requests.exceptions.ConnectionError:
                st.error("""
                **SYSTEM ERROR: Cannot Connect to Assessment Engine**
                
                The automated assessment service is currently unavailable. Please ensure:
                1. Ollama service is running: `ollama serve`
                2. Required model is installed: `ollama pull llama2`
                
                For manual assessment, please contact UK Visas and Immigration directly.
                """)
            except Exception as e:
                st.error(f" **CRITICAL ERROR**: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)

            # Summary
            st.markdown("## Consolidated Assessment Summary (Executive View)")
            if status == "Eligible":
                eligible = [v_type]
                ineligible = []
                insufficient = []
            elif status == "Not Eligible":
                eligible = []
                ineligible = [v_type]
                insufficient = []
            else:
                eligible = []
                ineligible = []
                insufficient = [v_type]
            missing_entities = missing + [f for f in st.session_state['common'] if st.session_state['common'].get(f, '') == '']
            st.markdown(f"* Eligible Visa Categories: {', '.join(eligible) if eligible else 'None'}")
            st.markdown(f"* Ineligible Visa Categories: {', '.join(ineligible) if ineligible else 'None'}")
            st.markdown(f"* Visa Categories with Insufficient Data: {', '.join(insufficient) if insufficient else 'None'}")
            st.markdown(f"* Missing or Incomplete Entities: {', '.join(missing_entities) if missing_entities else 'None'}")
            if status == "Eligible":
                next_steps = "Proceed with visa application submission."
            elif status == "Not Eligible":
                next_steps = "Review eligibility criteria and provide missing or corrected information."
            else:
                next_steps = "Provide complete eligibility data for assessment."
            st.markdown(f"* Data-Driven Next Steps: {next_steps}")
            
            # Store results for download
            st.session_state['assessment_complete'] = True
            st.session_state['assessment_results'] = {
                'visa_type': v_type,
                'status': status,
                'rationale': rationale,
                'fields': visa_fields_data,
                'eligible': ', '.join(eligible) if eligible else 'None',
                'ineligible': ', '.join(ineligible) if ineligible else 'None',
                'insufficient': ', '.join(insufficient) if insufficient else 'None',
                'missing_entities': ', '.join(missing_entities) if missing_entities else 'None',
                'next_steps': next_steps
            }
            
            # Download button
            st.markdown("---")
            report_text = generate_report_text()
            st.download_button(
                label=" DOWNLOAD ELIGIBILITY REPORT",
                data=report_text,
                file_name=f"UK_Visa_Eligibility_Report_{date.today()}.txt",
                mime="text/plain"
            )

elif selected == "4. Policy Expert":
    st.markdown("<h1>UK Immigration Policy Expert</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="gds-card">
        <h3>AI-Powered Immigration Assistance with Document Retrieval</h3>
        <p>Ask questions about UK visa policies, requirements, and your specific eligibility scenario.</p>
        <p><strong>Powered by:</strong> RAG (Retrieval-Augmented Generation) using official UK visa policy documents</p>
    </div>
    """, unsafe_allow_html=True)
    
    # PDF Upload Section
    with st.expander(" Manage Policy Documents", expanded=False):
        st.subheader("Upload UK Visa Policy PDFs")
        uploaded_files = st.file_uploader(
            "Upload PDF documents (Immigration Rules, Policy Guidance, etc.)",
            type=['pdf'],
            accept_multiple_files=True
        )
        
        if st.button(" Process & Index Documents") and uploaded_files:
            if not PINECONE_API_KEY:
                st.error(" PINECONE_API_KEY not found in environment variables")
            elif pinecone_index is None:
                st.error(" Pinecone index not initialized")
            elif embeddings is None:
                st.error(" Embeddings model not loaded")
            else:
                try:
                    from langchain_community.document_loaders import PyMuPDFLoader
                    from langchain_text_splitters import RecursiveCharacterTextSplitter
                    import tempfile
                    
                    with st.spinner("Processing PDF documents..."):
                        all_chunks = []
                        splitter = RecursiveCharacterTextSplitter(
                            chunk_size=800,
                            chunk_overlap=150
                        )
                        
                        for uploaded_file in uploaded_files:
                            # Save to temp file
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                                tmp_file.write(uploaded_file.read())
                                tmp_path = tmp_file.name
                            
                            # Load and split
                            loader = PyMuPDFLoader(tmp_path)
                            docs = loader.load()
                            chunks = splitter.split_documents(docs)
                            all_chunks.extend(chunks)
                            
                            # Clean up
                            os.unlink(tmp_path)
                        
                        # Create vectors
                        vectors = [
                            (str(uuid4()), 
                             embeddings.embed_query(doc.page_content), 
                             {"text": doc.page_content, "source": uploaded_file.name})
                            for doc in all_chunks
                        ]
                        
                        # Upload to Pinecone
                        pinecone_index.upsert(vectors=vectors)
                        
                    st.success(f" Successfully indexed {len(vectors)} chunks from {len(uploaded_files)} documents")
                    
                except Exception as e:
                    st.error(f"Error processing documents: {str(e)}")
    
    st.divider()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about UK visa policies..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response using RAG with Ollama
        with st.chat_message("assistant"):
            # Prepare context from user's data if available
            user_context = ""
            if st.session_state.get('common'):
                visa_type = st.session_state['common'].get('visa_type', '')
                if visa_type:
                    user_context = f"User is applying for: {visa_type}. "
            
            if st.session_state.get('assessment_results'):
                results = st.session_state['assessment_results']
                user_context += f"Assessment Status: {results['status']}. "
            
            # Retrieve relevant context from Pinecone
            retrieved_context = ""
            if pinecone_index and embeddings:
                try:
                    with st.spinner("Searching policy documents..."):
                        query_vector = embeddings.embed_query(prompt)
                        search_results = pinecone_index.query(
                            vector=query_vector,
                            top_k=5,
                            include_metadata=True
                        )
                        
                        if search_results["matches"]:
                            retrieved_context = "\n\n".join([
                                f"[Document Excerpt {i+1}]:\n{match['metadata']['text']}"
                                for i, match in enumerate(search_results["matches"])
                            ])
                            st.info(f"Retrieved {len(search_results['matches'])} relevant document excerpts")
                except Exception as e:
                    st.warning(f" Could not retrieve documents: {str(e)}")
            
            # Call Ollama API with RAG context
            try:
                ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
                ollama_model = os.getenv("OLLAMA_MODEL", "llama2")
                
                system_message = f"""You are a UK Immigration Policy Expert assistant. 
You help users understand UK visa requirements and eligibility criteria based on January 2026 policies.

{user_context}

Use the following official policy document excerpts to answer questions accurately:

{retrieved_context if retrieved_context else "No specific documents retrieved. Use your general knowledge of UK immigration policy."}

Provide accurate, helpful information about UK immigration rules, visa types, and requirements.
Be professional and official in tone, similar to GOV.UK guidance.
Always cite which document excerpt you're referencing when applicable."""
                
                # Prepare full conversation context
                full_prompt = system_message + "\n\nConversation History:\n"
                for msg in st.session_state.messages[-5:]:  # Last 5 messages for context
                    role = "Human" if msg["role"] == "user" else "Assistant"
                    full_prompt += f"{role}: {msg['content']}\n"
                full_prompt += "\nAssistant: "
                
                # Make request to Ollama
                with st.spinner(" Generating response..."):
                    response = requests.post(
                        ollama_url,
                        json={
                            "model": ollama_model,
                            "prompt": full_prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.3,
                                "num_predict": 1024
                            }
                        },
                        timeout=90
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    assistant_response = result.get("response", "").strip()
                    
                    if not assistant_response:
                        assistant_response = "I apologize, but I couldn't generate a response. Please try again."
                else:
                    assistant_response = f"Error connecting to Ollama API. Status code: {response.status_code}. Please ensure Ollama is running locally."
                
                st.markdown(assistant_response)
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                
            except requests.exceptions.ConnectionError:
                error_msg = """I apologize, but I cannot connect to the Ollama service. 

**To use the chatbot:**
1. Install Ollama from https://ollama.ai
2. Run `ollama pull llama2` (or your preferred model)
3. Ensure Ollama is running on http://localhost:11434

**Meanwhile, here's general UK visa guidance:**

**Common UK Visa Types:**
- **Student Visa**: For full-time study at licensed institutions
- **Skilled Worker Visa**: For skilled employment with a licensed sponsor
- **Graduate Visa**: For recent graduates from UK institutions
- **Health & Care Visa**: For healthcare professionals
- **Visitor Visa**: For tourism and short visits (up to 6 months)

**General Requirements:**
- Valid passport
- Proof of financial means
- English language proficiency (for most visa types)
- No serious criminal history
- Specific documents based on visa type (CAS, CoS, etc.)

What specific aspect would you like to know more about?"""
                st.markdown(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
            except Exception as e:
                error_msg = f"An error occurred: {str(e)}\n\nPlease ensure Ollama is properly installed and running."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})