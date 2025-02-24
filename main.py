from obswebsocket import obsws, events
import requests
import json

# REFER TO https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md#events

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
MIXITUP_HOST = config.get("MIXITUP_HOST", "localhost")
MIXITUP_PORT = config.get("MIXITUP_PORT", 8912)
OBS_MIU_MAPPINGS = config.get("OBS_MIU_MAPPINGS", "")
DEBUG_MODE = config.get("DEBUG_MODE", False)
MIXITUP_COMMANDS = []

def standardize_arguments(arguments):
    if type(arguments) is list:
        return " ".join(arguments)
    return arguments

def replace_identifiers(text, event):
    if len(text) < 1:
        return text

    modified = text
    for key, value in event.items():
        potential = '$' + key
        if potential in modified:
            modified = modified.replace(potential, str(value))

    return modified


def standardize_conditions(conditions):
    result = {}
    for key,value in conditions.items():
        if type(value) is not list:
            result[key] = [ value ]
        else:
            result[key] = value

    return result

def standardize_action(json_action):
    """Adds missing parts to the json, and reformats if necessary"""
    name = ''
    if "miu_action_group" in json_action:
        name = json_action["miu_action_group"]
    if "name" in json_action:
        name = json_action["name"]

    arguments = ''
    if "arguments" in json_action:
        arguments =  json_action["arguments"]
    if "argument" in json_action:
        arguments =  json_action["argument"]


    result = {
            "name" : name,
            "conditions" : standardize_conditions(json_action.get('conditions', {})),
            "arguments" : arguments
        }
    return result

def on_event(event):
    """Callback function to handle OBS events."""
    if DEBUG_MODE: print(event)

    # if there is no mapping we return
    if not event.name in OBS_MIU_MAPPINGS:
        return

    mapping = OBS_MIU_MAPPINGS[event.name]

    actions = []
    if "miu_action_groups" in mapping:
        for action in mapping["miu_action_groups"]:
            actions.append(standardize_action(action))

    if "miu_action_group" in mapping:
        actions.append(standardize_action(mapping))

    for action in actions:
        # if there is no miu action to call we return
        if action["name"] == '':
            return
        arguments = action["arguments"]
        arguments = " ".join(arguments) if type(arguments) is list else arguments
        arguments = replace_identifiers(arguments, event.datain)

        if evaluate_conditions(action["conditions"].items(), event.datain):
            send_to_mixitup(action["name"], arguments)


def evaluate_conditions(conditions, data):
    for name, value in conditions:
        if not name in data:
            return False

        allowed_values = []
        if type(value) is list:
            allowed_values = value
        else:
            allowed_values.append(value)

        if not data[name] in allowed_values:
            return False

    return True



def main():
    # Create a WebSocket connection to OBS
    ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)

    try:
        # Connect to OBS
        ws.connect()
        print("Connected to OBS WebSocket")

        # Register an event handler
        ws.register(on_event)

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
    global DEBUG_MODE, MIXITUP_COMMANDS

    if MIXITUP_COMMANDS and DEBUG_MODE == False:
        return MIXITUP_COMMANDS


    url = f"http://{MIXITUP_HOST}:{MIXITUP_PORT}/api/v2/commands"

    try:
        response = requests.get(url, {"skip": "0", "pageSize" : "9999" })
        if response.status_code == 200:
            MIXITUP_COMMANDS = json.loads(response.text)['Commands']
            return MIXITUP_COMMANDS
        else:
            print(f"Error sending to Mix It Up: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Failed to send to Mix It Up: {e}")


def get_miu_command_id(name):
    for command in get_miu_commands():
        #print(command)
        if command['Name'] == name:
            return command['ID']
    return False

def send_to_mixitup(action, arguments):
    """Send event data to Mix It Up."""
    command_id = get_miu_command_id(action)
    if not command_id:
        return

    url = f"http://{MIXITUP_HOST}:{MIXITUP_PORT}/api/v2/commands/{command_id}"
    event_data = {
        "Arguments": arguments,
        "Platform": "All"
    }

    try:
        response = requests.post(url, json=event_data)
        if response.status_code == 200:
            print(f"Sent to Mix It Up-\"{action}\": {event_data}")
        else:
            print(f"Error sending to Mix It Up: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Failed to send to Mix It Up: {e}")


if __name__ == "__main__":
    main()
