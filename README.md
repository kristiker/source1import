# source1import
Set of scripts for importing Source 1 assets such as materials, models, and particle effects into Source 2. Inspired by Valve's own [source1import.exe](https://www.youtube.com/watch?v=ZnY82mVJi9w) (written in C++ and Perl), this one is in Python.

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/downloads/release/python-386/)
## Requires:
[Python](https://www.python.org/downloads/release/python-396/#:~:text=Windows%20installer%20(64-bit)) 3.9  
`python -m pip install -r requirements.txt`

## Installing:
[Download as ZIP](https://github.com/kristiker/source1import/archive/refs/heads/master.zip) and Extract  
Open folder, press `Ctrl + L`, enter `cmd` and run the following commands
```bash
python -m pip install -r requirements.txt
cd utils
```
All set. Use `python materials_import.py --help` or read below examples to get started.

## Usage
Scripts are launched via command line:

**-i** *\<dir\>*  This should be an absolute path pointing into a source1 game directory containing gameinfo.txt   

**-e** *\<dir/modname\>*  Path to source2 mod/addon. \<*modname*\> (e.g. `-e portal2_imported`) instead of an absolute path will only work if the input folder **-i** is placed inside a source2 /game/ environment which also contains \<*modname*\>.  


### Usage examples:
```bash
cd utils
python scripts_import.py   -i "C:/.../Team Fortress 2/tf" -e "D:/Games/steamapps/common/sbox/addons/tf_source2"
python particles_import.py -i "C:/.../Portal 2/portal2" -e "C:/.../Half-Life Alyx/game/hlvr_addons/portal2"
python scenes_import.py    -i "C:/.../Half-Life Alyx/game/lostcoast" -e hlvr_addons/lostcoast_source2
python panorama_import.py  -i "C:/.../Half-Life Alyx/game/csgo" -e csgo_imported
python models_import.py    -i "C:/.../Half-Life Alyx/game/l4d2" -e l4d2_source2
python materials_import.py -i "C:/.../Half-Life Alyx/game/ep2" -e hlvr
```

#### Note:
* Make sure to import texture content first (`.vtf` files), via VTFEdit :: Tools -> Convert folder, or the included `vtf_to_tga.py`, using the same parameters.  

    Materials and particles won't convert correctly if `.tga` files aren't present inside `/content/<modname>/materials/` 


## Results
### [Inferno Source 2 Comparison - YouTube](https://www.youtube.com/watch?v=e-kcE9F_uH0)
