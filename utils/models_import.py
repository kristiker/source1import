import itertools
import shutil
from typing import Literal, Type, Union
import shared.base_utils2 as sh
import keyvalues3 as kv3
from pathlib import Path
from itertools import tee
from srctools import smd

"""
Import Source Engine models to Source 2

* Generates simple VMDL files linking the MDL.
    * This method has the highest compatibility and is fastest.
    * The model won't be editable until its decompiled from vmdl_c via ModelDoc.
    * Some complex models might crash the compiler i.e. L4D characters and cs animstates.
    * Some less important parameters like $keyvalues are ignored with current compilers.
    * The format for `models/example.vmdl` is:
        <!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->
        {
            m_sMDLFilename = "models/example.mdl"
        }

* Generates (poorly) translated VMDL files based on QC.
    * This method is less stable. The VMDL files are in ModelDoc format.
    * Instead of decompiling, original fbx/dmx/smd files are used.
"""

# mdl import
IMPORT_MDL = True

# qc import
IMPORT_QC = False
IGNORE_SINGLEBODY_BODYGROUPS = True
IGNORE_BBOX = False

SHOULD_OVERWRITE = False
SAMPBOX = False
COPY_FROM_SRC1_DIR = False

models = Path('models')
modelsrc = Path('modelsrc')

def main():
    print('Source 2 VMDL Generator!')
    
    if IMPORT_MDL:
        if COPY_FROM_SRC1_DIR:
            print(' - Copying MDL files from src1 dir!')
            for s1_model_resource in itertools.chain(
                sh.src(models).rglob('*.mdl'),
                sh.src(models).rglob('*.phy'),
                sh.src(models).rglob('*.vvd'),
                sh.src(models).rglob('*.dx90.vtx'),
            ):
                output_path = sh.output(s1_model_resource)
                output_path.parent.MakeDir()
                shutil.copy(s1_model_resource, output_path)

        print('- Generating VMDL from MDL!')
        mdl_files = sh.collect(models, '.mdl', '.vmdl', SHOULD_OVERWRITE, searchPath=sh.output(models))

        for mdl in mdl_files:
            ImportMDLtoVMDL(mdl)

    if IMPORT_QC:
        if COPY_FROM_SRC1_DIR:
            print(' - Copying model sources from src1 dir!')
            for s1_model_resource in itertools.chain(
                sh.src(modelsrc).rglob('*.qc'),
                sh.src(modelsrc).rglob('*.qci'),
                sh.src(modelsrc).rglob('*.smd'),
                sh.src(modelsrc).rglob('*.dmx'),
                sh.src(modelsrc).rglob('*.fbx'),
                sh.src(modelsrc).rglob('*.vta'),
            ):
                output_path = sh.output(models/s1_model_resource.local.relative_to(modelsrc))
                output_path.parent.MakeDir()
                shutil.copyfile(s1_model_resource, output_path)
                sh.status(f"Copied {s1_model_resource.local}")

        print('- Generating VMDL from QC!')
        qci_files = sh.collect(models, '.qci', '.vmdl', True, searchPath=sh.output(models))
        qc_files = sh.collect(models, '.qc', '.vmdl', True, searchPath=sh.output(models))
        
        for qci in qci_files:
            ImportQCtoVMDL(qci)
        
        for qc in qc_files:
            ImportQCtoVMDL(qc)

    print("Looks like we are done!")


def ImportMDLtoVMDL(mdl_path: Path):
    vmdl = dict(
        m_sMDLFilename = ("../"*SAMPBOX) + mdl_path.local.as_posix()
    )
    kv3.write(vmdl, mdl_path.with_suffix('.vmdl'))
    print('+ Generated', vmdl_path.local)
    return vmdl_path

from shared.qc import QC, QCBuilder, QCParseError
from shared.modeldoc import ModelDoc, _BaseNode, _Node

DEFAULT_WEIGHTLIST_NAME = "_qc_default"

AE_IDS = {
    -1: 'AE_INVALID',
    5004: 'AE_CL_PLAYSOUND',
    7777: 'AE_SV_PLAYSOUND',
    7777: 'AE_CL_STOPSOUND',
    6001: 'CL_EVENT_EJECTBRASS1',
    3014: 'EVENT_WEAPON_PISTOL_FIRE',
}


def ImportQCtoVMDL(qc_path: Path):
    vmdl = ModelDoc()
    
    # local paths
    active_folder: Path = qc_path.local.parent
    dir_stack: list[Path] = []
    
    def fixup_filepath(path):
        # resolve it on a full path so that it doesn't resolve to CWD
        path = (sh.EXPORT_CONTENT / active_folder / path).resolve()
        return path.local.as_posix()

    def fixup_material_path(name_or_path: str, is_path: bool = False):
        if not is_path:
            return (Path("materials/" + cdmaterials) / name_or_path ).as_posix()
        # supports path traversal
        return (sh.EXPORT_CONTENT / Path("materials/" + cdmaterials) / name_or_path ).resolve().local.as_posix()

    material_names: set[str] = set()
    cdmaterials = "" # TODO: support multiple cdmaterials

    def add_rendermesh(name: str, reference_mesh_file: str):
        body = QC.body()
        body.name = name
        body.mesh_filename = reference_mesh_file
        return add_rendermesh_from_body(body)
        
    def add_rendermesh_from_body(body: QC.body):
        rendermesh_file = sh.EXPORT_CONTENT / fixup_filepath(body.mesh_filename)
        if rendermesh_file.is_file():
            if rendermesh_file.suffix == ".smd":
                with open(rendermesh_file, "rb") as fp:
                    ref = smd.Mesh.parse_smd(fp)
                    for tri in ref.triangles:
                        material_names.add(tri.mat)
            elif rendermesh_file.suffix == ".dmx":
                #import shared.datamodel as dmx
                #dmx.load(rendermesh_file)
                ...

        else:
            sh.status(f"missing-mesh {rendermesh_file}")
        rendermeshfile = ModelDoc.RenderMeshFile(
            name = body.name,
            filename = rendermesh_file.local.as_posix(),
            import_scale = body.scale,
        )
        return vmdl.add_to_appropriate_list(rendermeshfile)

    with qc_path.open() as fp:
        try:
            qc_commands: list["QC.command" | str] = QCBuilder().parse(fp.read())
        except Exception:
            print("Failed to parse QC file", qc_path)
            raise

    model_name = ""
    global_surfaceprop = "default"
    origin = (0, 0, 0)
    sequences_declared: list[str] = []
    lod0 = None
    skeleton = ModelDoc.Skeleton()
    bHasDefaultWeightlist = False

    bone_name_fixup = lambda name: name.replace('.', '_')

    # These first
    for command in qc_commands:
        if isinstance(command, QC.surfaceprop):
            global_surfaceprop = command.name
        elif isinstance(command, QC.origin):
            origin = command.x, command.y, command.z

    for command in qc_commands:
        match command:
            case QC.staticprop():
                vmdl.rootNode.model_archetype = "static_prop_model"
                vmdl.rootNode.primary_associated_entity = "prop_static"
            case QC.popd():
                try:
                    active_folder = dir_stack.pop()
                except IndexError:
                    pass
            case QC.pushd():
                dir_stack.append(active_folder)
                active_folder = active_folder / command.path
        
        if isinstance(command, QC.include):
            prefab_path = (active_folder / command.filename).with_suffix('.vmdl_prefab')
            prefab = ModelDoc.Prefab(target_file=prefab_path.as_posix())
            vmdl.add_to_appropriate_list(prefab)

        elif isinstance(command, QC.modelname):
            model_name = command.filename

        # https://developer.valvesoftware.com/wiki/$body
        elif isinstance(command, QC.body):
            command: QC.body
            add_rendermesh_from_body(command)

        # https://developer.valvesoftware.com/wiki/$model_(QC)
        elif isinstance(command, QC.model):
            command: QC.model
            add_rendermesh(command.name, command.mesh_filename)
            ... # Options

        # https://developer.valvesoftware.com/wiki/$sequence
        elif isinstance(command, QC.sequence):
            command: QC.sequence
            animfile = ModelDoc.AnimFile(name = command.name)
            mode = 1
            # mode 1: new skeletal anim with simple options
            if command.options[0].endswith('.smd') or command.options[0].endswith('.dmx'):
                animfile.source_filename = fixup_filepath(command.options[0])
            else:
                mode = 2
                # TODO: more than 1 anims
                animfile.source_filename = fixup_filepath(command.options[0])

            if bHasDefaultWeightlist:
                animfile.weight_list_name = DEFAULT_WEIGHTLIST_NAME

            optionsiter = iter(command.options[1:])

            while option:=next(optionsiter, False):
                # Handle subgroups first
                if isinstance(option, list):
                    if option[0].lower() != 'event':
                        continue
                    event_class: str = option[1]
                    if str.isdigit(event_class):
                        try:
                            event_class = AE_IDS[int(event_class)]
                        except KeyError:
                            print("Unknown AnimEvent ID", event_class)
                    animevent = animfile.AnimEvent(
                        event_class=event_class,
                        event_frame=option[2],
                        note=" ".join(option[3:]),
                    )
                    if event_class in ('AE_CL_PLAYSOUND', 'AE_SV_PLAYSOUND', 'AE_CL_STOPSOUND'):
                        animevent.event_keys["name"] = option[3]
                    elif event_class == 'whatever':
                        ...
                    
                    animfile.children.append(animevent)
                    continue
                
                option = option.lower()

                if option == 'frame':
                    animfile.start_frame, animfile.end_frame = next(optionsiter), next(optionsiter)
                elif option in ('origin', 'angles'):
                    x,y,z = next(optionsiter), next(optionsiter), next(optionsiter)
                elif option in ('rotate', 'scale'):
                    f = next(optionsiter)
                elif option == 'reverse': animfile.reverse = True
                elif option == 'loop': animfile.looping = True
                elif option == 'hidden': animfile.hidden = True
                elif option == 'fps': animfile.framerate = next(optionsiter)
                elif option == 'motion extract axis': ... # What is this?
                elif option == 'activity' or option.startswith('act_'):
                    if option.startswith('act_'):
                        animfile.activity_name = option.upper()
                    else:
                        animfile.activity_name = str(next(optionsiter)).upper()
                    animfile.activity_weight = next(optionsiter)
                elif option == 'autoplay': ...
                elif option == 'addlayer':
                    sequence = next(optionsiter)
                    # TODO: AnimAddLayer child node
                elif option == 'blendlayer':
                    sequence = next(optionsiter)
                    startframe, peakframe, tailframe, endframe = next(optionsiter), next(optionsiter), next(optionsiter), next(optionsiter)
                    optionsiter, blendlayer_options = tee(optionsiter) # grab a second iterator
                    # TODO: AnimBlendLayer child node
                    while option:=next(blendlayer_options, False):
                        if option == 'spline': ...
                        elif option == 'xfade': ...
                        elif option == 'poseparameter':
                            poseparameter_name: str = next(blendlayer_options)
                            ...
                        elif option == 'noblend': ...
                        elif option == 'local': ...
                        else:
                            # advance optionsiter since local options stuff was consumed
                            optionsiter = blendlayer_options
                            break
                elif option == 'worldspace': animfile.worldSpace = True
                elif option == 'snap': ...
                elif option == 'realtime': ...
                elif option == 'fadein': animfile.fade_in_time = next(optionsiter)
                elif option == 'fadeout': animfile.fade_out_time = next(optionsiter)
                elif option == 'weightlist': animfile.weight_list_name = next(optionsiter)
                elif option == 'localhierarchy':
                    ...
                elif option == 'compress':
                    frameskip: int = next(optionsiter)
                    ...
                elif option == 'posecycle':
                    pose_parameter: str = next(optionsiter)
                    ...
                # Advanced, I suppose for mode=2?
                # https://developer.valvesoftware.com/wiki/Blend_sequence
                elif option == 'delta': animfile.delta = True
                elif option == 'predelta': ...
                elif option == 'blend':
                    blend_name: str = next(optionsiter)
                    _min: float = next(optionsiter)
                    _max: float = next(optionsiter)
                    ...
                elif option == 'blendwidth':
                    width: int = next(optionsiter)
                    ...
                elif option == 'blendref':
                    ref: str = next(optionsiter)
                    ...
                elif option == 'calcblend':
                    _name: str = next(optionsiter)
                    _attachment: str = next(optionsiter)
                    _idk: Literal["XR"] | Literal["YR"] | Literal["ZR"] = next(optionsiter)
                    ...
                elif option == 'blendcenter':
                    center: str = next(optionsiter)
                    ...
                elif option == 'ikrule': ...
                elif option == 'iklock': ...
                elif option == 'activitymodifier': ...
                # Misc
                elif option == 'node': ...
                elif option == 'transition': ...
                elif option == 'rtransition': ...
                elif option == '$skiptransition': ...
                elif option == 'keyvalues': ...
                
            vmdl.add_to_appropriate_list(animfile)
        
        elif isinstance(command, (QC.weightlist, QC.defaultweightlist)):
            command: QC.weightlist
            if isinstance(command, QC.defaultweightlist):
                command.name = DEFAULT_WEIGHTLIST_NAME
                bHasDefaultWeightlist = True
            weightlist = ModelDoc.WeightList(name = command.name)
            optionsiter = iter(command.options)
            for bone, weight in zip(optionsiter, optionsiter):
                weightlist.weights.append(
                    dict(bone=bone_name_fixup(bone), weight=weight)
)
            vmdl.add_to_appropriate_list(weightlist)

        # https://developer.valvesoftware.com/wiki/$bodygroup
        elif isinstance(command, QC.bodygroup):
            command: QC.bodygroup
            bodygroup = ModelDoc.BodyGroup(name=command.name)
            
            # ['studio', 'mybody', 'studio', 'myhead', 'studio', 'b.smd','blank']
            optionsiter = iter(command.options)
            while string:=next(optionsiter, False):
                if string == "studio":
                    qc_choice = next(optionsiter)
                    if qc_choice.endswith(".smd"):
                        choice_name = Path(qc_choice).stem
                        add_rendermesh(choice_name, qc_choice)
                    else:
                        choice_name = qc_choice
                    choice = ModelDoc.BodyGroupChoice()
                    choice.meshes.append(choice_name)
                    bodygroup.add_nodes(choice)
                elif string == "blank":
                    bodygroup.add_nodes(ModelDoc.BodyGroupChoice(name="blank"))

            if IGNORE_SINGLEBODY_BODYGROUPS and len(bodygroup.children) == 1:
                # name the body after this bodygroup
                vmdl.base_lists[ModelDoc.RenderMeshList].children[-1].name = bodygroup.name
                continue

            vmdl.add_to_appropriate_list(bodygroup)
        
        # https://developer.valvesoftware.com/wiki/$cdmaterials
        elif isinstance(command, QC.cdmaterials):
            command: QC.cdmaterials
            if cdmaterials:
                continue
            cdmaterials = command.folder
            defaultmaterialgroup = ModelDoc.DefaultMaterialGroup()
            for material in material_names:
                defaultmaterialgroup.remaps.append(
                    {
                        "from": material,
                        "to": fixup_material_path(material),
                    }
                )
            vmdl.add_to_appropriate_list(defaultmaterialgroup)

        # https://developer.valvesoftware.com/wiki/$texturegroup
        elif isinstance(command, QC.texturegroup):
            command: QC.texturegroup
            if len(command.options) < 2:
                continue
            defaultgroup = command.options[0]

            for skin_no, skin in enumerate(command.options[1:], 1):
                materialgroup = ModelDoc.MaterialGroup(
                    name = f"{command.name}_{skin_no}",
                )
                for i, default_mat in enumerate(defaultgroup):
                    if len(skin) <= i:
                        break
                    materialgroup.remaps.append(
                    {
                        "from": fixup_material_path(default_mat),
                        "to": fixup_material_path(skin[i], is_path=True),
                    }
                )
                vmdl.add_to_appropriate_list(materialgroup)

        # https://developer.valvesoftware.com/wiki/$renamematerial
        elif isinstance(command, QC.renamematerial):
            command: QC.renamematerial
            mgList = vmdl.base_lists.get(ModelDoc.MaterialGroupList)
            if mgList is None:
                continue

            dmg = mgList.find_by_class_bfs(ModelDoc.DefaultMaterialGroup)
            if dmg is None:
                continue
            
            # rename the s2 filename in default material group
            for remap in dmg.remaps:
                if remap["from"] != command.current:
                    continue
                remap["to"] = fixup_material_path(command.new)
                # then update any subsequent s2 links to the new one
                for mg in mgList.children:
                    if mg is dmg:
                        continue
                    for remap in mg.remaps:
                        if remap["from"] != fixup_material_path(command.current):
                            continue
                        remap["from"] = fixup_material_path(command.new)

        # https://developer.valvesoftware.com/wiki/$lod
        elif isinstance(command, QC.lod):
            command: QC.lod
            
            replacemodel = {}

            optionsiter = iter(command.options)
            while string:=next(optionsiter, False):
                if string == "replacemodel":
                    replacemodel.__setitem__(next(optionsiter), next(optionsiter))
                elif string == "removemodel":
                    replacemodel.__setitem__(next(optionsiter), None)
                elif string in ("replacematerial", "removemesh", "nofacial", "bonetreecollapse", "replacebone"):
                    ...
            # first LOD!
            if ModelDoc.LODGroupList not in vmdl.base_lists:
                lod0 = ModelDoc.LODGroup()
                ... # Form it based on the $body stuff
                vmdl.add_to_appropriate_list(lod0)
            
            # add stuff to lod0 that lodn is supposed to replace
            for lod0_mesh in replacemodel.keys():
                if lod0_mesh in lod0.meshes:
                    continue
                lod0.meshes.append(lod0_mesh)

            lod_n = ModelDoc.LODGroup(switch_threshold=command.threshold)
            for lod_n_mesh in replacemodel.values():
                if lod_n_mesh is None:
                    continue
                lod_n.meshes.append(lod_n_mesh)
            
            vmdl.add_to_appropriate_list(lod_n)

        # https://developer.valvesoftware.com/wiki/$attachment
        elif isinstance(command, QC.attachment):
            command: QC.attachment
            attachment = ModelDoc.Attachment(
                name = command.name,
                parent_bone = bone_name_fixup(command.parent_bone),
                relative_origin = [command.x, command.y, command.z],
                # TODO: rotation
            )
            vmdl.add_to_appropriate_list(attachment)

        # https://developer.valvesoftware.com/wiki/$collisionmodel
        elif isinstance(command, QC.collisionmodel):
            command: QC.collisionmodel
            physicsmeshfile = ModelDoc.PhysicsHullFile(
                filename=fixup_filepath(command.mesh_filename),
                surface_prop=global_surfaceprop
            )

            vmdl.add_to_appropriate_list(physicsmeshfile)
        
        # https://developer.valvesoftware.com/wiki/$collisionjoints
        elif isinstance(command, QC.collisionjoints):
            command: QC.collisionjoints
            physicsmeshfile = ModelDoc.PhysicsHullFile(
                filename=fixup_filepath(command.mesh_filename),
                surface_prop=global_surfaceprop
            )

            vmdl.add_to_appropriate_list(physicsmeshfile)
        
        # https://developer.valvesoftware.com/wiki/$includemodel
        # grab $animation, $sequence, $attachment and $collisiontext from this model
        elif isinstance(command, QC.includemodel):
            command: QC.includemodel
            vmdl.rootNode.base_model_name = (models / command.filename).with_suffix('.vmdl').as_posix()
        
        elif isinstance(command, QC.declaresequence):
            sequences_declared.append(command.name)
        
        elif isinstance(command, QC.definebone):
            command: QC.definebone
            # bone already defined, ignore
            bone_name = bone_name_fixup(command.name)
            parent_bone_name = bone_name_fixup(command.parent)
            if skeleton.find_by_name_dfs(bone_name):
                continue
            bone = ModelDoc.Bone(
                name = bone_name,
                origin=[command.posx, command.posy, command.posz],
                angles=[command.rotx, command.roty, command.rotz],
            )
            # unparented bone
            if not command.parent:
               skeleton.children.append(bone)
            else:
                # parented to a bone that can't have been declared yet
                if not len(skeleton.children):
                    continue
                # parented to a bone that can't be found on the tree yet
                found = skeleton.find_by_name_dfs(parent_bone_name)
                if not found:
                    continue
                found.add_nodes(bone)
        
        # https://developer.valvesoftware.com/wiki/$bbox
        elif isinstance(command, (QC.bbox, QC.cbox)):
            command: Union[QC.bbox, QC.cbox]
            if IGNORE_BBOX:
                continue
            if isinstance(command, QC.bbox):
                hull_type = ModelDoc.Bounds_Hull
            else:
                hull_type = ModelDoc.Bounds_View
                # If the coordinates of the this clipping bounding box are all zero, $bbox is used instead.
                if not any(param != 0 for param in command.__dict__.values()):
                    # Don't even bother
                    continue

            vmdl.add_to_appropriate_list(hull_type(
                name = command.__class__.__name__,
                mins = [command.minx, command.miny, command.minz],
                maxs = [command.maxx, command.maxy, command.maxz],
            ))


        # https://developer.valvesoftware.com/wiki/$keyvalues
        elif isinstance(command, QC.keyvalues):
            for key, value in command.__dict__.items():
                key = key.lower().strip('"')
                # https://developer.valvesoftware.com/wiki/Prop_data
                if key == "prop_data":
                    prop_data = ModelDoc.GenericGameData(game_class="prop_data")
                    prop_data.game_keys.update(value)
                    vmdl.add_to_appropriate_list(prop_data)

    bIsIncludeFile = False
    if qc_path.suffix == ".qci":
        bIsIncludeFile = True
    
    if not model_name and not bIsIncludeFile:
        raise QCParseError("No model name found in QC file %s" % qc_path.local)
    
    if bIsIncludeFile:
        out_vmdl_path = sh.output(qc_path, '.vmdl_prefab')
    else:
        out_vmdl_path = sh.EXPORT_CONTENT / (models / model_name.lower()).with_suffix('.vmdl').as_posix()
    
    if not SHOULD_OVERWRITE and out_vmdl_path.exists():
        sh.skip("already-exist", out_vmdl_path)
        return

    out_vmdl_path.parent.MakeDir()

    if len(sequences_declared):
        vmdl_prefab = ModelDoc()
        out_vmdl_prefab_path = out_vmdl_path.with_name("declared_sequences.vmdl_prefab")

        for sequence in sequences_declared:
            animfile = ModelDoc.AnimFile(
                name = sequence,
            )
            vmdl_prefab.add_to_appropriate_list(animfile)

        kv3.write(vmdl_prefab, out_vmdl_prefab_path)
        print('+ Saved prefab', out_vmdl_prefab_path.local)

    if len(skeleton.children):
        vmdl.rootNode.add_nodes(skeleton)
        
    kv3.write(vmdl, out_vmdl_path)
    print('+ Saved', out_vmdl_path.local)


from dataclasses import dataclass, asdict



if __name__ == "__main__":
    # TODO: Don't ask for src1?
    sh.parse_argv()
    main()
