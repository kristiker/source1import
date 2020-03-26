***HEY! These utilities are still broken in a lot of ways and will fail very often. Please use with the understanding that it doesn't perfectly convert files yet and will only go through certain texture sets perfectly. This program has so far been tested on L4D2 content and HL2 content, both pulled from Source 1 Filmmaker's files and DLC.***

# source2utils

This is a 3rd generation fork, first created by Rictus and then Forked by DankParrot/Alphyne. These are a set of scripts to help convert Source 1 assets to Source 2 with ease, partly using the tools Valve already have available, and using a materials script that takes a lot of guesswork. These tools were intended to be used with the Source 2 Filmmaker, but can be applied to any Source 2 project.

Below is a list of branches that have been tested with the tool:
- Source Filmmaker Branch (most content from this build is stable and should work nicely.)

Below is a list of branches that DON'T work with this tool (in SteamVR):
- Left 4 Dead 2 (most content works, but player models crash the engine.)

## vmt_to_vmat.py

A simple Python 3.7 batch converter to convert Source 1 .vmt material files to the Source 2 .vmat format.

The material parameters does not map one to one, so it won't convert the materials perfectly. 

I've taken some liberties with the available Standard VR shader in SteamVR as my guideline, and converting a specular map from Source 1 to PBR in Source 2 is not going to be totally 1 to 1. However, it does look pretty good in most use cases, and I'd reccomend modifying the script to your needs depending on what game/art style you're working with. For instance, I've had to dull the ReflectanceRange across the board for HL2 assets, which I didn't need to do for L4D2 assets.

To use, first modify global_vars.txt to include your game's content path. Then, run the script using `python vmt_to_vmat.py modName`, replacing modName with the name of your mod's folder (i.e. hl2, left4dead2, usermod, etc.) You may also add a second argument at the end if you wish to specify a specific directory.

## mdl_to_vmdl.py

Generates a .vmdl file that will tell Source 2 to import its accompanying .mdl file.

You must leave the original .mdl files for the .vmdls to compile.

Run the script with a __directory__ like `python mdl_to_vmdl.py models` and it will fill that directoy with .vmdls. Make sure you leave all the MDLs in tact so Source 2 can convert them.

## qc_to_vmdl.py

(deprecated)

An older attempt at converting models before I figured out how to directly import .mdl files.
You can use this as a base if you want to import the source files manually.

## System Requirements:
Python 3.7 or later

Python Image Library (PIL)  5.4.1

The SteamVR Workshop Tools (you do not need VR to run these!)

A Source 1 game's content

# Usage:
Step 1: Create your mod in the SteamVR Workshop Tools (see [this guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2014947360) on how to make this happen for the S2FM.) I would recommend naming the mod the same name as the name you're pulling files from, especially if you're batch converting a whole game.

Step 2: Extract the files you desire using GCFScape to the __CONTENT__ root of the mod, i.e. SteamVR/tools/steamvr_environments/content/steamtours_addons/hl2, following the same format as Source 1.

Step 3: Using VTFEdit, extract the textures from the .vtf files into .tga using the "Convert Folder" functionality under tools. Again, make sure these TGAs follow the exact same layout as Source 1.

Step 3.5: Add a new empty .txt file to the root of your mod's content file, called convertedBumpmaps.txt. This file stores the filenames of the .tga files that have been converted to S2's flipped green channel format.

Step 4: __Modify global_vars.txt to include the details of your project's files, pointing to your content/steamtours_addon/ folder.__

Step 5: First run mdl_to_vmdl.py, then run vmt_to_vmat.py, using the instructions above.

Step 6: Open your mod. Your files should now attempt to convert as you load them, but sometimes doing this process too fast (i.e. scrolling through the Content Browser super quick) will crash the game. Please take care not to break your system while loading these files.
