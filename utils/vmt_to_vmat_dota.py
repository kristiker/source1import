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

import sys
import os
import re
from PIL import Image
import PIL.ImageOps    

GAMEISTF2 = True;
SHADER = 'hero' # What shader to use.
TEXTURE_FILEEXT = '.tga' # File format of the textures.
MAP_SUBSTRING = '_alpha' # substring added after an alpha map's name, but before the extension
PATH_TO_CONTENT_ROOT = 'F:/Programs/Steam/steamapps/common/dota 2 beta/content/dota_addons/hl2/' # this leads to the root of the game folder, i.e. dota 2 beta/content/dota_addons/tf/, make sure to remember the final /

def parseVMTParameter(line, parameters):
    words = []
    
    if line.startswith('\t') or line.startswith(' '):
        words = re.split(r'\s+', line, 2)
    else:
        words = re.split(r'\s+', line, 1)
        
    words = list(filter(len, words))
    if len(words) < 2:
        return 
        
    key = words[0].strip('"')
    
    if key.startswith('/'):
        return
    
    if not key.startswith('$'):
        return

    val = words[1].strip('\n')
    
    # remove comments, HACK
    commentTuple = val.partition('//')
    
    if(val.strip('"' + "'") == ""):
        print("no value found, moving on")
        return
    
    parameters[key] = commentTuple[0]
    
def fixTexturePath(path, addonString = ""):
    retPath = path.strip().strip('"')
    retPath = retPath.replace('\\', '/') # Convert paths to use forward slashes.
    retPath = retPath.replace('.vtf', '') # remove any old extensions
    retPath = '"materials/' + retPath + addonString + TEXTURE_FILEEXT + '"'
    return retPath

def fixVector(s):
    s = s.strip('"[]{} ') # some VMT vectors use {}
    parts = [str(float(i)) for i in s.split(' ')]
    extra = (' 0.0' * max(3 - s.count(' '), 0) )
    return '"[' + ' '.join(parts) + extra + ']"'

def extractAlphaTextures(localPath):
    image_path = PATH_TO_CONTENT_ROOT + localPath
    mask_path = PATH_TO_CONTENT_ROOT + localPath[:-4] + "_alpha.tga"

    # Open the image and convert it to RGBA, just in case it was indexed
    image = Image.open(image_path).convert('RGBA')

    # Extract just the alpha channel
    alpha = image.split()[-1]

    # Unfortunately the alpha channel is still treated as such and can't be dumped
    # as-is

    # Create a new image with an opaque black background
    bg = Image.new("RGBA", image.size, (0,0,0,255))

    # Copy the alpha channel to the new image using itself as the mask
    bg.paste(alpha, mask=alpha)

    # Since the bg image started as RGBA, we can save some space by converting it
    # to grayscale ('L') Optionally, we can convert the image to be indexed which
    # saves some more space ('P') In my experience, converting directly to 'P'
    # produces both the Gray channel and an Alpha channel when viewed in GIMP,
    # althogh the file sizes is about the same
    bg.convert('L').convert('P', palette=Image.ADAPTIVE, colors=8).save(
                                                                    mask_path,
                                                                    optimize=True)
                                                                    
def flipNormalMap(localPath):
    image_path = PATH_TO_CONTENT_ROOT + localPath
    #mask_path = PATH_TO_CONTENT_ROOT + localPath[:-4] + "_alpha.tga"

    # Open the image and convert it to RGBA, just in case it was indexed
    image = Image.open(image_path).convert('RGBA')

    # Extract just the green channel
    r,g,b,a = image.split()

    g = PIL.ImageOps.invert(g)

    final_transparent_image = Image.merge('RGBA', (r,g,b,a))
    
    final_transparent_image.save(image_path)

#flipNormalMap("materials/models/player/demo/demoman_normal.tga")
    
#extractAlphaTextures("materials/models/bots/boss_bot/carrier_body.tga")

def getVmatParameter(key, val):
    key = key.strip('$').lower()
    
    # Dict for converting parameters
    convert = {
        #VMT paramter: VMAT parameter, value, additional lines to add. The last two variables take functions or strings, or None for using the old value.
        # fixTexturePath(val, "_test") if you want to add a value to the end of a path but before .tga
        'basetexture': ('TextureColor', fixTexturePath, '\tg_flAmbientScale "0.000"\n', False), # use this for default variables too, like ambient scale
        'bumpmap': ('TextureNormal', fixTexturePath, None, False),
        'color': ('g_vColorTint', None, None, False), #Assumes being used with basetexture
        'translucent': ('F_TRANSLUCENT', None, '\tg_flOpacityScale "1.000"\n', True),
		'alphatest': ('F_ALPHA_TEST', None, '\tg_flAlphaTestReference "0.500"\n', True),
        'additive': ('F_ADDITIVE_BLEND', None, None, True),
        'nocull': ('F_RENDER_BACKFACES', None, None, True),
        'decal':( 'F_OVERLAY', None, None, True),
        
        'envmap': ('F_SPECULAR', '1', '\tF_SPECULAR_CUBE_MAP 1\n\tF_SPECULAR_CUBE_MAP_PROJECTION 1\n\tg_flCubeMapBlurAmount "1.000"\n\tg_flCubeMapScalar "1.000"\n', True), #Assumes env_cubemap
        'envmaptint': ('TextureReflectance', fixVector, None, False),
        'envmapmask': ('TextureReflectance', fixTexturePath, None, False),
		
        # we don't need detail mask or any of this stuff unless the user chooses to
        'selfillum': ('g_flSelfIllumScale', '"1.000"', '\tF_MASKS_1 1\n\tTextureDetailMask "[0.000000 0.000000 0.000000 0.000000]"\n\tTextureDiffuseWarpMask "[0.000000 0.000000 0.000000 0.000000]"\n\tTextureMetalnessMask "[0.000000 0.000000 0.000000 0.000000]"\n', True),
        'selfillumtint': ('g_vSelfIllumTint', None, None, False),
        'selfillummask': ('TextureSelfIllumMask', fixTexturePath, None, False),
		
		'phong': ('g_flSpecularScale', None, '\tF_MASKS_2 1\n', True),
		'phongexponent': ('g_flSpecularExponent', None, None, False),
        'phongfresnelranges': ('//fresnelcomment', None, None, False),
        #'phongexponenttexture': ('TextureSpecularMask', fixTexturePath, None),
		
		'rimlight': ('g_flRimLightScale', None, '\tF_MASKS_2 1\n', False),
		'rimexponent': ('g_flRimLightScale', None, None, False),
		#'rimmask': ('TextureRimMask', None, None, True),
		
		'lightwarptexture': ('TextureFresnelWarpSpec', fixTexturePath, '\tTextureFresnelWarpColor ' + fixTexturePath(val) + '\n', False),
		
        # currently blanking this because TF2 uses detail for fire textures
		#'detail': ('TextureDetail', fixTexturePath, '\tF_DETAIL 1\n'),
		#'detailscale': ('g_vDetailTexCoordScale', '"[' + val + ' ' + val + ']"', None),
		#'detailblendfactor': ('g_flDetailBlendFactor', None, None),
		#note to self: create a function to fix values?
		}
        
    if key in convert:
        outValue = val
        additionalLines = ''
        
        if isinstance(convert[key][1], str):
            outValue = convert[key][1]
        elif hasattr(convert[key][1], '__call__'):
            outValue = convert[key][1](val)

        if isinstance(convert[key][2], str):
            additionalLines = convert[key][2]
        elif hasattr(convert[key][2], '__call__'):
            additionalLines = convert[key][2](val)
            
        '''if isinstance(convert[key][3], bool):
            if(val.replace('"', '') == "0" or val.replace('"', '') == "false"):
                return ''
        elif hasattr(convert[key][3], '__call__'):
            print("Error: no bool at the end of dict!!")
            return ''
            '''
        
        return '\t' + convert[key][0] + ' ' + outValue + '\n' + additionalLines
        
    return ''

def parseDir(dirName):
    files = []
    for root, dirs, fileNames in os.walk(dirName):
        for fileName in fileNames:	
            if fileName.lower().endswith('.vmt'):
                files.append(os.path.join(root,fileName))
            
    return files

print('\nSource 2 Material Conveter\n')

fileList = []

for filePath in sys.argv:
    absFilePath = os.path.abspath(filePath)
    if os.path.isdir(absFilePath):
        fileList.extend(parseDir(absFilePath))
    else:
        if absFilePath.lower().endswith('.vmt'):
            fileList.append(absFilePath)

    
for fileName in fileList:
    
    vmtParameters = {}
    # material types need to be lowercase because python is a bit case sensitive
    materialTypes = [
    "vertexlitgeneric",
    "unlitgeneric",
    "lightmappedgeneric",
    #"modulate",
    #"water", #TODO: integrate water/refract shaders into this script
    #"refract"
    #"lightmapped_4wayblend",
    #"lightmappedreflective",
    #"cables"
    ]
    validMaterial = False;
    
    basetexturePath = ""
    bumpmapPath = ""
    phong = False; #also counts for rimlight since they feed off each other
    baseMapAlphaPhongMask = False
    selfIllum = False
    translucent = False #also counts for alphatest
    
    with open(fileName, 'r') as vmtFile:
        for line in vmtFile.readlines():
            if any(wd in line.lower() for wd in materialTypes):
                validMaterial = True
            parseVMTParameter(line, vmtParameters)
    
    if validMaterial:
        print('Converting ' + os.path.basename(fileName))
        
        vmatFileName = fileName.replace('.vmt', '') + '.vmat'
        
        if os.path.exists(vmatFileName): continue
        
        with open(vmatFileName, 'w') as vmatFile:
            vmatFile.write('// Converted with vmt_to_vmat.py\n\n')
            vmatFile.write('Layer0\n{\n\tshader "' + SHADER + '.vfx"\n\n')
            for key, val in vmtParameters.items():
                vmatFile.write(getVmatParameter(key, val))
                if(key.lower() == "$phong" or key.lower() == "$rimlight"):
                    if val.strip('"' + "'") != "0":
                        phong = True
                elif(key.lower() == "$basemapalphaphongmask"):
                    if val.strip('"' + "'") != "0":
                        baseMapAlphaPhongMask = True
                elif(key.lower() == "$selfillum"):
                    if val.strip('"' + "'") != "0":
                        selfIllum = True
                elif(key.lower() == "$translucent" or key == "$alphatest"):
                    if val.strip('"' + "'") != "0":
                        translucent = True
                elif(key.lower() == "$basetexture"):
                    basetexturePath = val.lower()
                elif(key.lower() == "$bumpmap"):
                    bumpmapPath = val.lower()
            
            if "metal" in vmatFileName:
                vmatFile.write("\tg_flMetalness 1.000\n")
            
            if translucent:
                vmatFile.write('\tTextureTranslucency ' + fixTexturePath(basetexturePath, MAP_SUBSTRING) + '\n')
                extractAlphaTextures("materials/" + basetexturePath.replace('"', '') + TEXTURE_FILEEXT)
                
            if phong:
                if baseMapAlphaPhongMask:
                    vmatFile.write('\tTextureRimMask ' + fixTexturePath(basetexturePath, MAP_SUBSTRING) + '\n\tTextureSpecularMask ' + fixTexturePath(basetexturePath, MAP_SUBSTRING) + '\n')
                    extractAlphaTextures("materials/" + basetexturePath.replace('"', '') + TEXTURE_FILEEXT)
                else:
                    if(bumpmapPath == ''):
                        vmatFile.write('\tTextureSpecularMask "[1.000000 1.000000 1.000000 0.000000]"\n\tTextureRimMask "[1.000000 1.000000 1.000000 0.000000]"\n')
                        extractAlphaTextures("materials/" + basetexturePath.replace('"', '') + TEXTURE_FILEEXT)
                    else:
                        vmatFile.write('\tTextureSpecularMask ' + fixTexturePath(bumpmapPath, MAP_SUBSTRING) + '\n\tTextureRimMask ' + fixTexturePath(bumpmapPath, MAP_SUBSTRING) + '\n')
                        extractAlphaTextures("materials/" + bumpmapPath.replace('"', '') + TEXTURE_FILEEXT)
            
            if (selfIllum):
                vmatFile.write('\tTextureSelfIllumMask ' + fixTexturePath(basetexturePath, MAP_SUBSTRING) + '\n')
                extractAlphaTextures("materials/" + basetexturePath.replace('"', '') + TEXTURE_FILEEXT)
            
            vmatFile.write('}\n')
    
    bumpmapConvertedList = PATH_TO_CONTENT_ROOT + "convertedBumpmaps.txt"
    print(bumpmapConvertedList)
    #if os.path.exists(bumpmapConvertedList): continue
    
    # flip the green channels of any normal maps
    if(bumpmapPath != ""):
        foundMaterial = False
        with open(bumpmapConvertedList, 'r+') as bumpList: #change the read type to write
            for line in bumpList.readlines():
                if line.rstrip() == bumpmapPath.rstrip():
                    foundMaterial = True
        
            if not foundMaterial:
                flipNormalMap(fixTexturePath(bumpmapPath).strip("'" + '"'))
                print("flipped normal map")
                #append bumpmapPath to bumpmapCovertedList
                bumpList.write(bumpmapPath + "\n")
                bumpList.close()
        
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
