

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

SHADER = 'vr_standard' # What shader to use.
TEXTURE_FILEEXT = '.tga' # File format of the textures.

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
    
    if not key.startswith('$'):
        return
        
    val = words[1].strip('\n')
    
    parameters[key] = val
    
def fixTexturePath(path):
    retPath = path.strip().strip('"')
    retPath = retPath.replace('\\', '/') # Convert paths to use forward slashes.
    retPath = retPath.replace('.vtf', '') # remove any old extensions
    retPath = '"materials/' + retPath + TEXTURE_FILEEXT + '"'
    return retPath

def fixVector(s):
    s = s.strip('"[]{} ') # some VMT vectors use {}
    parts = [str(float(i)) for i in s.split(' ')]
    extra = (' 0.0' * max(3 - s.count(' '), 0) )
    return '"[' + ' '.join(parts) + extra + ']"'


def getVmatParameter(key, val):
    key = key.strip('$').lower()
    
    # Dict for converting parameters
    convert = {
        #VMT paramter: VMAT parameter, value, additional lines to add. The last two variables take functions or strings, or None for using the old value.
        'basetexture': ('TextureColor', fixTexturePath, None),
        'bumpmap': ('TextureNormal', fixTexturePath, None),
        'envmap': ('F_SPECULAR', '1', '\tF_SPECULAR_CUBE_MAP 1\n\tF_SPECULAR_CUBE_MAP_PROJECTION 1\n\tg_flCubeMapBlurAmount "1.000"\n\tg_flCubeMapScalar "1.000"\n'), #Assumes env_cubemap
        'envmaptint': ('TextureReflectance', fixVector, None),
        'envmapmask': ('TextureReflectance', fixTexturePath, None),
        'color': ('g_vColorTint', None, None), #Assumes being used with basetexture
        'selfillum': ('g_flSelfIllumScale', '"1.000"', None),
        'selfillumtint': ('g_vSelfIllumTint', None, None),
        'selfillummask': ('TextureSelfIllumMask', fixTexturePath, None),
        'phongexponenttexture': ('TextureGlossiness', fixTexturePath, None),
        'translucent': ('F_TRANSLUCENT', None, '\tg_flOpacityScale "1.000"\n'),
        'additive': ('F_ADDITIVE_BLEND', None, None),
        'nocull': ('F_RENDER_BACKFACES', None, None),
        'decal':( 'F_OVERLAY', None, None),
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
    
    vmatFileName = fileName.replace('.vmt', '') + '.vmat'
    
    if os.path.exists(vmatFileName): continue
    
    print('Converting ' + os.path.basename(fileName))
    
    vmtParameters = {}

    with open(fileName, 'r') as vmtFile:
        for line in vmtFile.readlines():
            parseVMTParameter(line, vmtParameters)    

    with open(vmatFileName, 'w') as vmatFile:
        vmatFile.write('// Converted with vmt_to_vmat.py\n\n')
        vmatFile.write('Layer0\n{\n\tshader "' + SHADER + '.vfx"\n\n')
        for key, val in vmtParameters.items():
            vmatFile.write(getVmatParameter(key, val))
        if "metal" in vmatFileName:
            vmatFile.write("\tg_flMetalness 1.000\n")
            
        vmatFile.write('}\n')

# input("\nDone, press ENTER to continue...")
