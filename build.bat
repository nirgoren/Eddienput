rmdir /s /q "./build"
rmdir /s /q "./dist"
pyinstaller src/gui.py --noconsole --icon=src/icon.ico --name EddieController
copy ViGEmBusSetup_x64.msi dist\EddieController\ViGEmBusSetup_x64.msi
copy src\ViGEmClient.dll dist\EddieController\ViGEmClient.dll
copy vcontroller\x64\Release\vcontroller.dll dist\EddieController\vcontroller.dll
copy src\beep.wav dist\EddieController\beep.wav
copy src\boop.wav dist\EddieController\boop.wav
copy src\boop_low.wav dist\EddieController\boop_low.wav
copy src\icon.ico dist\EddieController\icon.ico
Xcopy /E /I configs dist\EddieController\configs
Xcopy /E /I recordings dist\EddieController\recordings
copy LICENSE dist\EddieController\LICENSE
copy README.md dist\EddieController\README.md
del "./EddieController.spec"
PAUSE
