import os
import json
import logging
import requests
import pandas as pd
from datetime import datetime
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Twilio configuration
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
target_phone_number = os.getenv('TARGET_PHONE_NUMBER')

# Configure logging
log_file_path = os.path.join(os.path.dirname(__file__), "script_log2.txt")  # Updated log file path
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(message)s')

# State tracking file
state_file_path = os.path.join(os.path.dirname(__file__), "state2.json")  # Updated state file

def log_message(message):
    logging.info(message)

def load_last_state():
    """Load the last state from the state file."""
    if os.path.exists(state_file_path):
        with open(state_file_path, 'r') as f:
            return json.load(f)
    else:
        log_message(f"State file {state_file_path} does not exist. Creating a new one.")
        save_last_state({})  # Initialize an empty state
    return {}

def save_last_state(state):
    """Save the current state to the state file."""
    try:
        with open(state_file_path, 'w') as f:
            json.dump(state, f)
        log_message(f"State saved: {state}")
    except Exception as e:
        log_message(f"Failed to save state: {e}")

def send_sms(message):
    """Send an SMS using the Twilio API."""
    try:
        client = Client(account_sid, auth_token)
        sent_message = client.messages.create(
            body=message,
            from_=twilio_number,
            to=target_phone_number
        )
        log_message(f"SMS sent: {message} (SID: {sent_message.sid})")
    except Exception as e:
        log_message(f"Failed to send SMS: {e}")

def fetch_and_process_data():
    """Fetch data from the API, process it, and handle notifications."""
    current_date = datetime.today().strftime('%Y-%m-%d')
    url = "https://api.raporty.pse.pl/api/crb-prog"
    params = {
        "$select": "business_date,cen_prog,udtczas_oreb",
        "$filter": f"business_date eq '{current_date}'"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json().get('value', [])
        if data:
            df = pd.DataFrame(data)
            df = df.rename(columns={
                'business_date': 'date',
                'udtczas_oreb': 'od_do',
                'cen_prog': 'cen'
            })[['date', 'od_do', 'cen']]

            if len(df) >= 2:
                last_two_records = df.tail(2)
                log_message(f"Last two records:\n{last_two_records.to_string(index=False)}")

                first_cen = last_two_records.iloc[0]['cen']
                second_cen = last_two_records.iloc[1]['cen']

                current_event_id = last_two_records.iloc[-1].to_json()

                last_state = load_last_state()

                significant_change = False
                # Check for significant change in cen values
                if first_cen > 0 and second_cen < 0:
                    message = f"Cena ujemna. {last_two_records.to_string(index=False)}"
                    significant_change = True
                elif first_cen < 0 and second_cen > 0:
                    message = f"Cena dodatnia. {last_two_records.to_string(index=False)}"
                    significant_change = True
                else:
                    message = "No significant change in price values."

                log_message(message)

                # Check if this event has already been processed
                if significant_change and last_state.get('last_event_id') != current_event_id:
                    send_sms(message)
                    save_last_state({'last_event_id': current_event_id})

            else:
                log_message("Not enough data available to retrieve the last two records.")
        else:
            log_message("No data available for the current date.")

    except requests.exceptions.RequestException as e:
        log_message(f"Failed to retrieve data: {e}")

# Execute the function
fetch_and_process_data()
