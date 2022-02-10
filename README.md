# source1import
Set of scripts for importing Source 1 assets such as materials, models, and particle effects into Source 2. Inspired by Valve's own internal utility (written in C++ and Perl), this one is in Python.

## Usage
#### Note:
* Make sure to extract assets from VPK archives.
* Make sure to import texture content first (`.vtf` files), via VTFEdit :: Tools -> Convert folder.  
    Materials and particles won't convert correctly if `.tga` files aren't present inside `/content/<modname>/materials/` 

Download app from [Releases](https://github.com/kristiker/source1import/releases).  
The app can be slow to open up, but has no prerequisites. If that's not ideal, run the advanced way.
## Advanced:
### GUI:
* Double-click on `source1import.pyw`.

Building GUI:
```bash
pip install pyinstaller
./build.bat
```
### CLI:
```bash
cd utils
python scripts_import.py   -i "C:/.../Team Fortress 2/tf" -e "D:/Games/steamapps/common/sbox/addons/tf_source2"
python particles_import.py -i "C:/.../Portal 2/portal2" -e "C:/.../Half-Life Alyx/game/hlvr_addons/portal2"
python scenes_import.py    -i "C:/.../Half-Life Alyx/game/lostcoast" -e hlvr_addons/lostcoast
python panorama_import.py  -i "C:/.../Half-Life Alyx/game/csgo" -e csgo_imported
python models_import.py    -i "C:/.../Half-Life Alyx/game/l4d2" -e l4d2_source2
python materials_import.py -i "C:/.../Half-Life Alyx/game/ep2" -e hlvr  "materials/skybox"
```
* **-i** *\<dir\>*  This should be an absolute path pointing into a source1 game directory containing gameinfo.txt   
* **-e** *\<dir/modname\>*  Path to source2 mod/addon. \<*modname*\> (e.g. `-e portal2_imported`) instead of an absolute path will only work if the input folder **-i** is placed inside a source2 /game/ environment which also contains \<*modname*\>.  
* **[filter]** Optionally a path at the end can be added as a filter.
### Requirements:
* [Python](https://www.python.org/downloads/) >= 3.9  
* `pip install -r requirements.txt`
## Results
### [Inferno Source 2 Comparison - YouTube](https://www.youtube.com/watch?v=e-kcE9F_uH0)
