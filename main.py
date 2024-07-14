import streamlit as st
import requests
import json
from io import BytesIO
from dotenv import load_dotenv
import os
from retell import Retell
from fpdf import FPDF
import textwrap

load_dotenv()

retell_client = Retell(
    # Find the key in dashboard
    api_key=os.environ.get("RETELL_API_KEY"),
)

# Function to call the add user API
def add_user(name, contact, address, category, recording, screenshot):
    # TODO: Implement the actual API call
    # This is a placeholder function
    summary = ""
    if recording:
        # TODO: Analyze recording and generate summary
        summary += "Recording summary: ..."
    if screenshot:
        # TODO: Analyze screenshot and generate summary
        summary += "Screenshot summary: ..."
    
    # TODO: Make the actual API call to add user
    response = {"user_id": "12345"}  # Placeholder response
    return response["user_id"]

# Function to trigger Retell API call
def trigger_retell_call(user_id, name, contact, address):
    '''Trigger Retell Agent to call on user's contact number'''
    retell_llm_dynamic_variables = {"user id":user_id,"user name":name,"contact number":contact,"address":address}
    call = retell_client.call.create_phone_call(
            from_number="+14152302677",
            to_number=contact,
            retell_llm_dynamic_variables= retell_llm_dynamic_variables
        )
    return call.call_id

def generate_and_download_report(user_name, contact, address, call_summary):
    st.subheader("Avjo-ScamSOS Report")
    
    # Display report in Streamlit
    st.write(f"**User Name:** {user_name}")
    st.write(f"**Contact:** {contact}")
    st.write(f"**Address:** {address}")
    st.write("**Call Summary:**")
    st.text_area("", call_summary, height=150, disabled=True)
    
    # Generate PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Set font
    pdf.set_font("Arial", size=12)
    
    # Add content to PDF
    pdf.cell(200, 10, txt="Avjo-ScamSOS Report", ln=1, align='C')
    pdf.cell(200, 10, txt="", ln=1)  # Empty line
    pdf.cell(200, 10, txt=f"User Name: {user_name}", ln=1)
    pdf.cell(200, 10, txt=f"Contact: {contact}", ln=1)
    pdf.cell(200, 10, txt=f"Address: {address}", ln=1)
    pdf.cell(200, 10, txt="Call Summary:", ln=1)
    
    # Write call summary with word wrap
    pdf.set_font("Arial", size=10)
    wrapped_text = textwrap.wrap(call_summary, width=90)
    for line in wrapped_text:
        pdf.cell(0, 10, txt=line, ln=1)
    
    # Save PDF to BytesIO object
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_data = pdf_output.getvalue()
    
    # Create download button
    st.download_button(
        label="Download Report as PDF",
        data=pdf_data,
        file_name="Avjo-ScamSOS_Report.pdf",
        mime="application/pdf"
    )

# Function to submit complaint
def submit_complaint(user_id, name, contact, address, situation, caller_number, awb_number, amount):
    # TODO: Implement the actual complaint submission
    # This is where you would typically save the complaint to a database or send it to an API

    # Generate PDF report
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", size=14)
    
    # Add content to PDF
    pdf.cell(200, 10, txt="Complaint Report", ln=1, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="", ln=1)  # Empty line
    pdf.cell(200, 10, txt=f"User ID: {user_id}", ln=1)
    pdf.cell(200, 10, txt=f"Name: {name}", ln=1)
    pdf.cell(200, 10, txt=f"Contact: {contact}", ln=1)
    pdf.cell(200, 10, txt=f"Address: {address}", ln=1)
    pdf.cell(200, 10, txt=f"Caller Number: {caller_number}", ln=1)
    pdf.cell(200, 10, txt=f"AWB Number: {awb_number}", ln=1)
    pdf.cell(200, 10, txt=f"Amount: {amount}", ln=1)
    pdf.cell(200, 10, txt="Situation:", ln=1)
    
    # Write situation with word wrap and line breaks
    pdf.set_font("Arial", size=10)
    lines = situation.split('\n')
    for line in lines:
        wrapped_lines = textwrap.wrap(line, width=90)
        for wrapped_line in wrapped_lines:
            pdf.cell(0, 10, txt=wrapped_line, ln=1)
        if len(wrapped_lines) == 0:
            pdf.cell(0, 10, txt='', ln=1)  # Empty line for line breaks
    
    # Save PDF to BytesIO object
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_data = pdf_output.getvalue()
    
    # Display success message
    st.success("Complaint submitted successfully!")
    
    # Offer PDF for download
    st.download_button(
        label="Download Complaint Report",
        data=pdf_data,
        file_name="complaint_report.pdf",
        mime="application/pdf"
    )


st.title("Avjo-ScamSOS")

# User Details Form
with st.form("user_details"):
    name = st.text_input("Name")
    contact = st.text_input("Contact Number (with country code)")
    address = st.text_input("Address")
    category = st.selectbox("Category", ["OPA", "OPB", "OPC", "Others"])
    
    recording = st.file_uploader("Upload Recording (optional)", type=['mp3', 'wav'], accept_multiple_files=False)
    screenshot = st.file_uploader("Upload Screenshot (optional)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=False)
    
    submit_button = st.form_submit_button("Submit")

if submit_button:
    if name and contact and address and category:
        user_id = add_user(name, contact, address, category, recording, screenshot)
        st.success(f"User registered successfully. User ID: {user_id}")
        st.session_state['user_id'] = user_id
        st.session_state['name'] = name
        st.session_state['contact'] = contact
        st.session_state['address'] = address
    else:
        st.error("Please fill all required fields: Name, Contact Number, Address, and Category.")

# Options after user registration
if 'user_id' in st.session_state:
    option = st.radio("Choose an option:", ("File complaint offline", "Talk to an Agent"))
    
    if option == "Talk to an Agent":
        if st.button("Start Call"):
            call_id = trigger_retell_call(st.session_state['user_id'], st.session_state['name'], 
                                st.session_state['contact'], st.session_state['address'])
            st.info("Call initiated. Please wait for an agent to connect.")
    
    elif option == "File complaint offline":
        with st.form("complaint_form"):
            st.write("Complaint Form")
            name = st.text_input("Name", value=st.session_state['name'])
            contact = st.text_input("Contact", value=st.session_state['contact'])
            address = st.text_input("Address", value=st.session_state['address'])
            situation = st.text_area("Situation")
            caller_number = st.text_input("Contact of Frauder")
            awb_number = st.text_input("AWB Number")
            amount = st.number_input("Amount of Money Scammed", min_value=0.0)
            
            submit_complaint_button = st.form_submit_button("Submit Complaint")
        
        if submit_complaint_button:
            if name and contact and address and situation:
                submit_complaint(st.session_state['user_id'], name, contact, address, 
                                 situation, caller_number, awb_number, amount)
                st.success("Complaint submitted successfully.")
            else:
                st.error("Please fill all required fields: Name, Contact, Address, and Situation.")

# TODO: Implement dashboard to show call report after the call ends


call_obj = retell_client.call.retrieve(
    call_id
)
st.session_state['call_summary'] = call_obj.call_analysis.call_summary

if st.button("Generate Report"):
    generate_and_download_report(st.session_state['name'], st.session_state['contact'], st.session_state['address'], st.session_state['call_summary'])