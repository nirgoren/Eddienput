# eddiebot5000
Prerequisites:  
Install ViGEmBusSetup_x64.msi  

Symbols:  
You can define symbols, reassign symbols to other buttons, and set up macros in a JSON config file.  
The first line of a recordings file should be the location of the config file to be used.

Reserved symbols:  
W[*number*], +, startmix, option, endmix, [, ]

Supported buttons to map a symbol to:  
"BtnA"
"BtnB"
"BtnX"
"BtnY"
"BtnShoulderR"
"BtnShoulderL"
"BtnBack" (select)
"BtnStart"
"TriggerR"
"TriggerL"

Notation:  
* W[number] - Wait a certain number of frames
* *X* - Tap *X* and release the next frame
* [*X*] - Hold *X*
* ]*X*[ - Release *X*
* Note - For directions, if you want to switch from held direction to another held direction, 
there's no need to release in between.
(For example, if you want to go from down to forwards, just do [2] W10 [6], instead of [2] W10 ]2[+[6])

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
