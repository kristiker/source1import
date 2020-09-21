***HEY! These utilities are still broken in a lot of ways and will fail very often. Please use with the understanding that it doesn't perfectly convert files yet and will only go through certain texture sets perfectly. This program has so far been tested on L4D2 content and HL2 content, both pulled from Source 1 Filmmaker's files and DLC.***

# source2utils

This is a 3rd generation fork, first created by Rectus and then Forked by DankParrot/Alpyne and Caseytube. These are a set of scripts to help convert Source 1 assets to Source 2 with ease, partly using the tools Valve already have available, and using a materials script that takes a lot of guesswork. These tools were intended to be used with the Source 2 Filmmaker, but can be applied to any Source 2 project.

## System Requirements:
- [Python](https://www.python.org/downloads/) 3.7 or later

- [Python Image Library](https://pillow.readthedocs.io/en/5.1.x/installation.html) (`python -m pip install --upgrade Pillow`)

- The Half-Life: Alyx Workshop Tools

- A Source 1 game's content

- Enough disk space

# Usage:
1. Create your mod in the [HL:A Workshop Tools](https://developer.valvesoftware.com/wiki/Half-Life:_Alyx_Workshop_Tools/Creating_an_Addon). I would recommend naming the mod the same name as the name you're pulling files from, especially if you're batch converting a whole game.

2. Extract the files you desire using GCFScape to the __CONTENT__ root of the mod, i.e. Half-Life Alyx/content/hlvr_addons/csgo, following the same directory and naming scheme as Source 1 (`/sound/` however has to be renamed into `/sounds/`).

3. Make sure you have requirements in check (see [System Requirements](https://github.com/kristixx/source2utils#system-requirements)). Close your tools before running any script.

4. Run [vtf_to_tga.py](https://github.com/kristixx/source2utils#vtf_to_tgapy) first and [vmt_to_vmat.py](https://github.com/kristixx/source2utils#vmt_to_vmatpy) second using the instructions below. [mdl_to_vmdl.py](https://github.com/kristixx/source2utils#mdl_to_vmdlpy) can be safely ran at any order.

5. Open your mod. Your files should now attempt to compile as you load them, but sometimes doing this process too fast (i.e. scrolling through the Content Browser super quick) will make the tools hang. Simply wait and check the vconsole for messages.
- If your tools crash on load the problem is with the compiler being unable to import some of the source1 models.

## vtf_to_tga.py

Similarly to VTFEdit's export function, this script exports all VTF files into TGA/PFM using the Source engine's native converter tool [VTF2TGA](https://developer.valvesoftware.com/wiki/VTF2TGA). Included in the files are 2 versions of VTF2TGA; however, you can edit the script to use your own local VTF2TGA.

Usage: Run the script directly, or from the command line: `python vtf_to_tga.py "C:/../my_addon/content/materials"`.

## vmt_to_vmat.py

A simple Python 3.7 batch converter to convert Source 1 .vmt material files to the Source 2 .vmat format.

The material parameters does not map one to one, so it won't convert the materials perfectly. 

Usage: Run the script directly, or from the command line: `python vmt_to_vmat.py "C:/../my_addon/content/materials"`.
## mdl_to_vmdl.py

Generates a .vmdl file that will tell Source 2 to import its accompanying .mdl file. See [this](https://developer.valvesoftware.com/wiki/Half-Life:_Alyx_Workshop_Tools/Importing_Source_1_Models)

Do not delete the .mdl files. You must leave them for the .vmdls to compile.

Usage: Run the script directly, or from the command line: `python mdl_to_vmdl.py "C:/../my_addon/content/models"`. Make sure you leave all the MDLs in tact so Source 2 can convert them.
