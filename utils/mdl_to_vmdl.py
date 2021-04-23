#!usr/bin/python
from shared.base_utils import Source

SHOULD_OVERWRITE = False

fs = Source("models")

def ImportMDLtoVMDL(mdl_path, move_s1_assets = False):
    vmdl_path = fs.Output(mdl_path).with_suffix('.vmdl')
    mdl_filename = fs.LocalDir(mdl_path).as_posix()
    vmdl_path.parent.MakeDir()

    print('Importing', mdl_filename)

    with open(vmdl_path, 'w+') as out:
        out.write("<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->\n{\r\n")
        out.write(f"\tm_sMDLFilename = \"{mdl_filename}\"\r\n")
        out.write("}\r\n")

if __name__ == "__main__":

    print('Source 2 VMDL Generator!')

    fileList = fs.collect_files('.mdl', '.vmdl', SHOULD_OVERWRITE)

    for mdl_path in fileList:
        ImportMDLtoVMDL(mdl_path)
