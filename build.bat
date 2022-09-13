taskkill /IM source1import.exe /t /f
python -m PyInstaller ^
    -F ^
    -p utils ^
    --distpath=./ ^
    --add-data=utils/shared/import_blacklist.json;utils/shared ^
    --add-data=utils/shared/icon.ico;utils/shared ^
    --icon=utils/shared/icon.ico ^
    --add-binary=utils\shared\bin\vtf2tga;utils\shared\bin\vtf2tga ^
    --hidden-import utils.elements_import ^
    --hidden-import utils.maps_import ^
    --hidden-import utils.materials_import ^
    --hidden-import utils.models_import ^
    --hidden-import utils.particles_import ^
    --hidden-import utils.scenes_import ^
    --hidden-import utils.scripts_import ^
    --hidden-import utils.vtf_to_tga ^
    -w source1import.pyw
