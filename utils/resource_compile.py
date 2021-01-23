import subprocess
from pathlib import Path
import shared.base_utils as sh

#fs = sh.Source()

resourcecompiler_path = Path(r"D:\Games\steamapps\common\Half-Life Alyx\game/bin/win64/resourcecompiler.exe")

print(resourcecompiler_path)

command = [resourcecompiler_path] #, "-o", fs.Output(vtfFile.parent) , "-i", vtfFile
result = subprocess.run(command, stdout=subprocess.PIPE) #
print (result.stdout.decode("utf-8"))