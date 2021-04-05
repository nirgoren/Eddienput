rmdir /s /q "./build"
rmdir /s /q "./dist"
pyinstaller src/gui.py --noconsole --icon=src/icon.ico --name Eddienput
copy ViGEmBusSetup_x64.msi dist\Eddienput\ViGEmBusSetup_x64.msi
copy src\ViGEmClient.dll dist\Eddienput\ViGEmClient.dll
copy vcontroller\x64\Release\vcontroller.dll dist\Eddienput\vcontroller.dll
copy src\beep.wav dist\Eddienput\beep.wav
copy src\boop.wav dist\Eddienput\boop.wav
copy src\boop_low.wav dist\Eddienput\boop_low.wav
copy src\icon.ico dist\Eddienput\icon.ico
copy src\eddienput_controller.png dist\Eddienput\eddienput_controller.png
Xcopy /E /I configs dist\Eddienput\configs
Xcopy /E /I recordings dist\Eddienput\recordings
copy LICENSE dist\Eddienput\LICENSE
copy README.md dist\Eddienput\README.md
del "./Eddienput.spec"
PAUSE
