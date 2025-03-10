# Installation

## Python
Clone repository and install requirements. from requirements .txt

## On Windows
The builds section has the latest binaries supplied to simply run from an
Executable file.

# How to use
The heart and center of this application is the configuration file.
The file will be loaded into memory on startup, so if you actively work on it make sure to restart the application.
1. Activate OBS Websocket in Tools/WebSocket Server Settings.
2. Inside Mix it Up, enable Developer API in the Services section.  
3. Configure the ```config.json``` to define what events from OBS are sent to MIU.

# Config.json Examples
## Getting event information
By default the shipped ```config.json```, has ```debug_mode``` set to true. This will print every
single OBS event into the console window, including all the data it contains. I recommend simply
running with empty mapping in the beginning and just click around in OBS, change settings, switch scenes,
Hide elements etc, see what you can get from your streaming software and think what you might use it for
in Mix it Up.

Variable names are valueable here as you can send them to MIU easily with the right mapping.
Also you will use them as conditions later.

## Understanding the config mapping
We are going through specific exmaples and introduce features step by step.

### Simple Example
We always start with the event name, and inside the Dictionary we have the
conditions, which action to trigger and what data to send.

Fe. if you want to route all GameProgramScenes changed events to MIU,
this would be inside the ```OBS_MIU_MAPPINGS``` dictionary:
```json
    "CurrentProgramSceneChanged" : {
		"miu_action_group" : "SceneChanged"
    }
```
Every time this event fires, it will now trigger the miu action named "SceneChanged".
If you look at that event you can see it also has the Scene that we change to as a variable 
called ```sceneNamed```, if we want to pass that along as arguments for the Action our mapping
would look like this:
```json
    "CurrentProgramSceneChanged" : {
        "argument": "$sceneName",
        "miu_action_group" : "SceneChanged"
    }
```
Note that i adopted the $ symbol from MIU to identify which parts of the argument to replace with a
variables value. You are not limited to variables here, you can also simply write normal text in there.
```json
        "argument": "Secne we changed to: $sceneName"
```

Note that variable names are case sensitive.

### Conditions
Some events are very spammy, or you might only want the event under specific conditions, in that case
you want to define the conditions under which the event is relayed to MIU.
```json
    "CurrentProgramSceneChanged" : {
        "conditions": {
          "sceneName": ["AFK", "IRL"]
        },
        "name": "PlayMusic",
        "arguments": ["$sceneName", "activated"]
    }
```
This example would only activate if we change scenes named "AFK" or "IRL".
Note that name and miu_action_group are identical, and arguments and argument
are as well. I would recommend using "arguments" and "miu_action_group" to
make the mapping clearer.
Likewise, writing this:
```json
        "arguments": ["$sceneName", "activated"]
```
Is giving the same result as this:
```json
        "arguments": "$sceneName activated"
```

### Multiple mappings for one event type
To define multiple target actions  under varying conditions the syntax changes
a bit. 

We need to define a ```miu_action_groups``` array of actions within the event dictionary.
Each of them with their own conditions, arguments etc.
```json
	"InputSettingsChanged" : {
      "miu_action_groups": [
        {
          "conditions": {
            "inputName": "AFK",
            "inputSettings": {
              "text": "Only trigger if text is this"
            }
          },
          "arguments": "newText: $inputSettings/text",
          "miu_action_group": "TestBridge2"
        },
        {
          "conditions" : {
              "inputName" : "Game Capture"
          },
          "arguments": "WindowTitle $inputSettings/window",
          "arguments_process": "arguments.split(':', 1)[0]",
          "miu_action_group" : "TestBridge2"
        }
      ]
	}
```
In this example we respond to InputSettingsChanged and send it along to the MIU-Action 
```TestBridge2``` if the inputName is ```"AFK"``` (which for this event is the
name of the source) and if the text field is set to ```"Only trigger if text
is his"```.

Note that the argument i pass along is the text from nested data within the 
event, therefore i have to specify the nesting pathlike as
```$inputSettings/text```.

The second routing is sending the event along if the source named "Game Capture"
is changed in any way. Im also grabbing the window title and pass it along.

There is also custom python code in here to filter the argument string.

### Custom code for arguments
In the previous example we can see this line:
```json
          "arguments_process": "arguments.split(':', 1)[0]",
```
This code will be run on the arguments string after the identifers have been
replaced with the events values. I'm not responsible for your python skills ;).

This specific example will split the arguments string on all ":" and take the
first element only to pass along.
You can use either "arguments" or "argument" here, which will just be the 
resulting string, whatever is returned from your code will be passed along.

Make sure to test this well.