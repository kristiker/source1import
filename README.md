# source1import
Set of scripts for importing Source 1 assets such as materials, models, and particle effects into Source 2. Inspired by Valve's own internal utility (written in C++ and Perl), this one is in Python.

## Usage
#### Note:
* Make sure to extract s1 assets from VPK archives.
* Make sure to convert textures before materials. 
* Make sure to move the entire s1 `models` folder to `content/` **after the script is finished**.
* Make sure to move the entire s1 `sound` folder to `content/` and rename it to `sounds`.
* Make sure to read [this guide](https://developer.valvesoftware.com/wiki/Half-Life:_Alyx_Workshop_Tools/Importing_Source_1_Maps) for importing map files.
  - It suggests that your s1 files be in `game/<modname>` and imported files be in `content/hlvr_addons/<modname>_imported` – you will get correct texture scale and fixed up entities *only* that way.

Download app from [Releases](https://github.com/kristiker/source1import/releases).  
The app can be slow to open up, but has no prerequisites. If you want to make edits to the scripts & have Python installed, run the advanced way by downloading the code.
## Advanced:
### GUI:
* Just double-click on `source1import.pyw`.

### CLI:
```bash
cd utils
python scripts_import.py   -i "C:/.../Team Fortress 2/tf" -e "D:/Games/steamapps/common/sbox/addons/tf_source2"
python particles_import.py -i "C:/.../Portal 2/portal2" -e "C:/.../Half-Life Alyx/game/hlvr_addons/portal2"
python scenes_import.py    -i "C:/.../Half-Life Alyx/game/lostcoast" -e hlvr_addons/lostcoast
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
### [CS:GO Taser - Streamable](https://streamable.com/eders9)
### [Inferno Source 2 Comparison - YouTube](https://www.youtube.com/watch?v=e-kcE9F_uH0)
<img src="https://i.imgur.com/qxNDhEE.jpeg" width=100%>
<img src="https://i.imgur.com/zhHOMWJ.png" width=100%>
* bsp not supported yet, converted via hammer 5
