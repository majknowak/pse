import os
import json
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import pandas as pd
from dotenv import load_dotenv
from twilio.rest import Client

# =========================
# Environment & constants
# =========================
load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_URL = "https://api.raporty.pse.pl/api/price-fcst"
STATE_FILE = os.path.join(BASE_DIR, "state.json")
LOG_FILE = os.path.join(BASE_DIR, "script_log.txt")

TARGET_PHONES = [
    phone.strip()
    for phone in os.getenv("TARGET_PHONES", "").split(",")
    if phone.strip()
]

# =========================
# Logging
# =========================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)
logging.getLogger("twilio").setLevel(logging.WARNING)

def log_message(message: str):
    logging.info(message)

# =========================
# State handling
# =========================
def load_last_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_last_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# =========================
# SMS
# =========================
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

def send_sms(phone: str, message: str):
    try:
        client = Client(account_sid, auth_token)
        sent_message = client.messages.create(
            body=message,
            from_=twilio_number,
            to=phone
        )
        log_message(f"SMS sent to {phone} (SID: {sent_message.sid})")
    except Exception as e:
        log_message(f"Failed to send SMS to {phone}: {e}")

# =========================
# Data retrieval
# =========================
def fetch_data():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    params = {
        "$select": "business_date,cen_fcst,period",
        "$filter": f"business_date eq '{today}'",
        "$orderby": "period asc"
    }
    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()

    raw = response.json()
    data = raw["value"] if isinstance(raw, dict) and "value" in raw else raw

    return pd.DataFrame(data)

# =========================
# Main logic
# =========================
def main():
    now = datetime.now(ZoneInfo("Europe/Warsaw"))
    active_start = now.replace(hour=8, minute=30, second=0, microsecond=0)
    active_end = now.replace(hour=19, minute=30, second=0, microsecond=0)

    if not (active_start <= now < active_end):
        return

    try:
        df = fetch_data()
    except Exception as e:
        log_message(f"Failed to retrieve data: {e}")
        return

    if df.empty:
        log_message("Empty dataframe returned from API.")
        return

    if "cen_fcst" not in df.columns:
        log_message(f"Unexpected columns: {list(df.columns)}. Expected 'cen_fcst'.")
        return

    if len(df) < 2:
        log_message("Not enough data to evaluate.")
        return

    df["cen"] = df["cen_fcst"].astype(float)
    df["date"] = df["business_date"] + " " + df["period"]
    last_two_records = df.tail(2)[["date", "cen"]]

    log_message(
        f"Last two records:\n{last_two_records.to_string(index=False)}"
    )

    first_cen = last_two_records.iloc[0]["cen"]
    second_cen = last_two_records.iloc[1]["cen"]
    current_event_id = last_two_records.iloc[-1].to_json()

    last_state = load_last_state()
    last_event_id = last_state.get("last_event_id")

    significant_change = (
        (first_cen > 0 and second_cen < 0) or
        (first_cen < 0 and second_cen > 0)
    )

    if significant_change and last_event_id != current_event_id:
        if first_cen > 0 and second_cen < 0:
            message = f"Cena stała się ujemna.\n{last_two_records.to_string(index=False)}"
        else:
            message = f"Cena stała się dodatnia.\n{last_two_records.to_string(index=False)}"

        log_message(message)

        for phone in TARGET_PHONES:
            send_sms(phone, message)

        save_last_state({"last_event_id": current_event_id})
    else:
        log_message("No significant change in price values.")

# =========================
# Entry point
# =========================
if __name__ == "__main__":
    while True:
        main()
        time.sleep(120)
