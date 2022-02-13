import shared.base_utils2 as sh
import shared.datamodel as dmx
from pathlib import Path

SHOULD_OVERWRITE = False

def ImportSFMSession(session_path: Path):
    sh.status(f"- Opening {session_path.local}...")
    try:
        session = dmx.load(session_path)
    except Exception:
        return print("Error while reading:", session_path.local)

    #print(session.find_elements(elemtype='DmeFilmClip').pop()['materialOverlay'], "   ")
    dme_models = session.find_elements(elemtype='DmeGameModel')
    if dme_models is not None:
        for game_model in dme_models:
            # TODO: source2namefixup
            game_model['modelName'] = game_model.get('modelName', '').replace('.mdl', '.vmdl')

    session_out_path = sh.output(session_path, dest=sh.EXPORT_GAME)
    session_out_path.parent.MakeDir()
    # text cuz binary won't work right now.
    session.write(session_out_path, 'keyvalues2', 4)
    print('+ Imported', session_path.local)
    return session_out_path

def main():
    print('Source 2 Filmmaker Session Importer!')
    sh.importing = 'elements'
    sh.import_context['dest'] = sh.EXPORT_GAME
    for session in sh.collect('elements', '.dmx', '.dmx', SHOULD_OVERWRITE, searchPath=sh.src('elements/sessions')):
        ImportSFMSession(session)
    print("Looks like we are done!")

if __name__ == "__main__":
    sh.parse_argv()
    main()
