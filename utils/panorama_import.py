# import csgo source1 panorama into source2

from pathlib import Path
import zipfile as pbin
from io import TextIOWrapper

panorama_in = Path(r'D:\Games\steamapps\common\Half-Life Alyx\game\csgo\panorama')
panorama_out = Path(r'D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo\panorama')

code_pbin = panorama_in / "code.pbin"

from functools import wraps
importdict = {}
def zipimport(ext):
    def decorator(func):
        @wraps(func)
        def wrapper(asset_in: Path, asset_out: Path = None, pre_opened: TextIOWrapper = None, **kwargs):
            if pre_opened is None:
                pre_opened = open(asset_in, encoding="utf-8")
            try:
                if asset_out is None:
                    asset_out = panorama_out / asset_in.relative_to(panorama_in).with_suffix(ext)
                asset_out.parent.mkdir(parents=True, exist_ok=True)
                rv = func(asset_in, asset_out, pre_opened, **kwargs)
            finally:
                pre_opened.close()
            return rv
         
        importdict[ext.replace('v', '')] = wrapper
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
    with open(vxml_out, 'w', encoding="utf-8") as out:
        out.write(pre_opened.read()
            .replace('file://','s2r://')
            .replace('.css', '.vcss_c')
            .replace('.js', '.vjs_c')
            .replace('.vtf', '.vtex_c') # i guess
        )
        print("+ Saved", vxml_out.relative_to(panorama_out.parent))
'''
<root>
	<styles>
		<include src="s2r://panorama/styles/dotastyles.vcss_c" />
		<include src="s2r://panorama/styles/popups/popups_shared.vcss_c" />
		<include src="s2r://panorama/styles/popups/popup_custom_test.vcss_c" />
	</styles>
	
	<script>
		var SetupPopup = function()
		{
			var strPopupValue = $.GetContextPanel().GetAttributeString( "popupvalue", "(not found)" );
			$.GetContextPanel().SetDialogVariable( "popupvalue", strPopupValue );
		};
	</script>

	<PopupCustomLayout class="PopupPanel Hidden" popupbackground="dim" oncancel="UIPopupButtonClicked()" onload="SetupPopup()">
		<Label class="PopupTitle" text="Test Popup" />

		<Label class="PopupMessage" text="popupvalue: {s:popupvalue}" />	

		<Panel class="PopupButtonRow">
			<TextButton class="PopupButton" text="OK" onactivate="UIPopupButtonClicked()" />
		</Panel>
	
	</PopupCustomLayout>
</root>
'''
'''
<root>
	<styles>
		<include src="file://{resources}/styles/gamestyles.css" />
        <include src="file://{resources}/styles/popups/popups_shared.css" />
	</styles>
	
	<scripts>
		<include src="file://{resources}/scripts/popups/popup_navdrawer.js" />
	</scripts>

	<PopupCustomLayout class="PopupPanel Hidden" popupbackground="dim" onload="SetupPopup()">
		<Label class="PopupTitle" text="Test Custom Layout Popup" />

		<Label class="PopupMessage" text="popupvalue: {s:popupvalue}" />	

		<Panel class="PopupButtonRow">
			<TextButton class="PopupButton" text="OK" onactivate="OnOKPressed()" />
            <TextButton class="PopupButton" text="Cancel" onactivate="UIPopupButtonClicked()" />
		</Panel>
	
	</PopupCustomLayout>
</root>
'''

"""GenerateNameMappingFromAssetList: Unknown extension for "panorama/images/tooltips/tooltip_arrow_left.vtf"""

@zipimport('.vcss')
def ImportPanoramaCss(css_in: Path, vcss_out: Path = None, pre_opened: TextIOWrapper = None):
    with open(vcss_out, 'w', encoding="utf-8") as out:
        out.write(pre_opened.read()) # .replace('file://','s2r://')
        print("+ Saved", vcss_out.relative_to(panorama_out.parent))
    

@zipimport('.vjs')
def ImportJS(js_in: Path, vjs_out: Path = None, pre_opened: TextIOWrapper = None):
    with open(vjs_out, 'w', encoding="utf-8") as out:
        out.write(pre_opened.read())
        print("+ Saved", vjs_out.relative_to(panorama_out.parent))

@zipimport('.vcfg')
def ImportCfg(cfg_in: Path, vcfg_out: Path = None, pre_opened: TextIOWrapper = None):
    with open(vcfg_out, 'w', encoding="utf-8") as out:
        out.write(pre_opened.read())
        print("+ Saved", vcfg_out.relative_to(panorama_out.parent))

if __name__ == '__main__':
    if not code_pbin.exists():
        raise SystemExit()

    code = pbin.ZipFile(code_pbin, 'r')

    panorama_cfg = {}

    try:
        with TextIOWrapper(code.open('panorama/panorama.cfg'), encoding="utf-8") as cfg:
            ... # kv1 read
    except KeyError:
        print("panorama.cfg not found")

    for file in code.filelist:
        path = panorama_in.parent / file.filename
        fp = TextIOWrapper(code.open(file), encoding="utf-8")

        if file.filename.endswith('.cfg'):
            if file.filename == 'panorama/panorama.cfg': continue

        if importfunc := importdict.get(Path(file.filename).suffix):
            importfunc(path, pre_opened=fp)
        else:
            print("Import me senpai", file.filename)
            fp.close()