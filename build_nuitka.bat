taskkill /IM source1import.exe /t /f
python -m nuitka ^
	--standalone ^
	--onefile ^
	--windows-console-mode=disable ^
	--enable-plugin=tk-inter ^
	--include-package=utils ^
	--include-data-files=utils/shared/empty.vmap.txt=utils/shared/empty.vmap.txt ^
	--include-data-files=utils/shared/import_blacklist.json=utils/shared/import_blacklist.json ^
	--include-data-files=utils/shared/icon.ico=utils/shared/icon.ico ^
	--include-data-dir=utils\shared\bin\vtf2tga=utils\shared\bin\vtf2tga ^
	--include-module=utils.elements_import ^
	--include-module=utils.maps_import ^
	--include-module=utils.materials_import ^
	--include-module=utils.models_import ^
	--include-module=utils.particles_import ^
	--include-module=utils.scenes_import ^
	--include-module=utils.scripts_import ^
	--include-module=utils.vtf_to_tga ^
	--output-dir=./ ^
	source1import.pyw
