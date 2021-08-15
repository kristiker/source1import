from pathlib import Path
from shutil import copyfile
from difflib import get_close_matches
from PIL import Image, ImageOps

from shared import base_utils2 as sh
from shared.keyvalue_simple import getKV_tailored as getKeyValues
from shared.keyvalues1 import KV
from shared.materials.proxies import ProxiesToDynamicParams

import time
import shared.materials.skybox as sky
import numpy as np
from shared import PFM

# generic, blend instead of vr_complex, vr_simple_2wayblend etc...
LEGACY_SHADER = False
NEW_SH = not LEGACY_SHADER

# Path to content root, before /materials/

# Set this to True if you wish to overwrite your old vmat files. Same as adding -f to launch parameters
OVERWRITE_VMAT = True
OVERWRITE_SKYBOX_VMATS = True
OVERWRITE_SKYCUBES = True

# True to let vtex handle the inverting of the normalmap.
NORMALMAP_G_VTEX_INVERT = True

BASIC_PBR = True
MISSING_TEXTURE_SET_DEFAULT = True
USE_SUGESTED_DEFAULT_ROUGHNESS = True
SURFACEPROP_AS_IS = False

sh.DEBUG = False
msg = sh.msg
# File format of the textures. Needs to be lowercase
# source 2 supports all kinds: tga jpeg png gif psd exr tiff pfm...
TEXTURE_FILEEXT = ".tga"
IN_EXT = ".vmt"
OUT_EXT = ".vmat"
SOURCE2_SHADER_EXT = ".vfx"

VMAT_DEFAULT_PATH = Path("materials/default")

materials = Path("materials")
skyboxmaterials = materials / "skybox"
legacy_skyfaces = skyboxmaterials / "legacy_faces"

sh.importing = materials

skybox = Path("skybox")
SKY_FACES = ('up', 'dn', 'lf', 'rt', 'bk', 'ft')

class ValveMaterial:
    def __init__(self, shader, kv):
        self._shader = shader
        self._kv = kv

    @property
    def _KV(self): return self._kv

    @property
    def shader(self): return self._shader

class VMT(ValveMaterial):

    ver = 1  # materialsystem1
    __defaultkv = ('', {})  # unescaped, supports duplicates, keys case insensitive

    shader = ValveMaterial.shader
    KeyValues = ValveMaterial._KV

    def __init__(self, kv=None):

        if kv is None:
            kv = KV(*self.__defaultkv)
        if kv.keyName == '':
            kv.keyName = 'Wireframe_DX9'

        super().__init__(kv.keyName, kv)

    @KeyValues.setter
    def KeyValues(self, n):
        if isinstance(n, KV):  # change entire material
            self._kv = n
            self._shader = n.keyName
        elif isinstance(n, dict):  # change body, keep shader (VMT.KeyValues = { })
            self._kv = KV(self._shader, n)
        else:
            try: n = KV(*n)  # FIXME shit shit
            except Exception as ex:
                raise ValueError("Can only assign `kv1`, `dict` or similar to VMT KeyValues, not %s" % type(n))

    @KeyValues.deleter
    def KeyValues(self):
        self._kv = self.__defaultkv
        del self.shader

    @shader.setter  #  @ValveMaterial.shader.setter
    def shader(self, n):
        self._kv.keyName = n
        self._shader = n

    @classmethod
    def FromDict(cls, shader="error", dict={ }):
        kv = KV(shader, dict)
        return cls(kv)
    def WriteToFile(self, file):
        ...

class VMAT(ValveMaterial):

    ver = 2   # materialsystem2
    __defaultkv = ('Layer0', {'shader': 'error.vfx'})  # unescaped, keys case sensitive

    shader = ValveMaterial.shader
    KeyValues = ValveMaterial._KV

    def __init__(self, kv=None):
        if kv is None:
            kv = KV(*self.__defaultkv)
        super().__init__(kv.get('shader') or 'error.vfx', kv)

    @shader.getter
    def shader(self):
        return self._shader[:-len(SOURCE2_SHADER_EXT)]

    @shader.setter
    def shader(self, n: str):
        if not n.endswith(SOURCE2_SHADER_EXT): n += SOURCE2_SHADER_EXT
        self._shader = n
        self._kv['shader'] = n

# keep everything lowercase !!!
shaderDict = {
    "black":                "black",
    "sky":                  "sky",
    "unlitgeneric":         "vr_complex",
    "vertexlitgeneric":     "vr_complex",
    "decalmodulate":        "vr_projected_decals",  # https://developer.valvesoftware.com/wiki/Decals#DecalModulate
    "lightmappedgeneric":   "vr_complex",
    "lightmappedreflective":"vr_complex",
    "character":            "vr_complex",  # https://developer.valvesoftware.com/wiki/Character_(shader)
    "customcharacter":      "vr_complex",
    "teeth":                "vr_complex",
    "water":                "simple_water",
    "refract":              "refract",
    "worldvertextransition":"vr_simple_2way_blend",
    "lightmapped_4wayblend":"vr_simple_2way_blend",
    "cables":               "cables",
    "lightmappedtwotexture":"vr_complex",  # 2 multiblend $texture2 nocull scrolling, model, additive.
    "unlittwotexture":      "vr_complex",  # 2 multiblend $texture2 nocull scrolling, model, additive.
    "cable":                "cables",
    "splinerope":           "cables",
    "shatteredglass":       "vr_glass",
    "wireframe":            "tools_wireframe",
    "wireframe_dx9":        "error",
    "spritecard":           "spritecard",  # "modulate",
    #"subrect":              "spritecard",  # should we just cut? $Pos "256 0" $Size "256 256" $decalscale 0.25 decals\blood1_subrect.vmt
    #"weapondecal": weapon sticker
    "patch":                "vr_complex", # fallback if include doesn't have one
}

def chooseShader():
    d = {x:0 for x in list(shaderDict.values())}

    if vmt.shader not in shaderDict:
        if sh.DEBUG:
            failureList.add(f"{vmt.shader} unsupported shader", vmt.path)
        return "vr_black_unlit"

    if LEGACY_SHADER:   d["generic"] += 1
    else:               d[shaderDict[vmt.shader]] += 1

    if vmt.KeyValues['$decal'] == 1: d["vr_projected_decals"] += 10

    if vmt.shader == "worldvertextransition":
        if vmt.KeyValues['$basetexture2']: d["vr_simple_2way_blend"] += 10

    elif vmt.shader == "lightmappedgeneric":
        if vmt.KeyValues['$newlayerblending'] == 1: d["vr_simple_2way_blend"] += 10
        #if vmt.KeyValues['$decal'] == 1: sh["vr_projected_decals"] += 10

    elif vmt.shader == "":
        pass
    # TODO: vr_complex -> vr simple if no selfillum tintmask detailtexture specular
    return max(d, key = d.get)

ignoreList = [ "dx9", "dx8", "dx7", "dx6", "proxies"]

def default(texture_type):
    return VMAT_DEFAULT_PATH.as_posix() + "/default" + texture_type + ".tga"

def OutName(path: Path) -> Path:
    #if path.local.is_relative_to(materials/skybox/) and path.stem[-2:] in sky.skyboxFaces:
    #    sh.output(path).without_spaces().with_suffix(OUT_EXT)
    return sh.output(path).without_spaces().with_suffix(OUT_EXT)

def OutName_Sky(path: Path) -> Path:
    "materials/skybox/legacy_faces/sky_example.json -> materials/skybox/sky_example.vmat"
    return path.parents[1] / path.without_spaces().with_suffix(OUT_EXT).name

# "environment maps\metal_generic_002.vtf" -> "materials/environment maps/metal_generic_002.tga"
def fixVmtTextureDir(localPath, fileExt = TEXTURE_FILEEXT) -> str:
    if localPath == "" or not isinstance(localPath, str):
        return ""
    return (materials / localPath.lstrip('\\/')).with_suffix(fileExt).as_posix()

# TODO: renameee, remap table etc...
def formatNewTexturePath(vmtPath, textureType = TEXTURE_FILEEXT, noRename = False, forReal = True):

    #vmtPath = sh.src(fixVmtTextureDir(vmtPath)) + "." + textureType.split(".", 1)[1] or ''

    #if USE_DEFAULT_FOR_MISSING_TEXTURE and not os.path.exists(vmtPath):
    #    return default(textureType)

    #return vmtPath.local
    return str(fixVmtTextureDir(vmtPath))

def getTexture(vtf_path):
    "get vtf source"
    # TODO: if still not found check for vtf in input
    # if exists, use vtf_to_tga to extract it to output
    # source1import does the same
    return None

def createMask(image_path, copySub = '_mask', channel = 'A', invert = False, queue = True):

    if not (image_path:=fixVmtTextureDir(image_path)):
        return default(copySub)
    image_path = sh.output(Path(image_path))

    newMaskPath = image_path.parent /\
        f"{image_path.stem}_{channel[:3].lower()}{'-1' if invert else ''}{copySub + image_path.suffix}"

    msg(f"createMask{image_path.local.relative_to(materials).as_posix(), copySub, channel, invert, queue} -> {newMaskPath.local}")

    if newMaskPath.exists(): #and not DEBUG:
        return newMaskPath.local

    if not image_path.exists():
        msg("Couldn't find image", image_path)
        failureList.add(f"createMask not found", f'{vmt.path} - {image_path}')
        #if vmtTexture in vmt_to_vmat['textures']:
        #    failureList.add(f"{vmtTexture} not found", vmt.path) # FIXME ALL OF ME vmtTexture
        #else:
        return default(copySub)

    if not image_path.is_file() or not image_path.exists():
        failureList.add('createMask image not found', vmt.path)
        print(f"~ ERROR: Couldn't find requested image ({image_path}). Please check.")
        return default(copySub)

    image = Image.open(image_path).convert('RGBA')

    if channel == 'L':
        imgChannel = image.convert('L')
    else:
        imgChannel = image.getchannel(str(channel))

    if invert:
        imgChannel = ImageOps.invert(imgChannel)

    colors = imgChannel.getcolors()
    if len(colors) == 1:  # mask with single color
        if copySub == "_rough" and colors[0][1] == 0:  # fix some very dumb .convert('RGBA') with 255 255 255 alpha
            return default(copySub)  # TODO: should this apply to other types of masks as well?
        return fixVector(f"{{{colors[0][1]} {colors[0][1]} {colors[0][1]}}}", True)

    bg = Image.new("L", image.size)

    # Copy the specified channel to the new image using itself as the mask
    bg.paste(imgChannel)

    bg.convert('L').save(newMaskPath, optimize=True)  #.convert('P', palette=Image.ADAPTIVE, colors=8)
    bg.close()
    print("+ Saved mask to", newMaskPath.local)

    return newMaskPath.local

########################################################################
# Build sky cubemap from sky faces
# (blue_sky_up.tga, blue_sky_ft.tga, ...) -> blue_sky_cube.tga
# https://developer.valvesoftware.com/wiki/File:Skybox_Template.jpg
# https://learnopengl.com/img/advanced/cubemaps_skybox.png
# ----------------------------------------------------------------------
def createSkyCubemap(skyName: str, faceP: dict, maxFaceRes: int = 0) -> Path:

    # read friendly json -> code friendly data
    faceList, faceParams = {}, {}

    hdrType = faceP.get('_hdrtype')

    for face in SKY_FACES:
        if not (v := faceP.get(face)): continue
        facePath = v.get('path') if isinstance(v, dict) else v
        if not facePath:
            continue
        if not ( facePath := sh.output(facePath) ).is_file():
            del faceP[face]
            continue
        faceList[face] = facePath
        faceParams[face] = {}
        if isinstance(faceP[face], dict):
            faceParams[face].update(faceP[face])
        if (hdrType == 'uncompressed'):
            size = PFM.read_pfm(facePath)[2]
        else:
            size = Image.open(facePath).size
        faceParams[face]['size'] = size
        # the largest face determines the resolution of the full image
        maxFaceRes = max(maxFaceRes, max(size[0], size[1]))

    cube_w = 4 * maxFaceRes
    cube_h = 3 * maxFaceRes

    # skyName = skyName.rstrip('_')
    img_ext = '.pfm' if hdrType else TEXTURE_FILEEXT
    sky_cubemap_path =  sh.output( skyboxmaterials / (skyName + '_cube' + img_ext))

    # BlendCubeMapFaceCorners, BlendCubeMapFaceEdges
    
    if OVERWRITE_SKYCUBES and sky_cubemap_path.is_file():
        return sky_cubemap_path

    if hdrType in (None, 'compressed'):
        image_mode = 'RGBA' if (hdrType == 'compressed') else 'RGB'
        SkyCubemapImage = Image.new(image_mode, (cube_w, cube_h), color = (0, 0, 0))

        for face, facePath in faceList.items():
            faceScale = faceParams[face].get('scale')
            faceRotate = int(faceParams[face].get('rotate') or 0)
            if not (faceImage := Image.open(facePath).convert(image_mode)): continue

            pasteCoord = (cube_w/2, cube_h/2)
            if face == 'up':
                pasteCoord = ( cube_w - (maxFaceRes * 3) , cube_h - (maxFaceRes * 3) ) # (1, 2)
                faceRotate += 90
            elif face == 'ft': pasteCoord = ( cube_w - (maxFaceRes * 1) , cube_h - (maxFaceRes * 2) ) # (2, 3) -> (2, 4) #2)
            elif face == 'lf': pasteCoord = ( cube_w - (maxFaceRes * 4) , cube_h - (maxFaceRes * 2) ) # (2, 4) -> (2, 1) #1)
            elif face == 'bk': pasteCoord = ( cube_w - (maxFaceRes * 3) , cube_h - (maxFaceRes * 2) ) # (2, 1) -> (2, 2) #4)
            elif face == 'rt': pasteCoord = ( cube_w - (maxFaceRes * 2) , cube_h - (maxFaceRes * 2) ) # (2, 2) -> (2, 3) #3)
            elif face == 'dn':
                pasteCoord = ( cube_w - (maxFaceRes * 3) , cube_h - (maxFaceRes * 1) ) # (3, 2)
                faceRotate += 90

            # scale to fit on the y axis
            if faceImage.width != maxFaceRes:
                faceImage = faceImage.resize((maxFaceRes, round(faceImage.height * maxFaceRes/faceImage.width)), Image.BICUBIC)

            if faceRotate:
                faceImage = faceImage.rotate(faceRotate)

            SkyCubemapImage.paste(faceImage, pasteCoord)
            faceImage.close()

        # for hdr compressed: uncompress the whole tga map we just created and paste to pfm
        if (hdrType == 'compressed'):
            compressedPixels = SkyCubemapImage.load()
            stamp = time.time()
            hdrImageData = [0] * (cube_w * cube_h * 3) # TODO: numpy array
            cell = 0
            for x in range(cube_w):
                for y in range(cube_h):
                    R, G, B, A = compressedPixels[x,y] # image.getpixel( (x,y) )
                    hdrImageData[cell    ] = (R * (A * 16)) / 262144
                    hdrImageData[cell + 1] = (G * (A * 16)) / 262144
                    hdrImageData[cell + 2] = (B * (A * 16)) / 262144
                    cell += 3
            SkyCubemapImage.close()
            # questionable 90deg rotations
            HDRImageDataArray = np.rot90(np.array(hdrImageData, dtype='float32').reshape((cube_w, cube_h, 3)))
            PFM.write_pfm(sky_cubemap_path, HDRImageDataArray)
            print(f"It took: {time.time()-stamp} seconds!")
        else:
            SkyCubemapImage.save(sky_cubemap_path)
            #print('+ Successfuly created sky cubemap:', sky_cubemap_path.name)

    # hdr uncompressed: join the pfms same way as tgas TODO: ...
    elif hdrType == 'uncompressed':
        #emptyData = [0] * (cube_w * cube_h)
        #emptyArray = np.array(emptyData, dtype='float32').reshape((maxFace_h, maxFace_w, 3)
        #for face in skyboxFaces:
        #    if not (facePath := os.path.join("materials\\skybox", vmtSkybox[skyName][face].get('path'))): continue
        #    floatData, scale, _ = PFM.read_pfm(fs.Output(facePath))
        #for i in range(12):
        #    pass
        #    # paste each
        return

    return sky_cubemap_path

def flipNormalMap(localPath):

    image_path = sh.output(localPath)
    if not image_path.exists(): return False

    if NORMALMAP_G_VTEX_INVERT:
        if (settings_file := image_path.with_suffix(".txt")).exists():
            if sh.get_crc(settings_file) != '69D57F2B':
                settKV = KV.FromFile(settings_file)
                if settKV.keyName != 'settings':
                    settKV.keyName = 'settings'
                settKV["legacy_source1_inverted_normal"] = 1
                settKV.save(settings_file)
        else:
            with open(settings_file, 'w') as settingsFile:
                #settingsFile.write('"settings"\n{\t"legacy_source1_inverted_normal"\t"1"\n}')
                settingsFile.write('"settings"\n{\n\tlegacy_source1_inverted_normal\t"1"\n}\n')
    else:
        # Open the image and convert it to RGBA, just in case it was indexed
        image = Image.open(image_path).convert('RGBA')

        r,g,b,a = image.split()
        g = ImageOps.invert(g)
        final_transparent_image = Image.merge('RGBA', (r,g,b,a))
        final_transparent_image.save(image_path)

    return True

def fixVector(s, addAlpha = 1, returnList = False):

    s = str(s)
    if('{' in s or '}' in s): likelyColorInt = True
    else: likelyColorInt = False

    s = s.strip()  # TODO: remove letters
    s = s.replace('"', '').replace("'", "")
    s = s.strip().replace(",", "").strip('][}{').strip(')(')

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

surfprop_list = sh.GetJson(Path(__file__).parent / "shared/surfproperties.json")['hlvr']
# TODO: ideally, we want to import our legacy surfaceprops and use those instead of whatever is closest
def fixSurfaceProp(vmtVal):

    if SURFACEPROP_AS_IS or (vmtVal in ('default', 'default_silent', 'no_decal', 'player', 'roller', 'weapon')):
        return vmtVal

    elif vmtVal in surfprop_force:
        return surfprop_force[vmtVal]

    if("props" in vmat.path.parts): match = get_close_matches('prop.' + vmtVal, surfprop_list, 1, 0.4)
    else: match = get_close_matches('world.' + vmtVal, surfprop_list, 1, 0.6) or get_close_matches(vmtVal, surfprop_list, 1, 0.6)

    return match[0] if match else vmtVal

def presence(_, rv=1):
    return rv

def fix_envmap(vmtVal):
    if 'environment maps/metal' in vmtVal:
        vmt.KeyValues['$metalness'] = 0.888
    elif 'env_cubemap' == vmtVal:
        vmat.KeyValues['F_SPECULAR_CUBE_MAP'] = 1
    else:
        vmat.KeyValues['F_SPECULAR_CUBE_MAP'] = 2
        vmat.KeyValues['TextureCubeMap'] = "formatN"#TODO
    return 1  # presence()


def int_val(vmtVal, bInvert = False):
    if bInvert: vmtVal = not int(vmtVal)
        #return str(int(not int(vmtVal)))
    return int(vmtVal)

def mapped_val(vmtVal, dMap):
    if not vmtVal or vmtVal not in dMap:
        return None  # use default value
    return int(dMap[vmtVal])

def float_val(vmtVal):
    return "{:.6f}".format(float(vmtVal.strip(' \t"')))

def vmat_layered_param(vmatKey, layer = 'A', force = False):
    if vmat.shader == "vr_simple_2way_blend" or force:
        return vmatKey + layer
    return vmatKey


class TexTransform:
    def __init__(self, legacyMatrix):

        self.center     = 0.5, 0.5  # defines the point of rotation. Only useful if rotate is being used.
        self.scale      = 1, 1      # fits the texture into the material the given number of times. '2 1' is a 50% scale in the X axis.
        self.rotate     = 0         # rotates the texture counter-clockwise in degrees. Accepts any number, including negatives.
        self.translate  = 0, 0      # shifts the texture by the given numbers. '.5' will shift it half-way.

        if legacyMatrix:
            self._readLegacyMatrix(legacyMatrix)

    def _readLegacyMatrix(self, s):
        #  scale %f %f translate %f %f rotate %f (count 5, assumed center syntax)
        #  center %f %f scale %f %f rotate %f translate %f %f (count 7)
        s = s.strip('"')
        mxTerms = [i.strip("'") for i in s.split(' ')]

        for i, term in enumerate(mxTerms):

            try: nextTerm = float(mxTerms[i+1])
            except: continue

            if term == 'rotate':
                self.rotate = nextTerm
                continue

            try: nextnextTerm =  float(mxTerms[i+2])
            except: continue

            if term in ('center', 'scale', 'translate'):
                setattr(self, term, (nextTerm, nextnextTerm))

def is_convertible_to_float(value):
    try: float(value)
    except: return False
    else: return True


VMAT_REPLACEMENT = 0
VMAT_DEFAULTVAL = 1
VMAT_TRANSLFUNC = 2
VMAT_EXTRALINES = 3

IMPORT_MOD = "csgo"
EXPORT_MOD = "hlvr"


vmt_to_vmat = {

# http://counter-strike.net/workshop/workshopmaps#hammer
'f_keys': {

    '$translucent':     ('F_TRANSLUCENT',           '1'),  # "F_BLEND_MODE 0" for "vr_projected_decals"
    '$alphatest':       ('F_ALPHA_TEST',            '1'),
    '$phong':           ('F_SPECULAR',              '1'), # why did i do this
    '$envmap':          ('F_SPECULAR',              '1', [fix_envmap]),  # in "environment maps/metal" | "env_cubemap" F_SPECULAR_CUBE_MAP 1 // In-game Cube Map
    '$envmapanisotropy':('F_SPECULAR_CUBE_MAP_ANISOTROPIC_WARP', '1'), # requires F_ANISOTROPIC_GLOSS 1
    '$selfillum':       ('F_SELF_ILLUM',            '1'),
    '$additive':        ('F_ADDITIVE_BLEND',        '1'),
    '$ignorez':         ('F_DISABLE_Z_BUFFERING',   '1'),
    '$nocull':          ('F_RENDER_BACKFACES',      '1'),  # F_NO_CULLING 1 # see this for certain sheeted texs -> F_USE_SHEETS 1
    '$decal':           ('F_OVERLAY',               '1'),
    '$flow_debug':      ('F_FLOW_DEBUG',            '0'),
    '$detailblendmode': ('F_DETAIL_TEXTURE',        '1', [mapped_val, {'0':'1', '1':'2', '12':'0'} ]),  # https://developer.valvesoftware.com/wiki/$detail#Parameters_and_Effects
    '$decalblendmode':  ('F_DETAIL_TEXTURE',        '1', [mapped_val, {'0':'1', '1':'2', '12':'0'} ]),  # materialsystem\stdshaders\BaseVSShader.h#L26
    '$sequence_blend_mode': ('F_FAST_SEQUENCE_BLEND_MODE', '1', [mapped_val, {'0':'1', '1':'2', '2':'3'}]),

    '$selfillum_envmapmask_alpha': ('F_SELF_ILLUM', '1'),

    "$masks1": ('F_MASKS_1',    '1') if EXPORT_MOD == "dota" else None,  #
    "$masks2": ('F_MASKS_2',    '1') if EXPORT_MOD == "dota" else None,  #

    #'$phong':           ('F_PHONG',                 '1'),
    #'$vertexcolor:      ('F_VERTEX_COLOR',          '1'),
},

'textures': {
    # for the individual faces; the sky material is handled separately
    '$hdrcompressedtexture':('TextureColor',    '_color', [formatNewTexturePath]),  # compress
    '$hdrbasetexture':      ('TextureColor',    '_color', [formatNewTexturePath]),  # nocompress

    ## Top / Main layer
    '$basetexture':     ('TextureColor',        '_color',   [formatNewTexturePath]),
    '$painttexture':    ('TextureColor',        '_color',   [formatNewTexturePath]),
    '$material':        ('TextureColor',        '_color',   [formatNewTexturePath]),
    '$compress':        ('TextureSquishColor',  '_color',   [formatNewTexturePath], ('F_MORPH_SUPPORTED', 1), ('F_WRINKLE', 1)),
    '$stretch':         ('TextureStretchColor', '_color',   [formatNewTexturePath], ('F_MORPH_SUPPORTED', 1), ('F_WRINKLE', 1)),

    '$normalmap':       ('TextureNormal',       '_normal',  [formatNewTexturePath]),  # also covers $bumpmap
    '$bumpcompress':    ('TextureSquishNormal', '_normal',  [formatNewTexturePath], ('F_MORPH_SUPPORTED', 1), ('F_WRINKLE', 1)),
    '$bumpstretch':     ('TextureStretchNormal','_normal',  [formatNewTexturePath], ('F_MORPH_SUPPORTED', 1), ('F_WRINKLE', 1)),

    ## Layer blend mask
    '$blendmodulatetexture':\
                        ('TextureMask',             '_mask',   [createMask, 'G', False], ('F_BLEND', 1)) if NEW_SH else \
                        ('TextureLayer1RevealMask', '_blend',  [createMask, 'G', False], ('F_BLEND', 1)),
    ## Layer 1
    '$basetexture2':    ('TextureColorB' if NEW_SH else 'TextureLayer1Color',  '_color',  [formatNewTexturePath]),
    '$texture2':        ('TextureColorB' if NEW_SH else 'TextureLayer1Color',   '_color',  [formatNewTexturePath]),  # UnlitTwoTexture
    '$bumpmap2':        ('TextureNormalB' if NEW_SH else 'TextureLayer1Normal', '_normal', [formatNewTexturePath], None if NEW_SH else ('F_BLEND_NORMALS',  1)),

    ## Layer 2-3
    '$basetexture3':    ('TextureLayer2Color',  '_color',  [formatNewTexturePath]),
    '$basetexture4':    ('TextureLayer3Color',  '_color',  [formatNewTexturePath]),

    '$normalmap2':      ('TextureNormal2',      '_normal', [formatNewTexturePath],     ('F_SECONDARY_NORMAL', 1)),  # used with refract shader
    '$flowmap':         ('TextureFlow',         '',        [formatNewTexturePath],     ('F_FLOW_NORMALS', 1), ('F_FLOW_DEBUG', 1)),
    '$flow_noise_texture':('TextureNoise',      '_noise',  [formatNewTexturePath],     ('F_FLOW_NORMALS', 1), ('F_FLOW_DEBUG', 2)),
    '$detail':          ('TextureDetail',       '_detail', [formatNewTexturePath],     ('F_DETAIL_TEXTURE', 1)),  # $detail2
    '$decaltexture':    ('TextureDetail',       '_detail', [formatNewTexturePath],     ('F_DETAIL_TEXTURE', 1), ('F_SECONDARY_UV',  1), ('g_bUseSecondaryUvForDetailTexture',  1)),

    '$selfillummask':   ('TextureSelfIllumMask','_selfillummask', [formatNewTexturePath]),
    '$tintmasktexture': ('TextureTintMask',     '_mask',   [createMask, 'G', False],   ('F_TINT_MASK',  1)), #('TextureTintTexture',)
    '$_vmat_metalmask': ('TextureMetalness',    '_metal',  [formatNewTexturePath],     ('F_METALNESS_TEXTURE',  1)),  # F_SPECULAR too
    '$_vmat_transmask': ('TextureTranslucency', '_trans',  [formatNewTexturePath]),
    '$_vmat_rimmask':   ('TextureRimMask',      '_rimmask',[formatNewTexturePath]),

    # only the G channel ## $ambientoccltexture': '$ambientocclusiontexture':
    '$ao':          ('TextureAmbientOcclusion', '_ao',     [createMask, 'G', False],    ('F_AMBIENT_OCCLUSION_TEXTURE',  1)),  # g_flAmbientOcclusionDirectSpecular "1.000"
    '$aotexture':   ('TextureAmbientOcclusion', '_ao',     [createMask, 'G', False],    ('F_AMBIENT_OCCLUSION_TEXTURE',  1)),  # g_flAmbientOcclusionDirectSpecular "1.000"

    '$phongexponenttexture': ('TextureSpecularExponent', '_specexp', [formatNewTexturePath]),
    #'$phongexponent2' $phongmaskcontrastbrightness2, $phongbasetint2, $phongamount2
    '$lightwarptexture': ('TextureDiffuseWarp', '_diffusewarp', [formatNewTexturePath], ('F_DIFFUSE_WARP', 1)),
    '$phongwarptexture': ('TextureSpecularWarp', '_specwarp', [formatNewTexturePath],   ('F_SPECULAR_WARP', 1)),

    # Next script should take care of these, unless BASIC_PBR
    '$envmapmask':  ('$envmapmask',         '_env_mask',   [formatNewTexturePath]) if not BASIC_PBR else \
                    ('TextureRoughness',    '_rough',      [formatNewTexturePath]) if not LEGACY_SHADER else \
                    ('TextureGlossiness',   '_gloss',      [formatNewTexturePath]),

                    #if out dota2 ('TextureCubeMapSeparateMask', '_mask', ('F_MASK_CUBE_MAP_BY_SEPARATE_MASK' 1))

    ('$phong', 1): {
        '$phongmask':   ('$phongmask',          '_phong_mask', [formatNewTexturePath]) if not BASIC_PBR else \
                        ('TextureRoughness',    '_rough',      [formatNewTexturePath]) if not LEGACY_SHADER else \
                        ('TextureGlossiness',   '_gloss',      [formatNewTexturePath]),
    },
},

'transform': {
    '$basetexturetransform':    ('g_vTex'),  # g_vTexCoordScale "[1.000 1.000]"g_vTexCoordOffset "[0.000 0.000]"
    '$detailtexturetransform':  ('g_vDetailTex'),  # g_flDetailTexCoordRotation g_vDetailTexCoordOffset g_vDetailTexCoordScale g_vDetailTexCoordXform
    '$bumptransform':           ('g_vNormalTex'),
    #'$bumptransform2':         (''),
    #'$basetexturetransform2':  (''),   #
    #'$texture2transform':      (''),   #
    #'$blendmasktransform':     (''),   #
    #'$envmapmasktransform':    (''),   #
    #'$envmapmasktransform2':   (''),   #

},

'settings': {

    '$detailblendfactor':   ('g_flDetailBlendFactor',   '1.000',                    [float_val]), #'$detailblendfactor2', '$detailblendfactor3'
    '$detailscale':         ('g_vDetailTexCoordScale',  '[1.000 1.000]',            [fixVector, False]),

    '$color':               ('g_vColorTint',        '[1.000 1.000 1.000 0.000]',    [fixVector, True]),
    '$color2':              ('g_vColorTint',        '[1.000 1.000 1.000 0.000]',    [fixVector, True]),
    '$selfillumtint':       ('g_vSelfIllumTint',    '[1.000 1.000 1.000 0.000]',    [fixVector, True]),
    '$envmaptint':          ('g_vSpecularColor',    '[1.000 1.000 1.000 0.000]',    [fixVector, True]),
    '$emissiveblendtint':   ('g_vEmissiveTint',     '[1.000 1.000 1.000 0.000]',    [fixVector, True]),

    # s1 channels relative to each other "[0 0 0]" = "[1 1 1]" (lum preserving) -> s2 is color so it has a birghtness factor within it
    # perhaps default to 0.5 0.5 0.5 and scale it with $phongboost, etc
    '$phongtint':           ('g_vSpecularColor',    '[1.000 1.000 1.000 0.000]',    [fixVector, True]),

    '$alpha':               ('g_flOpacityScale',        '1.000',    [float_val]),
    '$alphatestreference':  ('g_flAlphaTestReference',  '0.500',    [float_val], ('g_flAntiAliasedEdgeStrength', 1.0)),
    '$blendtintcoloroverbase':('g_flModelTintAmount',   '1.000',    [float_val]),  # $layertint1
    '$selfillumscale':      ('g_flSelfIllumScale',      '1.000',    [float_val]),
    '$phongexponent':       ('g_flSpecularExponent',    '32.000',   [float_val]),
    '$phongboost':          ('g_flPhongBoost',          '1.000',    [float_val]),  #
    '$metalness':           ('g_flMetalness',           '0.000',    [float_val]),
    '$_metalness2':         ('g_flMetalnessB',          '0.000',    [float_val]),
    '$refractamount':       ('g_flRefractScale',        '0.200',    [float_val]),
    '$flow_worlduvscale':   ('g_flWorldUvScale',        '1.000',    [float_val]),
    '$flow_noise_scale':    ('g_flNoiseUvScale',        '0.010',    [float_val]),  # g_flNoiseStrength?
    '$flow_bumpstrength':   ('g_flnormalmap_listtrength',   '1.000',    [float_val]),

    '$nofog':   ('g_bFogEnabled',       '0',        [int_val, True]),
    "$notint":  ('g_flModelTintAmount', '1.000',    [int_val, True]),

    # rimlight
    '$rimlightexponent':    ('g_flRimLightScale',   '1.000',    [float_val]),
    #'$warpindex':           ('g_flDiffuseWrap',         '1.000',    [float_var]),  # requires F_DIFFUSE_WRAP 1. "?
    #'$diffuseexp':          ('g_flDiffuseExponent',     '2.000',    [float_var], 'g_vDiffuseWrapColor "[1.000000 1.000000 1.000000 0.000000]'),

    # shader.blend and shader.vr_standard(SteamVR) -- $NEWLAYERBLENDING
    '$blendsoftness':       ('g_flLayer1BlendSoftness', '0.500',    [float_val]),
    '$layerborderstrenth':  ('g_flLayer1BorderStrength','0.500',    [float_val]),
    '$layerborderoffset':   ('g_flLayer1BorderOffset',  '0.000',    [float_val]),
    '$layerbordersoftness': ('g_flLayer1BorderSoftness','0.500',    [float_val]),
    '$layerbordertint':     ('g_vLayer1BorderColor',    '[1.000000 1.000000 1.000000 0.000000]', [fixVector, True]),
},

'channeled_masks': {  # 1-X will extract and invert channel X // M_1-X to only invert on models
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

    '$rimmask':         ('$phongexponenttexture',       '$_vmat_rimmask',   'A'),

    '$masks1':  ('self', ('$_vmat_rimmask', '$phongalbedomask', '$_vmat_metalmask', '$warpindex'), 'RGBA') if IMPORT_MOD == "csgo" else \
                ('self', ('$rimmask', '$phongalbedomask', '$_vmat_metalmask', '$selfillum'), 'RGBA') if IMPORT_MOD == "dota" else \
                None,
    '$masks2':  ('self', ("$shadowsaturationmask", '$phongalbedomask', '$_vmat_metalmask', '$warpindex'), 'RGBA') if IMPORT_MOD == "csgo" else \
                ('self', ('$detailmask', '$_vmat_metalmask', '$_vmat_metalmask', '$selfillum'), 'RGBA') if IMPORT_MOD == "dota" else \
                None,
},

'dicts': {
    "proxies": None#(None, None, proxyshit)
},

'SystemAttributes': {
    '$surfaceprop':     ('PhysicsSurfaceProperties', 'default', [fixSurfaceProp])
},

'texture_settings': {
    '$noenvmapmip':             None,  # Lock specular cubemap to mip 0
    '$phongexponentfactor':     None,  # Multiply $phongexponenttexture by this amount
    '$invertphongmask':         None,  # Invert $phongmask specmask
},

# no direct replacement, etc
'others2': {
    # ssbump dose not work?
    #'$ssbump':               ('TextureBentNormal',    '_bentnormal.tga', 'F_ENABLE_NORMAL_SELF_SHADOW 1\n\tF_USE_BENT_NORMALS 1\n'),

    #'$iris': ('',    '',     ''),  # paste iris into basetexture

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

KNOWN = {}  # for proxies; when $color is known as g_vTintColor, proxies yielding to $color can be translated
for d in vmt_to_vmat.values():
    for k, v in d.items():
        if isinstance(v, tuple): v = v[0]
        KNOWN[k] = v

def convertVmtToVmat():

    # For each key-value in the vmt file...
    for vmtKey, vmtVal in vmt.KeyValues.iteritems():

        outKey = outVal = ''

        vmtKey = vmtKey.lower()
        vmtVal = str(vmtVal).strip().strip('"' + "'").strip(' \n\t"') # FIXME temp str

        # search through the dictionary above to find the appropriate replacement.
        for keyType in vmt_to_vmat:

            vmatTranslation = vmt_to_vmat[keyType].get(vmtKey)

            if not vmatTranslation:
                continue

            vmatReplacement = None
            vmatDefaultVal = None
            vmatTranslFunc = None
            outAddLines = []

            try:
                vmatReplacement = vmatTranslation [ VMAT_REPLACEMENT ]
                vmatDefaultVal  = vmatTranslation [ VMAT_DEFAULTVAL  ]
                vmatTranslFunc  = vmatTranslation [ VMAT_TRANSLFUNC  ]
                outAddLines     = list( vmatTranslation [ VMAT_EXTRALINES : ] )
            except IndexError:
                pass

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
                        outAddLines = list( vmatTranslation [ VMAT_TRANSLFUNC : ] )
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
                        try:
                            if (returnValue:= func_(*args_)):
                                outVal = returnValue
                            #args_.clear()
                            msg(outKey, returnValue)
                        except ValueError as errrrr:
                            print("Got ValueError:", errrrr, "on", f'{vmtKey}: {vmtVal} with {func_.__name__}')
                            failureList.add(f'ValueError on {func_.__name__}', f'{vmt.path} @ "{vmtKey}": "{vmtVal}"')
                            outVal = vmatDefaultVal
                        

            # no equivalent key-value for this key, only exists
            # add comment or ignore completely
            elif (outAddLines):
                if keyType not in ('transform'):  # exceptions
                    for key, value in outAddLines:
                        vmat.KeyValues[key] = value
                    continue
            else:
                continue

            # F_RENDER_BACKFACES 1 etc
            if keyType == 'f_keys':
                if vmtKey == "$translucent" and vmat.shader in ("vr_projected_decals", "vr_static_overlay"):
                    outKey = "F_BLEND_MODE"
                    outVal = (0 if (vmat.shader == "vr_projected_decals") else 1)

            elif(keyType == 'textures'):

                # Layer A
                if vmtKey in ('$basetexture', '$hdrbasetexture', '$hdrcompressedtexture', '$normalmap'):
                    outKey = vmat_layered_param(vmatReplacement)

                elif vmtKey in ('$normalmap', '$bumpmap2', '$normalmap2'):

                    if vmtVal == 'dev/flat_normal': outVal = default(vmatDefaultVal)

                    if not outVal == "materials/default/default_normal.tga":
                        flipNormalMap(Path(outVal))

            elif(keyType == 'transform'):  # here one key can add multiple keys
                if not vmatReplacement:
                    continue

                transform = TexTransform(vmtVal)
                msg( transform )
                # doesnt seem like there is rotation
                #if(matrixList[MATRIX_ROTATE] != '0.000'):
                #    if(matrixList[MATRIX_ROTATIONCENTER] != '[0.500 0.500]')

                if transform.rotate:
                    msg("HERE IT IS:", transform.rotate)

                # scale 5 5 -> g_vTexCoordScale "[5.000 5.000]"
                if(transform.scale != (1.000, 1.000)):
                    outKey = vmatReplacement + 'CoordScale'
                    outVal = fixVector(transform.scale, False)
                    vmat.KeyValues[outKey] = outVal

                # translate .5 2 -> g_vTexCoordOffset "[0.500 2.000]"
                if(transform.translate != (0.000, 0.000)):
                    outKey = vmatReplacement + 'CoordOffset'
                    outVal = fixVector(transform.translate, False)
                    vmat.KeyValues[outKey] = outVal

                continue ## Skip default content write

            # should use reverse of the basetexture alpha channel as a self iluminating mask
            # ... why reversE???

            elif(keyType == 'channeled_masks'):
                outVmtTexture = vmt_to_vmat['channeled_masks'][vmtKey][1]  # extract as

                if not vmt_to_vmat['textures'].get(outVmtTexture): break

                sourceTexture   = vmt_to_vmat['channeled_masks'][vmtKey][0]  # extract from
                sourceChannel   = vmt_to_vmat['channeled_masks'][vmtKey][2]  # channel to extract

                outKey          = vmt_to_vmat['textures'][outVmtTexture][VMAT_REPLACEMENT]
                outAddLines     = list(vmt_to_vmat['textures'][outVmtTexture][ VMAT_EXTRALINES : ] )
                sourceSubString = vmt_to_vmat['textures'][outVmtTexture][VMAT_DEFAULTVAL]

                if vmt.KeyValues[outVmtTexture]:
                    print("~", vmtKey, "conflicts with", outVmtTexture + ". Aborting mask extration (using original).")
                    continue

                shouldInvert    = False
                if ('1-' in sourceChannel):
                    if 'M_1-' in sourceChannel:
                        if vmt.KeyValues['$model']:
                            shouldInvert = True
                    else:
                        shouldInvert = True

                    sourceChannel = sourceChannel.strip('M_1-')

                # invert for brushes; if it's a model, keep the intact one ^
                # both versions are provided just in case for 'non models'
                #if not str(vmt.KeyValues['$model']).strip('"') != '0': invert

                outVal =  createMask(vmt.KeyValues[sourceTexture], sourceSubString, sourceChannel, shouldInvert)

            elif keyType == 'SystemAttributes':
                if not vmat.KeyValues['SystemAttributes']:
                    vmat.KeyValues['SystemAttributes'] = {}

                vmat.KeyValues['SystemAttributes'][outKey] = outVal
                continue

            try:
                if outAddLines[0] == None:
                    outAddLines = []
            except IndexError: pass

            for additional_key, value in outAddLines:
                vmat.KeyValues[additional_key] = value

            vmat.KeyValues[outKey] = outVal

            # dont break some keys have more than 1 translation (e.g. $selfillum)

    if USE_SUGESTED_DEFAULT_ROUGHNESS:
        ## if f_specular use this else use "[1.000000 1.000000 1.000000 0.000000]"
        # 2way blend has specular force enabled so maxing the rough should minimize specularity TODO
        if not vmat.shader == "vr_simple_2way_blend":
            if "TextureRoughness" not in vmat.KeyValues:
                vmat.KeyValues["TextureRoughness"] = "materials/default/default_rough_s1import.tga"
        else:
            default_rough = "materials/default/default_rough_s1import.tga"
            if vmat.KeyValues['F_SPECULAR'] == 1: # TODO: phong2 envmap2 and those sorts of stuff
                default_rough = "[1.000000 1.000000 1.000000 0.000000]"

            if "TextureRoughnessA" not in vmat.KeyValues:
                vmat.KeyValues["TextureRoughnessA"] = default_rough

            if "TextureRoughnessB" not in vmat.KeyValues:
                vmat.KeyValues["TextureRoughnessB"] = default_rough

def convertSpecials():

    if bumpmap := vmt.KeyValues["$bumpmap"]:
        vmt.KeyValues["$normalmap"] = bumpmap
        del vmt.KeyValues["$bumpmap"]

    # fix phongmask logic
    if vmt.KeyValues["$phong"] == 1 and not vmt.KeyValues["$phongmask"]:
        # sniper scope

        bHasPhongMask = False
        for key, val in vmt_to_vmat['channeled_masks'].items():
            if val[1] == '$phongmask' and vmt.KeyValues[key]:
                bHasPhongMask = True
                break
        if vmt.path.local.is_relative_to(materials/"models/weapons/shared/scope"):
            bHasPhongMask = False
        if not bHasPhongMask:  # normal map Alpha acts as a phong mask by default
            vmt.KeyValues['$normalmapalphaphongmask'] = 1

    # fix additive logic - Source 2 needs Translucency to be enabled for additive to work
    if vmt.KeyValues["$additive"] == 1 and not vmt.KeyValues["$translucent"]:
        vmt.KeyValues['$translucent'] = 1

    # fix unlit shader ## what about generic?
    if (vmt.shader == 'unlitgeneric') and (vmat.shader == "vr_complex"):
        vmat.KeyValues["F_UNLIT"] = 1

    # fix mod2x logic for "vr_projected_decals"
    if vmt.shader == 'decalmodulate':
        vmat.KeyValues['F_BLEND_MODE'] = 1  # 2 for vr_static_overlay

    # fix lit logic for "vr_projected_decals"
    if vmt.shader in ('lightmappedgeneric', 'vertexlitgeneric'):
        if vmat.shader == "vr_static_overlay":      vmat.KeyValues["F_LIT"] = 1
        elif vmat.shader == "vr_projected_decals": vmat.KeyValues["F_SAMPLE_LIGHTMAP"] = 1  # what does this do
    
    if vmat.shader == "vr_projected_decals":
        vmat.KeyValues['F_CUTOFF_ANGLE'] = 1

    # csgo viewmodels
    # if not mod == csgo: return
    viewmodels = materials / "models/weapons/v_models"
    if vmt.path.local.is_relative_to(viewmodels):
        # use _ao texture in \weapons\customization
        wpn_name = vmt.path.parent.name
        if (vmt.path.stem == wpn_name or vmt.path.stem == wpn_name.split('_')[-1]):
            vm_customization = viewmodels.parent / "customization"
            ao_path = sh.output(vm_customization/wpn_name/ (str(wpn_name) + "_ao"+ TEXTURE_FILEEXT))
            if ao_path.exists():
                ao_path_new = sh.output(materials/viewmodels/wpn_name/ao_path.name)
                try:
                    if not ao_path_new.exists() and ao_path_new.parent.exists():
                        copyfile(ao_path, ao_path_new)
                        print("+ Succesfully moved AO texture for weapon material:", wpn_name)
                    vmt.KeyValues["$aotexture"] = str(ao_path_new.local.relative_to(materials))
                    print("+ Using ao:", ao_path.name)
                except FileNotFoundError:
                    failureList.add("AOfix FileNotFoundError", f"{ao_path_new.name}, {ao_path.local}")

        #vmt.KeyValues.setdefault("$envmap", "0")  # specular looks ugly on viewmodels so disable it. does not affect scope lens
        if vmt.KeyValues["$envmap"]: del vmt.KeyValues["$envmap"]
        #"$envmap"                 "environment maps/metal_generic_001" --> metalness
        #"$envmaplightscale"       "1"
        #"$envmaplightscaleminmax" "[0 .3]"     metalness modifier?

def collectSkybox(name:str, face: str, vmt: VMT):

    ldr_tex = vmt.KeyValues.get('$basetexture')
    hdr_tex = vmt.KeyValues.get('$hdrbasetexture')
    hdr_compressed_tex = vmt.KeyValues.get('$hdrcompressedtexture')

    if (texture:= hdr_tex or hdr_compressed_tex or ldr_tex) is not None:
        face_collect_path = sh.output(legacy_skyfaces/name).with_suffix(".json")
        Collect = sh.GetJson(face_collect_path, bCreate = True)

        # First vmt to have $hdr decides hdr-ness
        if not Collect.setdefault('_hdrtype'):
            if hdr_tex:
                Collect['_hdrtype'] = 'uncompressed'
            elif hdr_compressed_tex:
                Collect['_hdrtype'] = 'compressed'

        src_extension = '.pfm' if Collect['_hdrtype'] == 'uncompressed' else TEXTURE_FILEEXT
        face_path = sh.output(fixVmtTextureDir(texture, src_extension))
        if face_path.is_relative_to(sh.output(skyboxmaterials)):
            # Move annoying face files into a folder 'legacy_faces'
            # Not deleting just incase they are needed somewhere separately, and to save time on future imports
            face_path_new = sh.output(legacy_skyfaces / face_path.name)
            if face_path.is_file():
                face_path.parent.MakeDir()
                face_path.rename(face_path_new)
            face_path = face_path_new

        if face_path.is_file():
            path = face_path.local.as_posix()
            Collect[face] = {}  # Dict won't be used if it won't have anything other than path

            faceTransform = TexTransform(vmt.KeyValues.get('$basetexturetransform'))
            if(faceTransform.rotate != 0):  # Hillarious. 
                Collect[face]['rotate'] = faceTransform.rotate
                msg("Collecting", face, "transformation: rotate", Collect[face]['rotate'], 'degrees')

            if Collect[face]:
                Collect[face]['path'] = path
            else:
                Collect[face] = path
            print(f"    + Collected face {face.upper()} for {name}_cube{src_extension}")
            sh.UpdateJson(face_collect_path, Collect)

        return face_collect_path

    if False: #bHasLDRFallback: TODO
        ldr_vmtPath = "1"
        ldr_vmtKeyValues = "2"
        collectSkybox(ldr_vmtPath, ldr_vmtKeyValues)

def _ImportVMTtoExtraVMAT(vmt_path: Path, shader = None, path = None):
    global vmat, import_extra
    old_vmat = vmat

    assert path != old_vmat.path

    vmat = VMAT()
    vmat.shader = shader if shader else old_vmat.shader
    vmat.path = path if path else old_vmat.path
    rv = ImportVMTtoVMAT(vmt_path, preset_vmat = True)
    if rv:
        import_extra+=1
    return rv

def ImportSkyJSONtoVMAT(json_collection: Path):
    vmat_path = sh.output( materials/skybox/(json_collection.stem + OUT_EXT))
    sky_cubemap_path = VMAT_DEFAULT_PATH / "default_cube.tga"

    cubemap = createSkyCubemap(json_collection.stem, sh.GetJson(json_collection))
    if cubemap:
        sky_cubemap_path = cubemap.local

    with open(vmat_path, 'w') as fp:
        fp.write('Layer0\n{\n\tshader "sky.vfx"\n' +
            f'\tSkyTexture\t"{sky_cubemap_path.as_posix()}"\n}}'
        )
    print("+ Saved", vmat_path.local)
    return vmat_path

def ImportVMTtoVMAT(vmt_path: Path, preset_vmat = False):

    global vmt, vmat
    validMaterial = False

    vmt = VMT(KV.FromFile(vmt_path))
    vmt.path = vmt_path

    if any(wd in vmt.shader for wd in shaderDict):
        validMaterial = True

    if vmt.shader == 'patch':

        if includePath := vmt.KeyValues["include"]:
            if includePath == r'materials\models\weapons\customization\paints\master.vmt':
                return

            patchKeyValues = vmt.KeyValues.copy()
            vmt.KeyValues.clear()

            print("+ Retrieving material properties from include:", includePath, end=' ... ')
            try:
                vmt.shader, vmt.KeyValues = getKeyValues(sh.src(includePath), ignoreList) # TODO: kv1read
            except FileNotFoundError:
                print("Did not find.")
                failureList.add("Include not found", f'{vmt.path} -- {includePath}' )
                return
            if not any(wd in vmt.shader for wd in shaderDict):
                vmt.KeyValues.clear()
                print("Include has unsupported shader.")
                return
            print("Done!")
            vmt.KeyValues.update(patchKeyValues)
            if vmt.KeyValues['insert']:
                vmt.KeyValues.update(vmt.KeyValues['insert']) # TODO: kv1.update(override=True)
                del vmt.KeyValues['insert']
            del vmt.KeyValues['include']
        else:
            print("~ WARNING: No include was provided on material with type 'Patch'. Is it a weapon skin?")

    if vmt.path.local.is_relative_to(skyboxmaterials):
        name, face = vmt.path.stem[:-2], vmt.path.stem[-2:]
        if face in SKY_FACES:
            return collectSkybox(name, face, vmt)

    if not validMaterial:
        return

    if not preset_vmat:
        vmat = VMAT()
        vmat.shader = chooseShader()
        vmat.path = OutName(vmt.path)

    vmat.path.parent.MakeDir()

    convertSpecials()
    convertVmtToVmat()

    if proxies:= vmt.KeyValues["proxies"]:
        vmat.KeyValues['DynamicParams'] = ProxiesToDynamicParams(proxies, KNOWN, vmt.KeyValues)
        print(vmat.KeyValues['DynamicParams'])

    with open(vmat.path, 'w') as vmatFile:
        msg(vmt.shader + " => " + vmat.shader, "\n")#, vmt.KeyValues)
        vmatFile.write(vmat.KeyValues.ToStr()) ###############################

    if sh.DEBUG: print("+ Saved", vmat.path)
    else: print("+ Saved", vmat.path.local)

    if vmat.shader == "vr_projected_decals":
        _ImportVMTtoExtraVMAT(vmt_path, shader="vr_static_overlay",
            path=(vmat.path.parent / (vmat.path.stem + '-static' + vmat.path.suffix)))

    return vmat.path

vmt, vmat = None, None

class Failures(dict):
    #data = {}
    def add(self, err, file):
        self.setdefault(err, list())
        self[err].append(file)
    
    #def __bool__(self):
    #    return len(self.data) > 0

failureList = Failures()

total=import_total=import_invalid=import_extra = 0

def main():
    print('\nSource 2 Material Converter!')
    print('----------------------------------------------------------------------------')

    global total, import_total, import_invalid
    for vmt_path in sh.collect(
            materials,
            IN_EXT, OUT_EXT,
            existing=OVERWRITE_VMAT,
            outNameRule=OutName,
            # proxies vec3 special materials/lights/camera.vmt
            # "models/player/**/*.vmt"
            # "de_nuke/nukwater_movingplane.vmt"
            # "models/weapons/v_models/rif_ak47/ak47.vmt"
            # "test/test.vmt"
            match=None):

        total += 1
        if ImportVMTtoVMAT(vmt_path):
            import_total += 1
        else:
            #sh.status(f"- skipping [invalid]: {vmt_path.local}")
            import_invalid += 1

    print("\nSkybox materials...")

    for skyfaces_json in sh.collect(
            None, '.json', OUT_EXT, OVERWRITE_SKYBOX_VMATS,
            outNameRule=OutName_Sky, searchPath=sh.EXPORT_CONTENT/legacy_skyfaces):
        ImportSkyJSONtoVMAT(skyfaces_json)

    if failureList:
        print("\n\t<<<< THESE MATERIALS HAVE ERRORS >>>>")
        for failure, files in failureList.items():
            print(failure)
            for file in files:
                print('\t' + str(file))
        print("\t^^^^ THESE MATERIALS HAVE ERRORS ^^^^")

    try:
        print(f"\nTotal imports:\t{import_total} / {total}\t| " + "{:.2f}".format((import_total/total) * 100) + f" % Imported")
        print(f"Total skipped:\t{import_invalid} / {total}\t| " + "{:.2f}".format((import_invalid/total) * 100) + f" % Skipped")
        print(f"Total errors :\t{len(failureList)} / {total}\t| " + "{:.2f}".format((len(failureList)/total) * 100) + f" % Had Errors")
        print(f"Total extra :\t{import_extra}")

    except Exception: pass
    # csgo -> 206 / 14792 | 1.39 % Error rate -- 4681 / 15308 | 30.58 % Skip rate
    # l4d2 -> 504 / 3675 | 13.71 % Error rate -- 374 / 3675 | 10.18 % Skip rate
    print("\nFinished! Your materials are now ready.")

if __name__ == "__main__":
    main()
