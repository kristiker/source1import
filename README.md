# source2utils

This is a 3rd generation fork, first created by Rictus and then Forked by DankParrot/Alphyne.
These scripts are meant to run using Python 3.7, and also require an installation of the Python Image Library

# System Requirements:
Python 3.7 or later
Python Image Library (PIL)

## vmt_to_vmat.py

A simple Python 3.7 batch converter to convert Source 1 .vmt material files to the Source 2 .vmat format.
The material parameters does not map one to one, so it won't convert the materials perfectly. 
I've taken some liberties with the available Standard VR shader in SteamVR as my guideline, and converting a specular map from Source 1 to PBR in Source 2 is not going to be totally 1 to 1. However, it does look pretty good in most use cases, and I'd reccomend modifying the script to your needs depending on what game/art style you're working with. For instance, I've had to dull the ReflectanceRange across the board for HL2 assets, which I didn't need to do for L4D2 assets.

# Usage:
Modify the script to include your personal game's content root (i.e. SteamVR/tools/steamvr_environments/content/steamtours_addons/) in the PATH_TO_GAME_CONTENT_ROOT variable.
Run the script using your mod name as an argument, i.e.:
python vmt_to_vmat.py left4dead2_movies
You can also add to that an argument for a specific path to a material file or folder, i.e.:
python vmt_to_vmat.py left4dead2_movies "C:\Program Files (x86)\Steam\steamapps\common\SteamVR\tools\steamvr_environments\content\steamtours_addons\hl2\materials\models\airboat"

## mdl_to_vmdl.py

Generates a .vmdl file that will tell Source 2 to import its accompanying .mdl file.
You must leave the original .mdl files for the .vmdls to compile.

Run the script with a __directory__ like `py mdl_to_vmdl.py models` and it will fill that directoy with .vmdls. Make sure you leave all the MDLs in tact so Source 2 can convert them.

## qc_to_vmdl.py

(deprecated)

An older attempt at converting models before I figured out how to directly import .mdl files.
You can use this as a base if you want to import the source files manually.
