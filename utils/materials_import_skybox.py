import shared.PFM as PFM
import os
from shutil import move
from pathlib import Path
import time
from PIL import Image
import numpy as np

COLLECTION_EXT = ".json"
skyboxFaces = ['up', 'dn', 'lf', 'rt', 'bk', 'ft']
materials, skybox, legacy_faces = Path("materials"), Path("skybox"), Path("legacy_faces")

#legacy_face_collections = materials / skybox / legacy_faces / Path("face_collections.json")

OVERWRITE_SKYBOX = True
OVERWRITE_SKYBOX_MATS = True

SKYBOX_CREATE_LDR_FALLBACK = True

# materials/skybox/legacy_faces/sky_example.json -> materials/skybox/sky_example.vmat 
def OutName(path: Path) -> Path:
    return fs.NoSpace(path.parents[1] / Path(path.with_suffix(OUT_EXT).name))

def collect_files_skycollections(path: Path, existing: bool = OVERWRITE_SKYBOX_MATS):
    search_path = path / skybox / legacy_faces
    return fs.collect_files(COLLECTION_EXT, OUT_EXT, existing = existing,  outNameRule=OutName, customPath = search_path)

def collectSkybox(vmtPath: Path, vmtKeyValues: dict) -> Path:

    name, face = vmtPath.stem[:-2], vmtPath.stem[-2:]

    if face not in skyboxFaces:
        return

    #jsonCollectionPath = fs.Input ( materials / skybox / legacy_faces / Path(name).with_suffix(".json") )
    jsonCollectionPath = fs.Output ( materials / skybox / legacy_faces / Path(name).with_suffix(".json") )
    hdrbasetexture = vmtKeyValues.get('$hdrbasetexture')
    hdrcompressedtexture = vmtKeyValues.get('$hdrcompressedtexture')

    collect = sh.GetJson(jsonCollectionPath, bCreate = True)

    if not collect.setdefault('_hdrtype'):
        if hdrbasetexture:
            collect['_hdrtype'] = 'uncompressed'
        elif hdrcompressedtexture:
            collect['_hdrtype'] = 'compressed'

    texture = vmtKeyValues.get('$hdrbasetexture') or vmtKeyValues.get('$hdrcompressedtexture') or vmtKeyValues.get('$basetexture')
    if texture:
        facePath = fs.Output( materials / Path(texture).with_suffix(('.pfm' if hdrbasetexture else TEXTURE_FILEEXT)) )
        newFacePath = facePath.parent / legacy_faces / facePath.name

        if (vtfFacePath := fs.Input(facePath).with_suffix(".vtf")).exists():
            os.makedirs(vtfFacePath.parent / legacy_faces, exist_ok=True)
            move(str(vtfFacePath), str(vtfFacePath.parent / legacy_faces / vtfFacePath.name))

        if facePath.exists():
            os.makedirs(facePath.parent / legacy_faces, exist_ok=True)
            move(str(facePath), str(newFacePath))

        facePath = newFacePath

        if(facePath.exists()):
            collect[face] = fs.LocalDir(facePath).as_posix()

    collect_face_extra = {}
    faceTransform = TexTransform(vmtKeyValues.get('$basetexturetransform'))
    if(faceTransform.rotate != 0):
        collect_face_extra['rotate'] = faceTransform.rotate
        msg("Collecting", face, "transformation: rotate", collect_face_extra['rotate'], 'degrees')
    
    if collect_face_extra:
        path = collect[face]
        collect[face] = {}
        collect[face]['path'] = path
        collect[face].update(collect_face_extra)

    #collections[name].update(collect)
    sh.UpdateJson(jsonCollectionPath, collect)

    if False: #bHasLDRFallback:
        ldr_vmtPath = "1"
        ldr_vmtKeyValues = "2" 
        collectSkybox(ldr_vmtPath, ldr_vmtKeyValues)
    
    return jsonCollectionPath


#if fs.LocalDir(vmtFilePath).is_relative_to(materials/skybox):
#    vmtSkyboxFile = vmtFilePath.with_suffix("").name
#    skyName, skyFace = [vmtSkyboxFile[:-2], vmtSkyboxFile[-2:]]
#    if skyFace in skyboxFaces:
#        collectSkyboxFaces(vmtKeyValues, skyName, skyFace)
#        vmatShader = shader.vr_complex
#        validMaterial = False
#        msg("MATERIAL:", matType)

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

    for face in skyboxFaces:

        if not (v := faceP.get(face)): continue
        facePath = v.get('path') if isinstance(v, dict) else v
        
        if not facePath:
            continue

        if not ( facePath := fs.Output(Path(facePath)) ).exists():
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

        # the largest face determines the resolution of the full map
        maxFaceRes = max(maxFaceRes, max(size[0], size[1]))

    # done
    #pprint( faceParams )
    #print()
    #pprint(faceList)
    cube_w = 4 * maxFaceRes
    cube_h = 3 * maxFaceRes

    # skyName = skyName.rstrip('_')
    img_ext = '.pfm' if hdrType else TEXTURE_FILEEXT
    sky_cubemap_path =  fs.Output( materials/skybox/ Path(skyName + '_cube').with_suffix(img_ext) )

    if not fs.ShouldOverwrite(sky_cubemap_path, OVERWRITE_SKYBOX):
        return sky_cubemap_path

    if hdrType in (None, 'compressed'):
        image_mode = 'RGBA' if (hdrType == 'compressed') else 'RGB'
        SkyCubemapImage = Image.new(image_mode, (cube_w, cube_h), color = (0, 0, 0))

        for face, facePath in faceList.items():
            faceScale = faceParams[face].get('scale')
            faceRotate = int(faceParams[face].get('rotate') or 0)
            if not (faceImage := Image.open(facePath).convert(image_mode)): continue
            
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

            if(faceRotate):
                faceImage = faceImage.rotate(faceRotate)

            SkyCubemapImage.paste(faceImage, pasteCoord)
            faceImage.close()

        # for hdr compressed: uncompress the whole tga map we just created and paste to pfm
        if (hdrType == 'compressed'):

            #print("UNCOMPRESSING... NOT!! -- saving your precious time..")
            #return sky_cubemap_path
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

def ImportSkyVMTtoVMAT(jsonFile: Path) -> Path:

    #if jsonFile.suffix == ".vmt":
    #    print("WUJTF")
    #    vmtKeyValues = sh.getKV(jsonFile)
    #    jsondata["name"] = collectSkybox(vmtFile, vmtKeyValues)
    #    return

    vmatFile = fs.Output( materials/skybox/ Path(jsonFile.stem).with_suffix(OUT_EXT) )

    cubemap = createSkyCubemap(jsonFile.stem, sh.GetJson(jsonFile))
    if cubemap:
        sky_cubemap_path = fs.LocalDir( cubemap )
    else:
        sky_cubemap_path = Path("materials/default/default_cube.tga")
    
    if fs.ShouldOverwrite(vmatFile, True):
        with open(vmatFile, 'w') as fp:
            fp.write('// Sky material and cubemap created by vmt_to_vmat.py\n\n')
            fp.write('Layer0\n{\n\tshader "sky.vfx"\n\n')
            fp.write(f'\tSkyTexture\t"{sky_cubemap_path}"\n\n}}\n')
        
        print(f"+ Saved {fs.LocalDir(vmatFile)}")

    return vmatFile

def main():
    
    skyCollections = collect_files_skycollections(r"D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo\materials", OVERWRITE_SKYBOX_MATS)
    for jsonCollection in skyCollections:
        print(jsonCollection.name, end=" - ")
        ImportSkyVMTtoVMAT(jsonCollection)

from vmt_to_vmat import TexTransform
from vmt_to_vmat import OUT_EXT, TEXTURE_FILEEXT

if __name__ == "__main__":
    import shared.base_utils as sh#from py_shared import GetJson, UpdateJson, getKV
    fs = sh.Source(materials, r"D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo", r"D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo")
    main()
else:
    import shared.base_utils as sh
    from vmt_to_vmat import PATH_TO_CONTENT_ROOT, PATH_TO_NEW_CONTENT_ROOT
    from shared.base_utils import msg, DEBUG
    fs = sh.Source(materials, PATH_TO_CONTENT_ROOT, PATH_TO_NEW_CONTENT_ROOT)

xd = {
  "_hdrtype": "uncompressed",
  "up": "materials/skybox/legacy_faces/sky_nightup.pfm",
  "dn": "materials/skybox/legacy_faces/sky_nightup.tga",
  "lf": "materials/skybox/legacy_faces/sky_nightup.tga",
  "rt": "materials/skybox/legacy_faces/sky_nightup.tga",
  "bk": "materials/skybox/legacy_faces/sky_nightup.tga",
  "ft": "materials/skybox/legacy_faces/sky_nightup.tga"
}
xd2 = {
	"_hdrtype": None,
    "up": "materials/skybox/legacy_faces/cs_baggage_skybox_up.tga",
    "dn": "materials/skybox/legacy_faces/cs_baggage_skybox_dn.tga",
    "lf": "materials/skybox/legacy_faces/cs_baggage_skybox_lf.tga",
    "rt": "materials/skybox/legacy_faces/cs_baggage_skybox_rt.tga",
    "bk": "materials/skybox/legacy_faces/cs_baggage_skybox_bk.tga",
    "ft": "materials/skybox/legacy_faces/cs_baggage_skybox_ft.tga"
}