rmdir /s /q "./build"
rmdir /s /q "./dist"
PyInstaller eddienput/gui.py --noconsole --icon=eddienput/icon.ico --name Eddienput
copy ViGEmBusSetup_x64.msi dist\Eddienput\ViGEmBusSetup_x64.msi
copy eddienput\ViGEmClient.dll dist\Eddienput\ViGEmClient.dll
copy vcontroller\x64\Release\vcontroller.dll dist\Eddienput\vcontroller.dll
copy eddienput\icon.ico dist\Eddienput\icon.ico
copy eddienput\config.json dist\Eddienput\config.json
copy eddienput\eddienput_controller.png dist\Eddienput\eddienput_controller.png
Xcopy /E /I eddienput\configs dist\Eddienput\configs
Xcopy /E /I eddienput\playbacks dist\Eddienput\playbacks
Xcopy /E /I eddienput\rec_configs dist\Eddienput\rec_configs
Xcopy /E /I eddienput\sounds dist\Eddienput\sounds
copy LICENSE dist\Eddienput\LICENSE
copy README.md dist\Eddienput\README.md
del "./Eddienput.spec"
PAUSE
