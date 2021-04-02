rmdir /s /q "./build"
rmdir /s /q "./dist"
del "./eddiebot.spec"
pyinstaller src/gui.py --noconsole --icon=src/icon.ico --name eddiebot
copy ViGEmBusSetup_x64.msi dist\eddiebot\ViGEmBusSetup_x64.msi
copy src\ViGEmClient.dll dist\eddiebot\ViGEmClient.dll
copy C:\dev\eddiebot\vcontroller\x64\Release\vcontroller.dll dist\eddiebot\vcontroller.dll
copy src\beep.wav dist\eddiebot\beep.wav
copy src\boop.wav dist\eddiebot\boop.wav
copy src\boop_low.wav dist\eddiebot\boop_low.wav
copy src\icon.ico dist\eddiebot\icon.ico
Xcopy /E /I src\configs dist\eddiebot\configs
copy src\eddie_mix.txt dist\eddiebot\eddie_mix.txt
copy src\gg.json dist\eddiebot\gg.json
copy LICENSE dist\eddiebot\LICENSE
copy README.md dist\eddiebot\README.md
PAUSE
