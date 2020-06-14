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
# or `python vmt_to_vmat.py input_path output_path`

import sys
import os
import os.path
from os import path
import shutil
from shutil import copyfile
import re
from PIL import Image
import PIL.ImageOps

# generic, blend instead of vr_complex, vr_2wayblend etc...
# blend doesn't seem to work though. why...
USE_RETRO_SHADERS = False

newshader = not USE_RETRO_SHADERS

# File format of the textures.
TEXTURE_FILEEXT = '.tga' 
# substring added after an alpha map's name, but before the extension
ALPHAMAP_SUBSTRING = '_trans'
INVERSE_SUBSTRING = '_s1_alpha_invert'
# this leads to the root of the NEW materials folder, i.e. D:\Users\username\Desktop\WORK\content\hlvr, make sure to remember the final slash!!
PATH_TO_NEW_CONTENT_ROOT = ""
PATH_TO_CONTENT_ROOT = ""
# Set this to True if you wish to overwrite your old vmat files
OVERWRITE_VMAT = True 

VMAT_REPLACEMENT = 0
VMAT_DEFAULT = 1
VMAT_EXTRALINES = 2

# shaders
SH_BLACK = 'black'
SH_VR_BLACK_UNLIT = 'vr_black_unlit'
SH_GENERIC = 'generic'
SH_VR_BASIC = 'vr_basic'
SH_VR_SIMPLE = 'vr_simple'
SH_VR_COMPLEX = 'vr_complex'
SH_VR_STANDARD = 'vr_standard'
SH_BLEND = 'blend'
SH_VR_SIMPLE_2WAY_BLEND = 'vr_simple_2way_blend'
SH_SKY = 'sky'
SH_VR_EYEBALL = 'vr_eyeball'
SH_SIMPLE_WATER = 'simple_water'
SH_REFRACT = 'refract'
SH_CABLES = 'cables'
SH_VR_MONITOR = 'MonitorScreen'

# What shader to use.
shaders = {
    SH_BLACK: 0,
    SH_VR_BLACK_UNLIT: 1,
    SH_GENERIC: 0,
    SH_VR_BASIC: 0,
    SH_VR_SIMPLE: 0,
    SH_VR_COMPLEX: 0,
    SH_VR_STANDARD: 0,
    SH_BLEND: 0,
    SH_VR_SIMPLE_2WAY_BLEND: 0,
    SH_SKY: 0,
    SH_VR_EYEBALL: 0,
    SH_SIMPLE_WATER: 0,
    SH_REFRACT: 0,
    SH_CABLES: 0,
    SH_VR_MONITOR: 0
}

# Most shaders have missing/additional properties.
# Need to set an apropriate one that doesn't sacrifice much.
def chooseShader(matType, vmtKeyValList, fileName):

    # not recognized, give emtpy shader SH_VR_BLACK_UNLIT
    if matType not in materialTypes:
        return max(shaders, key = shaders.get) 

    #TODO: if containts values starting with _rt_ give some empty shader

    shaders[SH_VR_BLACK_UNLIT] = 0
    
    if USE_RETRO_SHADERS:   shaders[SH_GENERIC] += 1
    else:                   shaders[materialTypes[matType]] += 1
    
    
    if matType == "unlitgeneric":
        shaders[SH_SKY] += 1

        if "skybox" in fileName: shaders[SH_SKY] += 2
        if "$nofog" in vmtKeyValList: shaders[SH_SKY] += 1
        if "$ignorez" in vmtKeyValList: shaders[SH_SKY] += 2

        if "$receiveflashlight" in vmtKeyValList: shaders[SH_SKY] -= 6
    
    elif matType == "worldvertextransition":
        if vmtKeyValList.get('$basetexture2'): shaders[SH_VR_SIMPLE_2WAY_BLEND] += 69

    elif matType == "":
        pass
    
    return max(shaders, key = shaders.get)

# material types need to be lowercase because python is a bit case sensitive
materialTypes = {
    "unlitgeneric":         SH_SKY,  
    "sky":                  SH_SKY,
    "vertexlitgeneric":     SH_VR_COMPLEX,
    "decalmodulate":        SH_VR_COMPLEX,
    "lightmappedgeneric":   SH_VR_COMPLEX,
    "patch":                SH_VR_COMPLEX,
    "teeth":                SH_VR_COMPLEX,
    "eyes":                 SH_VR_EYEBALL,
    "eyeball":              SH_VR_EYEBALL,
    "water":                SH_SIMPLE_WATER,
    "refract":              SH_REFRACT,
    "worldvertextransition":SH_VR_SIMPLE_2WAY_BLEND,
    "lightmappedreflective":SH_VR_COMPLEX,
    "cables":               SH_CABLES,
    "lightmappedtwotexture":SH_VR_COMPLEX, # 2 multiblend $texture2 nocull scrolling, model, additive.
    "unlittwotexture":      SH_VR_COMPLEX, # 2 multiblend $texture2 nocull scrolling, model, additive.
    "character":            SH_VR_COMPLEX
    #"lightmapped_4wayblend":SH_BLEND, # no available shader that 4blends
    #, #TODO: make this system functional
    #"modulate",
}

# fallback material types, ignore them
ignoreList = [
"vertexlitgeneric_hdr_dx9",
"vertexlitgeneric_dx9",
"vertexlitgeneric_dx8",
"vertexlitgeneric_dx7",
"lightmappedgeneric_hdr_dx9",
"lightmappedgeneric_dx9",
"lightmappedgeneric_dx8",
"lightmappedgeneric_dx7",
]

surfacePropertiesNew = {
    'stucco':       'world.drywall',
    'tile':         'world.tile_floor',
    'metalpanel':   'world.metal_panel',
}

QUOTATION = '"'
COMMENT = "// "

def parseDir(dirName):
    files = []
    for root, _, fileNames in os.walk(dirName):
        for fileName in fileNames:	
            if fileName.lower().endswith('.vmt'):
                files.append(os.path.join(root,fileName))
            
    return files

###
### Main Execution
###

currentDir = os.getcwd()

if not PATH_TO_CONTENT_ROOT:
    if(len(sys.argv) >= 2):
        PATH_TO_CONTENT_ROOT = sys.argv[1]
    else:
        #print("here: " + PATH_TO_CONTENT_ROOT)
        while not PATH_TO_CONTENT_ROOT:
            c = input('Type the root directory of the vmt materials you want to convert (enter to use current directory, q to quit).: ') or currentDir
            if not path.isdir(c):
                if c in ('q', 'quit', 'exit', 'close'):
                    quit()
                print('Could not find directory.')
                continue
            PATH_TO_CONTENT_ROOT = c.lower().strip().strip('"')
            #print(PATH_TO_CONTENT_ROOT)

if not PATH_TO_NEW_CONTENT_ROOT:
    if(len(sys.argv) >= 3):
        PATH_TO_NEW_CONTENT_ROOT = sys.argv[2]
    else:
        while not PATH_TO_NEW_CONTENT_ROOT:
            c = input('Type the directory you wish to output Source 2 materials to (enter to use the same dir): ') or currentDir
            if(c == currentDir):
                PATH_TO_NEW_CONTENT_ROOT = PATH_TO_CONTENT_ROOT # currentDir
            else:
                if not path.isdir(c):
                    if c in ('q', 'quit', 'exit', 'close'):
                        quit()
                    print('Could not find directory.')
                    continue
                PATH_TO_NEW_CONTENT_ROOT = c.lower().strip().strip('"')

PATH_TO_CONTENT_ROOT = os.path.normpath(PATH_TO_CONTENT_ROOT) + '\\'
PATH_TO_NEW_CONTENT_ROOT =  os.path.normpath(PATH_TO_NEW_CONTENT_ROOT) + '\\'

print('\nSource 2 Material Conveter! By Rectus via Github.')
print('Initially forked by Alpyne, this version by caseytube.\n')
print('+ Reading old materials from: ' + PATH_TO_CONTENT_ROOT)
print('+ New materials will be created in: ' + PATH_TO_NEW_CONTENT_ROOT)
print('--------------------------------------------------------------------------------------------------------')


# "environment maps/metal_generic_002" -> "materials/environment maps/metal_generic_002(.tga)"
def formatVmtTextureDir(localPath):
    localPath = 'materials/' + localPath.strip().strip('"') + TEXTURE_FILEEXT
    localPath = localPath.replace('\\', '/') # Convert paths to use forward slashes.
    localPath = localPath.replace('.vtf', '')#.replace('.tga', '') # remove any old extensions
    localPath = localPath.lower()

    return localPath

# materials/texture_color.tga -> C:/Users/User/Desktop/stuff/materials/texture_color.tga
def formatFullDir(localPath):
    #os.path.abspath(PATH_TO_CONTENT_ROOT + localPath)
    return os.path.abspath(os.path.join(PATH_TO_CONTENT_ROOT, localPath))

# inverse of formatFullDir()
def formatVmatDir(localPath):
    localPath = os.path.normpath(localPath)
    return localPath.replace(PATH_TO_CONTENT_ROOT, '')

# -------------------------------
# Returns texture path of given vmtParam, texture which has likely been renamed to be S2 naming compatible
# $basetexture  ->  /path/to/texture_color.tga of the TextureColor
# -------------------------------
def getTexture(vmtParam):
    # if we get a list choose from the one that exists
    if isinstance(vmtParam, tuple):
        for actualParam in vmtParam:
            if vmtKeyValList.get(actualParam):
                return formatNewTexturePath(vmtKeyValList[actualParam], vmt_to_vmat['textures'][actualParam][VMAT_DEFAULT], forReal=False)

    elif vmtKeyValList.get(vmtParam):
        return formatNewTexturePath(vmtKeyValList[vmtParam], vmt_to_vmat['textures'][vmtParam][VMAT_DEFAULT], forReal=False)
    
    return None

# -------------------------------
# Returns correct path, checks if alreay exists, renames with proper extensions, etc...
# -------------------------------
def formatNewTexturePath(vmtPath, textureType = TEXTURE_FILEEXT, renameTexture = False, forReal = True):

    # "newde_cache/nc_corrugated" -> materials/newde_cache/nc_corrugated
    textureLocal = formatVmtTextureDir(vmtPath)
    textureLocal = textureLocal.lower()
    
    # materials/newde_cache/nc_corrugated.tga -> materials/newde_cache/nc_corrugated
    if textureLocal[-4:] == TEXTURE_FILEEXT:
        textureLocal = textureLocal[:-4]
        if textureLocal[-4:] == TEXTURE_FILEEXT:
            textureLocal = textureLocal[:-4]

    
    # if already has s2 supported type in the name (_normal) doge_wainscoting_1_normal.tga
    # TODO: texture_n.tga -> texture_normal.tga
    if textureAddTag(textureLocal, textureType) == textureLocal:
        renameTexture = False
        return formatVmatDir(textureLocal + textureType[-4:])

    #if textureLocal.endswith(textureType[:-4]):
    #    renameTexture = False
    #    return formatVmatDir(textureLocal + textureType[-4:])

    # TODO: this is not correct - wtf
    if not forReal:
        newVmatFormattedTexture = formatVmatDir(textureLocal + textureType)
    
    # materials/newde_cache/nc_corrugated -> materials/newde_cache/nc_corrugated_color.tga
    if renameTexture:
        #if forReal:
        newVmatFormattedTexture = formatVmatDir(textureRename(textureLocal, textureLocal + textureType))
        #else:
            #newVmatFormattedTexture = formatVmatDir(textureLocal + textureType)
    else:
        newVmatFormattedTexture = formatVmatDir(textureLocal + textureType)

    return newVmatFormattedTexture

def textureAddTag(str1, str2):
    if str1.endswith(str2[:-4]):
        return str1
    str1 += str2
    return str1

def textureRename(localPath, newNamePath, makeCopy = False):

    if 'skybox' in localPath:
        return localPath

    localPath = formatFullDir(localPath)
    if localPath[:-4] != TEXTURE_FILEEXT:
        localPath += TEXTURE_FILEEXT
    newNamePath = formatFullDir(newNamePath)
    
    if(os.path.exists(newNamePath)):
        #print("+ Using already renamed texture: " + formatVmatDir(newNamePath))
    #elif not os.path.exists(localPath):
    #    #print("+ Missing texture " + formatVmatDir(localPath) + " queued for rename into: " + formatVmatDir(newNamePath))
    #    #print("+ Please find it and rename it accordingly or the material won't load")
        return newNamePath
    
    if not os.path.exists(localPath):
        print("+ Could not find texture " + formatVmatDir(localPath) + " queued for rename into: " + formatVmatDir(newNamePath))
        for key in list(vmt_to_vmat['textures']):
            if os.path.exists(localPath[:-4] + vmt_to_vmat['textures'][key][VMAT_DEFAULT]):
                makeCopy = True
                localPath = localPath[:-4] + vmt_to_vmat['textures'][key][VMAT_DEFAULT]
                print("+ Nevermind... found renamed copy! " + formatVmatDir(localPath))
                print("+ However, we shouldn't have had to search for it. Check if material's using same texture for more than one map.")
                break
        
        if not os.path.exists(localPath):
            print("+ Please find it and rename it accordingly or the material won't load")
            return newNamePath

    try:
        if not makeCopy:
            os.rename(localPath, newNamePath)
            #print("+ Renamed new texture to " + formatVmatDir(localPath))
        else:
            copyfile(localPath, newNamePath)
            #print("+ Copied new texture to " + formatVmatDir(localPath))
        
    
    except FileExistsError:
        print("+ Could not rename " + formatVmatDir(localPath) + ". Renamed copy already exists")
    
    except FileNotFoundError:
        if(not os.path.exists(newNamePath)):
            print("~ WARNING: couldnt find")

    return newNamePath

# Verify file paths
fileList = []
if(PATH_TO_CONTENT_ROOT):
    absFilePath = os.path.abspath(os.path.join(PATH_TO_CONTENT_ROOT, 'materials'))
    
    if os.path.isdir(absFilePath):
        fileList.extend(parseDir(absFilePath))
    
    elif(absFilePath.lower().endswith('.vmt')):
        fileList.append(absFilePath)
    
else:
    input("No directory specified, press any key to quit...")
    quit()

def parseVMTParameter(line, parameters):
    words = []
    
    if line.startswith('\t') or line.startswith(' '):
        #cached_line_prev = line
        re.sub('"', ' ', line) # fix for some weird cases like: "$key""value""
        words = re.split(r'\s+', line, 2)
    else:
        words = re.split(r'\s+', line, 1)
        
    words = list(filter(len, words))
    if len(words) < 2:
        #print("Cannot read -> " + str(words))
        return 
    key = words[0].strip('"').lower()
    
    if key.startswith('/'):
        return
    
    if not key.startswith('$'):
        if not key.startswith('include'):
            return

    # "GPU>=2?$detailtexture"
    if '?' in key:
        print("~ WARNING: Might not process well materials that have GPU-setting based parameters. Please manually check.")
        #key = key.split('?')[1].lower()
        key.split('?')
        if key[0] == 'GPU>=2':
            print("@ DBG: Trying using the high-shader parameter.")
            key = key[2].lower()
        else:
            print("~ WARNING: Might not process well materials that have GPU-setting based parameters. Please manually check.")
            if key[0] == 'GPU<2':
                return
            key = key[2].lower()

    val = words[1].lstrip('\n').lower()
    
    # remove comments, HACK
    commentTuple = val.partition('//')
    
    #if(val.strip('"' + "'") == ""):
    #    #print("+ No value found, moving on")
    #    return
    
    if not commentTuple[0] in parameters:
        parameters[key] = commentTuple[0]


def createMaskFromChannel(vmtTexture, channel = 'A', copySub = '_mask.tga', invert = True):
    if not os.path.exists(vmtTexture):
        vmtTexture = formatFullDir(vmtTexture)

    if invert:  alphapath = vmtTexture[:-4] + '_' + 'inverted-' + channel + copySub
    else:       alphapath = vmtTexture[:-4] + '_'               + channel + copySub
    
    if os.path.exists(alphapath):
        #print("+ Alpha mask already exists: " + alphapath)
        return formatVmatDir(alphapath)

    if os.path.exists(vmtTexture):
        # Open the image and convert it to RGBA, just in case it was indexed
        image = Image.open(vmtTexture).convert('RGBA')
        imgChannel = image.getchannel(str(channel))

        # Create a new image with an opaque black background
        bg = Image.new("RGBA", image.size, (0,0,0,255))

        # Copy the alpha channel to the new image using itself as the mask
        bg.paste(imgChannel)
        
        if invert:
            r,g,b,_ = bg.split()
            rgb_image = Image.merge('RGB', (r,g,b))
            inverted_image = PIL.ImageOps.invert(rgb_image)

            r2,g2,b2 = inverted_image.split()

            final_transparent_image = Image.merge('RGBA', (r2,g2,b2,255))
            
            final_transparent_image.save(alphapath)
            final_transparent_image.close()
        else:
            bg.save(alphapath)
            bg.close()
            
    else:
        print("~ WARNING: Couldn't find requested image (" + formatVmatDir(vmtTexture) + "). Please check.")
        return 'materials/default/default_mask.tga'

    print("+ Saved mask to" + formatVmatDir(alphapath))
    return formatVmatDir(alphapath)

def flipNormalMap(localPath):
    with open(formatFullDir(localPath[:-4] + '.txt'), 'w') as settingsFile:
        settingsFile.write('"settings"\n{\t"legacy_source1_inverted_normal" "1"\n}')

    """image_path = formatFullDir(localPath)
    
    if path.exists(image_path):
        # Open the image and convert it to RGBA, just in case it was indexed
        image = Image.open(image_path).convert('RGBA')

        # Extract just the green channel
        r,g,b,a = image.split()

        g = PIL.ImageOps.invert(g)

        final_transparent_image = Image.merge('RGBA', (r,g,b,a))
        
        final_transparent_image.save(image_path)"""

skybox = {
    'up':{},
    'dn':{},
    'lf':{},
    'rt':{},
    'bk':{},
    'ft':{}
}

def buildS2SkyCubemap(fileName):

    # https://developer.valvesoftware.com/wiki/File:Hdr_skyface_sides.jpg
    
    # Usually the up face. Using it to determine the final resolution.
    baseFace = fileName[:-4] + TEXTURE_FILEEXT
    
    if os.path.exists(baseFace):
        face_w, _ = Image.open(baseFace).size
        face_h = face_w # It's a square anyway, this deals with "scale 1 2"
    else:
        print("~ WARNING: Couldn't find skybox face " + formatVmatDir(baseFace) + ". SkyCube creation failed.")
        return 'materials/default/default_cube.pfm'
    
    SkyCubeImage_Path = fileName[:-6].rstrip('_') + '_cube' + TEXTURE_FILEEXT

    #if os.path.exists(SkyCubeImage_Path):
    #    print('+ SkyCube already exists. Skipping!')
    #    return SkyCubeImage_Path
    
    cube_w = 4 * face_w
    cube_h = 3 * face_h

    # TODO: check for hdr some other way
    # also what is l4d2 skybox/sky_l4d_rural02_ldrbk.pwl 
    # TODO: !!!!! HOW DO I DO HDR TEXTURES !!!!!
    if(fileName[-9:-6] == 'hdr'): 
        #SkyCubeImage_Path = fileName[:-6].rstrip('_') + '_cube.exr'
        return
    elif(fileName[-9:-6] == 'ldr'):
        #SkyCubeImage_Path = fileName[:-6].rstrip('_') + '_cube.exr'
        return
    else: SkyCubeImage_Path = fileName[:-6].rstrip('_') + '_cube' + TEXTURE_FILEEXT
    print('@ DBG: SKYBOX TEXTURE')
    SkyCubeImage = Image.new('RGB', (cube_w, cube_h), color = (0, 0, 0))
    for face in skybox:
        
        skybox[face]['path'] = fileName[:-6] + face + TEXTURE_FILEEXT
        
        if(not os.path.exists(skybox[face]['path'])):
            skybox[face]['path'] = None
            continue
        
        # TODO: i think top and bottom need to be rotated by 90 + side faces offset by x
        # check if front is below top and above bottom
        if face == 'up':   skybox[face]['position'] = (cube_w - 3 * face_w, cube_h - 3 * face_h)
        elif face == 'ft': skybox[face]['position'] = (cube_w - 2 * face_w, cube_h - 2 * face_h)
        elif face == 'lf': skybox[face]['position'] = (cube_w - 1 * face_w, cube_h - 2 * face_h)
        elif face == 'bk': skybox[face]['position'] = (cube_w - 4 * face_w, cube_h - 2 * face_h)
        elif face == 'rt': skybox[face]['position'] = (cube_w - 3 * face_w, cube_h - 2 * face_h)
        elif face == 'dn': skybox[face]['position'] = (cube_w - 3 * face_w, cube_h - 1 * face_h)
        
        faceHandle = Image.open(skybox[face]['path'])
        
        if(skybox[face].get('rotate')):
            print("@ DBG: ROTATING `" + face + "` BY THIS: " + str(skybox[face]['rotate']))
            faceHandle = faceHandle.rotate(int(skybox[face]['rotate']))
            skybox[face]['rotate'] = 0 # clear the value for the next sky cubemap
        
        SkyCubeImage.paste(faceHandle, skybox[face]['position'])

        SkyCubeImage.save(SkyCubeImage_Path)


    if os.path.exists(SkyCubeImage_Path):
        print('@ DBG: Successfuly created LDR skycube at: ' + formatVmatDir(SkyCubeImage_Path))
        return formatVmatDir(SkyCubeImage_Path)
    else:
        return 'materials/default/default_cube.pfm'

    return 'materials/default/default_cube.pfm'

def fixIntVector(s, needsAlpha = True, replicateSingle = 0):
    # {255 175 255}
    likelyColorInt = False
    likelySingle = False
    if('{' in s and '}' in s):
        likelyColorInt = True
    elif('[' not in s and ']' not in s):    
        likelySingle = True

    s = s.strip()
    s = s.strip('"' + "'")    
    s = s.strip().strip().strip('][}{')
    originalValueList = [str(float(i)) for i in s.split(' ') if i != '']
    
    # [4] -> [4.000000 4.000000]
    if(replicateSingle and likelySingle and len(originalValueList) <= 1):
        for _ in range(replicateSingle):
            originalValueList.append(originalValueList[0])
    
    # [255 175 255] -> [255 175 255 1.000]
    if(needsAlpha): originalValueList.append(1.0) # alpha
    
    # [255 128 255 1.000] -> [1.000000 0.500000 1.000000 1.000000]
    for strvalue in originalValueList:
        #if(needsAlpha and originalValueList.index(strvalue) > 2): break
        flvalue = float(strvalue)
        if likelyColorInt and originalValueList.index(strvalue) < 3:
            flvalue /= 255
        
        originalValueList[originalValueList.index(strvalue)] = "{:.6f}".format(flvalue)

    #print (originalValueList)
    return '[' + ' '.join(originalValueList) + ']'

def is_convertible_to_float(value):
  try:
    float(value)
    return True
  except:
    return False

MATRIX_ROTATIONCENTER = 0
MATRIX_SCALE = 1
MATRIX_ROTATE = 2
MATRIX_TRANSLATE = 3

def listMatrix(s):
    # [0, 1] center defines the point of rotation. Only useful if rotate is being used.
    # [2, 3] scale fits the texture into the material the given number of times. '2 1' is a 50% scale in the X axis.
    # [4]    rotate rotates the texture counter-clockwise in degrees. Accepts any number, including negatives.
    # [5, 6] translate shifts the texture by the given numbers. '.5' will shift it half-way.

    # Assuming you can't use these individually as "rotate 4" /// TODO: welp you can
    # $detailtexturetransform "center .5 .5 scale 1 1 rotate 0 translate 0 0"
    # -> [0.5, 0.5, 1.0, 1.0, 0.0, 0.0, 0.0]
    s = s.strip('"')
    valueList = [float(str(i)) for i in s.split(' ') if is_convertible_to_float(i)]

    # -> ['[0.5 0.5]', '[1.0 1.0]', '0.0', '[0.0 0.0]']
    return ['[' + "{:.3f}".format(valueList[0]) + ' ' + "{:.3f}".format(valueList[1]) + ']',\
            '[' + "{:.3f}".format(valueList[2]) + ' ' + "{:.3f}".format(valueList[3]) + ']',\
                  "{:.3f}".format(valueList[4]),\
            '[' + "{:.3f}".format(valueList[5]) + ' ' + "{:.3f}".format(valueList[6]) + ']'\
            ]

#   $NEWLAYERBLENDING
#   $BLENDSOFTNESS	0.05  
# 	$LAYERBORDERSTRENGTH	.25
# 	$LAYERBORDEROFFSET	0
# 	$LAYERBORDERSOFTNESS	.1
#   $LAYERBORDERTINT	"{150 200 1}"

normalmaps = ('$normal', '$bumpmap', '$bumpmap2')

vmt_to_vmat = {
    'textures': {

        '$hdrcompressedtexture':('SkyTexture',          '_cube.pfm',        ''),
        '$hdrbasetexture':      ('SkyTexture',          '_cube.pfm',        ''),
        
        ## Layer0 
        '$basetexture':         ('TextureColor',        '_color.tga',       ''), # SkyTexture
        '$painttexture':        ('TextureColor',        '_color.tga',       ''),
        '$bumpmap':             ('TextureNormal',       '_normal.tga',      ''),
        '$normalmap':           ('TextureNormal',       '_normal.tga',      ''),
        '$phongexponenttexture':('TextureRoughness',    '_rough.tga',       '') if newshader else ('TextureGlossiness', '_gloss.tga', 'F_ANISOTROPIC_GLOSS 1\n'),
        
        ## Layer1
        '$basetexture2':        ('TextureColorB',       '_color.tga',       '') if newshader else ('TextureLayer1Color', '_color.tga', ''),
        '$bumpmap2':            ('TextureNormalB',      '_normal.tga',      '') if newshader else ('TextureLayer1Normal', '_normal.tga', 'F_BLEND_NORMALS 1'),
        '$phongexponent2':      ('TextureRoughnessB',   '_rough.tga',       ''), # $phongmaskcontrastbrightness2, $phongbasetint2, $phongamount2

        ## Layer2-3
        '$basetexture3':        ('TextureLayer2Color',  '_color.tga',       ''),
        '$basetexture4':        ('TextureLayer3Color',  '_color.tga',       ''),

        '$blendmodulatetexture':('TextureMask',         '_mask.tga',    'F_BLEND 1') if newshader else ('TextureLayer1RevealMask', '_blend.tga',   'F_BLEND 1'),
        
        #'$texture2':            ('',  '_color.tga',       ''), # UnlitTwoTexture
        '$normalmap2':          ('TextureNormal2',      '_normal.tga',      'F_SECONDARY_NORMAL 1'), # used with refract shader
        '$flowmap':             ('TextureFlow',         TEXTURE_FILEEXT,    'F_FLOW_NORMALS 1\n\tF_FLOW_DEBUG 1'),
        '$flow_noise_texture':  ('TextureNoise',        '_noise.tga',       'F_FLOW_NORMALS 1\n\tF_FLOW_DEBUG 2'),
        '$detail':              ('TextureDetail',       '_detail.tga',      'F_DETAIL_TEXTURE 1\n'),
        '$decaltexture':        ('TextureDetail',       '_detail.tga',      'F_DETAIL_TEXTURE 1\n'),
        #'$detail2':            ('TextureDetail',       '_detail.tga',      'F_DETAIL_TEXTURE 1\n'),
        '$tintmasktexture':     ('TextureTintMask',     '_mask.tga',        'F_TINT_MASK 1'), # GREEN CHANNEL ONLY, RED IS FOR $envmapmaskintintmasktexture 1
        '$selfillummask':       ('TextureSelfIllumMask','_selfillummask.tga',''), # $blendtintbybasealpha 1 
        
        # also pretty much nothing
        '$envmap':              ('TextureCubeMap',      '_cube.pfm',        'F_SPECULAR 1\n\tF_SPECULAR_CUBE_MAP 1\n\tF_SPECULAR_CUBE_MAP_PROJECTION 1\n\tg_flCubeMapBlurAmount "1.000"\n\tg_flCubeMapScalar "1.000"\n\tg_vReflectanceRange "[0.000 0.600]"\n'),
        # does nothing?
        '$envmapmask':          ('TextureReflectance',  '_refl.tga',        ''),  #  selfillum_envmapmask_alpha envmapmaskintintmasktexture 
        # does nothing?
        '$phong':               ('TextureReflectance',  '_refl.tga',        '\n\tg_vReflectanceRange "[0.000 0.600]"\n'),
         

        #('TextureTintTexture',)
        
        # These have no separate masks
        '$translucent':         ('TextureTranslucency', '_trans.tga',        'F_TRANSLUCENT 1\n'), # g_flOpacityScale "1.000"
        '$alphatest':           ('TextureTranslucency', '_trans.tga',        'F_ALPHA_TEST 1\n'),
        
        # only the G channel -> R = flCavity, G = flAo, B = cModulation, A = flPaintBlend
        '$ao':                   ('TextureAmbientOcclusion', '_ao.tga',       'g_flAmbientOcclusionDirectSpecular "1.000"\n\tF_AMBIENT_OCCLUSION_TEXTURE 1\n'),
        '$aotexture':            ('TextureAmbientOcclusion', '_ao.tga',       'g_flAmbientOcclusionDirectSpecular "1.000"\n\tF_AMBIENT_OCCLUSION_TEXTURE 1\n'),
        #'$ambientoccltexture':   ('TextureAmbientOcclusion', '_ao.tga',       'g_flAmbientOcclusionDirectSpecular "1.000"\n\tF_AMBIENT_OCCLUSION_TEXTURE 1\n'),
        #'$ambientocclusiontexture':('TextureAmbientOcclusion', '_ao.tga',     'g_flAmbientOcclusionDirectSpecular "1.000"\n\tF_AMBIENT_OCCLUSION_TEXTURE 1\n')
    },

    # [0, 1] center defines the point of rotation. Only useful if rotate is being used.
    # [2, 3] scale fits the texture into the material the given number of times. '2 1' is a 50% scale in the X axis.
    #    [4] rotate rotates the texture counter-clockwise in degrees. Accepts any number, including negatives.
    # [5, 6] translate shifts the texture by the given numbers. '.5' will shift it half-way.
    # $detailtexturetransform "center .5 .5 scale 1 1 rotate 0 translate 0 0"
    'transform': {
        '$basetexturetransform':     ('g_vTex',          '', 'g_vTexCoordScale "[1.000 1.000]"g_vTexCoordOffset "[0.000 0.000]"'),
        '$basetexturetransform2':    ('', '', ''),
        '$texture2transform':        ('',                '', ''),
        '$detailtexturetransform':   ('g_vDetailTex',    '', 'g_flDetailTexCoordRotation g_vDetailTexCoordOffset g_vDetailTexCoordScale g_vDetailTexCoordXform'),
        '$blendmasktransform':       ('',                '', ''),
        '$bumptransform':            ('g_vNormalTex',    '', ''),
        '$bumptransform2':           ('',                '', ''),
        '$envmapmasktransform':      ('',                '', ''),
        '$envmapmasktransform2':     ('',                '', '')

    },
    
    'settings': {
        '$detailscale':         ('g_vDetailTexCoordScale',  '[1.000 1.000]',    ''),
        '$detailblendfactor':   ('g_flDetailBlendFactor',   '1.000',            ''),
        #'$detailblendfactor2':  ('g_flDetailBlendFactor',   '1.000',            ''),
        #'$detailblendfactor3':  ('g_flDetailBlendFactor',   '1.000',            ''),
        #'$detailblendfactor4':  ('g_flDetailBlendFactor',   '1.000',            ''),
        '$selfillumscale':      ('g_flSelfIllumScale',      '1.000',            ''),
        '$selfillumtint':       ('g_vSelfIllumTint','[1.000 1.000 1.000 0.000]',''),
        
        #Assumes env_cubemap
        # TODO: if envmapmask, apply tint to the map manually, else just use this below.
        #'$envmaptint':          ('TextureReflectance',      '[1.000 1.000 1.000 0.000]', ''),
        
        '$phongexponent':       ('TextureRoughness',    '[1.000 1.000 0.000 0.000]', ''),
        '$phongexponent2':      ('TextureRoughnessB',   '[1.000 1.000 0.000 0.000]', ''),

        '$color':               ('g_vColorTint',           '[1.000 1.000 1.000 0.000]', ''),
        #'$color2':               ('g_vColorTint',           '[1.000 1.000 1.000 0.000]', ''),
        
        # questionable
        '$blendtintcoloroverbase':('g_flModelTintAmount', '1.000', ''),

        '$surfaceprop':         ('SystemAttributes\n\t{\n\t\tPhysicsSurfaceProperties\t', 'default', ''),
        
        '$alpha':               ('g_flOpacityScale', '1.000', ''),
        '$alphatestreference':  ('g_flAlphaTestReference', '0.500', ''),
        
        # inverse
        '$nofog':               ('g_bFogEnabled', '0', ''),

        '$refractamount':       ('g_flRefractScale',        '0.200', ''),
        '$flow_worlduvscale':   ('g_flWorldUvScale',        '1.000', ''),
        '$flow_noise_scale':    ('g_flNoiseUvScale',        '0.010', ''), # g_flNoiseStrength?
        '$flow_bumpstrength':   ('g_flNormalMapStrength',   '1.000', ''),

        # SH_BLEND and SH_VR_STANDARD(SteamVR) -- $NEWLAYERBLENDING settings used on dust2 etc
        '$blendsoftness':       ('g_flLayer1BlendSoftness', '0.500',    ''),
        '$layerborderstrenth':  ('g_flLayer1BorderStrength','0.500',    ''),
        '$layerborderoffset':   ('g_flLayer1BorderOffset',  '0.000',    ''),
        '$layerbordersoftness': ('g_flLayer1BorderSoftness','0.500',    ''),

        '$layerbordertint':     ('g_vLayer1BorderColor',       '[1.000000 1.000000 1.000000 0.000000]', ''),
        
        #'LAYERBORDERSOFTNESS':  ('g_flLayer1BorderSoftness', '1.0', ''),
        #rimlight
          
    },

    'f_settings': {
        '$selfillum':           ('F_SELF_ILLUM',        '1', ''),
        '$additive':            ('F_ADDITIVE_BLEND',    '1', ''),
        '$nocull':              ('F_RENDER_BACKFACES',  '1', ''),
        '$decal':               ('F_OVERLAY',           '1', ''),
        '$flow_debug':          ('F_FLOW_DEBUG',        '0', ''),
        '$detailblendmode':     ('F_DETAIL_TEXTURE',    '1', ''), # not 1 to 1
        '$decalblendmode':      ('F_DETAIL_TEXTURE',    '1', ''), # not 1 to 1
    },

    'alphamaps': {
        
      # '$vmtKey':  (key for which we provide a map,  key from which we extract a map,    channel to extract)
        '$normalmapalphaenvmapmask':    ('$envmapmask',     normalmaps,         'A'), 
        '$basealphaenvmapmask':         ('$envmapmask',     '$basetexture',     'A'),
        '$envmapmaskintintmasktexture': ('$envmapmask',     '$tintmasktexture', 'R'),
        
        '$basemapalphaphongmask':       ('$phong',          '$basetexture',     'A'),
        '$basealphaphongmask':          ('$phong',          '$basetexture',     'A'), # rare and stupid
        '$normalmapalphaphongmask':     ('$phong',          normalmaps,         'A'), # rare and stupid
        '$bumpmapalphaphongmask':       ('$phong',          normalmaps,         'A'), # rare and stupid
        
        '$blendtintbybasealpha':        ('$tintmasktexture','$basetexture',     'A'),
        '$selfillum_envmapmask_alpha':  ('$selfillummask',  '$envmap',          'A')
    },

    
    # no direct replacement, etc
    'others2': {
        # ssbump shader is currently broken in HL:A.
        '$ssbump':               ('TextureBentNormal',    '_bentnormal.tga', '\n\tF_ENABLE_NORMAL_SELF_SHADOW 1\n\tF_USE_BENT_NORMALS 1\n'),
        '$newlayerblending':     ('',    '',     ''),



        # fRimMask = vMasks1Params.r;
		# fPhongAlbedoMask = vMasks1Params.g;
		# fMetalnessMask = vMasks1Params.b;
		# fWarpIndex = vMasks1Params.a;
        '$maskstexture':    ('',    '',     ''),
        '$masks':    ('',    '',     ''),
        '$masks1':    ('',    '',     ''),
        '$masks2':    ('',    '',     ''),
        
        # $selfillumfresnelminmaxexp "[1.1 1.7 1.9]"
        #'$selfillum_envmapmask_alpha':     ('',    '',     ''),
        
        
        # TODO: the fake source next to outside area on de_nuke;
        # x = texturescrollrate * cos(texturescrollangle) ?????
        # y = texturescrollrate * sin(texturescrollangle) ?????
        #'TextureScroll':    (('texturescrollvar', 'texturescrollrate', 'texturescrollangle'), 'g_vTexCoordScrollSpeed', '[0.000 0.000]') 
        
        # reflectance maxes at 0.6 for CS:GO
        #'$phong':                ('',    '',     '\n\tg_vReflectanceRange "[0.000 0.600]"\n')   
    }
}

def convertVmtToVmat(vmtKeyValList):

    vmatContent = ''

    for oldKey, oldVal in vmtKeyValList.items():

        #oldKey = oldKey.replace('$', '').lower()
        oldKey = oldKey.lower()
        oldVal = oldVal.strip().strip('"' + "'").strip(' \n\t"')
        outKey = outVal = outAdditionalLines = ''
        #print ( oldKey + " --->" + oldVal)
    
        for keyType in list(vmt_to_vmat):
            #vmtKeyList = vmt_to_vmat[keyType]
            for vmtKey, vmatItems in vmt_to_vmat[keyType].items():     
                
                if ( oldKey != vmtKey ):
                    continue

                vmatReplacement = vmatItems[VMAT_REPLACEMENT]
                vmatDefaultValue = vmatItems[VMAT_DEFAULT]
                vmatExtraLines = vmatItems[VMAT_EXTRALINES]
                if ( vmatReplacement and vmatDefaultValue ):
                    
                    outKey = vmatReplacement
                    
                    if (keyType == 'textures'):
                        outVal = 'materials/default/default' + vmatDefaultValue
                    else:
                        outVal = vmatDefaultValue
                    
                    outAdditionalLines = vmatExtraLines

                # no equivalent key-value for this key, only exists
                # add comment or ignore completely
                elif keyType ==  'transform':
                    pass

                elif (vmatExtraLines):
                    vmatContent += vmatExtraLines
                    break

                else:
                    #print('No replacement for %s. Skipping', vmtKey)
                    vmatContent += COMMENT + vmtKey
                    break


                if(keyType == 'textures'):
                    
                    if vmtKey == '$basetexture':

                        if '$newlayerblending' in vmtKeyValList or '$basetexture2' in vmtKeyValList:
                            #if vmatShader in (SH_VR_SIMPLE_2WAY_BLEND, 'xx'): 
                            outKey = vmatReplacement + 'A' # TextureColor -> TextureColorA
                            print("@ DBG: " + outKey + "<--- is noblend ok?")
                        
                        if vmatShader == SH_SKY:
                            outKey = 'SkyTexture'

                        outVal = formatNewTexturePath(oldVal, vmatDefaultValue, True)


                    elif vmtKey in ('$basetexture3', '$basetexture4'):
                        if USE_RETRO_SHADERS:
                            print('~ WARNING: Found 3/4-WayBlend but it is not supported.')
                            break


                    elif vmtKey in  ('$bumpmap', '$bumpmap2', '$normalmap', '$normalmap2'):
                        # all(k not in d for k in ('name', 'amount')) vmtKeyValList.keys() & ('newlayerblending', 'basetexture2', 'bumpmap2'): # >=
                        if (vmtKey != '$bumpmap2') and (vmatShader == SH_VR_SIMPLE_2WAY_BLEND or '$basetexture2' in vmtKeyValList):
                            outKey = vmatReplacement + 'A' # TextureNormal -> TextureNormalA
                        
                        # this is same as default_normal
                        #if oldVal == 'dev/flat_normal':
                        #    pass

                        if str(vmtKeyValList.get('$ssbump')).strip('"') == '1':
                            print('@ DBG: Found SSBUMP' + outVal)
                            outKey = COMMENT + '$SSBUMP' + '\n\t' + outKey
                            pass
                        #    
                        #    outKey = vmt_to_vmat['others2']['$ssbump'][VMAT_REPLACEMENT]
                        #    outAdditionalLines = vmt_to_vmat['others2']['$ssbump'][VMAT_EXTRALINES]

                        #    outVal = formatNewTexturePath(oldVal, vmt_to_vmat['others2']['$ssbump'][VMAT_DEFAULT], True)

                        #    
                        outVal = formatNewTexturePath(oldVal, vmatDefaultValue, True)

                    elif vmtKey == '$envmap':
                        if oldVal == 'env_cubemap':
                            if(vmtKeyValList.get('$envmaptint')):
                                outVal = fixIntVector(vmtKeyValList['$envmaptint'], True)
                            else:
                                vmatContent += '\t' + outAdditionalLines
                                break
                        
                        else:
                            # TODO: maybe make it real cubemap?
                            outAdditionalLines = 'F_SPECULAR 1\n\t'
                    
                    elif vmtKey == '$phong':
                        if oldVal == '0':
                            return
                        
                        #fixPhongRoughness(paramList = vmtKeyValList)

                        #if not vmtKeyValList.get('$basemapalphaphongmask'):
                            #outVal = createMaskFromChannel(getTexture(('$bumpmap', '$normalmap')), 'A', vmatDefaultValue, False)

                    
                    
                    
                    # TRY: invert for brushes, don't invert for models
                    #elif vmtKey == '$envmapmask':

                        # it's overriden with basealphaenvmapmask, why envmapmask then? 
                        #if vmtKeyValList.get('$basealphaenvmapmask'):
                        #    if vmtKeyValList['$basealphaenvmapmask'] != 0:
                        #        vmatContent += COMMENT + vmtKey
                        #        break

                        # create a non inverted one just in case
                        #createMaskFromChannel(oldVal, 'A', vmatDefaultValue, False)
                        # create inverted and set it
                        #outVal = createMaskFromChannel(oldVal, 'A', vmatDefaultValue, True)
                    
                    elif vmtKey == '$translucent' or vmtKey == '$alphatest':
                        if is_convertible_to_float(oldVal):
                            vmatContent += '\t' + outAdditionalLines

                            if vmtKey == '$alphatest':
                                sourceTexturePath = getTexture('$basetexture')
                                if sourceTexturePath:
                                    outVal = createMaskFromChannel(sourceTexturePath, 'A', vmatDefaultValue, True)
                            elif vmtKey == '$translucent':
                                outVal = fixIntVector(oldVal, True, 2)

                        # create a non inverted one just in case
                        #createMaskFromChannel(oldVal, 'A', vmatDefaultValue, False)
                        # create inverted and set it
                        else:
                            sourceTexturePath = formatNewTexturePath(oldVal, forReal=False)
                            outVal = createMaskFromChannel(sourceTexturePath, 'A', vmatDefaultValue, True) 

                    elif vmtKey == '$tintmasktexture':
                        sourceTexturePath = getTexture('$basetexture')
                        if sourceTexturePath:
                            outVal = createMaskFromChannel(sourceTexturePath, 'G', vmatDefaultValue, True)

                    elif vmtKey == '$aotexture':
                        outVal = createMaskFromChannel(oldVal, 'G', vmatDefaultValue, False)
                    
                    #### DEFAULT
                    else:
                        if oldVal == 'env_cubemap':
                            pass
                        if vmatShader == SH_SKY:
                            pass

                        outVal = formatNewTexturePath(oldVal, vmatDefaultValue, True)
                        
                        #outVal = formatNewTexturePath(oldVal, vmatDefaultValue, True)
                        

                
                elif(keyType == 'transform'):
                    if not vmatReplacement:
                        break

                    matrixList = listMatrix(oldVal)

                    ''' doesnt seem like there is rotation
                    if(matrixList[MATRIX_ROTATE] != '0.000'):
                        if(matrixList[MATRIX_ROTATIONCENTER] != '[0.500 0.500]')
                    '''
                    # scale 5 5 -> g_vTexCoordScale "[5.000 5.000]"
                    if(matrixList[MATRIX_SCALE] and matrixList[MATRIX_SCALE] != '[1.000 1.000]'):
                        vmatContent += '\t' + vmatReplacement + 'CoordScale' + '\t\t' + QUOTATION + matrixList[MATRIX_SCALE] + QUOTATION + '\n'
                    
                    # translate .5 2 -> g_vTexCoordScale "[0.500 2.000]"
                    if(matrixList[MATRIX_TRANSLATE] and matrixList[MATRIX_TRANSLATE] != '[0.000 0.000]'):    
                        vmatContent += '\t' + vmatReplacement + 'CoordOffset' + '\t\t' + QUOTATION + matrixList[MATRIX_TRANSLATE] + QUOTATION + '\n'
                    
                    break

                elif(keyType == 'settings'):
                    
                    if(vmtKey == '$detailscale'):
                        if '[' in oldVal:
                            # [10 10] -> [10.000000 10.000000]
                            outVal = fixIntVector(oldVal, False)
                        else:
                            # 10 -> [10.000000 10.000000]
                            outVal = fixIntVector(oldVal, False, 1)               
                
                   # TODO: test if its possible to drop oldVal as it is -raw-
                   # maybe it gets converted?
                    elif (vmtKey == '$surfaceprop'):
                        
                        if not oldVal:  surfacePropValue = vmatDefaultValue
                        else:
                            if oldVal in ('default', 'default_silent', 'no_decal', 'player', 'roller', 'weapon'):
                                surfacePropValue = oldVal

                            elif oldVal in surfacePropertiesNew:
                                surfacePropValue = surfacePropertiesNew[oldVal]  
                            
                            # lol
                            elif ("\\props\\" in vmatFileName):
                                surfacePropValue = 'prop.' + oldVal

                            # TODO: if 'world.'+oldVal exists
                            else:
                                surfacePropValue = 'world.' + oldVal       

                        vmatContent += '\n\t' + vmatReplacement + QUOTATION + surfacePropValue + QUOTATION + '\n\t}\n\n'
                        break

                    elif vmtKey == '$nofog':
                        
                        # 1 -> 0 and 0 -> 1
                        outVal = str(not int(oldVal))
                        
                        #if oldVal != '0':
                        #    outVal = '1'
                        #else:
                        #    outVal = '0'

                    elif vmtKey == '$selfillum':
                        
                        if oldVal == '0' or '$selfillummask' in vmtKeyValList:
                            break
                        
                        # should use reverse of the basetexture alpha channel as a self iluminating mask
                        # TextureSelfIlumMask "materials/*_selfilummask.tga"
                        sourceTexture = formatNewTexturePath(vmtKeyValList['$basetexture'], forReal=False)
                        outAdditionalLines \
                            = '\n\t' \
                            + vmt_to_vmat['textures']['selfillummask'][VMAT_REPLACEMENT] \
                            + '\t' \
                            + QUOTATION \
                            + createMaskFromChannel(sourceTexture, 'A', vmt_to_vmat['textures']['$selfillummask'][VMAT_DEFAULT], True ) \
                            + QUOTATION
                    
                    elif vmtKey in ("$color", '$color2', "$selfillumtint", '$layerbordertint'):
                        if oldVal:
                            outVal = fixIntVector(oldVal, True)
                    
                    # The other part are simple floats. Deal with them
                    else:
                        outVal = "{:.6f}".format(float(oldVal.strip(' \t"')))
                

                elif(keyType == 'alphamaps'):
                    
                    if not vmt_to_vmat['textures'].get(outVmtTexture):
                        print("@ DBG: Trying to extract map but the source is likely commented out?") 
                        break

                    outVmtTexture = vmt_to_vmat['alphamaps'][vmtKey][0]
                    sourceTexture = vmt_to_vmat['alphamaps'][vmtKey][1]
                    sourceChannel = vmt_to_vmat['alphamaps'][vmtKey][2]

                    outKey             = vmt_to_vmat['textures'][outVmtTexture][VMAT_REPLACEMENT]
                    outAdditionalLines = vmt_to_vmat['textures'][outVmtTexture][VMAT_EXTRALINES]
                    
                    sourceSubString    = vmt_to_vmat['textures'][outVmtTexture][VMAT_DEFAULT]
                    sourceTexturePath  = getTexture(sourceTexture)

                    if sourceTexturePath:
                        if vmtKeyValList.get(outVmtTexture):
                            print("~ WARNING: Conflicting " + vmtKey + " with " + outVmtTexture + ". Aborting mask creation (using original).")
                            break

                        outVal =  createMaskFromChannel(sourceTexturePath, sourceChannel, sourceSubString, False)
                        
                        # invert for brushes; if it's a model, keep the intact one ^
                        # both versions are provided just in case for 'non models'
                        #if not str(vmtKeyValList.get('$model')).strip('"') != '0':
                        #    outVal = createMaskFromChannel(sourceTexture, 'A', vmt_to_vmat['alphamaps']['$basealphaenvmapmask'][VMAT_DEFAULT], True )
                    else:
                        print("~ WARNING: Couldn't lookup texture from " + sourceTexture)
                        break


                # F_RENDER_BACKFACES 1 etc
                elif keyType == 'f_settings':
                    
                    if vmtKey in  ('$detailblendmode', '$decalblendmode'):
                        # https://developer.valvesoftware.com/wiki/$detail#Parameters_and_Effects
                        # materialsystem\stdshaders\BaseVSShader.h#L26

                        #Texture combining modes for combining base and detail/basetexture2
                        #Matches what's in common_ps_fxc.h
                        #define DETAIL_BLEND_MODE_RGB_EQUALS_BASE_x_DETAILx2				
                        #define DETAIL_BLEND_MODE_RGB_ADDITIVE								1	// Base.rgb+detail.rgb*fblend

                        #Texture combining modes for combining base and decal texture
                        #define DECAL_BLEND_MODE_DECAL_ALPHA								0	// Original mode ( = decalRGB*decalA + baseRGB*(1-decalA))
                        #define DECAL_BLEND_MODE_RGB_MOD1X									1	// baseRGB * decalRGB
                        #define DECAL_BLEND_MODE_NONE										2	// There is no decal texture
                        
                        if oldVal == '0':       outVal = '1' # Original mode (Mod2x)
                        elif oldVal == '1':     outVal = '2' # Base.rgb+detail.rgb*fblend 
                        #elif oldVal == '7':     outVal = 
                        elif oldVal == '12':    outVal = '0'
                        
                        else: outVal = '1'

                    vmatContent += '\t' + outKey + '\t\t' + outVal + '\n'  
                    continue
                
                elif keyType == 'others2':
                    if oldKey == '$ssbump': continue
                    vmatContent += '\t' + COMMENT + outKey + '\t\t' + QUOTATION + outVal + QUOTATION + '\n\t' + outAdditionalLines + '\n'
                    continue
                
                # g_bFogEnabled "1"
                if(outAdditionalLines):
                    vmatContent += '\n\t' + outAdditionalLines + '\n\t' + outKey + '\t\t' + QUOTATION + outVal + QUOTATION + '\n'
                else: 
                    vmatContent += '\t' + outKey + '\t\t' + QUOTATION + outVal + QUOTATION + '\n'

                ##print("DBG: " + oldKey + ' ' + oldVal + ' (' + vmatReplacement.replace('\t', '').replace('\n', '') + ' ' + vmatDefaultValue.replace('\t', '').replace('\n', '') + ') -------> ' + outKey + ' ' + outVal.replace('\t', '').replace('\n', '') + ' ' + outAdditionalLines.replace('\t', '').replace('\n', ''))
                print("@ DBG: " + oldKey + ' "' + oldVal + '" ---> ' + outKey + ' ' + outVal.replace('\t', '').replace('\n', '') + ' ' + outAdditionalLines.replace('\t', '').replace('\n', ''))

    return vmatContent
    


failures = []
# Main function, loop through every .vmt
x = 0
for fileName in fileList:
    x = x+1
    #if x > 100: quit()
    print('--------------------------------------------------------------------------------------------------------')
    print('+ Converting:  ' + fileName)
    vmtKeyValList = {}
    matType = ''
    validMaterial = False
    validPatch = False
    skipNextLine = False
    
    with open(fileName, 'r') as vmtFile:
        row = 0
        for line in vmtFile:
            
            line = line.strip()
            
            if not line or line.startswith('/'):
                continue
            
            #rawline = line.lower().replace('"', '').replace("'", "").replace("\n", "").replace("\t", "").replace("{", "").replace("}", "").replace(" ", "")/[^a-zA-Z]/
            if row < 1:
                matType = re.sub(r'[^A-Za-z0-9_-]', '', line).lower()
                #print(matType)
                if any(wd in matType for wd in materialTypes):
                    validMaterial = True
                
            if skipNextLine:
                if "]" in line or "}" in line:
                    skipNextLine = False
            else:
                parseVMTParameter(line, vmtKeyValList)
            
            if any(wd in line.lower() for wd in ignoreList):
                skipNextLine = True
            
            row += 1

    if matType == 'patch':
        includeFile = vmtKeyValList.get("include")
        if includeFile:
            includeFile = includeFile.replace('"', '').replace("'", '').strip()
            if includeFile == 'materials\\models\\weapons\\customization\\paints\\master.vmt':
                continue

            print("+ Patching material details from include: " + includeFile +'\n')
            try:
                with open(formatFullDir(includeFile), 'r') as vmtFile:
                    oldVmtKeyValList = vmtKeyValList.copy()
                    vmtKeyValList.clear()
                    for line in vmtFile.readlines():
                        if any(wd in line.lower() for wd in materialTypes):
                            print('+ Valid patch')
                            validPatch = True

                        parseVMTParameter(line, vmtKeyValList)
                    
                    vmtKeyValList.update(oldVmtKeyValList)
            
            except FileNotFoundError:
                failures.append(includeFile)
                print("~ WARNING: Couldn't find include file from patch. Skipping!")
                continue
                    
            if not validPatch:
                print("+ Include file is not a recognised material. Shader will be black by default.")
                # matType = 
                #continue
        else:
            print("~ WARNING: No include was provided on material with type 'Patch'. Is it a weapon skin?")
        
    
    skyboxName = os.path.basename(fileName).replace(".vmt", '')#[-2:]
    
    if('\\skybox\\' in fileName or '/skybox/' in fileName):
        faceTransform = vmtKeyValList.get('$basetexturetransform')
        if(faceTransform):
            transformMatrix = listMatrix(faceTransform)
            if(transformMatrix[MATRIX_ROTATE]):
                skybox[skyboxName[-2:]]['rotate'] = int(float(transformMatrix[MATRIX_ROTATE]))
        
        # Since we go through files alphabetically, we expect the last face to get processed to be 'up'
        # This is necessary since we need the rotation information for all the 6 faces. (why the fuck do you have to rotate a fucking sky face, baggage?)
        # Now begin building the sky cubemap 
        if(skyboxName[-2:] == 'up'):
            buildS2SkyCubemap(fileName)

    if validMaterial:
        vmatFileName = fileName.replace('.vmt', '') + '.vmat'
        if os.path.exists(vmatFileName) and not OVERWRITE_VMAT:
            print('+ File already exists. Skipping!')
            continue
        
        vmatShader = chooseShader(matType, vmtKeyValList, fileName)

        with open(vmatFileName, 'w') as vmatFile:
            vmatFile.write('// Converted with vmt_to_vmat.py\n')
            vmatFile.write('// From: ' + fileName + '\n\n')
            vmatFile.write('Layer0\n{\n\tshader "' + vmatShader + '.vfx"\n\n')
        
            print("@ DBG: Mattype: " + matType)

            
            vmatFile.write(convertVmtToVmat(vmtKeyValList)) ###############################        
            
            #check if base texture is empty
            #if "metal" in vmatFileName:
            #    vmatFile.write("\tg_flMetalness 1.000\n")
            
                    
            vmatFile.write('}\n')
            
        #with open(fileName) as f:
        #    with open(vmatFileName, "w") as f1:
        #        for line in f:
        #            f1.write(COMMENT + line)
        print ('+ Converted: ' + fileName)
        print ('+ Saved at:  ' + vmatFileName)
        print(matType)
        print ('--------------------------------------------------------------------------------------------------------')
    
    bumpmapConvertedList = formatFullDir("convertedfiles.txt")
    if not os.path.exists(bumpmapConvertedList):
        print('ERROR: Please create an empty text file named "convertedfiles.txt" in the root of the mod (i.e. content/steamtours_addons/hl2/materials)')
        print('Should go in here: ' + PATH_TO_NEW_CONTENT_ROOT)
        quit()
    
    ''' flip the green channels of any normal maps
    if(bumpmapPath != ""):
        #print("Checking if normal file " + bumpmapPath + " has been converted:")
        foundMaterial = False
        with open(bumpmapConvertedList, 'r+') as bumpList: #change the read type to write
            for line in bumpList.readlines():
                if line.rstrip() == bumpmapPath.rstrip():
                    foundMaterial = True
        
            if not foundMaterial:
                flipNormalMap(formatNewTexturePath(bumpmapPath).strip("'" + '"'))
                #print("flipped normal map of " + bumpmapPath)
                #append bumpmapPath to bumpmapCovertedList
                bumpList.write(bumpmapPath + "\n")
                bumpList.close() '''



    #cube.py --size 1024 --type tga --onefile input --dir
# TODO: reparse the vmt, see i.e. if alphatest, then TextureTranslucency "path/to/tex/name_alpha.tga",
# basemap alpha can either be a transparency mask, selfillum mask, or specular mask
# normalmap alpha can be a phong mask by default

# if $translucent/$alphatest
	# TextureTranslucency "path/to/tex/basetexture_alpha.tga"
# if $rimlight/$phong in vmt
	# if $basemapalphaphongmask in vmt
		#TextureRimMask/TextureSpecularMask "path/to/tex/basetexture_alpha.tga"
	# else
		#TextureRimMask/TextureSpecularMask "path/to/tex/bumpmap_alpha.tga"
# if $selfillum in vmt
	# Add Mask 1
	# TextureSelfIllumMask "path/to/tex/basetexture_alpha.tga"

# input("\nDone, press ENTER to continue...")
if len(failures) > 0:
    #print()
    #print()
    #print("ERROR: Couldn't convert everything as certain referenced materials are missing.")
    #print("Please check base game (HL2, Counter-Strike: Source, etc) materials folders for the following files and copy them to 'convertme' folder (retaining their path)")
    for failure in failures:
        print(failure)
