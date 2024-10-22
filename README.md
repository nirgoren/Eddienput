# Eddienput
![Github All Releases](https://img.shields.io/github/downloads/nirgoren/Eddienput/total.svg)

Eddienput (pronounced "edd-input") is a programmable virtual controller mainly aimed at enhancing training mode for all fighting games on PC.

## Prerequisites:  

Install ViGEmBusSetup_x64.msi (provided with the program)

## Build Instructions:

* *Note*: This part is mainly for developers, users can just grab the latest release from the releases page.
1. Clone the repo to some local folder
1. Install [Python 3.12](https://www.python.org/downloads/release/python-3120/)
1. Install [Poetry](https://python-poetry.org/docs/#installation)
1. `cd` into the cloned repo's root directory
1. Run `poetry shell`
1. Run `./build.bat`

The distributable directory containing the Eddienput executable should be found under `<repo_root>/dist/Eddienput`

## Usage:

The most common usage scenario would be to define playbacks/mixups in a playbacks file, load the file and play it. You can do so by following these steps:
1. Start Eddienput.exe with your own controller already connected (a second virtual controller should be connected as the program starts)
2. Define playbacks/mixups in a playbacks file (txt format) according to the syntax described below, save it and load the playbacks file into the program (drag and drop)
3. Now go into training mode in your game and select "controller" as the dummy action. If asked by the game to press start on P2 controller, press the "home" key on your keyboard to simulate pressing start on the virtual controller (required in some games)
4. You can now press F3 on your keyboard or a mapped button on your controller to play the playback by simulating button presses on P2 controller

You can also share your playbacks files with other players in your community in order to share combos, mixups and more. You can find some example playbacks files in the playbacks folder.

### Hotkeys:

* Player 1 Side                          - F1
* Player 2 Side                          - F2
* Play Sequence                          - F3 / Custom
* Stop Sequence                          - F4
* Reload Script                          - F5
* Decrease Number of Repetitions         - F6
* Increase Number of Repetitions         - F7
* Toggle Sequence Start/End Sound        - F8
* Map Play Button                        - F9
* Press Start on P2 Controller           - Home Key
* Press Select on P2 Controller          - End Key
* Toggle Manual P2 Control (for Mapping) - Insert Key

Hoykeys can be suppressed by toggling `Suppress Hotkeys` in the GUI window.

### Notation:  

* *#* - Start a comment line
* W*number* - Wait a certain number of frames (*number* being a positive integer)
* *X* - Tap *X* and release the next frame
* [*X*] - Hold *X*
* ]*X*[ - Release *X*
* Note - For directions, if you want to switch directly from held direction to another held direction,
do not release the held direction in between.
For example, if you want to go from down to forward, just do
`[2] W10 [6]`
instead of
`[2] W10 ]2[+[6]`
* **The above does not hold if the directions are mapped to keyboard keys (experimental)
* *+* - Add input to the same frame
#### Example:
```
configs\gg.json
# <- Indicates this line is a comment and is ignored by the parser
# The assumed game for this example is Guilty Gear XRD Rev2
# The first line (config\gg.json) indicates that we use the symbols and mappings defined in that file (that fit Guilty Gear notation)
# In the next line, we tell the dummy to perform a Gunflame (Asumming Sol Badguy is selected as P2), and then wait 60 frames (one second)
2 3 6+P W60
# Now dash forward (tap forward, wait one frame, then hold forward) for 20 frames and then stop (release forward)
6 W1 [6] W20 ]6[
# Now enter IK mode
K+P+S+H
```

### Mixups:

* Mixups consist of several user defined options, one of which is chosen at random based on the weights of the options
* A line consisting of the *startmix* keyword indicates the beginning of a mixup definition
* Options are defined with a line consisting of the *option* keyword optionally followed by a weight (non-negative integer)
* An option's default weight is 1
* Actions in the lines following the option will be performed if the option is chosen
* Close the mixup definition with a line consisting of the *endmix* keyword
* Nested mixups are not supported
#### Example:
```
configs\gg.json
# Classic Eddie high/low mixup (assuming Guilty Gear Accent Core +R)
# Fixed Mawaru setup (always performed)
2 3 6 H W4 [K] W11 ]K[ W20
# Start defining a mixup (Indentation is optional but recommended for readability)
startmix
  # Now one of the following options will be performed:
  # 1) dash 6K option (overhead) - 60% to be performed:
  option 60
    6 W1 [6] W10 K
  # 2) dash 5K option (low) - 40% to be performed:
  option 40
    6 W1 [6] W10 ]6[ W9 K
endmix
# Can now add more actions to be performed after the initial mixup ended (including other mixups)
```

### Looping:

* Actions can be repeated several times by defining a loop
* A line consisting of the *startloop* keyword followed by the number of repetitions (a positive integer) indicates the beginning of a loop definition
* Actions in the lines following the loop definition will be repeated by the number of repetitions defined
* Close the loop definition with a line consisting of the *endloop* keyword
* Mixups defined inside a loop must be closed before exiting the loop
* Loops can be defined inside mixups as long as the mixup doesn't end inside the loop
* Nested loops are not supported
#### Example:
```
configs\sf.json
# The assumed game for this example is Street Fighter 5 with Ken as P2
# Perform heavy tatsu 5 times waiting 180 frames (3 seconds) between each:
# Indentation is optional (recommended for readability)
loop 5
  2 1 4+HK W180
endloop
# End with an ex shoryuken
6 2 3+MP+HP
```

## Config files:  

You can define symbols, reassign symbols to other buttons, and set up macros in a JSON config file (see configs\gg.json for an example).  
The first line of a playback file should always be the path (absolute or relative) to the config file to be used.

#### Reserved symbols:  

* W*number*
* *+*
* startmix
* option
* endmix
* [
* ]
* loop
* endloop

#### Supported virtual controller buttons to map a symbol to:  
<details>
  <summary>Click to expand</summary>

  * "BtnA"
  * "BtnB"
  * "BtnX"
  * "BtnY"
  * "BtnShoulderR"
  * "BtnShoulderL"
  * "BtnBack"
  * "BtnStart"
  * "TriggerR"
  * "TriggerL"
  * { "Dpad": "down" }
  * { "Dpad": "left" }
  * { "Dpad": "right" }
  * { "Dpad": "up" }
  * { "Dpad": "down_left" }
  * { "Dpad": "down_right" }
  * { "Dpad": "up_left" }
  * { "Dpad": "up_right" }
</details>


#### Supported virtual keyboard buttons to map a symbol to (experimental):
<details>
  <summary>Click to expand</summary>

  * 'shift'
  * '0'             
  * '1'             
  * '2'             
  * '3'             
  * '4'             
  * '5'             
  * '6'             
  * '7'             
  * '8'             
  * '9'             
  * 'a'             
  * 'b'             
  * 'c'             
  * 'd'             
  * 'e'             
  * 'f'             
  * 'g'             
  * 'h'             
  * 'i'             
  * 'j'             
  * 'k'             
  * 'l'             
  * 'm'             
  * 'n'             
  * 'o'             
  * 'p'             
  * 'q'             
  * 'r'             
  * 's'             
  * 't'             
  * 'u'             
  * 'v'             
  * 'w'             
  * 'x'             
  * 'y'             
  * 'z'             
  * 'numpad_enter'
  * 'numpad_1'      
  * 'numpad_2'      
  * 'numpad_3'      
  * 'numpad_4'      
  * 'numpad_5'      
  * 'numpad_6'      
  * 'numpad_7'      
  * 'numpad_8'      
  * 'numpad_9'      
  * 'numpad_0'      
  * '-'             
  * '+'             
  * 'left'          
  * 'up'            
  * 'right'         
  * 'down'          
  * 'space'         
  * 'enter'         
</details>

## Recording:
The program can listen to controller inputs and generate Eddienput playbacks files. A controller has to be connected as the program starts to enable this feature.

Recording is initiated by pressing F10 on the keyboard. Once stopped by pressing the select button on the controller, the recorded inputs will be written into a playbacks file. The loaded recording configuration json file determines the symbols each button will be translated to, which should match the symbols defined in the configuration file for the generated playbacks file. If the loaded recording configuration file does not define a mapping between a button and a symbol, that button is ignored. See `rec_configs/rec.json` or `rec_configs/rec_bb.json` for examples.
## Others:

### Playing sounds
* "beep" - Plays a beep sound
#### Example:
```
configs\gg.json
# Assuming Guilty Gear Accent Core +R with Eddie as P2, Perform Eddie's reversal super and beep right when a slashback should be inputted
6 3 2 1 4 6+H W63 beep
```

To associate a symbol with some audio cue, in the config file add a mapping from
the symbol to its respective `.wav` file (see `configs\gg.json` for an example).

### General config file

In addition to the plyaback specific config file, Eddienput also loads some settings from a general config file in its directory `config.json` when it starts up. The settings that can be configured are:

* `playback`: A path to a playbacks file to load as the program starts.
* `playback_start_end_sound`: Either set to `true` or `false`, sets whether to play a sound when a playback starts/ends playing.
* `hot_reload`: Either set to `true` to `false`, sets whether the playbacks file is to be
reloaded automatically upon play.
* `side`: Set to either `P1` or `P2`, sets which player side to use as the program starts up.
* `record_to`: Set the default location to record to.
* `rec_config`: A path to the default configuration to be used for recording.

## Known Issues:
#### KOF2002 UM:

* Inputs are inconsistent when symbols are mapped to a virtual controller. They are more consistent when mapped to keys on the keyboard (use `configs\kof_keyboard.json`)

#### Guilty Gear Accent Core +R:

* P2 movement keys not recognized when mapped to keys on the keyboard (use `gg.json`). If you are a keyboard player, run two instances of the program at the same time (or connect some a real controller if you have one) so that the second virtual controller will be treated as P2's

#### Touhou 7.5: Suimusou - Immaterial and Missing Power

* Mapping to the keyboard arrow keys does not work. Assign the game's movement keys for P2 to some other keys (see configs\iamp_keyboard.json)

#### Mapping play button to a controller button

* Only supported on XInput controllers. If you use a PS4 pad, a possible workaround would be to use DS4Windows

#### Inconsistent inputs:

* It is recommended to disable Steam's Xbox controller support, as that introduces input inconsistencies (This most likely applies to XInput controllers in general)
