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
from shutil import copyfile
from PIL import Image, ImageOps
from time import time, sleep
from difflib import get_close_matches
from random import randint
#from s2_functions import *

# generic, blend instead of vr_complex, vr_2wayblend etc...
# blend doesn't seem to work though. why...
USE_OLD_SHADERS = False
newshader = not USE_OLD_SHADERS

# File format of the textures. Needs to be lowercase
TEXTURE_FILEEXT = '.tga'

# make sure to remember the final slash!!
PATH_TO_CONTENT_ROOT = r""
#PATH_TO_NEW_CONTENT_ROOT = r""

# Set this to True if you wish to overwrite your old vmat files
OVERWRITE_VMAT = True

REMOVE_VTF_FILES = False
# Set this to True if you wish to do basic renaming of your textures
# texture.tga, texture_color.tga -> texture_color.tga
RENAME_TEXTURES = True
RENAME_BY_COPYING = True
FINE_RENAME = 2

# True for messier file system while making the script a bit faster.
FILE_COUNT_OR_PROCESS = True

# True if you want simple, fast and inaccurate PBR (neither methods are implemented as of now)
BASIC_PBR = False

DEBUG = False
def dbg_msg(*args, **kwargs):
    if not DEBUG: pass
    else: print("@ DBG:", *args, **kwargs)

Late_Calls = []

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
#SH_SPRITECARD = 'spritecard'

# Most shaders have missing/additional properties.
# Need to set an apropriate one that doesn't sacrifice much.
def chooseShader(matType, vmtKeyValList, fileName):

    shaders = {
        SH_BLACK: 0,
        SH_VR_BLACK_UNLIT: 0,
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
    
    # not recognized, give emtpy shader SH_VR_BLACK_UNLIT
    if matType not in materialTypes:
        return SH_VR_BLACK_UNLIT

    #TODO: if containts values starting with _rt_ give some empty shader
    
    if USE_OLD_SHADERS:   shaders[SH_GENERIC] += 1
    else:                   shaders[materialTypes[matType]] += 1

    if matType == "unlitgeneric":

        if '\\skybox\\' in fileName or '/skybox/' in fileName: shaders[SH_SKY] += 4 # 95% correct
        if "$nofog" in vmtKeyValList: shaders[SH_SKY] += 1
        if "$ignorez" in vmtKeyValList: shaders[SH_SKY] += 2

        if "$receiveflashlight" in vmtKeyValList: shaders[SH_SKY] -= 6
        if "$alphatest" in vmtKeyValList: shaders[SH_SKY] -= 6
        if "$additive" in vmtKeyValList: shaders[SH_SKY] -= 3
        if "$vertexcolor" in vmtKeyValList: shaders[SH_SKY] -= 3
        # translucent
    
    elif matType == "worldvertextransition":
        if vmtKeyValList.get('$basetexture2'): shaders[SH_VR_SIMPLE_2WAY_BLEND] += 69
        else: print("~ ERROR: WTF")

    elif matType == "lightmappedgeneric":
        if vmtKeyValList.get('$newlayerblending') == '1': shaders[SH_VR_SIMPLE_2WAY_BLEND] += 420

    elif matType == "":
        pass
    
    return max(shaders, key = shaders.get)

# material types need to be lowercase because python is a bit case sensitive
materialTypes = {
    "sky":                  SH_SKY,
    "unlitgeneric":         SH_VR_COMPLEX,
    "vertexlitgeneric":     SH_VR_COMPLEX,
    "decalmodulate":        SH_VR_COMPLEX,
    "lightmappedgeneric":   SH_VR_COMPLEX,
    "lightmappedreflective":SH_VR_COMPLEX,
    "character":            SH_VR_COMPLEX,
    "customcharacter":      SH_VR_COMPLEX,
    "patch":                SH_VR_COMPLEX,
    "teeth":                SH_VR_COMPLEX,
    "eyes":                 SH_VR_EYEBALL,
    "eyeball":              SH_VR_EYEBALL,
    "water":                SH_SIMPLE_WATER,
    "refract":              SH_REFRACT,
    "worldvertextransition":SH_VR_SIMPLE_2WAY_BLEND,
    "lightmapped_4wayblend":SH_VR_SIMPLE_2WAY_BLEND, # no available shader that 4-way-blends
    "cables":               SH_CABLES,
    "lightmappedtwotexture":SH_VR_COMPLEX, # 2 multiblend $texture2 nocull scrolling, model, additive.
    "unlittwotexture":      SH_VR_COMPLEX, # 2 multiblend $texture2 nocull scrolling, model, additive.
    #"spritecard":           SH_SPRITECARD,
    #, #TODO: make this system functional
    #"modulate",
}

ignoreList = [ "dx9", "dx8", "dx7", "dx6"]

surfprop_force = {
    'stucco':       'world.drywall',
    'tile':         'world.tile_floor',
    'metalpanel':   'world.metal_panel',
    'wood':         'world.wood_solid',
}
surfprop_HLA = ['metal_panel', 'wood_solid', 'concrete']

QUOTATION = '"'
COMMENT = "// "
debugContent = ''
debugList = []

# and "asphalt_" in fileName
def parseDir(dirName):
    files = []
    skipdirs = ['dev', 'debug', 'tools', 'vgui', 'console', 'correction']
    for root, _, fileNames in os.walk(dirName):
        for skipdir in skipdirs:
            if ('materials\\' + skipdir) in root: continue
        #if not root.endswith(r'materials\skybox'): continue
        for fileName in fileNames:
            if fileName.lower().endswith('.vmt'): # : #
                files.append(os.path.join(root,fileName))
                if len(files) % randint(90, 270) == 0:
                    print("Found", len(files), "files")

    print("Total:", len(files), "files")

    return files

###
### Main Execution
###

if DEBUG:
    #currentDir = r"D:\Users\kristi\Desktop\WORK\MOD\content\hlvr"
    #currentDir =r"D:\Program Files (x86)\Steam\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo"
    currentDir = r"D:\Users\kristi\Desktop\WORK\test\there"
else:
    currentDir = os.getcwd()


if not PATH_TO_CONTENT_ROOT:
    if(len(sys.argv) >= 2):
        PATH_TO_CONTENT_ROOT = sys.argv[1]
    else:
        while not PATH_TO_CONTENT_ROOT:
            c = input('Type the root directory of the vmt materials you want to convert (enter to use current directory, q to quit).: ') or currentDir
            if not os.path.isdir(c):
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
            c = input('Type the directory you wish to output Source 2 materials to (enter to use the same dir): ') or currentDir
            if(c == currentDir):
                PATH_TO_NEW_CONTENT_ROOT = PATH_TO_CONTENT_ROOT # currentDir
            else:
                if not path.isdir(c):
                    if c in ('q', 'quit', 'exit', 'close'): quit()
                    print('Could not find directory.')
                    continue
                PATH_TO_NEW_CONTENT_ROOT = c.lower().strip().strip('"')
"""
PATH_TO_CONTENT_ROOT = os.path.normpath(PATH_TO_CONTENT_ROOT) + '\\'
#PATH_TO_NEW_CONTENT_ROOT =  os.path.normpath(PATH_TO_NEW_CONTENT_ROOT) + '\\'

print('\nSource 2 Material Conveter! By Rectus via Github.')
print('Initially forked by Alpyne, this version by caseytube.\n')
print('--------------------------------------------------------------------------------------------------------')

# "environment maps/metal_generic_002" -> "materials/environment maps/metal_generic_002(.tga)"
def formatVmtTextureDir(localPath, fileExt = TEXTURE_FILEEXT):
    if localPath.endswith(fileExt): fileExt = ''
    localPath = 'materials/' + localPath.strip().strip('"') + fileExt
    localPath = localPath.replace('\\', '/') # Convert paths to use forward slashes.
    localPath = localPath.replace('.vtf', '')#.replace('.tga', '') # remove any old extensions
    localPath = localPath.lower()

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

# -------------------------------
# Returns correct path, checks if alreay exists, renames with proper extensions, etc...
# -------------------------------
def formatNewTexturePath(vmtPath, textureType = TEXTURE_FILEEXT, noRename = False, forReal = True):

    global debugContent
    global debugList
    newName = ''
    
    subStr = textureType[:-4]#textureType.replace(TEXTURE_FILEEXT, '')
    #breakpoint()
    # don't rename

    # and Error loading resource file "materials/models/props/de_dust/hr_dust/dust_lights/street_lantern_03/street_lantern_03_color.vmat_c" (Error: ERROR_FILEOPEN)
    if vmtPath == '': return 'materials/default/default' + textureType

    vtfTexture = formatFullDir(formatVmtTextureDir(vmtPath + '.vtf', '') + '.vtf')
    if REMOVE_VTF_FILES and os.path.exists(vtfTexture):
        os.remove(vtfTexture)
        print("~ Removed vtf file: " + formatVmatDir(vtfTexture))

    # "newde_cache/nc_corrugated" -> materials/newde_cache/nc_corrugated
    textureLocal = formatVmtTextureDir(vmtPath, '')
    #textureLocal = textureLocal.lower()

    # no rename
    if not RENAME_TEXTURES  or noRename or not subStr or fileName.endswith('_normal.vmt'):
        return textureLocal + TEXTURE_FILEEXT
    # simple rename
    elif not FINE_RENAME: newName = textureLocal + textureType
    # processed rename
    else:
        oldName = os.path.basename(textureLocal)
        newName = textureAddSubStr(oldName, subStr)

        # BUG: mybumpmap.tga -> mymap_normal.tga
        if newName == oldName: return textureLocal + TEXTURE_FILEEXT #return (os.path.normpath(os.path.dirname(textureLocal) + '/' + newName + TEXTURE_FILEEXT)).replace('\\', '/')
        if textureType == "_color.tga" and textureLocal.endswith('_normal'):
            dbg_msg("FIXED NORMAL")
            return textureRename(textureLocal.rstrip(TEXTURE_FILEEXT) + "_color", textureLocal + '.tga', textureType)
        replList = {'refl':'mask', 'normal':'bump'}
        if subStr[1:] in replList and replList[subStr[1:]] in oldName:
            newName = ''.join(oldName.rsplit(replList[subStr[1:]], 1)).rstrip('_') + subStr

        for i in range(1, len(subStr[1:])):
            if textureLocal.endswith(subStr[:-i]) or (textureLocal.endswith(subStr[1:-i]) and i < 3): # i < 3 no underscore needs 3 letters minimum: texturedet
                if i == len(subStr[1:])-1 and FINE_RENAME > 1:
                    newName = ''.join(oldName.rsplit(subStr[1:-i], 1)).rstrip('_') + subStr[1:-i] + subStr
                else:
                    newName = ''.join(oldName.rsplit(subStr[1:-i], 1)).rstrip('_') + subStr

                if DEBUG: debugContent += "1 "
                break
            if i < (len(subStr[1:]) - 1): continue
            if oldName[:-1].endswith(subStr[1:]):
                if FINE_RENAME == 2: newName = ''.join(oldName[:-1].rsplit(subStr[1:], 1)).rstrip('_') + subStr
                else: newName = ''.join(oldName[:-1].rsplit(subStr[1:], 1)).rstrip('_') + subStr[-1:] + subStr
                if DEBUG: debugContent += "2 "
            elif subStr[1:] in oldName:
                debugContent += "3 "
                if subStr in oldName: newName = ''.join(oldName.rsplit(subStr, 1)).rstrip('_') + subStr
                else: newName = ''.join(oldName.rsplit(subStr[1:], 1)).rstrip('_') + subStr

        newName = (os.path.normpath(os.path.dirname(textureLocal) + '/' + newName + TEXTURE_FILEEXT)).replace('\\', '/')

        if forReal:
            if DEBUG: debugContent += os.path.basename(textureLocal) + ' -> ' + newName + '\n'

    if not forReal: return newName
    
    outVmatTexture =  textureRename(textureLocal, newName, textureType) or ('materials/default/default' + textureType)

    if 'materials/default/default' in outVmatTexture:
        print("~ ERROR: Could not find texture: " + formatFullDir(textureLocal))

    return outVmatTexture

def textureRename(localPath, newNamePath, textureType, makeCopy = False):

    if 'skybox' in localPath:
        return localPath

    localPath = formatFullDir(localPath)

    if not localPath.endswith(TEXTURE_FILEEXT):
        localPath += TEXTURE_FILEEXT

    # TODO: this is a temporary fix
    #if(os.path.exists(localPath.rstrip(TEXTURE_FILEEXT))):
    #    if not os.path.exists(localPath):
    #        os.rename(localPath.rstrip(TEXTURE_FILEEXT), localPath)

    newNamePath = formatFullDir(newNamePath)
    
    if(os.path.exists(newNamePath)):
        # don't need this, temporary fix only
        #if os.path.exists(localPath) and not makeCopy:
        #    os.remove(localPath)
        return formatVmatDir(newNamePath)

    # TODO: COPY. Make renaming optional.

    makeCopy = RENAME_BY_COPYING

    if not os.path.exists(localPath):
        print("+ Could not find texture " + localPath + " set to be renamed into: " + newNamePath.split('/')[-1])
 
        for key in list(vmt_to_vmat['textures']):
            #if os.path.exists(localPath[:-4] + vmt_to_vmat['textures'][key][VMAT_DEFAULT]):
            tryPath = formatFullDir(formatNewTexturePath(formatVmatDir(localPath[:-4]), vmt_to_vmat['textures'][key][VMAT_DEFAULT], forReal = False))
            dbg_msg("checking for", tryPath)
            if os.path.exists(tryPath):
                makeCopy = True
                localPath = localPath[:-4] + vmt_to_vmat['textures'][key][VMAT_DEFAULT]
                print("+ Nevermind... found a renamed copy! " + formatVmatDir(localPath))
                print("+ However, we shouldn't have had to search for it. Check if material's using same image for more than one map.")
                break

        if not os.path.exists(localPath):
            print("+ Please check!")
            return None
    else:
        if textureType != 'color.tga':
            for key in list(vmt_to_vmat['textures']):
                suffix = vmt_to_vmat['textures'][key][VMAT_DEFAULT]
                if suffix != textureType[:-4] and localPath.endswith(suffix):
                    #localPath = ''.join(localPath.rsplit(suffix, 1)) -- NO, localpath exists and I should not touch it.
                    # output should be texture_color_{suffix} while texture_color remains untouched.
                    dbg_msg("Problematic two map one image detected. Copying", localPath, "->", newNamePath)
                    #sleep(5.0)
                    makeCopy = True
                    break
    try:
        if not makeCopy:
            os.rename(localPath, newNamePath)
        else:
            copyfile(localPath, newNamePath)

    except FileExistsError:
        print("+ Could not rename " + formatVmatDir(localPath) + ". Renamed copy already exists")

    except FileNotFoundError:
        if(not os.path.exists(newNamePath)):
            print("~ ERROR: couldnt find")

    if os.path.exists(localPath) and not makeCopy:
        os.remove(localPath)

    return formatVmatDir(newNamePath)

# -------------------------------
# Returns texture path of given vmtParam, texture which has likely been renamed to be S2 naming compatible
# $basetexture  ->  materials/path/to/texture_color.tga of the TextureColor
# -------------------------------
def getTexture(vmtParams):

    texturePath = ''
    bFound = False

    if not isinstance(vmtParams, list):
        vmtParams = [ vmtParams ]

    for vmtParam in vmtParams:

        if not vmtKeyValList.get(vmtParam):
            continue

        texturePath = formatVmtTextureDir(vmtKeyValList[vmtParam])

        if os.path.exists(formatFullDir(texturePath)):
            bFound = True

        if not RENAME_BY_COPYING or not bFound:
            texturePath = formatNewTexturePath(vmtKeyValList[vmtParam], vmt_to_vmat['textures'][vmtParam][VMAT_DEFAULT], forReal=False)

        if os.path.exists(formatFullDir(texturePath)):
            bFound = True
            break

    if not bFound: texturePath = None # ''

    return texturePath

# Verify file paths
fileList = []
if(PATH_TO_CONTENT_ROOT):
    folderPath = PATH_TO_CONTENT_ROOT
    if not PATH_TO_CONTENT_ROOT.rstrip('\\/').endswith('materials'):
        folderPath = os.path.join(PATH_TO_CONTENT_ROOT, 'materials')

    absFilePath = os.path.abspath(folderPath)

    if os.path.isdir(absFilePath):
        print("Scanning for .vmt files. This may take a while...")
        fileList.extend(parseDir(absFilePath))
    elif(absFilePath.lower().endswith('.vmt')):
        fileList.append(absFilePath)
else:
    input("No file or directory specified, press any key to quit...")
    quit()

def parseVMTParameter(line, parameters):
    words = []
    nextLine = ''

    # doesn't split inside qotes
    words = re.split(r'\s+(?=(?:[^"]*"[^"]*")*[^"]*$)', line)
    words = list(filter(len, words))

    if not words: return
    elif len(words) == 1:
        Quott = words[0].count('"')
        # fix for: "$key""value""
        if Quott >= 4:
            m = re.match(r'^((?:[^"]*"){1}[^"]*)"(.*)', line)
            if m:
                line = m.group(1)  + '" ' + m.group(2)
                parseVMTParameter(line, vmtKeyValList)
        # fix for: $key"value"
        elif Quott == 2:
            # TODO: sth better that keeps text inside quotes intact.
            #line = line.replace('"', ' " ').rstrip(' " ') + '"'
            line = line.replace('"', '')
            parseVMTParameter(line, vmtKeyValList)
        return # no recursive loops please
    elif len(words) > 2:
        # fix for: "$key""value""$key""value" - we come here after len == 1 has happened
        nextLine = ' '.join(words[2:]) # words[2:3]
        words = words[:2]

    key = words[0].strip('"').lower()

    if key.startswith('/'):
        return

    if not key.startswith('$'):
        if not 'include' in key:
            return

    # "GPU>=2?$detailtexture"
    if '?' in key:
        print("~ WARNING: Might not process well materials that have GPU-setting based parameters. Please manually check.")
        #key = key.split('?')[1].lower()
        key.split('?')
        if key[0] == 'GPU>=2':
            dbg_msg("Trying using the high-shader parameter.")
            key = key[2].lower()
        else:
            print("~ WARNING: Might not process well materials that have GPU-setting based parameters. Please manually check.")
            if key[0] == 'GPU<2':
                return
            key = key[2].lower()

    val = words[1].lstrip('\n').lower() # .strip('"')

    # remove comments, HACK
    commentTuple = val.partition('//')
    
    if not commentTuple[0] in parameters:
        parameters[key] = commentTuple[0]

    if nextLine: parseVMTParameter(nextLine, vmtKeyValList)

def createMaskFromChannel(vmtTexture, channel = 'A', copySub = '_mask.tga', invert = True, queue = True):
    if not os.path.exists(vmtTexture):
        vmtTexture = formatFullDir(vmtTexture)

    if invert:  newMaskPath = vmtTexture[:-4] + '_' + channel[:3].lower() + '-1' + copySub
    else:       newMaskPath = vmtTexture[:-4] + '_' + channel[:3].lower()        + copySub
    
    if os.path.exists(newMaskPath) and not DEBUG:
        return formatVmatDir(newMaskPath)

    if os.path.exists(vmtTexture):
        image = Image.open(vmtTexture).convert('RGBA')
        imagePixels = image.load()

        if queue:
            Late_Calls.append((vmtTexture, channel, copySub, invert, False))
        elif channel == 'luminance':
            maskImage = Image.new('L', image.size)
            maskPixels = maskImage.load()
            last_time = time()
            for x in range(image.width):
                for y in range(image.height):

                    R, G, B, _ = imagePixels[x,y] # image.getpixel( (x,y) )
                    #######################################################
                    LuminanceB = (0.299*R + 0.587*G + 0.114*B)
                    #######################################################
                    maskPixels[x,y] = round(LuminanceB) # maskImage.putpixel((x,y), )

            dbg_msg("It took:", time()-last_time, "seconds to calculate luminance")
            maskImage.save(newMaskPath, optimize=True, quality=85)
            maskImage.close()

        else:
            imgChannel = image.getchannel(str(channel))
            # Create a new image with an opaque black background TODO: 'L'
            bg = Image.new("RGBA", image.size, (0,0,0,255))

            # Copy the alpha channel to the new image using itself as the mask
            bg.paste(imgChannel)

            if invert:
                r,g,b,_ = bg.split()
                rgb_image = Image.merge('RGB', (r,g,b))
                inverted_image = ImageOps.invert(rgb_image)

                r2,g2,b2 = inverted_image.split()
                final_transparent_image = Image.merge('RGB', (r2,g2,b2)).convert('RGBA')

                final_transparent_image.save(newMaskPath, optimize=True)
                final_transparent_image.close()
            else:
                bg.save(newMaskPath, optimize=True)
                bg.close()

    else:
        print("~ ERROR: Couldn't find requested image (" + vmtTexture + "). Please check.")
        return 'materials/default/default' + copySub

    if not queue:
        print("+ Saved mask to " + formatVmatDir(newMaskPath))

    return formatVmatDir(newMaskPath)

def flipNormalMap(localPath):

    image_path = formatFullDir(localPath)
    if not os.path.exists(image_path): return

    if FILE_COUNT_OR_PROCESS:
        with open(formatFullDir(localPath[:-4] + '.txt'), 'w') as settingsFile:
            settingsFile.write('"settings"\n{\t"legacy_source1_inverted_normal" "1"\n}')
    else:
        # Open the image and convert it to RGBA, just in case it was indexed
        image = Image.open(image_path).convert('RGBA')

        r,g,b,a = image.split()
        g = ImageOps.invert(g)
        final_transparent_image = Image.merge('RGBA', (r,g,b,a))
        final_transparent_image.save(image_path)

    return localPath

skyboxPath = {}
skyboxFaces = ['up', 'dn', 'lf', 'rt', 'bk', 'ft']

def fixIntVector(s, addAlpha = 1, returnList = False):

    likelyColorInt = False
    if('{' in s or '}' in s):
        likelyColorInt = True

    s = s.strip() # TODO: remove letters
    s = s.strip('"' + "'")
    s = s.strip().strip().strip('][}{')

    try: originalValueList = [str(float(i)) for i in s.split(' ') if i != '']
    except: originalValueList =  [1.000000, 1.000000, 1.000000]

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

def is_convertible_to_float(value):
  try:
    float(value)
    return True
  except: return False

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

normalmaps = ['$normal', '$bumpmap', '$bumpmap2']

VMAT_REPLACEMENT = 0
VMAT_DEFAULT = 1
VMAT_EXTRALINES = 2

# TODO: Eliminate hardcoded file extensions throughout the entire code.
vmt_to_vmat = {
    'textures': {

        '$hdrcompressedtexture':('SkyTexture',          '.pfm',             'F_TEXTURE_FORMAT2 6 // BC6H (HDR compressed - recommended)'),
        '$hdrbasetexture':      ('SkyTexture',          '.pfm',             ''),
        
        ## Layer0 
        '$basetexture':         ('TextureColor',        '_color.tga',       ''), # SkyTexture
        '$painttexture':        ('TextureColor',        '_color.tga',       ''),
        '$bumpmap':             ('TextureNormal',       '_normal.tga',      ''),
        '$normalmap':           ('TextureNormal',       '_normal.tga',      ''),

        ## Layer1
        '$basetexture2':        ('TextureColorB',       '_color.tga',       '') if newshader else ('TextureLayer1Color', '_color.tga', ''),
        '$bumpmap2':            ('TextureNormalB',      '_normal.tga',      '') if newshader else ('TextureLayer1Normal', '_normal.tga', 'F_BLEND_NORMALS 1'),
        #'$phongexponent2':      ('TextureRoughnessB',   '_rough'+TEXTURE_FILEEXT,       ''), # $phongmaskcontrastbrightness2, $phongbasetint2, $phongamount2

        ## Layer2-3
        '$basetexture3':        ('TextureLayer2Color',  '_color.tga',       ''),
        '$basetexture4':        ('TextureLayer3Color',  '_color.tga',       ''),

        ## Layer blend mask
        '$blendmodulatetexture':('TextureMask',             '_mask.tga',    'F_BLEND 1') if newshader \
                            else('TextureLayer1RevealMask', '_blend.tga',   'F_BLEND 1'),
        
        #'$texture2':            ('',  '_color.tga',       ''), # UnlitTwoTexture
        '$normalmap2':          ('TextureNormal2',      '_normal.tga',      'F_SECONDARY_NORMAL 1'), # used with refract shader
        '$flowmap':             ('TextureFlow',         '.tga',    'F_FLOW_NORMALS 1\n\tF_FLOW_DEBUG 1'),
        '$flow_noise_texture':  ('TextureNoise',        '_noise.tga',       'F_FLOW_NORMALS 1\n\tF_FLOW_DEBUG 2'),
        '$detail':              ('TextureDetail',       '_detail.tga',      'F_DETAIL_TEXTURE 1\n'),

        '$decaltexture':        ('TextureDetail',       '_detail.tga',      'F_DETAIL_TEXTURE 1\n\tF_SECONDARY_UV 1\n\tg_bUseSecondaryUvForDetailTexture "1"'),
        #'$detail2':            ('TextureDetail',       '_detail.tga',      'F_DETAIL_TEXTURE 1\n'),
        '$tintmasktexture':     ('TextureTintMask',     '_mask.tga',        'F_TINT_MASK 1'), # GREEN CHANNEL ONLY, RED IS FOR $envmapmaskintintmasktexture 1
        '$selfillummask':       ('TextureSelfIllumMask','_selfillummask.tga',''),
        '$metalnessmask':       ('TextureMetalness',    '_metal.tga',       'F_METALNESS_TEXTURE 1'), # F_SPECULAR too

        #('TextureTintTexture',)
        # These have no separate masks
        '$translucent':         ('TextureTranslucency', '_trans.tga',       'F_TRANSLUCENT 1\n'), # g_flOpacityScale "1.000"
        '$alphatest':           ('TextureTranslucency', '_trans.tga',       'F_ALPHA_TEST 1\n'),
        
        # in viewmodels, only the G channel -> R = flCavity, G = flAo, B = cModulation, A = flPaintBlend
        '$ao':                  ('TextureAmbientOcclusion', '_ao.tga',      'g_flAmbientOcclusionDirectSpecular "1.000"\n\tF_AMBIENT_OCCLUSION_TEXTURE 1\n'),
        '$aotexture':           ('TextureAmbientOcclusion', '_ao.tga',      'g_flAmbientOcclusionDirectSpecular "1.000"\n\tF_AMBIENT_OCCLUSION_TEXTURE 1\n'),
        #'$ambientoccltexture': '$ambientocclusiontexture':

        # Next script should take care of these, unless BASIC_PBR
        '$envmapmask': ('$envmapmask', '_env_mask.tga', '') if not BASIC_PBR else ('TextureRoughness', '_rough.tga', ''),
        '$phongmask': ('$phongmask', '_phong_mask.tga', ''),
    },

    # [0, 1] center defines the point of rotation. Only useful if rotate is being used.
    # [2, 3] scale fits the texture into the material the given number of times. '2 1' is a 50% scale in the X axis.
    #    [4] rotate rotates the texture counter-clockwise in degrees. Accepts any number, including negatives.
    # [5, 6] translate shifts the texture by the given numbers. '.5' will shift it half-way.
    # $detailtexturetransform "center .5 .5 scale 1 1 rotate 0 translate 0 0"
    'transform': {
        '$basetexturetransform':     ('g_vTex',          '', 'g_vTexCoordScale "[1.000 1.000]"g_vTexCoordOffset "[0.000 0.000]"'),
        '$detailtexturetransform':   ('g_vDetailTex',    '', 'g_flDetailTexCoordRotation g_vDetailTexCoordOffset g_vDetailTexCoordScale g_vDetailTexCoordXform'),
        '$bumptransform':            ('g_vNormalTex',    '', ''),
        '$bumptransform2':           ('',                '', ''),
        '$basetexturetransform2':    ('',               '', ''),    #
        '$texture2transform':        ('',                '', ''),   #
        '$blendmasktransform':       ('',                '', ''),   #
        '$envmapmasktransform':      ('',                '', ''),   #
        '$envmapmasktransform2':     ('',                '', '')    #

    },

    'settings': {

        #TODO: implement this in a better way
        '$surfaceprop':         ('SystemAttributes\n\t{\n\t\tPhysicsSurfaceProperties\t', 'default', ''),

        '$detailscale':         ('g_vDetailTexCoordScale',  '[1.000 1.000]',    ''),
        '$detailblendfactor':   ('g_flDetailBlendFactor',   '1.000',            ''),
        #'$detailblendfactor2':  ('g_flDetailBlendFactor',   '1.000',            ''),
        #'$detailblendfactor3':  ('g_flDetailBlendFactor',   '1.000',            ''),
        #'$detailblendfactor4':  ('g_flDetailBlendFactor',   '1.000',            ''),

        '$color':               ('g_vColorTint',           '[1.000 1.000 1.000 0.000]', ''),
        '$color2':              ('g_vColorTint',           '[1.000 1.000 1.000 0.000]', ''),
        '$selfillumscale':      ('g_flSelfIllumScale',      '1.000',            ''),
        '$selfillumtint':       ('g_vSelfIllumTint',        '[1.000 1.000 1.000 0.000]', ''),
        '$blendtintcoloroverbase':('g_flModelTintAmount', '1.000', ''),
        '$layertint1':          ('','',''),

        # requires F_DIFFUSE_WRAP 1. "? 
        '$warpindex':           ('g_flDiffuseWrap',     '1.000', ''),
        '$diffuseexp':          ('g_flDiffuseExponent', '2.000', 'g_vDiffuseWrapColor "[1.000000 1.000000 1.000000 0.000000]'),

        '$metalness':           ('g_flMetalness',           '0.0',   ''),
        '$alpha':               ('g_flOpacityScale',        '1.000', ''),
        '$alphatestreference':  ('g_flAlphaTestReference',  '0.500', 'g_flAntiAliasedEdgeStrength "1.000"'),
        '$refractamount':       ('g_flRefractScale',        '0.200', ''),
        '$flow_worlduvscale':   ('g_flWorldUvScale',        '1.000', ''),
        '$flow_noise_scale':    ('g_flNoiseUvScale',        '0.010', ''), # g_flNoiseStrength?
        '$flow_bumpstrength':   ('g_flNormalMapStrength',   '1.000', ''),

        # inverse
        '$nofog':   ('g_bFogEnabled',       '0',        '_bool_invert'),
        "$notint":  ('g_flModelTintAmount', '1.000',    '_bool_invert'),

        # SH_BLEND and SH_VR_STANDARD(SteamVR) -- $NEWLAYERBLENDING settings used on dust2 etc. might as well comment them for steamvr
        #'$blendsoftness':       ('g_flLayer1BlendSoftness', '0.500',    ''),
        #'$layerborderstrenth':  ('g_flLayer1BorderStrength','0.500',    ''),
        #'$layerborderoffset':   ('g_flLayer1BorderOffset',  '0.000',    ''),
        #'$layerbordersoftness': ('g_flLayer1BorderSoftness','0.500',    ''),
        #'$layerbordertint':     ('g_vLayer1BorderColor',       '[1.000000 1.000000 1.000000 0.000000]', ''),
        #'LAYERBORDERSOFTNESS':  ('g_flLayer1BorderSoftness', '1.0', ''),
        #rimlight
    },

    'f_settings': {
        '$envmap':          ('F_SPECULAR',              '1', ''),
        '$selfillum':       ('F_SELF_ILLUM',            '1', ''),
        '$additive':        ('F_ADDITIVE_BLEND',        '1', ''),
        '$ignorez':         ('F_DISABLE_Z_BUFFERING',   '1',''),
        '$nocull':          ('F_RENDER_BACKFACES',      '1', ''),
        '$decal':           ('F_OVERLAY',               '1', ''),
        '$flow_debug':      ('F_FLOW_DEBUG',            '0', ''),
        '$detailblendmode': ('F_DETAIL_TEXTURE',        '1', ''), # not 1 to 1
        '$decalblendmode':  ('F_DETAIL_TEXTURE',        '1', ''), # not 1 to 1
        '$sequence_blend_mode': ('F_FAST_SEQUENCE_BLEND_MODE', '1', '' ) # spritecard/// 
    },

    'mask_inside_mask': {
      # '$vmtKey':                      (extract_from,      extract_as,         channel to extract)
        # TODO: envmap, phong need processing. They should be added as a key.
        '$normalmapalphaenvmapmask':    (normalmaps,        '$envmapmask',      'A'), 
        '$basealphaenvmapmask':         ('$basetexture',    '$envmapmask',      'A'), # 'M_1-A'
        '$envmapmaskintintmasktexture': ('$tintmasktexture','$envmapmask',      'R'),

        '$basemapalphaphongmask':       ('$basetexture',    '$phongmask',       'A'),
        '$basealphaphongmask':          ('$basetexture',    '$phongmask',       'A'),
        '$normalmapalphaphongmask':     (normalmaps,        '$phongmask',       'A'),
        '$bumpmapalphaphongmask':       (normalmaps,        '$phongmask',       'A'),
        '$basemapluminancephongmask':   ('$basetexture',    '$phongmask',       'luminance'),

        '$blendtintbybasealpha':        ('$basetexture',    '$tintmasktexture', 'A'),
        '$selfillum_envmapmask_alpha':  ('$envmapmask',     '$selfillummask',   'A')

        #'$masks1': ('self', ('$rimmask', '$phongalbedomask', '$metalnessmask', '$warpindex'), 'RGBA')
    },

    # no direct replacement, etc
    'others2': {
        # ssbump shader is currently broken in HL:A.
        #'$ssbump':               ('TextureBentNormal',    '_bentnormal.tga', '\n\tF_ENABLE_NORMAL_SELF_SHADOW 1\n\tF_USE_BENT_NORMALS 1\n'),
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
                #dbg_msg("################", vmtKey)
                vmatReplacement = vmatItems[VMAT_REPLACEMENT]
                vmatDefaultValue = vmatItems[VMAT_DEFAULT]
                vmatExtraLines = vmatItems[VMAT_EXTRALINES]
                if ( vmatReplacement and vmatDefaultValue ):
                    
                    outKey = vmatReplacement
                    
                    if (keyType == 'textures'):
                        outVal = 'materials/default/default' + vmatDefaultValue
                    else:
                        outVal = vmatDefaultValue
                    
                    if vmatExtraLines == '_bool_invert':
                        oldVal = str(int(not int(oldVal)))
                        outAdditionalLines = ''
                    else:
                        outAdditionalLines = vmatExtraLines

                # no equivalent key-value for this key, only exists
                # add comment or ignore completely
                elif (vmatExtraLines):
                    if keyType in ('transform'): # exceptions
                        pass
                    else:
                        vmatContent += vmatExtraLines
                        break
                else:
                    vmatContent += COMMENT + vmtKey
                    break


                if(keyType == 'textures'):
                    
                    if vmtKey in ['$basetexture', '$hdrbasetexture', '$hdrcompressedtexture']:
                        # semi-BUG: how is hr_dust_tile_01,02,03 blending when its shader is LightmappedGeneric??????????
                        if '$newlayerblending' in vmtKeyValList or '$basetexture2' in vmtKeyValList:
                            outKey = vmatReplacement + 'A' # TextureColor -> TextureColorA
                            dbg_msg("" + outKey + "<--- is noblend ok?")
                        
                        if vmatShader == SH_SKY:
                            outKey = 'SkyTexture'
                            outVal = formatVmtTextureDir(oldVal[:-2].rstrip('_') + '_cube' + vmatDefaultValue.lstrip('_color'), fileExt = '')

                        else:
                            outVal = formatNewTexturePath(oldVal, vmatDefaultValue)

                    elif vmtKey in ['$basetexture3', '$basetexture4']:
                        if not USE_OLD_SHADERS: print('~ WARNING: Found 3/4-WayBlend but it is not supported with the current shader ' + vmatShader + '.')

                    elif vmtKey in  ('$bumpmap', '$bumpmap2', '$normalmap', '$normalmap2'):
                        # all(k not in d for k in ('name', 'amount')) vmtKeyValList.keys() & ('newlayerblending', 'basetexture2', 'bumpmap2'): # >=
                        if (vmtKey != '$bumpmap2') and (vmatShader == SH_VR_SIMPLE_2WAY_BLEND or '$basetexture2' in vmtKeyValList):
                            outKey = vmatReplacement + 'A' # TextureNormal -> TextureNormalA

                        # this is same as default_normal
                        #if oldVal == 'dev/flat_normal':
                        #    pass

                        if str(vmtKeyValList.get('$ssbump')).strip('"') == '1':
                            dbg_msg('Found SSBUMP' + outVal)
                            outKey = COMMENT + '$SSBUMP' + '\n\t' + outKey
                            pass

                        outVal = formatNewTexturePath(oldVal, vmatDefaultValue)
                        if not 'default/default' in outVal:
                            flipNormalMap(outVal)

                    elif vmtKey == '$blendmodulatetexture':
                        sourceTexturePath = getTexture(vmtKey)
                        if sourceTexturePath:
                            outVal = createMaskFromChannel(sourceTexturePath, 'G', vmatDefaultValue, False)

                    elif vmtKey == '$translucent' or vmtKey == '$alphatest':
                        #if is_convertible_to_float(oldVal):
                        #    vmatContent += '\t' + outAdditionalLines

                        if vmtKey == '$alphatest':
                            sourceTexturePath = getTexture('$basetexture')
                            if sourceTexturePath:
                                #if '$model' in vmtKeyValList or 'models' in vmatFileName:
                                outVal = createMaskFromChannel(sourceTexturePath, 'A', vmatDefaultValue, False)
                                #else: #????
                                #    outVal = createMaskFromChannel(sourceTexturePath, 'A', vmatDefaultValue, True)

                        elif vmtKey == '$translucent':
                            if is_convertible_to_float(oldVal):
                                #outVal = fixIntVector(oldVal)
                                sourceTexturePath = getTexture('$basetexture')
                                if sourceTexturePath:
                                    outVal = createMaskFromChannel(sourceTexturePath, 'A', vmatDefaultValue, False)

                    elif vmtKey == '$tintmasktexture':
                        sourceTexturePath = getTexture(vmtKey)
                        if sourceTexturePath:
                            outVal = createMaskFromChannel(sourceTexturePath, 'G', vmatDefaultValue, False)

                    elif vmtKey == '$aotexture':
                        sourceTexturePath = getTexture(vmtKey)
                        if sourceTexturePath:
                            outVal = createMaskFromChannel(sourceTexturePath, 'G', vmatDefaultValue, False)

                    elif vmtKey == '$envmapmask':
                        # do the inverting stuff
                        pass 

                    #### DEFAULT
                    else:
                        if vmatShader == SH_SKY: pass
                        else: outVal = formatNewTexturePath(oldVal, vmatDefaultValue)


                elif(keyType == 'transform'):
                    if not vmatReplacement or vmatShader == SH_SKY:
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

                    break ### Skip default content write

                elif(keyType == 'settings'):

                    if(vmtKey == '$detailscale'):
                        outVal = fixIntVector(oldVal, addAlpha=False)               

                   # TODO: 
                   # maybe it gets converted?
                    elif (vmtKey == '$surfaceprop'):
                        
                        # bit hardcoded
                        if oldVal in ('default', 'default_silent', 'no_decal', 'player', 'roller', 'weapon'):
                            pass

                        elif oldVal in surfprop_force:
                            outVal = surfprop_force[oldVal]

                        else:
                            if("props" in vmatFileName): match = get_close_matches('prop.' + oldVal, surfprop_HLA, 1, 0.4)
                            else: match = get_close_matches('world.' + oldVal, surfprop_HLA, 1, 0.6) or get_close_matches(oldVal, surfprop_HLA, 1, 0.6)

                            outVal = match[0] if match else oldVal

                        print(outVal)
                        vmatContent += '\n\t' + outKey + QUOTATION + outVal + QUOTATION + '\n\t}\n\n'
                        break ### Skip default content write

                    elif vmtKey == '$selfillum': # TODO: fix this
                        
                        if oldVal == '0' or '$selfillummask' in vmtKeyValList:
                            break

                        # should use reverse of the basetexture alpha channel as a self iluminating mask
                        # TextureSelfIlumMask "materials/*_selfilummask.tga"
                        sourceTexture = getTexture("$basetexture")
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
                    
                    #elif vmtKey in ('$phongexponent', '$phongexponent2'): # TODO:
                    #    if (vmatShader == SH_VR_SIMPLE_2WAY_BLEND) and vmtKey == '$phongexponent':
                    #        outKey += 'A'
                    #    #break
                    #    #continue
                    #    pass

                    # The other part are simple floats. Deal with them
                    else:
                        outVal = "{:.6f}".format(float(oldVal.strip(' \t"')))
                

                elif(keyType == 'mask_inside_mask'):
                    outVmtTexture = vmt_to_vmat['mask_inside_mask'][vmtKey][1]

                    #if DEBUG and oldKey == "$normalmapalphaenvmapmask": breakpoint()

                    if not vmt_to_vmat['textures'].get(outVmtTexture): break

                    sourceTexture       = vmt_to_vmat['mask_inside_mask'][vmtKey][0]
                    sourceChannel       = vmt_to_vmat['mask_inside_mask'][vmtKey][2]
                    outKey              = vmt_to_vmat['textures'][outVmtTexture][VMAT_REPLACEMENT]
                    outAdditionalLines  = vmt_to_vmat['textures'][outVmtTexture][VMAT_EXTRALINES]
                    sourceSubString     = vmt_to_vmat['textures'][outVmtTexture][VMAT_DEFAULT]

                    shouldInvert        = False

                    if ('1-' in sourceChannel):
                        if 'M_1-' in sourceChannel:
                            if vmtKeyValList.get('$model'): 
                                shouldInvert = True
                        else:
                            shouldInvert = True

                        sourceChannel = sourceChannel.strip('M_1-')

                    sourceTexturePath   = getTexture(sourceTexture)

                    if sourceTexturePath:
                        if vmtKeyValList.get(outVmtTexture):
                            print("~ WARNING: Conflicting " + vmtKey + " with " + outVmtTexture + ". Aborting mask creation (using original).")
                            break

                        outVal =  createMaskFromChannel(sourceTexturePath, sourceChannel, sourceSubString, shouldInvert)

                        # invert for brushes; if it's a model, keep the intact one ^
                        # both versions are provided just in case for 'non models'
                        #if not str(vmtKeyValList.get('$model')).strip('"') != '0':
                        #    outVal = createMaskFromChannel(sourceTexture, 'A', vmt_to_vmat['alphamaps']['$basealphaenvmapmask'][VMAT_DEFAULT], True )
                    else:
                        print("~ WARNING: Couldn't lookup texture from " + str(sourceTexture))
                        break


                # F_RENDER_BACKFACES 1 etc
                elif keyType == 'f_settings':
                    if vmtKey in  ('$detailblendmode', '$decalblendmode'):
                        # https://developer.valvesoftware.com/wiki/$detail#Parameters_and_Effects
                        # materialsystem\stdshaders\BaseVSShader.h#L26

                        if oldVal == '0':       outVal = '1' # Original mode (Mod2x)
                        elif oldVal == '1':     outVal = '2' # Base.rgb+detail.rgb*fblend 
                        elif oldVal == '12':    outVal = '0'
                        else: outVal = '1'

                    if outKey in vmatContent: ## Replace values that are already in
                        dbg_msg('' + outKey + ' is already in.')
                        vmatContent = re.sub(r'%s.+' % outKey, outKey + ' ' + outVal, vmatContent)
                    else:
                        vmatContent += '\t' + outKey + ' ' + outVal + '\n'  
                    break ### Skip default content write

                elif keyType == 'others2':
                    break ### Skip default content write
                
                if(outAdditionalLines): outAdditionalLines = '\n\t' + outAdditionalLines + '\n'

                #############################
                ### Default content write ###
                line = outAdditionalLines + '\t' + outKey + '\t\t' + QUOTATION + outVal + QUOTATION + '\n'
                vmatContent = vmatContent + line

                if DEBUG:
                    if(outVal.endswith(TEXTURE_FILEEXT)): outVal = formatFullDir(outVal)
                    ##dbg_msg( oldKey + ' ' + oldVal + ' (' + vmatReplacement.replace('\t', '').replace('\n', '') + ' ' + vmatDefaultValue.replace('\t', '').replace('\n', '') + ') -------> ' + outKey + ' ' + outVal.replace('\t', '').replace('\n', '') + ' ' + outAdditionalLines.replace('\t', '').replace('\n', ''))
                    dbg_msg( oldKey + ' "' + oldVal + '" ---> ' + outKey + ' ' + outVal.replace('\t', '').replace('\n', '') + ' ' + outAdditionalLines.replace('\t', '').replace('\n', ''))

                break ### stop looping, we replaced the key we needed

    return vmatContent

def convertSpecials(vmtKeyValList):

    # fix phongmask
    if vmtKeyValList.get("$phong") == '1' and not vmtKeyValList.get("$phongmask"):
        bHasPhongMask = False
        for key, val in vmt_to_vmat['mask_inside_mask'].items():
            if val[1] == '$phongmask':
                if vmtKeyValList.get(key):
                    bHasPhongMask = True
                    break
        if not bHasPhongMask: # normal map alpha acts as a phong mask by default
            vmtKeyValList.setdefault('$normalmapalphaphongmask', '1')

    # viewmodels
    if "models\\weapons\\v_models" in fileName:
        # use _ao texture in \weapons\customization\
        weaponDir = os.path.dirname(fileName)
        weaponPathSplit = fileName.split("\\weapons\\v_models\\")
        weaponPathName = os.path.dirname(weaponPathSplit[1])
        dbg_msg(weaponPathName + ".vmt")
        if fileName.endswith(weaponPathName + ".vmt") or fileName.endswith(weaponPathName.split('_')[-1] + ".vmt"):
            aoTexturePath = os.path.normpath(weaponPathSplit[0] + "\\weapons\\customization\\" + weaponPathName + '\\' + weaponPathName + "_ao" + TEXTURE_FILEEXT)
            aoNewPath = os.path.normpath(weaponDir + "\\" + weaponPathName + TEXTURE_FILEEXT)
            dbg_msg(aoTexturePath)
            if os.path.exists(aoTexturePath):
                dbg_msg(aoNewPath)
                if not os.path.exists(aoNewPath):
                    #os.rename(aoTexturePath, aoNewPath)
                    copyfile(aoTexturePath, aoNewPath)
                    print("+ Succesfully moved AO texture for weapon material:", weaponPathName)
                vmtKeyValList["$aotexture"] = formatVmatDir(aoNewPath).replace('materials\\', '')
                print("+ Using ao:", weaponPathName + "_ao" + TEXTURE_FILEEXT)

        vmtKeyValList.setdefault("$envmap", "0") # specular looks ugly on viewmodels so disable it. does not affect scope lens

failures = []
listsssss = []

#######################################################################################
# Main function, loop through every .vmt
##
for fileName in fileList:
    print('---------------------------------------------------------------------------')
    print('+ Reading file:  ' + fileName)
    #breakpoint()
    vmtKeyValList = {}
    matType = ''
    vmatShader = ''
    vmatFileName = ''
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
                if any(wd in matType for wd in materialTypes):
                    validMaterial = True
                
            if skipNextLine:
                if "]" in line or "}" in line:
                    skipNextLine = False
            else:
                parseVMTParameter(line, vmtKeyValList)
            
            if any(line.lower().endswith(wd) for wd in ignoreList):
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
                        
                        line = line.strip()
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
        
    vmatFileName = fileName.replace('.vmt', '') + '.vmat'
    vmatShader = chooseShader(matType, vmtKeyValList, fileName)

    skyboxName = os.path.basename(fileName).replace(".vmt", '')#[-2:]
    skyboxName, skyboxFace = [skyboxName[:-2], skyboxName[-2:]]
    #skyboxName, skyboxFace = skyboxName.rsplit(skyboxName[-2:-1], 1)
    #skyboxFace = skyboxName[-2:-1] + skyboxFace
    if((('\\skybox\\' in fileName) or ('/skybox/' in fileName)) and (skyboxFace in skyboxFaces)): # and shader
        if skyboxName not in skyboxPath:
            skyboxPath.setdefault(skyboxName, {'up':{}, 'dn':{}, 'lf':{}, 'rt':{}, 'bk':{}, 'ft':{}})
        for face in skyboxFaces:
            if(skyboxFace != face): continue
            
            facePath = vmtKeyValList.get('$hdrbasetexture') or vmtKeyValList.get('$hdrcompressedtexture') or vmtKeyValList.get('$basetexture')
            if(facePath and os.path.exists(formatFullDir(formatNewTexturePath(facePath, noRename= True)))):
                skyboxPath[skyboxName][face]['path'] = formatNewTexturePath(facePath, noRename= True)
                dbg_msg("Collecting", face, "sky face", skyboxPath[skyboxName][face]['path'])
            transform = vmtKeyValList.get('$basetexturetransform')
            
            if(transform):
                faceTransform = listMatrix(transform) if(transform) else list()
                skyboxPath[skyboxName][face]['rotate'] = int(float(faceTransform[MATRIX_ROTATE]))
                dbg_msg("Collecting", face, "transformation", skyboxPath[skyboxName][face]['rotate'], 'degrees')

            # skip vmat for dn, lf, rt, bk, ft
            # TODO: ok we might need the vmats for all of them because they might be used somewhere else
            vmatShader = SH_SKY
            vmatFileName = vmatFileName.replace(face + '.vmat', '').rstrip('_') + '.vmat'
            if face != 'bk': validMaterial = False


    if validMaterial:
        if os.path.exists(vmatFileName) and not OVERWRITE_VMAT:
            print('+ File already exists. Skipping!')
            continue

        with open(vmatFileName, 'w') as vmatFile:
            vmatFile.write('// Converted with vmt_to_vmat.py\n')
            vmatFile.write('// From: ' + fileName + '\n\n')
            dbg_msg("" + matType + " => " + vmatShader)
            vmatFile.write('Layer0\n{\n\tshader "' + vmatShader + '.vfx"\n\n')

            convertSpecials(vmtKeyValList)

            vmatFile.write(convertVmtToVmat(vmtKeyValList)) ###############################

            #check if base texture is empty
            #if "metal" in vmatFileName:
            #    vmatFile.write("\tg_flMetalness 1.000\n")

            vmatFile.write('}\n')

        vmatFile
        #with open(fileName) as f:
        #    with open(vmatFileName, "w") as f1:
        #        for line in f:
        #            f1.write(COMMENT + line)
        if DEBUG: print ('+ Converted: ' + fileName)
        print ('+ Saved at:  ' + vmatFileName)
        print ('---------------------------------------------------------------------------')
    
    else: print("+ Invalid material. Skipping!")


    if not matType:
        if DEBUG: debugContent += "Warning" + fileName + '\n'

print("Done with the materials...\nNow onto the images that need processing...")

for args in Late_Calls:
    createMaskFromChannel( *args )


########################################################################
# Build skybox cubemap from sky faces
# (blue_sky_up.tga, blue_sky_ft.tga, ...) -> blue_sky_cube.tga
# https://developer.valvesoftware.com/wiki/File:Skybox_Template.jpg
# https://learnopengl.com/img/advanced/cubemaps_skybox.png
for skyName in skyboxPath:

    #if True: break
    # what is l4d2 skybox/sky_l4d_rural02_ldrbk.pwl
    # TODO: decouple this in a separate script. face_to_cubemap_sky.py
    # write the sky face contents in a text file. allow manual sky map creation

    # TODO: !!!!! HOW DO I DO HDR FILES !!!!! '_cube.exr'
    # idea: convert to tiff

    faceCount = 0
    facePath = ''
    SkyCubeImage_Path = ''
    for face in skyboxFaces:
        facePath = skyboxPath[skyName][face].get('path')
        if not facePath: continue
        faceHandle = Image.open(formatFullDir(facePath))

        if not faceHandle: continue
        if((not skyboxPath[skyName][face].get('scale') or len(skyboxFaces) == skyboxFaces.index(face)+1) and (not skyboxPath[skyName][face].get('resolution'))):
            skyboxPath[skyName]['resolution'] = faceHandle.size
        skyboxPath[skyName][face]['handle'] = faceHandle
        faceCount += 1

    if not faceCount or not skyboxPath[skyName]['resolution']: continue

    face_w = face_h = skyboxPath[skyName]['resolution'][0]
    cube_w = 4 * face_w
    cube_h = 3 * face_h
    SkyCubeImage = Image.new('RGBA', (cube_w, cube_h), color = (0, 0, 0)) # alpha?

    for face in skyboxFaces:
        faceHandle = skyboxPath[skyName][face].get('handle')
        if not faceHandle: continue
        facePath = formatFullDir(skyboxPath[skyName][face]['path'])

        faceScale = skyboxPath[skyName][face].get('scale')
        faceRotate = skyboxPath[skyName][face].get('rotate')

        #dbg_msg("Using image", formatVmatDir(facePath), "for the", face, "face")
        vtfTexture = facePath.replace(TEXTURE_FILEEXT, '') + '.vtf'
        if REMOVE_VTF_FILES and os.path.exists(vtfTexture):
            os.remove(vtfTexture)
            print("~ Removed vtf file: " + formatVmatDir(vtfTexture))

        # TODO: i think top and bottom need to be rotated by 90 + side faces offset by x
        # check if front is below top and above bottom
        # move this inside the dict
        # Ahhhh https://github.com/TheAlePower/TeamFortress2/blob/1b81dded673d49adebf4d0958e52236ecc28a956/tf2_src/utils/splitskybox/splitskybox.cpp#L172
        if face == 'up':   facePosition = (cube_w - 3 * face_w, cube_h - 3 * face_h)
        elif face == 'ft': facePosition = (cube_w - 2 * face_w, cube_h - 2 * face_h)
        elif face == 'lf': facePosition = (cube_w - 1 * face_w, cube_h - 2 * face_h)
        elif face == 'bk': facePosition = (cube_w - 4 * face_w, cube_h - 2 * face_h)
        elif face == 'rt': facePosition = (cube_w - 3 * face_w, cube_h - 2 * face_h)
        elif face == 'dn': facePosition = (cube_w - 3 * face_w, cube_h - 1 * face_h)

        if faceHandle.width != face_w:
            faceHandle = faceHandle.resize((face_w, round(faceHandle.height * face_w/faceHandle.width)), Image.BICUBIC)

        if(skyboxPath[skyName][face].get('rotate')):
            dbg_msg("ROTATING `" + face + "` BY THIS: " + str(skyboxPath[skyName][face]['rotate']))
            faceHandle = faceHandle.rotate(int(skyboxPath[skyName][face]['rotate']))

        
        SkyCubeImage.paste(faceHandle, facePosition)
        faceHandle.close()

    if facePath:
        SkyCubeImage_Path = facePath.replace(TEXTURE_FILEEXT, '')[:-2].rstrip('_') + '_cube' + TEXTURE_FILEEXT
        SkyCubeImage.save(SkyCubeImage_Path)

    if os.path.exists(SkyCubeImage_Path):
        print('+ Successfuly created sky cubemap at: ' + SkyCubeImage_Path)

print("\nFinished! Your materials are now ready.")
dbg_msg("\n\n\n\n\n")
