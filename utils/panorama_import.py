# import csgo source1 panorama into source2

from pathlib import Path, PurePosixPath
import zipfile as pbin
from io import TextIOWrapper
import re

import shared.keyvalues1 as kv1
import shared.base_utils2 as sh
sh.importing = Path("panorama")

REPLACE_NAMEDPATHS = True

CODE_PBIN = sh.IMPORT_GAME / sh.importing / "code.pbin"
IMPORT_FUNC = {}  # IMPORT_FUNC['.vxml']() is ImportPanoramaXml()

from functools import wraps
def zipimport(ext):
    def decorator(func):
        @wraps(func)
        def wrapper(asset_in: Path, asset_out: Path = None, pre_opened: TextIOWrapper = None, **kwargs):
            if pre_opened is None:
                pre_opened = open(asset_in, encoding="utf-8")
            try:
                if asset_out is None:
                    asset_out = sh.output(asset_in).with_suffix(ext)
                asset_out.parent.mkdir(parents=True, exist_ok=True)
                rv = func(asset_in, asset_out, pre_opened, **kwargs)
            finally:
                pre_opened.close()
            return rv
         
        IMPORT_FUNC[ext.replace('v', '')] = wrapper
        return wrapper
    return decorator

@zipimport
def ImportPanoramaVFont(asset_in: Path, pre_opened: TextIOWrapper = None):
    ...
    # \panorama\fonts\*.vfont

@zipimport
def ImportPanoramaFontConfig(asset_in: Path, pre_opened: TextIOWrapper = None):
    ...
    # \panorama\fonts\fonts.conf

@zipimport('.vxml')
def ImportPanoramaXml(xml_in: Path, vxml_out: Path = None, pre_opened: TextIOWrapper = None):
    
    def fix_src_paths(src_path: re.Match):
        'file://{resources}/styles/dotastyles.css -> s2r://panorama/styles/dotastyles.vcss_c'
        EXTENSIONS = {
            '.xml': '.vxml_c',
            '.css': '.vcss_c',
            '.js': '.vjs_c',
            '.vtf': '.vtex_c',
            '.svg': '.vsvg_c',
            # webm and png as is
        }

        full_match, path_match = src_path.group(0, 1)
        if not path_match:
            return full_match

        source2_path: str = path_match

        if source2_path.startswith('file://'):
            if REPLACE_NAMEDPATHS:
                for namedpath in panorama_cfg.get('namedpaths', ()):
                    namedpath_curly = '{' + namedpath + '}'
                    if namedpath_curly in source2_path:
                        source2_path = source2_path.replace(namedpath_curly, panorama_cfg['namedpaths'][namedpath])
        
            source2_path = PurePosixPath(source2_path.removeprefix('file://'))
            source2_path = source2_path.with_suffix( EXTENSIONS.get( source2_path.suffix, source2_path.suffix ) )
            source2_path = f"s2r://{source2_path}"
    
        return full_match.replace(path_match, source2_path)  # needs to be a better way

    with open(vxml_out, 'w', encoding="utf-8") as out:
        xml_content = pre_opened.read()
        out.write(
            re.sub(r'src\s*=\s*"?(.+?)["|\s]', fix_src_paths, xml_content)
        )
        print("+ Saved", vxml_out.local)

"""GenerateNameMappingFromAssetList: Unknown extension for "panorama/images/tooltips/tooltip_arrow_left.vtf"""

@zipimport('.vcss')
def ImportPanoramaCss(css_in: Path, vcss_out: Path = None, pre_opened: TextIOWrapper = None):
    with open(vcss_out, 'w', encoding="utf-8") as out:
        out.write(pre_opened.read()) # .replace('file://','s2r://')
        print("+ Saved", vcss_out.local)
    

@zipimport('.vjs')
def ImportJS(js_in: Path, vjs_out: Path = None, pre_opened: TextIOWrapper = None):
    with open(vjs_out, 'w', encoding="utf-8") as out:
        out.write(pre_opened.read())
        print("+ Saved", vjs_out.local)

@zipimport('.vcfg')
def ImportCfg(cfg_in: Path, vcfg_out: Path = None, pre_opened: TextIOWrapper = None):
    with open(vcfg_out, 'w', encoding="utf-8") as out:
        out.write(pre_opened.read())
        print("+ Saved", vcfg_out.local)

if __name__ == '__main__':
    if not CODE_PBIN.is_file():
        raise SystemExit(0)

    code = pbin.ZipFile(CODE_PBIN, 'r')

    panorama_cfg = {}
    try:
        with TextIOWrapper(code.open('panorama/panorama.cfg'), encoding="utf-8") as cfg:
            panorama_cfg = kv1.KV.FromBuffer(cfg.read())
    except KeyError:
        print("panorama.cfg not found")

    for file in code.filelist:
        path_extract = sh.IMPORT_GAME / file.filename
        fp = TextIOWrapper(code.open(file), encoding="utf-8")

        if file.filename.endswith('.cfg'):
            if file.filename == 'panorama/panorama.cfg': continue

        if importfunc := IMPORT_FUNC.get(path_extract.suffix):
            importfunc(path_extract, pre_opened=fp)
        else:
            print("Import me senpai", file.filename)
            fp.close()
