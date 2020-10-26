# Converts Source 1 .vmt material files to simple Source 2 .vmat files.
#
# Copyright (c) 2016 Rectus
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import re, sys, os, json
from pathlib import Path
from shutil import copyfile, move
from difflib import get_close_matches
from enum import Enum
import pyutils.PFM as PFM
from PIL import Image, ImageOps
import py_shared as sh

# generic, blend instead of vr_complex, vr_simple_2wayblend etc...
LEGACY_SHADER = False
NEW_SH = not LEGACY_SHADER

# File format of the textures. Needs to be lowercase
# source 2 supports all kinds: tga jpeg png gif psd exr tiff pfm...
# Just make sure the name of the file is the same as that of the .vtf, and that the path in the .vmt matches.
TEXTURE_FILEEXT = '.tga' # psd

# py_shared TODO: use an IN and OUT akin to s1import_txtmap
# Path to content root, before /materials/
PATH_TO_CONTENT_ROOT = r""
PATH_TO_NEW_CONTENT_ROOT = r""

# Set this to True if you wish to overwrite your old vmat files. Same as adding -f to launch parameters
OVERWRITE_VMAT = False
OVERWRITE_SKYBOX = False

# True to let vtex handle the inverting of the normalmap.
NORMALMAP_G_VTEX_INVERT = True

BASIC_PBR = True
MISSING_TEXTURE_SET_DEFAULT = True
USE_SUGESTED_DEFAULT_ROUGHNESS = True
SURFACEPROP_AS_IS = False
SKYBOX_CREATE_LDR_FALLBACK = True

DEBUG = False
def msg(*args, **kwargs):
    if DEBUG:
        print("@ DBG:", *args, **kwargs)

materials = Path("materials")
fs = sh.Source(materials, PATH_TO_CONTENT_ROOT, PATH_TO_NEW_CONTENT_ROOT)

skybox = Path("skybox")
vmtSkybox = {}
skyboxFaces = ['up', 'dn', 'lf', 'rt', 'bk', 'ft']

shader = Enum("shader",
    [
        "black",
        "vr_black_unlit",
        "generic",
        "vr_basic",
        "vr_complex",
        "vr_simple",
        "vr_standard", # steamvr shader
        "blend",
        "vr_simple_2way_blend",
        "sky",
        "vr_eyeball",
        "simple_water",
        "refract",
        "cables",
        "MonitorScreen",
        "projected_decal_modulate",
        "spritecard", # what is this mess
        "vr_glass", # glass
        "vr_projected_decals",
        "vr_static_overlay", # vr_projected_decals without the ability to subdivide
        "vr_power_cables",
        "tools_wireframe", # vr_tools_wireframe
        "tools_generic", # for tool textures /materials/tools/
    ]
)

# material types need to be lowercase
materialTypes = {
    "black":                shader.black,
    "sky":                  shader.sky,
    "unlitgeneric":         shader.vr_complex,
    "vertexlitgeneric":     shader.vr_complex,
    "decalmodulate":        shader.vr_projected_decals, # https://developer.valvesoftware.com/wiki/Decals#DecalModulate
    "lightmappedgeneric":   shader.vr_complex,
    "lightmappedreflective":shader.vr_complex,
    "character":            shader.vr_complex, # https://developer.valvesoftware.com/wiki/Character_(shader)
    "customcharacter":      shader.vr_complex,
    "teeth":                shader.vr_complex,
    "water":                shader.simple_water,
    "refract":              shader.refract,
    "worldvertextransition":shader.vr_simple_2way_blend,
    "lightmapped_4wayblend":shader.vr_simple_2way_blend,
    "cables":               shader.cables,
    "lightmappedtwotexture":shader.vr_complex, # 2 multiblend $texture2 nocull scrolling, model, additive.
    "unlittwotexture":      shader.vr_complex, # 2 multiblend $texture2 nocull scrolling, model, additive.
    "cable":                shader.cables,
    "splinerope":           shader.cables,
    "shatteredglass":       shader.vr_glass,
    "wireframe":            shader.tools_wireframe,
    "spritecard":           shader.spritecard, #"modulate",
    #"subrect":              shader.spritecard, # should we just cut? $Pos "256 0" $Size "256 256" $decalscale 0.25 decals\blood1_subrect.vmt
    #"weapondecal": weapon sticker
    "patch":                shader.vr_complex, # fallback if include doesn't have one
}

def chooseShader():

    sh = {x:0 for x in shader}

    # not recognized, give empty shader
    if matType not in materialTypes:
        if DEBUG:
            if (ffff := "At least 1 material: unmatched shader " + matType) not in failureList: failureList.append(ffff)
        return shader.vr_black_unlit

    if LEGACY_SHADER:   sh[shader.generic] += 1
    else:               sh[materialTypes[matType]] += 1

    if vmtKeyValues.get('$decal') == '1': sh[shader.vr_projected_decals] += 10

    if matType == "worldvertextransition":
        if vmtKeyValues.get('$basetexture2'): sh[shader.vr_simple_2way_blend] += 10

    elif matType == "lightmappedgeneric":
        if vmtKeyValues.get('$newlayerblending') == '1': sh[shader.vr_simple_2way_blend] += 10
        #if vmtKeyValues.get('$decal') == '1': sh[shader.vr_projected_decals] += 10

    elif matType == "":
        pass
    # TODO: vr_complex -> vr simple if no selfillum tintmask detailtexture specular
    return max(sh, key = sh.get)

ignoreList = [ "dx9", "dx8", "dx7", "dx6", "proxies"]

IN_EXT = ".vmt"
OUT_EXT = ".vmat"

VMAT_DEFAULT_PATH = Path("materials/default")
f_KeyVal = '\t{}\t{}\n'
f_KeyValQuoted = '\t{}\t"{}"\n'
f_KeyQuotedValQuoted = '\t"{}"\t"{}"\n'

def ext(this: Path, ext = TEXTURE_FILEEXT) -> Path:
    return this.with_suffix(ext)
def default(defaulttype):
    return VMAT_DEFAULT_PATH / Path("default" + defaulttype).with_suffix(".tga")

print('\nSource 2 Material Conveter! By Rectus via Github.')
print('Initially forked by Alpyne, this version by caseytube.\n')
print('--------------------------------------------------------------------------------------------------------')

def parseKeyValue(line, vmtKeyValues):
    words = []
    nextLine = ''

    # doesn't split inside qotes
    words = re.split(r'\s', line, maxsplit=1) #+(?=(?:[^"]*"[^"]*")*[^"]*$)
    words = list(filter(len, words))

    if not words: return
    elif len(words) == 1:
        Quott = words[0].count('"')
        # fix for: "$key""value""
        if Quott >= 4:
            m = re.match(r'^((?:[^"]*"){1}[^"]*)"(.*)', line)
            if m:
                line = m.group(1)  + '" ' + m.group(2)
                parseKeyValue(line, vmtKeyValues)
        # fix for: $key"value"
        elif Quott == 2:
            # TODO: sth better that keeps text inside quotes intact.
            #line = line.replace('"', ' " ').rstrip(' " ') + '"'
            line = line.replace('"', '')
            parseKeyValue(line, vmtKeyValues)
        return # no recursive loops please
    elif len(words) > 2:
        # fix for: "$key""value""$key""value" - we come here after len == 1 has happened
        nextLine = ' '.join(words[2:]) # words[2:3]
        words = words[:2]

    key = words[0].strip('"').lower()

    if not key.startswith('$'):
        if not 'include' in key:
            return

    # "GPU>=2?$detailtexture"
    if '?' in key:
        #key = key.split('?')[1].lower()
        key.split('?')
        if key[0] == 'GPU>=2':
            key = key[2].lower()
        else:
            if key[0] == 'GPU<2':
                return
            key = key[2].lower()

    val = words[1].lower().strip().strip('"')

    vmtKeyValues[key] = val

    if nextLine: parseKeyValue(nextLine, vmtKeyValues)


def OutName(path: Path) -> Path:
    return fs.NoSpace(fs.Output(path).with_suffix(OUT_EXT))

# "environment maps\metal_generic_002.vtf" -> "materials/environment maps/metal_generic_002.tga"
def fixVmtTextureDir(localPath, fileExt = TEXTURE_FILEEXT) -> str:
    if localPath == "" or not isinstance(localPath, str):
        return ""
    return fs.FixLegacyLocal(Path(localPath).with_suffix(fileExt)).as_posix()

# TODO: renameee, remap table etc...
def formatNewTexturePath(vmtPath, textureType = TEXTURE_FILEEXT, noRename = False, forReal = True):

    #vmtPath = fs.Input(fixVmtTextureDir(vmtPath, '')) + "." + textureType.split(".", 1)[1] or ''

    #if USE_DEFAULT_FOR_MISSING_TEXTURE and not os.path.exists(vmtPath):
    #    return default(textureType)

    #return fs.LocalDir(vmtPath)
    return str(fixVmtTextureDir(vmtPath))

def getTexture(vmtParam):
    """
    Returns full texture path of given vmt Param or vmt Path\n
    $basetexture              -> C:/../materials/as/seen/in/basetexture/tex_color.tga\n
    path/to/texture_color.tga -> C:/../materials/path/to/texture_color.tga\n
    """
    if type(vmtParam) is str:
        if value := vmtKeyValues.get(vmtParam):
            if (path := fs.Output(fixVmtTextureDir(value))).exists():
                return path
        elif (path := fs.Output(fixVmtTextureDir(vmtParam))).exists():
                return path
        elif (path := fs.Output(Path(vmtParam))).exists():
                return path

    elif isinstance(vmtParam, Path):
        if not vmtParam.exists():
            if (path := fs.Output(vmtParam)).exists():
                return path
        return vmtParam

    # TODO: if still not found check for vtf in input
    # if exists, use vtf_to_tga to extract it to output
    # source1import does the same

    return None

def createMask(vmtTexture, copySub = '_mask', channel = 'A', invert = False, queue = True):

    imagePath = getTexture(vmtTexture)
    #msg("createMask with", fs.LocalDir(vmtTexture), copySub, channel, invert, queue)

    if not imagePath:
        msg("No input for createMask.", imagePath)
        failureList.append(f"{str(vmtFilePath)} - {vmtTexture} not found")
        return default(copySub)

    if invert:  newMask = imagePath.stem + '_' + channel[:3].lower() + '-1' + copySub
    else:       newMask = imagePath.stem + '_' + channel[:3].lower()        + copySub
    newMaskPath = imagePath.parent / Path(newMask).with_suffix(imagePath.suffix)

    if newMaskPath.exists(): #and not DEBUG:
        return fs.LocalDir(newMaskPath)

    if not imagePath.is_file() or not imagePath.exists():
        failureList.append(str(vmtFilePath))
        print(f"~ ERROR: Couldn't find requested image ({imagePath}). Please check.")
        return default(copySub)

    image = Image.open(imagePath).convert('RGBA')

    if channel == 'L':
        imgChannel = image.convert('L')
    else:
        imgChannel = image.getchannel(str(channel))

    if invert:
        imgChannel = ImageOps.invert(imgChannel)

    colors = imgChannel.getcolors()
    if len(colors) == 1: # mask with single color
        if copySub == "_rough" and colors[0][1] == 0: # fix some very dumb .convert('RGBA') with 255 255 255 alpha
            return default(copySub) # TODO: should this apply to other types of masks as well?
        return fixVector(f"{{{colors[0][1]} {colors[0][1]} {colors[0][1]}}}", True)

    bg = Image.new("L", image.size)

    # Copy the specified channel to the new image using itself as the mask
    bg.paste(imgChannel)

    bg.convert('L').save(newMaskPath, optimize=True) #.convert('P', palette=Image.ADAPTIVE, colors=8)
    bg.close()
    print("+ Saved mask to", fs.LocalDir(newMaskPath))

    return fs.LocalDir(newMaskPath)

def flipNormalMap(localPath):

    image_path = fs.Output(localPath)
    if not image_path.exists(): return

    if NORMALMAP_G_VTEX_INVERT:
        with open(image_path.with_suffix(".txt"), 'w') as settingsFile: # TODO: add keyval
            settingsFile.write('"settings"\n{\t"legacy_source1_inverted_normal" "1"\n}')
    else:
        # Open the image and convert it to RGBA, just in case it was indexed
        image = Image.open(image_path).convert('RGB')

        r,g,b,a = image.split()
        g = ImageOps.invert(g)
        final_transparent_image = Image.merge('RGB', (r,g,b,a))
        final_transparent_image.save(image_path)

    return localPath

def fixVector(s, addAlpha = 1, returnList = False):

    s = str(s)
    if('{' in s or '}' in s): likelyColorInt = True
    else: likelyColorInt = False

    s = s.strip() # TODO: remove letters
    s = s.replace('"', '').replace("'", "")
    s = s.strip().replace(",", "").strip('][}{')

    try: originalValueList = [str(float(i)) for i in s.split(' ') if i != '']
    except: return None #originalValueList =  [1.000000, 1.000000, 1.000000]

    dimension = len(originalValueList)
    if dimension < 3: likelyColorInt = False

    for strvalue in originalValueList:
        flvalue = float(strvalue)
        if likelyColorInt: flvalue /= 255

        originalValueList[originalValueList.index(strvalue)] = "{:.6f}".format(flvalue)

    # todo $detailscale "[8 8 8]" ---> g_vDetailTexCoordScale [8.000000 8.000000 8.000000]
    if(dimension <= 1):
        originalValueList.append(originalValueList[0])  # duplicate for 2D
    elif(addAlpha and (dimension == 3)):
        originalValueList.append("{:.6f}".format(1))    # add alpha

    if returnList:  return originalValueList
    else:           return '[' + ' '.join(originalValueList) + ']'

surfprop_force = {
    'stucco':       'world.drywall',
    'tile':         'world.tile_floor',
    'metalpanel':   'world.metal_panel',
    'wood':         'world.wood_solid',
}

surfprop_list = []#['metal_panel', 'wood_solid', 'concrete', "plaster"]

json_path = fs.currentDir / Path("surfproperties_hla.json")

with open(json_path, "r+") as fp:
    try: json_data = json.load(fp)
    except json.decoder.JSONDecodeError:
        json_data = {}

    surfprop_list = json_data.get("surfproperties_hla", [])
    #print(surfprop_HLA)

def fixSurfaceProp(vmtVal):

    if SURFACEPROP_AS_IS or (vmtVal in ('default', 'default_silent', 'no_decal', 'player', 'roller', 'weapon')):
        return vmtVal

    elif vmtVal in surfprop_force:
        return surfprop_force[vmtVal]

    if("props" in vmatFilePath.parts): match = get_close_matches('prop.' + vmtVal, surfprop_list, 1, 0.4)
    else: match = get_close_matches('world.' + vmtVal, surfprop_list, 1, 0.6) or get_close_matches(vmtVal, surfprop_list, 1, 0.6)

    return match[0] if match else vmtVal


def int_val(vmtVal, bInvert = False):
    if bInvert: vmtVal = not int(vmtVal)
        #return str(int(not int(vmtVal)))
    return str(int(vmtVal))

def mapped_val(vmtVal, dMap):
    if not vmtVal or vmtVal not in dMap:
        return None # use default value
    return str(int(dMap[vmtVal]))

def float_val(vmtVal):
    return "{:.6f}".format(float(vmtVal.strip(' \t"')))

def vmat_layered_param(vmatKey, layer = 'A', force = False):
    if vmatShader == shader.vr_simple_2way_blend or force:
        return vmatKey + layer
    return vmatKey

MATRIX_CENTER = 0
MATRIX_SCALE = 1
MATRIX_ROTATE = 2
MATRIX_TRANSLATE = 3

def listMatrix(s):
    # [0, 1] center defines the point of rotation. Only useful if rotate is being used.
    # [2, 3] scale fits the texture into the material the given number of times. '2 1' is a 50% scale in the X axis.
    # 4      rotate rotates the texture counter-clockwise in degrees. Accepts any number, including negatives.
    # [5, 6] translate shifts the texture by the given numbers. '.5' will shift it half-way.

    # "center .5 .5 scale 1 1 rotate 0 translate 0 0" -> [ [0.5 0.5], [1.0, 1.0], 0.0, [0.0, 0.0] ]
    if not s: return

    s = s.strip('"')
    eachTerm = [i for i in s.split(' ')]
    transformList = [None, None, None, None]

    for i in eachTerm:
        try:
            if i == 'rotate':
                nextTerm = int(eachTerm[eachTerm.index(i)+1].strip("'"))
                transformList [ MATRIX_ROTATE ] = nextTerm
                continue

            nextTerm =      float(eachTerm[eachTerm.index(i)+1].strip("'"))
            nextnextTerm =  float(eachTerm[eachTerm.index(i)+2].strip("'"))

            if i == 'center':   transformList [ MATRIX_CENTER ]     = [ nextTerm, nextnextTerm ]
            if i == 'scale':    transformList [ MATRIX_SCALE ]      = [ nextTerm, nextnextTerm ]
            if i == 'translate':transformList [ MATRIX_TRANSLATE ]  = [ nextTerm, nextnextTerm ]
        except:
            pass

    return transformList

def is_convertible_to_float(value):
    try:
        float(value)
        return True
    except: return False

def collectSkyboxFaces(vmtKeyValues, name, face):
        hdrbasetexture = vmtKeyValues.get('$hdrbasetexture')
        hdrcompressedtexture = vmtKeyValues.get('$hdrcompressedtexture')

        if name not in vmtSkybox:
            vmtSkybox.setdefault(name, {'up':{}, 'dn':{}, 'lf':{}, 'rt':{}, 'bk':{}, 'ft':{}})
            if hdrcompressedtexture:
                vmtSkybox[name]['_hdrtype'] = 'compressed'
            if hdrbasetexture:
                vmtSkybox[name]['_hdrtype'] = 'uncompressed'

        if hdrbasetexture or hdrcompressedtexture:
            if not vmtKeyValues.get('$_vmt_ldr_fallback') and vmtKeyValues.get('$basetexture') and not '_ldr_fallback' in vmtFilePath.stem:
                newVmtPath = vmtFilePath.parent / Path(name.replace("hdr", "").rstrip('_') + "_ldr_fallback" + face).with_suffix(IN_EXT)
                if SKYBOX_CREATE_LDR_FALLBACK and fs.ShouldOverwrite(newVmtPath):
                    print("Splitting LDR fallback from", vmtSkyboxFile, "to", fs.LocalDir(newVmtPath))
                    vmtNewLines = []
                    with open(vmtFilePath, 'r') as vmatFile:
                        for line in vmatFile.readlines():
                            line = line.lower()
                            if '$hdrbasetexture' in line or '$hdrcompressedtexture' in line:
                                line.replace('$hdrbasetexture', '$_vmt_ldr_fallback')
                                line.replace('$hdrcompressedtexture', '$_vmt_ldr_fallback')

                            vmtNewLines.append(line)

                    with open(newVmtPath, 'w') as vmtNewFile: vmtNewFile.writelines(vmtNewLines)

                vmtFileList_extra.append(newVmtPath)

            if '$basetexture' in vmtKeyValues: del vmtKeyValues['$basetexture']

        if face not in vmtSkybox[name]: return

        texture = vmtKeyValues.get('$hdrbasetexture') or vmtKeyValues.get('$hdrcompressedtexture') or vmtKeyValues.get('$basetexture')
        facePath = fs.Output(formatNewTexturePath(texture, textureType = '.pfm' if hdrbasetexture else TEXTURE_FILEEXT))

        if(facePath and os.path.exists(facePath)):
            vmtSkybox[name][face]['path'] = os.path.basename(facePath)

            if not hdrbasetexture:
                vmtSkybox[name][face]['resolution'] = Image.open(facePath).size
            else:
                vmtSkybox[name][face]['resolution'] = PFM.read_pfm(facePath)[2]

            face_res = max(vmtSkybox[name][face]['resolution'][0],vmtSkybox[name][face]['resolution'][1])
            vmtSkybox[name]['_maxres'] = max(face_res, vmtSkybox[name].get('_maxres') or 0)

        faceTransform = listMatrix(vmtKeyValues.get('$basetexturetransform'))
        if(faceTransform and faceTransform[MATRIX_ROTATE]):
            vmtSkybox[name][face]['rotate'] = int(float(faceTransform[MATRIX_ROTATE]))
            msg("Collecting", face, "transformation", vmtSkybox[name][face]['rotate'], 'degrees')

VMAT_REPLACEMENT = 0
VMAT_DEFAULTVAL = 1
VMAT_TRANSLFUNC = 2
VMAT_EXTRALINES = 3

vmt_to_vmat = {

#'shader': { '$_vmat_shader':    ('shader',  'generic.vfx', [ext, '.vfx']),},

'f_properties': {
    '$_vmat_unlit':     ('F_UNLIT',                 '1', None),
    '$_vmat_lit':       ('F_LIT',                   '1', None),
    '$_vmat_samplightm':('F_SAMPLE_LIGHTMAP',       '1', None),
    '$_vmat_blendmode': ('F_BLEND_MODE',            '0', None),

    '$translucent':     ('F_TRANSLUCENT',           '1', None), # "F_BLEND_MODE 0" for shader.vr_projected_decals
    '$alphatest':       ('F_ALPHA_TEST',            '1', None),
    '$envmap':          ('F_SPECULAR',              '1', None), # in "environment maps/metal" | "env_cubemap" F_SPECULAR_CUBE_MAP 1 // In-game Cube Map
    '$selfillum':       ('F_SELF_ILLUM',            '1', None),
    '$additive':        ('F_ADDITIVE_BLEND',        '1', None),
    '$ignorez':         ('F_DISABLE_Z_BUFFERING',   '1', None),
    '$nocull':          ('F_RENDER_BACKFACES',      '1', None), # F_NO_CULLING 1
    '$decal':           ('F_OVERLAY',               '1', None),
    '$flow_debug':      ('F_FLOW_DEBUG',            '0', None),
    '$detailblendmode': ('F_DETAIL_TEXTURE',        '1', [mapped_val, {'0':'1', '1':'2', '12':'0'} ]), # https://developer.valvesoftware.com/wiki/$detail#Parameters_and_Effects
    '$decalblendmode':  ('F_DETAIL_TEXTURE',        '1', [mapped_val, {'0':'1', '1':'2', '12':'0'} ]), # materialsystem\stdshaders\BaseVSShader.h#L26
    '$sequence_blend_mode': ('F_FAST_SEQUENCE_BLEND_MODE', '1', [mapped_val, {'0':'1', '1':'2', '2':'3'}]),

    '$selfillum_envmapmask_alpha': ('F_SELF_ILLUM', '1', None),

    #'$phong':           ('F_PHONG',                 '1'),
    #'$vertexcolor:      ('F_VERTEX_COLOR',          '1'),
},

'textures': {
    # for the individual faces; the sky material is handled separately
    '$hdrcompressedtexture':('TextureColor',    '_color', [formatNewTexturePath], ''), # compress
    '$hdrbasetexture':      ('TextureColor',    '_color', [formatNewTexturePath], ''), # nocompress

    ## Top / Main layer
    '$basetexture':     ('TextureColor',        '_color',   [formatNewTexturePath],     '' ),
    '$painttexture':    ('TextureColor',        '_color',   [formatNewTexturePath],     '' ),
    '$material':        ('TextureColor',        '_color',   [formatNewTexturePath],     '' ),

    '$normalmap':       ('TextureNormal',       '_normal',  [formatNewTexturePath],     '' ), # $bumpmap

    ## Layer blend mask
    '$blendmodulatetexture':\
                        ('TextureMask',             '_mask',   [createMask, 'G', False], 'F_BLEND 1') if NEW_SH else \
                        ('TextureLayer1RevealMask', '_blend',  [createMask, 'G', False], 'F_BLEND 1'),
    ## Layer 1
    '$basetexture2':    ('TextureColorB' if NEW_SH else 'TextureLayer1Color',  '_color',  [formatNewTexturePath], '' ),
    '$texture2':        ('TextureColorB' if NEW_SH else 'TextureLayer1Color',   '_color',  [formatNewTexturePath], '' ), # UnlitTwoTexture
    '$bumpmap2':        ('TextureNormalB' if NEW_SH else 'TextureLayer1Normal', '_normal', [formatNewTexturePath], '' if NEW_SH else 'F_BLEND_NORMALS 1' ),

    ## Layer 2-3
    '$basetexture3':    ('TextureLayer2Color',  '_color',  [formatNewTexturePath],     ''),
    '$basetexture4':    ('TextureLayer3Color',  '_color',  [formatNewTexturePath],     ''),

    '$normalmap2':      ('TextureNormal2',      '_normal', [formatNewTexturePath],     'F_SECONDARY_NORMAL 1'), # used with refract shader
    '$flowmap':         ('TextureFlow',         '',        [formatNewTexturePath],     'F_FLOW_NORMALS 1\n\tF_FLOW_DEBUG 1'),
    '$flow_noise_texture':\
                        ('TextureNoise',        '_noise',  [formatNewTexturePath],     'F_FLOW_NORMALS 1\n\tF_FLOW_DEBUG 2'),
    '$detail':          ('TextureDetail',       '_detail', [formatNewTexturePath],     'F_DETAIL_TEXTURE 1\n'), # $detail2
    '$decaltexture':    ('TextureDetail',       '_detail', [formatNewTexturePath],     'F_DETAIL_TEXTURE 1\n\tF_SECONDARY_UV 1\n\tg_bUseSecondaryUvForDetailTexture "1"'),

    '$selfillummask':   ('TextureSelfIllumMask','_selfillummask', [formatNewTexturePath],  ''),
    '$tintmasktexture': ('TextureTintMask',     '_mask',   [createMask, 'G', False],   'F_TINT_MASK 1'), #('TextureTintTexture',)
    '$_vmat_metalmask': ('TextureMetalness',    '_metal',  [formatNewTexturePath],     'F_METALNESS_TEXTURE 1'), # F_SPECULAR too
    '$_vmat_transmask': ('TextureTranslucency', '_trans',  [formatNewTexturePath],     ''),

    # only the G channel ## $ambientoccltexture': '$ambientocclusiontexture':
    '$ao':          ('TextureAmbientOcclusion', '_ao',     [createMask, 'G', False],    'F_AMBIENT_OCCLUSION_TEXTURE 1'), # g_flAmbientOcclusionDirectSpecular "1.000"
    '$aotexture':   ('TextureAmbientOcclusion', '_ao',     [createMask, 'G', False],    'F_AMBIENT_OCCLUSION_TEXTURE 1'), # g_flAmbientOcclusionDirectSpecular "1.000"

    #'$phongexponent2' $phongmaskcontrastbrightness2, $phongbasetint2, $phongamount2

    # Next script should take care of these, unless BASIC_PBR
    '$envmapmask':  ('$envmapmask',         '_env_mask',   [formatNewTexturePath], '') if not BASIC_PBR else \
                    ('TextureRoughness',    '_rough',      [formatNewTexturePath], '') if not LEGACY_SHADER else \
                    ('TextureGlossiness',   '_gloss',      [formatNewTexturePath], ''),

    '$phongmask':   ('$phongmask',          '_phong_mask', [formatNewTexturePath], '') if not BASIC_PBR else \
                    ('TextureRoughness',    '_rough',      [formatNewTexturePath], '') if not LEGACY_SHADER else \
                    ('TextureGlossiness',   '_gloss',      [formatNewTexturePath], ''),
},

'transform': {
    '$basetexturetransform':    ('g_vTex'), # g_vTexCoordScale "[1.000 1.000]"g_vTexCoordOffset "[0.000 0.000]"
    '$detailtexturetransform':  ('g_vDetailTex'), # g_flDetailTexCoordRotation g_vDetailTexCoordOffset g_vDetailTexCoordScale g_vDetailTexCoordXform
    '$bumptransform':           ('g_vNormalTex'),
    #'$bumptransform2':         (''),
    #'$basetexturetransform2':  (''),   #
    #'$texture2transform':      (''),   #
    #'$blendmasktransform':     (''),   #
    #'$envmapmasktransform':    (''),   #
    #'$envmapmasktransform2':   (''),   #

},

'settings': {

    '$detailblendfactor':   ('g_flDetailBlendFactor',   '1.000',                    [float_val],       ''), #'$detailblendfactor2', '$detailblendfactor3'
    '$detailscale':         ('g_vDetailTexCoordScale',  '[1.000 1.000]',            [fixVector, False], ''),

    '$color':               ('g_vColorTint',        '[1.000 1.000 1.000 0.000]',    [fixVector, True],  ''),
    '$color2':              ('g_vColorTint',        '[1.000 1.000 1.000 0.000]',    [fixVector, True],  ''),
    '$selfillumtint':       ('g_vSelfIllumTint',    '[1.000 1.000 1.000 0.000]',    [fixVector, True],  ''),

    '$alpha':               ('g_flOpacityScale',        '1.000',    [float_val], ''),
    '$alphatestreference':  ('g_flAlphaTestReference',  '0.500',    [float_val], 'g_flAntiAliasedEdgeStrength "1.000"'),
    '$blendtintcoloroverbase':('g_flModelTintAmount',   '1.000',    [float_val], ''), # $layertint1
    '$selfillumscale':      ('g_flSelfIllumScale',      '1.000',    [float_val], ''),
    '$phongboost':          ('g_flPhongBoost',          '1.000',    [float_val], ''),
    '$metalness':           ('g_flMetalness',           '0.000',    [float_val], ''),
    '$_metalness2':         ('g_flMetalnessB',          '0.000',    [float_val], ''),
    '$refractamount':       ('g_flRefractScale',        '0.200',    [float_val], ''),
    '$flow_worlduvscale':   ('g_flWorldUvScale',        '1.000',    [float_val], ''),
    '$flow_noise_scale':    ('g_flNoiseUvScale',        '0.010',    [float_val], ''), # g_flNoiseStrength?
    '$flow_bumpstrength':   ('g_flnormalmap_listtrength',   '1.000',    [float_val], ''),

    '$nofog':   ('g_bFogEnabled',       '0',        [int_val, True], ''),
    "$notint":  ('g_flModelTintAmount', '1.000',    [int_val, True], ''),

    # rimlight
    #'$warpindex':           ('g_flDiffuseWrap',         '1.000',    [float_var], ''), # requires F_DIFFUSE_WRAP 1. "?
    #'$diffuseexp':          ('g_flDiffuseExponent',     '2.000',    [float_var], 'g_vDiffuseWrapColor "[1.000000 1.000000 1.000000 0.000000]'),

    # shader.blend and shader.vr_standard(SteamVR) -- $NEWLAYERBLENDING
    '$blendsoftness':       ('g_flLayer1BlendSoftness', '0.500',    [float_val], ''),
    '$layerborderstrenth':  ('g_flLayer1BorderStrength','0.500',    [float_val], ''),
    '$layerborderoffset':   ('g_flLayer1BorderOffset',  '0.000',    [float_val], ''),
    '$layerbordersoftness': ('g_flLayer1BorderSoftness','0.500',    [float_val], ''),
    '$layerbordertint':     ('g_vLayer1BorderColor',    '[1.000000 1.000000 1.000000 0.000000]', [fixVector, True], ''),
},

'channeled_masks': { # 1-X will extract the inverse of channel X; M_1-X to only invert on models
   #'$vmtKey':                      (extract_from,       extract_as,       channel to extract)
    '$normalmapalphaenvmapmask':    ('$normalmap',    '$envmapmask',      '1-A'),
    '$basealphaenvmapmask':         ('$basetexture',    '$envmapmask',      'M_1-A'),
    '$envmapmaskintintmasktexture': ('$tintmasktexture','$envmapmask',      '1-R'),
    '$basemapalphaphongmask':       ('$basetexture',    '$phongmask',       '1-A'),
    '$basealphaphongmask':          ('$basetexture',    '$phongmask',       '1-A'),
    '$normalmapalphaphongmask':     ('$normalmap',    '$phongmask',       '1-A'),
    '$bumpmapalphaphongmask':       ('$normalmap',    '$phongmask',       '1-A'),
    '$basemapluminancephongmask':   ('$basetexture',    '$phongmask',       'L'),

    '$blendtintbybasealpha':        ('$basetexture',    '$tintmasktexture', 'A'),
    '$selfillum_envmapmask_alpha':  ('$envmapmask',     '$selfillummask',   'A'),

    '$translucent':                 ('$basetexture',    '$_vmat_transmask', 'A'),
    '$alphatest':                   ('$basetexture',    '$_vmat_transmask', 'A'),
    '$selfillum':                   ('$basetexture',    '$selfillummask',   'A'),
    #'$phong':                       (normalmap_list,    '$phongmask',       'A'),

    #'$masks1': ('self', ('$rimmask', '$phongalbedomask', '$_vmat_metalmask', '$warpindex'), 'RGBA')
},

'SystemAttributes': {
    '$surfaceprop':     ('PhysicsSurfaceProperties', 'default', [fixSurfaceProp], '')
},
# no direct replacement, etc
'others2': {
    # ssbump dose not work?
    #'$ssbump':               ('TextureBentNormal',    '_bentnormal.tga', 'F_ENABLE_NORMAL_SELF_SHADOW 1\n\tF_USE_BENT_NORMALS 1\n'),

    #'$iris': ('',    '',     ''), # paste iris into basetexture

    # fRimMask = vMasks1Params.r;
    # fPhongAlbedoMask = vMasks1Params.g;
    # fMetalnessMask = vMasks1Params.b;
    # fWarpIndex = vMasks1Params.a;
    # https://developer.valvesoftware.com/wiki/Character_(shader)
    #'$maskstexture':    ('',    '',     ''),
    #'$masks':   ('',    '',     ''),
    #'$masks1':  ('',    '',     ''),
    #'$masks2':  ('',    '',     ''),
    #'$phong':   ('',    '',     ''),

    # $selfillumfresnelminmaxexp "[1.1 1.7 1.9]"
    #'$selfillum_envmapmask_alpha':     ('',    '',     ''),

    # TODO: the fake source next to outside area on de_nuke;
    # x = texturescrollrate * cos(texturescrollangle) ?????
    # y = texturescrollrate * sin(texturescrollangle) ?????
    #'TextureScroll':    (('texturescrollvar', 'texturescrollrate', 'texturescrollangle'), 'g_vTexCoordScrollSpeed', '[0.000 0.000]')
}
}

def convertVmtToVmat(vmtKeyValues):

    vmatContent = ''
    lines_SysAtributes = []

    # for each key-value in the vmt file ->
    for vmtKey, vmtVal in vmtKeyValues.items():

        outKey = outVal = outAddLines = ''

        vmtKey = vmtKey.lower()
        vmtVal = vmtVal.strip().strip('"' + "'").strip(' \n\t"')

        # search through the dictionary above to find the appropriate replacement.
        for keyType in list(vmt_to_vmat):

            vmatTranslation = vmt_to_vmat[keyType].get(vmtKey)

            if not vmatTranslation:
                continue

            vmatReplacement = None
            vmatDefaultVal = None
            vmatTranslFunc = None
            outAddLines = None

            try:
                vmatReplacement = vmatTranslation [ VMAT_REPLACEMENT  ]
                vmatDefaultVal  = vmatTranslation [ VMAT_DEFAULTVAL   ]
                vmatTranslFunc  = vmatTranslation [ VMAT_TRANSLFUNC   ]
                outAddLines     = vmatTranslation [ VMAT_EXTRALINES   ]
            except: pass

            if ( vmatReplacement and vmatDefaultVal ):

                outKey = vmatReplacement

                if (keyType == 'textures'):
                    outVal = default(vmatDefaultVal)
                else:
                    outVal = vmatDefaultVal

                if vmtVal:
                    outVal = vmtVal

                if vmatTranslFunc:
                    if not hasattr(vmatTranslFunc[0], '__call__'):
                        outAddLines = vmatTranslation [ VMAT_TRANSLFUNC   ]
                    else:
                        func_ = vmatTranslFunc[0]
                        args_ = []
                        args_.insert(0, vmtVal)
                        args_.extend(vmatTranslFunc[1:])

                        if func_ in (formatNewTexturePath, createMask):
                            #print("Adding arg to", func_, end = ' ->')
                            args_.insert(1, vmatDefaultVal)
                            #print(vmatTranslFunc)

                        msg(vmtKey, "->\t" + func_.__name__, args_, end=" -> ")
                        if (returnValue:= func_(*args_)):
                            outVal = returnValue
                        #args_.clear()
                        msg(outKey, returnValue)

            # no equivalent key-value for this key, only exists
            # add comment or ignore completely
            elif (outAddLines):
                if keyType in ('transform'): # exceptions
                    pass
                else:
                    vmatContent += outAddLines
                    continue
            else:
                continue

            # F_RENDER_BACKFACES 1 etc
            if keyType == 'f_properties':
                if vmatShader == shader.vr_projected_decals and vmtKey == "$translucent":
                    outKey, outVal = "F_BLEND_MODE", "0"

                if outKey in vmatContent: ## Replace keyval if already added
                    msg(outKey + ' is already in.')
                    vmatContent = re.sub(r'%s.+' % outKey, outKey + ' ' + outVal, vmatContent)
                else:
                    vmatContent = f_KeyVal.format(outKey, outVal) + vmatContent # add these keys to the top
                continue ### Skip default content write

            elif(keyType == 'textures'):

                # Layer A
                if vmtKey in ('$basetexture', '$hdrbasetexture', '$hdrcompressedtexture', '$normalmap'):
                    outKey = vmat_layered_param(vmatReplacement)

                elif vmtKey in ('$normalmap', '$bumpmap2', '$normalmap2'):

                    if vmtVal == 'dev/flat_normal': outVal = default(vmatDefaultVal)

                    outVal = Path(outVal) # not wise
                    #if not str(VMAT_DEFAULT_PATH) in outVal:
                    if not outVal.is_relative_to(VMAT_DEFAULT_PATH):
                        flipNormalMap(outVal)

            elif(keyType == 'transform'): # here one key can add multiple keys
                if not vmatReplacement:
                    continue

                matrixList = listMatrix(vmtVal)
                msg( matrixList )
                # doesnt seem like there is rotation
                #if(matrixList[MATRIX_ROTATE] != '0.000'):
                #    if(matrixList[MATRIX_ROTATIONCENTER] != '[0.500 0.500]')

                # scale 5 5 -> g_vTexCoordScale "[5.000 5.000]"

                if matrixList[MATRIX_ROTATE]:
                    msg("HERE IT IS:", int(float(matrixList[MATRIX_ROTATE])))

                if(matrixList[MATRIX_SCALE] and matrixList[MATRIX_SCALE] != [1.000, 1.000]):
                    outKey = vmatReplacement + 'CoordScale'
                    outVal = fixVector(matrixList[MATRIX_SCALE], False)
                    vmatContent += f_KeyValQuoted.format(outKey, outVal)

                # translate .5 2 -> g_vTexCoordOffset "[0.500 2.000]"
                if(matrixList[MATRIX_TRANSLATE] and matrixList[MATRIX_TRANSLATE] != [0.000, 0.000]):
                    outKey = vmatReplacement + 'CoordOffset'
                    outVal = fixVector(matrixList[MATRIX_TRANSLATE], False)
                    vmatContent += f_KeyValQuoted.format(outKey, outVal)

                continue ## Skip default content write

            # should use reverse of the basetexture alpha channel as a self iluminating mask
            # ... why reversE???

            elif(keyType == 'channeled_masks'):
                outVmtTexture = vmt_to_vmat['channeled_masks'][vmtKey][1] # extract as

                if not vmt_to_vmat['textures'].get(outVmtTexture): break

                sourceTexture   = vmt_to_vmat['channeled_masks'][vmtKey][0] # extract from
                sourceChannel   = vmt_to_vmat['channeled_masks'][vmtKey][2] # channel to extract

                outKey          = vmt_to_vmat['textures'][outVmtTexture][VMAT_REPLACEMENT]
                outAddLines     = vmt_to_vmat['textures'][outVmtTexture][VMAT_EXTRALINES]
                sourceSubString = vmt_to_vmat['textures'][outVmtTexture][VMAT_DEFAULTVAL]

                if vmtKeyValues.get(outVmtTexture):
                    print("~", vmtKey, "conflicts with", outVmtTexture + ". Aborting mask extration (using original).")
                    continue

                shouldInvert    = False
                if ('1-' in sourceChannel):
                    if 'M_1-' in sourceChannel:
                        if vmtKeyValues.get('$model'):
                            shouldInvert = True
                    else:
                        shouldInvert = True

                    sourceChannel = sourceChannel.strip('M_1-')

                # invert for brushes; if it's a model, keep the intact one ^
                # both versions are provided just in case for 'non models'
                #if not str(vmtKeyValues.get('$model')).strip('"') != '0': invert

                outVal =  createMask(sourceTexture, sourceSubString, sourceChannel, shouldInvert)

            elif keyType == 'SystemAttributes':
                lines_SysAtributes.append(f_KeyValQuoted.format(outKey, outVal))
                continue

            if(outAddLines): outAddLines = '\n\t' + outAddLines + '\n'

            ##################################################################
            ###                 Default content write                      ###
            vmatContent += outAddLines + f_KeyValQuoted.format(outKey, outVal)
            ##################################################################

            #msg( vmtKey, '"'+vmtVal+'"', "->", outKey, '"'+outVal.replace('\t', '').replace('\n', '')+'"', outAddLines.replace('\t', '').replace('\n', ''))

            # dont break some keys have more than 1 translation (e.g. $selfillum)

    if USE_SUGESTED_DEFAULT_ROUGHNESS:
        if not vmatShader == shader.vr_simple_2way_blend:
            if "TextureRoughness" not in vmatContent:
                 vmatContent += f_KeyValQuoted.format("TextureRoughness", "materials/default/default_rough_s1import.tga")
        else: # stupid
            if "TextureRoughnessA" not in vmatContent:
                vmatContent += f_KeyValQuoted.format("TextureRoughnessA", "materials/default/default_rough_s1import.tga")
            if "TextureRoughnessB" not in vmatContent:
                vmatContent += f_KeyValQuoted.format("TextureRoughnessB", "materials/default/default_rough_s1import.tga")

    if lines_SysAtributes:
        vmatContent += '\n\tSystemAttributes\n\t{\n'
        for line in lines_SysAtributes:
            vmatContent += '\t' + line
        vmatContent += '\t}\n'

    return vmatContent

def convertSpecials(vmtKeyValues):

    if bumpmap := vmtKeyValues.get("$bumpmap"):
        del vmtKeyValues["$bumpmap"]
        vmtKeyValues["$normalmap"] = bumpmap

    # fix phongmask logic
    if vmtKeyValues.get("$phong") == '1' and not vmtKeyValues.get("$phongmask"):
        # sniper scope

        bHasPhongMask = False
        for key, val in vmt_to_vmat['channeled_masks'].items():
            if val[1] == '$phongmask' and vmtKeyValues.get(key):
                bHasPhongMask = True
                break
        if fs.LocalDir(vmtFilePath).is_relative_to(materials/Path("models/weapons/shared/scope")):
            bHasPhongMask = False
        if not bHasPhongMask: # normal map Alpha acts as a phong mask by default
            vmtKeyValues['$normalmapalphaphongmask'] = '1'

    # fix additive logic - Source 2 needs Translucency to be enabled for additive to work
    if vmtKeyValues.get("$additive") == '1' and not vmtKeyValues.get("$translucent"):
        vmtKeyValues['$translucent'] = '1'

    # fix unlit shader ## what about generic?
    if (matType == 'unlitgeneric') and (vmatShader == shader.vr_complex):
        vmtKeyValues["$_vmat_unlit"] = '1'

    # fix mod2x logic for shader.vr_projected_decals
    if matType == 'decalmodulate':
        vmtKeyValues['$_vmat_blendmode'] = '1'

    # fix lit logic for shader.vr_projected_decals
    if matType in ('lightmappedgeneric', 'vertexlitgeneric'):
        if vmatShader == shader.vr_static_overlay: vmtKeyValues["$_vmat_lit"] = '1'
        elif vmatShader == shader.vr_projected_decals: vmtKeyValues["$_vmat_samplightm"] = '1' # F_SAMPLE_LIGHTMAP 1 ?

    # csgo viewmodels
    viewmodels = Path("models/weapons/v_models")
    if fs.LocalDir(vmtFilePath).is_relative_to(materials/viewmodels):
        # use _ao texture in \weapons\customization
        weaponName = vmtFilePath.parent.name
        if (vmtFilePath.stem == weaponName or vmtFilePath.stem == weaponName.split('_')[-1]):
            customization = viewmodels.parent / Path("customization")
            aoPath = fs.Output(materials/customization/weaponName/ Path(str(weaponName) + "_ao"+ TEXTURE_FILEEXT))
            if aoPath.exists():
                aoNewPath = fs.Output(materials/viewmodels/weaponName/ Path(aoPath.name))
                try:
                    if not aoNewPath.exists() and aoNewPath.parent.exists():
                        copyfile(aoPath, aoNewPath)
                        print("+ Succesfully moved AO texture for weapon material:", weaponName)
                    vmtKeyValues["$aotexture"] = str(fs.LocalDir_Legacy(fs.LocalDir(aoNewPath)))
                    print("+ Using ao:", aoPath.name)
                except FileNotFoundError: pass

        #vmtKeyValues.setdefault("$envmap", "0") # specular looks ugly on viewmodels so disable it. does not affect scope lens
        if vmtKeyValues.get("$envmap"): del vmtKeyValues["$envmap"]
        #"$envmap"                 "environment maps/metal_generic_001" --> metalness
        #"$envmaplightscale"       "1"
        #"$envmaplightscaleminmax" "[0 .3]"     metalness modifier?



vmtFileList_extra = []
vmtFileList = fs.collect_files(IN_EXT, OUT_EXT, existing=OVERWRITE_VMAT, outNameRule = OutName)
total, import_total, import_invalid = 0, 0, 0
failureList = []

#######################################################################################
# Main function, loop through every .vmt
##
for vmtFilePath in sh.combine_files(vmtFileList, vmtFileList_extra):
    total += 1
    #if total > 1000: break
    matType = ''
    vmtKeyValues = {}
    vmatFilePath = ''
    vmatShader = ''
    validMaterial = False
    validInclude = False
    skipNextLine = False

    with open(vmtFilePath, 'r') as vmtFile:
        row = 0
        for line in vmtFile:

            line = line.strip().split("//", 1)[0].lower()

            if not line or line.startswith('/'):
                continue

            if row < 1:
                matType = re.sub(r'[^A-Za-z0-9_-]', '', line)
                if any(wd in matType for wd in materialTypes):
                    validMaterial = True

            if skipNextLine:
                if "]" in line or "}" in line:
                    skipNextLine = False
                continue
            else:
                parseKeyValue(line, vmtKeyValues)

            if any(line.lower().endswith(wd) for wd in ignoreList):
                msg("Skipping {} block:", line)
                skipNextLine = True

            if "}" in line and row != 0:
                break

            row += 1

    if matType == 'patch':
        includePath = vmtKeyValues.get("include")
        if includePath:
            #includePath = includePath.replace('"', '').replace("'", '').strip()
            if includePath == r'materials\models\weapons\customization\paints\master.vmt':
                continue

            print("+ Retrieving material info from:", includePath, end='')
            try:
                with open(fs.Input(includePath), 'r') as includeFile:
                    patchKeyValues = vmtKeyValues.copy()
                    vmtKeyValues.clear()

                    for line in includeFile.readlines():
                        line = line.lower().strip()
                        if not validInclude and any(wd in line for wd in materialTypes):
                            print(' ... Done!!')
                            matType = re.sub(r'[^A-Za-z0-9_-]', '', line)
                            validInclude = True

                        if validInclude:
                            parseKeyValue(line, vmtKeyValues)

                    vmtKeyValues.update(patchKeyValues)

            except FileNotFoundError:
                print(" ...Did not find")
                failureList.append(includePath + " -- Cannot find include.")
                continue

            if not validInclude:
                print(" ... Include has unsupported shader.")
                # matType =
                #continue
        else:
            print("~ WARNING: No include was provided on material with type 'Patch'. Is it a weapon skin?")

    vmatShader = chooseShader()

    if fs.LocalDir(vmtFilePath).is_relative_to(materials/skybox):
        vmtSkyboxFile = vmtFilePath.with_suffix("").name
        skyName, skyFace = [vmtSkyboxFile[:-2], vmtSkyboxFile[-2:]]
        if skyFace in skyboxFaces:
            collectSkyboxFaces(vmtKeyValues, skyName, skyFace)
            vmatShader = shader.vr_complex
            validMaterial = False
            msg("MATERIAL:", matType)

    if validMaterial:
        vmatFilePath = OutName(vmtFilePath)

        if not vmatFilePath.parent.exists(): fs.MakeDir(vmatFilePath.parent)

        if not fs.ShouldOverwrite(vmatFilePath, OVERWRITE_VMAT):
            print(f'+ File already exists. Skipping! {vmatFilePath}')
            continue

        with open(vmatFilePath, 'w') as vmatFile:
            vmatFile.write('// Converted with vmt_to_vmat.py\n')
            vmatFile.write('// From: ' + str(vmtFilePath) + '\n\n')
            msg(matType + " => " + vmatShader.name, "\n", vmtKeyValues)
            vmatFile.write('Layer0\n{\n\tshader "' + vmatShader.name + '.vfx"\n\n')

            convertSpecials(vmtKeyValues)

            vmatFile.write(convertVmtToVmat(vmtKeyValues)) ###############################

            vmatFile.write('}\n')

            import_total += 1

        if DEBUG: print("+ Saved", vmatFilePath)
        else: print("+ Saved", fs.LocalDir(vmatFilePath))

    else: import_invalid += 1


    if not matType:
        if DEBUG: debugContent += "Warning" + str(vmtFilePath) + '\n'

print("\nDone with the materials...\nNow onto our sky cubemaps...")

import numpy as np

with open(fs.Input("skyboxfaces.json"), 'w+') as fp:
    try: json_vmtSkybox = json.load(fp)
    except json.decoder.JSONDecodeError:
        json_vmtSkybox = {}

    vmtSkybox.update(json_vmtSkybox)

    json.dump(vmtSkybox, fp, sort_keys=True, indent=4)

########################################################################
# Build sky cubemap from sky faces
# (blue_sky_up.tga, blue_sky_ft.tga, ...) -> blue_sky_cube.tga
# https://developer.valvesoftware.com/wiki/File:Skybox_Template.jpg
# https://learnopengl.com/img/advanced/cubemaps_skybox.png
for skyName in vmtSkybox:

    # TODO: faces_to_cubemap.py

    hdrType = vmtSkybox[skyName].get("_hdrtype")
    maxFace_w = maxFace_h = vmtSkybox[skyName].get("_maxres")
    if not maxFace_w: continue

    cube_w = 4 * maxFace_w
    cube_h = 3 * maxFace_h

    facePath = ''
    # skyName = skyName.rstrip('_')
    img_ext = '.pfm' if hdrType else TEXTURE_FILEEXT
    vmat_path =         fs.Output( materials/skybox/Path(skyName).with_suffix(OUT_EXT) )
    sky_cubemap_path =  fs.Output( materials/skybox/Path(skyName + '_cube').with_suffix(img_ext) )

    if not fs.ShouldOverwrite(sky_cubemap_path, OVERWRITE_SKYBOX):
        continue

    # hdr uncompressed: join the pfms same way as tgas
    if (hdrType == 'uncompressed'):
        # TODO: ...
        #emptyData = [0] * (cube_w * cube_h)
        #emptyArray = np.array(emptyData, dtype='float32').reshape((maxFace_h, maxFace_w, 3)
        #for face in skyboxFaces:
        #    if not (facePath := os.path.join("materials\\skybox", vmtSkybox[skyName][face].get('path'))): continue
        #    floatData, scale, _ = PFM.read_pfm(fs.Output(facePath))

        #for i in range(12):
        #    pass
        #    # paste each

        continue

    imgMode = 'RGBA' if (hdrType == 'compressed') else 'RGB'
    SkyCubemapImage = Image.new(imgMode, (cube_w, cube_h), color = (0, 0, 0))

    for face in skyboxFaces:
        if not (facePath := vmtSkybox[skyName][face].get('path')): continue
        facePath = fs.Output(materials/skybox/Path(facePath))
        faceScale = vmtSkybox[skyName][face].get('scale')
        faceRotate = int(vmtSkybox[skyName][face].get('rotate') or 0)
        if not (faceImage := Image.open(facePath).convert(imgMode)): continue

        if face == 'up':
            pasteCoord = ( cube_w - (maxFace_w * 3) , cube_h - (maxFace_h * 3) ) # (1, 2)
            faceRotate += 90
        elif face == 'ft': pasteCoord = ( cube_w - (maxFace_w * 1) , cube_h - (maxFace_h * 2) ) # (2, 3) -> (2, 4) #2)
        elif face == 'lf': pasteCoord = ( cube_w - (maxFace_w * 4) , cube_h - (maxFace_h * 2) ) # (2, 4) -> (2, 1) #1)
        elif face == 'bk': pasteCoord = ( cube_w - (maxFace_w * 3) , cube_h - (maxFace_h * 2) ) # (2, 1) -> (2, 2) #4)
        elif face == 'rt': pasteCoord = ( cube_w - (maxFace_w * 2) , cube_h - (maxFace_h * 2) ) # (2, 2) -> (2, 3) #3)
        elif face == 'dn':
            pasteCoord = ( cube_w - (maxFace_w * 3) , cube_h - (maxFace_h * 1) ) # (3, 2)
            faceRotate += 90

        # scale to fit on the y axis
        if faceImage.width != maxFace_w:
            faceImage = faceImage.resize((maxFace_w, round(faceImage.height * maxFace_w/faceImage.width)), Image.BICUBIC)

        if(faceRotate):
            faceImage = faceImage.rotate(faceRotate)

        SkyCubemapImage.paste(faceImage, pasteCoord)
        faceImage.close()
        # TODO: move faces in /legacy_faces/ 
        # move(facePath, facePath.parent / Path("legacy_faces") / facePath.name )

    # for hdr compressed: uncompress the whole tga map we just created and paste to pfm
    if (hdrType == 'compressed'):
        compressedPixels = SkyCubemapImage.load()
        hdrImageData = list()
        #hdrImageData = [0] * (cube_w * cube_h * 3)
        for x in range(cube_w):
            for y in range(cube_h):

                R, G, B, A = compressedPixels[x,y] # image.getpixel( (x,y) )
                # could this optimization worrk?
                #chanDataIndex = 3 * x * y
                #hdrImageData[chanDataIndex    ] = (R * (A * 16)) / 262144
                #hdrImageData[chanDataIndex + 1] = (G * (A * 16)) / 262144
                #hdrImageData[chanDataIndex + 2] = (B * (A * 16)) / 262144
                hdrImageData.append(float( (R * (A * 16)) / 262144 ))
                hdrImageData.append(float( (G * (A * 16)) / 262144 ))
                hdrImageData.append(float( (B * (A * 16)) / 262144 ))

        SkyCubemapImage.close()

        # questionable 90deg rotations
        HDRImageDataArray = np.rot90(np.array(hdrImageData, dtype='float32').reshape((cube_w, cube_h, 3)))
        PFM.write_pfm(sky_cubemap_path, HDRImageDataArray)

    else:
        SkyCubemapImage.save(sky_cubemap_path)

    if sky_cubemap_path.exists():

        if fs.ShouldOverwrite(vmat_path):
            with open(vmat_path, 'w') as vmatFile:
                vmatFile.write('// Sky material and cube map created by vmt_to_vmat.py\n\n')
                vmatFile.write('Layer0\n{\n\tshader "sky.vfx"\n\n')
                vmatFile.write(f'\tSkyTexture\t"{fs.LocalDir(sky_cubemap_path)}"\n\n}}')

        print('+ Successfuly created material and sky cubemap:', os.path.basename(sky_cubemap_path))


if failureList: print("\n\t<<<< THESE MATERIALS HAVE ERRORS >>>>")
for failure in failureList:        print(failure)
if failureList: print("\t^^^^ THESE MATERIALS HAVE ERRORS ^^^^")

try:

    print(f"\nTotal imports:\t{import_total} / {total}\t| " + "{:.2f}".format((import_total/total) * 100) + f" % Success rate")
    print(f"Total skipped:\t{import_invalid} / {total}\t| " + "{:.2f}".format((import_invalid/total) * 100) + f" % Skip rate")
    print(f"Total errors :\t{len(failureList)} / {total}\t| " + "{:.2f}".format((len(failureList)/total) * 100) + f" % Error rate")

except: pass
# csgo -> 206 / 14792 | 1.39 % Error rate -- 4637 / 14792 | 31.35 % Skip rate
# l4d2 -> 504 / 3675 | 13.71 % Error rate -- 374 / 3675 | 10.18 % Skip rate
print("\nFinished! Your materials are now ready.")
