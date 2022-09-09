import shared.base_utils2 as sh
from pathlib import Path
from shared.keyvalues3 import KV3File, KV3Header
from shared.modeldoc import ModelDoc
from shared.qcparse import QCParse

SHOULD_OVERWRITE = False
SAMPBOX = False

models = Path('models')

def main():
    print('Source 2 VMDL Generator/QC Converter!')

    qci_files = sh.collect(models, '.qci', '.vmdl', SHOULD_OVERWRITE)
    qc_files = sh.collect(models, '.qc', '.vmdl', SHOULD_OVERWRITE)

    #for qci in qci_files:
    #    ImportQCtoVMDL(qci)
    
    for qc in qc_files:
        ImportQCtoVMDL(qc)
    mdl_files = sh.collect(models, '.mdl', '.vmdl', SHOULD_OVERWRITE, searchPath=sh.output(models))

    for mdl in mdl_files:
        ImportMDLtoVMDL(mdl)

    print("Looks like we are done!")


def ImportMDLtoVMDL(mdl_path: Path):
    vmdl_path = mdl_path.with_suffix('.vmdl')
    vmdl = KV3File(
        m_sMDLFilename = ("../"*SAMPBOX) + mdl_path.local.as_posix()
    )
    sh.write(vmdl_path, vmdl.ToString())
    print('+ Generated', vmdl_path.local)
    return vmdl_path

def ImportQCtoVMDL(qc_path: Path):
    out_vmdl_path = sh.output(qc_path, '.vmdl')
    vmdl = ModelDocVMDL()
    
    active_folder = qc_path.parent

    qc_commands = QCParse.parse(qc_path)

    for command in qc_commands:
        if command is QCParse.staticprop:
            vmdl.root.model_archetype = "static_prop_model"
            vmdl.root.primary_associated_entity = "prop_static"
        
        elif isinstance(command, QCParse.body):
            command: QCParse.body
            rendermeshfile = ModelDoc.RenderMeshFile(
                name = command.name,
                filename = f"models/{command.mesh_filename}"
            )
            vmdl.root.add_nodes(ModelDoc.RenderMeshList().with_nodes( rendermeshfile ))
        
        elif isinstance(command, QCParse.sequence):
            command: QCParse.sequence
            animfile = ModelDoc.AnimFile(
                name = command.name,
                source_filename = f"models/{command.mesh_filename}"
            )
            vmdl.root.add_nodes(ModelDoc.AnimationList().with_nodes(animfile))

    sh.write(out_vmdl_path, vmdl.ToString())
    print('+ Saved', out_vmdl_path.local)


class ModelDocVMDL(KV3File):
    def __init__(self):
        super().__init__(
            rootNode = ModelDoc.RootNode(),
        )
        self.header = KV3Header(format='source1imported_sbox', format_ver='3cec427c-1b0e-4d48-a90a-0436f33a6041')

    @property
    def root(self) -> ModelDoc.RootNode:
        return self["rootNode"]

if __name__ == "__main__":
    sh.parse_argv()
    main()
