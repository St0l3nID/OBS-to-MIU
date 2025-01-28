from obswebsocket import obsws, events
import requests
import json


# Load configuration from JSON file
def load_config(file_path="config.json"):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {}

config = load_config()

OBS_HOST = config.get("OBS_HOST", "localhost")
OBS_PORT = config.get("OBS_PORT", 4455)
OBS_PASSWORD = config.get("OBS_PASSWORD", "")
OBS_SOURCE = config.get("OBS_SOURCE", "Game Capture")
MIXITUP_HOST = config.get("MIXITUP_HOST", "localhost")
MIXITUP_PORT = config.get("MIXITUP_PORT", 8912)
MIXITUP_COMMAND = config.get("MIXITUP_COMMAND", "Change Category")

def on_event(event):
    """Callback function to handle OBS events."""
    print(event)
    if not event.datain['inputName'] == OBS_SOURCE:
        return

    window = event.datain['inputSettings']['window']
    if not window:
        return

    window_name = window.split(':')[0]
    send_to_mixitup(window_name)

def main():
    # Create a WebSocket connection to OBS
    ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)

    try:
        # Connect to OBS
        ws.connect()
        print("Connected to OBS WebSocket")

        # Register an event handler
        ws.register(on_event, events.InputSettingsChanged)

        # Keep the script running to listen for events
        input("Press Enter to exit...\n")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Disconnect from OBS
        ws.disconnect()
        print("Disconnected from OBS WebSocket")

def get_miu_commands():
    """Send event data to Mix It Up."""
    url = f"http://{MIXITUP_HOST}:{MIXITUP_PORT}/api/v2/commands"

    try:
        response = requests.get(url, {"pageSize" : "9999" })
        if response.status_code == 200:
            return response
        else:
            print(f"Error sending to Mix It Up: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Failed to send to Mix It Up: {e}")


def send_to_mixitup(arguments):
    """Send event data to Mix It Up."""
    command_id = False
    for command in json.loads(get_miu_commands().text)['Commands']:
        #print(command)
        if command['Name'] == MIXITUP_COMMAND:
            command_id = command['ID']

    if not command_id:
        return

    url = f"http://{MIXITUP_HOST}:{MIXITUP_PORT}/api/v2/commands/{command_id}"
    event_data = {
        "Arguments": arguments,
        "Platform": "Twitch"
    }

    try:
        response = requests.post(url, json=event_data)
        if response.status_code == 200:
            print(f"Sent to Mix It Up: {event_data}")
        else:
            print(f"Error sending to Mix It Up: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Failed to send to Mix It Up: {e}")


if __name__ == "__main__":
    main()
