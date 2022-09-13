from typing import Type, Union
import shared.base_utils2 as sh
from pathlib import Path
from shared.keyvalues3 import KV3File, KV3Header

"""
Import Source Engine models to Source 2

* Generates simple VMDL files linking the MDL.
    * This method has the highest compatibility and is fastest.
    * The model won't be editable until its decompiled from vmdl_c via ModelDoc.
    * Some complex models might crash the compiler i.e. L4D characters and cs animstates.
    * Some less important parameters like $keyvalues are ignored.
    * The format for `models/example.vmdl` is:
        <!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->
        {
            m_sMDLFilename = "models/example.mdl"
        }

* Generates (poorly) translated VMDL files based on QC.
    * VMDL is the equivalent of QC but the formats differ a lot.

In contrast with the other scripts, models_import will search for files to
convert at *output* (e.g. Source2 content), and src1 input is ignored.
Reason is that Source 2 can *right away* accept both MDL and SMD files
as CONTENT, and it's more efficient for the user to move
those to Source 2 CONTENT than for the script to copy stuff around.

So: move your Source1 GAME `models` to Source2 CONTENT `models`.
If you're converting QC files (aka `modelsrc`), you can put those in S2 `models` as well,
or anywhere inside it (like `models/legacy_qc/`) since QC files don't need to have
the same name the mdl. Source2 will happily read Source1 SMD, DMX, and MDL+PHY+VVD files as long as
they are placed somewhere inside Source2 CONTENT `models`.
"""

IMPORT_MDL = True
IMPORT_QC = False

SHOULD_OVERWRITE = False
SAMPBOX = False

models = Path('models')

def main():
    print('Source 2 VMDL Generator!')
    if IMPORT_MDL:
        print('- Generating VMDL from MDL!')
        mdl_files = sh.collect(models, '.mdl', '.vmdl', SHOULD_OVERWRITE, searchPath=sh.output(models))

        for mdl in mdl_files:
            ImportMDLtoVMDL(mdl)

    if IMPORT_QC:
        print('- Generating VMDL from QC!')
        qci_files = sh.collect(models, '.qci', '.vmdl', SHOULD_OVERWRITE, searchPath=sh.output(models))
        qc_files = sh.collect(models, '.qc', '.vmdl', SHOULD_OVERWRITE, searchPath=sh.output(models))
        
        for qci in qci_files:
            ImportQCtoVMDL(qci)
        
        for qc in qc_files:
            ImportQCtoVMDL(qc)

    print("Looks like we are done!")


def ImportMDLtoVMDL(mdl_path: Path):
    vmdl_path = mdl_path.with_suffix('.vmdl')
    vmdl = KV3File(
        m_sMDLFilename = ("../"*SAMPBOX) + mdl_path.local.as_posix()
    )
    sh.write(vmdl_path, vmdl.ToString())
    print('+ Generated', vmdl_path.local)
    return vmdl_path

from shared.qc import QC, QCBuilder, QCParseError
from shared.modeldoc import ModelDoc, _BaseNode, _Node

def ImportQCtoVMDL(qc_path: Path):
    vmdl = ModelDocVMDL()
    
    active_folder: Path = qc_path.local.parent
    dir_stack: list[Path] = []
    fixup_filepath = lambda path: (active_folder / path).as_posix()

    qc_commands: list[Union["QC.command", str]] = QCBuilder().parse(qc_path.open().read())

    model_name = ""
    global_surfaceprop = "default"
    origin = (0, 0, 0)
    sequences_declared: list[str] = []
    lod0 = None
    skeleton = ModelDoc.Skeleton()

    bone_name_fixup = lambda name: name.replace('.', '_')

    # These first
    for command in qc_commands:
        if isinstance(command, QC.surfaceprop):
            global_surfaceprop = command.name
        elif isinstance(command, QC.origin):
            origin = command.x, command.y, command.z


    for command in qc_commands:

        if command is QC.staticprop:
            vmdl.root.model_archetype = "static_prop_model"
            vmdl.root.primary_associated_entity = "prop_static"
        
        elif command is QC.popd:
            try:
                active_folder = dir_stack.pop()
            except IndexError():
                pass
        
        elif isinstance(command, QC.pushd):
            dir_stack.append(active_folder)
            active_folder = active_folder / command.path
        
        elif isinstance(command, QC.include):
            prefab_path = (active_folder / command.filename).with_suffix('.vmdl_prefab')
            prefab = ModelDoc.Prefab(target_file=prefab_path.as_posix())
            vmdl.add_to_appropriate_list(prefab)

        elif isinstance(command, QC.modelname):
            model_name = command.filename

        # https://developer.valvesoftware.com/wiki/$body
        elif isinstance(command, QC.body):
            command: QC.body
            rendermeshfile = ModelDoc.RenderMeshFile(
                name = command.name,
                filename = fixup_filepath(command.mesh_filename),
                import_scale=command.scale,
            )
            vmdl.add_to_appropriate_list(rendermeshfile)
        
        # https://developer.valvesoftware.com/wiki/$model_(QC)
        elif isinstance(command, QC.model):
            command: QC.model
            rendermeshfile = ModelDoc.RenderMeshFile(
                name = command.name,
                filename = fixup_filepath(command.mesh_filename),
            )
            vmdl.add_to_appropriate_list(rendermeshfile)
            ... # Options

        # https://developer.valvesoftware.com/wiki/$sequence
        elif isinstance(command, QC.sequence):
            command: QC.sequence
            animfile = ModelDoc.AnimFile(
                name = command.name,
                source_filename = fixup_filepath(command.mesh_filename),
            )
            vmdl.add_to_appropriate_list(animfile)

        # https://developer.valvesoftware.com/wiki/$bodygroup
        elif isinstance(command, QC.bodygroup):
            command: QC.bodygroup
            bodygroup = ModelDoc.BodyGroup(name=command.name)
            
            # TODO: this is probably not right
            # if smd add as RenderMeshFile?
            # ['studio', 'mybody', 'studio', 'myhead', 'studio', 'b.smd','blank']
            optionsiter = iter(command.options)
            while string:=next(optionsiter, False):
                if string == "studio":
                    choice = ModelDoc.BodyGroupChoice()
                    choice.meshes.append(next(optionsiter))
                    bodygroup.add_nodes(choice)
                elif string == "blank":
                    bodygroup.add_nodes(ModelDoc.BodyGroupChoice(name="blank"))

            vmdl.add_to_appropriate_list(bodygroup)
        
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
            vmdl.root.base_model_name = (models / command.filename).with_suffix('.vmdl').as_posix()
        
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
    
    if not bIsIncludeFile:
        out_vmdl_path = sh.EXPORT_CONTENT / (models / model_name.lower()).with_suffix('.vmdl')
    else:
        out_vmdl_path = sh.output(qc_path, '.vmdl_prefab')
    out_vmdl_path.parent.MakeDir()

    if len(sequences_declared):
        vmdl_prefab = ModelDocVMDL()
        out_vmdl_prefab_path = out_vmdl_path.with_name("declared_sequences.vmdl_prefab")

        for sequence in sequences_declared:
            animfile = ModelDoc.AnimFile(
                name = sequence,
            )
            vmdl_prefab.add_to_appropriate_list(animfile)

        sh.write(out_vmdl_prefab_path, vmdl_prefab.ToString())
        print('+ Saved prefab', out_vmdl_prefab_path.local)

    if len(skeleton.children):
        vmdl.root.add_nodes(skeleton)
        
    sh.write(out_vmdl_path, vmdl.ToString())
    print('+ Saved', out_vmdl_path.local)


from dataclasses import asdict
class ModelDocVMDL(KV3File):
    def __init__(self):
        self.header = KV3Header(format='source1imported_sbox', format_ver='3cec427c-1b0e-4d48-a90a-0436f33a6041')
        self.root = ModelDoc.RootNode()

        self.base_lists: dict[Type[_BaseNode], _BaseNode] = {}

    def __str__(self):
        self["rootNode"] = asdict(self.root)
        return super().__str__()

    def add_to_appropriate_list(self, node: _Node):
        """
        Adds bodygroup to bodygrouplist, animfile to animationlist, etc. Only makes one list.
        """
        container_type = ModelDoc.get_container(type(node))
        container = self.base_lists.get(container_type)
        if container is None:
            container = container_type()
            self.base_lists[container_type] = container
            self.root.add_nodes(container)
        
        container.add_nodes(node)

if __name__ == "__main__":
    # TODO: Don't ask for src1?
    sh.parse_argv()
    main()
