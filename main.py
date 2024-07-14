import streamlit as st
import requests
import json
from io import BytesIO
from dotenv import load_dotenv
import os
from retell import Retell

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
    metadata = {"user id":user_id,"user name":name,"contact number":contact,"address":address}
    call = retell_client.call.create_phone_call(
            from_number="+14152302677",
            to_number=contact,
            metadata= metadata
        )
    return call.call_id

# Function to submit complaint
def submit_complaint(user_id, name, contact, address, situation, caller_number, awb_number, amount):
    # TODO: Implement the actual complaint submission
    # This is a placeholder function
    pass

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
            caller_number = st.text_input("Caller Number")
            awb_number = st.text_input("AWB Number")
            amount = st.number_input("Amount of Money", min_value=0.0)
            
            submit_complaint_button = st.form_submit_button("Submit Complaint")
        
        if submit_complaint_button:
            if name and contact and address and situation:
                submit_complaint(st.session_state['user_id'], name, contact, address, 
                                 situation, caller_number, awb_number, amount)
                st.success("Complaint submitted successfully.")
            else:
                st.error("Please fill all required fields: Name, Contact, Address, and Situation.")

# TODO: Implement dashboard to show call report after the call ends