from enum import Enum, auto
import math
from pathlib import Path
from shutil import copyfile
from typing import Any, Callable, Literal
from PIL import Image, ImageOps

import shared.base_utils2 as sh
from shared.base_utils2 import IMPORT_MOD, DOTA2, STEAMVR, HLVR, SBOX, ADJ
from shared.keyvalue_simple import getKV_tailored as getKeyValues
from shared.keyvalues1 import KV
from shared.material_proxies import ProxiesToDynamicParams

import numpy as np
from shared import PFM

# Set this to True if you wish to overwrite your old vmat files.
OVERWRITE_VMAT = False
OVERWRITE_MODIFIED = False
OVERWRITE_SKYCUBES = False

# True to let vtex handle the inverting of the normalmap.
NORMALMAP_G_VTEX_INVERT = True

MISSING_TEXTURE_SET_DEFAULT = True # valve uses dev/white
USE_SUGESTED_DEFAULT_ROUGHNESS = True
SIMPLE_SHADER_WHERE_POSSIBLE = True
PRINT_LEGACY_IMPORT = False  # Print vmt inside vmat as reference. Increases file size.
IGNORE_PROXIES = False

sh.DEBUG = False

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

skybox = Path("skybox")
SKY_FACES = ('up', 'dn', 'lf', 'rt', 'bk', 'ft')

# Higher values increase brightness
HDRCOMPRESS_FIX_MUL = 4  # 1 to 16
# Higher values increase vibrance and contrast
HDRCOMPRESS_FIX_EXP = 1.6  # 1 to 2.2

class Failures(dict):
    def add(self, err, file):
        self.setdefault(err, list())
        self[err].append(file)
    def __len__(self):
        return sum(len(filelist) for filelist in self.values())

    #def __bool__(self):
    #    return len(self.data) > 0

failureList = Failures()
total=import_total=import_invalid=import_extra = 0

def main():
    print('\nSource 2 Material Converter!')

    # update branch conditionals
    globals().update((k,v) for (k, v) in sh.__dict__.items() if k in ("IMPORT_MOD", "DOTA2", "STEAMVR", "HLVR", "SBOX", "ADJ"))

    # update translation table based on branch conditions
    global vmt_to_vmat
    vmt_to_vmat = vmt_to_vmat_pre()

    for d in vmt_to_vmat.values():
        for k, v in d.items():
            if isinstance(v, tuple): v = v[0]
            KNOWN[k] = v

    global total, import_total, import_invalid
    sh.importing = materials
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
            sh.skip("invalid", vmt_path)
            import_invalid += 1

    print("\nSkybox materials...")

    for skyfaces_json in sh.collect(
            None, '.json', OUT_EXT, OVERWRITE_VMAT,
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
    # csgo -> 183 / 15308 | 1.20 % Error rate -- 4842 / 15308 | 31.63 % Skip rate
    # l4d2 -> 504 / 3675 | 13.71 % Error rate -- 374 / 3675 | 10.18 % Skip rate
    print("\nFinished! Your materials are now ready.")

class ValveMaterial:
    def __init__(self, shader, kv):
        self._shader = shader
        self._kv = kv

    @property
    def _KV(self): return self._kv

    @property
    def shader(self): return self._shader

class VMT(ValveMaterial):

    __defaultkv = ('', {})  # unescaped, supports duplicates, keys case insensitive

    shader: str = ValveMaterial.shader
    KeyValues: KV = ValveMaterial._KV

    def __init__(self, kv: KV = None):

        if kv is None:
            kv = KV(*self.__defaultkv)
        if kv.keyName == '':
            kv.keyName = 'Wireframe_DX9'

        if bumpmap := kv['$bumpmap']:
            kv["$normalmap"] = bumpmap
            del kv['$bumpmap']
        
        if compileclip := kv['%compileclip']:
            kv['%playerclip'] = compileclip
            kv['%compilenpcclip'] = compileclip
            del kv['%compileclip']
        

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
    
    def is_tool_material(self):
        return self.path.local.is_relative_to("materials/tools") and self.path.name.startswith("tools")

class VMAT(ValveMaterial):

    __defaultkv = ('Layer0', {'shader': 'error.vfx'})  # unescaped, keys case sensitive

    shader: str = ValveMaterial.shader
    KeyValues: dict = ValveMaterial._KV

    def __init__(self, kv=None):
        if kv is None:
            kv = KV(*self.__defaultkv)
        super().__init__(kv.get('shader') or 'error.vfx', kv)

    @shader.getter
    def shader(self):
        return self._shader.removesuffix(SOURCE2_SHADER_EXT)

    @shader.setter
    def shader(self, n: str):
        if not n.endswith(SOURCE2_SHADER_EXT): n += SOURCE2_SHADER_EXT
        self._shader = n
        self._kv['shader'] = n

class core(str, Enum):
    """core shaders"""
    def __call__(self):
        if HLVR or ADJ:
            return "vr_" + self.name
        return self.name
    complex = auto()
    simple = auto()
    glass = auto()
    black_unlit = auto()
    static_overlay = auto()
    projected_decals = auto()

class hlvr(str, Enum):
    __call__ = lambda self: self.name
    vr_simple_2way_blend = auto()

class steamvr(str, Enum):
    __call__ = lambda self: self.name
    vr_standard = auto()
    projected_decal_modulate = auto()

# keep everything lowercase !!!
def main_ubershader():
    if STEAMVR: return steamvr.vr_standard()
    elif DOTA2: return "global_lit_simple"
    else: return core.complex()

def main_blendable():
    if HLVR: return hlvr.vr_simple_2way_blend()
    elif SBOX: return "blendable"
    elif DOTA2: return "multiblend"
    else: return main_ubershader()

def main_water():
    if SBOX: return "water"
    elif DOTA2: return "water_dota"
    else: return "simple_water"

def static_decal_solution():
    if STEAMVR:
        return main_ubershader()
    return core.static_overlay()

shaderDict = {
    "black":                "black",
    "sky":                  "sky",
    "unlitgeneric":         main_ubershader,
    "vertexlitgeneric":     main_ubershader,
    "decalmodulate":        core.projected_decals,  # https://developer.valvesoftware.com/wiki/Decals#DecalModulate
    "lightmappedgeneric":   main_ubershader,
    "lightmappedreflective":main_ubershader,
    "character":            main_ubershader,  # https://developer.valvesoftware.com/wiki/Character_(shader)
    "customcharacter":      main_ubershader,
    "teeth":                main_ubershader,
    "water":                main_water,
    #"refract":              "refract",
    "worldvertextransition":main_blendable,
    "lightmapped_4wayblend":main_blendable,  # TODO: Form blendmap from luminance https://developer.valvesoftware.com/wiki/Lightmapped_4WayBlend#Controlling_Blendinghttps://developer.valvesoftware.com/wiki/Lightmapped_4WayBlend#Controlling_Blending
    "multiblend":           main_blendable,
    "lightmappedtwotexture":main_ubershader,  # 2 multiblend $texture2 nocull scrolling, model, additive.
    "unlittwotexture":      main_ubershader,  # 2 multiblend $texture2 nocull scrolling, model, additive.
    "cable":                "cables",
    "splinerope":           "cables",
    "shatteredglass":       core.glass,
    "wireframe":            "tools_wireframe",
    "wireframe_dx9":        "error",
    #"spritecard":           "spritecard",  these are just vtexes with params defined in vpcf renderer - skip
    #"subrect":              "spritecard",  # should we just cut? $Pos "256 0" $Size "256 256" $decalscale 0.25 decals\blood1_subrect.vmt
    #"weapondecal": weapon sticker
    "patch":                main_ubershader, # fallback if include doesn't have one
    #grass
    #customweapon
    #decalbasetimeslightmapalphablendselfillum
    #screenspace_general
    #sprite
    #nodraw
    #particlesphere
    #shadow
    #weapondecal
    #eyes
    #flashlight_shadow_decal
    #modulate
    #weapondecal_dx9
}

def chooseShader():
    get_shader = lambda v: v() if callable(v) else v
    d = {get_shader(x):0 for x in list(shaderDict.values())}

    if vmt.shader not in shaderDict:
        if sh.DEBUG:
            failureList.add(f"{vmt.shader} unsupported shader", vmt.path)
        return core.black_unlit

    d[get_shader(shaderDict[vmt.shader])] += 1

    if vmt.is_tool_material():
        return "generic"

    if vmt.KeyValues['$beachfoam']:
        return "csgo_beachfoam"

    if vmt.shader == "decalmodulate":
        if STEAMVR:
            vmat.KeyValues["F_MODULATE_2X"] = 1
            return steamvr.projected_decal_modulate()
        return core.projected_decals()

    if vmt.KeyValues['$decal'] == 1:
        return static_decal_solution()

    if vmt.shader == "worldvertextransition":
        if vmt.KeyValues['$basetexture2']: d[main_blendable()] += 10

    elif vmt.shader == "lightmappedgeneric":
        if vmt.KeyValues['$newlayerblending'] == 1: d[main_blendable()] += 10

    return get_shader(max(d, key = d.get))

ignoreList = [ "dx9", "dx8", "dx7", "dx6", "proxies"]

def default(texture_type:str, extension:str = ".tga") -> str:
    return VMAT_DEFAULT_PATH.as_posix() + "/default" + texture_type + extension

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

def formatNewTexturePath(vmtPath, textureType = TEXTURE_FILEEXT, noRename = False, forReal = True):
    #if USE_DEFAULT_FOR_MISSING_TEXTURE and not os.path.exists(vmtPath):
    #    return default(textureType)

    texturePath = sh.output(fixVmtTextureDir(vmtPath))
    if not texturePath.is_file():
        # it's an animated texture!
        if (frame:=texturePath.with_stem(texturePath.stem + "000")).is_file():
            frames = [frame]
            for i in range(1, 1000):
                frame = texturePath.with_stem(f"{texturePath.stem}{i:03}")
                if not frame.is_file(): break
                frames.append(frame)
            grid_w, grid_h, texturePath = TextureFramesToSheet(frames)
            vmat.KeyValues["g_nNumAnimationCells"] = len(frames)
            #vmat.KeyValues["g_flAnimationTimePerFrame"] = 1 / fps
            vmat.KeyValues["g_vAnimationGrid"] = f"[{grid_w} {grid_h}]"
    else:
        # animation sheet is already built
        if (sheetdata:=texturePath.with_name(texturePath.stem + '.sheet.json')).is_file():
            vmat.KeyValues.update(sh.GetJson(sheetdata))

    return texturePath.local.as_posix()

def getTexture(vtf_path):
    "get vtf source"
    # TODO: if still not found check for vtf in input
    # if exists, use vtf_to_tga to extract it to output
    # source1import does the same
    return None

def createMask(image_path, copySub = '_mask', channel = 'A', invert = False, queue = True) -> str:

    if not (image_path:=fixVmtTextureDir(image_path)):
        return default(copySub)
    image_path = sh.output(Path(image_path))

    newMaskPath = image_path.parent /\
        f"{image_path.stem}_{channel[:3].lower()}{'-1' if invert else ''}{copySub + image_path.suffix}"

    sh.msg(f"createMask{image_path.local.relative_to(materials).as_posix(), copySub, channel, invert, queue} -> {newMaskPath.local}")

    if sh.MOCK:
        newMaskPath.open('a').close()
        return newMaskPath.local.as_posix()

    if newMaskPath.exists():
        return newMaskPath.local.as_posix()

    if not image_path.is_file():
        sh.msg("Couldn't find image", image_path)
        failureList.add(f"createMask not found", f'{vmt.path.local} - {image_path.local}')
        print(f"~ ERROR: Couldn't find requested image ({image_path.local}).\nPlease make sure all textures have been pre-exported.")
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
        if (copySub == ("_gloss" if STEAMVR else "_rough")
        and colors[0][1] == (255 if STEAMVR else 0)):  # fix some very dumb .convert('RGBA') with 255 255 255 alpha
            return default(copySub)  # TODO: should this apply to other types of masks as well?
        return fixVector(f"{{{colors[0][1]} {colors[0][1]} {colors[0][1]}}}", True)

    bg = Image.new("L", image.size)

    # Copy the specified channel to the new image using itself as the mask
    bg.paste(imgChannel)

    bg.convert('L').save(newMaskPath, optimize=True)  #.convert('P', palette=Image.ADAPTIVE, colors=8)
    bg.close()
    print("+ Saved mask to", newMaskPath.local)

    return newMaskPath.local.as_posix()

########################################################################
# Build sky cubemap from sky faces
# (blue_sky_up.tga, blue_sky_ft.tga, ...) -> blue_sky_cube.tga
# https://developer.valvesoftware.com/wiki/File:Skybox_Template.jpg
# https://learnopengl.com/img/advanced/cubemaps_skybox.png
# ----------------------------------------------------------------------
def createSkyCubemap(json_collection: Path, maxFaceRes: int = 0):

    cube_name = None
    faceP = sh.GetJson(json_collection)

    if len(faceP) < 2:  # sky_l4d_rural02_ldr and co.
        return
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
        maxFaceRes = max(maxFaceRes, max(size[0], size[1]))  # the largest face determines the resolution of the full image
        if cube_name is None:  # Derive _cube name from face name. Dont get duplicates alla nukeblank_cube, dustblank_cube
            cube_name = facePath.stem[:-2].lower()

    if not len(faceList):
        return

    # cube_name = cube_name.rstrip('_')
    img_ext = '.pfm' if hdrType else TEXTURE_FILEEXT
    sky_cubemap_path =  sh.output( skyboxmaterials / (cube_name + '_cube' + img_ext))

    # BlendCubeMapFaceCorners, BlendCubeMapFaceEdges

    if not OVERWRITE_SKYCUBES and sky_cubemap_path.is_file():
        return sky_cubemap_path

    cube_w = 4 * maxFaceRes
    cube_h = 3 * maxFaceRes

    def get_transform(face: Literal['up', 'dn', 'lf', 'rt', 'bk', 'ft'], faceRotate: int):
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
        return pasteCoord, faceRotate

    if hdrType != 'uncompressed':
        image_mode = 'RGBA' if (hdrType == 'compressed') else 'RGB'
        SkyCubemapImage = Image.new(image_mode, (cube_w, cube_h), color = (0, 0, 0))
    else:
        SkyCubemapImage = np.zeros((cube_h, cube_w, 3), dtype='float32')

    for face, facePath in faceList.items():
        #faceScale = faceParams[face].get('scale')
        if hdrType != 'uncompressed':
            if not (faceImage := Image.open(facePath).convert(image_mode)): continue
        else:
            try: faceImage, scale, _ = PFM.read_pfm(facePath)
            except Exception: continue

        pasteCoord, faceRotate = get_transform(face, int(faceParams[face].get('rotate') or 0))
        if hdrType != 'uncompressed':
            if faceImage.width != maxFaceRes:  # scale to fit on the y axis
                faceImage = faceImage.resize((maxFaceRes, round(faceImage.height * maxFaceRes/faceImage.width)), Image.BICUBIC)
            if faceRotate:
                faceImage = faceImage.rotate(faceRotate)

            SkyCubemapImage.paste(faceImage, pasteCoord)
        else:
            if faceRotate:
                faceImage = np.rot90(faceImage, -1)

            SkyCubemapImage[pasteCoord[1]:pasteCoord[1]+faceImage.shape[0],
                            pasteCoord[0]:pasteCoord[0]+faceImage.shape[1]] = np.flipud(faceImage)

    if hdrType is None:
        SkyCubemapImage.save(sky_cubemap_path)
    elif hdrType == 'uncompressed':
        PFM.write_pfm(sky_cubemap_path, SkyCubemapImage)
    else:
        # https://developer.valvesoftware.com/wiki/Valve_Texture_Format#:~:text=RGB%20%3D%20(RGB%20*%20(A%20*%2016))%20/%20262144
        compressed_array = np.asarray( SkyCubemapImage, dtype='uint32')
        RGB = compressed_array[:,:,:3]
        A = compressed_array[:,:,[-1]]
        uncompress = (((RGB * (A * 16) / 262144) * HDRCOMPRESS_FIX_MUL) ** HDRCOMPRESS_FIX_EXP).astype(np.float32)
        # one between source2 and GIMP is reading the PFM flipped upside down. uncomment to display correctly on GIMP
        #uncompress = np.flipud(uncompress)
        PFM.write_pfm(sky_cubemap_path, uncompress)

    return sky_cubemap_path

def TextureFramesToSheet(frames: list[Path]):
    # find closest power of two number
    grid_max_power = math.ceil(math.log2(len(frames)))
    # keep the grid squarish
    grid_rows = 2 ** math.ceil(grid_max_power/2)
    grid_columns = 2 ** math.floor(grid_max_power/2)

    if sh.MOCK:
        sheet_path = sh.output(frames[0].with_stem(frames[0].stem[:-3]))
        sheet_path.open('a').close()
    else:
        sheet_path = save_atlas(frames, grid_rows, grid_columns)
    print("+ Saved animated texture", sheet_path.local.as_posix())
    sheet_path.with_name(sheet_path.stem + '.sheet.json').write_text(
        f'{{"g_nNumAnimationCells":{len(frames)},"g_vAnimationGrid":"[{grid_rows} {grid_columns}]"}}'
    )

    return grid_rows, grid_columns, sheet_path

def save_atlas(frames, grid_rows, grid_columns):
    sheet_image: Image = None
    sheet_path: Path = None
    for frame_no, frame in enumerate(frames):
        frame_image = Image.open(frame)
        if sheet_image is None:
            sheet_width = frame_image.width*grid_rows
            sheet_height = frame_image.height*grid_columns
            sheet_image = Image.new('RGB', (sheet_width, sheet_height), color = (0, 0, 0))
            sheet_path = sh.output(frame.with_stem(frame.stem[:-3]))
        frame_position_in_sheet = (
            (frame_no % grid_rows) * frame_image.width,
            (frame_no // grid_rows) * frame_image.height
        )
        sheet_image.paste(frame_image, frame_position_in_sheet)

    sheet_image.save(sheet_path)
    return sheet_path

def set_texture_settings(local_texture_path: Path, **settings):
    image_path = sh.output(local_texture_path)
    if not image_path.exists():
        return
    if (settings_file := image_path.with_suffix(".txt")).is_file():
        if not OVERWRITE_VMAT:
            return
        settKV = KV.FromFile(settings_file)
        settKV.update(settings)
    else:
        settKV = KV("settings", settings)
    settKV.save(settings_file)

def flipNormalMap(localPath):
    if NORMALMAP_G_VTEX_INVERT:
        set_texture_settings(localPath, legacy_source1_inverted_normal = 1)
        return

    image_path = sh.output(localPath)
    if not image_path.exists():
        return
    # Open the image and convert it to RGBA, just in case it was indexed
    image = Image.open(image_path).convert('RGBA')

    r,g,b,a = image.split()
    g = ImageOps.invert(g)
    final_transparent_image = Image.merge('RGBA', (r,g,b,a))
    final_transparent_image.save(image_path)

def fixVector(s, addAlpha = 1, returnList = False):

    s = str(s)
    if('{' in s or '}' in s): likelyColorInt = True
    else: likelyColorInt = False

    s = s.strip()  # TODO: remove letters
    s = s.replace('"', '').replace("'", "")
    s = s.strip().replace(",", "").strip('][}{').strip(')(')

    try: originalValueList = [str(float(i)) for i in s.split(' ') if i != '']
    except ValueError: return None #originalValueList =  [1.000000, 1.000000, 1.000000]

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

def presence(_, rv=1):
    return rv

def fix_envmap(vmtVal):
    if 'environment maps/metal' in vmtVal:
        if vmtVal == 'environment maps/metal_generic_003':
            vmt.KeyValues['$metalness'] = 0.55
        else:
            vmt.KeyValues['$metalness'] = 0.888
    elif 'env_cubemap' == vmtVal:
        vmat.KeyValues['F_SPECULAR_CUBE_MAP'] = 1
    else:
        vmat.KeyValues['F_SPECULAR_CUBE_MAP'] = 2
        vmat.KeyValues['TextureCubeMap'] = default('_cube', '.pfm')#TODO
    return 1  # presence()


def bool_val(bInvert = False):
    def bool_val(v: str):
        rv = bool(float(v))
        if bInvert:
            rv = not rv
        return int(rv)
    return bool_val

def mapped_val(v: str, dMap: dict):
    if not v or v not in dMap:
        return None  # use default value
    return int(dMap[v])

def float_val(v: str):
    return "{:.6f}".format(float(v.strip(' \t"')))

def uniform_vec2(v: str):
    return "[{:.6f} {:.6f}]".format(float(v), float(v))

def vmat_layered_param(vmatKey, layer = 'A', force = False):
    if vmat.shader in (hlvr.vr_simple_2way_blend(), "blendable") or force:
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
            except (IndexError, ValueError): continue

            if term == 'rotate':
                self.rotate = nextTerm
                continue

            try: nextnextTerm =  float(mxTerms[i+2])
            except (IndexError, ValueError): continue

            if term in ('center', 'scale', 'translate'):
                setattr(self, term, (nextTerm, nextnextTerm))

def is_convertible_to_float(value):
    try: float(value)
    except ValueError: return False
    else: return True

class vmat_translation:
    def __init__(self,
            one: str,
            two: str | int | float = None,
            three: list[Callable, Any] = None,
            *extralines: tuple[str, str]
        ):
        if isinstance(one, tuple):
            raise ValueError("unpack your arguments")

        self._innertuple = (one, two, three, *extralines)

        self.replacement = one
        self.defaultval = two

        _build_extralines = lambda iterable:\
            list() if iterable is None else list(xtra for xtra in iterable if isinstance(xtra, tuple) and len(xtra) == 2)

        if isinstance(three, list) and len(three) and callable(three[0]):
            self.translfunc = three
            self.extralines = _build_extralines(extralines)
        else:
            self.translfunc = None
            self.extralines = _build_extralines(three, *extralines)

    "texture context"
    @property
    def texture_suffix(self): return self.defaultval
    @property
    def default_texture(self): return default(self.defaultval)

    "channeled_masks context"
    @property
    def extract_from(self): return self._innertuple[0]
    @property
    def extract_as(self): return self._innertuple[1]
    @property
    def channel_to_extract(self): return self._innertuple[2]

    def translate(self, vmtKey: str, vmtVal: str) -> str | None:
        func_ = self.translfunc[0]
        args_ = []
        args_.insert(0, vmtVal)
        args_.extend(self.translfunc[1:])
        if func_ in (formatNewTexturePath, createMask):
            args_.insert(1, self.texture_suffix)

        sh.msg(vmtKey, "->\t" + func_.__name__, args_, end=" -> ")
        try:
            return func_(*args_)
        except ValueError as errrrr:
            print("Got ValueError:", errrrr, "on", f'{vmtKey}: {vmtVal} with {func_.__name__}')
            failureList.add(f'ValueError on {func_.__name__}', f'{vmt.path.local} @ "{vmtKey}": "{vmtVal}"')

# callable - to evaluate conditionals at runtime
vmt_to_vmat_pre: Callable[[], dict[ str, dict[str, tuple | None] ]] = lambda: {

'features': {

    '$translucent':     ('F_TRANSLUCENT',           '1'),  # "F_BLEND_MODE 0" for projected_decals
    '$alphatest':       ('F_ALPHA_TEST',            '1'),
    '$phong':           ('F_SPECULAR',              '1'),
    '$envmap':          ('F_SPECULAR',              '1', [fix_envmap]),  # in "environment maps/metal" | "env_cubemap" F_SPECULAR_CUBE_MAP 1 // In-game Cube Map
    '$envmapanisotropy':('F_SPECULAR_CUBE_MAP_ANISOTROPIC_WARP', '1'), # requires F_ANISOTROPIC_GLOSS 1
    '$ssbump':          ('F_ENABLE_NORMAL_SELF_SHADOW', '1') if SBOX else None,
    '$selfillum':       ('F_SELF_ILLUM',            '1'),
    '$additive':        ('F_ADDITIVE_BLEND',        '1'),
    '$ignorez':         ('F_DISABLE_Z_BUFFERING',   '1'),
    '$nocull':          ('F_RENDER_BACKFACES',      '1'),  # F_NO_CULLING 1 # see this for certain sheeted texs -> F_USE_SHEETS 1
    '$decal':           ('F_OVERLAY',               '1'),
    '$flow_debug':      ('F_FLOW_DEBUG',            '0'),
    '$detailblendmode': ('F_DETAIL_TEXTURE',        '1', [mapped_val, {'0':'1', '1':'2', '7': '1', '12':'0'} ]),  # https://developer.valvesoftware.com/wiki/$detail#Parameters_and_Effects
    '$decalblendmode':  ('F_DETAIL_TEXTURE',        '1', [mapped_val, {'0':'1', '1':'2', '12':'0'} ]),  # materialsystem\stdshaders\BaseVSShader.h#L26
    '$sequence_blend_mode': ('F_FAST_SEQUENCE_BLEND_MODE', '1', [mapped_val, {'0':'1', '1':'2', '2':'3'}]),
    '$gradientmodulation':  ('F_GRADIENTMODULATION', '1'),
    '$selfillum_envmapmask_alpha': ('F_SELF_ILLUM', '1'),
    '$forceenvmap':     ('F_REFLECTION_TYPE', 1),  # Water reflection type
    '$addbumpmaps':     ('F_ADDBUMPMAPS',     1),
    "$masks1":          ('F_MASKS_1',    '1') if DOTA2 else None,
    "$masks2":          ('F_MASKS_2',    '1') if DOTA2 else None,
    "$newlayerblending":('F_LAYER_BORDER_TINT', '2') if DOTA2 else \
                        ('F_FANCY_BLENDING', '1') if STEAMVR else \
                        None,

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
    '$modelmaterial':   ('TextureColor',        '_color',   [formatNewTexturePath]),
    '$compress':        ('TextureSquishColor',  '_color',   [formatNewTexturePath], ('F_MORPH_SUPPORTED', 1), ('F_WRINKLE', 1)),
    '$stretch':         ('TextureStretchColor', '_color',   [formatNewTexturePath], ('F_MORPH_SUPPORTED', 1), ('F_WRINKLE', 1)),

    '$normalmap':       ('TextureNormal',       '_normal',  [formatNewTexturePath]),  # also covers $bumpmap
    '$bumpcompress':    ('TextureSquishNormal', '_normal',  [formatNewTexturePath], ('F_MORPH_SUPPORTED', 1), ('F_WRINKLE', 1)),
    '$bumpstretch':     ('TextureStretchNormal','_normal',  [formatNewTexturePath], ('F_MORPH_SUPPORTED', 1), ('F_WRINKLE', 1)),

    ## Layer blend mask
    '$blendmodulatetexture':\
                        ('TextureMask',             '_mask',   [createMask, 'G', False], ('F_BLEND', 1)) if HLVR else \
                        ('TextureLayer1RevealMask', '_blend',  [createMask, 'G', False], ('F_BLEND', 1)) if STEAMVR else \
                        ('TextureBlendMaskB',      '_blend',  [createMask, 'G', False]) if SBOX else \
                        None,
    ## Layer 1
    '$basetexture2':    ('TextureColorB' if not STEAMVR else 'TextureLayer1Color',  '_color',  [formatNewTexturePath]),
    # There is also Texture2Color, F_TWOTEXTURE, Texture2Translucency, g_vTexCoord2
    '$texture2':        ('TextureColorB' if not STEAMVR else 'TextureLayer1Color',   '_color',  [formatNewTexturePath]),  # UnlitTwoTexture
    '$bumpmap2':        ('TextureNormalB' if not STEAMVR else 'TextureLayer1Normal', '_normal', [formatNewTexturePath], None if not STEAMVR else ('F_BLEND_NORMALS',  1)),

    ## Layer 2-3
    '$basetexture3':    ('TextureColorC' if SBOX else 'TextureLayer2Color',  '_color',  [formatNewTexturePath]),
    '$basetexture4':    ('TextureColorD' if SBOX else 'TextureLayer3Color',  '_color',  [formatNewTexturePath]),

    '$normalmap2':      ('TextureNormal2',      '_normal', [formatNewTexturePath],     ('F_SECONDARY_NORMAL', 1)),  # used with refract shader
    '$flowmap':         ('TextureFlow',         '',        [formatNewTexturePath],     ('F_FLOW_NORMALS', 1), ('F_FLOW_DEBUG', 1)),
    '$flow_noise_texture':('TextureNoise',      '_noise',  [formatNewTexturePath],     ('F_FLOW_NORMALS', 1), ('F_FLOW_DEBUG', 2)),
    '$detail':          ('TextureDetail',       '_detail', [formatNewTexturePath],     ('F_DETAIL_TEXTURE', 1)),
    '$decaltexture':    ('TextureDetail',       '_detail', [formatNewTexturePath],     ('F_DETAIL_TEXTURE', 1), ('F_SECONDARY_UV',  1), ('g_bUseSecondaryUvForDetailTexture',  1)),
    '$detail2':         ('TextureDetail2',      '_detail', [formatNewTexturePath]),

    '$selfillummask':   ('TextureSelfIllumMask','_selfillummask', [formatNewTexturePath]),
    '$tintmasktexture': ('TextureTintMask',     '_mask',   [createMask, 'G', False],   ('F_TINT_MASK',  1)), #('TextureTintTexture',)
    '$_vmat_metalmask': ('TextureMetalness',    '_metal',  [formatNewTexturePath],     ('F_METALNESS_TEXTURE',  1)) if not STEAMVR else \
                        ('TextureReflectance',    '_refl',  [formatNewTexturePath]),   # F_SPECULAR too?
    '$_vmat_transmask': ('TextureTranslucency', '_trans',  [formatNewTexturePath]),
    '$_vmat_rimmask':   ('TextureRimMask',      '_rimmask',[formatNewTexturePath]),

    # only the G channel ## $ambientoccltexture': '$ambientocclusiontexture':
    '$ao':          ('TextureAmbientOcclusion', '_ao',     [createMask, 'G', False],    ('F_AMBIENT_OCCLUSION_TEXTURE',  1)),  # g_flAmbientOcclusionDirectSpecular "1.000"
    '$aotexture':   ('TextureAmbientOcclusion', '_ao',     [createMask, 'G', False],    ('F_AMBIENT_OCCLUSION_TEXTURE',  1)),  # g_flAmbientOcclusionDirectSpecular "1.000"

    '$phongexponenttexture': ('TextureSpecularExponent', '_specexp', [formatNewTexturePath]),
    #'$phongexponent2' $phongmaskcontrastbrightness2, $phongbasetint2, $phongamount2
    '$lightwarptexture': ('TextureDiffuseWarp', '_diffusewarp', [formatNewTexturePath], ('F_DIFFUSE_WARP', 1)),
    '$phongwarptexture': ('TextureSpecularWarp', '_specwarp', [formatNewTexturePath],   ('F_SPECULAR_WARP', 1)),

    '$envmapmask':  ('TextureCubeMapSeparateMask', '_mask', ('F_MASK_CUBE_MAP_BY_SEPARATE_MASK', 1)) if DOTA2 else \
                    ('TextureRoughness',    '_rough',      [createMask, 'L', True]) if not STEAMVR else \
                    ('TextureGlossiness',   '_gloss',      [formatNewTexturePath]),

    #('$phong', 1): {
    '$phongmask':   ('TextureRoughness',    '_rough',      [formatNewTexturePath]) if not STEAMVR else \
                    ('TextureGlossiness',   '_gloss',      [formatNewTexturePath]),
    #},
},

'transform': {  # Center Scale Rotation Offset F_TEXTURETRANSFORMS
    '$basetexturetransform':    ('g_vTexCoord',),  # g_vLayer1TexCoord for blends F_LAYERS
    '$detailtexturetransform':  ('g_vDetailTexCoord',),  #  g_vDetailTexCoordXform
    '$bumptransform':           ('g_vNormalTexCoord',),  # g_vLayer1NormalTexCoord for blends F_LAYERS
    '$blendmodulatetransform':  ('g_vBlendModulateTexCoord',),
    '$bumptransform2':          ('g_vLayer2NormalTexCoord',), # g_vTexCoordScale2 in hlvr
    '$basetexturetransform2':   ('g_vLayer2TexCoord',),
    '$texture2transform':       ('g_vTexCoord2',),
    #'$blendmasktransform':      (''),
    #'$envmapmasktransform':     (''),
    #'$envmapmasktransform2':    (''),
},

'settings': {

    '$detailblendfactor':   ('g_flDetailBlendFactor',   '1.000', [float_val]), #'$detailblendfactor2', '$detailblendfactor3'
    '$detailscale':         ('g_vDetailTexCoordScale',  '[1.000 1.000]', [fixVector, False]),
    '$detailscale2':        ('g_vLayer2DetailScale',    '[1.000 1.000]', [fixVector, False]),

    '$color':               ('g_vColorTint',        '[1.000 1.000 1.000 0.000]',    [fixVector, True]),
    '$color2':              ('g_vColorTint',        '[1.000 1.000 1.000 0.000]',    [fixVector, True]),
    '$selfillumtint':       ('g_vSelfIllumTint',    '[1.000 1.000 1.000 0.000]',    [fixVector, True]),
    '$envmaptint':          ('g_vEnvironmentMapTint','[1.000 1.000 1.000 0.000]',    [fixVector, True]), # g_vSpecularColor
    '$emissiveblendtint':   ('g_vEmissiveTint',     '[1.000 1.000 1.000 0.000]',    [fixVector, True]),
    '$layertint1':          ('g_vLayer1Tint',       '[1.000 1.000 1.000 0.000]',    [fixVector, True]),
    '$layertint2':          ('g_vLayer2Tint',       '[1.000 1.000 1.000 0.000]',    [fixVector, True]),
    '$reflecttint':         ('g_vReflectionTint',   '[1.000 1.000 1.000 0.000]',    [fixVector, True]),
    '$refracttint':         ('g_vRefractionTint',   '[1.000 1.000 1.000 0.000]',    [fixVector, True]),
    '$fogcolor':            ('g_vWaterFogColor',    '[1.000 1.000 1.000 0.000]',    [fixVector, True]),

    '$gradientcolorstop0':  ('g_vGradientColorStop0', '[1.000 1.000 1.000 0.000]',  [fixVector, True]),
    '$gradientcolorstop1':  ('g_vGradientColorStop1', '[1.000 1.000 1.000 0.000]',  [fixVector, True]),
    '$gradientcolorstop2':  ('g_vGradientColorStop2', '[1.000 1.000 1.000 0.000]',  [fixVector, True]),
    '$uvscale':             ('g_flTexCoordScale', '', [float_val]),
    # MultiBlend
    '$scale':               None,
    '$scale2':              ('g_vTexCoordScale2', '[1.000 1.000]', [uniform_vec2]),
    '$scale3':              ('g_vTexCoordScale3', '[1.000 1.000]', [uniform_vec2]),
    '$scale4':              ('g_vTexCoordScale4', '[1.000 1.000]', [uniform_vec2]),

    # s1 channels relative to each other "[0 0 0]" = "[1 1 1]" (lum preserving) -> s2 is color so it has a brightness factor within it
    # perhaps default to 0.5 0.5 0.5 and scale it with $phongboost, etc
    '$phongtint':           ('g_vSpecularColor',    '[1.000 1.000 1.000 0.000]',    [fixVector, True]),

    '$frame':               ('g_flAnimationFrame',      '0.000',    [float_val], ('F_TEXTURE_ANIMATION', 1)),
    '$alpha':               ('g_flOpacityScale',        '1.000',    [float_val]),
    '$alphatestreference':  ('g_flAlphaTestReference',  '0.500',    [float_val], ('g_flAntiAliasedEdgeStrength', 1.0)),
    '$blendtintcoloroverbase':('g_flModelTintAmount',   '1.000',    [float_val]),  # $layertint1
    '$selfillumscale':      ('g_flSelfIllumScale',      '1.000',    [float_val]),
    '$phongexponent':       ('g_flSpecularExponent',    '32.000',   [float_val]),
    '$phongboost':          ('g_flPhongBoost',          '1.000',    [float_val]),
    '$metalness':           ('g_flMetalness',           '0.000',    [float_val]),
    '$_metalness2':         ('g_flMetalnessB',          '0.000',    [float_val]),
    '$ssbump':   ('g_flLightRangeForSelfShadowNormals', '1.000',    [float_val]) if SBOX else None, # tiny hack
    '$reflectamount':       ('g_flReflectionAmount',    '',         [float_val]),
    '$refractamount':       ('g_flRefractionAmount',    '',         [float_val]),
    #'$refractamount':       ('g_flRefractScale',        '0.200',    [float_val]),
    '$flow_worlduvscale':   ('g_flWorldUvScale',        '1.000',    [float_val]),
    '$flow_noise_scale':    ('g_flNoiseUvScale',        '0.010',    [float_val]),  # g_flNoiseStrength?
    '$flow_bumpstrength':   ('g_flBumpStrength',        '',         [float_val]),
    '$flow_timescale':      ('g_flFlowTimeScale',       '',         [float_val]),
    '$flow_normaluvscale':  ('g_flNormalUvScale',       '',         [float_val]),
    '$flow_timeintervalinseconds': ('g_flNormalFlowTimeIntervalInSeconds', '', [float_val]),
    '$flow_uvscrolldistance':      ('g_flNormalFlowUvScrollDistance', '', [float_val]),

    '$forcefresnel':('g_flReflectance', '', [float_val]), # requires F_FRESNEL
    '$fogend':      ('g_flWaterDepth',  '', [float_val]),
    '$fogstart':    ('g_flWaterStart',  '', [float_val]),


    '$nofog':   ('g_bFogEnabled',       '0',        [bool_val(bInvert=True)]),
    '$notint':  ('g_flModelTintAmount', '1.000',    [bool_val(bInvert=True)]),
    '$allowdiffusemodulation': ('g_flModelTintAmount', '1.000',    [bool_val()]),

    # rimlight
    '$rimlightscale':    ('g_flRimLightScale',   '1.000',    [float_val]),
    '$rimlightcolor':    ('g_vRimLightColor'    '[1.000000 1.000000 1.000000 0.000000]', [fixVector, True]),
    #'$warpindex':           ('g_flDiffuseWrap',         '1.000',    [float_var]),  # requires F_DIFFUSE_WRAP 1. "?
    #'$diffuseexp':          ('g_flDiffuseExponent',     '2.000',    [float_var], 'g_vDiffuseWrapColor "[1.000000 1.000000 1.000000 0.000000]'),

    # shader.blend and shader.vr_standard(SteamVR) -- $NEWLAYERBLENDING
    '$blendsoftness':       ('g_flLayer1BlendSoftness' if not SBOX else 'g_flBlendSoftnessB',
                                                        '0.500',    [float_val]),
    '$layerborderstrenth':  ('g_flLayer1BorderStrength','0.500',    [float_val]),
    '$layerborderoffset':   ('g_flLayer1BorderOffset',  '0.000',    [float_val]),
    '$layerbordersoftness': ('g_flLayer1BorderSoftness','0.500',    [float_val]),
    '$layerbordertint':     ('g_vLayer1BorderColor',    '[1.000000 1.000000 1.000000 0.000000]', [fixVector, True]),

    # Diferent names in source1import.exe why?
    #('$newlayerblending', 1): {  # F_FANCY_BLENDING
    #    '$layerbordertint':     ('g_vLayerBorderTint',      '[1.000000 1.000000 1.000000 0.000000]', [fixVector, True]),
    #    '$blendsoftness':       ('g_flBlendSoftness',       '0.500',    [float_val]),
    #    '$layerborderstrength': ('g_flLayerBorderStrength', '0.500',    [float_val]),
    #    '$layerborderoffset':   ('g_flLayerBorderOffset',   '0.000',    [float_val]),
    #    '$layerbordersoftness': ('g_flLayerBorderSoftness', '0.500',    [float_val]),
#F_TEXTURETRANSFORMS TextureLayer1Detail g_vLayer1DetailScale $detailtint
# $bumpdetailscale1       $bumpdetailscale2       g_vLayer1DetailTintAndBlend
# $detail2        TextureLayer2Detail     $detailScale2   g_vLayer2DetailScale
# $detailtint2    g_vLayer2DetailTintAndBlend     F_DETAILTEXTURE
# $detailblendmode F_DETAILBLENDMODE
# F_SPECULAR F_SPECULAR_CUBE_MAP DecalColor DecalTranslucency       [1.000000 1.000000 1.000000 1.000000]
    #}
},

'channeled_masks': {  # 1-X will extract and invert channel X // M_1-X to only invert on models
   #'$vmtKey':                      (extract_from,       extract_as,       channel to extract)
    '$normalmapalphaenvmapmask':    ('$normalmap',    '$envmapmask',        'A' if STEAMVR else '1-A'),
    '$basealphaenvmapmask':         ('$basetexture',    '$envmapmask',      'A' if STEAMVR else '1-A'),
    '$envmapmaskintintmasktexture': ('$tintmasktexture','$envmapmask',      'R' if STEAMVR else '1-R'),
    '$basemapalphaphongmask':       ('$basetexture',    '$phongmask',       'A' if STEAMVR else '1-A'),
    '$basealphaphongmask':          ('$basetexture',    '$phongmask',       'A' if STEAMVR else '1-A'),
    '$normalmapalphaphongmask':     ('$normalmap',    '$phongmask',         'A' if STEAMVR else '1-A'),
    '$bumpmapalphaphongmask':       ('$normalmap',    '$phongmask',         'A' if STEAMVR else '1-A'),
    '$basemapluminancephongmask':   ('$basetexture',    '$phongmask',       'L'),

    '$blendtintbybasealpha':        ('$basetexture',    '$tintmasktexture', 'A'),
    '$selfillum_envmapmask_alpha':  ('$envmapmask',     '$selfillummask',   'A'),

    '$translucent':                 ('$basetexture',    '$_vmat_transmask', 'A'),
    '$alphatest':                   ('$basetexture',    '$_vmat_transmask', 'A'),
    '$selfillum':                   ('$basetexture',    '$selfillummask',   'A'),
    #'$phong':                       ('$normalmap',    '$phongmask',       '1-A'),

    '$rimmask':         ('$phongexponenttexture',       '$_vmat_rimmask',   'A'),

    #'$masks1':  ('self', ('$_vmat_rimmask', '$phongalbedomask', '$_vmat_metalmask', '$warpindex'), 'RGBA') if IMPORT_MOD == "csgo" else \
    #            ('self', ('$rimmask', '$phongalbedomask', '$_vmat_metalmask', '$selfillum'), 'RGBA') if IMPORT_MOD == "dota" else \
    #            None,
    #'$masks2':  ('self', ("$shadowsaturationmask", '$phongalbedomask', '$_vmat_metalmask', '$warpindex'), 'RGBA') if IMPORT_MOD == "csgo" else \
    #            ('self', ('$detailmask', '$_vmat_metalmask', '$_vmat_metalmask', '$selfillum'), 'RGBA') if IMPORT_MOD == "dota" else \
    #            None,
},

'dicts': {
    "proxies": None#(None, None, proxyshit)
},

'SystemAttributes': {
    '$surfaceprop':     ('PhysicsSurfaceProperties', 'default', [str])
    #'$surfaceprop2'
    #'$surfaceprop3'
    #'$surfaceprop4'
},

'texture_settings': {
    '$noenvmapmip':             None,  # Lock specular cubemap to mip 0
    '$phongexponentfactor':     None,  # Multiply $phongexponenttexture by this amount
    '$invertphongmask':         None,  # Invert $phongmask specmask
},

# no direct replacement, etc
'others2': {
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
}
}

vmt_to_vmat = vmt_to_vmat_pre()

KNOWN = {}
"""for proxies; when $color is known as g_vTintColor, proxies yielding to $color can be translated"""

def convertVmtToVmat():
    # For each key-value in the vmt file...
    for vmtKey, vmtVal in vmt.KeyValues.iteritems():
        outKey = outVal = ''

        vmtKey: str = vmtKey.lower()
        vmtVal: str = str(vmtVal).strip().strip('"' + "'").strip(' \r\n\t"')

        # search through the dictionary above to find the appropriate replacement.
        for keyType, translate in vmt_to_vmat.items():

            vmatTranslation = translate.get(vmtKey)

            if not vmatTranslation:
                continue

            vmatTranslation = vmat_translation(*vmatTranslation)

            if ( vmatTranslation.replacement and vmatTranslation.defaultval ):

                outKey = vmatTranslation.replacement
                outVal = vmatTranslation.defaultval

                if (keyType == 'textures'):
                    outVal = default(vmatTranslation.texture_suffix)

                if vmtVal:
                    outVal = vmtVal

                if vmatTranslation.translfunc is not None:
                    if ((rv:=vmatTranslation.translate(vmtKey, vmtVal)) is not None):
                        outVal = rv
                        sh.msg(outKey, outVal)

            # it only has fixed extra lines
            elif (vmatTranslation.extralines):
                for key, value in vmatTranslation.extralines:
                    vmat.KeyValues[key] = value
                continue
            # transform is special
            elif keyType not in ('transform'):
                continue

            if keyType == 'features':
                if vmtKey == "$translucent" and vmat.shader in (core.projected_decals(), core.static_overlay()):
                    outKey = "F_BLEND_MODE"
                    outVal = (0 if (vmat.shader == core.projected_decals()) else 1)

            elif(keyType == 'textures'):
                # Layer A
                if vmtKey in ('$basetexture', '$hdrbasetexture', '$hdrcompressedtexture', '$normalmap'):
                    outKey = vmat_layered_param(vmatTranslation.replacement)

                if vmtKey.startswith('$basetexture'):
                    if (sh.ADJ or sh.DOTA2) and outVal != default("_color"):
                        set_texture_settings(outVal, mip_algorithm="Nice")

                if vmtKey in ('$normalmap', '$bumpmap2', '$normalmap2'):
                    if vmtVal == 'dev/flat_normal':
                        outVal = vmatTranslation.default_texture

                    # don't flip default normal
                    if outVal != default("_normal"):
                        # don't flip ssbump
                        if not vmt.KeyValues["$ssbump"]:
                            flipNormalMap(Path(outVal))

            elif(keyType == 'transform'):  # here one key can add multiple keys
                if not vmatTranslation.replacement:
                    continue
                transform = TexTransform(vmtVal)
                # no rotation in source 2
                #if(matrixList[MATRIX_ROTATE] != '0.000'):
                #    if(matrixList[MATRIX_ROTATIONCENTER] != '[0.500 0.500]')

                if transform.rotate:
                    sh.msg("HERE IT IS:", transform.rotate)

                # scale 5 5 -> g_vTexCoordScale "[5.000 5.000]"
                if(transform.scale != (1.000, 1.000)):
                    outKey = vmatTranslation.replacement + 'Scale'
                    outVal = fixVector(transform.scale, False)
                    vmat.KeyValues[outKey] = outVal

                # translate .5 2 -> g_vTexCoordOffset "[0.500 2.000]"
                if(transform.translate != (0.000, 0.000)):
                    outKey = vmatTranslation.replacement + 'Offset'
                    outVal = fixVector(transform.translate, False)
                    vmat.KeyValues[outKey] = outVal

                continue ## Skip default content write

            elif(keyType == 'channeled_masks'):
                outVmtTexture = vmatTranslation.extract_as
                sourceTexture = vmatTranslation.extract_from
                sourceChannel = vmatTranslation.channel_to_extract

                newTexture = vmt_to_vmat['textures'].get(outVmtTexture)
                if not newTexture:
                    break

                newTexture = vmat_translation(*newTexture)

                outKey = newTexture.replacement
                sourceSubString = newTexture.texture_suffix
                vmatTranslation.extralines = newTexture.extralines

                if vmt.KeyValues[outVmtTexture]:
                    print("~", vmtKey, "conflicts with", outVmtTexture + ". Aborting mask extration (using original).")
                    continue

                shouldInvert = False
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
                vmat.KeyValues.setdefault('SystemAttributes', {})[outKey] = outVal
                continue

            # Finally, add to vmat
            for additional_key, value in vmatTranslation.extralines:
                vmat.KeyValues[additional_key] = value

            vmat.KeyValues[outKey] = outVal

            # dont break some keys have more than 1 translation (e.g. $selfillum)

    if vmt.is_tool_material():
        toolattributes = vmat.KeyValues.setdefault("Attributes", {})
        toolattributes["tools.toolsmaterial"] = 1

        # most of these need nodraw
        if vmt.path.stem != "toolsblack":
            toolattributes["mapbuilder.nodraw"] = 1
        
        if not vmt.path.stem.endswith("clip"):
            toolattributes["mapbuilder.nonsolid"] = 1

        tags = list()
        for key, value in vmt.KeyValues.items():
            if not key.startswith("%"):
                continue
            key = key.lstrip("%").removeprefix("compile")
            if key == "keywords":
                continue
            toolattributes[f"mapbuilder.{key}"] = value
            tags.append(key)
            
        if sh.SBOX:
            toolattributes["mapbuilder.tags"] = " ".join(tags)

    if USE_SUGESTED_DEFAULT_ROUGHNESS and not vmt.is_tool_material() \
        and not vmat.shader == steamvr.projected_decal_modulate():
        # 2way blend has specular force enabled so maxing the rough should minimize specularity
        if vmat.shader == hlvr.vr_simple_2way_blend():
            #if vmat.KeyValues['F_SPECULAR'] == 1:
            #    default_rough = "[1.000000 1.000000 1.000000 0.000000]"
            vmat.KeyValues.setdefault("TextureRoughnessA", default("_rough_s1import"))
            vmat.KeyValues.setdefault("TextureRoughnessB", default("_rough_s1import"))
        else:
            vmat.KeyValues.setdefault("TextureRoughness", default("_rough_s1import"))

def convertSpecials():

    # fix phongmask logic
    if vmt.KeyValues["$phong"] == 1 and not vmt.KeyValues["$phongmask"]:
        # sniper scope

        bHasPhongMask = False
        for key, val in vmt_to_vmat['channeled_masks'].items():
            if vmat_translation(*val).extract_as == '$phongmask' and vmt.KeyValues[key]:
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
    if (vmt.shader == 'unlitgeneric'):
        if (vmat.shader in (main_ubershader(), "generic")):
            vmat.KeyValues["F_UNLIT"] = 1

    if STEAMVR:
        # 2 in 2 out
        if vmt.shader == 'worldvertextransition':
            vmat.KeyValues['F_BLEND'] = 1
        # 4 in 3 out, one is rip
        if vmt.shader == 'lightmapped_4wayblend':
            vmat.KeyValues['F_BLEND'] = 2 # 3 layers max in steamvr, not 4
    elif SBOX:
        if vmt.shader == 'worldvertextransition':
            vmat.KeyValues['F_MULTIBLEND'] = 1  # 2 layers
        if vmt.shader == 'lightmapped_4wayblend':
            vmat.KeyValues['F_MULTIBLEND'] = 3 # 4 layers

    # fix mod2x logic for projected_decals
    if vmt.shader == 'decalmodulate':
        vmat.KeyValues['F_BLEND_MODE'] = 1 if (vmat.shader == core.projected_decals()) else 3

    # fix lit logic for projected_decals
    if vmt.shader in ('lightmappedgeneric', 'vertexlitgeneric'):
        if vmat.shader == core.static_overlay():      vmat.KeyValues["F_LIT"] = 1
        elif vmat.shader == core.projected_decals(): vmat.KeyValues["F_SAMPLE_LIGHTMAP"] = 1  # what does this do

    if vmat.shader == core.projected_decals():
        vmat.KeyValues['F_CUTOFF_ANGLE'] = 1

    elif vmat.shader == main_ubershader():
        if SBOX and vmt.KeyValues["$ssbump"]:
            vmat.KeyValues['F_SPECULAR'] = 1 # self shadowing normals require specular to work

    # csgo viewmodels
    # if not mod == csgo: return
    viewmodels = materials / "models/weapons/v_models"
    if vmt.path.local.is_relative_to(viewmodels):
        # use _ao texture in \weapons\customization
        wpn_name = vmt.path.parent.name
        if (vmt.path.stem == wpn_name or vmt.path.stem == wpn_name.split('_')[-1]):
            vm_customization = viewmodels.parent / "customization"
            ao_path = sh.output(vm_customization/wpn_name/ (str(wpn_name) + "_ao"+ TEXTURE_FILEEXT))
            if ao_path.is_file():
                ao_path_new = sh.output(materials/viewmodels/wpn_name/ao_path.name)
                try:
                    if not ao_path_new.is_file() and ao_path_new.parent.exists():
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
        if face_collect_path.is_file() and not OVERWRITE_VMAT:
            return sh.skip('already-collected', face_collect_path)
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
            # Not deleting just incase they are needed somewhere else, and to save time on future imports
            face_path_new = sh.output(legacy_skyfaces / face_path.name)
            if face_path.is_file():
                face_path.parent.MakeDir()
                face_path_new.unlink(missing_ok=True)
                face_path.rename(face_path_new)
            face_path = face_path_new

        if face_path.is_file():
            path = face_path.local.as_posix()
            Collect[face] = {}  # Dict won't be used if it won't have anything other than path

            faceTransform = TexTransform(vmt.KeyValues.get('$basetexturetransform'))
            if(faceTransform.rotate != 0):
                Collect[face]['rotate'] = faceTransform.rotate
                sh.msg("Collecting", face, "transformation: rotate", Collect[face]['rotate'], 'degrees')

            if Collect[face]:
                Collect[face]['path'] = path
            else:
                Collect[face] = path
            print(f"    + Collected face {face.upper()} for {name}_cube{src_extension}")
            sh.UpdateJson(face_collect_path, Collect)
        else:
            print("missing sky face:", face_path.local)

        return face_collect_path

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

    cubemap = createSkyCubemap(json_collection)
    if cubemap:
        sky_cubemap_path = cubemap.local

    with open(vmat_path, 'w') as fp:
        fp.write(KV('Layer0', {
            'shader': 'sky.vfx',
            'SkyTexture': sky_cubemap_path.as_posix(),
            'F_TEXTURE_FORMAT2': 0,
        }).ToString())

    print("+ Saved", vmat_path.local.as_posix())

    return vmat_path

def ImportVMTtoVMAT(vmt_path: Path, preset_vmat = False):

    global vmt, vmat
    validMaterial = False

    vmt = VMT(KV.FromFile(vmt_path))  # Its actually a collection - needs CollectionFromFile
    vmt.path = vmt_path

    if any(wd in vmt.shader for wd in shaderDict):
        validMaterial = True

    if vmt.shader == 'patch':
        if includePath := vmt.KeyValues["include"]:
            if includePath == r'materials\models\weapons\customization\paints\master.vmt':
                return
            includePath = Path(includePath).as_posix()
            patchKeyValues = vmt.KeyValues.copy()
            vmt.KeyValues.clear()
            print("+ Retrieving material properties from include:", includePath, end=' ... ')
            try:
                vmt.shader, vmt.KeyValues = getKeyValues(sh.src(includePath), ignoreList) # TODO: kv1read
            except FileNotFoundError:
                print("Did not find.")
                failureList.add("Include not found", f'{vmt.path.local} -- {includePath}' )
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

    if not OVERWRITE_MODIFIED and vmat.path.is_file():
        with open(vmat.path, 'r') as fp:
            # don't overwrite if material has been modified
            if fp.readline() == "// THIS FILE IS AUTO-GENERATED\n":
                return
    else:
        vmat.path.parent.MakeDir()

    convertSpecials()
    convertVmtToVmat()

    if (not IGNORE_PROXIES) and (proxies:= vmt.KeyValues["proxies"]):
        kvalues, vmat.KeyValues['DynamicParams'] = ProxiesToDynamicParams(proxies, KNOWN, vmt.KeyValues)
        vmat.KeyValues.update(kvalues)

    if SIMPLE_SHADER_WHERE_POSSIBLE:
        complex_shader_params = {
            "F_MORPH_SUPPORTED",
            "F_TEXTURE_ANIMATION",
            "F_ALPHA_TEST",
            "F_TRANSLUCENT",
            "F_TINT_MASK",
            "F_UNLIT",
            "F_SELF_ILLUM",
            "F_ENABLE_NORMAL_SELF_SHADOW",
            "F_DETAIL_TEXTURE",
            "F_SECONDARY_UV",
        }
        if vmat.shader == core.complex():
            if not any(key in complex_shader_params for key in vmat.KeyValues) and "F_SPECULAR" in vmat.KeyValues:
                vmat.shader = core.simple()
                if "TextureAmbientOcclusion" in vmat.KeyValues:
                    vmat.KeyValues['F_AMBIENT_OCCLUSION_TEXTURE'] = 1

    if PRINT_LEGACY_IMPORT:
        vmat.KeyValues['legacy_import'] = vmt.KeyValues.as_value()

    if DOTA2:
        if vmat.KeyValues.get("F_UNLIT"):
            del vmat.KeyValues['F_UNLIT']
            vmat.KeyValues['F_FULLBRIGHT'] = 1

    sh.msg(vmt.shader + " => " + vmat.shader, "\n")
    vmat.path.write_text(vmat.KeyValues.ToString())

    print("+ Saved", vmat.path if sh.DEBUG else vmat.path.local.as_posix())

    #if vmat.shader == vr.projected_decals():
    #    _ImportVMTtoExtraVMAT(vmt_path, shader=vr.static_overlay(),
    #        path=(vmat.path.parent / (vmat.path.stem + '-static' + vmat.path.suffix)))

    return vmat.path

if __name__ == "__main__":
    sh.parse_argv()
    main()
