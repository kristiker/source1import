import re, sys, os

INPUT_FILE_EXT = '.qc'
OUTPUT_FILE_EXT = '.vmdl'

MATERIALS_DIR_BASE = 'materials/'

VMDL_BASE = '''<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->
{
    m_meshList =
    {
        m_meshList =
        [
            <meshes>
        ]
    }
    
}
'''
VMDL_MESH = '''{{
    m_meshName = "{mesh_name}"
    m_meshFile = "{mesh_file}"
    m_materialSearchPath = "{cdmaterials}"
    m_bSkinParentedObjects = true
    m_bLegacySkinParentedTransforms = false
    m_bExpensiveTangents = false
    m_bHighPrecisionTexCoords = false
    m_bPerVertexCurvature = false
    m_bBentNormals = false
    m_bIgnoreCloth = false
    m_bGetSkinningFromLod0 = false
    m_pMorphInfo = null
}},
'''.replace('\n', '\n\t\t\t')

def parse_qc(qc):
    # strip comments
    qc = re.sub(r'//.*', '', qc)
    tokens = re.split(r'\s+', qc)

    return tokens

def walk_dir(dirname):
    files = []

    for root, dirs, filenames in os.walk(dirname):
        for filename in filenames:
            if filename.lower().endswith(INPUT_FILE_EXT):
                files.append(os.path.join(root,filename))
            
    return files

abspath = ''
files = []

# recursively search all dirs and files
for path in sys.argv:
    abspath = os.path.abspath(path)
    if os.path.isdir(abspath):
        files.extend(walk_dir(abspath))
        break
    #else:
    #    if abspath.lower().endswith(INPUT_FILE_EXT):
    #        files.append(abspath)

def putl(f, line, indent = 0):
    f.write(('\t' * indent) + line + '\r\n')

def strip_quotes(s):
    return s.strip('"').strip("'")

def fix_path(s):
    return strip_quotes(s).replace('\\', '/').replace('//', '/').strip('/')

def relative_path(s, base):
    base = base.replace(abspath, '')
    base = base.replace(os.path.basename(base), '')

    return fix_path(os.path.basename(abspath) + base + '/' + fix_path(s))


def get_mesh_name(file):
    return os.path.splitext(os.path.basename(fix_path(file)))[0]

for filename in files:

    out_name = filename.replace(INPUT_FILE_EXT, OUTPUT_FILE_EXT)

    if os.path.exists(out_name): continue

    print('Converting', os.path.basename(filename))

    qc_params = []
    
    with open(filename, 'r') as qc_file:
        qc_params = parse_qc(qc_file.read())

    cdmaterials = ''
    meshes = []

    # naïve method of getting mesh list
    for i, p in enumerate(qc_params):
        if p in ['$model', '$body']:
            meshes.append((qc_params[i+1], qc_params[i+2]))
        elif p == '$bodygroup':
            meshes.append((qc_params[i+1], qc_params[i+4]))
        elif p == '$cdmaterials' and not cdmaterials: # just use first $cdmaterials
            cdmaterials = qc_params[i+1]

    meshes_str = ''
    for m in meshes:
        meshes_str += VMDL_MESH.format(
            mesh_name=get_mesh_name(m[1]), # ignore specified mesh name for now
            mesh_file=relative_path(m[1], filename),
            cdmaterials=MATERIALS_DIR_BASE + fix_path(cdmaterials)
        )

    #out = sys.stdout

    with open(out_name, 'w') as out:
        putl(out, VMDL_BASE.replace('<meshes>', meshes_str).replace((' ' * 4), '\t'))
