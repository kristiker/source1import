import re, sys, os, json
from pathlib import Path
from shutil import copyfile, move
from difflib import get_close_matches
from shared.keyvalue_simple import getKV_tailored as getKeyValues
from PIL import Image, ImageOps
import shared.base_utils as sh
import vdf

import materials_import_skybox as sky
# generic, blend instead of vr_complex, vr_simple_2wayblend etc...
LEGACY_SHADER = False
NEW_SH = not LEGACY_SHADER

# py_shared TODO: use an IN and OUT akin to s1import_txtmap
# Path to content root, before /materials/
PATH_TO_CONTENT_ROOT = r""
PATH_TO_NEW_CONTENT_ROOT = r""

# Set this to True if you wish to overwrite your old vmat files. Same as adding -f to launch parameters
OVERWRITE_VMAT = True
sky.OVERWRITE_SKYBOX = False
sky.OVERWRITE_SKYBOX_MATS = False

# True to let vtex handle the inverting of the normalmap.
NORMALMAP_G_VTEX_INVERT = True

BASIC_PBR = True
MISSING_TEXTURE_SET_DEFAULT = True
USE_SUGESTED_DEFAULT_ROUGHNESS = True
SURFACEPROP_AS_IS = False

from shared.base_utils import msg, DEBUG
DEBUG = False
# File format of the textures. Needs to be lowercase
# source 2 supports all kinds: tga jpeg png gif psd exr tiff pfm...
TEXTURE_FILEEXT = '.tga'
IN_EXT = ".vmt"
OUT_EXT = ".vmat"
SOURCE2_SHADER_EXT = ".vfx"

VMAT_DEFAULT_PATH = Path("materials/default")

materials = Path("materials")
fs = sh.Source(materials, PATH_TO_CONTENT_ROOT, PATH_TO_NEW_CONTENT_ROOT)

skybox = Path("skybox")

class ValveMaterial:
    def __init__(self, version, materialPath = "", kv: dict = {}):

        self.version = version # materialsystem 1/2
        self.shader = "error"

        self.KeyValues = {} # main KV settings; getFullKeyValues() if you want the full thing
        self.KV_branches = {} # proxy {}, systemattributes {}, dynamicparams {}

        if kv: self.shader, self.KeyValues = self._processRawKeyValues(kv)

        self.path = Path(materialPath)

    def getFullKeyValues(self):
        mainKey = self.shader
        if self.version == 2:
            mainKey = "Layer0"
        return dict( (mainKey, self.KeyValues) )

    def setShader(self, shader: str):
        self.shader = shader
        if self.version == 2:
            self.KeyValues["shader"] = self.shader + SOURCE2_SHADER_EXT

    def _processRawKeyValues(self, kv: dict) -> tuple:
        try:
            mainKey = next(iter(kv))
        except StopIteration:
            return "", {}

        KeyValues = kv[mainKey]
        if self.version == 2:
            return KeyValues.get("shader", ""), KeyValues
        return mainKey, KeyValues

    def __str__(self):
        return f"{self.shader} Source{self.version} {self.shader} Material at {self.path}"

# keep everything lowercase !!!
shaderDict = {
    "black":                "black",
    "sky":                  "sky",
    "unlitgeneric":         "vr_complex",
    "vertexlitgeneric":     "vr_complex",
    "decalmodulate":        "vr_projected_decals", # https://developer.valvesoftware.com/wiki/Decals#DecalModulate
    "lightmappedgeneric":   "vr_complex",
    "lightmappedreflective":"vr_complex",
    "character":            "vr_complex", # https://developer.valvesoftware.com/wiki/Character_(shader)
    "customcharacter":      "vr_complex",
    "teeth":                "vr_complex",
    "water":                "simple_water",
    "refract":              "refract",
    "worldvertextransition":"vr_simple_2way_blend",
    "lightmapped_4wayblend":"vr_simple_2way_blend",
    "cables":               "cables",
    "lightmappedtwotexture":"vr_complex", # 2 multiblend $texture2 nocull scrolling, model, additive.
    "unlittwotexture":      "vr_complex", # 2 multiblend $texture2 nocull scrolling, model, additive.
    "cable":                "cables",
    "splinerope":           "cables",
    "shatteredglass":       "vr_glass",
    "wireframe":            "tools_wireframe",
    "spritecard":           "spritecard", #"modulate",
    #"subrect":              "spritecard", # should we just cut? $Pos "256 0" $Size "256 256" $decalscale 0.25 decals\blood1_subrect.vmt
    #"weapondecal": weapon sticker
    "patch":                "vr_complex", # fallback if include doesn't have one
}

def chooseShader():
    sh = {x:0 for x in list(shaderDict.values())}

    if vmt.shader not in shaderDict:
        if DEBUG:
            if (ffff := "At least 1 material: unmatched shader " + vmt.shader) not in failureList: failureList.append(ffff)
        return "vr_black_unlit"

    if LEGACY_SHADER:   sh["generic"] += 1
    else:               sh[shaderDict[vmt.shader]] += 1

    if vmt.KeyValues.get('$decal') == '1': sh["vr_projected_decals"] += 10

    if vmt.shader == "worldvertextransition":
        if vmt.KeyValues.get('$basetexture2'): sh["vr_simple_2way_blend"] += 10

    elif vmt.shader == "lightmappedgeneric":
        if vmt.KeyValues.get('$newlayerblending') == '1': sh["vr_simple_2way_blend"] += 10
        #if vmt.KeyValues.get('$decal') == '1': sh["vr_projected_decals"] += 10

    elif vmt.shader == "":
        pass
    # TODO: vr_complex -> vr simple if no selfillum tintmask detailtexture specular
    return max(sh, key = sh.get)

ignoreList = [ "dx9", "dx8", "dx7", "dx6", "proxies"]

f_KeyVal = '\t{}\t{}\n'
f_KeyValQuoted = '\t{}\t"{}"\n'
f_KeyQuotedValQuoted = '\t"{}"\t"{}"\n'

def default(defaulttype):
    return VMAT_DEFAULT_PATH / Path("default" + defaulttype).with_suffix(".tga")

def OutName(path: Path) -> Path:
    #if fs.LocalDir(path).is_relative_to(materials/skybox/) and path.stem[-2:] in skyboxFaces:
    #    return fs.NoSpace(fs.Output(path).with_suffix(OUT_EXT))
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
        if value := vmt.KeyValues.get(vmtParam):
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
        failureList.append(f"{str(vmt.path)} - {vmtTexture} not found")
        return default(copySub)

    if invert:  newMask = imagePath.stem + '_' + channel[:3].lower() + '-1' + copySub
    else:       newMask = imagePath.stem + '_' + channel[:3].lower()        + copySub
    newMaskPath = imagePath.parent / Path(newMask).with_suffix(imagePath.suffix)

    if newMaskPath.exists(): #and not DEBUG:
        return fs.LocalDir(newMaskPath)

    if not imagePath.is_file() or not imagePath.exists():
        failureList.append(str(vmt.path))
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
        with open(image_path.with_suffix(".txt"), 'w') as settingsFile:
            kv = vdf.parse(settingsFile)
            settings = kv.get("settings", {})
            settings["legacy_source1_inverted_normal"] = 1
            kv["settings"] = settings
            vdf.dump(kv, settingsFile, pretty=True)
            
            #settingsFile.write('"settings"\n{\t"legacy_source1_inverted_normal" "1"\n}')
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

surfprop_list = sh.GetJson(Path(__file__).parent / Path("surfproperties.json"))['hlvr']
# TODO: ideally, we want to import our legacy surfaceprops and use those instead of whatever is closest 
def fixSurfaceProp(vmtVal):

    if SURFACEPROP_AS_IS or (vmtVal in ('default', 'default_silent', 'no_decal', 'player', 'roller', 'weapon')):
        return vmtVal

    elif vmtVal in surfprop_force:
        return surfprop_force[vmtVal]

    if("props" in vmat.path.parts): match = get_close_matches('prop.' + vmtVal, surfprop_list, 1, 0.4)
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

#'shader': { '$_vmat_shader':    ('shader',  'generic.vfx', [ext, SOURCE2_SHADER_EXT]),},

'f_properties': {
    '$_vmat_unlit':     ('F_UNLIT',                 '1', None),
    '$_vmat_lit':       ('F_LIT',                   '1', None),
    '$_vmat_samplightm':('F_SAMPLE_LIGHTMAP',       '1', None),
    '$_vmat_blendmode': ('F_BLEND_MODE',            '0', None),

    '$translucent':     ('F_TRANSLUCENT',           '1', None), # "F_BLEND_MODE 0" for "vr_projected_decals"
    '$alphatest':       ('F_ALPHA_TEST',            '1', None),
    '$envmap':          ('F_SPECULAR',              '1', None), # in "environment maps/metal" | "env_cubemap" F_SPECULAR_CUBE_MAP 1 // In-game Cube Map
    '$envmapanisotropy':('F_ANISOTROPIC_GLOSS',     '1', None),
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

    "$masks1": ('F_MASKS_1',    '1', None) if EXPORT_MOD == "dota" else None, # 
    "$masks2": ('F_MASKS_2',    '1', None) if EXPORT_MOD == "dota" else None, # 

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
    '$compress':        ('TextureSquishColor',  '_color',   [formatNewTexturePath],     'F_MORPH_SUPPORTED 1\n\tF_WRINKLE 1' ),
    '$stretch':         ('TextureStretchColor', '_color',   [formatNewTexturePath],     'F_MORPH_SUPPORTED 1\n\tF_WRINKLE 1' ),

    '$normalmap':       ('TextureNormal',       '_normal',  [formatNewTexturePath],     '' ), # $bumpmap
    '$bumpcompress':    ('TextureSquishNormal', '_normal',  [formatNewTexturePath],     'F_MORPH_SUPPORTED 1\n\tF_WRINKLE 1' ),
    '$bumpstretch':     ('TextureStretchNormal','_normal',  [formatNewTexturePath],     'F_MORPH_SUPPORTED 1\n\tF_WRINKLE 1' ),

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
    '$flow_noise_texture':('TextureNoise',      '_noise',  [formatNewTexturePath],     'F_FLOW_NORMALS 1\n\tF_FLOW_DEBUG 2'),
    '$detail':          ('TextureDetail',       '_detail', [formatNewTexturePath],     'F_DETAIL_TEXTURE 1\n'), # $detail2
    '$decaltexture':    ('TextureDetail',       '_detail', [formatNewTexturePath],     'F_DETAIL_TEXTURE 1\n\tF_SECONDARY_UV 1\n\tg_bUseSecondaryUvForDetailTexture "1"'),

    '$selfillummask':   ('TextureSelfIllumMask','_selfillummask', [formatNewTexturePath],  ''),
    '$tintmasktexture': ('TextureTintMask',     '_mask',   [createMask, 'G', False],   'F_TINT_MASK 1'), #('TextureTintTexture',)
    '$_vmat_metalmask': ('TextureMetalness',    '_metal',  [formatNewTexturePath],     'F_METALNESS_TEXTURE 1'), # F_SPECULAR too
    '$_vmat_transmask': ('TextureTranslucency', '_trans',  [formatNewTexturePath],     ''),
    '$_vmat_rimmask':   ('TextureRimMask',      '_rimmask',[formatNewTexturePath],     ''),

    # only the G channel ## $ambientoccltexture': '$ambientocclusiontexture':
    '$ao':          ('TextureAmbientOcclusion', '_ao',     [createMask, 'G', False],    'F_AMBIENT_OCCLUSION_TEXTURE 1'), # g_flAmbientOcclusionDirectSpecular "1.000"
    '$aotexture':   ('TextureAmbientOcclusion', '_ao',     [createMask, 'G', False],    'F_AMBIENT_OCCLUSION_TEXTURE 1'), # g_flAmbientOcclusionDirectSpecular "1.000"

    '$phongexponenttexture': ('TextureSpecularExponent', '_specexp', [formatNewTexturePath], ''),
    #'$phongexponent2' $phongmaskcontrastbrightness2, $phongbasetint2, $phongamount2
    '$lightwarptexture': ('TextureDiffuseWarp', '_diffusewarp', [formatNewTexturePath], 'F_DIFFUSE_WARP 1'),
    '$phongwarptexture': ('TextureSpecularWarp', '_specwarp', [formatNewTexturePath], 'F_SPECULAR_WARP 1'),

    # Next script should take care of these, unless BASIC_PBR
    '$envmapmask':  ('$envmapmask',         '_env_mask',   [formatNewTexturePath], '') if not BASIC_PBR else \
                    ('TextureRoughness',    '_rough',      [formatNewTexturePath], '') if not LEGACY_SHADER else \
                    ('TextureGlossiness',   '_gloss',      [formatNewTexturePath], ''),

                    #if out dota2 'TextureCubeMapSeparateMask' '_mask' 'F_MASK_CUBE_MAP_BY_SEPARATE_MASK 1'

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
    '$envmaptint':          ('g_vSpecularColor',    '[1.000 1.000 1.000 0.000]',    [fixVector, True],  ''),
    # s1 channels relative to each other "[0 0 0]" = "[1 1 1]" -> s2 is color so it has a birghtness factor within it
    # perhaps default to 0.5 0.5 0.5 and scale it with $phongboost, etc
    '$phongtint':           ('g_vSpecularColor',    '[1.000 1.000 1.000 0.000]',    [fixVector, True],  ''),

    '$alpha':               ('g_flOpacityScale',        '1.000',    [float_val], ''),
    '$alphatestreference':  ('g_flAlphaTestReference',  '0.500',    [float_val], 'g_flAntiAliasedEdgeStrength "1.000"'),
    '$blendtintcoloroverbase':('g_flModelTintAmount',   '1.000',    [float_val], ''), # $layertint1
    '$selfillumscale':      ('g_flSelfIllumScale',      '1.000',    [float_val], ''),
    '$phongexponent':       ('g_flSpecularExponent',    '32.000',   [float_val], ''),
    '$phongboost':          ('g_flPhongBoost',          '1.000',    [float_val], ''), # 
    '$metalness':           ('g_flMetalness',           '0.000',    [float_val], ''),
    '$_metalness2':         ('g_flMetalnessB',          '0.000',    [float_val], ''),
    '$refractamount':       ('g_flRefractScale',        '0.200',    [float_val], ''),
    '$flow_worlduvscale':   ('g_flWorldUvScale',        '1.000',    [float_val], ''),
    '$flow_noise_scale':    ('g_flNoiseUvScale',        '0.010',    [float_val], ''), # g_flNoiseStrength?
    '$flow_bumpstrength':   ('g_flnormalmap_listtrength',   '1.000',    [float_val], ''),

    '$nofog':   ('g_bFogEnabled',       '0',        [int_val, True], ''),
    "$notint":  ('g_flModelTintAmount', '1.000',    [int_val, True], ''),

    # rimlight
    '$rimlightexponent':    ('g_flRimLightScale',   '1.000',    [int_val],  ''),
    #'$warpindex':           ('g_flDiffuseWrap',         '1.000',    [float_var], ''), # requires F_DIFFUSE_WRAP 1. "?
    #'$diffuseexp':          ('g_flDiffuseExponent',     '2.000',    [float_var], 'g_vDiffuseWrapColor "[1.000000 1.000000 1.000000 0.000000]'),

    # shader.blend and shader.vr_standard(SteamVR) -- $NEWLAYERBLENDING
    '$blendsoftness':       ('g_flLayer1BlendSoftness', '0.500',    [float_val], ''),
    '$layerborderstrenth':  ('g_flLayer1BorderStrength','0.500',    [float_val], ''),
    '$layerborderoffset':   ('g_flLayer1BorderOffset',  '0.000',    [float_val], ''),
    '$layerbordersoftness': ('g_flLayer1BorderSoftness','0.500',    [float_val], ''),
    '$layerbordertint':     ('g_vLayer1BorderColor',    '[1.000000 1.000000 1.000000 0.000000]', [fixVector, True], ''),
},

'channeled_masks': { # 1-X will extract and invert channel X // M_1-X to only invert on models
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
    "proxies": None#(None, None, proxyshit, '')
},

'SystemAttributes': {
    '$surfaceprop':     ('PhysicsSurfaceProperties', 'default', [fixSurfaceProp], '')
},

'texture_settings': {
    '$noenvmapmip':             None, # Lock specular cubemap to mip 0
    '$phongexponentfactor':     None, # Multiply $phongexponenttexture by this amount
    '$invertphongmask':         None, # Invert $phongmask specmask
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

def convertVmtToVmat():

    vmatContent = ''    
    lines_SysAtributes = []

    # for each key-value in the vmt file ->
    for vmtKey, vmtVal in vmt.KeyValues.items():

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
                if vmat.shader == "vr_projected_decals" and vmtKey == "$translucent":
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

                transform = TexTransform(vmtVal)
                msg( transform )
                # doesnt seem like there is rotation
                #if(matrixList[MATRIX_ROTATE] != '0.000'):
                #    if(matrixList[MATRIX_ROTATIONCENTER] != '[0.500 0.500]')

                # scale 5 5 -> g_vTexCoordScale "[5.000 5.000]"

                if transform.rotate:
                    msg("HERE IT IS:", transform.rotate)

                if(transform.scale != (1.000, 1.000)):
                    outKey = vmatReplacement + 'CoordScale'
                    outVal = fixVector(transform.scale, False)
                    vmatContent += f_KeyValQuoted.format(outKey, outVal)

                # translate .5 2 -> g_vTexCoordOffset "[0.500 2.000]"
                if(transform.translate != (0.000, 0.000)):
                    outKey = vmatReplacement + 'CoordOffset'
                    outVal = fixVector(transform.translate, False)
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

                if vmt.KeyValues.get(outVmtTexture):
                    print("~", vmtKey, "conflicts with", outVmtTexture + ". Aborting mask extration (using original).")
                    continue

                shouldInvert    = False
                if ('1-' in sourceChannel):
                    if 'M_1-' in sourceChannel:
                        if vmt.KeyValues.get('$model'):
                            shouldInvert = True
                    else:
                        shouldInvert = True

                    sourceChannel = sourceChannel.strip('M_1-')

                # invert for brushes; if it's a model, keep the intact one ^
                # both versions are provided just in case for 'non models'
                #if not str(vmt.KeyValues.get('$model')).strip('"') != '0': invert

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
        if not vmat.shader == "vr_simple_2way_blend":
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

def convertSpecials():

    if bumpmap := vmt.KeyValues.get("$bumpmap"):
        del vmt.KeyValues["$bumpmap"]
        vmt.KeyValues["$normalmap"] = bumpmap

    # fix phongmask logic
    if vmt.KeyValues.get("$phong") == '1' and not vmt.KeyValues.get("$phongmask"):
        # sniper scope

        bHasPhongMask = False
        for key, val in vmt_to_vmat['channeled_masks'].items():
            if val[1] == '$phongmask' and vmt.KeyValues.get(key):
                bHasPhongMask = True
                break
        if fs.LocalDir(vmt.path).is_relative_to(materials/Path("models/weapons/shared/scope")):
            bHasPhongMask = False
        if not bHasPhongMask: # normal map Alpha acts as a phong mask by default
            vmt.KeyValues['$normalmapalphaphongmask'] = '1'

    # fix additive logic - Source 2 needs Translucency to be enabled for additive to work
    if vmt.KeyValues.get("$additive") == '1' and not vmt.KeyValues.get("$translucent"):
        vmt.KeyValues['$translucent'] = '1'

    # fix unlit shader ## what about generic?
    if (vmt.shader == 'unlitgeneric') and (vmat.shader == "vr_complex"):
        vmt.KeyValues["$_vmat_unlit"] = '1'

    # fix mod2x logic for "vr_projected_decals"
    if vmt.shader == 'decalmodulate':
        vmt.KeyValues['$_vmat_blendmode'] = '1'

    # fix lit logic for "vr_projected_decals"
    if vmt.shader in ('lightmappedgeneric', 'vertexlitgeneric'):
        if vmat.shader == "vr_static_overlay": vmt.KeyValues["$_vmat_lit"] = '1'
        elif vmat.shader == "vr_projected_decals": vmt.KeyValues["$_vmat_samplightm"] = '1' # F_SAMPLE_LIGHTMAP 1 ?

    # csgo viewmodels
    viewmodels = Path("models/weapons/v_models")
    if fs.LocalDir(vmt.path).is_relative_to(materials/viewmodels):
        # use _ao texture in \weapons\customization
        weaponName = vmt.path.parent.name
        if (vmt.path.stem == weaponName or vmt.path.stem == weaponName.split('_')[-1]):
            customization = viewmodels.parent / Path("customization")
            aoPath = fs.Output(materials/customization/weaponName/ Path(str(weaponName) + "_ao"+ TEXTURE_FILEEXT))
            if aoPath.exists():
                aoNewPath = fs.Output(materials/viewmodels/weaponName/ Path(aoPath.name))
                try:
                    if not aoNewPath.exists() and aoNewPath.parent.exists():
                        copyfile(aoPath, aoNewPath)
                        print("+ Succesfully moved AO texture for weapon material:", weaponName)
                    vmt.KeyValues["$aotexture"] = str(fs.LocalDir_Legacy(fs.LocalDir(aoNewPath)))
                    print("+ Using ao:", aoPath.name)
                except FileNotFoundError: pass

        #vmt.KeyValues.setdefault("$envmap", "0") # specular looks ugly on viewmodels so disable it. does not affect scope lens
        if vmt.KeyValues.get("$envmap"): del vmt.KeyValues["$envmap"]
        #"$envmap"                 "environment maps/metal_generic_001" --> metalness
        #"$envmaplightscale"       "1"
        #"$envmaplightscaleminmax" "[0 .3]"     metalness modifier?

from shared.materials.proxies import ProxiesToDynamicParams
KNOWN = {}
for d in vmt_to_vmat.values():
    for k, v in d.items():
       KNOWN[k] = v 
def convertProxies():
    buffer = ""
    dynamicParams = ProxiesToDynamicParams(vmt.KV_branches["proxies"], KNOWN, vmt.KeyValues)
    if dynamicParams:
        buffer += "\tDynamicParams\n\t{\n"
        for key, val in dynamicParams.items():
            buffer += "\t" + f_KeyValQuoted.format(key, val)
        buffer += "\t}\n"
    return buffer

from materials_import_skybox import \
    skyboxFaces, collectSkybox, collect_files_skycollections, ImportSkyVMTtoVMAT

def ImportVMTtoVMAT(vmtFilePath: Path) -> Path:

    global vmat, jsonSkyCollection
    validMaterial = False
    validInclude = False

    vmt.shader, vmt.KeyValues = getKeyValues(vmtFilePath, ignoreList)

    kvv = vdf.parse(open(vmtFilePath), mapper=vdf.VDFDict, merge_duplicate_keys=False)
    
    kvv = dict((k.lower(), v) for k,v in kvv.items())
    kvv[vmt.shader] = dict((k.lower(), v) for k,v in kvv[vmt.shader].items())
    
    for k in kvv[vmt.shader].get("proxies", {}):
        print(k)
    
    vmt.KV_branches["proxies"] = kvv[vmt.shader]["proxies"]
    del kvv

    #print(vmtFilePath.name)
    if any(wd in vmt.shader for wd in shaderDict):
        validMaterial = True

    if vmt.shader == 'patch':
        includePath = vmt.KeyValues.get("include")
        if vmt.KeyValues.get("#include"): failureList.append(includePath + " -- HASHED.") # temp
        if includePath:
            if includePath == r'materials\models\weapons\customization\paints\master.vmt':
                return
            print("+ Retrieving material properties from include:", includePath, end='')
            try:
                patchKeyValues = vmt.KeyValues.copy()
                vmt.KeyValues.clear()

                vmt.shader, vmt.KeyValues = getKeyValues(fs.Input(includePath), ignoreList)
                if not any(wd in vmt.shader for wd in shaderDict):
                    validInclude = False
                    vmt.KeyValues.clear()

                vmt.KeyValues.update(patchKeyValues)

            except FileNotFoundError:
                print(" ...Did not find")
                failureList.append(includePath + " -- Cannot find include.")
                return

            if not validInclude:
                print(" ... Include has unsupported shader.")
                #continue
        else:
            print("~ WARNING: No include was provided on material with type 'Patch'. Is it a weapon skin?")

    if fs.LocalDir(vmt.path).is_relative_to(materials/skybox):
        name, face = vmt.path.stem[:-2], vmt.path.stem[-2:]
        if face in skyboxFaces:
            faceCollection = collectSkybox(vmt.path, vmt.KeyValues)
            #if not faceCollection in jsonSkyCollection:
            print(f"+ Collected face {face.upper()} of {name}")
            #    jsonSkyCollection.append(faceCollection)
            validMaterial = False

    if validMaterial:
        vmat = ValveMaterial(2, OutName(vmt.path))
        vmat.setShader( chooseShader() ) #vmat.shader = chooseShader()

        vmat.path.parent.MakeDir()

        if not fs.ShouldOverwrite(vmat.path, OVERWRITE_VMAT):
            print(f'+ File already exists. Skipping! {vmat.path}')
            return

        with open(vmat.path, 'w') as vmatFile:
            vmatFile.write('// Converted with vmt_to_vmat.py\n')
            vmatFile.write('// From: ' + str(vmt.path) + '\n\n')
            msg(vmt.shader + " => " + vmat.shader, "\n", vmt.KeyValues)
            vmatFile.write('Layer0\n{\n\tshader "' + vmat.shader + '.vfx"\n\n')

            convertSpecials()

            vmatFile.write(convertVmtToVmat()) ###############################

            vmatFile.write(convertProxies())
            
            vmatFile.write('}\n')
#           import_total += 1

        if DEBUG: print("+ Saved", vmat.path)
        else: print("+ Saved", fs.LocalDir(vmat.path))

 #   else: import_invalid += 1

vmt, vmat = None, None
failureList = []
jsonSkyCollection = []

#######################################################################################
# Main function, loop through every .vmt
##
def main():
    print('\nSource 2 Material Conveter!')
    print('----------------------------------------------------------------------------')
    vmtFileList_extra = []
    #jsonSkyCollection = []
    vmtFileList = fs.collect_files(IN_EXT, OUT_EXT, existing=OVERWRITE_VMAT, outNameRule = OutName)
    total, import_total, import_invalid = 0, 0, 0
    global vmt, vmat
    for vmtFilePath in sh.combine_files(vmtFileList, vmtFileList_extra):
        #break
        total += 1
        #if total > 1000: break
        vmt = ValveMaterial(1, vmtFilePath)
        ImportVMTtoVMAT(vmtFilePath)

    print("\nSkybox materials...")
    
    #skyCollections = collect_files_skycollections(r"D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo\materials") #OVERWRITE_SKYBOX_MATS
    #for jsonCollection in skyCollections:
    #    #print(f"Attempting to import {jsonCollection}")
    #    ImportSkyVMTtoVMAT(jsonCollection)

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
    
    # D:\Games\steamapps\common\Half-Life Alyx\game\bin\win64>resourcecompiler.exe -game hlvr -r -i "D:\Games\steamapps\common\Half-Life Alyx\content\csgo_imported\materials"

if __name__ == "__main__":
    main()
