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
# python vmt_to_vmat.py MODNAME OPTIONAL_PATH_TO_FOLDER

import sys
import os
import os.path
from os import path
import shutil
from shutil import copyfile
import re
from PIL import Image
import PIL.ImageOps

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
SH_VR_BASC = 'vr_basic'
SH_VR_SIMPLE = 'vr_simple'
SH_VR_COMPLEX = 'vr_complex'
SH_VR_STANDARD = 'vr_standard'
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
    SH_VR_SIMPLE: 0,
    SH_VR_COMPLEX: 0,
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
        print(matType)
        print("DBGGGG: NOT IN ")
        return max(shaders, key = shaders.get) 

    #TRY: if containts values starting with _rt_ give some empty shader

    shaders[SH_VR_BLACK_UNLIT] = 0
    shaders[materialTypes[matType]] += 1
    
    # sky shader matches
    if matType == "sky":
        return SH_SKY

    elif matType == "unlitgeneric":
        shaders[SH_SKY] += 1
        shaders[SH_GENERIC] += 1
        
        if "nofog" in vmtKeyValList or "ignorez" in vmtKeyValList:
            shaders[SH_SKY] += 2
        if "receiveflashlight" in vmtKeyValList:
            shaders[SH_SKY] -= 3

    elif matType == "eyes" or matType == "eyeball":
        return shaders[SH_VR_EYEBALL]
    
    elif matType == "":
        pass
    
    elif matType == "":
        pass
    
    elif matType == "":
        pass
    
    elif matType == "":
        pass
    
    elif matType == "":
        pass
    
    elif matType == "":
        pass
    
    elif matType == "":
        pass
    
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
    #"lightmapped_4wayblend",
    #, #TODO: make this system functional
    #"modulate",
}
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

QUOTATION = '"'
COMMENT = "// "
skyboxfaces = ['up','dn', 'lf', 'rt', 'bk', 'ft']


def parseDir(dirName):
    files = []
    for root, dirs, fileNames in os.walk(dirName):
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
        print("here: " + PATH_TO_CONTENT_ROOT)
        while not PATH_TO_CONTENT_ROOT:
            c = input('Enter the root directory of the old materials or enter nothing to read from the current directory ('+ currentDir + '): ') or currentDir
            if not path.isdir(c):
                print('Not a directory')
                continue
            PATH_TO_CONTENT_ROOT = c.lower().strip().strip('"')
            print(PATH_TO_CONTENT_ROOT)

if not PATH_TO_NEW_CONTENT_ROOT:
    if(len(sys.argv) >= 3):
        PATH_TO_NEW_CONTENT_ROOT = sys.argv[2]
    else:
        while not PATH_TO_NEW_CONTENT_ROOT:
            c = input('Type your new materials\' directory or enter to create the files on the same dir ('+ PATH_TO_CONTENT_ROOT + '): ') or currentDir
            if(c == currentDir):
                PATH_TO_NEW_CONTENT_ROOT = PATH_TO_CONTENT_ROOT # currentDir
            else:
                if not path.isdir(c):
                    print('Not a directory')
                    continue
                PATH_TO_NEW_CONTENT_ROOT = c.lower().strip().strip('"')

PATH_TO_CONTENT_ROOT = os.path.normpath(PATH_TO_CONTENT_ROOT) + '\\'
PATH_TO_NEW_CONTENT_ROOT =  os.path.normpath(PATH_TO_NEW_CONTENT_ROOT) + '\\'

print('+ Reading old materials from: ' + PATH_TO_CONTENT_ROOT)
print('+ Creating new materials in: ' + PATH_TO_NEW_CONTENT_ROOT)

print('Source 2 Material Conveter! By Rectus via Github.')
print('Initially forked by Alpyne, this version by caseytube.')
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

# C:/Users/User/Desktop/stuff/materials/texture_color.tga -> materials/texture_color.tga
def formatVmatDir(localPath):
    localPath = os.path.normpath(localPath)
    return localPath.replace(PATH_TO_CONTENT_ROOT, '')

# -------------------------------
# Returns texture path of given vmtParam, texture which has likely been renamed to be S2 naming compatible
# $basetexture  ->  /path/to/texture_color.tga of the TextureColor
# -------------------------------
def getTexture(vmtParam):
    if isinstance(vmtParam, tuple):
        for actualParam in vmtParam:
            if vmtKeyValList.get(actualParam):
                return formatNewTexturePath(vmtKeyValList[actualParam], vmt_to_vmat['textures'][actualParam][VMAT_DEFAULT], forReal=False)

    elif vmtKeyValList.get(vmtParam):
        return formatNewTexturePath(vmtKeyValList[vmtParam], vmt_to_vmat['textures'][vmtParam][VMAT_DEFAULT], forReal=False)
    
    return None

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
    if textureAddTag(textureLocal, textureType) == textureLocal:
        print("DOING THISSSSSSSSSSSSSSSSSS")
        renameTexture = False
        return formatVmatDir(textureLocal + textureType[-4:])

    #if textureLocal.endswith(textureType[:-4]):
    #    renameTexture = False
    #    return formatVmatDir(textureLocal + textureType[-4:])

    if not forReal:
        newVmatFormattedTexture = formatVmatDir(textureLocal + textureType)
        print("MAYBE HERE:? " + newVmatFormattedTexture)
    
    # materials/newde_cache/nc_corrugated -> materials/newde_cache/nc_corrugated_color.tga
    if renameTexture:
        #if forReal:
        newVmatFormattedTexture = formatVmatDir(textureRename(textureLocal, textureLocal + textureType))
        #else:
            #newVmatFormattedTexture = formatVmatDir(textureLocal + textureType)
            #print("MAYBE HERE:? " + newVmatFormattedTexture)
    else:
        newVmatFormattedTexture = formatVmatDir(textureLocal + textureType)

    #print(newVmatFormattedTexture)
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
        print("+ Using already renamed texture: " + formatVmatDir(newNamePath))
    #elif not os.path.exists(localPath):
    #    print("+ Missing texture " + formatVmatDir(localPath) + " queued for rename into: " + formatVmatDir(newNamePath))
    #    print("+ Please find it and rename it accordingly or the material won't load")
        return newNamePath
    
    if not os.path.exists(localPath):
        print("+ Could not find texture " + formatVmatDir(localPath) + " queued for rename into: " + formatVmatDir(newNamePath))
        for key in list(vmt_to_vmat['textures']):
            if os.path.exists(localPath[:-4] + vmt_to_vmat['textures'][key][VMAT_DEFAULT]):
                makeCopy = True
                localPath = localPath[:-4] + vmt_to_vmat['textures'][key][VMAT_DEFAULT]
                print("+ Nevermind... found renamed copy! " + formatVmatDir(localPath))
                print("+ However, we should'nt have had to search for it anyway. Material likely using same texture for more than one map")
                break
        
        if not os.path.exists(localPath):
            print("+ Please find it and rename it accordingly or the material won't load")
            return newNamePath

    try:
        if not makeCopy:
            os.rename(localPath, newNamePath)
            print("+ Renamed new texture to " + formatVmatDir(localPath))
        else:
            copyfile(localPath, newNamePath)
            print("+ Copied new texture to " + formatVmatDir(localPath))
        
    
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
    #print(PATH_TO_CONTENT_ROOT)
    
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
        #-words = re.split(r'\s+', line, 2)
        words = re.split(r'\s+', line, 2)
    else:
        words = re.split(r'\s+', line, 1)
        
    words = list(filter(len, words))
    if len(words) < 2:
        #print("Cannot read -> " + str(words))
        return 
    
    key = words[0].strip('"').lower()
    
    # "GPU>=2?$detailtexture"
    if '?' in key:
        print("~ WARNING: Might not process well materials that have GPU-setting based parameters. Please manually check.")
        #key = key.split('?')[1].lower()
        key.split('?')
        if key[0] == 'GPU>=2':
            key = key[2].lower()
        else:
            print("~ WARNING: Might not process well materials that have GPU-setting based parameters. Please manually check.")
            if key[0] == 'GPU<2':
                return
            key = key[2].lower()
    if key.startswith('/'):
        return
    
    if not key.startswith('$'):
        if not key.startswith('include'):
            return

    val = words[1].strip('\n').lower()
    
    # remove comments, HACK
    commentTuple = val.partition('//')
    
    #if(val.strip('"' + "'") == ""):
    #    print("+ No value found, moving on")
    #    return
    
    if not commentTuple[0] in parameters:
        parameters[key] = commentTuple[0]


def createMaskFromChannel(vmtTexture, channel = 'A', copySub = '_mask.tga', invert = True):
    if not os.path.exists(vmtTexture):
        vmtTexture = formatFullDir(vmtTexture)
    print ("HERE: " + vmtTexture)
    if invert:  alphapath = vmtTexture[:-4] + '_' + 'inverted-' + channel + copySub
    else:       alphapath = vmtTexture[:-4] + '_'               + channel + copySub
    print ("TO: " + alphapath)
    
    if os.path.exists(alphapath):
        print("+ Alpha mask already exists: " + alphapath)
        return formatVmatDir(alphapath)
    
    print("+ Attempting to extract alpha from " + vmtTexture)
    if os.path.exists(vmtTexture):
        # Open the image and convert it to RGBA, just in case it was indexed
        image = Image.open(vmtTexture).convert('RGBA')

        # Extract just the alpha channel
        #alpha = image.split()[-1]
        # Unfortunately the alpha channel is still treated as such and can't be dumped
        # as-is

        imgChannel = image.getchannel(str(channel))

        # Create a new image with an opaque black background
        bg = Image.new("RGBA", image.size, (0,0,0,255))

        # Copy the alpha channel to the new image using itself as the mask
        bg.paste(imgChannel)
        
        if invert:
            r,g,b,a = bg.split()
            rgb_image = Image.merge('RGB', (r,g,b))
            inverted_image = PIL.ImageOps.invert(rgb_image)

            r2,g2,b2 = inverted_image.split()

            final_transparent_image = Image.merge('RGB', (r2,g2,b2))
            
            final_transparent_image.save(alphapath)
            final_transparent_image.close()
        else:
            bg.save(alphapath)
            bg.close()
            print("Saved mask to" + formatVmatDir(alphapath))
    else:
        print("Couldn't find requested image. Please update")
        return 'materials/default/default_mask.tga'

    print('+++++ ' + formatVmatDir(alphapath))
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


def buildS2CompatibleSkybox(vmatFileName):
    #vmatFileName.replace('up.vmt', '.vmat').replace('dn.vmt', '.vmat').replace('lf.vmt', '.vmat').replace('rt.vmt', '.vmat').replace('bk.vmt', '.vmat').replace('ft.vmt', '.vmat')
    #TODO
    print("Grab the")
    print('up, dn, lf, rt, bk, ft .vmt files of the' + vmatFileName[:-6])
    print("and edit them into a proper _cube.PFM cubemap")

    return 'nukeblank.pfm'

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
    
    # "4" -> [4.000000 4.000000]
    if(replicateSingle and likelySingle and len(originalValueList) <= 1):
        for _ in range(replicateSingle):
            originalValueList.append(originalValueList[0])
    
    # 255 175 255 -> [255 175 255 1.000]
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


MATRIX_ROTATIONCENTER = 0
MATRIX_SCALE = 1
MATRIX_ROTATE = 2
MATRIX_TRANSLATE = 3

def is_convertible_to_float(value):
  try:
    float(value)
    return True
  except:
    return False

def listMatrix(s):
    # [0, 1] center defines the point of rotation. Only useful if rotate is being used.
    # [2, 3] scale fits the texture into the material the given number of times. '2 1' is a 50% scale in the X axis.
    # [4]    rotate rotates the texture counter-clockwise in degrees. Accepts any number, including negatives.
    # [5, 6] translate shifts the texture by the given numbers. '.5' will shift it half-way.

    # Assuming you can't use these individually as "rotate 4" /// welp you can
    # $detailtexturetransform "center .5 .5 scale 1 1 rotate 0 translate 0 0"
    # -> [0.5, 0.5, 1.0, 1.0, 0.0, 0.0, 0.0]
    s = s.strip('"')
    valueList = [float(str(i)) for i in s.split(' ') if is_convertible_to_float(i)]

    # -> [  '[0.5 0.5]', '[1.0 1.0]', '0.0', '[0.0 0.0]'    ]
    return ['[' + "{:.3f}".format(valueList[0]) + ' ' + "{:.3f}".format(valueList[1]) + ']',\
            '[' + "{:.3f}".format(valueList[2]) + ' ' + "{:.3f}".format(valueList[3]) + ']',\
                  "{:.3f}".format(valueList[4]),\
            '[' + "{:.3f}".format(valueList[5]) + ' ' + "{:.3f}".format(valueList[6]) + ']'\
            ]

# NEWLAYERBLENDING
#   $BLENDSOFTNESS	0.05  
# 	$LAYERBORDERSTRENGTH	.25
# 	$LAYERBORDEROFFSET	0
# 	$LAYERBORDERSOFTNESS	.1
#   $LAYERBORDERTINT	"{150 200 1}"



vmt_to_vmat = {
    'textures': {
        # SkyTexture

        '$hdrcompressedTexture': ('SkyTexture',          '_cube.pfm',        ''),
        '$basetexture':          ('TextureColor',        '_color.tga',       ''),
        '$painttexture':         ('TextureColor',        '_color.tga',       ''),
        'basetexture2':          ('TextureColorB',       '_color.tga',       ''),
        '$texture2':             ('TextureColorB',       '_color.tga',       ''),
        '$bumpmap':              ('TextureNormal',       '_normal.tga',      ''),
        '$bumpmap2':             ('TextureNormalB',      '_normal.tga',      ''),
        '$normalmap':            ('TextureNormal',       '_normal.tga',      ''),
        '$normalmap2':           ('TextureNormal2',      '_normal.tga',      'F_SECONDARY_NORMAL 1'), # used with refract shader
        '$flowmap':              ('TextureFlow',         '.tga',             'F_FLOW_NORMALS 1\n\tF_FLOW_DEBUG 1'),
        '$flow_noise_texture':   ('TextureNoise',        '_noise.tga',       'F_FLOW_NORMALS 1\n\tF_FLOW_DEBUG 2'),
        '$blendmodulatetexture': ('TextureMask',         '_mask.tga',        'F_BLEND 1\n\tF_BLEND_NORMALS 1'), # TextureLayer1RevealMask
        '$detail':               ('TextureDetail',       '_detail.tga',      'F_DETAIL_TEXTURE 1\n'),
        #'$detail2':              ('TextureDetail',       '_detail.tga',      'F_DETAIL_TEXTURE 1\n'),
        '$tintmasktexture':      ('TextureTintMask',     '_mask.tga',        'F_TINT_MASK 1'), # GREEN CHANNEL ONLY, RED IS FOR $envmapmaskintintmasktexture 1
        '$selfillummask':        ('TextureSelfIllumMask','_selfillummask.tga',''), # $blendtintbybasealpha 1 
        '$envmap':               ('TextureCubeMap',      '_cube.pfm',        'F_SPECULAR 1\n\tF_SPECULAR_CUBE_MAP 1\n\tF_SPECULAR_CUBE_MAP_PROJECTION 1\n\tg_flCubeMapBlurAmount "1.000"\n\tg_flCubeMapScalar "1.000"\n\tg_vReflectanceRange "[0.000 0.600]"\n'),
        '$envmapmask':           ('TextureReflectance',  '_refl.tga',        ''),  # '_rough.tga' TextureRoughness selfillum_envmapmask_alpha envmapmaskintintmasktexture 
        #'$phongexponenttexture': ('TextureGlossiness',   '_gloss.tga',        'F_ANISOTROPIC_GLOSS 1\n'), # = 'basemapalphaphongmask':('TextureReflectance',  '_trans.tga',        ''), # 'refl.tga'
        '$phongexponenttexture': ('TextureRoughness',   '_rough.tga',        ''), # nah not really.
        #('TextureTintTexture',)
        
        # These have no separate masks
        '$translucent':          ('TextureTranslucency', '_trans.tga',        'F_TRANSLUCENT 1\n'), # g_flOpacityScale "1.000"
        '$alphatest':            ('TextureTranslucency', '_trans.tga',        'F_ALPHA_TEST 1\n'),
        '$aotexture':            ('TextureAmbientOcclusion', '_ao.tga',       'g_flAmbientOcclusionDirectSpecular "1.000"\n\tF_AMBIENT_OCCLUSION_TEXTURE 1\n'),
        '$ambientoccltexture':   ('TextureAmbientOcclusion', '_ao.tga',       'g_flAmbientOcclusionDirectSpecular "1.000"\n\tF_AMBIENT_OCCLUSION_TEXTURE 1\n'),
        '$ambientocclusiontexture':('TextureAmbientOcclusion', '_ao.tga',     'g_flAmbientOcclusionDirectSpecular "1.000"\n\tF_AMBIENT_OCCLUSION_TEXTURE 1\n')
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
        '$detailscale':          ('g_vDetailTexCoordScale', '[1.000 1.000]', ''),
        '$detailblendfactor':    ('g_flDetailBlendFactor', '1.000',            ''),
        '$selfillumtint':        ('g_vSelfIllumTint', '[1.000 1.000 1.000 0.000]', ''),
        '$selfillumscale':       ('g_flSelfIllumScale', '1.000', ''),
        
        #Assumes env_cubemap
        '$envmaptint':           ('TextureReflectance',      '[1.000 1.000 1.000 0.000]', ''),

        '$color':                ('g_vColorTint',            '[1.000 1.000 1.000 0.000]', ''),
        '$color2':               ('g_vColorTint',            '[1.000 1.000 1.000 0.000]', ''),
        
        # questionable
        '$blendtintcoloroverbase':('g_flModelTintAmount', '1.000', ''),

        '$surfaceprop':          ('SystemAttributes\n\t{\n\t\tPhysicsSurfaceProperties\t', 'world.concrete', ''),
        
        '$alpha':                ('g_flOpacityScale', '1.000', ''),
        '$alphatestreference':   ('g_flAlphaTestReference', '0.500', ''),
        
        # opposite
        '$nofog':                ('g_bFogEnabled', '0', ''),

        '$refractamount':        ('g_flRefractScale', '0.200', ''),
        '$flow_worlduvscale':    ('g_flWorldUvScale', '1.000', ''),
        '$flow_noise_scale':     ('g_flNoiseUvScale', '0.010', ''),

        # These only exist on vr_standard.vfx shader of SteamVR, but they match the $NEWLAYERBLENDING settings used on dust2 
        '$blendsoftness':        ('g_flLayer1BlendSoftness', '1.000', ''),
        '$layerborderstrenth':   ('g_flLayer1BorderStrength', '1.000', ''),
        '$layerborderoffset':    ('g_flLayer1BorderOffset', '1.000', ''),
        '$layerbordersoftness':  ('g_flLayer1BorderSoftness', '1.000', ''),
        '$layerbordertint':      ('g_vLayer1BorderColor', '[1.000000 1.000000 1.000000 0.000000]', ''),
        
        #'LAYERBORDERSOFTNESS':  ('g_flLayer1BorderSoftness', '1.0', ''),
        #rimlight
          
    },

    'f_settings': {
        '$selfillum':            ('F_SELF_ILLUM',        '1', ''),
        '$additive':             ('F_ADDITIVE_BLEND',    '1', ''),
        '$nocull':               ('F_RENDER_BACKFACES',  '1', ''),
        '$decal':                ('F_OVERLAY',           '1', ''),
        '$flow_debug':           ('F_FLOW_DEBUG',        '0', ''),
        #'$detailblendmode':      ('F_DETAIL_TEXTURE',    '1', '') # not 1 to 1
    },

    'alphamaps': {
        '$basealphaenvmapmask':         ('TextureReflectance',  '_refl.tga',            '$basetexture', 'A'),
        '$normalmapalphaenvmapmask':    ('TextureReflectance',  '_refl.tga',            ('$normal', '$bumpmap', '$bumpmap2'),      'A'), 
        '$envmapmaskintintmasktexture': ('TextureReflectance',  '_refl.tga',            '$tintmask',    'R'),
        '$basemapalphaphongmask':       ('TextureRoughness',    '_rough.tga',           '$basetexture', 'A'),
        '$blendtintbybasealpha':        ('TextureTintMask',     '_mask.tga',            '$basetexture', 'A'),
        '$selfillum_envmapmask_alpha':  ('TextureSelfIllumMask','_selfillummask.tga',   '$envmap',      'A')
    },

    
    # no direct replacement
    'others2': {
        '$ssbump':               ('TextureBentNormal',    '_bentnormal.tga', '\n\tF_ENABLE_NORMAL_SELF_SHADOW 1\n\tF_USE_BENT_NORMALS 1\n'),
        '$newlayerblending':     ('',    '',     ''),

        # $selfillumfresnelminmaxexp "[1.1 1.7 1.9]"
        #'$selfillum_envmapmask_alpha':     ('',    '',     ''),

        #'$envmapmaskintintmasktexture':     ('',    '',     ''),
        
        '$phong':                ('',    '',     '\n\tg_vReflectanceRange "[0.000 0.600]"\n')   
    }
}

'''
    F_ADVANCED_FRESNEL_CONTROLS 1
    //---- Lighting ----
	g_flFresnelExponent "5.000"
	g_vFresnelFacingRange "[0.000 1.000]"
	g_vGlossinessRange "[0.000 1.000]"
	g_vMetalnessRange "[0.000 1.000]"
	g_vReflectanceRange "[0.000 1.000]"
	TextureFresnelFacing "materials/default/default_fresnel.tga"
	TextureGlossiness "materials/default/default_gloss.tga"
	TextureMetalness "materials/default/default_metal.tga"
	TextureReflectance "materials/default/default_refl.tga"

    F_TREE_ANIMATION 1
    //---- Foliage Animation ----
	g_flBendScale "0.100"
	g_flBranchAmp "1.000"
	g_flBranchFrequency "1.000"
	g_flDetailAmp "1.000"
	g_flDetailFrequency "1.000"
	g_flWindAngle "0.000"
	g_flWindSpeed "1.000"
	
    //---- 2-Sided Rendering ----
	F_RENDER_BACKFACES 1
	F_TRANSMISSIVE_SUNLIGHT 1
	F_TRANSMISSIVE_THICKNESS 1
    //---- Two-Sided Rendering ----
	g_flTransmissiveColorBoost "1.000"
	g_flTransmissiveSoftness "0.3"
	g_vTransmissiveColorTint "[1.000000 1.000000 1.000000 0.000000]"
'''
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
                    print('No replacement for %s. Skipping', vmtKey)
                    vmatContent += COMMENT + vmtKey
                    break


                if(keyType == 'textures'):
                    if vmtKey == '$basetexture':

                        if '$newlayerblending' in vmtKeyValList or '$basetexture2' in vmtKeyValList or '$bumpmap2' in vmtKeyValList or '$texture2' in vmtKeyValList:
                            #if vmatShader in (SH_VR_SIMPLE_2WAY_BLEND, 'xx'): 
                            outKey = vmatReplacement + 'A' # TextureColor -> TextureColorA
                            print (outKey + "<--- is noblend ok?")
                        
                        if vmatShader == SH_SKY:
                            outKey = 'SkyTexture'

                        outVal = formatNewTexturePath(oldVal, vmatDefaultValue, True)

                    elif vmtKey in  ('$bumpmap', '$bumpmap2', '$normalmap', '$normalmap2'):
                        # all(k not in d for k in ('name', 'amount')) vmtKeyValList.keys() & ('newlayerblending', 'basetexture2', 'bumpmap2'): # >=
                        #if vmtKey not in ('$bumpmap2', '$normalmap2') and vmatShader in (SH_VR_SIMPLE_2WAY_BLEND, 'xx'):
                        #    outKey = vmatReplacement + 'A' # TextureNormal -> TextureNormalA
                        
                        # this is same as default_normal
                        #if oldVal == 'dev/flat_normal':
                        #    pass

                        if str(vmtKeyValList.get('$ssbump')).strip('"') == '1':
                            print('Found SSBUMP' + outVal)
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
                        if oldVal.isdigit():
                            vmatContent += '\t' + outAdditionalLines

                            if vmtKey == '$alphatest':
                                sourceTexture = getTexture('$basetexture')
                                if sourceTexture:
                                    outVal = createMaskFromChannel(sourceTexture, 'A', vmatDefaultValue, True)
                            break
                        # create a non inverted one just in case
                        #createMaskFromChannel(oldVal, 'A', vmatDefaultValue, False)
                        # create inverted and set it
                        sourceTexture = formatNewTexturePath(oldVal, forReal=False)
                        outVal = createMaskFromChannel(sourceTexture, 'A', vmatDefaultValue, True) 

                    elif vmtKey == '$tintmasktexture':
                        sourceTexture = getTexture('$basetexture')
                        if sourceTexture:
                            outVal = createMaskFromChannel(sourceTexture, 'G', vmatDefaultValue, True)

                    
                    
                    #### DEFAULT
                    else:
                        if oldVal == 'env_cubemap':
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
                
                    elif (vmtKey == '$surfaceprop'):
                        
                        if oldVal:  vmatContent += '\n\t' + vmatReplacement + QUOTATION +'world.' + oldVal + QUOTATION + '\n\t}\n\n'
                        else:       vmatContent += '\n\t' + vmatReplacement + QUOTATION + vmatDefaultValue + QUOTATION + '\n\t}\n\n'
                        
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
                    
                    elif vmtKey in ("$color", '$color2', "$selfillumtint", '$envmaptint', '$layerbordertint'):
                        
                        if((vmtKey == '$envmaptint') and (vmtKeyValList.get('$envmapmask') or vmtKeyValList.get('$basealphaenvmapmask') or vmtKeyValList.get('$normalmapalphaenvmapmask'))):
                            print("~ WARNING: Conflicting $envmapmask/$basealphaenvmapmask/$normalmapalphaenvmapmask with $envmaptint")
                            break

                        if oldVal:
                            outVal = fixIntVector(oldVal, True)
                    
                    # The other part are simple floats. Deal with them
                    else:
                        outVal = "{:.6f}".format(float(oldVal.strip(' \t"')))
                

                elif(keyType == 'alphamaps'):
                    
                    #sourceKey = vmt_to_vmat['alphamaps'][vmtKey][VMAT_EXTRALINES]
                    #sourceTexture = formatNewTexturePath(vmtKeyValList[sourceKey], vmt_to_vmat['textures'][sourceKey][VMAT_DEFAULT], True, False) # sth liek thi
                    #alphaTextureTag = vmt_to_vmat['alphamaps'][vmtKey][VMAT_DEFAULT]
                    
                    print('- ALPHAMAPS ' + vmtKey)
                    print(vmatExtraLines)
                    sourceTexture = getTexture(vmatExtraLines)
                    if sourceTexture:
                        outVal =  createMaskFromChannel(sourceTexture, vmatItems[3], vmt_to_vmat['alphamaps'][vmtKey][VMAT_DEFAULT], False)
                        print('THIS OWRKS???????? ' + outVal )
                    else:
                        print("~ WARNING: Couldn't find a texture from " + vmatExtraLines)
                    outAdditionalLines = ''
                    if vmtKey ==  '$envmapmaskintintmasktexture':
                        outAdditionalLines = 'F_TINT_MASK 1'
                    
                    '''if vmtKey == '$basealphaenvmapmask':
                        
                        sourceTexture = formatFullDir(formatNewTexturePath(vmtKeyValList['$basetexture'], vmt_to_vmat['textures']['$basetexture'][VMAT_DEFAULT], True, False))
                        
                        outVal = createMaskFromChannel(sourceTexture, 'A', vmt_to_vmat['alphamaps']['$basealphaenvmapmask'][VMAT_DEFAULT], False )
                        
                        # invert for brushes; if it's a model, keep the intact one ^
                        # both versions are provided just in case for 'non models'
                        if not str(vmtKeyValList.get('$model')).strip('"') != '0':
                            outVal = createMaskFromChannel(sourceTexture, 'A', vmt_to_vmat['alphamaps']['$basealphaenvmapmask'][VMAT_DEFAULT], True )
                            

                    elif vmtKey == '$normalmapalphaenvmapmask':
                        print(vmtKeyValList)
                        normalMap = ''
                        if vmtKeyValList.get('$normalmap'):
                            normalMap = str(vmtKeyValList.get('$normalmap'))
                        elif vmtKeyValList.get('$bumpmap'):
                            normalMap = str(vmtKeyValList.get('$bumpmap'))
                        
                        if not normalMap:
                            outVal = 'materials/default/default' + vmt_to_vmat['textures']['$normalmap'][VMAT_DEFAULT]
                        else:
                            if str(vmtKeyValList.get('$ssbump')).strip('"') == '1':
                                sourceTexture = formatFullDir(formatNewTexturePath(normalMap, TEXTURE_FILEEXT, True, False))
                            else:
                                sourceTexture = formatFullDir(formatNewTexturePath(normalMap, vmt_to_vmat['textures']['$normalmap'][VMAT_DEFAULT], True, False))
                            
                            print('+++++++' + sourceTexture)
                        #if str(vmtKeyValList.get('$ssbump')).strip('"') == '1':
                        #    normalMapTypeSubString =  vmt_to_vmat['others2']['ssbump'][VMAT_DEFAULT]
                        
                            outVal = createMaskFromChannel(sourceTexture, 'A', vmt_to_vmat['alphamaps']['$normalmapalphaenvmapmask'][VMAT_DEFAULT], True )
                    
                    elif vmtKey ==  '$envmapmaskintintmasktexture':
                        sourceTexture = formatFullDir(formatNewTexturePath(vmtKeyValList['$tintmasktexture'], vmt_to_vmat['textures']['$normalmap'][VMAT_DEFAULT], True, False))
                        outVal = createMaskFromChannel(sourceTexture, 'R', vmt_to_vmat['alphamaps']['envmapmaskintintmasktexture'][VMAT_DEFAULT], True)
                        outAdditionalLines = 'F_TINT_MASK 1'

                    elif vmtKey ==  '$basemapalphaphongmask':
                        sourceTexture = formatFullDir(formatNewTexturePath(vmtKeyValList['$basetexture'], vmt_to_vmat['textures']['$normalmap'][VMAT_DEFAULT], True, False))
                        outVal = createMaskFromChannel(sourceTexture, 'A', vmt_to_vmat['alphamaps']['basemapalphaphongmask'][VMAT_DEFAULT], True)

                    elif vmtKey ==  '$blendtintbybasealpha':
                        sourceTexture = formatFullDir(formatNewTexturePath(vmtKeyValList['$basetexture'], vmt_to_vmat['textures']['$normalmap'][VMAT_DEFAULT], True, False))
                        outVal = createMaskFromChannel(sourceTexture, 'A', vmt_to_vmat['alphamaps']['$blendtintbybasealpha'][VMAT_DEFAULT], True)
                    
                    elif vmtKey == '$selfillum_envmapmask_alpha':
                        if vmtKeyValList.get('$selfillum'):
                            print('Warning: Found conflicting $selfillum with $selfillum_envmapmask_alpha. Please correct manually')

                        sourceTexture = formatFullDir(formatNewTexturePath(vmtKeyValList['$envmapmask'], vmt_to_vmat['textures']['$envmapmask'][VMAT_DEFAULT], True, False))
                        outVal = createMaskFromChannel(sourceTexture, 'A', vmt_to_vmat['alphamaps']['$selfillum_envmapmask_alpha'][VMAT_DEFAULT], True)
                '''
                
                # F_RENDER_BACKFACES 1
                elif keyType == 'f_settings':
                    
                    if vmtKey == '$detailblendmode':
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
                        
                        #elif oldVal == '7':

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

                #print("DBG: " + oldKey + ' ' + oldVal + ' (' + vmatReplacement.replace('\t', '').replace('\n', '') + ' ' + vmatDefaultValue.replace('\t', '').replace('\n', '') + ') -------> ' + outKey + ' ' + outVal.replace('\t', '').replace('\n', '') + ' ' + outAdditionalLines.replace('\t', '').replace('\n', ''))
                print("DBGGGGGGGGG: " + oldKey + ' "' + oldVal + '" -------> ' + outKey + ' ' + outVal.replace('\t', '').replace('\n', '') + ' ' + outAdditionalLines.replace('\t', '').replace('\n', ''))

    return vmatContent
    


failures = []
# Main function, loop through every .vmt
x = 0
for fileName in fileList:
    x = x+1
    if x > 1000: quit()
    print('--------------------------------------------------------------------------------------------------------')
    print('+ Loading File:\n' + fileName)
    vmtKeyValList = {}
    validMaterial = False
    validPatch = False
    skipNextLine = False
    
    with open(fileName, 'r') as vmtFile:
        for line in vmtFile.readlines():
            if any(wd in line.lower() for wd in materialTypes):
                validMaterial = True
                matType = line.lower().replace('"', '').strip()
                
            if skipNextLine:
                if "]" in line or "}" in line:
                    skipNextLine = False
            else:
                parseVMTParameter(line, vmtKeyValList)
            
            if any(wd in line.lower() for wd in ignoreList):
                skipNextLine = True

    if '"patch"' in matType: # .lower()
        patchFile = vmtKeyValList["include"].replace('"', '').replace("'", '')
        print("+ Patching materials details from: " + patchFile +'\n')
        try:
            with open(formatFullDir(patchFile), 'r') as vmtFile:
                for line in vmtFile.readlines():
                    if any(wd in line.lower() for wd in materialTypes):
                        validPatch = True
                    parseVMTParameter(line, vmtKeyValList)
        except FileNotFoundError:
            failures.append(patchFile)
            print("Couldn't find patch file. Skipping!")
            continue
                
        if not validPatch:
            print("+ Patch file is not a valid material. Skipping!")
            continue
        
    skyBoxVmtFile = os.path.basename(fileName.strip(".vmt"))[-2:]
    if(skyBoxVmtFile[-2:] in skyboxfaces):
        newVmatSkybox = buildS2CompatibleSkybox(fileName)
        if(os.path.exists(newVmatSkybox)) and not OVERWRITE_VMAT:
            print('+ File already exists. Skipping!')

    if validMaterial:
        vmatFileName = fileName.replace('.vmt', '') + '.vmat'
        if os.path.exists(vmatFileName) and not OVERWRITE_VMAT:
            print('+ File already exists. Skipping!')
            continue
        
        print('+ Converting ' + os.path.basename(fileName))
        #print(vmtKeyValList)
        vmatShader = chooseShader(matType, vmtKeyValList, fileName)
        if '$blendmodulatetexture' in vmtKeyValList or '$newlayerblending' in vmtKeyValList:
            vmatShader == SH_VR_SIMPLE_2WAY_BLEND

            
        #    isBlend = true materialTypes[matType.strip('""\n"')]
        with open(vmatFileName, 'w') as vmatFile:
            vmatFile.write('// Converted with vmt_to_vmat.py\n')
            vmatFile.write('// Original file: ' + fileName + '\n\n')
            vmatFile.write('Layer0\n{\n\tshader "' + vmatShader + '.vfx"\n\n')
        
            print("mattype: " + matType)

            
            vmatFile.write(convertVmtToVmat(vmtKeyValList)) ###############################        
            
            
            
            
            #check if base texture is empty
            #if "metal" in vmatFileName:
            #    vmatFile.write("\tg_flMetalness 1.000\n")
            
                    
            vmatFile.write('}\n')
            
        #with open(fileName) as f:
        #    with open(vmatFileName, "w") as f1:
        #        for line in f:
        #            f1.write(COMMENT + line)

        print ('+ Saved new file at:' + vmatFileName)

    bumpmapConvertedList = formatFullDir("convertedfiles.txt")
    if not os.path.exists(bumpmapConvertedList):
        print('ERROR: Please create an empty text file named "convertedfiles.txt" in the root of the mod (i.e. content/steamtours_addons/hl2/materials)')
        print('Should go in here: ' + PATH_TO_NEW_CONTENT_ROOT)
        quit()
    
    ''' flip the green channels of any normal maps
    if(bumpmapPath != ""):
        print("Checking if normal file " + bumpmapPath + " has been converted:")
        foundMaterial = False
        with open(bumpmapConvertedList, 'r+') as bumpList: #change the read type to write
            for line in bumpList.readlines():
                if line.rstrip() == bumpmapPath.rstrip():
                    foundMaterial = True
        
            if not foundMaterial:
                flipNormalMap(formatNewTexturePath(bumpmapPath).strip("'" + '"'))
                print("flipped normal map of " + bumpmapPath)
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
    print()
    print()
    print("ERROR: Couldn't convert everything as certain referenced materials are missing.")
    print("Please check base game (HL2, Counter-Strike: Source, etc) materials folders for the following files and copy them to 'convertme' folder (retaining their path)")
    for failure in failures:
        print(failure)
