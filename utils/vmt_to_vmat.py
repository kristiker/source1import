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

# Usage Instructions:
# run the script directly
# or `python vmt_to_vmat.py input_path`

#  Translation table is found at vmt_to_vmat below

import re, sys, os
from pathlib import Path # TBD
from shutil import copyfile
from difflib import get_close_matches
from enum import Enum
import pyutils.PFM as PFM
from PIL import Image, ImageOps
#from s2_helpers import *

# generic, blend instead of vr_complex, vr_2wayblend etc...
# blend doesn't seem to work though. why...
LEGACY_SHADER = False
NEW_SH = not LEGACY_SHADER

# File format of the textures. Needs to be lowercase
# source 2 supports all kinds: tga jpeg png gif psd exr tiff pfm...
# Just make sure the name of the file is the same as that of the .vtf, and that the path in the .vmt matches.
TEXTURE_FILEEXT = '.tga'

# Path to content root, before /materials/
PATH_TO_CONTENT_ROOT = r""
#PATH_TO_NEW_CONTENT_ROOT = r""

# Set this to True if you wish to overwrite your old vmat files
OVERWRITE_VMAT = False
OVERWRITE_SKYBOX = False

# False to let the engine handle the inverting of the normalmap.
NORMALMAP_G_INVERT_DIRECTLY = False

BASIC_PBR = True
SURFACEPROP_AS_IS = False
SKYBOX_CREATE_LDR_FALLBACK = True

DEBUG = False
def msg(*args, **kwargs):
    if DEBUG:
        print("@ DBG:", *args, **kwargs)

Late_Calls = []
failures = []

fileList = []

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
        "vr_static_overlay",
        "vr_power_cables",
        "tools_wireframe", # vr_tools_wireframe
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

def chooseShader(matType, vmtKeyValues, fileName):

    sh = {x:0 for x in shader}

    # not recognized, give empty shader
    if matType not in materialTypes:
        if DEBUG:
            if (ffff := "unmatched shader " + matType) not in failures: failures.append(ffff)
        return shader.vr_black_unlit

    if LEGACY_SHADER:   sh[shader.generic] += 1
    else:               sh[materialTypes[matType]] += 1

    if matType == "worldvertextransition":
        if vmtKeyValues.get('$basetexture2'): sh[shader.vr_simple_2way_blend] += 10

    elif matType == "lightmappedgeneric":
        if vmtKeyValues.get('$newlayerblending') == '1': sh[shader.vr_simple_2way_blend] += 10
        if vmtKeyValues.get('$decal') == '1': sh[shader.vr_static_overlay] += 10

    elif matType == "":
        pass

    return max(sh, key = sh.get)

ignoreList = [ "dx9", "dx8", "dx7", "dx6", "proxies"]

INPUT_FILE_EXT = ".vmt"
OUTPUT_FILE_EXT = ".vmat"

VMAT_DEFAULT_PATH = "materials/default/default"
f_KeyVal = '\t{}\t{}\n'
f_KeyValQuoted = '\t{}\t"{}"\n'
f_KeyQuotedValQuoted = '\t"{}"\t"{}"\n'

def ext(this, ext = TEXTURE_FILEEXT): return this + ext
def default(defaulttype): return VMAT_DEFAULT_PATH + defaulttype

print('\nSource 2 Material Conveter! By Rectus via Github.')
print('Initially forked by Alpyne, this version by caseytube.\n')
print('--------------------------------------------------------------------------------------------------------')

#currentDir = r"D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo"
currentDir =  os.path.dirname(os.path.realpath(__file__)) #os.getcwd()

if not PATH_TO_CONTENT_ROOT:
    if(len(sys.argv) >= 2):
        PATH_TO_CONTENT_ROOT = sys.argv[1]
    else:
        while not PATH_TO_CONTENT_ROOT:
            c = input('Type in the directory of the .vmt file(s) (enter to use current directory, q to quit).: ') or currentDir
            if not os.path.isdir(c) and not os.path.isfile(c):
                if c in ('q', 'quit', 'exit', 'close'): quit()
                print('Could not find directory.')
                continue
            PATH_TO_CONTENT_ROOT = c.lower().strip().strip('"')

# Useful for modname_imported
"""
if not PATH_TO_NEW_CONTENT_ROOT:
    if(len(sys.argv) >= 3):
        PATH_TO_NEW_CONTENT_ROOT = sys.argv[2]
    else:
        while not PATH_TO_NEW_CONTENT_ROOT:
            c = input('Type in the directory you wish to output the converted materials to (enter to use the same dir): ') or currentDir
            if not path.isdir(c):
                    if c in ('q', 'quit', 'exit', 'close'): quit()
                    print('Could not find directory.')
                    continue
                PATH_TO_NEW_CONTENT_ROOT = c.lower().strip().strip('"')
"""

def parseDir(dirName):
    fileCount = 0
    files = []
    for root, _, fileNames in os.walk(dirName):
        #if fileCount > 200: break
        for skipdir in ['console', 'correction', 'dev', 'debug', 'editor', 'tools', 'models\\editor' ]: # 'vgui',
            if ('materials\\' + skipdir) in root: fileNames.clear()

        for fileName in fileNames:
            if fileName.lower().endswith(INPUT_FILE_EXT): # : #
                fileCount += 1
                filePath = os.path.join(root,fileName)
                if len(files) % 17 == 0 or (len(files) == 0):
                    print(f"  Found {len(files)} %sfiles" % ("" if OVERWRITE_VMAT else f"/ {fileCount} "), end="\r")
                if not OVERWRITE_VMAT:
                    if os.path.exists(filePath.replace(INPUT_FILE_EXT, OUTPUT_FILE_EXT)): continue
                files.append(filePath)

    print(f"  Found {len(files)} %sfiles" % ("" if OVERWRITE_VMAT else f"/ {fileCount} "))
    return files

if os.path.isfile(PATH_TO_CONTENT_ROOT): # input is a single file
    if(PATH_TO_CONTENT_ROOT.lower().endswith(INPUT_FILE_EXT)):
        fileList.append(PATH_TO_CONTENT_ROOT)
        PATH_TO_CONTENT_ROOT = PATH_TO_CONTENT_ROOT.split("materials", 1)[0]
    else:
        print("~ Invalid file.")
else:
    folderPath = PATH_TO_CONTENT_ROOT
    if not 'materials' in PATH_TO_CONTENT_ROOT \
    and not PATH_TO_CONTENT_ROOT.endswith(INPUT_FILE_EXT) \
    and not PATH_TO_CONTENT_ROOT.rstrip('\\/').endswith('materials'):
        folderPath = os.path.abspath(os.path.join(PATH_TO_CONTENT_ROOT, 'materials'))
    if os.path.isdir(folderPath):
        print("\n-", folderPath.capitalize())
        print("+ Scanning for .vmt files. This may take a while...")
        fileList.extend(parseDir(folderPath))
    else: print("~ Could not find a /materials/ folder inside this dir.\n")

PATH_TO_CONTENT_ROOT = os.path.normpath(PATH_TO_CONTENT_ROOT) + '\\'
#PATH_TO_NEW_CONTENT_ROOT =  os.path.normpath(PATH_TO_NEW_CONTENT_ROOT) + '\\'

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
        print("~ WARNING: This key might not translate properly", key)
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


# "environment maps/metal_generic_002" -> "materials/environment maps/metal_generic_002.tga"
def fixVmtTextureDir(localPath, fileExt = TEXTURE_FILEEXT):
    if localPath.endswith(fileExt): fileExt = ''
    localPath = localPath.replace('.vtf', '') # remove any old extensions
    localPath = os.path.normpath('materials/' + localPath + fileExt)
    localPath = localPath.lower().replace('\\', '/') # Convert paths to use forward slashes.

    return localPath

# materials/texture_color.tga -> C:/Users/User/Desktop/stuff/materials/texture_color.tga
def formatFullDir(localPath):
    return os.path.abspath(os.path.join(PATH_TO_CONTENT_ROOT, localPath))

# inverse of formatFullDir()
def formatVmatDir(localPath):
    if not localPath: return None
    localPath = os.path.normpath(localPath)
    return localPath.replace(PATH_TO_CONTENT_ROOT, '')

def textureAddSubStr(str1, str2):
    if str1.endswith(str2):
        return str1
    #str1 += str2
    return (str1 + str2)


# Returns correct path
def formatNewTexturePath(vmtPath, textureType = TEXTURE_FILEEXT, noRename = False, forReal = True):
    # and Error loading resource file "materials/models/props/de_dust/hr_dust/dust_lights/street_lantern_03/street_lantern_03_color.vmat_c" (Error: ERROR_FILEOPEN)

    vmtPath = formatFullDir(fixVmtTextureDir(vmtPath, '')) + "." + textureType.split(".", 1)[1] or ''

    if not os.path.exists(vmtPath):
        return default(textureType)

    return formatVmatDir(vmtPath)

# -------------------------------
# Returns full texture path of given vmt Param, vmt Params, or vmt Path
# $basetexture              -> C:/addon_root/materials/path/to/texture_color.tga
# path/to/texture_color.tga -> C:/addon_root/materials/path/to/texture_color.tga
# -------------------------------
def getTexture(vmtParams):

    texturePath = ''
    bFound = False

    if not isinstance(vmtParams, list):
        vmtParams = [ vmtParams ]

    for vmtParam in vmtParams:

        # were given a full path
        if os.path.exists(vmtParam):
            return vmtParam

        # well it is not a key
        elif not vmtKeyValues.get(vmtParam):
            texturePath = formatFullDir(fixVmtTextureDir(vmtParam))
            if os.path.exists(texturePath):
                bFound = True
                break
            continue

        # now it has to be a key...
        texturePath = fixVmtTextureDir(vmtKeyValues[vmtParam])

        if not bFound:
            texturePath = formatNewTexturePath(vmtKeyValues[vmtParam], vmt_to_vmat['textures'][vmtParam][VMAT_DEFAULTVAL], forReal=False)
            texturePath = formatFullDir(texturePath)

        if os.path.exists(texturePath):
            bFound = True
            break

    if not bFound: texturePath = '' # ''

    return texturePath

def createMask(vmtTexture, copySub = '_mask.tga', channel = 'A', invert = False, queue = True):

    imagePath = getTexture(vmtTexture)
    #msg("createMask with", formatVmatDir(vmtTexture), copySub, channel, invert, queue)

    if not imagePath:
        msg("No input for createMask.", imagePath)
        failures.append(vmtFilePath + f" - {vmtTexture} not found")
        return default(copySub)

    if invert:  newMaskPath = imagePath[:-4] + '_' + channel[:3].lower() + '-1' + copySub
    else:       newMaskPath = imagePath[:-4] + '_' + channel[:3].lower()        + copySub

    if os.path.exists(newMaskPath) and not DEBUG:
        return formatVmatDir(newMaskPath)

    if not os.path.exists(imagePath):
        failures.append(vmtFilePath)
        print("~ ERROR: Couldn't find requested image (" + imagePath + "). Please check.")
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
        return fixVector(f"{{{colors[0][1]} {colors[0][1]} {colors[0][1]}}}", True)

    bg = Image.new("L", image.size)

    # Copy the specified channel to the new image using itself as the mask
    bg.paste(imgChannel)

    bg.convert('L').save(newMaskPath, optimize=True) #.convert('P', palette=Image.ADAPTIVE, colors=8)
    bg.close()
    print("+ Saved mask to " + formatVmatDir(newMaskPath))

    return formatVmatDir(newMaskPath)

def flipNormalMap(localPath):

    image_path = formatFullDir(localPath)
    if not os.path.exists(image_path): return

    if not NORMALMAP_G_INVERT_DIRECTLY:
        with open(formatFullDir(localPath[:-4] + '.txt'), 'w') as settingsFile:
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
surfprop_HLA = ['metal_panel', 'wood_solid', 'concrete']

def fixSurfaceProp(vmtVal):

    if SURFACEPROP_AS_IS or vmtVal in ('default', 'default_silent', 'no_decal', 'player', 'roller', 'weapon'):
        return vmtVal

    elif vmtVal in surfprop_force:
        return surfprop_force[vmtVal]
    else:
        if("props" in vmatFilePath): match = get_close_matches('prop.' + vmtVal, surfprop_HLA, 1, 0.4)
        else: match = get_close_matches('world.' + vmtVal, surfprop_HLA, 1, 0.6) or get_close_matches(vmtVal, surfprop_HLA, 1, 0.6)

        return match[0] if match else vmtVal


def int_val(vmtVal, bInvert = False):
    if bInvert: vmtVal = not int(vmtVal)
        #return str(int(not int(vmtVal)))
    return str(int(vmtVal))

def mapped_val(vmtVal, dMap):
    if not vmtVal or vmtVal not in dMap:
        return None
    return str(int(dMap[vmtVal]))

def float_val(vmtVal):
    return "{:.6f}".format(float(vmtVal.strip(' \t"')))

def material_A(vmatKey):
    return vmatKey + 'A'

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
            if not vmtKeyValues.get('$_vmt_ldr_fallback') and vmtKeyValues.get('$basetexture') and not '_ldr_fallback' in vmtFilePath:
                vmtNewPath = os.path.join(os.path.dirname(vmtFilePath), name.replace("hdr", "").rstrip('_') + "_ldr_fallback" + face + INPUT_FILE_EXT)
                if SKYBOX_CREATE_LDR_FALLBACK and (OVERWRITE_VMAT or not os.path.exists(vmtNewPath)):
                    print("Splitting LDR fallback from", vmtSkyboxFile, "to", formatVmatDir(vmtNewPath))
                    vmtNewLines = []
                    with open(vmtFilePath, 'r') as vmatFile:
                        for line in vmatFile.readlines():
                            line = line.lower()
                            if '$hdrbasetexture' in line or '$hdrcompressedtexture' in line:
                                line.replace('$hdrbasetexture', '$_vmt_ldr_fallback')
                                line.replace('$hdrcompressedtexture', '$_vmt_ldr_fallback')

                            vmtNewLines.append(line)

                    with open(vmtNewPath, 'w') as vmtNewFile: vmtNewFile.writelines(vmtNewLines)

                if vmtNewPath not in fileList:
                    fileList.append(vmtNewPath)

            if '$basetexture' in vmtKeyValues: del vmtKeyValues['$basetexture']

        if face not in vmtSkybox[name]: return

        texture = vmtKeyValues.get('$hdrbasetexture') or vmtKeyValues.get('$hdrcompressedtexture') or vmtKeyValues.get('$basetexture')
        facePath = formatFullDir(formatNewTexturePath(texture, textureType = '.pfm' if hdrbasetexture else TEXTURE_FILEEXT))

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


normalmap_list = ['$normal', '$bumpmap', '$bumpmap2']

VMAT_REPLACEMENT = 0
VMAT_DEFAULTVAL = 1
VMAT_TRANSLFUNC = 2
VMAT_EXTRALINES = 3


vmt_to_vmat = {

#'shader': { '$_vmat_shader':    ('shader',  'generic.vfx', [ext, '.vfx']), ''},

'f_properties': {
    '$_vmat_unlit':     ('F_UNLIT',                 '1', None, ''),

    '$translucent':     ('F_TRANSLUCENT',           '1', None),
    '$alphatest':       ('F_ALPHA_TEST',            '1', None),
    '$envmap':          ('F_SPECULAR',              '1', None),
    '$selfillum':       ('F_SELF_ILLUM',            '1', None),
    '$additive':        ('F_ADDITIVE_BLEND',        '1', None),
    '$ignorez':         ('F_DISABLE_Z_BUFFERING',   '1', None),
    '$nocull':          ('F_RENDER_BACKFACES',      '1', None),
    '$decal':           ('F_OVERLAY',               '1', None), # F_BLEND_MODE 1 (for translucency no F_TRANSLUCENT)
    '$flow_debug':      ('F_FLOW_DEBUG',            '0', None),
    '$detailblendmode': ('F_DETAIL_TEXTURE',        '1', [mapped_val, {'0':'1', '1':'2', '12':'0'} ]), # https://developer.valvesoftware.com/wiki/$detail#Parameters_and_Effects
    '$decalblendmode':  ('F_DETAIL_TEXTURE',        '1', [mapped_val, {'0':'1', '1':'2', '12':'0'} ]), # materialsystem\stdshaders\BaseVSShader.h#L26
    '$sequence_blend_mode': ('F_FAST_SEQUENCE_BLEND_MODE', '1', [mapped_val, {'0':'1', '1':'2', '2':'3'}]),

    '$selfillum_envmapmask_alpha': ('F_SELF_ILLUM', '1', None),

    #'$phong':           ('F_PHONG',                 '1'),
    #'$vertexcolor:      ('F_VERTEX_COLOR',          '1'),
},

'textures': {
    # for faces; sky materials are handled differently
    '$hdrcompressedtexture':('TextureColor',  '_color.tga', [formatNewTexturePath], ''), # compress
    '$hdrbasetexture':      ('TextureColor',  '_color.pfm', [formatNewTexturePath], ''), # nocompress

    ## Top / Main layer
    '$basetexture':     ('TextureColor',        ext('_color'),   [formatNewTexturePath],     '' ),
    '$painttexture':    ('TextureColor',        ext('_color'),   [formatNewTexturePath],     '' ),
    '$material':        ('TextureColor',        ext('_color'),   [formatNewTexturePath],     '' ),

    '$bumpmap':         ('TextureNormal',       ext('_normal'),  [formatNewTexturePath],     '' ),
    '$normalmap':       ('TextureNormal',       ext('_normal'),  [formatNewTexturePath],     '' ),

    ## Layer blend mask
    '$blendmodulatetexture':\
                        ('TextureMask',             ext('_mask'),   [createMask, 'G', False], 'F_BLEND 1') if NEW_SH else \
                        ('TextureLayer1RevealMask', ext('_blend'),  [createMask, 'G', False], 'F_BLEND 1'),
    ## Layer 1
    '$basetexture2':    ('TextureColorB' if NEW_SH else 'TextureLayer1Color',  ext('_color'),  [formatNewTexturePath], '' ),
    '$texture2':        ('TextureColorB' if NEW_SH else 'TextureLayer1Color',   ext('_color'),  [formatNewTexturePath], '' ), # UnlitTwoTexture
    '$bumpmap2':        ('TextureNormalB' if NEW_SH else 'TextureLayer1Normal', ext('_normal'), [formatNewTexturePath], '' if NEW_SH else 'F_BLEND_NORMALS 1' ),

    ## Layer 2-3
    '$basetexture3':    ('TextureLayer2Color',  ext('_color'),  [formatNewTexturePath],     ''),
    '$basetexture4':    ('TextureLayer3Color',  ext('_color'),  [formatNewTexturePath],     ''),

    '$normalmap2':      ('TextureNormal2',      ext('_normal'), [formatNewTexturePath],     'F_SECONDARY_NORMAL 1'), # used with refract shader
    '$flowmap':         ('TextureFlow',         ext(''),        [formatNewTexturePath],     'F_FLOW_NORMALS 1\n\tF_FLOW_DEBUG 1'),
    '$flow_noise_texture':\
                        ('TextureNoise',        ext('_noise'),  [formatNewTexturePath],     'F_FLOW_NORMALS 1\n\tF_FLOW_DEBUG 2'),
    '$detail':          ('TextureDetail',       ext('_detail'), [formatNewTexturePath],     'F_DETAIL_TEXTURE 1\n'), # $detail2
    '$decaltexture':    ('TextureDetail',       ext('_detail'), [formatNewTexturePath],     'F_DETAIL_TEXTURE 1\n\tF_SECONDARY_UV 1\n\tg_bUseSecondaryUvForDetailTexture "1"'),

    '$selfillummask':   ('TextureSelfIllumMask',ext('_selfillummask'), [formatNewTexturePath],  ''),
    '$tintmasktexture': ('TextureTintMask',     ext('_mask'),   [createMask, 'G', False],   'F_TINT_MASK 1'), #('TextureTintTexture',)
    '$_vmat_metalmask': ('TextureMetalness',    ext('_metal'),  [formatNewTexturePath],     'F_METALNESS_TEXTURE 1'), # F_SPECULAR too
    '$_vmat_transmask': ('TextureTranslucency', ext('_trans'),  [formatNewTexturePath],     ''),

    # only the G channel ## $ambientoccltexture': '$ambientocclusiontexture':
    '$ao':          ('TextureAmbientOcclusion', ext('_ao'),     [createMask, 'G', False],    'F_AMBIENT_OCCLUSION_TEXTURE 1'), # g_flAmbientOcclusionDirectSpecular "1.000"
    '$aotexture':   ('TextureAmbientOcclusion', ext('_ao'),     [createMask, 'G', False],    'F_AMBIENT_OCCLUSION_TEXTURE 1'), # g_flAmbientOcclusionDirectSpecular "1.000"

    #'$phongexponent2' $phongmaskcontrastbrightness2, $phongbasetint2, $phongamount2

    # Next script should take care of these, unless BASIC_PBR
    '$envmapmask':  ('$envmapmask',         ext('_env_mask'),   [formatNewTexturePath], '') if not BASIC_PBR else \
                    ('TextureRoughness',    ext('_rough'),      [formatNewTexturePath], '') if not LEGACY_SHADER else \
                    ('TextureGlossiness',   ext('_gloss'),      [formatNewTexturePath], ''),

    '$phongmask':   ('$phongmask',          ext('_phong_mask'), [formatNewTexturePath], '') if not BASIC_PBR else \
                    ('TextureRoughness',    ext('_rough'),      [formatNewTexturePath], '') if not LEGACY_SHADER else \
                    ('TextureGlossiness',   ext('_gloss'),      [formatNewTexturePath], ''),
},

'transform': {
    '$basetexturetransform':     ('g_vTex',          'x', None, ''), # g_vTexCoordScale "[1.000 1.000]"g_vTexCoordOffset "[0.000 0.000]"
    '$detailtexturetransform':   ('g_vDetailTex',    'x', None, ''), # g_flDetailTexCoordRotation g_vDetailTexCoordOffset g_vDetailTexCoordScale g_vDetailTexCoordXform
    '$bumptransform':            ('g_vNormalTex',    'x', None, ''),
    #'$bumptransform2':           ('',                '', ''),
    #'$basetexturetransform2':    ('',               '', ''),    #
    #'$texture2transform':        ('',                '', ''),   #
    #'$blendmasktransform':       ('',                '', ''),   #
    #'$envmapmasktransform':      ('',                '', ''),   #
    #'$envmapmasktransform2':     ('',                '', '')    #

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

    # SH_BLEND and SH_VR_STANDARD(SteamVR) -- $NEWLAYERBLENDING
    '$blendsoftness':       ('g_flLayer1BlendSoftness', '0.500',    [float_val], ''),
    '$layerborderstrenth':  ('g_flLayer1BorderStrength','0.500',    [float_val], ''),
    '$layerborderoffset':   ('g_flLayer1BorderOffset',  '0.000',    [float_val], ''),
    '$layerbordersoftness': ('g_flLayer1BorderSoftness','0.500',    [float_val], ''),
    '$layerbordertint':     ('g_vLayer1BorderColor',    '[1.000000 1.000000 1.000000 0.000000]', [fixVector, True], ''),
},

'channeled_masks': {
   #'$vmtKey':                      (extract_from,       extract_as,       channel to extract)|
    '$normalmapalphaenvmapmask':    (normalmap_list,    '$envmapmask',      '1-A'),
    '$basealphaenvmapmask':         ('$basetexture',    '$envmapmask',      'M_1-A'), # 'M_1-A'
    '$envmapmaskintintmasktexture': ('$tintmasktexture','$envmapmask',      '1-R'),
    '$basemapalphaphongmask':       ('$basetexture',    '$phongmask',       '1-A'),
    '$basealphaphongmask':          ('$basetexture',    '$phongmask',       '1-A'),
    '$normalmapalphaphongmask':     (normalmap_list,    '$phongmask',       '1-A'),
    '$bumpmapalphaphongmask':       (normalmap_list,    '$phongmask',       '1-A'),
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
    #'$newlayerblending':     ('',    '',     ''),

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
            #breakpoint()
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
                if outKey in vmatContent: ## Replace keyval if already added
                    msg(outKey + ' is already in.')
                    vmatContent = re.sub(r'%s.+' % outKey, outKey + ' ' + outVal, vmatContent)
                else:
                    vmatContent = f_KeyVal.format(outKey, outVal) + vmatContent # add these keys to the top
                continue ### Skip default content write

            elif(keyType == 'textures'):

                if vmtKey in ['$basetexture', '$hdrbasetexture', '$hdrcompressedtexture']:
                    # semi-BUG: how is hr_dust_tile_01,02,03 blending when its shader is LightmappedGeneric??????????
                    if '$newlayerblending' in vmtKeyValues or '$basetexture2' in vmtKeyValues:
                        outKey = vmatReplacement + 'A' # TextureColor -> TextureColorA

                    if vmatShader == shader.sky:
                        outKey = 'SkyTexture'
                        outVal = fixVmtTextureDir(vmtVal[:-2].rstrip('_') + '_cube' + vmatDefaultVal.lstrip('_color'), fileExt = '')

                elif vmtKey in ['$basetexture3', '$basetexture4']:
                    if not LEGACY_SHADER: print("~ WARNING: 3/4-WayBlend are limited to 2 layers with the current shader", vmatShader)

                elif vmtKey in  ('$bumpmap', '$bumpmap2', '$normalmap', '$normalmap2'):
                    # all(k not in d for k in ('name', 'amount')) vmtKeyValues.keys() & ('newlayerblending', 'basetexture2', 'bumpmap2'): # >=
                    if (vmtKey != '$bumpmap2') and (vmatShader == shader.vr_simple_2way_blend or '$basetexture2' in vmtKeyValues):
                        outKey = vmatReplacement + 'A' # TextureNormal -> TextureNormalA

                    if not 'default/default' in outVal:
                        flipNormalMap(outVal)

                    # this is same as default_normal
                    if vmtVal == 'dev/flat_normal':
                        outVal = default(vmatDefaultVal)

                #### DEFAULT
                #else:
                #    if vmatShader == shader.sky: pass
                #    else: outVal = formatNewTexturePath(vmtVal, vmatDefaultVal)

            elif(keyType == 'transform'):
                if not vmatReplacement or vmatShader == shader.sky:
                    break

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
                outVmtTexture = vmt_to_vmat['channeled_masks'][vmtKey][1]

                if not vmt_to_vmat['textures'].get(outVmtTexture): break

                sourceTexture   = vmt_to_vmat['channeled_masks'][vmtKey][0] # extract as
                sourceChannel   = vmt_to_vmat['channeled_masks'][vmtKey][2] # extract from

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

    if lines_SysAtributes:
        vmatContent += '\n\tSystemAttributes\n\t{\n'
        for line in lines_SysAtributes:
            vmatContent += '\t' + line
        vmatContent += '\t}\n'

    return vmatContent

def convertSpecials(vmtKeyValues):

    # fix phongmask logic
    if vmtKeyValues.get("$phong") == '1' and not vmtKeyValues.get("$phongmask"):
        bHasPhongMask = False
        for key, val in vmt_to_vmat['channeled_masks'].items():
            if val[1] == '$phongmask' and vmtKeyValues.get(key):
                bHasPhongMask = True
                break
        if not bHasPhongMask: # normal map Alpha acts as a phong mask by default
            vmtKeyValues.setdefault('$normalmapalphaphongmask', '1')

    # fix additive logic
    if vmtKeyValues.get("$additive") == '1' and not vmtKeyValues.get("$translucent"):
        # Source 2 need Translucency to be enabled for additive to work
        vmtKeyValues.setdefault('$translucent', '1')

    # fix unlit shader ## what about generic?
    if (matType == 'unlitgeneric') and (vmatShader == shader.vr_complex):
        vmtKeyValues.setdefault("$_vmat_unlit", '1')

    # csgo viewmodels
    if "models\\weapons\\v_models" in vmtFilePath:
        # use _ao texture in \weapons\customization\
        weaponDir = os.path.dirname(vmtFilePath)
        weaponPathSplit = vmtFilePath.split("\\weapons\\v_models\\")
        weaponPathName = os.path.dirname(weaponPathSplit[1])
        if vmtFilePath.endswith(weaponPathName + INPUT_FILE_EXT) or vmtFilePath.endswith(weaponPathName.split('_')[-1] + INPUT_FILE_EXT):
            aoTexturePath = os.path.normpath(weaponPathSplit[0] + "\\weapons\\customization\\" + weaponPathName + '\\' + weaponPathName + "_ao" + TEXTURE_FILEEXT)
            aoNewPath = os.path.normpath(weaponDir + "\\" + weaponPathName + TEXTURE_FILEEXT)
            msg("AO FIX", weaponPathName + INPUT_FILE_EXT, aoTexturePath, aoNewPath)
            if os.path.exists(aoTexturePath):
                msg(aoNewPath)
                if not os.path.exists(aoNewPath):
                    #os.rename(aoTexturePath, aoNewPath)
                    copyfile(aoTexturePath, aoNewPath)
                    print("+ Succesfully moved AO texture for weapon material:", weaponPathName)
                vmtKeyValues["$aotexture"] = formatVmatDir(aoNewPath).replace('materials\\', '')
                print("+ Using ao:", weaponPathName + "_ao" + TEXTURE_FILEEXT)

        #vmtKeyValues.setdefault("$envmap", "0") # specular looks ugly on viewmodels so disable it. does not affect scope lens



#failures = []
invalids = 0

#######################################################################################
# Main function, loop through every .vmt
##
for vmtFilePath in fileList:
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
            else:
                parseKeyValue(line, vmtKeyValues)

            if any(line.lower().endswith(wd) for wd in ignoreList): # split at // take the before part
                msg("Skipping {} block:", line)
                skipNextLine = True

            row += 1

    if matType == 'patch':
        includePath = vmtKeyValues.get("include")
        if includePath:
            #includePath = includePath.replace('"', '').replace("'", '').strip()
            if includePath == r'materials\models\weapons\customization\paints\master.vmt':
                continue

            print("+ Retrieving material info from:", includePath, end='')
            try:
                with open(formatFullDir(includePath), 'r') as includeFile:
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
                failures.append(includePath + " -- Cannot find include.")
                continue

            if not validInclude:
                print(" ... Include has unsupported shader.")
                # matType =
                #continue
        else:
            print("~ WARNING: No include was provided on material with type 'Patch'. Is it a weapon skin?")

    vmatFilePath = vmtFilePath.replace(INPUT_FILE_EXT, '') + OUTPUT_FILE_EXT
    vmatShader = chooseShader(matType, vmtKeyValues, vmtFilePath)

    vmtSkyboxFile = os.path.basename(vmtFilePath).replace(INPUT_FILE_EXT, '')
    skyName, skyFace = [vmtSkyboxFile[:-2], vmtSkyboxFile[-2:]]
    if((formatVmatDir(vmtFilePath).startswith("materials\\skybox\\")) and (skyFace in skyboxFaces)): # and shader
        collectSkyboxFaces(vmtKeyValues, skyName, skyFace)
        vmatShader = shader.vr_complex
        msg("MATERIAL:", matType)

    if validMaterial:
        if os.path.exists(vmatFilePath) and not OVERWRITE_VMAT:
            print('+ File already exists. Skipping!')
            continue

        with open(vmatFilePath, 'w') as vmatFile:
            vmatFile.write('// Converted with vmt_to_vmat.py\n')
            vmatFile.write('// From: ' + vmtFilePath + '\n\n')
            msg(matType + " => " + vmatShader.name)
            vmatFile.write('Layer0\n{\n\tshader "' + vmatShader.name + '.vfx"\n\n')

            convertSpecials(vmtKeyValues)

            vmatFile.write(convertVmtToVmat(vmtKeyValues)) ###############################

            vmatFile.write('}\n')

        if DEBUG: print("+ Saved", vmatFilePath)
        else: print("+ Saved", formatVmatDir(vmatFilePath))

        # TODO: see if this is actually needed
        vmatName = os.path.basename(vmatFilePath)
        if ' ' in vmatName:
            vmatFilePath2 = vmatFilePath.replace(vmatName, vmatName.replace(' ', '_'))
            if not os.path.exists(vmatFilePath2):
                copyfile(vmatFilePath, vmatFilePath2)

    else: invalids += 1


    if not matType:
        if DEBUG: debugContent += "Warning" + vmtFilePath + '\n'

print("\nDone with the materials...\nNow onto our sky cubemaps...")

import json
import numpy as np

with open(formatFullDir("skyboxfaces.json"), 'w+') as fp:
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

    # what is l4d2 skybox/sky_l4d_rural02_ldrbk.pwl
    # TODO: faces_to_cubemap.py

    hdrType = vmtSkybox[skyName].get("_hdrtype")
    maxFace_w = maxFace_h = vmtSkybox[skyName].get("_maxres")
    if not maxFace_w: continue

    cube_w = 4 * maxFace_w
    cube_h = 3 * maxFace_h

    facePath = ''
    vmat_path = formatFullDir(os.path.join("materials\\skybox", skyName.rstrip('_') + OUTPUT_FILE_EXT))
    sky_cubemap_path = skyName.rstrip('_') + '_cube' + ('.pfm' if hdrType else TEXTURE_FILEEXT)
    sky_cubemap_path = formatFullDir(os.path.join("materials\\skybox", sky_cubemap_path))

    if not OVERWRITE_SKYBOX and os.path.exists(sky_cubemap_path): continue

    # uncompressed -> join the pfms same way as tgas
    if (hdrType == 'uncompressed'):
        #emptyData = [0] * (cube_w * cube_h)
        #emptyArray = np.array(emptyData, dtype='float32').reshape((maxFace_h, maxFace_w, 3)
        #for face in skyboxFaces:
        #    if not (facePath := os.path.join("materials\\skybox", vmtSkybox[skyName][face].get('path'))): continue
        #    floatData, scale, _ = PFM.read_pfm(formatFullDir(facePath))

        #for i in range(12):
        #    pass
        #    # paste each

        continue

    imgMode = 'RGBA' if (hdrType == 'compressed') else 'RGB'
    SkyCubemapImage = Image.new(imgMode, (cube_w, cube_h), color = (0, 0, 0)) # alpha?

    for face in skyboxFaces:
        if not (facePath := vmtSkybox[skyName][face].get('path')): continue
        facePath = formatFullDir(os.path.join("materials\\skybox", facePath))
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

    # compressed -> uncompress the whole tga map we just created and paste to pfm
    if (hdrType == 'compressed'):
        compressedPixels = SkyCubemapImage.load()
        hdrImageData = list()
        for x in range(cube_w):
            for y in range(cube_h):

                R, G, B, A = compressedPixels[x,y] # image.getpixel( (x,y) )

                hdrImageData.append(float( (R * (A * 16)) / 262144 ))
                hdrImageData.append(float( (G * (A * 16)) / 262144 ))
                hdrImageData.append(float( (B * (A * 16)) / 262144 ))

        SkyCubemapImage.close()

        HDRImageDataArray = np.rot90(np.array(hdrImageData, dtype='float32').reshape((cube_w, cube_h, 3)))
        PFM.write_pfm(sky_cubemap_path, HDRImageDataArray)

    else:
        SkyCubemapImage.save(sky_cubemap_path)

    if os.path.exists(sky_cubemap_path):

        if OVERWRITE_VMAT or not os.path.exists(vmat_path):
            with open(vmat_path, 'w') as vmatFile:
                vmatFile.write('// Sky material and cube map created by vmt_to_vmat.py\n\n')
                vmatFile.write('Layer0\n{\n\tshader "sky.vfx"\n\n')
                vmatFile.write(f'\tSkyTexture\t"{formatVmatDir(sky_cubemap_path)}"\n\n}}')

        print('+ Successfuly created material and sky cubemap:', os.path.basename(sky_cubemap_path))


if failures: print("\n\t<<<< THESE MATERIALS HAVE ERRORS >>>>")
for failure in failures:        print(failure)
if failures: print("\t^^^^ THESE MATERIALS HAVE ERRORS ^^^^")

try:
    print(f"\nTotal errors :\t{len(failures)} / {len(fileList)}\t| " + "{:.2f}".format((len(failures)/len(fileList)) * 100) + f" % Error rate")
    print(f"Total ignores :\t{invalids} / {len(fileList)}\t| " + "{:.2f}".format((invalids/len(fileList)) * 100) + f" % Skip rate")
except: pass
# csgo -> 206 / 14792 | 1.39 % Error rate -- 4637 / 14792 | 31.35 % Skip rate
# l4d2 -> 504 / 3675 | 13.71 % Error rate -- 374 / 3675 | 10.18 % Skip rate
print("\nFinished! Your materials are now ready.")
