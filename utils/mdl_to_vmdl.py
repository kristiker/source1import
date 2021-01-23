#!usr/bin/python
from pathlib import Path
import shared.base_utils as sh

SHOULD_OVERWRITE = False

IN_EXT = '.mdl'
OUT_EXT = '.vmdl'

fs = sh.Source("models")

def ImportMDLtoVMDL_simple(mdl_path, move_s1_assets = False):
    vmdl_path = fs.Output(mdl_path).with_suffix(OUT_EXT)
    m_sMDLFilename = fs.LocalDir(mdl_path).as_posix()
    vmdl_path.parent.MakeDir()

    print('Importing', m_sMDLFilename)

    with open(vmdl_path, 'w+') as out:
        out.write("<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->\n{\r\n")
        out.write(f"\tm_sMDLFilename = \"{m_sMDLFilename}\"\r\n")
        out.write("}\r\n")

def main():
    
    print('Source 2 VMDL Generator!')
    
    fileList = fs.collect_files(IN_EXT, OUT_EXT, SHOULD_OVERWRITE)

    for mdl_path in fileList:
        ImportMDLtoVMDL_simple(mdl_path)

if __name__ == "__main__":
    main()
