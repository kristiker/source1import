import shared.base_utils2 as sh
import shared.datamodel as dmx
from pathlib import Path

SHOULD_OVERWRITE = False

def ImportSFMSession(session_path: Path):
    """Update SFM resource references for S2FM."""
    sh.status(f"- Opening {session_path.local}...")
    try:
        session = dmx.load(session_path)
    except Exception:
        return print("Error while reading:", session_path.local)

    # Map
    for clip in session.find_elements(elemtype='DmeFilmClip'):
        clip['mapname'] = clip.get('mapname', '').replace('.bsp', '.vmap')

    # Materials
    for overlay in session.find_elements(elemtype='DmeMaterialOverlayFXClip'):
        overlay['material'] = overlay.get('material', '').replace('.vmt', '.vmat')

    # Models
    for game_model in session.find_elements(elemtype='DmeGameModel'):
        game_model['modelName'] = game_model.get('modelName', '').replace('.mdl', '.vmdl')

    # Particles
    for game_particle in session.find_elements(elemtype='DmeGameParticleSystem'):
        game_particle['particleSystemType'] = sh.RemapTable.get('vpcf', {}).get(game_particle.get('particleSystemType', ''), '')

    # Projected Lights (cookies)
    for projected_light in session.find_elements(elemtype='DmeProjectedLight'):
        projected_light['texture'] = projected_light.get('texture', '').replace('.vtf', '.vtex')

    # Sounds
    for game_sound in session.find_elements(elemtype='DmeGameSound'):
        game_sound.name = game_sound.name.replace('\\', '/')
        file = Path(game_sound.get('soundname', '')) # 'sounds'/ 
        if file.name:
            game_sound['soundname'] = file.with_suffix('.vsnd').as_posix()

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
