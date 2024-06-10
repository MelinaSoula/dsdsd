import json
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from twilio.rest import Client
from streamlit_autorefresh import st_autorefresh

# Load credentials from config file
with open("config.json") as config_file:
    config = json.load(config_file)

account_sid = config["twilio_account_sid"]
auth_token = config["twilio_auth_token"]
twilio_phone_number = config["twilio_phone_number"]
firebase_cert_path = config["firebase_cert_path"]
recipient_phone_number = config["recipient_phone_number"]

client = Client(account_sid, auth_token)

if not firebase_admin._apps:
   cred = credentials.Certificate(firebase_cert_path)
   firebase_admin.initialize_app(cred)

# Access Firestore
db = firestore.client()

# Rest of your code...

def update_holiday_mode_status(status):
    doc_ref = db.collection("settings").document("holiday_mode")
    doc_ref.set({"enabled": status}, merge=True)

def get_holiday_mode_status():
    doc_ref = db.collection("settings").document("holiday_mode")
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get("enabled", False)
    return False

st.set_page_config(page_title="Home Security System", layout="wide")
st_autorefresh(interval=30000,  key="dataframerefresh")

# Customizing the app appearance with color scheme
st.markdown(
    """
    <style>
    .stApp {
        background-color: #e5ecf9;
    }
    .stCheckbox span {
        font-size: 16px;
        color: #333333;
    }
    .stCheckbox label {
        color: #333333;
    }
    .stButton.success {
        background-color: #5cb85c;
        color: white;
    }
    .stButton.warning {
        background-color: #d9534f;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏠 Home Security System")
st.markdown("---")
st.header("Holiday Mode")

holiday_mode_status = get_holiday_mode_status()
if st.checkbox("Enable Holiday Mode", value=holiday_mode_status):
    update_holiday_mode_status(True)
    st.success("✅ Holiday Mode Enabled")
else:
    update_holiday_mode_status(False)
    st.warning("❌ Holiday Mode Disabled")

def get_last_document():
    radar_data_ref = db.collection("radar_data")
    query = radar_data_ref.order_by("Counter", direction=firestore.Query.DESCENDING).limit(1)
    result = query.get()
    if result:
        return result[0].to_dict()
    return None

last_document = get_last_document()

st.subheader("Latest Radar Measurements")
if last_document:
    st.write(f"Counter: {last_document.get('Counter')}")
    st.write(f"Presence detect: {last_document.get('Presence detect')}")
    st.write(f"Moving target: {last_document.get('Moving target')}")
    st.write(f"Moving target Distance: {last_document.get('Moving target Distance')}")
    st.write(f"Stationary target: {last_document.get('Stationary target')}")
    st.write(f"Stationary target Distance: {last_document.get('Stationary target Distance')}")
    st.write(f"Timestamp: {last_document.get('timestamp')}")
else:
    st.write("No radar data available.")

holiday_mode_status = get_holiday_mode_status()

if 'alarm_sent' not in st.session_state:
    st.session_state.alarm_sent = False

if holiday_mode_status and last_document and last_document.get("Presence detect") == 1 and not st.session_state.alarm_sent:
    st.warning("🚨 ALARM - Presence detected during Holiday Mode!")
    
    message = client.messages.create(
        from_=twilio_phone_number,
        body='ALARM - Presence detected during Holiday Mode!',
        to=recipient_phone_number
    )

    print(message.sid)
    
    st.session_state.alarm_sent = True

    update_holiday_mode_status(False)
