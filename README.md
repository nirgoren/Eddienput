# eddiebot
EddieBot is a programmable virtual controller mainly aimed at enhancing training mode for fighting games. 

Prerequisites:  
Install ViGEmBusSetup_x64.msi  

Usage:
The most common usage would be to define recordings/mixups in a recording file, load the file and play the recording. You can do so by following these steps:
* Define recordings/mixups in a recording file (txt format) according to the syntax described below, save it and load the recording into the program.
* Now go into training mode in your game and select "controller" as the dummy action, then press the "home" key on your keyboard to simulate pressing start on the virtual controller (required in most games). 
* You can now press F3 on your keyboard or a mapped button on your controller to play the recording by simulating button presses on P2 controller.

Symbols:  
You can define symbols, reassign symbols to other buttons, and set up macros in a JSON config file.  
The first line of a recordings file should always be the path (absolute or relative) to the config file to be used.

Reserved symbols:  
W[*number*], +, startmix, option, endmix, [, ], loop, endloop

Supported controller buttons to map a symbol to:  
"BtnA"
"BtnB"
"BtnX"
"BtnY"
"BtnShoulderR"
"BtnShoulderL"
"BtnBack"
"BtnStart"
"TriggerR"
"TriggerL"
{ "Dpad": "down" }
{ "Dpad": "left" }
{ "Dpad": "right" }
{ "Dpad": "up" }
{ "Dpad": "down_left" }
{ "Dpad": "down_right" }
{ "Dpad": "up_left" }
{ "Dpad": "up_right" }


Supported keyboard buttons to map a symbol to:
TODO

Notation:  
* W[number] - Wait a certain number of frames
* *X* - Tap *X* and release the next frame
* [*X*] - Hold *X*
* ]*X*[ - Release *X*
* Note - For directions, if you want to switch from held direction to another held direction, 
there's no need to release in between.
(For example, if you want to go from down to forwards, just do [2] W10 [6], instead of [2] W10 ]2[+[6])
** The above does not hold if the directions are mapped to keyboard keys

Mixups:
* Mixups consist of several user defined options, one of which is chosen at random based on the weight of the options
* A line consisting of the *startmix* keyword indicates the beginning of a mixup definition
* Options are defined with a line consisting of the *option* keyword optionally followed by a weight (non-negative integer)
* An option's default weight is 1
* Actions in the lines following the option will be performed if the option is chosen
* Close the mixup definition with a line consisting of the *endmix* keyword
* Nested mixups are not supported
TODO example

Looping:
* Actions can be repeated several times by defining a loop 
* A line consisting of the *startloop* keyword followed by the number of repetitions (a positive integer) indicates the beginning of a loop definition
* Actions in the lines following the loop definition will be repeated by the number of repetitions defined
* Close the loop definition with a line consisting of the *endloop* keyword
* Mixups defined inside a loop must be closed before exiting the loop
* Loops can be defined inside mixups as long as the mixup doesn't end inside the loop
* Nested loops are not supported
TODO example

Hotkeys:
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
