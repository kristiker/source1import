import re
from pathlib import Path

def parseKeyValue(line, vmtKeyValues):
    words = []
    nextLine = ''

    # doesn't split inside qotes
    words = re.split(r'\s', line, maxsplit=1) #+(?=(?:[^"]*"[^"]*")*[^"]*$)
    words = list(filter(len, words))

    if not words: return
    elif len(words) == 1:
        Quott = words[0].count('"')
        # fix for: "$key""value""
        if Quott >= 4:
            m = re.match(r'^((?:[^"]*"){1}[^"]*)"(.*)', line)
            if m:
                line = m.group(1)  + '" ' + m.group(2)
                parseKeyValue(line, vmtKeyValues)
        # fix for: $key"value"
        elif Quott == 2:
            # TODO: sth better that keeps text inside quotes intact.
            #line = line.replace('"', ' " ').rstrip(' " ') + '"'
            line = line.replace('"', '')
            parseKeyValue(line, vmtKeyValues)
        return # no recursive loops please
    elif len(words) > 2:
        # fix for: "$key""value""$key""value" - we come here after len == 1 has happened
        nextLine = ' '.join(words[2:]) # words[2:3]
        words = words[:2]

    key = words[0].strip('"').lower()

    if not key.startswith('$'):
        if not 'include' in key:
            return

    # "GPU>=2?$detailtexture"
    if '?' in key:
        #key = key.split('?')[1].lower()
        key.split('?')
        if key[0] == 'GPU>=2':
            key = key[2].lower()
        else:
            if key[0] == 'GPU<2':
                return
            key = key[2].lower()

    val = words[1].lower().strip().strip('"')

    vmtKeyValues[key] = val

    if nextLine: parseKeyValue(nextLine, vmtKeyValues)


def getKV_tailored(vmtFilePath: Path, ignoreList: list):
    """
    Tailored for vmt files. Returns material type + keyvalues
    """
    matType = ''
    vmtKeyValues = {}
    skipNextLine = False
    collectNextLine = False
    proxy_lines = ""

    with open(vmtFilePath, 'r') as vmtFile:
        for row, line in enumerate(vmtFile):

            line = line.strip().split("//", 1)[0].lower()
            if not line or line.startswith('/'):
                continue

            if row < 1:
                matType = re.sub(r'[^A-Za-z0-9_-]', '', line)

            if skipNextLine:
                if "]" in line or "}" in line:
                    skipNextLine = False
                continue
            #elif collectNextLine:
            #    proxy_lines += line + "\n"
            #    if "}" in line:
            #        collectNextLine = False
            else:
                parseKeyValue(line, vmtKeyValues)
            
            #if "proxies" in line:
            #    collectNextLine = True
                
            if any(line.lower().endswith(wd) for wd in ignoreList):
                skipNextLine = True

            if "}" in line and row != 0:
                break
            #row += 1
    
    return matType, vmtKeyValues