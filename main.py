import streamlit as st
import requests
import json
from io import BytesIO
import openai
from google.cloud import vision
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.environ.get("OPEN_AI_API_KEY")
# Load service account key from Streamlit secrets
service_account_info = json.loads(st.secrets["google"]["service_account_key"])
client = vision.ImageAnnotatorClient.from_service_account_info(service_account_info)


def detect_text(content):
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if response.error.message:
        raise Exception(f"{response.error.message}")
    return texts


# Function to call the add user API
def add_user(name, contact, address, category, recording, screenshot):
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
                st.write(response["text"])
            except Exception as e:
                st.error(f"An error occurred: {e}")
        recording_content += response["text"]
    if screenshot:
        # Read the file
        content = screenshot.read()

        # Display the uploaded image
        st.image(content, caption="Uploaded Image", use_column_width=True)

        # Perform text detection
        st.write("Detecting text...")
        texts = detect_text(content)
        # Display detected text
        if texts:
            st.write("Detected text:")
            st.write(texts[0].description)
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
    url = "http://raw-eloise-bharatavjo-64825601.koyeb.app/user"  # Update with your actual API endpoint URL

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
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            print("User added successfully!")
            print("Response JSON:", response.json())
        else:
            print(f"Failed to add user. Status code: {response.status_code}")
            print("Response JSON:", response.json())

    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
    response = {"user_id": "12345"}  # Placeholder response
    return response["user_id"]


# Function to trigger Retell API call
def trigger_retell_call(user_id, name, contact, address):
    # TODO: Implement the actual Retell API call
    # This is a placeholder function
    pass


# Function to submit complaint
def submit_complaint(
    user_id, name, contact, address, situation, caller_number, awb_number, amount
):
    # TODO: Implement the actual complaint submission
    # This is a placeholder function
    pass


st.title("Avjo-ScamSOS")

# User Details Form
with st.form("user_details"):
    name = st.text_input("Name")
    contact = st.text_input("Contact Number")
    address = st.text_input("Address")
    category = st.selectbox("Category", ["OPA", "OPB", "OPC", "Others"])

    recording = st.file_uploader(
        "Upload Recording (optional)", type=["mp3", "wav"], accept_multiple_files=False
    )
    screenshot = st.file_uploader(
        "Upload Screenshot (optional)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=False,
    )

    submit_button = st.form_submit_button("Submit")

if submit_button:
    if name and contact and address and category:
        user_id = add_user(name, contact, address, category, recording, screenshot)
        st.success(f"User registered successfully. User ID: {user_id}")
        st.session_state["user_id"] = user_id
        st.session_state["name"] = name
        st.session_state["contact"] = contact
        st.session_state["address"] = address
    else:
        st.error(
            "Please fill all required fields: Name, Contact Number, Address, and Category."
        )

# Options after user registration
if "user_id" in st.session_state:
    option = st.radio(
        "Choose an option:", ("File complaint offline", "Talk to an Agent")
    )

    if option == "Talk to an Agent":
        if st.button("Start Call"):
            trigger_retell_call(
                st.session_state["user_id"],
                st.session_state["name"],
                st.session_state["contact"],
                st.session_state["address"],
            )
            st.info("Call initiated. Please wait for an agent to connect.")

    elif option == "File complaint offline":
        with st.form("complaint_form"):
            st.write("Complaint Form")
            name = st.text_input("Name", value=st.session_state["name"])
            contact = st.text_input("Contact", value=st.session_state["contact"])
            address = st.text_input("Address", value=st.session_state["address"])
            situation = st.text_area("Situation")
            caller_number = st.text_input("Caller Number")
            awb_number = st.text_input("AWB Number")
            amount = st.number_input("Amount of Money", min_value=0.0)

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
                st.success("Complaint submitted successfully.")
            else:
                st.error(
                    "Please fill all required fields: Name, Contact, Address, and Situation."
                )

# TODO: Implement dashboard to show call report after the call ends
