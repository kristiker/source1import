***HEY! These utilities are still broken in a lot of ways and will fail very often. Please use with the understanding that it doesn't perfectly convert files yet and will only go through certain texture sets perfectly. This program has so far been tested on L4D2 content and HL2 content, both pulled from Source 1 Filmmaker's files and DLC.***

# source2utils

This is a 3rd generation fork, first created by Rectus and then Forked by DankParrot/Alpyne and Caseytube. These are a set of scripts to help convert Source 1 assets to Source 2 with ease, partly using the tools Valve already have available, and using a materials script that takes a lot of guesswork. These tools were intended to be used with the Source 2 Filmmaker, but can be applied to any Source 2 project.

## System Requirements:
- [Python](https://www.python.org/downloads/release/python-386/) 3.8

- [Python Image Library](https://pillow.readthedocs.io/en/5.1.x/installation.html) (`python -m pip install --upgrade Pillow`)
- [Numpy](https://numpy.org/install/) (`python -m pip install --upgrade numpy`)

- The Half-Life: Alyx Workshop Tools

- A Source 1 game's content

- Enough disk space (roughly 3x the size)

# Usage:
1. Create your addon in the [HL:A Workshop Tools](https://developer.valvesoftware.com/wiki/Half-Life:_Alyx_Workshop_Tools/Creating_an_Addon). I would recommend naming the mod the same name as the name you're pulling files from, especially if you're batch converting a whole game.

2. Extract the files you desire using GCFScape to the __GAME__ root of the mod, i.e. Half-Life Alyx/game/mod_name, following the same directory and naming scheme as Source 1

3. Make sure you have requirements in check (see [System Requirements](https://github.com/kristixx/source2utils#system-requirements)).

4. Running the scripts
    - General usage: `python_script.py -i "path/to/source1/game/root/" -o "path/to/source2/game/root" -f [optional] Force overwrite`
    - Examples
        * using _imported mod: `vmt_to_vmat.py -i "D:/Games/Half-Life Alyx/game/tf" -o "D:/Games/Half-Life Alyx/content/tf_imported"`
        * using addon: `vmt_to_vmat.py -i "D:/my files/tf" -o "D:/Games/Half-Life Alyx/content/hlvr_addons/tf"`

4. Importing materials
    - Have your `.tga` image files ready inside the __CONTENT__ folder. To export `.tga` files from `.vtf`:
        * Use VTFEdit Folder Export (especially for large numbers of files!). Can be skipped now that we have __vtf_to_tga.py__
        * VTFEdit will usually skip some `.vtf` files (especially for newer games). __vtf_to_tga.py__ can be used to export these remaining files.
        <!--- * __vtf_to_tga.py__ can import (read: translate) `*.txt` VTEX compile parameters too! Make sure to include them too. -->

    - Now that you have the texture images ready, run __vmt_to_vmat.py__ to import the actual `.vmt` material files.

5. Importing models
    - Run __mdl_to_vmdl.py__ to import `.mdl` model files.
        * This script doesn't actually do any 'real' importing. The importing process is achieved in engine by resourcecompiler.
        Unfortunately this in-house `.mdl` importer does not work on every asset, and will often crash the tools.
        To not have the tools crash, you have to delete the problematic `.vmdl` file and then: either ignore said model or manually import it via other tools.
        * https://github.com/REDxEYE/Source2Converter might be able to do a better job here.
    
    - Move the entire source1 /models/ folder (containing `.mdl`s) to source2, otherwise your models will show up as errors. <!--- this is dumb -->

6. Importing sounds
    - Rename the entire `/sound/` folder to `/sounds/` then move/copy it to the __CONTENT__ folder of your imported mod.

7. Importing particle system/sprite/script/ files
    - Not supported yet. You have to do them manually

8. Importing maps
    - Hammer can import `.vmf` map files on its own. https://developer.valvesoftware.com/wiki/Half-Life:_Alyx_Workshop_Tools/Importing_Source_1_Maps

9. Done! Open your mod. Your files should now attempt to compile as you load them, but sometimes doing this process too fast (i.e. scrolling through the Content Browser super quick) will make the tools hang. Simply wait and check the vconsole for messages.
- If your tools crash on load the problem is with the compiler being unable to import some of the source1 models. Open vconsole and take note of the problematic `.vmdl` to then delete it.

## vtf_to_tga.py

Similarly to VTFEdit's export function, this script exports all VTF files into TGA/PFM using the Source engine's native converter tool [VTF2TGA](https://developer.valvesoftware.com/wiki/VTF2TGA). Included in the files are 2 versions of VTF2TGA; however, you can edit the script to use your own local VTF2TGA.

It is recommended to use VTFEdit first, as it is much faster at batch extracting image files. You can use vtf_to_tga.py afterwards to extract the images VTFEdit could not.

## vmt_to_vmat.py

A simple Python batch converter to convert Source 1 .vmt material files to the Source 2 .vmat format.

## mdl_to_vmdl.py

Generates a .vmdl file that will tell Source 2 to import its accompanying .mdl file. See [this](https://developer.valvesoftware.com/wiki/Half-Life:_Alyx_Workshop_Tools/Importing_Source_1_Models)

Do not delete the .mdl files. You must leave them for the .vmdls to compile.
