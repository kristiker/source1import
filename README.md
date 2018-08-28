# source2utils

## vmt_to_vmat.py

A simple Python 3.7 batch converter to convert Source 1 .vmt material files to the Source 2 .vmat format.
The material parameters does not map one to one, so it won't convert the materials perfectly. 

Usage: Run the script with material files or directories contaioning them as argumnets (or simply drag and drop the file/dir on the script file). WARNING: Will overwrite any vmat files it converts.

## mdl_to_vmdl.py

Generates a .vmdl file that will tell Source 2 to import its accompanying .mdl file.
You must leave the original .mdl files for the .vmdls to compile.

## qc_to_vmdl.py

(deprecated)

An older attempt at converting models before I figured out how to directly import .mdl files.
You can use this as a base if you want to import the source files manually.