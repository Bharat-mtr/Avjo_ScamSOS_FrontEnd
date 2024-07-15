import streamlit as st
import requests
import json
from io import BytesIO
from dotenv import load_dotenv
import os
from retell import Retell
import openai
from google.cloud import vision
from fpdf import FPDF
import textwrap
import time

load_dotenv()

retell_client = Retell(
    # Find the key in dashboard
    api_key=os.environ.get("RETELL_API_KEY"),
)
backend_base_url = os.environ.get("BACKEND_BASE_URL")

openai.api_key = os.environ.get("OPEN_AI_API_KEY")
# Load service account key from Streamlit secrets
service_account_info = json.loads(st.secrets["google"]["service_account_key"])
client = vision.ImageAnnotatorClient.from_service_account_info(service_account_info)


def check_call_status(call_id):
    try:
        response = requests.get(f"{backend_base_url}/call_status/{call_id}")
        if response.status_code == 200:
            data = response.json()
            print("Call status:", data.get("status", "Unknown"))
            if (
                data.get("status") == "call_ended"
                or data.get("status") == "call_analyzed"
            ):
                return True
        else:
            print(f"Failed to fetch call status. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching call status: {e}")
    return False


def detect_text(content):
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if response.error.message:
        raise Exception(f"{response.error.message}")
    return texts


# Function to call the add user API
def add_user(name, contact, address, recording, screenshot):
    # TODO: Implement the actual API call
    # This is a placeholder function
    recording_content = ""
    screenshot_content = ""
    if recording:
        # Display file details
        st.write(f"Uploaded file: {recording.name}")
        st.write(f"File type: {recording.type}")
        st.write(f"File size: {recording.size} bytes")

        # Convert the uploaded file to a file-like object that Whisper API can read
        audio_file = BytesIO(recording.getvalue())
        audio_file.name = recording.name  # Give it a name attribute to mimic a file

        # Send the file to Whisper AI for transcription
        with st.spinner("Transcribing..."):
            try:
                response = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    api_key=os.environ.get(
                        "OPEN_AI_API_KEY"
                    ),  # Pass your OpenAI API key here
                )
                st.success("Transcription complete!")
                # st.write(response["text"])
            except Exception as e:
                st.error(f"An error occurred: {e}")
        recording_content += response["text"]
    if screenshot:
        # Read the file
        content = screenshot.read()

        # Display the uploaded image
        st.image(content, caption="Uploaded Image", use_column_width=True)

        # Perform text detection
        st.write("Redaing Image...")
        texts = detect_text(content)
        # Display detected text
        if texts:
            st.write("Reading completed")
            # st.write(texts[0].description)
            screenshot_content += texts[0].description + " "
        else:
            st.write("No text detected.")
    context = None
    if recording or screenshot:
        prompt = f"""Analyze the following information and provide a concise description of the potential fraud situation:
                        1. Transcript (in Hindi or English):
                        {recording_content}

                        2. Messages extracted from images:
                        {screenshot_content}

                        Based on these inputs, generate a brief summary that:
                        1. Identifies the type of fraud being attempted
                        2. Outlines the key elements of the scam
                        3. Highlights any red flags or warning signs
                        4. Suggests potential motives of the fraudster
    Provide this description in a clear, concise manner, focusing on the most relevant details that indicate fraudulent activity."""
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=200,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        context = completion.choices[0].message.content
    # Define the URL of the Flask API endpoint
    # url = "http://raw-eloise-bharatavjo-64825601.koyeb.app/user"  # Update with your actual API endpoint URL
    url = f"{backend_base_url}/user"
    # Define the data to be sent as JSON in the request body
    new_user_data = {
        "username": name,
        "address": address,
        "contact": contact,
        "context": context,
    }

    # Convert the data to JSON format
    try:
        response = requests.post(
            url, json=new_user_data, headers={"Content-Type": "application/json"}
        )
        print(response)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            print("User added successfully!")
            print("Response JSON:", response.json())
        else:
            print(f"Failed to add user. Status code: {response.status_code}")
            print("Response JSON:", response.json())
            return "0000"

    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
    print(response)
    return response.json()["data"]["user_id"]


# Function to trigger Retell API call
def trigger_retell_call(user_id, name, contact, address):
    """Trigger Retell Agent to call on user's contact number"""
    retell_llm_dynamic_variables = {
        "user id": str(user_id),
        "user name": name,
        "contact number": contact,
        "address": address,
    }
    # st.write(contact + type(contact))
    print(retell_llm_dynamic_variables)
    call = retell_client.call.create_phone_call(
        from_number="+14152302677",
        to_number=str(contact),
        retell_llm_dynamic_variables=retell_llm_dynamic_variables,
    )
    return call.call_id


def generate_and_download_report(user_name, contact, address, call_summary):
    print("Inside genrating report function")
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
    pdf.cell(200, 10, txt="Avjo-ScamSOS Report", ln=1, align="C")
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
    pdf_bytes = pdf.output(dest="S").encode("latin-1")

    # Create download button
    st.download_button(
        label="Download Report as PDF",
        data=pdf_bytes,
        file_name="Avjo-ScamSOS_Report.pdf",
        mime="application/pdf",
    )


# Function to submit complaint
def submit_complaint(
    user_id, name, contact, address, situation, caller_number, awb_number, amount
):
    # TODO: Implement the actual complaint submission
    # This is where you would typically save the complaint to a database or send it to an API

    # Generate PDF report
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", size=14)

    # Add content to PDF
    pdf.cell(200, 10, txt="Complaint Report", ln=1, align="C")
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="", ln=1)  # Empty line
    pdf.cell(200, 10, txt=f"Case ID: {user_id}", ln=1)
    pdf.cell(200, 10, txt=f"Name: {name}", ln=1)
    pdf.cell(200, 10, txt=f"Contact Number: {contact}", ln=1)
    pdf.cell(200, 10, txt=f"Current Address: {address}", ln=1)
    pdf.cell(
        200,
        10,
        txt=f"Scammer's Contact Number (if known): {caller_number or 'Not provided'}",
        ln=1,
    )
    pdf.cell(
        200,
        10,
        txt=f"Parcel Tracking Number (if applicable): {awb_number or 'Not applicable'}",
        ln=1,
    )
    pdf.cell(
        200, 10, txt=f"Amount Lost (if any): {amount or 'No amount specified'}", ln=1
    )
    pdf.cell(200, 10, txt="Incident Description:", ln=1)

    # Write situation with word wrap and line breaks
    pdf.set_font("Arial", size=10)
    lines = situation.split("\n")
    for line in lines:
        wrapped_lines = textwrap.wrap(line, width=90)
        for wrapped_line in wrapped_lines:
            pdf.cell(0, 10, txt=wrapped_line, ln=1)
        if len(wrapped_lines) == 0:
            pdf.cell(0, 10, txt="", ln=1)  # Empty line for line breaks

    # Save PDF to BytesIO object
    pdf_bytes = pdf.output(dest="S").encode("latin-1")

    # Display success message
    st.success("Complaint submitted successfully!")

    # Offer PDF for download
    st.download_button(
        label="Download Complaint Report",
        data=pdf_bytes,
        file_name="complaint_report.pdf",
        mime="application/pdf",
    )


# Set page config
st.set_page_config(page_title="Avjo-ScamSOS", page_icon="🆘", layout="wide")

# Custom CSS
st.markdown(
    """
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: auto;
    }
    .stTextInput>div>div>input, .stSelectbox>div>div>select {
        background-color: transparent;
        color: inherit;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        color: #155724;
        border-radius: 0.3rem;
        margin-bottom: 1rem;
    }
    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        color: #721c24;
        border-radius: 0.3rem;
        margin-bottom: 1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


# App title and introduction
st.title("🆘 Avjo-ScamSOS: Your Protection Against Scams")
st.markdown(
    "Welcome to Avjo-ScamSOS, your first line of defense against fraudulent activities. We're here to help you report and combat scams effectively."
)
st.markdown("---")

# User Details Form
st.header("Step 1: Tell Us About Your Situation")
st.markdown("Please provide your information so we can assist you better.")

# User Details Form
with st.form("user_details"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Name")
    with col2:
        contact = st.text_input(
            "Contact Number (with country code)", placeholder="e.g., +919305857798"
        )
    address = st.text_input("Address")
    col3, col4 = st.columns(2)
    with col3:
        recording = st.file_uploader(
            "Upload Any Relevant Audio Recording (optional)",
            type=["mp3", "wav"],
            accept_multiple_files=False,
        )

    with col4:
        screenshot = st.file_uploader(
            "Upload Any Relevant Screenshot (optional)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=False,
        )

    submit_button = st.form_submit_button("Register My Information")

if submit_button:
    if name and contact and address:
        user_id = add_user(name, contact, address, recording, screenshot)
        st.markdown(
            f'<p class="success-message">User registered successfully.</p>',
            unsafe_allow_html=True,
        )
        st.session_state["user_id"] = user_id
        st.session_state["name"] = name
        st.session_state["contact"] = contact
        st.session_state["address"] = address

    else:
        st.markdown(
            '<p class="error-message">Please fill all required fields: Name, Contact Number, Address.</p>',
            unsafe_allow_html=True,
        )

# Options after user registration
if "user_id" in st.session_state:
    st.markdown("---")
    st.header("Step 2: Choose Your Next Action")

    st.markdown("How would you like to proceed?")
    option = st.radio(
        label="Choose an option:",
        options=("File a Detailed Report", "Speak with a Support Agent"),
    )

    if option == "Speak with a Support Agent":
        if "call_started" not in st.session_state:
            st.session_state.call_started = False
        if "call_analyzed" not in st.session_state:
            st.session_state.call_analyzed = False

        if not st.session_state.call_started:
            st.markdown(
                "Our support agents are ready to assist you. Click the button below to initiate a call."
            )

            if st.button("Connect with an Agent 📞"):
                call_id = trigger_retell_call(
                    st.session_state["user_id"],
                    st.session_state["name"],
                    st.session_state["contact"],
                    st.session_state["address"],
                )
                st.session_state["call_id"] = call_id
                st.session_state.call_started = True
                st.info("We're connecting you with an agent. Please stay on the line.")

                st.write("Call Status:")
                # Display spinner while waiting for call to end
                with st.spinner("Your call is in progress..."):
                    status_text = st.empty()
                    time_elapsed = 0
                    while True:
                        if check_call_status(call_id):
                            break
                        time.sleep(5)  # Adjust interval as needed
                        time_elapsed += 5
                        status_text.text(f"Call in progress ({time_elapsed} seconds)")
                st.success("Call ended successfully!")

                time.sleep(2)

    elif option == "File a Detailed Report":
        st.subheader("Incident Report Form")
        st.markdown("Please provide as much detail as possible about the incident.")
        with st.form("complaint_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Your Name", value=st.session_state["name"])
                address = st.text_input(
                    "Your Address", value=st.session_state["address"]
                )
                caller_number = st.text_input("Scammer's Contact Number (if known)")
            with col2:
                contact = st.text_input(
                    "Your Contact", value=st.session_state["contact"]
                )
                awb_number = st.text_input("Tracking Number (if applicable)")
                # Modified amount input
                amount = st.text_input(
                    "Amount lost (if any, include currency)",
                    placeholder="e.g., $1000, ₹50000, £500",
                )
                st.caption(
                    "Leave blank if no money was lost or if you're unsure of the amount."
                )

            situation = st.text_area("Please describe the incident in detail")
            submit_complaint_button = st.form_submit_button("Submit Complaint")

        if submit_complaint_button:
            if name and contact and address and situation:
                submit_complaint(
                    st.session_state["user_id"],
                    name,
                    contact,
                    address,
                    situation,
                    caller_number,
                    awb_number,
                    amount,
                )
                st.markdown(
                    '<p class="success-message">Thank you for submitting your report. We will review it and take appropriate action.</p>',
                    unsafe_allow_html=True,
                )

            else:
                st.markdown(
                    '<p class="error-message">Please ensure all required fields are filled: Name, Contact, Address, and Incident Description.</p>',
                    unsafe_allow_html=True,
                )


# if 'call_id' in st.session_state:
#         analyse_call = st.button("Analyse call")
#         if analyse_call or 'analyse_call' in st.session_state:
#             call_obj = retell_client.call.retrieve(
#                 st.session_state["call_id"]
#             )
#             st.session_state['call_summary'] = call_obj.call_analysis.call_summary
#             st.session_state['analyse_call'] = True
#             print(st.session_state['call_summary'])
#             generate_report_button = st.button("Generate Report")
#             if generate_report_button:
#                 generate_and_download_report(st.session_state['name'], st.session_state['contact'], st.session_state['address'], st.session_state['call_summary'])


if "call_id" in st.session_state:
    print("got call id")
    if st.session_state.call_started and not st.session_state.call_analyzed:
        call_obj = retell_client.call.retrieve(st.session_state["call_id"])
        print(call_obj)
        while call_obj.call_analysis == None:
            time.sleep(1)
        print(call_obj.call_analysis)    
        st.session_state["call_summary"] = call_obj.call_analysis.call_summary
        st.session_state.call_analyzed = True
        st.success("We've analyzed your call to better assist you.")

    if st.session_state.call_analyzed:
        st.subheader("Call Analysis")
        st.write(st.session_state["call_summary"])

        if st.button("Generate Detailed Report"):
            generate_and_download_report(
                st.session_state["name"],
                st.session_state["contact"],
                st.session_state["address"],
                st.session_state["call_summary"],
            )

    # Add a reset button to start over
    if st.button("Start a New Report"):
        for key in ["call_started", "call_analyzed", "call_id", "call_summary"]:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()
