rmdir /s /q "./build"
rmdir /s /q "./dist"
py -3.7 -m PyInstaller src/gui.py --noconsole --icon=src/icon.ico --name Eddienput
copy ViGEmBusSetup_x64.msi dist\Eddienput\ViGEmBusSetup_x64.msi
copy src\ViGEmClient.dll dist\Eddienput\ViGEmClient.dll
copy vcontroller\x64\Release\vcontroller.dll dist\Eddienput\vcontroller.dll
copy src\icon.ico dist\Eddienput\icon.ico
copy src\config.json dist\Eddienput\config.json
copy src\eddienput_controller.png dist\Eddienput\eddienput_controller.png
Xcopy /E /I configs dist\Eddienput\configs
Xcopy /E /I recordings dist\Eddienput\recordings
Xcopy /E /I src\sounds dist\Eddienput\sounds
copy LICENSE dist\Eddienput\LICENSE
copy README.md dist\Eddienput\README.md
del "./Eddienput.spec"
PAUSE
