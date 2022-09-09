from pathlib import Path
import vpk

content = Path(input("Enter your content path, e.g. D:/Games/steamapps/common/Half-Life Alyx/content/hlvr_addons/csgo\n>"))
root_mod = Path(input("Enter root game, e.g. D:/Games/steamapps/common/Half-Life Alyx/game/hlvr\n>"))

game = content
while True:
    game = game.parent
    if game.name == "content":
        mod = content.relative_to(game)
        game = game.parent / "game" / mod
        break

pak = vpk.VPK(root_mod/"pak01_dir.vpk")
already_available_textures = set()

# find vtexes in pak
for pakked_file, _ in pak.items():
    if not pakked_file.startswith("materials/particle"):
        continue
    if not pakked_file.endswith(".vtex_c"):
        continue
    already_available_textures.add(pakked_file)

# Delete our "overrides"
for tex in already_available_textures:
    content_side = (content/tex).with_suffix(".vtex")
    game_side = game/tex
    if content_side.is_file():
        content_side.unlink()
        print("Removed content side", content_side.relative_to(content))
    if game_side.is_file():
        game_side.unlink()
        print("Removed game side", tex)
