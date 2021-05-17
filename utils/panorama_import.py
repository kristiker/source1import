#import source1 panorama from csgo into source2



from pathlib import Path


def ImportPanoramaVFont(asset_path: Path):
    ...
    # \panorama\fonts\*.vfont

def ImportPanoramaFontConfig(asset_path: Path):
    ...
    # \panorama\fonts\fonts.conf

def ImportPanoramaCss(asset_path: Path):
    ...
def ImportPanoramaXml(asset_path: Path):
    ...
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
def ImportPanoramaCss(asset_path: Path):
    ...