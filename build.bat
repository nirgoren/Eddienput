rmdir /s /q "./build"
rmdir /s /q "./dist"
del "./eddiebot.spec"
pyinstaller src/gui.py --noconsole --name eddiebot
copy ViGEmBusSetup_x64.msi dist\eddiebot\ViGEmBusSetup_x64.msi
copy src\ViGEmClient.dll dist\eddiebot\ViGEmClient.dll
copy C:\dev\eddiebot\vcontroller\x64\Release\vcontroller.dll dist\eddiebot\vcontroller.dll
copy src\beep.wav dist\eddiebot\beep.wav
copy src\boop.wav dist\eddiebot\boop.wav
copy src\boop_low.wav dist\eddiebot\boop_low.wav
copy src\icon.png dist\eddiebot\icon.png
copy src\recordings.txt dist\eddiebot\recordings.txt
copy README.md dist\eddiebot\readme.txt
copy src\gg.json dist\eddiebot\gg.json
copy LICENSE dist\eddiebot\LICENSE
PAUSE
