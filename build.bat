taskkill /IM source1import.exe /t /f
pyinstaller ^
    -F ^
    -p utils ^
    --distpath=./ ^
    --add-data=utils/shared/import_blacklist.json;utils/shared ^
    --add-data=utils/shared/icon.ico;utils/shared ^
    --icon=utils/shared/icon.ico ^
    --add-binary=utils\shared\bin\vtf2tga;utils\shared\bin\vtf2tga ^
    -w source1import.pyw
