rmdir /s /q "./build"
rmdir /s /q "./dist"
del "./eddiebot.spec"
pyinstaller src/eddiebot.py
copy ScpVBus-x64\vXboxInterface.dll dist\eddiebot\vXboxInterface.dll
copy src\recordings.txt dist\eddiebot\recordings.txt
copy src\readme.txt dist\eddiebot\readme.txt
copy src\config.json dist\eddiebot\config.json
PAUSE
